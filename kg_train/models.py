import datetime
from django.db import models
from django.utils import timezone

from colorfield.fields import ColorField

from prose.models import Document

MAX_DISPLAY_LENGTH = 40
ELLIPSIS = "..."
INITIAL_PATH="/home/bitnami/cb"

class TextFileStatus(models.Model):
    description = models.CharField(max_length=80) 
    def __str__(self):
        return f"{self.id}: {self.description}"

class TextFolder(models.Model):
    file_name = models.CharField("Name (windows / AWS)", max_length=80)
    folder = models.FilePathField(path=INITIAL_PATH, allow_folders=True)
    time_uploaded = models.DateTimeField(null=True)
    total_pages = models.IntegerField("Total pages in original", null=True)

class TextFile(models.Model):
    folder = models.ForeignKey(TextFolder, on_delete=models.CASCADE)
    file_name = models.CharField("Name (windows / AWS)", max_length=80)
    file = models.FileField(upload_to="uploads/")
    file_size = models.IntegerField("File Size (bytes)", null=True)
    status = models.ForeignKey(TextFileStatus, on_delete=models.CASCADE)
    body = models.OneToOneField(Document, on_delete=models.CASCADE, null=True)
    short_name = None

    @property
    def display_name(self):
        if self.short_name:
            return self.short_name
        if len(self.file_name) > MAX_DISPLAY_LENGTH:
            self.short_name = self.file_name[:MAX_DISPLAY_LENGTH] + ELLIPSIS 
            return self.short_name
        return self.file_name

    
    def __str__(self):
        return self.display_name()

class NerLabel(models.Model):
    short_name = models.CharField("Short", max_length=10)
    description = models.CharField("Long", max_length=80)
    color = ColorField(default="#ff0000")
    def __str__(self):
        return self.short_name
