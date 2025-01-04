from django.apps import AppConfig

from django.core.signals import request_finished

# I think this name becomes the leading prefix on the database table names, etc.
class MyCalendarConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mycalendar'

    def ready(self):
        from . import signals
        request_finished.connect(signals.my_callback)
