from django.db import models as md1

# Create your models here.
from django.contrib.gis.db import models

class Marker(models.Model):
    name = models.CharField(max_length=255)
    location = models.PointField()

    def __str__(self):
        return self.name

class CensusBorderCounty(models.Model):
    # COUNTY_1
    county_code = models.CharField(max_length=3, primary_key=True)
    # COUNTY
    county_name = models.CharField(max_length=66)
    # STATE
    state_name = models.CharField(max_length=66)
    # STATE_1
    state_code = models.CharField(max_length=2)
    pop2000 = models.IntegerField("Population 2000")

    # GeoDjango-specific: a geometry field (MultiPolygonField)
    mpoly = models.MultiPolygonField()

    # Returns the string representation of the model.
    def __str__(self):
        return self.county_name

class CensusTract(models.Model):
    county_code = models.ForeignKey(CensusBorderCounty, on_delete=models.CASCADE)
    state_code = models.CharField(max_length=2)
    tract_id = models.CharField(max_length=6)
    short_name = models.CharField(max_length=7)
    long_name = models.CharField(max_length=20)
    interp_lat = models.CharField(max_length=11)
    interp_long = models.CharField(max_length=12)

    # GeoDjango-specific: a geometry field (MultiPolygonField)
    mpoly = models.MultiPolygonField()

    # Returns the string representation of the model.
    def __str__(self):
        return self.short_name

# pp = pulse_plus (in the original Digital Element Net Acuity DB 30
class DigitalElementIpRange(md1.Model):
    # Note, this is just for IPv4.  We might have to change for IPv6
    ip_range_start = models.CharField(max_length=20)
    ip_range_end = models.CharField(max_length=20)
    pp_city = models.CharField(max_length=20)
    pp_cxn_speed = models.CharField(max_length=20)
    pp_cxn_type = models.CharField(max_length=10)
    pp_latitude = models.CharField(max_length=20)
    pp_longitude = models.CharField(max_length=20)
    census_tract = models.ForeignKey(CensusTract, null=True, on_delete=models.SET_NULL)
    mpoly = models.MultiPolygonField()

    def __str__(self):
        return self.ip_range_start

