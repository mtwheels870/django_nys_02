from datetime import timedelta

from django.apps import AppConfig
from django.utils import timezone

from django_nys_02.celery import app as celery_app, QUEUE_NAME

from .tasks_periodic import check_new_surveys

@celery_app.task(name='blah_de_blah')
def blah_de_blah(arg1, arg2):
    print(f"blah_de_blah(), arg1 = {arg1}, arg2 = {arg2}")

TIME_FORMAT2 = "%H:%M:%S"

def _add_surveys_to_queues():
    now = timezone.now()
    now_string = now.strftime(TIME_FORMAT2 )
    print(f"TasksPeriodic._add_surveys_to_queues(), now = {now_string}")
    one_hour = timedelta(hours=1)
    now_plus_one = now + one_hour
    upcoming_surveys = IpRangeSurvey.objects.filter(
            time_tally_stopped__isnull=True).filter(time_scheduled__gte=now).filter(time_scheduled__lte=now_plus_one)
    f = lambda survey: survey.id
    survey_ids = [f(x) for x in upcoming_surveys]
    print(f"TasksPeriodic._as2qs(), survey_id = {survey_ids}")

@celery_app.task(name='check_new_surveys', bind=True)
def check_new_surveys(self, arg1, arg2):
    _add_surveys_to_queues()
# I think this name becomes the leading prefix on the database table names, etc.

class PowerScanConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'powerscan'

    def ready(self):
        # Can't put this at the top-level (apps aren't ready yet)
        from django_celery_beat.models import PeriodicTask, IntervalSchedule

        # Post-initialization tasks here
        # self._add_surveys_to_queues()

        # 'task': 'periodic_task_to_do',
                #'task': 'powerscan.tasks_periodic.periodic_task_to_do',
        celery_app.conf.beat_schedule = {
            'add-every-minute': {
                'task': 'blah_de_blah',
                'schedule': 180.0,   
                'args': (23, 37),   
            },
        }

        # Create the schedule object
#        schedule, created = IntervalSchedule.objects.get_or_create(
#            every=10,
#            period=IntervalSchedule.SECONDS,
#        )

        # Create the Periodic task
#        periodic_task = PeriodicTask.objects.create(
#            interval=schedule,                  # we created this above.
#            name='Importing contacts',          # simply describes this periodic task.
#            task='proj.tasks.import_contacts',  # name of task.
#        )

