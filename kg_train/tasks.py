# MTW: Celery tasks.  Autodiscovered, see celery.py
# app.autodiscover_tasks()

import os
import datetime
from celery import shared_task

from .models import TextFileStatus, TextFile, TextFolder

VENV_PYTHON_PATH="/home/bitnami/nlp/venv01/bin"

def make_tmp_files(file_id):
    temp_directory = "/tmp/invoke_prodigy"
    now = datetime.datetime.now()
    folder_snapshot = now.strftime("%Y%m%d_%H%M%S")
    full_path = os.path.join(temp_directory, folder_snapshot)
    if not os.path.exists(full_path):
        os.makedirs(temp_directory)
    print("tasks.py:make_tmp_files(), directory = {temp_directory}")


@shared_task
def invoke_prodigy(x, y, folder_id, file_id):
    print(f"tasks.py:add(), adding {x} and {y}, file_id = {file_id}")
    make_tmp_files(file_id)

    return x + y

