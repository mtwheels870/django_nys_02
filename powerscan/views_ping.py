from enum import Enum
import logging
from django.shortcuts import render
from django.utils import timezone
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models.signals import post_save
from django.dispatch import receiver

from django_celery_results.models import TaskResult

from celery.signals import task_postrun

# from  django_tables2.config import RequestConfig

from rest_framework import viewsets
from rest_framework_gis import filters

from django_nys_02.celery import app as celery_app, QUEUE_NAME

from .tasks import build_whitelist, zmap_from_file, tally_results, CELERY_FIELD_SURVEY_ID

from .models import (
    UsState,
    IpRangeSurvey,
    IpSurveyState
)

from .forms import PingStrategyForm

# Import our neighbors

KEY_ID = "id"
KEY_AGG_TYPE = "agg_type"
KEY_MAP_BBOX = "map_bbox"
KEY_LEAFLET_MAP = "leaflet_map"

# These fields are used in the templates
FIELD_CELERY_DETAILS = "celery_stuff"
FIELD_STATUS = "status_message" 
FIELD_SURVEY_ID = "survey_id" 
FIELD_SURVEY_STATUS = "survey_status" 

# For our test case, we just use 15s
# PING_RESULTS_DELAY = 15
PING_RESULTS_DELAY = 15 * 60
PING_SMALL_DELAY = 20

# State machines for ping stuff
class SurveyStatus(Enum):
    NULL = 0
    STATES_CONFIGURED = 1
    BUILT_WL = 2
    PING_STARTED = 3
    PING_COMPLETED = 4

    def __str__(self):
        return str(self.name)

