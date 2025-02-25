# MTW: Celery tasks.  Autodiscovered, see celery.py
# app.autodiscover_tasks()

import sys
import os
import datetime
import json
import subprocess
import shutil

import celery
from celery import shared_task, Task, group, chain
from celery import signals, states
from celery.app import control 

from django.http import JsonResponse
from django_celery_results.models import TaskResult
from django.core.management import call_command
from django.utils import timezone

from .models import IpRangeSurvey, CountRangeTract, IpRangePing, DeIpRange

SMALL_CHUNK_SIZE = 10000
TOTAL_OBJECTS = 22000

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
    # f = lambda crt: crt.census_tract
    # list_tracts = [f(x) for x in list_count_range_tracts]
    print(f"ping_tracts(), survey_id = {survey_id}, tracts(id)s: {list_tracts}")

@shared_task(bind=True)
def finish_survey(self, survey_id, args):
    print(f"finish_survey(), survey_id = {survey_id}")
    survey = IpRangeSurvey.objects.get(pk=survey_id)
    survey.time_stopped = timezone.now()
    survey.save()

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
    result = chained_task.apply_async()
    return result

    # Break into batches of 10 tracts, right now
    
