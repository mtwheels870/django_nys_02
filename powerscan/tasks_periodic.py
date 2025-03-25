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

class SurveyScheduler(Task):
    def __init__(self):
        self.stuff = "Yellow"

    @celery_app.task(name='blah_de_blah', bind=True)
    def periodic_task_to_do(self, arg1, arg2):
        print(f"periodic_task_to_do(), self: {self}, arg1 = {arg1}, arg2 = {arg2}")

