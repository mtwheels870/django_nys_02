# MTW: Celery tasks.  Autodiscovered, see celery.py
# app.autodiscover_tasks()

import sys
import os
import datetime
import json
import subprocess
import shutil
import ipaddress
import netaddr

import celery
from celery import shared_task, Task, group, chain
from celery import signals, states
from celery.app import control 

from django.http import JsonResponse
from django_celery_results.models import TaskResult
from django.core.management import call_command
from django.utils import timezone

from django_nys_02.celery import app as celery_app, QUEUE_NAME

from .models import IpRangeSurvey, CountRangeTract, IpRangePing, DeIpRange, WorkerLock
from .ping import PingSurveyManager

SMALL_CHUNK_SIZE = 10000
TOTAL_OBJECTS = 22000

TEMP_DIRECTORY = "/tmp/exec_zmap/"

#@shared_task(bind=True)
# Nested method
def _get_all_ranges(survey, tract, index_range):
    batches = []
    get_range_chunks = True
    range_start = 0
    range_end = range_start + SMALL_CHUNK_SIZE
    total_ranges = tract.deiprange_set.all().count()
    print(f"get_all_ranges(), tract_id = {tract.id}, total_ranges = {total_ranges}")
    while get_range_chunks:
        print(f"get_all_ranges(), getting {SMALL_CHUNK_SIZE} ranges, getting[{range_start},{range_end}]")
        ip_ranges = tract.deiprange_set.all().order_by("id")[range_start:range_end]
        ranges_returned = ip_ranges.count()
        for range in ip_ranges:
            if index_range % 1000 == 0:
                print(f"start_range_survey(), creating range[{index_range:05}], {range.ip_range_start}")
            range_ping = IpRangePing(ip_survey=survey,ip_range=range)
            range_ping.save()
            index_range = index_range + 1
        batches.append((range_start, range_start + ranges_returned))
        range_start = range_end
        range_end = range_end + SMALL_CHUNK_SIZE
        # We're at the end of a census tract
        if ranges_returned < SMALL_CHUNK_SIZE:
            break
    return index_range, batches

#def start_range_survey(self, *args, **kwargs):
@shared_task(bind=True)
def start_range_survey(self, *args, **kwargs):

    # Main method
    print(f"start_range_survey(), self = {self}, kwargs = {kwargs}, creating survey")

    survey = IpRangeSurvey()
    survey.save()
    # Use the minus to be descending
    count_range_tracts = CountRangeTract.objects.order_by("-range_count")
    
    # Iterate through each of those counties and walk through all of the ranges
    all_batches = []
    index_range = 0
    for tract_count in count_range_tracts:
        tract = tract_count.census_tract
        try:
            index_range, batches = _get_all_ranges(survey, tract, index_range)
            all_batches.append(batches)
            if index_range > TOTAL_OBJECTS:
                break
        # Get all of the ranges from this census tract
        except (KeyError, DeIpRange.DoesNotExist):
            print(f"start_range_survey(), Exception, no ranges for tract = {tract.id}")

    survey.time_started = timezone.now()
    # Hack, should actually take the size from count_range_tracts
    survey.num_total_objects = TOTAL_OBJECTS 
    survey.save()
    print(f"start_range_survey(), created {survey.num_total_objects} ip ranges to ping")
    print(f"start_range_survey(), all_batches: ")
    for index, batch in enumerate(all_batches):
        print(f"s_r_s(), batch[{index}] : {batch}")
    return TOTAL_OBJECTS

@shared_task(bind=True)
def ping_tracts(self, survey_id, list_tracts):
    print(f"ping_tracts(), self = {self}")
    # f = lambda crt: crt.census_tract
    # list_tracts = [f(x) for x in list_count_range_tracts]
    print(f"ping_tracts(), survey_id = {survey_id}, tracts(id)s: {list_tracts}")
    return 23

@shared_task(bind=True)
def finish_survey(self, results, survey_id):
    try:
        print(f"finish_survey(), self = {self}")
        print(f"finish_survey(), survey_id = {survey_id}, results = {results}")
        survey = IpRangeSurvey.objects.get(pk=survey_id)
        survey.time_stopped = timezone.now()
        survey.save()
        print(f"finish_survey(), after save...")
    except (KeyError, DeIpRange.DoesNotExist):
        raise Exception(f"finish_survey(), Exception, could not find survey {survey_id}")
    print(f"finish_survey(), returning")
    return 37

@shared_task(bind=True)
def start_tracts(self, *args, **kwargs):

    # Main method
    print(f"start_tracts(), self = {self}, kwargs = {kwargs}, creating survey")

    survey = IpRangeSurvey()
    survey.time_started = timezone.now()
    survey.save()
    # Use the minus to be descending
    count_range_tracts = CountRangeTract.objects.order_by("-range_count")
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

