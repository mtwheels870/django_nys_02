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
from datetime import timedelta

from django.apps import AppConfig
from django.utils import timezone

from django_nys_02.celery import app as celery_app

from .tasks_periodic import check_new_surveys,PERIODIC_SECS 

class PowerScanConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'powerscan'

    def ready(self):
        """
        Docstring here
        """
        # Can't put this at the top-level (apps aren't ready yet)
        from django_celery_beat.models import PeriodicTask, IntervalSchedule

        celery_app.conf.beat_schedule = {
            'schedule-new-surveys' : {
                'task': 'check_new_surveys',
                'schedule': PERIODIC_SECS,
            },
        }

