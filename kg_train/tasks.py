# MTW: Celery tasks.  Autodiscovered, see celery.py
# app.autodiscover_tasks()

import sys
import os
import datetime
import json
import subprocess
import shutil

import celery
from celery import shared_task, Task
from celery import signals, states
from celery.app import control 

from django.http import JsonResponse
from django_celery_results.models import TaskResult
from django.core.management import call_command

from .models import TextFile, NerLabel

SOURCE1 = "/usr/bin/bash"

VENV_PATH = "/home/bitnami/nlp/venv01"
PRODIGY_PATH = "prodigy"

FILE_TEXT = "text_file.txt"
FILE_LABEL = "ner_labels"
FILE_PRODIGY_CONFIG = "config.json"
FILE_OUTPUT = "prodigy_output.txt"

TEMP_DIRECTORY = "/tmp/invoke_prodigy"
PRESERVE_COUNT = 3

def cleanup_temp_dir(temp_directory):
    directory_list = []
    for file in os.listdir(temp_directory):
        full_path = os.path.join(temp_directory, file)
        if os.path.isdir(full_path):
            directory_list.append(full_path)
    directory_list.sort()
    directory_len = len(directory_list)
    print(f"cleanup_temp(), len(directory_list) = {directory_len}")
    preserve_list = directory_list[-PRESERVE_COUNT:]
    kill_count = directory_len - PRESERVE_COUNT
    kill_list = directory_list[:kill_count]
    print(f"kill_list({len(kill_list)}): {kill_list}")
    print(f"preserve_list({len(preserve_list)}): {preserve_list}")
    for directory in kill_list:
        shutil.rmtree(directory)

def make_temp_dir():
    now = datetime.datetime.now()
    cleanup_temp_dir(TEMP_DIRECTORY)
    folder_snapshot = now.strftime("%Y%m%d_%H%M%S")
    full_path = os.path.join(TEMP_DIRECTORY, folder_snapshot)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    # print(f"tasks.py:make_temp_dir(), full_path = {full_path}")
    return full_path

def generate_prodigy_config(dir_path):
    data = {
        "host": "0.0.0.0",
        "port": 8081,
        "db": "postgresql",
        "db_settings": {
            "postgresql": {
                "dbname": "prodigy",
                "user": "cb_admin",
                "password": "Ch0c0late!",
                "host": "localhost",
                "port": 5432
        }
    }
    json_string = json.dumps(data) + "\n"

    config_file = os.path.join(dir_path, FILE_PRODIGY_CONFIG)
    with open(config_file, "w") as file_writer:
        file_writer.write(json_string)
    return config_file

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

    prodigy_config = generate_prodigy_config(dir_path)

    file_output = os.path.join(dir_path, FILE_OUTPUT)

    return file_path_text, file_path_label, prodigy_config, file_output 

@shared_task(bind=True)
def prodigy_start(self, *args, **kwargs):
    print(f"invoke_prodigy(), self = {self}")
    file_id = kwargs['file_id']

    dir_path = make_temp_dir()
    file_path_text, file_path_label, config_file, output_file = generate_prodigy_files(dir_path, file_id)

    recipe = "ner.manual"
    ner_dataset = "south_china_sea_01"
    language_model = "en_core_web_sm"

    sys_path_string = ":".join(sys.path)
    new_path = f"{VENV_PATH}/bin:" + sys_path_string
    environment = {
        "VIRTUAL_ENV" : VENV_PATH,
        "PATH" : new_path}
#        "PRODIGY_HOST" : "0.0.0.0" }

    first = f"{PRODIGY_PATH} {recipe} {ner_dataset} {language_model} {file_path_text} "
    second = f"--label {file_path_label} --config {config_file}"
    # second = f"--label {file_path_label}"
    full_command = first + second

    print(f"invoke_prodigy(), full_command:\n{full_command}")
    print(f"                    output_file = {output_file}")
    with open(output_file, "w") as logfile:
        process = subprocess.Popen(full_command, shell=True, stdout=logfile, stderr=logfile,
            env=environment)

    return process.pid

