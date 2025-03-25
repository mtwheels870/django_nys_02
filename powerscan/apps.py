from django.apps import AppConfig
from django.utils import timezone

from django_nys_02.celery import app as celery_app, QUEUE_NAME

#@celery_app.task(name='blah_de_blah')
#def blah_de_blah(arg1, arg2):
#    print(f"blah_de_blah(), arg1 = {arg1}, arg2 = {arg2}")

# I think this name becomes the leading prefix on the database table names, etc.
class PowerScanConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'powerscan'

    def _add_surveys_to_queues(self):
        print(f"PowerScanConfig._add_surveys_to_queues()")
        now = timezone.now()
        one_hour = timedelta(hours=1)
        now_plus_one = now + one_hour
        upcoming_surveys = IpRangeSurvey.object.filter(
                time_tally_stopped__isnull=True).filter(time_scheduled__ge=now).filter(time_scheduled__lt=now_plus_one)
        f = lambda survey: survey.id
        survey_ids = [f(x) for x in upcoming_surveys]
        print(f"PSC._as2qs(), survey_id = {survey_ids}")

    def ready(self):
        # Can't put this at the top-level (apps aren't ready yet)
        from django_celery_beat.models import PeriodicTask, IntervalSchedule

        # Post-initialization tasks here
        self._add_surveys_to_queues()

        # 'task': 'periodic_task_to_do',
                #'task': 'powerscan.tasks_periodic.periodic_task_to_do',
        celery_app.conf.beat_schedule = {
            'add-every-minute': {
                'task': 'check_new_surveys',
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

