from django import forms
from django.forms import ModelForm

from .models import CountRangeTract, IpRangePing

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
    CHOICES = [
        ["value1", "Label 1"],
        ["value2", "Label 2"],
        ["value3", "Label 3"],
    ]
    my_field = forms.ChoiceField(choices=CHOICES)

class IpRangePingForm(ModelForm):
    class Meta:
        model = IpRangePing
        fields = ["time_pinged"]
