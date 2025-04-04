import datetime
import pgtrigger
from django.db import models
from django.utils import timezone

from js_asset import JS

from colorfield.fields import ColorField

from django_nys_02.settings import PRODIGY_PORT

# from prose.models import Document
from django_prose_editor.fields import ProseEditorField

# Here, so we don't get circular imports
PRODIGY_URL_BASE = "http://18.208.200.162:" + str(PRODIGY_PORT)


#MAX_DISPLAY_LENGTH = 40
# ELLIPSIS = "..."
#INITIAL_PATH="/home/bitnami/cb"

#DJANGO_PROSE_EDITOR_PRESETS = {
#    "announcements": [
#        JS("prose-editors/announcements.js", {"defer": True}),
#    ],
#}

class TextFileStatus(models.Model):
    description = models.CharField(max_length=80) 
    def __str__(self):
        return self.description
        # return f"{self.id}: {self.description}"

class TextFolder(models.Model):
    folder_name = models.CharField("Folder name (original PDF file)", max_length=40)
    input_path = models.CharField("File Path (as string)", max_length=120)
    time_uploaded = models.DateTimeField(null=True)
    pages_original = models.IntegerField("Total pages in original", null=True)
    pages_db = models.IntegerField("Pages in database (to be labeled)", null=True)
    def __str__(self):
        return self.folder_name
        # return f"{self.id}: {self.folder_name} ({self.pages_db} in database)"

class TextFile(models.Model):
    folder = models.ForeignKey(TextFolder, on_delete=models.CASCADE)
    file_name = models.CharField("Name (windows / AWS)", max_length=80)
    page_number = models.IntegerField("Page Number")
    file_size = models.IntegerField("File Size (bytes)", null=True)
    status = models.ForeignKey(TextFileStatus, on_delete=models.CASCADE)
    prose_editor = ProseEditorField("text", preset="announcements")
    time_edited = models.DateTimeField(null=True)
    time_label_start = models.DateTimeField(null=True)
    label_batches_total = models.IntegerField("Total batchs to label", null=True)
    label_batches_done = models.IntegerField("Batchs actually labeled", null=True)
    prodigy_dataset = models.CharField("Prodigy DataSet Name", max_length=80)
    def __str__(self):
        return self.file_name

class NerLabel(models.Model):
    short_name = models.CharField("Short", max_length=20)
    description = models.CharField("Long", max_length=80)
    color = ColorField(default="#ff0000")
    def __str__(self):
        return self.short_name

#@pgtrigger.register(
#    pgtrigger.Trigger(
#        name='update_timestamp',
#        when=pgtrigger.Before,
#        operation=pgtrigger.Update,
#        fields=['field1', 'field2'],
#        func="NEW.updated_at = NOW(); RETURN NEW;",
#    )
#)
def mtw_dummy_function():
    print(f'mtw_dummy_function(), dummy function on trigger')
