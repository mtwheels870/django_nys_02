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

@celery_app.task(name='check_new_surveys', bind=True)
def check_new_surveys(self, arg1, arg2):
    print(f"check_new_surveys(), self: {self}, arg1 = {arg1}, arg2 = {arg2}")

