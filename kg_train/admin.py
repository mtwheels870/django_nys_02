from django import forms
from django.db import models
from django.contrib import admin

import file_picker

from .models import TextFile, NerLabel

class TextFileForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        print(f"TextFileForm.__init__()")
        super(TextFileForm, self).__init__(*args, **kwargs)
        from file_picker.widgets import SimpleFilePickerWidget
        from file_picker.wymeditor.widgets import WYMeditorWidget
        pickers = {'image': "images", 'file': "files"}
        # simple widget
        simple_widget = SimpleFilePickerWidget(pickers=pickers)
        self.fields['file_name'].widget = simple_widget
        # wymeditor widget
        wym_widget = WYMeditorWidget(pickers=pickers)
        self.fields['aws_file_path'].widget = wym_widget

    class Meta(object):
        model = TextFile
        fields = '__all__'

class TextFileAdmin(admin.ModelAdmin):
    print(f"TextFileAdmin.ctor()")
    formfield_overrides = {
        # This overrides all text fields (not by name)
        models.TextField: {
            'widget': file_picker.widgets.SimpleFilePickerWidget(pickers={
                'image': "images", # a picker named "images" from file_picker.uploads
                'file': "files", # a picker named "files" from file_picker.uploads
            }),
        },
    }

    form = TextFileForm

    class Media:
        js = ("http://cdn.jquerytools.org/1.2.5/full/jquery.tools.min.js",)

admin.site.register(TextFile, TextFileAdmin)

# Don't need a custom admin for this one
admin.site.register(NerLabel)
