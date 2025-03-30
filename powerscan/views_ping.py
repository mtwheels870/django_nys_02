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

from rest_framework import viewsets
from rest_framework_gis import filters

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from django_nys_02.settings import CELERY_QUEUE
from django_nys_02.celery import app as celery_app
from django_nys_02.asgi import application

from .tasks import (
    build_whitelist, zmap_from_file, tally_results,
    CELERY_FIELD_SURVEY_ID, 
    TIME_FORMAT_STRING
)
from .tasks_periodic import start_ping
from .models import (
    UsState,
    IpRangeSurvey,
    IpSurveyState
)

from .forms import PingStrategyForm, ScheduleSurveyForm
from .consumers import celery_results_handler, CeleryResultsHandler
from .tables import IpSurveyTable, CeleryTaskTable
from .survey_util import SurveyUtil

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
FIELD_SURVEY_ID = "field_survey_id"
FIELD_SURVEY_NAME = "field_survey_name"
FIELD_START_TIME = "field_start_time"
FIELD_RECURRING = "field_recurring"
FIELD_NUM_OCCURRENCES = "field_num_occurrences"
FIELD_CURRENT_TIME = "current_time"

class CreateNewSurveyView(generic.edit.FormView):
    # model = TextFile
    form_class = PingStrategyForm
    template_name = "powerscan/survey_config.html"
    _status_message = ""
    _survey_id = 0

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        form = context_data['form']
        field_survey_id = form.fields['field_survey_id']
        field_survey_id.initial = "0"

        # There's an unbound, empty form in context_data...
        # File stuff
        context_data[FIELD_STATUS] = self._status_message
        survey_status = celery_results_handler.reset()
        context_data[FIELD_SURVEY_STATUS] = survey_status 

        return context_data

    # Configure just creates the state survey items, everything else is done asynchronously in
    # build_whitelist.  REasons - slow to create all of those database entries.  We don't want to pass a list
    # of states to the celery worker.  So, we create the survey, pass the survey id to the worker, and she reads
    # the pre-saved states from the database
    def _configure_survey(self, selected_states):
        survey = IpRangeSurvey()
        # print(f"SURVEY SAVE, 11")
        survey.save()
        abbrevs = []
        selected_states_string = ",".join(selected_states)
        print(f"CPV._configure_survey(), selected_states (fp) = {selected_states_string}")
        for state in UsState.objects.filter(state_fp__in=selected_states).order_by("state_abbrev"):
            abbrevs.append(state.state_abbrev)
            survey_state = IpSurveyState(survey=survey, us_state=state)
            survey_state.save()
        self._survey_id = survey.id
        abbrev_string = ",".join(abbrevs)
        survey.name = abbrev_string
        # print(f"SURVEY SAVE, 2") 
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
        print(f"CPV.build_whitelist(), apply_async(), queue: {CELERY_QUEUE}")
        async_result = build_whitelist.apply_async(
            kwargs={"survey_id" : survey_id},
            queue=CELERY_QUEUE,
            routing_key='ping.tasks.build_whitelist')
        #celery_results_handler.save_pending(async_result)
        return async_result

    # CreateNewSurveyView
    def post(self, request, *args, **kwargs):
        form = PingStrategyForm(request.POST)
        if not form.is_valid():
            print(f"CPV.post(), form is INVALID, creating empty")
            new_form = PingStrategyForm()
        else:
            selected_states = form.cleaned_data['field_states']
            survey_id = form.cleaned_data['field_survey_id']

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
                # async_result = start_ping(args=(survey_id, 0))
                async_result = start_ping.apply_async(
                    kwargs={"survey_id" : survey_id, "delay_secs" : 0},
                    queue=CELERY_QUEUE,
                    routing_key='ping.tasks.start_ping')
                self._status_message = f"Started tally, async_result = {async_result}"
                celery_results_handler.set_status(CeleryResultsHandler.SurveyStatus.PING_STARTED)
                # Jump to the survey table
                return HttpResponseRedirect(reverse("app_powerscan:survey_table"))

            if 'schedule_survey' in request.POST:
                int_survey_id = int(survey_id)
                return HttpResponseRedirect(reverse("app_powerscan:schedule_survey", args=(int_survey_id,)))

            # Not sure why we have to create a new form here (but it works)
            initial_data = {"field_survey_id" : survey_id, "field_states" : selected_states }
            new_form = PingStrategyForm(initial=initial_data)

        # FIELD_CELERY_DETAILS : self._get_celery_details(),
        status = celery_results_handler.get_status()
        print(f"CPV.post(), new status = {status}")
            #FIELD_TASKS : self._get_tasks(),
        context = {"form" : new_form,
            FIELD_STATUS : self._status_message,
            FIELD_SURVEY_STATUS : status
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
        now_fmt = timezone.now().strftime(TIME_FORMAT_STRING)
        context[FIELD_CURRENT_TIME] = now_fmt
        return context

    def get_queryset(self):
        #self.folder_id = self.kwargs.get('folder_id')
        # print(f"TFDV.get_queryset(), doing query")
        # We get the last 20 (so that's two pages worth)
        #queryset = IpRangeSurvey.objects.order_by("-time_created")[:20]
        queryset = IpRangeSurvey.objects.order_by("-id")
        return queryset 

    def post(self, request, *args, **kwargs):
        selected_pks = request.POST.getlist('selection')
        num_selected = len(selected_pks)
        if 'edit' in request.POST:
            if num_selected == 1:
                survey_id = selected_pks[0]
                print(f"RSV.post()[edit], editing page")
                # This is a copy/paste error (from kg_train - never changed)
                return HttpResponseRedirect(reverse("app_powerscan:schedule_survey", args=(survey_id, )))
            else:
                print(f"RSV.post()[edit], num_selected = {num_selected} (must be one (1) only)")
        elif 'delete' in request.POST:
            result = SurveyUtil._delete_surveys(selected_pks)
        elif 'ping_now' in request.POST:
            print(f"RSV.post(), ping_now(), calling start_ping.async()") 
            async_result = start_ping.apply_async(
                kwargs={"survey_id" : survey_id, "delay_secs" : 0},
                queue=CELERY_QUEUE,
                routing_key='ping.tasks.start_ping')
            self._status_message = f"Started tally, async_result = {async_result}"
            celery_results_handler.set_status(CeleryResultsHandler.SurveyStatus.PING_STARTED)
        elif 'new' in request.POST:
            return HttpResponseRedirect(reverse("app_powerscan:ping_strat_index"))
        else:
            print(f"RSV.post(), unrecognized post request:")
            for i, key in enumerate(request.POST):
                value = request.POST[key]
                print(f"          [{i}]: {key} = {value}")
        now_fmt = timezone.now().strftime(TIME_FORMAT_STRING)
        context = {
            FIELD_CURRENT_TIME : now_fmt,
        }
        # Stay on the same page
        return redirect(request.path, context)


class CeleryTasksView(SingleTableView):
    #data = [
    #    {"name": "John", "surname": "Doe", "address": "123 Main St"},
    #    {"name": "Jane", "surname": "Smith", "address": "456 Oak Ave"},
    #]
    table_class = CeleryTaskTable 
    #table_class = NonModelTable
    template_name = "powerscan/tasks_table.html"
    table_pagination = {
        "per_page": 10
    }

    def _make_task_tuple(self, status, task):
        request = task["request"]
        # print(f"_m_t_t(), request = {request}")
        name = request["type"]
        # print(f"_m_t_t(), name = {name}")
        survey_id = request["kwargs"]["survey_id"]
        eta = task["eta"]
        dict = {"status" : status, "survey_id" : survey_id, "name" : name, "eta" : eta}
        return dict

    def get_queryset(self):
        inspect = celery_app.control.inspect()
        tasks_active = inspect.active()
        data = []
        if tasks_active:
            # I think each of these (active, scheduled) is a list of tasks (so there will be one item).
            for index, (key, value) in enumerate(tasks_active.items()):
                # print(f"CPV.g_tasks(), active[{index}]: {key} = {value}")
                for task in value:
                    tuple = self._make_task_tuple("active", task)
                    data.append(tuple)

            tasks_scheduled = inspect.scheduled()
            for index, (key, value) in enumerate(tasks_scheduled.items()):
                # print(f"CPV.g_tasks(), scheduled[{index}]: {key} = {value}")
                for task in value:
                    tuple = self._make_task_tuple("scheduled", task)
                    data.append(tuple)
        return data

class ScheduleSurveyView(generic.edit.FormView):
    form_class = ScheduleSurveyForm
    template_name = "powerscan/schedule_survey.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        form = context_data['form']
        survey_id = self.kwargs.get('pk')
        print(f"SSV.g_c_d(), survey_id = {survey_id}")
        survey = get_object_or_404(IpRangeSurvey, pk=survey_id)
        field_survey_id = form.fields[FIELD_SURVEY_ID]
        field_survey_id.initial = survey_id
        field_survey_name = form.fields[FIELD_SURVEY_NAME]
        field_survey_name.initial = survey.name
        field_start_time = form.fields[FIELD_START_TIME]
        field_start_time.initial = timezone.now()
        return context_data

    def _clone_survey(self, survey, start_time):
        new_survey = IpRangeSurvey(name=survey.name, time_whitelist_created=survey.time_whitelist_created,
            parent_survey_id=survey.id, time_scheduled=start_time)
        return new_survey

    def _schedule_surveys(self, survey_id, start_time, recurring, num_occurrences):
        print(f"SSV._schedule_surveys(), survey_id = {survey_id}, start_time = {start_time}")
        print(f"      recurring = {recurring}, num_occurrences = {num_occurrences}")
        survey = get_object_or_404(IpRangeSurvey, pk=survey_id)
        survey.time_scheduled = start_time
        survey.save()
        if recurring and num_occurrences > 1:
            if not recurring:
                print(f"SSV._schedule_surveys(), num_occurrences = {num_occurrences}, but recurring = {recurring}")
                return
            td = recurring
            print(f"      td = {td}")
            # The first occurrence was created (above), hence the -1 in here
            for index in range(num_occurrences - 1):
                start_time = start_time + td
                start_string = start_time.strftime(TIME_FORMAT_STRING)
                new_survey = self._clone_survey(survey, start_time)
                new_survey.save()
                print(f"    iteration[{index}]: {start_string}")
        # print(f"SURVEY SAVE, 1") 

    def post(self, request, *args, **kwargs):
        survey_id = kwargs["pk"]
        print(f"SSV.post(), survey_id = {survey_id}")
        if 'discard' in request.POST:
            print(f"SSV.post(), discarding")

        if 'submit' in request.POST:
            form = ScheduleSurveyForm(request.POST)
            print(f"SSV.post(), submitting")
            if not form.is_valid():
                print(f"SSV.post(), form is INVALID, creating empty")
                # Clear the form and stay here
                context = {"form" : form}
                # We re-reneder the same form, but the errors will now be displayed
                return render(request, self.template_name, context)
            else:
                # Form is valid
                start_time = form.cleaned_data[FIELD_START_TIME]
                recurring = form.cleaned_data[FIELD_RECURRING]
                num_occurrences = form.cleaned_data[FIELD_NUM_OCCURRENCES]
                self._schedule_surveys(survey_id, start_time, recurring, num_occurrences) 
        return HttpResponseRedirect(reverse("app_powerscan:survey_table"))

        #context_data[FIELD_CELERY_DETAILS] = self._get_celery_details()
        #context_data[FIELD_TASKS] = self._get_tasks()
        # print(f"CPV.get_context_data(), kwargs = {kwargs}, survey_status = {survey_status}")

        #context_data[FIELD_SURVEY_ID] = self._survey_id
