from django.utils.html import format_html

import django_tables2 as tables

from .models import MmIpRange, IpRangeSurvey

DATE_TIME_FORMAT = "%m/%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"

MAX_STRING_LENGTH = 15
class MmIpRangeTable(tables.Table):
    class Meta:
        model = MmIpRange
        template_name = "django_tables2/bootstrap-responsive.html"
        empty_text = "(No IP ranges selected yet)"
        # template_name = "django_tables2/bootstrap.html"
        fields = ["ip_range_start", "company_name", "naics_code", "organization"]

    def render_company_name(self, value, record):
        abbreviated_string = value[:MAX_STRING_LENGTH]
        return format_html("{}", abbreviated_string)

    def render_organization(self, value, record):
        abbreviated_string = value[:MAX_STRING_LENGTH]
        return format_html("{}", abbreviated_string)

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
        return self._render_time(value)

    def _render_thousands(self, value):
        thousands = float(value) / 1000.0
        return f"{thousands:,}"

    def render_num_ranges_responded(self, value, record):
        return self._render_thousands(value)

    def render_num_total_ranges(self, value, record):
        return self._render_thousands(value)

class NonModelTable(tables.Table):
    name = tables.Column()
    surname = tables.Column()
    address = tables.Column()

    class Meta:
        template_name = "django_tables2/bootstrap4.html"

