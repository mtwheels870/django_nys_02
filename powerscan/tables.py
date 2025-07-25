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
#import datetime

from datetime import timedelta

from celery.utils import iso8601

from django.utils.html import format_html

import django_tables2 as tables

from django_nys_02.celery import app as celery_app

from .models import MmIpRange, IpRangeSurvey

DATE_TIME_FORMAT = "%m/%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"

MAX_STRING_LENGTH = 15
class AggregationHistoryTable(tables.Table):
    selection = tables.CheckBoxColumn({"flavor" : "vanilla"}, accessor="id")
    id = tables.Column(verbose_name="Id")
    name = tables.Column(verbose_name="Name")
    agg_type = tables.Column(verbose_name="Agg Type")
    hosts_responded = tables.Column(verbose_name="Returns(K)")
    hosts_pinged = tables.Column(verbose_name="Total(K)")
    percentage = tables.Column(verbose_name="% Returned")

    class Meta:
        template_name = "django_tables2/bootstrap4.html"
        empty_text = "(No geography selected yet)"
        fields = ["selection", "id", "name", "hosts_responded", "hosts_pinged", "percentage"]
        exclude = ["agg_type"]

    def _render_thousands(self, value):
        """
        Docstring here
        """
        thousands = value / 1000.0
        return f"{thousands:.1f}"

    def render_hosts_responded(self, value, record):
        """
        Docstring here
        """
        return self._render_thousands(value)

    def render_hosts_pinged(self, value, record):
        """
        Docstring here
        """
        return self._render_thousands(value)

    def render_percentage(self, value, record):
        """
        Docstring here
        """
        percentage = value * 100.0
        return f"{percentage:.2f}"

class IpSurveyTable(tables.Table):
    selection = tables.CheckBoxColumn(accessor="pk")

    # Derived columns
    ranges = tables.Column(verbose_name="Ranges(k) [r p /%]")
    hosts = tables.Column(verbose_name="Hosts(k) [r p %]")
    class Meta:
        model = IpRangeSurvey
        template_name = "django_tables2/bootstrap-responsive.html"
        fields = ["selection", "id", "parent_survey_id", "name", "time_created", "time_scheduled", "time_ping_started",
            "time_tally_stopped", "ranges", "hosts"]

    def _render_time(self, value, include_date=False):
        """
        Docstring here
        """
        if not value:
            return_string = ""
        elif include_date:
            return_string = value.strftime(DATE_TIME_FORMAT)
        else:
            return_string = value.strftime(TIME_FORMAT)
        return return_string

    def render_time_created(self, value, record):
        """
        Docstring here
        """
        return self._render_time(value, include_date=True)

    def render_time_scheduled(self, value, record):
        """
        Docstring here
        """
        return self._render_time(value, include_date=True)

    def render_time_ping_started(self, value, record):
        """
        Docstring here
        """
        return self._render_time(value)

    def render_time_tally_stopped(self, value, record):
        """
        Docstring here
        """
        time_string = self._render_time(value)
        if value and record.time_ping_started:
            timedelta_secs = value - record.time_ping_started
            timedelta_mins = timedelta_secs.total_seconds() / 60
            return f"{time_string} ({timedelta_mins:.1f}m)"

        else:
            return time_string

    def _render_thousands(self, value):
        """
        Docstring here
        """
        thousands = float(value) / 1000.0
        #return f"{thousands:,}"
        return f"{thousands:.2f}"

#    def render_ranges(self, value, record):
#        return "Ranges"
#    def render_ranges_responded(self, value, record):
#        return self._render_thousands(value)

#    def render_ranges_pinged(self, value, record):
#        return self._render_thousands(value)

class CeleryTaskTable(tables.Table):
    selection = tables.CheckBoxColumn(accessor="uuid")
    uuid = tables.Column()
    status = tables.Column()
    survey_id = tables.Column()
    name = tables.Column()
    eta = tables.Column(verbose_name="Start Time")

    class Meta:
        template_name = "django_tables2/bootstrap4.html"

    def __init__(self, *args, **kwargs):
        """
        Docstring here
        """
        super().__init__(*args, **kwargs)

    def render_eta(self, value, record):
        """
        Docstring here
        """
        dt = iso8601.parse_iso8601(value)
        return dt.strftime(DATE_TIME_FORMAT)
