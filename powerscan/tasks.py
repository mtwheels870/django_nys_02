# MTW: Celery tasks.  Autodiscovered, see celery.py
# app.autodiscover_tasks()

# General Python
import sys
import os
import datetime
import json
import subprocess
import shutil
import ipaddress
import netaddr

from enum import Enum

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

# Out stuff
from django_nys_02.celery import app as celery_app, QUEUE_NAME

from .models import (
    IpRangeSurvey, CountTract, IpRangePing, 
    MmIpRange)

from .ping import PingSurveyManager

SMALL_CHUNK_SIZE = 10000
TOTAL_OBJECTS = 22000

TEMP_DIRECTORY = "/tmp/exec_zmap/"

CELERY_FIELD_SURVEY_ID = "survey_id"

RESULTS_STATES = "states"
RESULTS_COUNTIES = "counties"
RESULTS_TRACTS = "tracts"
RESULTS_RANGES = "ranges"

def start_tracts(self, *args, **kwargs):

    # Main method
    print(f"start_tracts(), self = {self}, kwargs = {kwargs}, creating survey")

    survey = IpRangeSurvey()
    survey.time_started = timezone.now()
    survey.save()
    # Use the minus to be descending
    count_range_tracts = CountTract.objects.order_by("-range_count")
    f = lambda crt: crt.census_tract.id
    batch_one = [f(x) for x in count_range_tracts[:10]]
    #batch_two = [f(x) for x in count_range_tracts[11:20]]
    #batch_three = [f(x) for x in count_range_tracts[21:30]]
    ending_task = finish_survey.s(survey.id)

#    grouped_tasks = group(ping_tracts.s(survey.id, batch_one), ping_tracts.s(survey.id, batch_two), 
#        ping_tracts.s(survey.id, batch_three)) 
    # chained_task = chain(grouped_tasks, ending_task)
    chained_task = chain(ping_tracts.s(survey.id, batch_one), ending_task)
    print(f"start_tracts(), chained_task = {chained_task}")
    result = chained_task.apply_async(
                queue=QUEUE_NAME,
                routing_key='ping.tasks.start_tracts')
    print(f"start_tracts(), after apply_async(), result = {result}")
    return result

    # Break into batches of 10 tracts, right now
    
def make_temp_dir(tract_id):
    now = datetime.datetime.now()
    #cleanup_temp_dir(temp_directory_port)
    folder_snapshot = now.strftime("%Y%m%d_%H%M%S")
    full_path = os.path.join(TEMP_DIRECTORY, folder_snapshot, str(tract_id))
    print(f"make_temp_dir(), full_path = {full_path}")
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    # print(f"tasks.py:make_temp_dir(), full_path = {full_path}")
    return full_path

def _prep_file_range(ip_range, dir_path):
    # Create the CSV file
    ip_start = ip_range.ip_range_start
    ip_end = ip_range.ip_range_end
    ip_start_underscores = ip_start.replace('.', '_')
    output_file_name = f"{ip_start_underscores}.csv"
    file_path_text = os.path.join(dir_path, output_file_name)
    cidrs = netaddr.iprange_to_cidrs(ip_start, ip_end)
    ip_network = cidrs[0]
    print(f"prep_file_range(), ip_start = {ip_start}, ip_end = {ip_end}, ip_network = {ip_network}")
    #network = ipaddress.ip_network(str(cidrs), strict=False)
    #num_potential = cidrs.size
    return file_path_text, ip_network 

def _count_output_lines(file_path):
    return sum(1 for _ in open(file_path))

def _ping_single_range(survey, tract, ip_range, dir_path, debug):
    file_path, ip_network = _prep_file_range(ip_range, dir_path)
    file_path_string = str(file_path)
    ip_net_string = str(ip_network)
    if debug:
        print(f"_ping_single_range(), ip_start = {ip_range.ip_range_start}, ")
        print(f"     file_path = {file_path_string}, ip_net_string = {ip_net_string}")

    # Start the subprocess
    _execute_subprocess2(ip_net_string, file_path_string, debug)

    num_responses = _count_output_lines(file_path)
    range_ping = IpRangePing(ip_survey=survey,ip_range=ip_range,
        num_ranges_pinged=ip_network.size,
        num_ranges_responded=num_responses,
        time_pinged=timezone.now())
    range_ping.save()

