from django import forms

from .models import CountRangeTract

class SelectedCensusTractForm(forms.Form):
    agg_type = forms.CharField(widget=forms.HiddenInput())
    id = forms.IntegerField(widget=forms.HiddenInput())
