from pathlib import Path

from django.utils import timezone
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.geos import Point, MultiPoint
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Centroid

from .models import (
    TextFileStatus, 
    TextFile,
    NerLabel)

label_dictionary = {
    "PERSON":"People, including fictional.",
    "NORP" : "Nationalities or religious or political groups.",
    "FAC" : "Buildings, airports, highways, bridges, etc.",
    "ORG" : "Companies, agencies, institutions, etc.",
    "GPE" : "Countries, cities, states.",
    "EVENT" : "Named hurricanes, battles, wars, sports events, etc.",
    "DATE": "Absolute or relative dates or periods.",
    "TIME": "Times smaller than a day.",
    "QUANTITY": "Measurements, as of weight or distance.",
    "ORDINAL": "first, second, etc.",
    "CARDINAL": "one, two, three...",
    "MILITARY": "Military forces, such as PLAN",
    "CIVILIAN": "Civil forces, such as maritime militia, fishing fleets",
}

class Loader():
    def __init__(self):
        self.counter = 0

    def run_status(self, verbose=True):
        status = ["uploaded", "editing", "labeled"]
        for single_status in status:
            ts = TextFileStatus(description=single_status)
            ts.save()

    def create_labels(self, verbose=True):
        for _, (key, value) in enumerate(label_dictionary.items()):
            print(f"create_labels(), {key} = {value}")
            ner_label = NerLabel(short_name=key, description=value)
            ner_label.save()

    def load_single_label(self, verbose=True);
        ner_label = NerLabel(short_name="LOCATION",
            description="Geospatial location on the earth (point, line, polygon)")
        ner_label.save()