def _execute_subprocess(ip_net_string, file_path_string, debug):
    try:
        # This seems wrong for a ICMP
        # port = 80
        rate_packets_second = 10000
        list_command = ["zmap",
            "--quiet", f"-r {rate_packets_second}",
            "--probe-module=icmp_echoscan", f"{ip_net_string}", f"-o {file_path_string}"]
        full_command = " ".join(list_command)
        #if"zmap -p {port} -r {rate_packets_second} {ip_net_string} -o {file_path_string}"
        if debug:
            print(f"_ping_single_range(), calling subprocess.Popen(), full_command = {full_command}")
        # stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process = subprocess.Popen(full_command, shell=True, stdout=None, stderr=None) 

        # We need this here for now, else we don't have an output file and there are no lines to count (for responses)
        stdout, stderr = process.communicate(timeout=10)
        ret_val = process.returncode
        if ret_val:
            print(f"_ping_single_range(), subprocess.Popen(), bad return code = {ret_val}, stdout:")
            print(f"{stdout}\nstderr:\n{stderr}")
    except Exception as e:
        raise Exception(f"_execute_subprocess(), Exception {e}, Popen command: {full_command}")
    return ret_val

def _ping_single_range(survey, tract, ip_range, dir_path, debug):
    file_path, ip_network = _prep_file_range(ip_range, dir_path)
    file_path_string = str(file_path)
    ip_net_string = str(ip_network)
    if debug:
        print(f"_ping_single_range(), ip_start = {ip_range.ip_range_start}, ")
        print(f"     file_path = {file_path_string}, ip_net_string = {ip_net_string}")

    # Start the subprocess
    _execute_subprocess(ip_net_string, file_path_string, debug)

    num_responses = _count_output_lines(file_path)
    range_ping = IpRangePing(ip_survey=survey,ip_range=ip_range,
        num_ranges_pinged=ip_network.size,
        num_ranges_responded=num_responses,
        time_pinged=timezone.now())
    range_ping.save()

def _ping_all_ranges(survey, tract, debug):
    print(f"_ping_all_ranges(), tract = {tract}, debug = {debug}")
    ip_ranges = tract.deiprange_set.all()
    total_ranges = ip_ranges.count()
    if debug:
        print(f"_ping_all_ranges(), tract_id = {tract.id}, total_ranges = {total_ranges}")
    dir_path = make_temp_dir(tract.id)

    for index, ip_range in enumerate(ip_ranges):
        _ping_single_range(survey, tract, ip_range, dir_path, debug)
    return total_ranges

@shared_task(bind=True)
def zmap_all(self, *args, **kwargs):

    # Main method

    survey = IpRangeSurvey()
    survey.time_started = timezone.now()
    survey.save()
    print(f"zmap_all(), self = {self}, kwargs = {kwargs}, created survey = {survey.id}")
    # Use the minus to be descending
    count_range_tracts = CountRangeTract.objects.order_by("-range_count")
    print(f"zmap_all(), num_tracts = {count_range_tracts.count()}")
    ranges_pinged = 0
    for index_tract, count_tract in enumerate(count_range_tracts):
        tract = count_tract.census_tract
        debug = (index_tract == 0)
        ranges_this_tract = _ping_all_ranges(survey, tract, debug)
        ranges_pinged = ranges_pinged + ranges_this_tract 
        if index_tract >= 1:
            break

    # Save the completion time
    survey.time_stopped = timezone.now()
    survey.num_total_objects = ranges_pinged
    survey.save()

    return ranges_pinged 

    # Break into batches of 10 tracts, right now
    
def whitelist_maxm(survey_manager):
    ranges = MmIpRange.objects.all()
    for index, range in enumerate(ranges):
        if index % 1000 == 0:
            print(f"whitelist_maxm(), range[{index}]: {range.ip_network}")
        survey_manager.add(index, range.id, range.ip_network)
        # DEBUG
        if index >= 100:
            break
    return index

@shared_task(bind=True)
def build_whitelist(self, *args, **kwargs):
    # Ensure another worker hasn't grabbed the survey, yet
    print(f"build_whitelist(), self = {self}, kwargs = {kwargs}")
    worker_lock_id = kwargs["worker_lock_id"]
    ip_source_id = kwargs["ip_source_id"]
    worker_lock = WorkerLock.objects.get(pk=worker_lock_id)
    if worker_lock.time_started:
        print(f"build_whitelist(), worker_lock.time_started: {worker_lock.time_started}, another worker grabbed it, exiting")
        return 0
    # Save that we started the process, that's our (worker) lock
    worker_lock.time_started = timezone.now()
    worker_lock.save()

    print(f"build_whitelist(), source_id = {ip_source_id}")
    survey_manager = PingSurveyManager()
    if ip_source_id == 2:
        num_ranges = whitelist_maxm(survey_manager)
    elif ip_source_id == 1:
        print(f"build_whitelist(), currently don't support ip_source_id = {ip_source_id}")
    else:
        raise Exception(f"build_whitelist(), unrecognized source_id: {ip_source_id}")

    print(f"build_whitelist(), cleaning up survey manager, lock")
    survey_manager.close()
    worker_lock.delete()
    return num_ranges
