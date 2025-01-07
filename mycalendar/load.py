from .models import (
    ScheduleType
)

class Loader():
    def __init__(self):
        self.counter = 0

    def create_types(self, verbose=True):
        types = ["TractDensity", "GeographicCoverage", "ASAP"]
        for survey_name in types:
            st = ScheduleType(survey_name=survey_name)
            st.save()
