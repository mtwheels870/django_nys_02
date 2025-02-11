from django import forms

from .models import CountRangeTract

class SelectedCensusTractForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput())

