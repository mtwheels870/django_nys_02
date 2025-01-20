from django import forms
from django.db import models
from django.contrib import admin

import file_picker

from .models import Post, TextFile

class PostForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        print(f"PostForm.__init__()")
        super(PostForm, self).__init__(*args, **kwargs)
        from file_picker.widgets import SimpleFilePickerWidget
        from file_picker.wymeditor.widgets import WYMeditorWidget
        pickers = {'image': "images", 'file': "files"}
        # simple widget
        simple_widget = SimpleFilePickerWidget(pickers=pickers)
        self.fields['body'].widget = simple_widget
        # wymeditor widget
        wym_widget = WYMeditorWidget(pickers=pickers)
        self.fields['teaser'].widget = wym_widget

    class Meta(object):
        model = Post
        fields = '__all__'

class TextFileForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        print(f"TextFileForm.__init__()")
        super(TextFileForm, self).__init__(*args, **kwargs)
        from file_picker.widgets import SimpleFilePickerWidget
        from file_picker.wymeditor.widgets import WYMeditorWidget
        pickers = {'image': "images", 'file': "files"}
        # simple widget
        simple_widget = SimpleFilePickerWidget(pickers=pickers)
        self.fields['body'].widget = simple_widget
        # wymeditor widget
        wym_widget = WYMeditorWidget(pickers=pickers)
        self.fields['teaser'].widget = wym_widget

    class Meta(object):
        model = TextFile
        fields = '__all__'

class PostAdmin(admin.ModelAdmin):
    print(f"PostAdmin.ctor()")
    formfield_overrides = {
        models.TextField: {
            'widget': file_picker.widgets.SimpleFilePickerWidget(pickers={
                'image': "images", # a picker named "images" from file_picker.uploads
                'file': "files", # a picker named "files" from file_picker.uploads
            }),
        },
    }

    form = PostForm

    class Media:
        js = ("http://cdn.jquerytools.org/1.2.5/full/jquery.tools.min.js",)

class TextFileAdmin(admin.ModelAdmin):
    print(f"TextFileAdmin.ctor()")
    formfield_overrides = {
        models.TextField: {
            'widget': file_picker.widgets.SimpleFilePickerWidget(pickers={
                'image': "images", # a picker named "images" from file_picker.uploads
                'file': "files", # a picker named "files" from file_picker.uploads
            }),
        },
    }

    form = PostForm

    class Media:
        js = ("http://cdn.jquerytools.org/1.2.5/full/jquery.tools.min.js",)


admin.site.register(Post, PostAdmin)
admin.site.register(TextFile, TextFileAdmin)
