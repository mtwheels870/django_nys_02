import os

from django.conf import settings

from celery import Celery

from .settings import CELERY_QUEUE, CELERY_APP_NAME

# Set the default Django settings module for the 'celery' program.
# MTW os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj.settings')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_nys_02.settings')

app = Celery(CELERY_APP_NAME)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace='CELERY')

# Same as the CELERY_... version (in settings.py)
# app.conf.broker_connection_retry_on_startup = True
app.conf.task_routes = ([
    ('prodigy.tasks.*', {'queue': CELERY_QUEUE }),
],)

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

