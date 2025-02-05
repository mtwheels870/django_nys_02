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
    "LOC" : "Named Location",
    "DATE" :"Absolute or relative dates or periods.", 
    "EVENT" : "Named political, military, social, or atmospheric event",
    "GPE" : "Countries, cities, states.",
    "ORG" : "Companies, agencies, institutions, etc.",
    "NORP" : "Nationalities, political, or religious groups.",
    "FORCE_MILITIA" : "Quasi-military forces (e.g. maritime militia)",
    "FORCE_NATL" : "Military forces (e.g. PLAN)",
    "FORCE_CIVIL" : "Civilian forces (e.g. fishing fleets, hydrocarbon exploration)",
    "BASE": "Military base, including ports, airstrips, etc.",
    "PERSON" : "People, usually political or military leaders",
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

    def load_single_label(self, verbose=True):
        ner_label = NerLabel(short_name="LOCATION",
            description="Geospatial location on the earth (point, line, polygon)")
        ner_label.save()

