from django import forms

from .models import TextFolder

class UploadFolderForm(forms.ModelForm):
    class Meta:
        model = TextFolder
        fields = [ 'input_path' ]
