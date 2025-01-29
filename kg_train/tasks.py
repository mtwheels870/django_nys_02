# MTW: Celery tasks.  Autodiscovered, see celery.py
# app.autodiscover_tasks()

import sys
import os
import datetime
import json
import subprocess

from celery import shared_task, Task
from celery import signals, states

from django.http import JsonResponse
from django_celery_results.models import TaskResult
from django.core.management import call_command

from .models import TextFile, NerLabel

SOURCE1 = "/usr/bin/bash"

VENV_PATH = "/home/bitnami/nlp/venv01"
PRODIGY_PATH = "prodigy"

FILE_TEXT = "text_file.txt"
FILE_LABEL = "ner_labels"

def make_temp_dir():
    temp_directory = "/tmp/invoke_prodigy"
    now = datetime.datetime.now()
    folder_snapshot = now.strftime("%Y%m%d_%H%M%S")
    full_path = os.path.join(temp_directory, folder_snapshot)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    # print(f"tasks.py:make_temp_dir(), full_path = {full_path}")
    return full_path

def generate_prodigy_files(dir_path, file_id):
    text_file = TextFile.objects.filter(id=file_id)[0]
    file_path_text = os.path.join(dir_path, FILE_TEXT)
    with open(file_path_text, "w") as file_writer:
        file_content = text_file.prose_editor 
        file_writer.write(file_content)
    # print(f"tasks.py:generate_prodigy_files(), file_path_text = {file_path_text}")

    file_path_label = os.path.join(dir_path, FILE_LABEL)
    all_labels = NerLabel.objects.all()
    with open(file_path_label, "w") as file_writer:
        for label in all_labels:
            short_name = label.short_name + "\n"
            file_writer.write(short_name)

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
dpopenef invoke_prodigy(self, folder_id, file_id):
    dir_path = make_temp_dir()
    file_path_text, file_path_label = generate_prodigy_files(dir_path, file_id)

    recipe = "ner.manual"
    ner_dataset = "south_china_sea_01"
    language_model = "en_core_web_sm"

    sys_path_string = ":".join(sys.path)
    new_path = f"{VENV_PATH}/bin:" + sys_path_string
    environment = {
        "VIRTUAL_ENV" : VENV_PATH,
        "PATH" : new_path,
        "PRODIGY_HOST" : "0.0.0.0" }

    full_command = f"{PRODIGY_PATH} {recipe} {ner_dataset} {language_model} {file_path_text} --label {file_path_label}"

    print(f"invoke_prodigy(), full_command = {full_command}")
    process = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=environment)
    pid = process.pid
    returncode = process.returncode
    print(f"invoke_prodigy(), after Popen(), pid = {pid}, returncode = {returncode}")

    # Processing blocks here, so we can just use the popen object below (to kill the child)
    stdout, stderr = process.communicate()
    if process.returncode == 0:
        retval = True
        print(f"invoke_prodigy(), SUCCESS, stdout = {stdout}")
    else:
        retval = False
        print(f"invoke_prodigy(), FAILURE, stderr = {stderr}")
    kill_child_process(process)
    # session['popen_pid'] = pid
    return retval

def kill_child_process(process):
    process.terminate()
    process.wait()
    if process.poll():
        process.kill()

@signals.task_postrun.connect
def handle_task_postrun(sender, task_id, task, retval,
        *args, **kwargs):
    # Handle the result in your view
    print(f"tasks.py:h_t_pr(), task completed with retval: {retval}")

@signals.task_revoked.connect
def handle_task_revoke(sender, *args, **kwargs):
    terminated = kwargs['terminated']
    signum = kwargs['signum']
    # Handle the result in your view
    print(f"tasks.py:h_t_revoked(), sender = {sender}, terminated = {terminated}")

@shared_task
def callback_task(result):
    print(f"tasks.py:callabck_task(), Task completed with result = {result}")

