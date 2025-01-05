from django.apps import AppConfig

from django.core.signals import request_finished

PINPOINT_CAL_SLUG = "pp"

# I think this name becomes the leading prefix on the database table names, etc.
class MyCalendarConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mycalendar'
    
    def __init__(self):
        self.calendar_pp = Calendar.objects.filter(slug__eq=PINPOINT_CAL_SLUG)

    def ready(self):
        from . import signals
        request_finished.connect(signals.my_callback)
