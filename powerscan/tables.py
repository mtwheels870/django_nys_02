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
    selection = tables.CheckBoxColumn(accessor="survey_id")
    # survey_id = tables.Column(verbose_name="Survey_Id")
    # ping_time = tables.Column(verbose_name="Ping Time (UTC)")
    name = tables.Column(verbose_name="Name")
    hosts_responded = tables.Column(verbose_name="Returns(K)")
    hosts_pinged = tables.Column(verbose_name="Total(K)")
    percentage = tables.Column(verbose_name="% Returned")

    class Meta:
        template_name = "django_tables2/bootstrap4.html"
        # model = MmIpRange
        empty_text = "(No geography selected yet)"
        # template_name = "django_tables2/bootstrap.html"
        # This only works with models
        # fields = "__all__"
        fields = ["selection", "name", "hosts_responded", "hosts_pinged", "percentage"]

#    def render_ping_time(self, value, record):
#        return value.strftime(TIME_FORMAT)

    def _render_thousands(self, value):
        thousands = value / 1000.0
        return f"{thousands:.2f}"

    def render_hosts_responded(self, value, record):
        return self._render_thousands(value)

    def render_hosts_pinged(self, value, record):
        return self._render_thousands(value)

    def render_percentage(self, value, record):
        return f"{value:.2f}"

class IpSurveyTable(tables.Table):
    selection = tables.CheckBoxColumn(accessor="pk")
    class Meta:
        model = IpRangeSurvey
        template_name = "django_tables2/bootstrap-responsive.html"
        # template_name = "django_tables2/bootstrap.html"
        # fields = ["selection", "time_created", "time_ping_started", "time_tally_stopped", "num_total_ranges"]
        fields = ["selection", "id", "parent_survey_id", "name", "time_created", "time_scheduled", "time_ping_started",
            "time_tally_stopped", "num_ranges_responded", "num_total_ranges"]

    def _render_time(self, value, include_date=False):
        if not value:
            return_string = ""
        elif include_date:
            return_string = value.strftime(DATE_TIME_FORMAT)
        else:
            return_string = value.strftime(TIME_FORMAT)
        return return_string

    def render_time_created(self, value, record):
        return self._render_time(value, include_date=True)

    def render_time_scheduled(self, value, record):
        return self._render_time(value)

    def render_time_ping_started(self, value, record):
        return self._render_time(value)

    def render_time_tally_stopped(self, value, record):
        time_string = self._render_time(value)
        if value and record.time_ping_started:
            timedelta_secs = value - record.time_ping_started
            timedelta_mins = timedelta_secs.total_seconds() / 60
            return f"{time_string} ({timedelta_mins:.1f}m)"

        else:
            return time_string

    def _render_thousands(self, value):
        thousands = float(value) / 1000.0
        #return f"{thousands:,}"
        return f"{thousands:.2f}"

    def render_num_ranges_responded(self, value, record):
        return self._render_thousands(value)

    def render_num_total_ranges(self, value, record):
        return self._render_thousands(value)

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
        super().__init__(*args, **kwargs)

    def render_eta(self, value, record):
        dt = iso8601.parse_iso8601(value)
        return dt.strftime(DATE_TIME_FORMAT)
