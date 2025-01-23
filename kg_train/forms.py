from django import forms

from .models import DocumentSet

class UploadFolderForm(forms.ModelForm):
    class Meta:
        model = DocumentSet
        fields = [ 'file' ]
