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

from django_nys_02.celery import app as celery_app, QUEUE_NAME

#from .models import IpRangeSurvey

PERIODIC_MINS = 2
PERIODIC_SECS = PERIODIC_MINS * 60

TIME_FORMAT2 = "%H:%M:%S"

ESTIMATED_RANGES_MIN = 4500

def _start_ping(survey_id):
    from .tasks import zmap_from_file

    #print(f"CPV.post(), start_ping...")
    async_result = zmap_from_file.apply_async(
        kwargs={"survey_id" : survey_id},
            #"ip_source_id": IP_RANGE_SOURCE },
        queue=QUEUE_NAME,
        routing_key='ping.tasks.zmap_from_file')
    return async_result

def _estimate_zmap_time(survey_id):
    from .models import IpSurveyState

    total_ranges = 0
    #print(f"_estimate_zmap_time(), survey_id = {survey_id}")
    for survey_state in IpSurveyState.objects.filter(survey__id=survey_id):
        state = survey_state.us_state
        estimated_ranges = state.estimated_ranges
        #print(f"       state: {state.state_abbrev}, count = {estimated_ranges:,}")
        total_ranges = total_ranges + estimated_ranges
    estimated_mins = total_ranges / ESTIMATED_RANGES_MIN 
    estimated_secs = estimated_mins * 60
    #first = "_estimate_zmap_time(), total_ranges = "
    #second = f"{total_ranges}, estimated m/s = {estimated_mins:.1f}/{estimated_secs:.0f}"
    #print(first + second)
    return estimated_mins, estimated_secs

def _start_tally(survey_id, metadata_file, delay_mins, delay_secs):
    from .tasks import tally_results

    now = timezone.now()
    formatted_now = now.strftime(TIME_FORMAT_STRING)
    delta = timedelta(seconds=delay_secs)
    tally_start = now + delta
    formatted_tally_start = tally_start.strftime(TIME_FORMAT_STRING)
    first = "CPV._start_tally(), calling tally_results (delayed), delay: "
    second = f"{delay_mins:.1f}m, now: {formatted_now}, tally_start: {formatted_tally_start}"
    print(first + second)
    async_result2 = tally_results.apply_async(
        countdown=delay_secs,
        #"ip_source_id": IP_RANGE_SOURCE,
        kwargs={"survey_id": survey_id,
            "metadata_file": metadata_file} )
    #celery_results_handler.save_pending(async_result2)
    return async_result2

def _add_surveys_to_queues():
    from .models import IpRangeSurvey

    now = timezone.now()
    now_string = now.strftime(TIME_FORMAT2 )

    back_one_period = timedelta(minutes=PERIODIC_MINS)
    window_begin = now - back_one_period
    begin_string = window_begin.strftime(TIME_FORMAT2 )

    forward_two_periods = timedelta(minutes=(2 * PERIODIC_MINS))
    window_end = now + forward_two_periods 
    end_string = window_end.strftime(TIME_FORMAT2 )

    # now_p1_string = now_plus_one.strftime(TIME_FORMAT2)
    print(f"TasksPeriodic._add_surveys_to_queues(), now = {now_string} window = [{begin_string},{end_string}]")
    upcoming_surveys = IpRangeSurvey.objects.filter(
            time_tally_stopped__isnull=True).filter(
            time_scheduled__gte=window_begin).filter(
            time_scheduled__lte=window_end)
    index = 0
    for survey in upcoming_surveys:
        print(f"survey[{index}]: {survey.id},{survey.name},{survey.time_scheduled}")
        index = index + 1
    f = lambda survey: survey.id
    survey_ids = [f(x) for x in upcoming_surveys]
    print(f"TasksPeriodic._as2qs(), survey_id = {survey_ids}")

@celery_app.task(name='check_new_surveys', bind=True)
def check_new_surveys(self):
    _add_surveys_to_queues()
# I think this name becomes the leading prefix on the database table names, etc.
