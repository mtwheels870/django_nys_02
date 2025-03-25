from django.apps import AppConfig

from django_celery_beat.models import PeriodicTask, IntervalSchedule

from django_nys_02.celery import app as celery_app, QUEUE_NAME

# I think this name becomes the leading prefix on the database table names, etc.
class PowerScanConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'powerscan'

    def ready(self):
        # Post-initialization tasks here
        print(f"PowerScanConfig.app.ready()")

        celery_app.conf.beat_schedule = {
            'add-every-minute': {
                'task': 'periodic_task_to_do',
                'schedule': 10.0,   # This runs the task every minute
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

