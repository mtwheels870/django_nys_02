# MTW: Celery tasks.  Autodiscovered, see celery.py
# app.autodiscover_tasks()

# General Python
import sys
import os
import datetime
from datetime import timedelta

# Celery / Django
import celery
from celery import shared_task, Task, group, chain
from celery.app import control 

from django.utils import timezone

from django_nys_02.settings import CELERY_QUEUE
from django_nys_02.celery import app as celery_app

from .survey_util import SurveyUtil

#from .models import IpRangeSurvey

PERIODIC_MINS = 2
PERIODIC_SECS = PERIODIC_MINS * 60

TIME_FORMAT2 = "%H:%M:%S"

ESTIMATED_BASE_MIN = 2.0
ESTIMATED_RANGES_PER_MIN = 4500


@celery_app.task
def _build_clone_details(survey_id, parent_survey_id):
    # Clone all of the database stuff
    SurveyUtil.copy_geography(survey_id, parent_survey_id)

    # Set up the file structure
    SurveyUtil.link_file_string(survey_id, parent_survey_id)
    return survey_id

#
# This needs to be a shared_task b/c it can be called from the views_ping (ping immediately) or 
# from the scheduler (celery beat)
#
@shared_task(bind=True)
def start_ping(self, *args, **kwargs):
    from .tasks import zmap_from_file
    from .models import IpRangeSurvey

    #print(f"start_ping(), args = {args}, kwargs = {kwargs}")
    if "survey_id" not in kwargs:
        print(f"start_ping(), args = {args}, kwargs = {kwargs}")
        return
    survey_id = kwargs["survey_id"]
    zmap_delay_secs = int(kwargs["delay_secs"])
    print(f"Task.start_ping(), start_ping, survey_id = {survey_id}, zmap_delay_secs = {zmap_delay_secs}")

    # We can use these estimates in either case (it's just a clone)
    tally_delay_mins, tally_delay_secs = _estimate_zmap_time(survey_id)

    survey = IpRangeSurvey.objects.get(pk=survey_id)
    parent_survey_id = survey.parent_survey_id
    if not parent_survey_id:
        print(f"Task.start_ping(), after estimate, tally_delay m/s = {tally_delay_mins:.1f}/{tally_delay_secs:.0f}")
        parent_survey_id_string = "0"
        chain01 = chain(zmap_from_file.s(survey_id).set(countdown=zmap_delay_secs),
                _start_tally.s(survey_id, tally_delay_mins, tally_delay_secs))
        async_result = chain01.run()
        #print(f"Task.start_ping(), chain01 = {chain01}, async_result = {async_result}")
    else:
        #print(f"Task.start_ping(), derivative survey, need to clone here")
        # Zmap gets passed the two args from the build_clone_details
        chain02 = chain(_build_clone_details.s(survey_id, parent_survey_id),
                zmap_from_file.s().set(countdown=zmap_delay_secs),
                _start_tally.s(survey_id, tally_delay_mins, tally_delay_secs))
        async_result = chain02.run()

                # queue=QUEUE_NAME,routing_key='ping.tasks.zmap_from_file')))
    #print(f"start_ping(), async_result = {async_result}")
    return async_result

def _estimate_zmap_time(survey_id):
    from .models import IpSurveyState

    total_ranges = 0
    #print(f"_estimate_zmap_time(), survey_id = {survey_id}")
    for survey_state in IpSurveyState.objects.filter(survey__id=survey_id):
        state = survey_state.us_state
        estimated_ranges = state.estimated_ranges
        #print(f"       state: {state.state_abbrev}, count = {estimated_ranges:,}")
        total_ranges = total_ranges + estimated_ranges
    estimated_mins = ESTIMATED_BASE_MIN + (total_ranges / ESTIMATED_RANGES_PER_MIN)
    estimated_secs = estimated_mins * 60
    #first = "_estimate_zmap_time(), total_ranges = "
    #second = f"{total_ranges}, estimated m/s = {estimated_mins:.1f}/{estimated_secs:.0f}"
    #print(first + second)
    return estimated_mins, estimated_secs

@celery_app.task
def _start_tally(metadata_file, survey_id, delay_mins, delay_secs):
    from .tasks import tally_results

    #print(f"TasksPeriodic._start_tally(), metadata_file = {metadata_file}, survey_id = {survey_id}")
    if not metadata_file:
        print(f"TasksPeriodic._start_tally(), no metadata_file, bailing...")
        return None
    now = timezone.now()
    formatted_now = now.strftime(TIME_FORMAT2)
    delta = timedelta(seconds=delay_secs)
    tally_start = now + delta
    formatted_tally_start = tally_start.strftime(TIME_FORMAT2)
    first = "TasksPeriodic._start_tally(), calling tally_results (delayed), delay: "
    second = f"{delay_mins:.1f}m, now: {formatted_now}, tally_start: {formatted_tally_start}"
    print(first + second)
    # Because this is a subtask, we'll have pre-pended args?
    async_result2 = tally_results.apply_async([metadata_file, survey_id], countdown=delay_secs)
#        kwargs={"survey_id": survey_id,
#            "metadata_file": metadata_file} )
    #celery_results_handler.save_pending(async_result2)
    return async_result2

