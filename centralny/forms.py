from django import forms

from .models import CountRangeTract

class SelectedCensusTractForm(forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput())

