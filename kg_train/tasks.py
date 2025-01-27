# MTW: Celery tasks.  Autodiscovered, see celery.py
# app.autodiscover_tasks()

import os
import datetime
from celery import shared_task, Task
from django.http import JsonResponse
from django_celery_results.models import TaskResult

from .models import TextFileStatus, TextFile, TextFolder

VENV_PYTHON_PATH="/home/bitnami/nlp/venv01/bin"
FILE_TEXT = "text_file.txt"

def make_tmp_files():
    temp_directory = "/tmp/invoke_prodigy"
    now = datetime.datetime.now()
    folder_snapshot = now.strftime("%Y%m%d_%H%M%S")
    full_path = os.path.join(temp_directory, folder_snapshot)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    print(f"tasks.py:make_tmp_files(), full_path = {full_path}")
    return full_path

def generate_prodigy_files(dir_path, file_id):
    text_file = TextFile.objects.filter(id=file_id)[0]
    file_path_text = os.path.join(dir_path, FILE_TEXT)
    with open(file_path_text, "w") as file_writer:
        file_content = text_file.prose_editor 
        file_writer.write(file_content)
    print(f"tasks.py:generate_prodigy_files(), file_path_text = {file_path_text}")
    return file_path_text 

# This returns the status of the worker/celery
def get_task_result(request, task_id):
    print(f"tasks.py:get_task_result(), task_id = {task_id}")
    task_result = TaskResult.objects.get(task_id=task_id)
    return JsonResponse({
        'task_id': task_result.task_id,
        'status': task_result.status,
        'result': task_result.result
    })

class InvokeProdigyTask(Task):
    # args = tuple
    # kwards = Dict
    def on_failure(self, exception, task_id, args, kwargs, exception_info):
        print(f'IPT.on_failure(), task: {task_id} failed, exception: {exception}')

    def on_success(self, retval, task_id, args, kwargs):
        print(f'IPT.on_success(), task: {task_id} sucess, retval = {retval}')

# Note, this just does the action.  Result is above 
@shared_task(bind=True, base=InvokeProdigyTask)
def invoke_prodigy(self, x, y, folder_id, file_id):
    print(f"tasks.py:invoke_prodigy(), self = {self}")
    dir_path = make_tmp_files()
    file_path_text = generate_prodigy_files(dir_path, file_id)
    return x + y

@shared_task
def callback_task(result):
    print(f"Task completed with result = {result}")
