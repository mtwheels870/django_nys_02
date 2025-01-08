import argparse

try:
    from django.core.management.base import NoArgsCommand as BaseCommand
except ImportError:
    from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Fire the zmap tool with a given survey_id"

    def add_arguments(self, parser):
        print(f"Command, setting up parser = {parser}")
        parser.add_argument("survey_id", type=int, help="ID of the survey range to ping", default=4)

    def handle(self, **options):
        import datetime
        from schedule.models import Calendar
        from schedule.models import Event
        from schedule.models import Rule
        print(f"Command.handle(), options = {options}")
        survey_id = options["survey_id"]

        print(f"running zmap, survey_id = {survey_id}")
