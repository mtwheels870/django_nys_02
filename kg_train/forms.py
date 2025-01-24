from django import forms
from django_prose_editor.fields import ProseEditorFormField

from js_asset import JS

from .models import TextFolder, TextFile

DJANGO_PROSE_EDITOR_PRESETS = {
    "announcements": [
        JS("prose-editors/announcements.js", {"defer": True}),
    ],
}

class UploadFolderForm(forms.ModelForm):
    class Meta:
        model = TextFolder
        fields = [ 'input_path' ]

class EditForm(forms.ModelForm):
    class Meta:
        model = TextFile
        fields = [ 'file_name' ]

class EditorForm(forms.Form):
    text = ProseEditorFormField(_("text"), preset="announcements")
