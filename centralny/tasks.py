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

@shared_task(bind=True)
def start_range_survey(self, *args, **kwargs):
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
        # Get all of the ranges from this census tract
            ip_ranges = tract.deiprange_set(pk=tract.id)
        except (KeyError, DeIpRange.DoesNotExist):
            print(f"start_range_survey(), Exception, no ranges for tract = {tract.id}")
        else:
            selected_choice = question.choice_set.get(pk=request.POST["choice"])
            for range in ip_ranges:
                if index_range < 10:
                    print(f"start_range_survey(), creating range[{index_range:05}], {range.ip_range.ip_range_start}")
                range_ping = IpRangePing(ip_survey=survey,ip_range=range)
                range_ping.save()
                index_range = index_range + 1
                if index_range > 10000:
                    outer_loop = False
                    break
        if not outer_loop:
            break 

    survey.time_started = timezone.now()
    survey.save()
            
