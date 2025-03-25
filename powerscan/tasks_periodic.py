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

# This could actually be running (although we don't see the print message), but we never declared the test.s() 
# routing.  Don't think so.  Not set up
@celery_app.after_finalize.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    print(f"setup_periodic_tasks(), sender = {sender}, kwargs = {kwargs}")
    sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')

    # Executes every Monday morning at 7:30 a.m.
    sender.add_periodic_task(
        crontab(minute=00), test.s(':00 minute task'),
        crontab(minute=30), test.s(':30 minute task'),
    )
