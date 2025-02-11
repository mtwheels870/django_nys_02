from django import forms
from django_prose_editor.fields import ProseEditorFormField

from .models import CountRangeTract

class SelectedCensusTractForm(forms.ModelForm):
    class Meta:
        model = CountRangeTract
        fields = [ 'id' ]

