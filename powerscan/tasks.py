# MTW: Celery tasks.  Autodiscovered, see celery.py
# app.autodiscover_tasks()

# General Python
import sys
import os
import datetime
from datetime import timedelta
import json
import subprocess
import shutil
import ipaddress
import netaddr
import traceback
import logging

# Celery / Django
import celery
from celery import shared_task, Task, group, chain
from celery import signals, states
from celery.app import control 

from django.http import JsonResponse
from django_celery_results.models import TaskResult
from django.core.management import call_command
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Our stuff
from django_nys_02.settings import CELERY_QUEUE
from django_nys_02.celery import app as celery_app

from .models import (
    IpRangeSurvey, CountTract, IpRangePing, 
    MmIpRange, DebugPowerScan
)

from .ping import PingSurveyManager

#SMALL_CHUNK_SIZE = 10000
#TOTAL_OBJECTS = 22000

CELERY_FIELD_SURVEY_ID = "survey_id"

RESULTS_STATES = "states"
RESULTS_COUNTIES = "counties"
RESULTS_TRACTS = "tracts"
RESULTS_RANGES = "ranges"

TALLY_DELAY_MINS = 5
TALLY_DELAY_SECS = TALLY_DELAY_MINS * 60

MAX_TALLY_RETRY_COUNT = 8

TIME_FORMAT_STRING = "%H:%M:%S"

DEBUG_ID = 1

RATE_PACKETS_SECOND = 10000
# RATE_PACKETS_SECOND = 2000

logger = logging.getLogger(__name__)

def unused_start_tracts(self, *args, **kwargs):
    survey = IpRangeSurvey()
    survey.time_started = timezone.now()
    survey.save()
    # Use the minus to be descending
    count_range_tracts = CountTract.objects.order_by("-range_count")
    f = lambda crt: crt.census_tract.id
    batch_one = [f(x) for x in count_range_tracts[:10]]
    ending_task = finish_survey.s(survey.id)

    chained_task = chain(ping_tracts.s(survey.id, batch_one), ending_task)
    result = chained_task.apply_async(
                queue=CELERY_QUEUE,
                routing_key='ping.tasks.start_tracts')
    return result

    # Break into batches of 10 tracts, right now
    
def unused_make_temp_dir(tract_id):
    TEMP_DIRECTORY = "/tmp/exec_zmap/"
    now = datetime.datetime.now()
    #cleanup_temp_dir(temp_directory_port)
    folder_snapshot = now.strftime("%Y%m%d_%H%M%S")
    full_path = os.path.join(TEMP_DIRECTORY, folder_snapshot, str(tract_id))
    # print(f"make_temp_dir(), full_path = {full_path}")
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    # print(f"tasks.py:make_temp_dir(), full_path = {full_path}")
    return full_path

def _unused_prep_file_range(ip_range, dir_path):
    # Create the CSV file
    ip_start = ip_range.ip_range_start
    ip_end = ip_range.ip_range_end
    ip_start_underscores = ip_start.replace('.', '_')
    output_file_name = f"{ip_start_underscores}.csv"
    file_path_text = os.path.join(dir_path, output_file_name)
    cidrs = netaddr.iprange_to_cidrs(ip_start, ip_end)
    ip_network = cidrs[0]
    # print(f"prep_file_range(), ip_start = {ip_start}, ip_end = {ip_end}, ip_network = {ip_network}")
    return file_path_text, ip_network 

def _count_output_lines(file_path):
    return sum(1 for _ in open(file_path))

def _unused_ping_single_range(survey, tract, ip_range, dir_path, debug):
    file_path, ip_network = _prep_file_range(ip_range, dir_path)
    file_path_string = str(file_path)
    ip_net_string = str(ip_network)
    if debug:
        logger.info(f"_unused_ping_single_range(), ip_start = {ip_range.ip_range_start}, ")
        logger.info(f"     file_path = {file_path_string}, ip_net_string = {ip_net_string}")

    # Start the subprocess
    _execute_subprocess2(ip_net_string, file_path_string, debug)

    num_responses = _count_output_lines(file_path)
    range_ping = IpRangePing(ip_survey=survey,ip_range=ip_range,
        num_ranges_pinged=ip_network.size,
        num_ranges_responded=num_responses,
        time_pinged=timezone.now())
    range_ping.save()

