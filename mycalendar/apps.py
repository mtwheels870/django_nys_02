import sys

from django.apps import AppConfig
from django.core.signals import request_finished
from django.utils import timezone

CALENDAR_SLUG_PP = "pp"

# I think this name becomes the leading prefix on the database table names, etc.
#    def __init__(self): self.calendar_pp = Calendar.objects.filter(slug__eq=PINPOINT_CAL_SLUG)
class MyCalendarConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mycalendar'

    def ready(self):

        # from . import signals
        # request_finished.connect(signals.my_callback)
        print("MyCalendarConfig.ready(), moved all of the init logic..")
        self.pp_calendar = None

    def get_calendar(self):
        from schedule.models import (Calendar, Event, Rule)

        if self.pp_calendar:
            print(f"Could not find calendar(slug) {CALENDAR_SLUG_PP}")
            return self.pp_calendar;

        try:
            self.pp_calendar = Calendar.objects.get(slug=CALENDAR_SLUG_PP)
            self.rule_daily = Rule.objects.get(name="Daily")
        except Calendar.DoesNotExist:
            print(f"Could not find calendar(slug) {CALENDAR_SLUG_PP}")
            sys.exit(1)
        except Rule.DoesNotExist:
            print("Could not find calendar rules")
            sys.exit(1)
        self.today = timezone.now()
        print("Finished configuring calendar")
