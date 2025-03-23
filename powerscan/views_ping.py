import logging
import datetime
from datetime import timedelta
from django.shortcuts import render
from django.utils import timezone
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404, render, redirect

from django_tables2 import SingleTableView

from django_celery_results.models import TaskResult

from celery import shared_task
from celery.app import control 

# @receiver(post_save, sender=django_celery_results.models.TaskResult)
# from celery.signals import task_postrun

# from  django_tables2.config import RequestConfig

from rest_framework import viewsets
from rest_framework_gis import filters

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from django_nys_02.celery import app as celery_app, QUEUE_NAME
from django_nys_02.asgi import application

from .tasks import (
    build_whitelist, zmap_from_file, tally_results,
    CELERY_FIELD_SURVEY_ID, 
    TIME_FORMAT_STRING
)

from .models import (
    UsState,
    IpRangeSurvey,
    IpSurveyState
)

from .forms import PingStrategyForm
from .consumers import celery_results_handler, CeleryResultsHandler

from .tables import IpSurveyTable

# Import our neighbors

KEY_ID = "id"
KEY_AGG_TYPE = "agg_type"
KEY_MAP_BBOX = "map_bbox"
KEY_LEAFLET_MAP = "leaflet_map"

# These fields are used in the templates
#FIELD_CELERY_DETAILS = "celery_stuff"
FIELD_STATUS = "status_message" 
#FIELD_SURVEY_ID = "survey_id" 
FIELD_SURVEY_STATUS = "survey_status" 
FIELD_TASKS = "tasks" 


ESTIMATED_RANGES_MIN = 4500
# For our test case, we just use 15s
# PING_RESULTS_DELAY = 15
#PING_RESULTS_MINS = 60
#PING_RESULTS_SECS = PING_RESULTS_MINS * 60

#task_consumer = TaskConsumer()
#channel_name = task_consumer.get_channel_name()
#print(f"After TaskConsumer() create, channel name = {channel_name}")

