from django import forms
from django_prose_editor.fields import ProseEditorFormField

from .models import CountRangeTract

class SelectedCensusTractForm(forms.ModelForm):
    id = forms.IntField(widget=forms.HiddenInput())