class ConfigurePingView(generic.edit.FormView):
    # model = TextFile
    form_class = PingStrategyForm
    template_name = "powerscan/ps_detail.html"
    _status_message = ""
    _survey_id = 0
    _current_status = SurveyStatus.NULL

    def _get_celery_details(self):
        return f"App name: '{celery_app.main}', queue = '{QUEUE_NAME}'"

    def get_context_data(self, **kwargs):
        print(f"CPV.get_context_data(), kwargs = {kwargs}")
        context_data = super().get_context_data(**kwargs)
        form = context_data['form']
        field_survey_id = form.fields['field_survey_id']
        field_survey_id.initial = "0"

        # There's an unbound, empty form in context_data...
        # File stuff
        context_data[FIELD_CELERY_DETAILS] = self._get_celery_details()
        context_data[FIELD_STATUS] = self._status_message
        context_data[FIELD_SURVEY_STATUS] = self._current_status

        #context_data[FIELD_SURVEY_ID] = self._survey_id

        return context_data

    # Configure just creates the state survey items, everything else is done asynchronously in
    # build_whitelist.  REasons - slow to create all of those database entries.  We don't want to pass a list
    # of states to the celery worker.  So, we create the survey, pass the survey id to the worker, and she reads
    # the pre-saved states from the database
    def _configure_survey(self, selected_states):
        survey = IpRangeSurvey()
        survey.save()
        abbrevs = []
        print(f"CPV._configure_survey(), selected_states (fp) = {selected_states}")
        for state in UsState.objects.filter(state_fp__in=selected_states).order_by("state_abbrev"):
            abbrevs.append(state.state_abbrev)
            survey_state = IpSurveyState(survey=survey, us_state=state)
            survey_state.save()
        self._survey_id = survey.id
        return abbrevs, survey.id

    def _build_whitelist(self, survey_id):
        if not survey_id:
            print(f"CPV.build_whitelist(), survey not configured! (should be extracted from the form)")
            return None

        print(f"CPV.build_whitelist(), survey: {survey_id}")
        survey = IpRangeSurvey.objects.get(pk=survey_id)
        survey.time_whitelist_created = timezone.now()
        # MaxM ranges
        print(f"CPV.build_whitelist(), apply_async()")
        async_result = build_whitelist.apply_async(
            kwargs={"survey_id" : survey_id},
            queue=QUEUE_NAME,
            routing_key='ping.tasks.build_whitelist')
        return async_result

    @task_postrun.connect(sender=build_whitelist)
    def build_whitelist_postrun(task_id, task, retval, *args, **kwargs):
        print(f"CPV.build_whitelist_postrun(), task_id = {task_id}, task = {task}, retval = {retval}, kwargs = {kwargs}")
        # information about task are located in headers for task messages
        # using the task protocol version 2.
        #info = headers if 'task' in headers else body
        #print('after_task_publish for task id {info[id]}'.format(
        #    info=info,
        #))

    def _start_ping(self, survey_id):
        #print(f"CPV.post(), start_ping...")
        async_result = zmap_from_file.apply_async(
            kwargs={"survey_id" : survey_id},
                #"ip_source_id": IP_RANGE_SOURCE },
            queue=QUEUE_NAME,
            routing_key='ping.tasks.zmap_from_file')
        return async_result

    @task_postrun.connect(sender=zmap_from_file)
    def zmap_from_file_postrun(task_id, task, retval, *args, **kwargs):
        print(f"CPV.zmap_from_file_postrun(), task_id = {task_id}, task = {task}, retval = {retval}, kwargs = {kwargs}")

    def _start_tally(self, survey_id, metadata_file, results_delay):
        now = timezone.now()
        print(f"CPV._start_tally(), calling tally_results (delayed), now = {now}, seconds = {results_delay}")
        # Fire off the counting task
        async_result2 = tally_results.apply_async(
            countdown=results_delay,
            #"ip_source_id": IP_RANGE_SOURCE,
            kwargs={"survey_id": survey_id,
                "metadata_file": metadata_file} )
        return async_result2

    def post(self, request, *args, **kwargs):
        form = PingStrategyForm(request.POST)
        if not form.is_valid():
            print(f"CPV.post(), form is INVALID, creating empty")
            new_form = PingStrategyForm()
        else:
            selected_states = form.cleaned_data['field_states']
            survey_id = form.cleaned_data['field_survey_id']

            if 'return_to_map' in request.POST:
                return HttpResponseRedirect(reverse("app_cybsen:map_viewer"))

            if 'configure_survey' in request.POST:
                abbrevs, survey_id = self._configure_survey(selected_states)
                abbrevs_string = ", ".join(abbrevs)
                self._status_message = f"Configured survey {survey_id} with states [{abbrevs_string}]"
                # Fall through
                self._current_status = SurveyStatus.STATES_CONFIGURED 

            if 'build_whitelist' in request.POST:
                async_result = self._build_whitelist(survey_id)
                self._status_message = f"Built whitelist {async_result} ..."
                # Fall through
                self._current_status = SurveyStatus.BUILT_WL 

            if 'start_ping' in request.POST:
                async_result = self._start_ping(survey_id)
                metadata_file = async_result.get()
                print(f"CPV.post(), async_result.metadata_file = {metadata_file}")

                async_result2 = self._start_tally(survey_id, metadata_file, PING_RESULTS_DELAY)
                self._status_message = f"Started tally, async_result2 = {async_result2}"
                self._current_status = SurveyStatus.PING_STARTED 

            if 'ping_96' in request.POST:
                survey_id = 96
                print(f"CPV.post(), ping_96")
                async_result = self._start_ping(survey_id)
                metadata_file = async_result.get()
                print(f"CPV.post(), async_result.metadata_file = {metadata_file}")

                ping_delay = PING_SMALL_DELAY
                async_result2 = self._start_tally(survey_id, metadata_file, ping_delay)
                self._status_message = f"Started tally, async_result2 = {async_result2}"

            if 'cancel_ping' in request.POST:
                print(f"CPV.post(), cancel_ping, survey_id = {survey_id}")
                self._current_status = SurveyStatus.NULL 

            # Not sure why we have to create a new form here (but it works)
            initial_data = {"field_survey_id" : survey_id, "field_states" : selected_states }
            new_form = PingStrategyForm(initial=initial_data)

        # No Work: field_survey_id.initial = self._survey_id
        # field_survey_id = self._survey_id
        # FIELD_SURVEY_ID : self._survey_id}
        context = {"form" : new_form,
            FIELD_CELERY_DETAILS : self._get_celery_details(),
            FIELD_STATUS : self._status_message,
            FIELD_SURVEY_STATUS : self._current_status,
        }
        return render(request, self.template_name, context)

    @receiver(post_save, sender=TaskResult)
    def task_result_saved(sender, **kwargs):
        print(f"task_result_saved(), sender = {sender}, kwargs = {kwargs}")

        #print(f"CPV.after super.get_context_data(), context_data = {context_data}")
        # print(f"CPV.get_context_data() 3, form = {form}")
        #print(f"CPV.get_context_data() 4, field_survey_id = {field_survey_id}")
        #print(f"CPV.get_context_data() 5, (after setting initial) field_survey_id = {field_survey_id}")