def _task_check_args(task_name, args, index):
    length = index + 1
    if len(args) <= length:
        print(f"_task_check_args(), task = {task_name}, len = {len(args)}, index = {index}"
        return None
    survey_id = args[index]
    print(f"_task_check_args(), task = {task_name}, args[{index}] = {survey_id}")
    return survey_id 

def _task_check_kwargs(task_name, kwargs):
    result = kwargs[
    if "survey_id" in kwargs:
        survey_id = kwargs["survey_id"]
        print(f"_task_check_kwargs(), task = {task_name}, survey_id = {survey_id}")
        return survey_id
    return None

def _get_task_survey_id(task):
    if not "kwargs" in task:
        if "request" in task:
            request = task["request"]
            if "name" in request:
                task_name = request["name"]
                match task_name:
                    case "powerscan.tasks.zmap_from_file":
                        return _task_check_args(task_name, request["args"], 0)
                    case "powerscan.tasks.tally_results":
                        return _task_check_args(task_name, request["args"], 1)
                    case "powerscan.tasks_periodic.start_ping":
                        return _task_check_kwargs(task_name, request["kwargs"])
                    case _:
        return None
    kwargs = task["kwargs"]
    if "survey_id" in kwargs:
        survey_id = kwargs["survey_id"]
        type = task["type"]
        print(f"      task[kwargs][survey_id]: {survey_id} = {type}")
        return survey_id
    else:
        # type = task["type"]
        # print(f"      task = {type}, no kwargs")
        return None

def _scheduled_active_surveys():
    running_surveys = []
    running_survey_ids = ()
    inspect = celery_app.control.inspect()

    tasks_active = inspect.active()
    if tasks_active:
        # tasks_active is a dict!
        for index, (key, value) in enumerate(tasks_active.items()):
            # print(f"CPV.g_tasks(), active[{index}]: {key} = {value}")
            for task in value:
                survey_id = _get_task_survey_id(task)
                if survey_id:
                    running_surveys.append(survey_id)

    tasks_scheduled = inspect.scheduled()
    if tasks_scheduled:
        for index, (key, value) in enumerate(tasks_scheduled.items()):
            # print(f"CPV.g_tasks(), active[{index}]: {key} = {value}")
            for task in value:
                survey_id = _get_task_survey_id(task)
                if survey_id:
                    running_surveys.append(survey_id)
    return running_surveys

def _schedule_surveys_tasks(upcoming_surveys):
    index = 0
    running_survey_ids = _scheduled_active_surveys()
    now = timezone.now()
    #print(f"_schedule_surveys_tasks(), running_survey_ids = {running_survey_ids}")
    for survey in upcoming_surveys:
        survey_id = survey.id
        if survey_id in running_survey_ids:
            print(f"survey[{index}]: {survey_id} already has a task!")
        else:
            time_difference = survey.time_scheduled - now       # time diff in microseconds
            time_diff_secs = time_difference.seconds / 1000.0
            print(f"CALC: {survey.time_scheduled} - {now} = {time_diff_secs:.1f}")
            delay_secs = 0 if time_difference.seconds < 0 else time_difference.seconds
            print(f"Scheduling: survey[{index}]: {survey.id},{survey.name},{survey.time_scheduled}")
            print(f"    queue = {CELERY_QUEUE}, delay_secs = {delay_secs:.1f}")
            # We're not an apply_async here, so the calling signature is different
            async_result = start_ping(
                survey_id=survey.id, delay_secs=0,
                queue=CELERY_QUEUE,
                routing_key='ping.tasks.start_ping')
            #print(f"    async_result = {async_result}")
        index = index + 1

    f = lambda survey: survey.id
    survey_ids = [f(x) for x in upcoming_surveys]
    if len(survey_ids) > 0:
        print(f"TasksPeriodic._sched_surv(), survey_id = {survey_ids}")

def _add_surveys_to_queues(debug_scheduler):
    from .models import IpRangeSurvey

    now = timezone.now()
    now_string = now.strftime(TIME_FORMAT2 )

    back_one_period = timedelta(minutes=PERIODIC_MINS)
    window_begin = now - back_one_period
    begin_string = window_begin.strftime(TIME_FORMAT2 )

    forward_two_periods = timedelta(minutes=(2 * PERIODIC_MINS))
    window_end = now + forward_two_periods 
    end_string = window_end.strftime(TIME_FORMAT2 )

    # now_p1_string = now_plus_one.strftime(TIME_FORMAT2)
    # Take surveys whose ping has not been started and whose time_scheduled is in our window
    upcoming_surveys = IpRangeSurvey.objects.filter(
            time_ping_started__isnull=True).filter(
            time_scheduled__gte=window_begin).filter(
            time_scheduled__lte=window_end)
    num_surveys = len(upcoming_surveys)
    if num_surveys > 0 or debug_scheduler:
        print(f"TasksPeriodic._schedule_surveys_tasks(), now = {now_string} window = [{begin_string},{end_string}]")
        _schedule_surveys_tasks(upcoming_surveys)

@celery_app.task(name='check_new_surveys', bind=True)
def check_new_surveys(self):
    from .models import DebugPowerScan
    from .tasks import DEBUG_ID

    debug = DebugPowerScan.objects.get(pk=DEBUG_ID)
    _add_surveys_to_queues(debug.scheduler)

