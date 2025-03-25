from django.apps import AppConfig

from django_nys_02.celery import app as celery_app, QUEUE_NAME

#from .tasks_periodic import periodic_task_to_do

#@celery_app.task(name='blah_de_blah')
#def blah_de_blah(arg1, arg2):
#    print(f"blah_de_blah(), arg1 = {arg1}, arg2 = {arg2}")

# I think this name becomes the leading prefix on the database table names, etc.
class PowerScanConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'powerscan'

    def ready(self):
        # Can't put this at the top-level (apps aren't ready yet)
        from django_celery_beat.models import PeriodicTask, IntervalSchedule

        # Post-initialization tasks here
        print(f"PowerScanConfig.app.ready()")
        survey_scheduler = SurveyScheduler()

        # 'task': 'periodic_task_to_do',
                #'task': 'powerscan.tasks_periodic.periodic_task_to_do',
        celery_app.conf.beat_schedule = {
            'add-every-minute': {
                'task': 'blah_de_blah',
                'schedule': 10.0,   # This runs the task every minute.  MTW, why does 10.0 = every minute?
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

