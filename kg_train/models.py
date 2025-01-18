import datetime
from django.db import models
from django.utils import timezone

class TextFileStatus(models.Model):
    description = models.CharField(max_length=80) 

class TextFile(models.Model):
    file_name = models.CharField(max_length=80)
    date_uploaded = models.DateTimeField("date published")
    status = models.ForeignKey(TextFileStatus, on_delete=models.CASCADE)
    aws_file_path = models.CharField(max_length=120)
    def __str__(self):
        return self.file_name
