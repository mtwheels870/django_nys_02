# MTW: Celery tasks.  Autodiscovered, see celery.py
# app.autodiscover_tasks()

import sys
import os
import datetime
import json
import subprocess
import shutil

import celery
from celery import shared_task, Task
from celery import signals, states
from celery.app import control 

from django.http import JsonResponse
from django_celery_results.models import TaskResult
from django.core.management import call_command
from django.utils import timezone

from .models import IpRangeSurvey, CountRangeTract, IpRangePing, DeIpRange

SMALL_CHUNK_SIZE = 10000
TOTAL_OBJECTS = 2000



#@shared_task(bind=True)
#def start_range_survey(self, *args, **kwargs):
class RangeSurvey(Task):
    def __init__(self):
        self.batches = []

    def _get_all_ranges(self, survey, tract, index_range):
        outer_loop = True
        get_range_chunks = True
        range_start = 0
        range_end = range_start + SMALL_CHUNK_SIZE
        print(f"get_all_ranges(), tract_id = {tract.id}")
        while get_range_chunks:
            print(f"get_all_ranges(), getting {SMALL_CHUNK_SIZE} ranges, getting[{range_start},{range_end}]")
            ip_ranges = tract.deiprange_set.all().order_by("id")[range_start:range_end]
            ranges_returned = ip_ranges.count()
            for range in ip_ranges:
                if index_range % 200 == 0:
                    print(f"start_range_survey(), creating range[{index_range:05}], {range.ip_range_start}")
                range_ping = IpRangePing(ip_survey=survey,ip_range=range)
                range_ping.save()
                index_range = index_range + 1
                if index_range > TOTAL_OBJECTS:
                    print(f"start_range_survey(), index_range > 10000, breaking")
                    outer_loop = False
                    get_range_chunks = False
                    break
            range_start = range_end
            range_end = range_end + SMALL_CHUNK_SIZE
            if ranges_returned < SMALL_CHUNK_SIZE:
                break
        return outer_loop, index_range 

    @shared_task(bind=True)
    def run(self, *args, **kwargs):
        print(f"start_range_survey(), self = {self}, kwargs = {kwargs}, creating survey")

        survey = IpRangeSurvey()
        survey.save()
        # Use the minus to be descending
        count_range_tracts = CountRangeTract.objects.order_by("-range_count")
        
        # Iterate through each of those counties and walk through all of the ranges
        outer_loop = True
        index_range = 0
        for tract_count in count_range_tracts:
            tract = tract_count.census_tract
            try:
                outer_loop, index_range = self._get_all_ranges(survey, tract, index_range)
            # Get all of the ranges from this census tract
            except (KeyError, DeIpRange.DoesNotExist):
                print(f"start_range_survey(), Exception, no ranges for tract = {tract.id}")
            if not outer_loop:
                break 

        survey.time_started = timezone.now()
        # Hack, should actually take the size from count_range_tracts
        survey.num_total_objects = TOTAL_OBJECTS 
        survey.save()
        print(f"start_range_survey(), created {survey.num_total_objects} ip ranges to ping")
