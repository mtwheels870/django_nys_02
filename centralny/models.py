# Subclasses from django.db import models 
from django.forms import ModelForm
from django.utils import timezone
from django.contrib import admin
from django.contrib.gis.db import models

class Marker(models.Model):
    name = models.CharField(max_length=255)
    location = models.PointField()

    def __str__(self):
        return self.name

class County(models.Model):
    # COUNTY_1
    county_code = models.CharField(max_length=3, db_index=True)
    # COUNTY
    county_name = models.CharField(max_length=66)
    # STATE
    state_name = models.CharField(max_length=66)
    # STATE_1
    state_code = models.CharField(max_length=2)
    pop2000 = models.IntegerField("Population 2000")

    # GeoDjango-specific: a geometry field (MultiPolygonField)
    mpoly = models.MultiPolygonField()

    @property
    @admin.display(description="Population 2000", ordering="pop2000")
    def pop2000_formatted(self):
        return f"{self.pop2000:,}"

    # Returns the string representation of the model.
    def __str__(self):
        return self.county_name

class CensusTract(models.Model):
    # Should be county_ref or something (it's not an actual code)
    county_code = models.ForeignKey(County, on_delete=models.CASCADE)
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
    census_tract = models.ForeignKey(CensusTract, null=True, on_delete=models.SET_NULL)
    mpoint = models.MultiPointField(null=True)

    def __str__(self):
        return self.ip_range_start

class CountRangeTract(models.Model):
    census_tract = models.ForeignKey(CensusTract, on_delete=models.CASCADE)
    range_count = models.IntegerField(default=0)
    mpoint = models.MultiPointField(null=True)

    def __str__(self):
        return f"{census_tract}: {range_count:,}"

class CountRangeCounty(models.Model):
    # Should be county_ref or something (it's not an actual code)
    county_code = models.ForeignKey(County, on_delete=models.CASCADE)
    range_count = models.IntegerField(default=0)
    centroid = models.PointField(null=True)

    def __str__(self):
        return f"County: {county_code}"

class IpRangeSurvey(models.Model):
    time_created = models.DateTimeField(null=True, auto_now_add=True)
    time_approved = models.DateTimeField(null=True)
    survey_type = models.IntegerField(default=0)
    survey_name = models.CharField(max_length=20, null=True)
    num_ranges = models.IntegerField(null=True)

    def approve(self):
        self.time_approved = timezone.now()
        print(f"IpRangePing.approve(), time_approved = {self.time_approved}")
        self.save()

    def __str__(self):
        if self.survey_name:
            return f"Survey[{self.id}]: {self.survey_name}, {self.num_ranges} ranges"
        else:
            return f"Unnamed survey[{self.id}]: {self.num_ranges} ranges"

class IpRangePing(models.Model):
    # One survey can have multiple pings
    ip_survey = models.ForeignKey(IpRangeSurvey, null=True, on_delete=models.CASCADE)
    # THis is a 1-1 relationship: one range = one ping
    ip_range = models.ForeignKey(DeIpRange, on_delete=models.CASCADE)
    time_pinged = models.DateTimeField(null=True)
    addresses_pinged = models.BinaryField(max_length=32, default=b'\x00')
    addresses_responded = models.BinaryField(max_length=32, default=b'\x00')

    def __str__(self):
        return f"Range[{self.id}]: [{self.ip_range.ip_range_start},{self.ip_range.ip_range_end}], time_pinged = {self.time_pinged}"

class IpRangePingForm(ModelForm):
    class Meta:
        model = IpRangePing
        fields = ["time_pinged"]
