# Subclasses from django.db import models 
from django.forms import ModelForm
from django.utils import timezone
from django.contrib import admin
from django.contrib.gis.db import models


#
# Straight Geo, right from US Census
#
# https://www.census.gov/cgi-bin/geo/shapefiles/index.php
    
class UsState(models.Model):
    # COUNTY_1
    state_fp = models.CharField(max_length=2, db_index=True)
    state_name = models.CharField(max_length=100)
    interp_lat = models.CharField(max_length=11)
    interp_long = models.CharField(max_length=12)

    # GeoDjango-specific: a geometry field (MultiPolygonField)
    mpoly = models.MultiPolygonField()

    # Returns the string representation of the model.
    def __str__(self):
        return self.state_name

#state_fp = models.CharField(max_length=2, db_index=True)
class County(models.Model):
    geoid = models.CharField(max_length=5, db_index=True)
    # COUNTY_1
    county_fp = models.CharField(max_length=3)
    # COUNTY
    county_name = models.CharField(max_length=100)
    # STATE_1
    us_state = models.ForeignKey(UsState, on_delete=models.CASCADE)

    interp_lat = models.CharField(max_length=11)
    interp_long = models.CharField(max_length=12)

    # GeoDjango-specific: a geometry field (MultiPolygonField)
    mpoly = models.MultiPolygonField()

    #@property
    #@admin.display(description="Population 2000", ordering="pop2000")
    #def pop2000_formatted(self):
    #    return f"{self.pop2000:,}"

    # Returns the string representation of the model.
    def __str__(self):
        return self.county_name

class CensusTract(models.Model):
    county = models.ForeignKey(County, on_delete=models.CASCADE)
    tract_id = models.CharField(max_length=6)
    name = models.CharField(max_length=7)
    interp_lat = models.CharField(max_length=11, null=True)
    interp_long = models.CharField(max_length=12, null=True)
    geoid = models.CharField(max_length=11, db_index=True)

    # GeoDjango-specific: a geometry field (MultiPolygonField)
    mpoly = models.MultiPolygonField()

    # Returns the string representation of the model.
    def __str__(self):
        return self.name

#
# Power Scan, IP ranges (and aggregations)
#
class CountState(models.Model):
    us_state = models.ForeignKey(UsState, on_delete=models.CASCADE)
    range_count = models.IntegerField(default=0)
    centroid = models.PointField(null=True)

    class Meta:
        ordering = ["-range_count"]

    def __str__(self):
        return f"County: {self.county.county_fp}"
#
# Power Scan, IP ranges (and aggregations)
#
class CountCounty(models.Model):
    # Should be county_ref or something (it's not an actual code)
    county = models.ForeignKey(County, on_delete=models.CASCADE)
    range_count = models.IntegerField(default=0)
    centroid = models.PointField(null=True)

    class Meta:
        ordering = ["-range_count"]

    def __str__(self):
        return f"County: {self.county.county_fp}"

# pp = pulse_plus (in the original Digital Element Net Acuity DB 30

class CountTract(models.Model):
    census_tract = models.ForeignKey(CensusTract, on_delete=models.CASCADE)
    range_count = models.IntegerField(default=0)
    mpoint = models.MultiPointField(null=True)

    class Meta:
        ordering = ["-range_count"]

    def __str__(self):
        return f"{self.census_tract}: {self.range_count:,}"


class MmIpRange(models.Model):
    ip_network = models.CharField("IP Network", max_length=20)
    geoname_id = models.CharField("GeoNameId", max_length=10)
    zip_code = models.CharField("Zip_Code", null=True, max_length=10)
    mm_latitude = models.CharField(max_length=20)
    mm_longitude = models.CharField(max_length=20)
    accuracy = models.IntegerField()
    census_tract = models.ForeignKey(CensusTract, null=True, on_delete=models.CASCADE)
    mpoint = models.MultiPointField(null=True)

    def __str__(self):
        return f"{self.geoname_id}: {self.ip_network}"

#
# Classes to work with celery workers and do a scan
#
class WorkerLock(models.Model):
    purpose = models.CharField(max_length=12)
    time_created = models.DateTimeField(auto_now_add=True)
    time_started = models.DateTimeField(null=True)

class IpRangeSurvey(models.Model):
    time_created = models.DateTimeField(auto_now_add=True)

    # First celery worker sets this (effectively the lock)
    time_started = models.DateTimeField(null=True)

    # After a successful ping campaign, celery worker will set time stopped and num objects
    time_stopped = models.DateTimeField(null=True)
    num_total_ranges = models.IntegerField(default=0)

    def __str__(self):
        return f"Survey[{self.id}]"

class IpRangePing(models.Model):
    # One survey can have multiple pings
    ip_survey = models.ForeignKey(IpRangeSurvey, null=True, on_delete=models.CASCADE)
    # THis is a 1-1 relationship: one range = one ping
    ip_range = models.ForeignKey(MmIpRange, on_delete=models.CASCADE)
    time_pinged = models.DateTimeField(null=True)
    num_ranges_pinged = models.IntegerField(default=0)
    num_ranges_responded = models.IntegerField(default=0)

    def __str__(self):
        return f"Range[{self.id}]: [{self.ip_range.ip_range_start},{self.ip_range.ip_range_end}], time_pinged = {self.time_pinged}"

#
# Unused
#
class DeIpRange(models.Model):
    # Note, this is just for IPv4.  We might have to change for IPv6
    ip_range_start = models.CharField("IP Start", max_length=20)
    ip_range_end = models.CharField("IP End", max_length=20)
    pp_cxn_speed = models.CharField(max_length=20)
    pp_cxn_type = models.CharField(max_length=10)
    pp_latitude = models.CharField(max_length=20)
    pp_longitude = models.CharField(max_length=20)
    company_name = models.CharField(max_length=60, null=True)
    naics_code = models.CharField(max_length=8, null=True)
    organization = models.CharField(max_length=80, null=True)
    srs_company_name = models.CharField(max_length=60, null=True)
    srs_issuer_id = models.CharField(max_length=10, null=True)
    srs_latitude = models.CharField(max_length=20, null=True)
    srs_longitude = models.CharField(max_length=20, null=True)
    srs_strength = models.CharField(max_length=3, null=True)
    census_tract = models.ForeignKey(CensusTract, null=True, on_delete=models.CASCADE)
    mpoint = models.MultiPointField(null=True)

    def __str__(self):
        return self.ip_range_start
