from django.db import models

# Create your models here.
from django.contrib.gis.db import models

class Marker(models.Model):
    name = models.CharField(max_length=255)
    location = models.PointField()

    def __str__(self):
        return self.name

class CensusBorderCounty(models.Model):
    # Regular Django fields corresponding to the attributes in the
    # world borders shapefile.
    # COUNTY
    county_name = models.CharField(max_length=66)
    # STATE
    state_name = models.CharField(max_length=66)
    # COUNTY_1
    county_code = models.CharField(max_length=3)
    # STATE_1
    state_code = models.CharField(max_length=2)
    pop2000 = models.IntegerField("Population 2000")

    # GeoDjango-specific: a geometry field (MultiPolygonField)
    mpoly = models.MultiPolygonField()

    # Returns the string representation of the model.
    def __str__(self):
        return self.county_name
