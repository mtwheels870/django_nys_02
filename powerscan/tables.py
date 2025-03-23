from django.utils.html import format_html

import django_tables2 as tables

from .models import MmIpRange, IpRangeSurvey

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
        fields = ["selection", "id", "time_created", "states"]
        #print(f"CPV.get_context_data() 5, (after setting initial) field_survey_id = {field_survey_id}")

    def render_states(self, value, record):
        survey_states = record.ipsurveystate_set()
        print(f"IST.render_states(), survey_states = {survey_states}")
        return "a, b, c"

    def render_time(self, value):
        if not value:
            return ""
        else: 
            return value.strftime(TIME_FORMAT)

    def render_time_created(self, value, record):
        return self.render_time(value)
#
#    def render_time_ping_started(self, value, record):
#        return self.render_time(value)
#
#    def render_time_rally_stopped(self, value, record):
#        return self.render_time(value)

#    def render_num_total_ranges(self, value, record):
#        return "{value:,}"
