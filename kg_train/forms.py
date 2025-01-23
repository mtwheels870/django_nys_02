from django import forms

from .models import DocumentSet

class UploadFolderForm(forms.ModelForm):
    class Meta:
        model = TextFile
        fields = [ 'file', 'file_name', 'status' ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'status' in self.data:
            self.fields['status'].initial = 1

