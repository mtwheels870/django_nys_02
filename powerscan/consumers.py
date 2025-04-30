#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, PINP01NT, LLC
#
# https://pinp01nt.com/
#
# All rights reserved.

"""
Docstring here

Authors: Michael T. Wheeler (mike@pinp01nt.com)

"""
import json
import logging

from enum import Enum

# from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer, SyncConsumer, AsyncConsumer
from asgiref.sync import async_to_sync

CHANNEL_GROUP_WORKERS = "workers"
CHANNEL_GROUP_CONTROLLERS = "controllers"

CHANNEL_NAME_TASK_RESULT = "task_result"
CHANNEL_NAME_RESULT_ACK = "result_ack"

class CeleryResultsHandler:
    # State machines for ping stuff
    class SurveyStatus(Enum):
        NULL = 0
        STATES_CONFIGURED = 1
        BUILT_WL = 2
        PING_STARTED = 3
        PING_COMPLETED = 4
        TALLY_COMPLETED = 5

        def __str__(self):
            return str(self.name)

    def __init__(self):
        self.reset()

    def get_status(self):
        return self._survey_status

    def set_status(self, new_status, task_result=None):
        self._survey_status = new_status
        if task_result:
            self._pending_task_result[task_result.task_id] = None

    def reset(self):
        self._hash_task_ids = {}
        self._pending_task_result = {}
        self.set_status(self.SurveyStatus.NULL)
        return self.SurveyStatus.NULL

#    def save_pending(self, task_result):
#        self._pending_task_result[task_result.id] = None

    def store_task_result(self, task_result):
        task_id = task_result.task_id
        print(f"store_task_result(), task_result = {task_id}")
        if not task_id in self._pending_task_result:
            print(f"store_task_result(), should not be here!, task_id = {task_id} not in dictionary")

celery_results_handler = CeleryResultsHandler()

