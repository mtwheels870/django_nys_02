from django import forms

from .models import TextFile

class UploadFileForm(forms.ModelForm):
    class Meta:
        model = TextFile
        fields = [ 'file_name', 'file', 'status' ]
