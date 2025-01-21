import datetime
from django.db import models
from django.utils import timezone

class TextFileStatus(models.Model):
    description = models.CharField(max_length=80) 
    def __str__(self):
        return f"{self.id}: {self.description}"

class TextFile(models.Model):
    file_name = models.CharField(max_length=80)
    file = models.FileField(upload_to="uploads/")
    status = models.ForeignKey(TextFileStatus, on_delete=models.CASCADE)
    def __str__(self):
        return self.file_name
