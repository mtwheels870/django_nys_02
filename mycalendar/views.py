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

from .models import (
    ScheduledIpRangeSurvey,
    ScheduleType,
)

class CalendarMixin(CalendarViewPermissionMixin):
    model = IpRangeSurvey
    slug_url_kwarg = "stuff"

class ScheduleSurveyDetailView(CalendarMixin, generic.DetailView):
    template_name = "./schedsurv_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stuff'] = "Really cool stuff"
        # context['types'] = ScheduleType.objects.all()
        # pk = self.kwargs.get('pk')  # Or 'product_id' if you customized the parameter name
        # Use pk to access the object or do other operations
        print(f"PingStrategyDetailView.get_context_data(), stuff = {context['stuff']}")
        return context
