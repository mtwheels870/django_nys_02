from django.utils.html import format_html

import django_tables2 as tables

from .models import TextFile, NerLabel

class TextFileTable(tables.Table):
    selection = tables.CheckBoxColumn(accessor="pk")
    class Meta:
        model = TextFile
        template_name = "django_tables2/bootstrap-responsive.html"
        # template_name = "django_tables2/bootstrap.html"
        fields = ["selection", "page_number", "file_name", "status", "time_edited", "time_labeled", "file_size"]

    def render_page_number(self, value, record):
        return format_html("<b>{}</b>", value)

    def render_time_labeled(self, value, record):
        string_value = value.strftime("%m%d %H%M")
        print(f"render_time(), value = {value}, string_value = {string_value}")
        return format_html("<b>{}</b>", string_value)

class NerLabelTable(tables.Table):
    selection = tables.CheckBoxColumn(accessor="pk")
    class Meta:
        model = NerLabel
        template_name = "django_tables2/bootstrap-responsive.html"
        # template_name = "django_tables2/bootstrap.html"
        fields = ["selection", "short_name", "description", "color"]

