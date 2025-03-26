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

from django_nys_02.celery import app as celery_app, QUEUE_NAME

from .models import IpRangeSurvey

TIME_FORMAT2 = "%H:%M:%S"

def _add_surveys_to_queues():
    now = timezone.now()
    now_string = now.strftime(TIME_FORMAT2 )
    print(f"TasksPeriodic._add_surveys_to_queues(), now = {now_string}")
    one_hour = timedelta(hours=1)
    now_plus_one = now + one_hour
    upcoming_surveys = IpRangeSurvey.objects.filter(
            time_tally_stopped__isnull=True).filter(time_scheduled__gte=now).filter(time_scheduled__lte=now_plus_one)
    f = lambda survey: survey.id
    survey_ids = [f(x) for x in upcoming_surveys]
    print(f"TasksPeriodic._as2qs(), survey_id = {survey_ids}")

@celery_app.task(name='check_new_surveys', bind=True)
def check_new_surveys(self, arg1, arg2):
    _add_surveys_to_queues()