def send_task_result(data):
    channel_layer = get_channel_layer()
    result = {"result": f"Processed: {data}"}
    # Is this passing a function pointer?
    async_to_sync(channel_layer.group_send) (
        "task_updates", {"type": "task.completed", "message": result}
    )


#def _ping_all_ranges(survey, tract, debug):
#    print(f"_ping_all_ranges(), tract = {tract}, debug = {debug}")
#    ip_ranges = tract.deiprange_set.all()
#    total_ranges = ip_ranges.count()
#    if debug:
#        print(f"_ping_all_ranges(), tract_id = {tract.id}, total_ranges = {total_ranges}")
#    dir_path = make_temp_dir(tract.id)

#    for index, ip_range in enumerate(ip_ranges):
#        _ping_single_range(survey, tract, ip_range, dir_path, debug)
#    return total_ranges

@shared_task(bind=True)
def build_whitelist(self, *args, **kwargs):
    # Ensure another worker hasn't grabbed the survey, yet
    print(f"build_whitelist(), self = {self}, kwargs = {kwargs}")
    survey_id_string = kwargs[CELERY_FIELD_SURVEY_ID]
    survey_id = int(survey_id_string)
    survey = IpRangeSurvey.objects.get(pk=survey_id)
    if survey.time_whitelist_started:
        first = f"build_whitelist(), survey.time_whitelist_started : {survey.time_whitelist_started},"
        second = "another worker grabbed it, exiting"
        print(first + second)
        return 0
    # Save that we started the process, that's our (worker) lock
    survey.time_whitelist_started = timezone.now()
    survey.save()


    survey_manager = PingSurveyManager(survey_id)
    num_states, num_counties, num_tracts, num_ranges = survey_manager.build_whitelist()

    message = f"build_whitelist(), self = {self}, {num_ranges} ranges, cleaning up survey manager"
    survey_manager.close()

    # Django channels back to the caller
    send_task_result(message)
    return num_states, num_counties, num_tracts, num_ranges