@shared_task(bind=True)
def build_whitelist(self, *args, **kwargs):
    debug = DebugPowerScan.objects.get(pk=DEBUG_ID)
    # Ensure another worker hasn't grabbed the survey, yet
    # print(f"build_whitelist(), self = {self}, kwargs = {kwargs}")
    survey_id_string = kwargs[CELERY_FIELD_SURVEY_ID]
    survey_id = int(survey_id_string)
    survey = IpRangeSurvey.objects.get(pk=survey_id)
    if survey.time_whitelist_started:
        first = f"build_whitelist(), survey.time_whitelist_started : {survey.time_whitelist_started},"
        second = "another worker grabbed it, exiting"
        logger.info(first + second)
        return 0

    # Save that we started the process, that's our (worker) lock
    survey.time_whitelist_started = timezone.now()
    survey.save()

    survey_manager = PingSurveyManager(survey_id, debug.whitelist)
    # num_states, num_counties, num_tracts, num_ranges = survey_manager.build_whitelist()
    num_states, num_counties, num_ranges = survey_manager.build_whitelist()

    if debug.whitelist:
        message = f"build_whitelist(), self = {self}, {num_ranges} ranges, cleaning up survey manager"
    survey_manager.close()
    survey.num_total_ranges = num_ranges
    survey.save()

    # Django channels back to the caller
    return num_states, num_counties, num_ranges

def _execute_subprocess(whitelist_file, output_file, metadata_file, log_file):
    try:
        # This seems wrong for a ICMP
        # port = 80
        # f"--log-file=${log_file}", NoVa
        list_command = ["zmap",
            "--quiet", f"-r {RATE_PACKETS_SECOND}",
            f"--whitelist-file={whitelist_file}",
            f"--output-file={output_file}",
            "--output-module=csv",
            "--output-fields=saddr,timestamp-ts",
            f"--metadata-file={metadata_file}",
            f"--log-file={log_file}", 
            "--sender-threads=1",
            "--probe-module=icmp_echoscan"]
        full_command = " ".join(list_command)
        #if"zmap -p {port} -r {rate_packets_second} {ip_net_string} -o {file_path_string}"
        first_100 = full_command[:100]
        logger.info(f"_execute_subprocess(), calling subprocess.Popen(), full_command(100) = {first_100}")
        # stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process = subprocess.Popen(full_command, shell=True, stdout=None, stderr=None) 

        # We need this here for now, else we don't have an output file and there are no lines to count (for responses)
        #stdout, stderr = process.communicate(timeout=10)
        ret_val = process.returncode
        if ret_val:
            logger.warning(f"_execute_subproces(), subprocess.Popen(), bad return code = {ret_val}, stdout:")
            stdout, stderr = process.communicate(timeout=10)
            print(f"{stdout}\nstderr:\n{stderr}")
    except Exception as e:
        raise Exception(f"_execute_subprocess(), Exception {e}, Popen command: {full_command}")
    return ret_val

# def zmap_from_file(self, *args, **kwargs):
#    survey_id_string = kwargs[CELERY_FIELD_SURVEY_ID]
@shared_task(bind=True)
def zmap_from_file(self, survey_id_string):
    debug = DebugPowerScan.objects.get(pk=DEBUG_ID)
    # Ensure another worker hasn't grabbed the survey, yet
    #ip_source_id = kwargs["ip_source_id"]
    #survey_id = int(survey_id_string)
    survey_id = int(survey_id_string)
    survey = IpRangeSurvey.objects.get(pk=survey_id)

    if survey.time_ping_started:
        first = f"zmap_from_file(), survey.time_ping_started: {survey.time_ping_started}," 
        second = "another worker grabbed it, exiting"
        logger.info(first + second)
        return 0
    # Save that we started the process, that's our (worker) lock
    survey.time_ping_started = timezone.now()
    formatted_start = survey.time_ping_started.strftime(TIME_FORMAT_STRING)
    survey.save()

    # Check our debug flag
    debug_zmap = debug.zmap
    survey_manager = PingSurveyManager.find(survey_id, debug_zmap)
    if not survey_manager:
        logger.warning(f"zmap_from_file({survey_id}), no directory, quitting")
        return None

    whitelist_file, output_file, metadata_file, log_file = survey_manager.get_zmap_files()

    # Run Zmap command here. We'll process the output file when the zmap is done running
    ret_val = _execute_subprocess(whitelist_file, output_file, metadata_file, log_file)
    return metadata_file

