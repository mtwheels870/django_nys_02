#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, PINP01NT, LLC
#
# https://pinp01nt.com/
#
# All rights reserved.

"""
Docstring here

Authors: Michael T. Wheeler (mike@pinp01nt.com)

"""
# MTW: Celery tasks.  Autodiscovered, see celery.py
# app.autodiscover_tasks()

# General Python
import sys
import os
import datetime
from datetime import timedelta

# Celery / Django
import celery
from celery import shared_task, Task, group, chain
from celery.app import control 

from django.utils import timezone

from django_nys_02.settings import CELERY_QUEUE
from django_nys_02.celery import app as celery_app

from .survey_util import SurveyUtil

#from .models import IpRangeSurvey

# Celery beat will wake up on this value, check for new jobs
PERIODIC_MINS = 2
PERIODIC_SECS = PERIODIC_MINS * 60

TIME_FORMAT2 = "%H:%M:%S"

ESTIMATED_BASE_MIN = 2.0
# ESTIMATED_RANGES_PER_MIN = 4500
ESTIMATED_RANGES_PER_MIN = 4000


@celery_app.task
def _build_clone_details(survey_id, parent_survey_id):
    """
    Docstring here
    """
    # Clone all of the database stuff
    SurveyUtil.copy_geography(survey_id, parent_survey_id)

    # Set up the file structure
    SurveyUtil.link_file_string(survey_id, parent_survey_id)
    return survey_id

#
# This needs to be a shared_task b/c it can be called from the views_ping (ping immediately) or 
# from the scheduler (celery beat)
#
@shared_task(bind=True)
def start_ping(self, *args, **kwargs):
    """
    Docstring here
    """
    from .tasks import zmap_from_file
    from .models import IpRangeSurvey

    #print(f"start_ping(), args = {args}, kwargs = {kwargs}")
    if "survey_id" not in kwargs:
        print(f"start_ping(), args = {args}, kwargs = {kwargs}")
        return
    survey_id = kwargs["survey_id"]
    zmap_delay_secs = int(kwargs["delay_secs"])
    print(f"Task.start_ping({survey_id}), zmap_delay_secs = {zmap_delay_secs}")

    # We can use these estimates in either case (it's just a clone)
    tally_delay_mins, tally_delay_secs = _estimate_zmap_time(survey_id)

    survey = IpRangeSurvey.objects.get(pk=survey_id)
    parent_survey_id = survey.parent_survey_id
    if not parent_survey_id:
        # print(f"Task.start_ping(), after estimate, tally_delay m/s = {tally_delay_mins:.1f}/{tally_delay_secs:.0f}")
        parent_survey_id_string = "0"
        chain01 = chain(zmap_from_file.s(survey_id).set(countdown=zmap_delay_secs),
                _start_tally.s(survey_id, tally_delay_mins, tally_delay_secs))
        async_result = chain01.run()
    else:
        # Zmap gets passed the two args from the build_clone_details
        chain02 = chain(_build_clone_details.s(survey_id, parent_survey_id),
                zmap_from_file.s().set(countdown=zmap_delay_secs),
                _start_tally.s(survey_id, tally_delay_mins, tally_delay_secs))
        async_result = chain02.run()
    return async_result

def _estimate_zmap_time(survey_id):
    """
    Docstring here
    """
    from .models import IpSurveyState

    total_ranges = 0
    for survey_state in IpSurveyState.objects.filter(survey__id=survey_id):
        state = survey_state.us_state
        estimated_ranges = state.estimated_ranges
        #print(f"       state: {state.state_abbrev}, count = {estimated_ranges:,}")
        total_ranges = total_ranges + estimated_ranges

    # Calculate when we *think* the zmap job should be done, start the tally
    estimated_mins = ESTIMATED_BASE_MIN + (total_ranges / ESTIMATED_RANGES_PER_MIN)
    estimated_secs = estimated_mins * 60
    return estimated_mins, estimated_secs

@celery_app.task
def _start_tally(metadata_file, survey_id, delay_mins, delay_secs):
    """
    Docstring here
    """
    from .tasks import tally_results

    if not metadata_file:
        print(f"TasksPeriodic._start_tally(), no metadata_file, bailing...")
        return None
    now = timezone.now()
    formatted_now = now.strftime(TIME_FORMAT2)
    delta = timedelta(seconds=delay_secs)
    tally_start = now + delta
    formatted_tally_start = tally_start.strftime(TIME_FORMAT2)
    first = f"TasksPeriodic._start_tally({survey_id}), "
    second = f"+{delay_mins:.1f}m, start: {formatted_tally_start}"
    print(first + second)
    retry_count = 0
    async_result2 = tally_results.apply_async([metadata_file, survey_id, retry_count], countdown=delay_secs)
    return async_result2

def _task_check_args(task, task_name, args, index):
    """
    Docstring here
    """
    required_length = index + 1
    if len(args) < required_length:
        print(f"_task_check_args(), task = {task_name}, index = {index}, args = {args}")
        print(f"          task = {task}")
        return None
    survey_id = args[index]
    return survey_id 

def _task_check_kwargs(task_name, kwargs):
    """
    Docstring here
    """
    if "survey_id" in kwargs:
        survey_id = kwargs["survey_id"]
        return survey_id
    return None

