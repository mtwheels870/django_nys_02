from django import forms
from django.forms import ModelForm

from .models import CountTract, IpRangePing, UsState

# widget=forms.HiddenInput())
class SelectedCensusTractForm(forms.Form):
    #agg_type = forms.CharField(initial="SomeType")
    #id = forms.IntegerField(initial=23)
    #map_bbox = forms.CharField(initial="a=b")
    agg_type = forms.CharField()
    id = forms.IntegerField(label="Db ID")
    range_count = forms.IntegerField(label="Total IP Ranges")
    map_bbox = forms.CharField(widget=forms.HiddenInput())

    # Range count doesn't work for IP ranges (looks like a single range, really many)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['agg_type'].widget.attrs['readonly'] = True
        self.fields['id'].widget.attrs['readonly'] = True
        self.fields['range_count'].widget.attrs['readonly'] = True
        self.fields['map_bbox'].widget.attrs['readonly'] = True

class PingStrategyForm(forms.Form):
    choices = []
    for state in UsState.objects.all().order_by("state_name"):
        choices.append([state.state_fp, state.state_name])
    field_states = forms.MultipleChoiceField(
        choices=choices,
        widget=forms.SelectMultiple, label="Select State(s) to Ping:") 
    # field_survey_id = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}),
    field_survey_id = forms.CharField(label="Survey Id (if created)", initial="0")

class ScheduleSurveyForm(forms.Form):
    field_survey_id = forms.IntegerField(label="Survey ID:")
    field_survey_name = forms.CharField(label="States:")
    field_start_time = forms.DateTimeField(label="Start Time (first ping):")
    field_recurring = forms.DurationField(label="Recurring (amount)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['field_survey_id'].widget.attrs['readonly'] = True
        self.fields['field_survey_name'].widget.attrs['readonly'] = True
    

