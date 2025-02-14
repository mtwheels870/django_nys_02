from django.utils.html import format_html

import django_tables2 as tables

from .models import DeIpRange

MAX_STRING_LENGTH = 15
class DeIpRangeTable(tables.Table):
    class Meta:
        model = DeIpRange
        template_name = "django_tables2/bootstrap-responsive.html"
        empty_text = "No IP ranges selected yet"
        # template_name = "django_tables2/bootstrap.html"
        fields = ["ip_range_start", "company_name", "naics_code", "organization"]

    def render_company_name(self, value, record):
        abbreviated_string = value[:MAX_STRING_LENGTH]
        return format_html("{}", abbreviated_string)

    def render_organization(self, value, record):
        abbreviated_string = value[:MAX_STRING_LENGTH]
        return format_html("{}", abbreviated_string)

