import django_tables2 as tables

from .models import TextFile

class TextFileTable(tables.Table):
    class Meta:
        model = TextFile
        template_name = "django_tables2/bootstrap-responsive.html"
        fields = ["page_number", "file_name", "file_size", "status", "body"]
