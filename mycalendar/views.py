import logging

from django.apps import apps
from django.shortcuts import render
from django.utils import timezone
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404, render
# import django.dispatch

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

def set_schedule_type(request, pk):
    survey = get_object_or_404(IpRangeSurvey, pk=pk)
    try:
        selected_sched_type = request.POST["sched_type"]
        print(f"pk: {pk}")
    except (KeyError):
        # Redisplay the question voting form.
        # Fix the hard-coded name below (/polls/nys/)
        return render(
            request,
            "./schedsurv_done.html",
            {
                "error_message": "You didn't select a schedule_type.",
            },
        )
    else:
        # app_name = request.resolver_match.app_name
        #configs = apps.app_configs
        #for index, app in enumerate(configs):
        #    print(f"app[{index}] = {app}")
        app_config = apps.get_app_config('mycalendar')
        calendar = app_config.get_calendar()
        today = app_config.today
        print(f"set_schedule_type(), today: {today}")
        scheduled_survey = ScheduledIpRangeSurvey(calendar=calendar,
            ip_range_survey=survey, time_approved=timezone.now(),
            survey_type=selected_sched_type)
        scheduled_survey.save()
        new_id = scheduled_survey.id
        return HttpResponseRedirect(reverse("app_my_scheduler:dailycalendar", args=(new_id,)))

