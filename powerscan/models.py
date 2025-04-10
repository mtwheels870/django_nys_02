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
    state_abbrev = models.CharField(max_length=2, null=True)
    state_name = models.CharField(max_length=100)
    interp_lat = models.CharField(max_length=11)
    interp_long = models.CharField(max_length=12)
    estimated_ranges = models.IntegerField(null=True)

    # GeoDjango-specific: a geometry field (MultiPolygonField)
    mpoly = models.MultiPolygonField()

    virtual = models.BooleanField(default=False)

    # Returns the string representation of the model.
    def __str__(self):
        return self.state_name

    def __hash__(self):
        return int(self.state_fp)

#state_fp = models.CharField(max_length=2, db_index=True)
class County(models.Model):
    geoid = models.CharField(max_length=5, db_index=True)
    # COUNTY_FP is not unique (across states)
    county_fp = models.CharField(max_length=3)
    # COUNTY
    county_name = models.CharField(max_length=100)
    # STATE_1
    us_state = models.ForeignKey(UsState, on_delete=models.CASCADE)

    interp_lat = models.CharField(max_length=11)
    interp_long = models.CharField(max_length=12)

    # GeoDjango-specific: a geometry field (MultiPolygonField)
    mpoly = models.MultiPolygonField()

    virtual = models.BooleanField(default=False)
    #@property
    #@admin.display(description="Population 2000", ordering="pop2000")
    #def pop2000_formatted(self):
    #    return f"{self.pop2000:,}"

    # Returns the string representation of the model.
    def __str__(self):
        return self.county_name

    def __hash__(self):
        return int(self.geoid)

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
    
    def __hash__(self):
        return int(self.tract_id)

#
# Power Scan, IP ranges (and aggregations)
#
class CountState(models.Model):
    us_state = models.ForeignKey(UsState, on_delete=models.CASCADE)
    range_count = models.IntegerField(default=0)
    hosts_potential = models.IntegerField(default=0)
    hosts_returned = models.IntegerField(default=0)
    centroid = models.PointField(null=True)

    class Meta:
        ordering = ["-range_count"]

    def __str__(self):
        return f"State: {self.us_state.state_name}"
#
# Power Scan, IP ranges (and aggregations)
#
class CountCounty(models.Model):
    # Should be county_ref or something (it's not an actual code)
    county = models.ForeignKey(County, on_delete=models.CASCADE)
    range_count = models.IntegerField(default=0)
    hosts_potential = models.IntegerField(default=0)
    hosts_returned = models.IntegerField(default=0)
    centroid = models.PointField(null=True)

    class Meta:
        ordering = ["-range_count"]

    def __str__(self):
        return f"County: {self.county.county_fp}"

# pp = pulse_plus (in the original Digital Element Net Acuity DB 30

class CountTract(models.Model):
    census_tract = models.ForeignKey(CensusTract, on_delete=models.CASCADE)
    range_count = models.IntegerField(default=0)
    hosts_potential = models.IntegerField(default=0)
    hosts_returned = models.IntegerField(default=0)
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
    county = models.ForeignKey(County, null=True, on_delete=models.CASCADE)
    mpoint = models.MultiPointField(null=True)

    def __str__(self):
        return f"{self.ip_network}"

#
# Classes to work with celery workers and do a scan
#
class IpRangeSurvey(models.Model):
    time_created = models.DateTimeField(auto_now_add=True, verbose_name="Created (UTC)")
    name = models.CharField(max_length=40, null=True)

    time_scheduled = models.DateTimeField(null=True, verbose_name="Scheduled")
    time_whitelist_created = models.DateTimeField(null=True)
    time_whitelist_started = models.DateTimeField(null=True)

    # First celery worker sets this (effectively the lock)
    time_ping_started = models.DateTimeField(null=True, verbose_name="Ping Started")
    time_ping_stopped = models.DateTimeField(null=True)

    time_tally_started = models.DateTimeField(null=True)
    time_tally_stopped = models.DateTimeField(null=True, verbose_name="Results Processed")

    num_total_ranges = models.IntegerField(default=0, verbose_name="Ranges(K) Pinged")
    num_ranges_responded = models.IntegerField(default=0, verbose_name="Responded(K)")
    # Should this be a ForeignKey (back to this model?)
    parent_survey_id = models.BigIntegerField(null=True, verbose_name="Copies")

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
        first = f"Range[{self.id}]: [{self.ip_range.ip_range_start},{self.ip_range.ip_range_end}], "
        second = f"time_pinged = {self.time_pinged}"
        return first + second

class IpSurveyState(models.Model):
    survey = models.ForeignKey(IpRangeSurvey, on_delete=models.CASCADE)
    us_state = models.ForeignKey(UsState, on_delete=models.CASCADE)
    num_ranges_pinged = models.IntegerField(default=0)
    num_ranges_responded = models.IntegerField(default=0)
    def __str__(self):
        return f"Survey results for state: {self.us_state.state_abbrev}"

class IpSurveyCounty(models.Model):
    survey = models.ForeignKey(IpRangeSurvey, on_delete=models.CASCADE)
    county = models.ForeignKey(County, on_delete=models.CASCADE)
    num_ranges_pinged = models.IntegerField(default=0)
    num_ranges_responded = models.IntegerField(default=0)
    def __str__(self):
        return f"Survey results for county: {self.county.county_fp}"

class IpSurveyTract(models.Model):
    survey = models.ForeignKey(IpRangeSurvey, on_delete=models.CASCADE)
    tract = models.ForeignKey(CensusTract, on_delete=models.CASCADE)
    num_ranges_pinged = models.IntegerField(default=0)
    num_ranges_responded = models.IntegerField(default=0)
    def __str__(self):
        return f"Survey results for tract: {self.tract.tract_id}"

class MilitaryBase(models.Model):
    # Should be county_ref or something (it's not an actual code)
    base_id = models.IntegerField(default=0, db_index=True)
    name = models.CharField(max_length=30)
    point = models.PointField(null=True)

    def __str__(self):
        return {self.name.county_fp}

class DebugPowerScan(models.Model):
    profile_name =  models.CharField(max_length=30, default="Stuff")
    whitelist = models.BooleanField(default=False)
    zmap = models.BooleanField(default=False)
    tally_results = models.BooleanField(default=False)
    scheduler = models.BooleanField(default=False)
    task_queues = models.BooleanField(default=False)
    calculate_baseline = models.BooleanField(default=False)

    def __str__(self):
        first = f"profile[{self.profile_name}, whitelist = {self.whitelist}, zmap = {self.zmap}, "
        second = f"     tally_results = {self.tally_results}, scheduler = {self.scheduler}\n"
        third = f"calculate_baseline = {self.calculate_baseline}"
        return first + second + third

#class WorkerLock(models.Model):
#    purpose = models.CharField(max_length=12)
#    time_created = models.DateTimeField(auto_now_add=True)
#    time_started = models.DateTimeField(null=True)
