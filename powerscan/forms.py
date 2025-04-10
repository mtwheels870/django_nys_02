from django import forms
from django.forms import ModelForm
from django.forms.widgets import SplitDateTimeWidget

#from django.forms import DateTimeField
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime

from .models import CountTract, IpRangePing, UsState

# widget=forms.HiddenInput())
class SelectedAggregationForm(forms.Form):
    agg_type = forms.CharField(widget=forms.HiddenInput())
    survey_id = forms.IntegerField(label="Survey ID", widget=forms.HiddenInput())
    time_pinged = forms.DateTimeField(label="Time Pinged (EDT)", widget=forms.HiddenInput()))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
#        self.fields['agg_type'].widget.attrs['readonly'] = True
#        self.fields['survey_id'].widget.attrs['readonly'] = True
#        self.fields['time_pinged'].widget.attrs['readonly'] = True

#    def render_time_pinged(self, value, record):
#        return f"Render: {value} here"

class PingStrategyForm(forms.Form):
    choices = []
    for state in UsState.objects.all().order_by("state_name"):
        choices.append([state.state_fp, state.state_name])
    field_states = forms.MultipleChoiceField(
        choices=choices,
        widget=forms.SelectMultiple, label="Select State(s) to Ping:") 
    # field_survey_id = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}),
    field_survey_id = forms.CharField(label="Survey Id (if created)", initial="0")

class CustomDateTimeField(forms.DateTimeField):
    def to_python(self, value):
        if isinstance(value, list):
            if all(v is None for v in value):
                return None
            value = ' '.join(str(v) for v in value if v is not None)
        try:
            return parse_datetime(value)
        except (ValueError, TypeError):
            raise ValidationError("Enter a valid date/time.")

class ScheduleSurveyForm(forms.Form):
    field_survey_id = forms.IntegerField(label="Survey ID:")
    field_survey_name = forms.CharField(label="States:")
    field_start_time = CustomDateTimeField(label="Start Time (first ping):", widget=SplitDateTimeWidget)
    # field_start_time = forms.DateTimeField(label="Start Time (first ping):", widget=SplitDateTimeWidget)
    field_recurring = forms.DurationField(label="Recurring (time amount)", required=False)
    field_num_occurrences = forms.IntegerField(label="Num Occurrences:", initial=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['field_survey_id'].widget.attrs['readonly'] = True
        self.fields['field_survey_name'].widget.attrs['readonly'] = True
    
    class Meta:
        fields = "__all__"