def _get_task_survey_id(task):
    """
    Docstring here
    """
    if not "kwargs" in task:
        if "request" in task:
            request = task["request"]
            if "name" in request:
                task_name = request["name"]
                match task_name:
                    case "powerscan.tasks.zmap_from_file":
                        survey_id = _task_check_args(task, task_name, request["args"], 0)
                        if survey_id:
                            return survey_id, "zmap_from_file"
                        else:
                            return None, None
                    case "powerscan.tasks.tally_results":
                        # This is messed up.  We can get tally_results with args[] or with kwargs[] (probably b/c of 
                        # the ping immediately logic (shared task) and the delay stuff
                        args = request["args"]
                        if len(args) > 0:
                            survey_id = _task_check_args(task, task_name, request["args"], 1)
                        else:
                            survey_id = _task_check_kwargs(task_name, request["kwargs"])
                        if survey_id:
                            return survey_id, "tally_results"
                        else:
                            return None, None
                    case "powerscan.tasks_periodic.start_ping":
                        survey_id = _task_check_kwargs(task_name, request["kwargs"])
                        if survey_id:
                            return survey_id, "start_ping"
                        else:
                            return None, None
                    case _:
                        return None, None
        return None, None
    kwargs = task["kwargs"]
    if "survey_id" in kwargs:
        survey_id = kwargs["survey_id"]
        type = task["type"]
        print(f"      task[kwargs][survey_id]: {survey_id} = {type}")
        return survey_id, "task_here"
    else:
        return None, None

def _scheduled_active_surveys(debug_tasks_queues):
    """
    Docstring here
    """
    running_surveys = {}
    inspect = celery_app.control.inspect()

    tasks_active = inspect.active()
    if tasks_active:
        # tasks_active is a dict!
        for index, (key, value) in enumerate(tasks_active.items()):
            # print(f"CPV.g_tasks(), active[{index}]: {key} = {value}")
            for task in value:
                survey_id, task = _get_task_survey_id(task)
                if survey_id:
                    running_surveys[survey_id] = task
                if debug_tasks_queues:
                    print(f"_s_a_s(active), task = {task}, survey_id = {survey_id}")
                    # .append(survey_id)

    tasks_scheduled = inspect.scheduled()
    if tasks_scheduled:
        for index, (key, value) in enumerate(tasks_scheduled.items()):
            # print(f"CPV.g_tasks(), active[{index}]: {key} = {value}")
            for task in value:
                survey_id, task = _get_task_survey_id(task)
                if survey_id:
                    running_surveys[survey_id] = task
                    # running_surveys.append(survey_id)
                if debug_tasks_queues:
                    print(f"_s_a_s(scheduled), task = {task}, survey_id = {survey_id}")
    return running_surveys

def _schedule_surveys_tasks(upcoming_surveys, debug_tasks_queues):
    """
    Docstring here
    """
    index = 0
    running_survey_ids = _scheduled_active_surveys(debug_tasks_queues)
    now = timezone.now()
    for survey in upcoming_surveys:
        survey_id = survey.id
        if debug_tasks_queues:
            print(f"survey[{index}]: checking {survey_id}...")
        if survey_id in running_survey_ids:
            task = running_survey_ids[survey_id]
            print(f"survey[{index}]: {survey_id} already has a task: {task}")
        else:
            t_s = survey.time_scheduled.strftime(TIME_FORMAT2 )
            now_f = now.strftime(TIME_FORMAT2)
            if survey.time_scheduled < now:
                delay_secs = 0
            else:
                time_difference = survey.time_scheduled - now       # time diff in microseconds
                delay_secs = time_difference.seconds 
            # delay_secs = 0 if time_difference.seconds < 0 else time_difference.seconds
            print(f"Scheduling: survey[{index}]: {survey.id}, scheduled: {t_s}, now: {now_f}")
            print(f"    queue = {CELERY_QUEUE}, delay_secs = {delay_secs:.1f}")
            # We're not an apply_async here, so the calling signature is different
            async_result = start_ping(
                survey_id=survey.id, delay_secs=delay_secs,
                queue=CELERY_QUEUE,
                routing_key='ping.tasks.start_ping')
            #print(f"    async_result = {async_result}")
        index = index + 1

def _add_surveys_to_queues(debug_scheduler, debug_tasks_queues):
    """
    Docstring here
    """
    from .models import IpRangeSurvey

    now = timezone.now()
    now_string = now.strftime(TIME_FORMAT2 )

    back_one_period = timedelta(minutes=PERIODIC_MINS)
    window_begin = now - back_one_period
    begin_string = window_begin.strftime(TIME_FORMAT2 )

    forward_two_periods = timedelta(minutes=(2 * PERIODIC_MINS))
    window_end = now + forward_two_periods 
    end_string = window_end.strftime(TIME_FORMAT2 )

    # Take surveys whose ping has not been started and whose time_scheduled is in our window
    upcoming_surveys = IpRangeSurvey.objects.filter(
            time_ping_started__isnull=True).filter(
            time_scheduled__gte=window_begin).filter(
            time_scheduled__lte=window_end)
    num_surveys = len(upcoming_surveys)
    if num_surveys > 0 or debug_scheduler:
        print(f"TasksPeriodic.add_to_q(), [{begin_string}...{now_string}...{end_string}]")
        _schedule_surveys_tasks(upcoming_surveys, debug_tasks_queues)

@celery_app.task(name='check_new_surveys', bind=True)
def check_new_surveys(self):
    """
    Docstring here
    """
    from .models import DebugPowerScan
    from .tasks import DEBUG_ID

    debug = DebugPowerScan.objects.get(pk=DEBUG_ID)
    _add_surveys_to_queues(debug.scheduler, debug.task_queues)