class ConfigurePingView(generic.edit.FormView):
    # model = TextFile
    form_class = PingStrategyForm
    template_name = "powerscan/ps_detail.html"
    _status_message = ""
    _survey_id = 0

    def _get_celery_details(self):
        return f"App name: '{celery_app.main}', queue = '{QUEUE_NAME}'"

    def _get_tasks(self):
        inspect = celery_app.control.inspect()
        tasks_active = inspect.active()
        if tasks_active:
            for index, (key, value) in enumerate(tasks_active.items()):
                print(f"CPV.g_tasks(), active[{index}]: {key} = {value}")

            tasks_scheduled = inspect.scheduled()
            for index, (key, value) in enumerate(tasks_scheduled.items()):
                print(f"CPV.g_tasks(), scheduled[{index}]: {key} = {value}")
            return tasks_active 
        else:
            print(f"CPV.g_tasks(), no active tasks! (celery not running?)")
        return "No tasks (is celery running?)"

        #f = lambda task: task.name
        #active_task_names = [f(x) for x in inspect.active()]
        #index = 0
        #for task in tasks_active:
        #    print(f"CPV.g_tasks(), active task[{index}] = {task}, {type(task)}")

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        form = context_data['form']
        field_survey_id = form.fields['field_survey_id']
        field_survey_id.initial = "0"

        # There's an unbound, empty form in context_data...
        # File stuff
        #context_data[FIELD_CELERY_DETAILS] = self._get_celery_details()
        context_data[FIELD_STATUS] = self._status_message
        survey_status = celery_results_handler.reset()
        context_data[FIELD_SURVEY_STATUS] = survey_status 
        context_data[FIELD_TASKS] = self._get_tasks()
        print(f"CPV.get_context_data(), kwargs = {kwargs}, survey_status = {survey_status}")

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
        abbrev_string = ",".join(abbrevs)
        survey.name = abbrev_string
        survey.save()
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
        #celery_results_handler.save_pending(async_result)
        return async_result

    def _start_ping(self, survey_id):
        #print(f"CPV.post(), start_ping...")
        async_result = zmap_from_file.apply_async(
            kwargs={"survey_id" : survey_id},
                #"ip_source_id": IP_RANGE_SOURCE },
            queue=QUEUE_NAME,
            routing_key='ping.tasks.zmap_from_file')
        return async_result

    def _estimate_zmap_time(self, survey_id):
        total_ranges = 0
        print(f"_estimate_zmap_time(), survey_id = {survey_id}")
        for survey_state in IpSurveyState.objects.filter(survey__id=survey_id):
            state = survey_state.us_state
            estimated_ranges = state.estimated_ranges
            print(f"       state: {state.state_abbrev}, count = {estimated_ranges:,}")
            total_ranges = total_ranges + estimated_ranges
        estimated_mins = total_ranges / ESTIMATED_RANGES_MIN 
        estimated_secs = estimated_mins * 60
        first = "_estimate_zmap_time(), total_ranges = "
        second = f"{total_ranges}, estimated m/s = {estimated_mins:.1f}/{estimated_secs:.0f}"
        print(first + second)
        return estimated_mins, estimated_secs

    def _start_tally(self, survey_id, metadata_file, delay_mins, delay_secs):
        now = timezone.now()
        formatted_now = now.strftime(TIME_FORMAT_STRING)
        delta = timedelta(seconds=delay_secs)
        tally_start = now + delta
        formatted_tally_start = tally_start.strftime(TIME_FORMAT_STRING)
        first = "CPV._start_tally(), calling tally_results (delayed), delay: "
        second = f"{delay_mins:.1f}m, now: {formatted_now}, tally_start: {formatted_tally_start}"
        print(first + second)
        async_result2 = tally_results.apply_async(
            countdown=delay_secs,
            #"ip_source_id": IP_RANGE_SOURCE,
            kwargs={"survey_id": survey_id,
                "metadata_file": metadata_file} )
        #celery_results_handler.save_pending(async_result2)
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
                celery_results_handler.set_status(CeleryResultsHandler.SurveyStatus.STATES_CONFIGURED)

            if 'build_whitelist' in request.POST:
                async_result = self._build_whitelist(survey_id)
                self._status_message = f"Built whitelist: {async_result} ..."
                # Fall through
                celery_results_handler.set_status(CeleryResultsHandler.SurveyStatus.BUILT_WL, async_result)

            if 'start_ping' in request.POST:
                async_result = self._start_ping(survey_id)
                metadata_file = async_result.get()
                print(f"CPV.post(), async_result.metadata_file = {metadata_file}")

                delay_mins, delay_secs = self._estimate_zmap_time(survey_id)
                async_result2 = self._start_tally(survey_id, metadata_file, delay_mins, delay_secs )
                self._status_message = f"Started tally, async_result2 = {async_result2}"
                celery_results_handler.set_status(CeleryResultsHandler.SurveyStatus.PING_STARTED)

            if 'cancel_ping' in request.POST:
                print(f"CPV.post(), cancel_ping, survey_id = {survey_id}")
                celery_results_handler.set_status(CeleryResultsHandler.SurveyStatus.NULL)

            # Not sure why we have to create a new form here (but it works)
            initial_data = {"field_survey_id" : survey_id, "field_states" : selected_states }
            new_form = PingStrategyForm(initial=initial_data)

        # FIELD_CELERY_DETAILS : self._get_celery_details(),
        context = {"form" : new_form,
            FIELD_STATUS : self._status_message,
            FIELD_SURVEY_STATUS : celery_results_handler.get_status(),
            FIELD_TASKS : self._get_tasks(),
        }
        return render(request, self.template_name, context)

class RecentSurveyView(SingleTableView):
    model = IpRangeSurvey
    table_class = IpSurveyTable
    template_name = "powerscan/surveys_table.html"
    table_pagination = {
        "per_page": 10
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_queryset(self):
        #self.folder_id = self.kwargs.get('folder_id')
        # print(f"TFDV.get_queryset(), doing query")
        # We get the last 20 (so that's two pages worth)
        #queryset = IpRangeSurvey.objects.order_by("-time_created")[:20]
        queryset = IpRangeSurvey.objects.order_by("-id")
        return queryset 

    def post(self, request, *args, **kwargs):
        folder_id = kwargs["folder_id"]
        selected_pks = request.POST.getlist('selection')
        num_selected = len(selected_pks)
        if num_selected  == 0:
            print(f"TFDV.post(), no selected rows")
            return redirect(request.path)
        elif num_selected > 1:
            print(f"TFDV.post(), >1 selected rows")
            return redirect(request.path)
        else:
            # Check which button we're in: edit or label
            file_id = selected_pks[0]
            if 'edit' in request.POST:
                print(f"TFDV.post(), editing page")
                return HttpResponseRedirect(reverse("app_kg_train:file_edit", args=(folder_id, file_id,)))
            elif 'label' in request.POST:
                return self.label_page(request, folder_id, file_id)
            else:
                print(f"TFDV.post(), unrecognized button:")
                for i, key in enumerate(request.POST):
                    value = request.POST[key]
                    print(f"          [{i}]: {key} = {value}")
                return redirect(request.path)

