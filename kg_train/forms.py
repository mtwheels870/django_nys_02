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
    selected_file_id = forms.IntegerField(widget=forms.HiddenInput(), required=False, initial=0)
    text_editor = ProseEditorFormField()

class MyForm(forms.Form):
    # Add any other fields you need here
    pass
