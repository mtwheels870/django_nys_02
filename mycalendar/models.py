# Subclasses from django.db import models 
from django.forms import ModelForm
from django.utils import timezone
from django.contrib import admin
from django.contrib.gis.db import models

from schedule.models import Calendar
from schedule.models import Event
from schedule.models import Rule

from centralny.models import DeIpRange

class ScheduledIpRangePing(models.Model):
    # THis is a 1-1 relationship: one range = one ping
    ip_range = models.ForeignKey(DeIpRange, on_delete=models.CASCADE)
    time_pinged = models.DateTimeField(null=True)
    addresses_pinged = models.BinaryField(max_length=32, default=b'\x00')
    addresses_responded = models.BinaryField(max_length=32, default=b'\x00')

    def __str__(self):
        return f"Ping: {self.id}, ip_range: {self.ip_range.ip_range_start}, time_pinged = {self.time_pinged}"


class ScheduledIpRangeSurvey(models.Model):
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE)
    # One to many.  An IpRangeSurvey can have multiple ranges
    ip_range_ping = models.ForeignKey(IpRangePing, on_delete=models.CASCADE)
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
            return f"Survey: {self.survey_name}, {self.num_ranges} ranges"
        else:
            return f"Unnamed survey, {self.num_ranges} ranges"

