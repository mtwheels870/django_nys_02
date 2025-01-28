# MTW: Celery tasks.  Autodiscovered, see celery.py
# app.autodiscover_tasks()

import os
import datetime
from celery import shared_task, Task
from celery import signals, states
from django.http import JsonResponse
from django_celery_results.models import TaskResult
from django.core.management import call_command

from .models import TextFile, NerLabel

PYTHON_PATH="/home/bitnami/nlp/venv01/bin/python"
FILE_TEXT = "text_file.txt"
FILE_LABEL = "ner_labels"

def make_temp_dir():
    temp_directory = "/tmp/invoke_prodigy"
    now = datetime.datetime.now()
    folder_snapshot = now.strftime("%Y%m%d_%H%M%S")
    full_path = os.path.join(temp_directory, folder_snapshot)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    print(f"tasks.py:make_temp_dir(), full_path = {full_path}")
    return full_path

def generate_prodigy_files(dir_path, file_id):
    text_file = TextFile.objects.filter(id=file_id)[0]
    file_path_text = os.path.join(dir_path, FILE_TEXT)
    with open(file_path_text, "w") as file_writer:
        file_content = text_file.prose_editor 
        file_writer.write(file_content)
    print(f"tasks.py:generate_prodigy_files(), file_path_text = {file_path_text}")

    file_path_label = os.path.join(dir_path, FILE_LABEL)
    all_labels = NerLabel.objects.all()
    with open(file_path_label, "w") as file_writer:
        for label in all_labels:
            short_name = label.short_name + "\n"
            file_write.write(short_name)

    return file_path_text, file_path_label

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
    # print(f"tasks.py:invoke_prodigy(), self = {self}")
    # print(f"                 dir(self) = {dir(self)}")
    dir_path = make_temp_dir()
    file_path_text, file_path_label = generate_prodigy_files(dir_path, file_id)

    recipe = "ner.manual"
    ner_dataset = "ner_south_china_sea01"
    command = [PYTHON_PATH, recipe, ner_dataset, file_path_text, "--label", file_path_label]
    command_string = ", ".join(command)
    print(f"invoke_prodigy(), command = {command_string}")
    result = subprocess.run(command)
    print(f"invoke_prodigy(), result = {result}")
    #signals.task_postrun.send(sender=self, task_id=self.request.id, task=self, state=states.SUCCESS,
    #    retval=states.SUCCESS, args=[], kwargs={"key":"value"}) 
    # signals.task_success.send(sender=self, result=result)
    return result

@shared_task
def callback_task(result):
    print(f"tasks.py:callabck_task(), Task completed with result = {result}")
