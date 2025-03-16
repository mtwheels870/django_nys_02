import json

from enum import Enum

from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

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
        print(f"CeleryResultsHandler.init(), self = {self}")
        self.reset()

    def get_status(self):
        return self._survey_status

    def set_status(self, new_status, task_result=None):
        self._survey_status = new_status
        if task_result:
            print(f"CeleryResultsHandler.set_status(), self = {self}, task_result = {task_result.task_id}")
            self._pending_task_result[task_result.task_id] = None

    def reset(self):
        self._hash_task_ids = {}
        self._pending_task_result = {}
        self.set_status(self.SurveyStatus.NULL)
        return self.SurveyStatus.NULL

    def save_pending(self, task_result):
        self._pending_task_result[task_result.id] = None

    def store_task_result(self, task_result):
        task_id = task_result.task_id
        print(f"store_task_result(), task_result = {task_id}")
        if not task_id in self._pending_task_result:
            print(f"store_task_result(), should not be here!, task_id = {task_id} not in dictionary")

celery_results_handler = CeleryResultsHandler()

class TaskConsumer(WebsocketConsumer):
    groups = ["task_updates"]

    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def task_completed(self, event):
        message = event["message"]
        print(f"TaskConsumer.task_completed(), message = {message}")
        self.send(text_data=json.dumps({"message" : message}))

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        print(f"ChatConsumer.receive(), read message = {message}")
        reply = "reply to " + message

        #self.send(text_data=json.dumps({"message": message}))
        self.send(text_data=json.dumps({"message": reply}))
