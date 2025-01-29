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

# This doesn't strictly edit the TextFile, just the prose_editor field
class EditorForm(forms.Form):
    text_editor = ProseEditorFormField()

class TextLabelForm(forms.Form):
    task_id = forms.CharField(widget=forms.HiddenInput())
