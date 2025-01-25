from django import forms
from django_prose_editor.fields import ProseEditorFormField

from .models import TextFolder, TextFile

class UploadFolderForm(forms.ModelForm):
    class Meta:
        model = TextFolder
        fields = [ 'input_path' ]

class EditForm(forms.ModelForm):
    class Meta:
        model = TextFile
        fields = [ 'file_name' ]

class EditorForm(forms.Form):
    text_editor = ProseEditorFormField()
