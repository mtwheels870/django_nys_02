import django_tables2 as tables

from .models import TextFile, NerLabel
from .models import PrdgyDataset

class DatasetTable(tables.Table):
    selection = tables.CheckBoxColumn(accessor="pk")
    class Meta:
        model = PrdgyDataset
        template_name = "django_tables2/bootstrap-responsive.html"
        # template_name = "django_tables2/bootstrap.html"
        fields = ["selection", "name", "created", "meta", "session" ]
