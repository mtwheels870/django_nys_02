import json

from enum import Enum

from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer, SyncConsumer


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

class TaskConsumer(AsyncWebsocketConsumer):
    # groups = ["task_updates"]
    groups = ["task-one", "task-two"]

    async def connect(self):
        self.topic_name = "task-one"
        #self.room_name = self.scope['url_route']['kwargs']['room_name']
        #self.room_group_name = f"chat_{self.room_name}"
        print(f"TaskConsumer.connect(), group_add {self.topic_name},{self.channel_name}")
        await self.channel_layer.group_add(
            self.topc_name,
            self.channel_name
        )

        print(f"TaskConsumer.connect(), calling accept()")
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.topic_name,
            self.channel_name
        )

    async def receive(self, text_data):
        print(f"TaskConsumer.receive(), text_data = {text_data}")
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

I am trying to set up an app which uses django2.0.2 and channels2.1.1. What I would like to achieve is using a background/worker task to perform some work that will produce data, that should dynamically appear on the website. My problem, related primarily to channels, is: how do I correctly establish communication between the worker, and the consumer connected to a websocket?

Below is a minimal example highlighting the issue: The idea is that the user triggers the worker, the worker produces some data and sends it, via the channel layer, to a consumer that is connected to the websocket.

#routing.py
from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from testApp.consumers import *

application = ProtocolTypeRouter({
    "websocket":AuthMiddlewareStack(
        URLRouter([
            path("wspath",TestConsumer),
        ]),
    ),
    "channel":ChannelNameRouter({
        "test_worker": TestWorker,
    }),
})
The consumers:

#consumers.py
from channels.consumer import SyncConsumer
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

class TestConsumer(WebsocketConsumer):
    def websocket_connect(self,message):
        async_to_sync(self.channel_layer.group_add)("testGroup",self.channel_name)
        self.connect()
        #I understand this next part is a bit weird, but I figured it 
        #is the most concise way to explain my problem
        async_to_sync(self.channel_layer.group_send)(
            "testGroup",
            {
                'type':"echo_msg",
                'msg':"sent from WebsocketConsumer",
            })

    def echo_msg(self, message):
        print("Message to WebsocketConsumer", message)

class TestWorker(SyncConsumer):
    def triggerWorker(self, message):
        async_to_sync(self.channel_layer.group_add)("testGroup",self.channel_name)
        async_to_sync(self.channel_layer.group_send)(
            "testGroup",
            {
                'type':"echo_msg",
                'msg':"sent from worker",
            })

    def echo_msg(self, message):
        print("Message to worker ", message)
