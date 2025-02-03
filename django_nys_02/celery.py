import os

from django.conf import settings

from celery import Celery

# Set the default Django settings module for the 'celery' program.
# MTW os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj.settings')
# PRODUCTION CHANGE (2x)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_nys_02.settings')

app = Celery('django_nys_02')

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

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