def _process_zmap_results(survey, survey_manager, metadata_file_job, now):
    whitelist_file, output_file, metadata_file_survey, log_file = survey_manager.get_zmap_files()
    if metadata_file_job != metadata_file_survey:
        logger.info(f"_process_zmap_results(), md_file_job = {metadata_file_job}, md_survey = {metadata_file_survey}")
        return 0

    # See whether the metadata file has values
    size = os.path.getsize(metadata_file_job)
    if size == 0:
        #print(f"_process_zmap_results(), empty metadata file: {metadata_file_job}")
        return 0

    # Calculate zmap time
    survey.time_ping_stopped = now
    # print(f"SURVEY SAVE, 7")
    survey.save()
    if not survey.time_ping_stopped:
        print(f"_process_zmap_results(), time_ping_stopped = {survey.time_ping_stopped}")
        timedelta_secs = 0
    elif not survey.time_ping_started:
        print(f"_process_zmap_results(), time_ping_started = {survey.time_ping_started}")
        timedelta_secs = 0
    else:
        timedelta_secs = survey.time_ping_stopped - survey.time_ping_started
    timedelta_mins = timedelta_secs.total_seconds() / 60
    formatted_now = now.strftime(TIME_FORMAT_STRING)
    # print(f"_process_zmap_results(), now {formatted_now}, zmap time = {timedelta_mins:.1f} mins")
    return survey_manager.process_results(survey)

@celery_app.task
def tally_results(metadata_file, survey_id, retry_count):
    # Ensure another worker hasn't grabbed the survey, yet
    now = timezone.now()
    formatted_now = now.strftime(TIME_FORMAT_STRING)
    try:
        int_survey_id = int(survey_id)
        survey = IpRangeSurvey.objects.get(pk=int_survey_id)
        if survey.time_tally_started:
            first = f"tally_results(), survey = {int_survey_id}, tally_started { survey.time_tally_started}, "
            second = f"another worker grabbed it"
            print(first + second)
            return 0
        # We save this, but we'll set it back to null if we're not ready to tally (no metadata file)
        survey.time_tally_started = now
        survey.save()

        debug = DebugPowerScan.objects.get(pk=DEBUG_ID)
        debug_tally = debug.tally_results 

        survey_manager = PingSurveyManager.find(int_survey_id, debug_tally)
        if not survey_manager:
            print(f"Task.tally_results(), no survey manager for survey_id: {int_survey_id}")
            return 0
        pings_to_db = _process_zmap_results(survey, survey_manager, metadata_file, now)
        if pings_to_db == 0:
            delta = timedelta(seconds=TALLY_DELAY_SECS)
            tally_start = now + delta
            formatted_start = tally_start.strftime(TIME_FORMAT_STRING)
            retry_count = retry_count + 1
            if retry_count > MAX_TALLY_RETRY_COUNT:
                print(f"Task.tally_results({int_survey_id}), max retries ({MAX_TALLY_RETRY_COUNT}) exceeded, aborting")
                return
            first = f"Task.tally_results({int_survey_id}), empty_zmap_file, delay:"
            second = f"{TALLY_DELAY_MINS}m, new start: {formatted_start}, retry_count: {retry_count}"
            print(first + second)
            async_result2 = tally_results.apply_async(
                countdown=TALLY_DELAY_SECS, 
                kwargs={"survey_id": survey_id,
                    "metadata_file": metadata_file,
                    "retry_count": retry_count} )
            survey.time_tally_started = None
            survey.save()
            return 0

        survey.time_tally_stopped = timezone.now()
        survey.num_ranges_responded = pings_to_db
        # print(f"SURVEY SAVE, 10")
        survey.save()
        print(f"Task.tally_results({survey_id}), saved {pings_to_db:,} hosts to db")
    except Exception as e:
        print(f"Task.tally_results({survey_id}), exception: {e}")
        pings_to_db = -1
    return pings_to_db 

    #network = ipaddress.ip_network(str(cidrs), strict=False)
    #num_potential = cidrs.size
        #exc_type, exc_value, exc_traceback = sys.exc_info()
        #print(f"    exc_traceback = {dir(exc_traceback)}")
        #exc_traceback.print_exc()
        #exc_traceback.print_exception(*sys.exc_info())
                #"ip_source_id": IP_RANGE_SOURCE,
            # print(f"SURVEY SAVE, 9")
        # print(f"SURVEY SAVE, 8")
    # print(f"tally_results(), metadata = {metadata_file}, survey_id = {survey_id}")
    # print(f"tally_results(), now: {formatted_now}")
