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
    county_code = models.CharField(max_length=3, primary_key=True)
    # STATE_1
    state_code = models.CharField(max_length=2)
    pop2000 = models.IntegerField("Population 2000")

    # GeoDjango-specific: a geometry field (MultiPolygonField)
    mpoly = models.MultiPolygonField()

    # Returns the string representation of the model.
    def __str__(self):
        return self.county_name

class CensusTract(models.Model):
    # Regular Django fields corresponding to the attributes in the
    # world borders shapefile.
    state_code = models.CharField(max_length=2)
    county_code = models.CharField(max_length=3)
    county = models.ForeignKey(CensusBorderCounty, on_delete=models.CASCADE)
    tract_id = models.CharField(max_length=6)
    short_name = models.CharField(max_length=7)
    long_name = models.CharField(max_length=20)
    interp_lat = models.CharField(max_length=11)
    interp_long = models.CharField(max_length=12)

    # GeoDjango-specific: a geometry field (MultiPolygonField)
    mpoly = models.MultiPolygonField()

    # Returns the string representation of the model.
    def __str__(self):
        return self.county_name
