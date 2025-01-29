import os
import pathlib
import re

from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.views.generic.edit import FormView

from django.utils import timezone

from django_tables2 import SingleTableView

from celery import Task
from celery import signals

from .models import TextFileStatus, TextFile, TextFolder
from .forms import UploadFolderForm, EditorForm
from .tables import TextFileTable
from .tasks import invoke_prodigy, callback_task

class TextFileEditView(generic.edit.FormView):
    # model = TextFile
    form_class = EditorForm
    template_name = "kg_train/file_edit.html"
    success_url = "kg_train/index.html"
    initial_text = "Placeholder here"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        # After this, the form is created

        # File stuff
        file_id = self.kwargs.get('file_id')
        context_data['file_id'] = file_id
        text_file = get_object_or_404(TextFile, pk=file_id)
        context_data['page_number'] = text_file.page_number 

        # Folder stuff
        folder_id = self.kwargs.get('folder_id')
        context_data['folder_id'] = folder_id
        text_folder = get_object_or_404(TextFolder, pk=folder_id)
        context_data['folder_name'] = text_folder.folder_name 

        form = context_data['form']
        text_editor = form.fields['text_editor']
        text_editor.initial = text_file.prose_editor
        return context_data

    # Straight override (so we can use reverse)
    def get_success_url(self):
        context_data = self.get_context_data()
        folder_id = context_data['folder_id']
        return reverse("app_kg_train:detail", args=(folder_id,))

    def post(self, request, *args, **kwargs):
        # print(f"TFEV.post(), kwargs = {kwargs}")
        form = EditorForm(request.POST)
        if form.is_valid():
            text_editor_data = form.cleaned_data['text_editor']
            file_id = kwargs["file_id"]
            text_file = get_object_or_404(TextFile, pk=file_id)
            text_file.time_edited = timezone.now()
            text_file.prose_editor = text_editor_data 
            text_file.save()
        else:
            print(f"TFEV.post(), form is INVALID")
        return HttpResponseRedirect(self.get_success_url())

class TextFileLabelView(generic.DetailView):
    model = TextFile
    template_name = "kg_train/file_label.html"

    def get_object(self):
        file_id = self.kwargs['file_id']
        return TextFile.objects.filter(id=file_id)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        task_id = self.request.session["task_id"]
        context_data["task_id"] = task_id

        # File stuff
        file_id = self.kwargs.get('file_id')
        context_data['file_id'] = file_id
        text_file = get_object_or_404(TextFile, pk=file_id)
        context_data['page_number'] = text_file.page_number 

        # Folder stuff
        folder_id = self.kwargs.get('folder_id')
        context_data['folder_id'] = folder_id
        text_folder = get_object_or_404(TextFolder, pk=folder_id)
        context_data['folder_name'] = text_folder.folder_name 

        return context_data

    def post(self, request, *args, **kwargs):
        folder_id = kwargs["folder_id"]
        file_id = kwargs["file_id"]
        # context_data = self.get_context_data()
        # task_id = context_data["task_id"]
        print(f"TFLV.post(), dir(self) = {dir(self)}")
        for i, key in request;
            value = request[key]
            print(f"    [{i}] {key} = {value}")
        if 'save' in request.POST:
            print(f"TFLV.post(), save labels before we leave, task_id = {task_id}")
        elif 'exit' in request.POST:
            print(f"TFLV.post(), discard labels before we leave, task_id = {task_id}")
        return HttpResponseRedirect(reverse("app_kg_train:detail", args=(folder_id,)))

