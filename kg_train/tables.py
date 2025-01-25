import django_tables2 as tables

from .models import TextFile

class TextFileTable(tables.Table):
    selection = tables.CheckBoxColumn(accessor="pk")
    class Meta:
        model = TextFile
        template_name = "django_tables2/bootstrap-responsive.html"
        fields = ["selection", "page_number", "file_name", "file_size", "status"]
        per_page = 5
