import logging
from django.shortcuts import render
from django.utils import timezone
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404, render
import django.dispatch

from rest_framework import viewsets
from rest_framework_gis import filters

from centralny.models import (
    IpRangePing,
    IpRangeSurvey
)

from mycalendar.models import (
    ScheduledIpRangeSurvey
)


class ScheduleSurveyDetailView(generic.DetailView):
    model = IpRangeSurvey
    template_name = "./schedsurv_create.html"

