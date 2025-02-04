import django_tables2 as tables

from .models import TextFile, NerLabel

class TextFileTable(tables.Table):
    selection = tables.CheckBoxColumn(accessor="pk")
    class Meta:
        model = TextFile
        template_name = "django_tables2/bootstrap-responsive.html"
        # template_name = "django_tables2/bootstrap.html"
        fields = ["selection", "page_number", "file_name", "status", "time_edited", "time_labeled", "file_size"]
    class render_file_name(self, value, record):
        return format_html("<b>{}</b>", value)

class NerLabelTable(tables.Table):
    selection = tables.CheckBoxColumn(accessor="pk")
    class Meta:
        model = NerLabel
        template_name = "django_tables2/bootstrap-responsive.html"
        # template_name = "django_tables2/bootstrap.html"
        fields = ["selection", "short_name", "description", "color"]

