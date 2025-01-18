from pathlib import Path

from django.utils import timezone
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.geos import Point, MultiPoint
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Centroid

from .models import (
    TextFileStatus, 
    TextFile)

class Loader():
    def __init__(self):
        self.counter = 0

    def run_status(self, verbose=True):
        status = ["uploaded", "editing", "labeled"]
        for single_status in status:
            ts = TextFileStatus(description=single_status)
            ts.save()