def _execute_subprocess(whitelist_file, output_file, metadata_file, log_file):
    try:
        # This seems wrong for a ICMP
        # port = 80
        rate_packets_second = 10000
        # f"--log-file=${log_file}", NoVa
        list_command = ["zmap",
            "--quiet", f"-r {rate_packets_second}",
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
        print(f"_ping_single_range(), calling subprocess.Popen(), full_command = {full_command}")
        # stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process = subprocess.Popen(full_command, shell=True, stdout=None, stderr=None) 

        print(f"\n_ping_single_range(), should track metadata file: {metadata_file}")
        # We need this here for now, else we don't have an output file and there are no lines to count (for responses)
        #stdout, stderr = process.communicate(timeout=10)
        ret_val = process.returncode
        if ret_val:
            print(f"_ping_single_range(), subprocess.Popen(), bad return code = {ret_val}, stdout:")
            stdout, stderr = process.communicate(timeout=10)
            print(f"{stdout}\nstderr:\n{stderr}")
    except Exception as e:
        raise Exception(f"_execute_subprocess(), Exception {e}, Popen command: {full_command}")
    return ret_val

@shared_task(bind=True)
def zmap_from_file(self, *args, **kwargs):
    # Ensure another worker hasn't grabbed the survey, yet
    survey_id_string = kwargs[CELERY_FIELD_SURVEY_ID]
    print(f"zmap_from_file(), survey_id = {survey_id_string}")
    #ip_source_id = kwargs["ip_source_id"]
    survey_id = int(survey_id_string)
    survey = IpRangeSurvey.objects.get(pk=survey_id)

    if survey.time_ping_started:
        print(f"zmap_from_file(), survey.time_ping_started: {survey.time_ping_started}, another worker grabbed it, exiting")
        return 0
    # Save that we started the process, that's our (worker) lock
    survey.time_ping_started = timezone.now()
    survey.save()

    #print(f"build_whitelist(), source_id = {ip_source_id}")
    survey_manager = PingSurveyManager.find(survey_id)
    whitelist_file, output_file, metadata_file, log_file = survey_manager.get_zmap_files()

    # Run Zmap command here. We'll process the output file when the zmap is done running
    ret_val = _execute_subprocess(whitelist_file, output_file, metadata_file, log_file)
    return metadata_file

def _process_zmap_results(survey, survey_manager, metadata_file_job):
    whitelist_file, output_file, metadata_file_survey, log_file = survey_manager.get_zmap_files()
    if metadata_file_job != metadata_file_survey:
        print(f"_process_zmap_results(), metadata1 = {metadata_file_job}, metadata2 = {metadata_file_survey}")
        return 0

    # See whether the metadata file has values
    size = os.path.getsize(metadata_file_job)
    if size == 0:
        print(f"_process_zmap_results(), empty metadata file: {metadata_file_job}")
        return 0

    return survey_manager.process_results(survey)

@shared_task(bind=True)
def tally_results(self, *args, **kwargs):
    # Ensure another worker hasn't grabbed the survey, yet
    print(f"tally_results(), self = {self}, kwargs = {kwargs}")
    survey_id_string = kwargs[CELERY_FIELD_SURVEY_ID]
    #ip_source_id = kwargs["ip_source_id"]
    metadata_file = kwargs["metadata_file"]
    survey_id = int(survey_id_string)
    survey = IpRangeSurvey.objects.get(pk=survey_id)
    if survey.time_tally_started:
        print(f"tally_results(), survey.time_tally_started { survey.time_tally_started}, another worker grabbed it")
        return 0
    survey.time_tally_started = timezone.now()
    survey.save()

    survey_manager = PingSurveyManager.find(survey_id)
    pings_to_db = _process_zmap_results(survey, survey_manager, metadata_file)
    survey.time_stopped = timezone.now()
    survey.save()
    print(f"tally_results(), saved {pings_to_db} to database survey_id = {survey_id}")
    return pings_to_db 

@receiver(post_save, sender=TaskResult)
def task_result_saved(sender, **kwargs):
    #print(f"task_result_saved(), sender = {sender}, kwargs = {kwargs}")
    task_result = kwargs['instance']
    id = task_result.task_id
    status = task_result.status
    result = task_result.result
    print(f"task_result_saved(), task_result = {task_result}")
    print(f"     id = {id}, status = {status}, result = {result}")
    if status == states.SUCCESS:
        celery_results_handler.store_task_result(task_result)
    else:
        print(f"task_result_saved(), status = {status}, ignoring")
        


    #print(f"build_whitelist(), source_id = {ip_source_id}")
    #if ip_source_id == 2:
    #elif ip_source_id == 1:
    #    print(f"build_whitelist(), currently don't support ip_source_id = {ip_source_id}")
    #else:
    #    raise Exception(f"build_whitelist(), unrecognized source_id: {ip_source_id}")
#def _execute_subprocess2(ip_net_string, file_path_string, debug):
#    try:
#        # This seems wrong for a ICMP
#        # port = 80
#        rate_packets_second = 10000
#        list_command = ["zmap",
#            "--quiet", f"-r {rate_packets_second}",
#            "--probe-module=icmp_echoscan", f"{ip_net_string}", f"-o {file_path_string}"]
#        full_command = " ".join(list_command)
#        #if"zmap -p {port} -r {rate_packets_second} {ip_net_string} -o {file_path_string}"
#        if debug:
#            print(f"_ping_single_range(), calling subprocess.Popen(), full_command = {full_command}")
#        # stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#        process = subprocess.Popen(full_command, shell=True, stdout=None, stderr=None) 
#
        # We need this here for now, else we don't have an output file and there are no lines to count (for responses)
#        stdout, stderr = process.communicate(timeout=10)
#        ret_val = process.returncode
#        if ret_val:
#            print(f"_ping_single_range(), subprocess.Popen(), bad return code = {ret_val}, stdout:")
#            print(f"{stdout}\nstderr:\n{stderr}")
#    except Exception as e:
#        raise Exception(f"_execute_subprocess2(), Exception {e}, Popen command: {full_command}")
#    return ret_val
