from django import forms

from .models import TextFolder

class UploadFolderForm(forms.ModelForm):
    class Meta:
        model = TextFolder
        fields = [ 'input_path' ]

class EditForm(forms.ModelForm):
    class Meta:
        model = TextFile
        fields = [ 'file_name' ]
