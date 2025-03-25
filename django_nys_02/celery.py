import os

from django.conf import settings

from celery import Celery

# Set the default Django settings module for the 'celery' program.
# MTW os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj.settings')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_nys_02.settings')

# PRODUCTION CHANGE: /dev/production/, /cb_development/cb_production/
app = Celery('celery_django_dev')
QUEUE_NAME = "cb_development"

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
# MTW: No Va.  app.config_from_object(f'django.conf:{settings.__name__}', namespace='CELERY')
# This works:
# app.config_from_object("django_nys_02.config:CeleryConfig", namespace='CELERY')
app.config_from_object("django.conf:settings", namespace='CELERY')
# Same as the CELERY_... version (in settings.py)
# app.conf.broker_connection_retry_on_startup = True
app.conf.task_routes = ([
    ('prodigy.tasks.*', {'queue': QUEUE_NAME }),
],)

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

@app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    print(f"setup_periodic_tasks(), setting up basic shit")
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')

    # Calls test('hello') every 30 seconds.
    # It uses the same signature of previous task, an explicit name is
    # defined to avoid this task replacing the previous one defined.
    sender.add_periodic_task(30.0, test.s('hello'), name='add every 30')

    # Calls test('world') every 30 seconds
    sender.add_periodic_task(30.0, test.s('world'), expires=10)

    # Executes every Monday morning at 7:30 a.m.
    sender.add_periodic_task(
        crontab(hour=7, minute=30, day_of_week=1),
        test.s('Happy Mondays!'),
    )
