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

class ScheduleSurveyDetailView(generic.DetailView):
    model = ScheduledIpRangeSurvey
    template_name = "./schedsurv_detail.html"

    def get_queryset(self):
        """ Excludes any Qs that aren't published, yet.  """
        return ScheduledIpRangeSurvey.objects.filter(time_created__lte=timezone.now())
