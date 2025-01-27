# MTW: Celery tasks.  Autodiscovered, see celery.py
# app.autodiscover_tasks()

from celery import shared_task

@shared_task
def add(x, y):
    print(f"tasks.py:add(), adding {x} and {y}")
    return x + y

