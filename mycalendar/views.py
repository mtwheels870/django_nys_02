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

class ScheduleSurveyMixin:
    model = IpRangeSurvey
    sched_types_kwarg = "sched_types"

class ScheduleSurveyDetailView(ScheduleSurveyMixin, generic.DetailView):
    template_name = "./schedsurv_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sched_types'] = ScheduleType.objects.all()
        # pk = self.kwargs.get('pk')  # Or 'product_id' if you customized the parameter name
        # Use pk to access the object or do other operations
        return context
