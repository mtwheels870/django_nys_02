import json
import logging

from enum import Enum

from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer, SyncConsumer, AsyncConsumer
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
        # print(f"CeleryResultsHandler.init(), self = {self}")
        self.reset()

    def get_status(self):
        return self._survey_status

    def set_status(self, new_status, task_result=None):
        self._survey_status = new_status
        if task_result:
            #print(f"CeleryResultsHandler.set_status(), self = {self}, task_result = {task_result.task_id}")
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

class ChatConsumer(AsyncWebsocketConsumer):
    # groups = ["task_updates"]
    groups = ["task-one", "task-two"]

    async def connect(self):
        self.topic_name = "task-one"
        #self.room_name = self.scope['url_route']['kwargs']['room_name']
        #self.room_group_name = f"chat_{self.room_name}"
        print(f"ChatConsumer.connect(), group_add {self.topic_name},{self.channel_name}")
        await self.channel_layer.group_add(
            self.topc_name,
            self.channel_name
        )

        print(f"ChatConsumer.connect(), calling accept()")
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.topic_name,
            self.channel_name
        )

    async def receive(self, text_data):
        print(f"ChatConsumer.receive(), text_data = {text_data}")
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
    
        await self.channel_layer.group_send(
            self.topic_name,
            {
                'type': 'chat.message',
                'message': message
            }
        )
    
    async def chat_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))

    def get_channel_name(self):
        print(f"TaskConsumer.g_c_n(), dir(self): {dir(self)}")
        return "MickeyMouse"
    
    async def task_one(self, event):
        print(f"TaskConsumer.task_one(), self = {self}, event = {event}")

    async def task_two(self, event):
        print(f"TaskConsumer.task_two(), self = {self}, event = {event}")

# The Task consumer recieves the results (when the task is done)
class TaskConsumer(AsyncConsumer):
    def __init__(self):
        print(f"TaskConsumer.init()")

    async def connnect(self):
        print(f"TaskConsumer.connect(), we don't get this")
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        print(f"TaskConsumer.disconnect(), never get this")
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def process_task_result(self, message):
        print(f"TaskConsumer.process_task_result(), Task received: ({message['task_result_data']})")
        #self.logger.info(f"TaskConsumer.background_task(), Task received: {message['task_name']}")
        # Perform the task
        await self.channel_layer.group_send(CHANNEL_GROUP_WORKERS,
        {
            # Why is this task.finished?  (and not underscore?)
            "type": "task.finished",
            "result": "Task completed successfully"
        })
    
    async def task_finished(self, message):
        print(f"Task finished with result: {message['result']}")

    async def application_send(self, event):
        await self.send(event['text'])
