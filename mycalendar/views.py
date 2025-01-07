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

PP_CALENDAR_SLUG = "pp"

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

def set_schedule_type(request, survey_id):
    survey = get_object_or_404(IpRangeSurvey, pk=survey_id)
    try:
        selected_sched_type = request.POST["sched_type"]
        print(f"selected_sched_type: {selected_sched_type}")
    except (KeyError):
        # Redisplay the question voting form.
        # Fix the hard-coded name below (/polls/nys/)
        return render(
            request,
            "./schedsurv_create.html",
            {
                "survey_id": survey_id,
                "error_message": "You didn't select a schedule_type.",
            },
        )
    else:
        # What does F() do?
        #selected_choice.votes = F("votes") + 1
        #selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        r"^calendar/daily/(?P<calendar_slug>[-\w]+)/$",
        return HttpResponseRedirect(reverse(f"calendar/daily/{PP_CALENDAR_SLUG}", args=(survey_id,)))
