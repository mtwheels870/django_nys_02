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
from .forms import UploadFolderForm
from .tables import TextFileTable
from .tasks import invoke_prodigy, callback_task

class IndexView(generic.ListView):
    template_name = "kg_train/folder_index.html"
    context_object_name = "uploaded_folders_list"

    def get_queryset(self):
        """ Return the last five published questions."""
        # return TextFile.objects.filter(date_uploaded=timezone.now()).order_by("-date_uploaded")[:20]
        return TextFolder.objects.all()
    
# Returns a dictionary of: path : page number
def read_directory(directory_path):
    page_files = {}
    pattern = r"(\d+)_(\d+)\.txt"
    path = pathlib.PurePath(directory_path)
    directory_name = path.name
    max_page_num = None
    files = [f for f in os.listdir(directory_path) if f.endswith(".txt")]
    for file_name in files:
        match = re.search(pattern, file_name)
        if match:
            page_num = int(match.group(1))
            if not max_page_num:
                max_page_num = int(match.group(2))
            else:
                new_max = int(match.group(2))
                if new_max != max_page_num:
                    print(f"WARNING! Previous max = {max_page_num}, new max = {new_max}")
            page_files[file_name] = page_num
    return directory_name, page_files, max_page_num

def read_page_files(text_folder, directory_path, page_files):
    initial_status = TextFileStatus.objects.get(pk=1)
    for i, key in enumerate(page_files):
        page_number = page_files[key]
        # print(f"r_p_f(), page[{key}] = {page_number}")
        full_path = os.path.join(directory_path, key)
        with open(full_path, "r") as file_reader:
            file_content = file_reader.read()
            file_size = len(file_content)
            # body_document = Document.objects.create(content=file_content)
            text_file = TextFile(folder=text_folder, file_name=key, page_number=page_number,
                file_size=file_size, status=initial_status, prose_editor=file_content)
            # print(f"r_p_f(), saving page here...")
            text_file.save()

# On hitting "upload" button, we end up here
# Actually, this view handles both GET and POST requests.
def upload_folder(request):
    if request.method == "POST":
        # form = UploadFolderForm(request.POST, request.FILES)
        form = UploadFolderForm(request.POST)
        if form.is_valid():
            # This uses the Form to create an instance (TextFile)
            text_folder = form.save()
            directory_path = form.cleaned_data['input_path']
            directory_name, page_files, max_page_num = read_directory(directory_path)
            text_folder.folder_name = directory_name
            text_folder.time_uploaded = timezone.now()
            text_folder.pages_original = max_page_num
            text_folder.pages_db = len(page_files)
            text_folder.save()
            print(f"u_f(), path = {directory_path}, num_pages = {text_folder.pages_db}, max_page = {max_page_num}")

            # Now, read the individual pages
            read_page_files(text_folder, directory_path, page_files)
            return HttpResponseRedirect(reverse("app_kg_train:index"))
        else:
            print(f"upload_file(), INVALID, errors = {form.errors}")
    # else, we're == GET
    else:
        form = UploadFolderForm()
        # This will fall through to the following with an empty form to be populated
    return render(request, "kg_train/folder_upload.html", {"form": form})

class TextFolderDetailView(SingleTableView):
    model = TextFile
    table_class = TextFileTable
    template_name = "kg_train/folder_detail.html"
    table_pagination = {
        "per_page": 10
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['folder_id'] = self.folder_id
        # print(f"TFDW.get_context_data(), folder_id = {self.folder_id}")
        return context

    def get_queryset(self):
        self.folder_id = self.kwargs.get('folder_id')
        return TextFile.objects.filter(folder_id=self.folder_id).order_by("page_number")

    def label_page(self, folder_id, file_id):
        # Invoke celery task here
        async_result = invoke_prodigy.apply_async((folder_id, file_id))

        # Handle the signal when we're done
        # task_completed.connect(handle_task_completed)
        request.session["task_id"] = async_result.id
        # request.session["popen_id"] = popen.id
        return redirect(reverse("app_kg_train:file_label", args=(folder_id, file_id,)))

    def post(self, request, *args, **kwargs):
        folder_id = kwargs["folder_id"]
        selected_pks = request.POST.getlist('selection')
        num_selected = len(selected_pks)
        if num_selected  == 0:
            print(f"TFDV.post(), no selected rows")
            return redirect(request.path)
        elif num_selected > 1:
            print(f"TFDV.post(), >1 selected rows")
            return redirect(request.path)
        else:
            # Check which button we're in: edit or label
            file_id = selected_pks[0]
            if 'edit' in request.POST:
                print(f"TFDV.post(), editing page")
                return HttpResponseRedirect(reverse("app_kg_train:file_edit", args=(folder_id, file_id,)))
            elif 'label' in request.POST:
                return self.label_page(folder_id, file_id)
            else:
                print(f"TFDV.post(), unrecognized button:")
                for i, key in enumerate(request.POST):
                    value = request.POST[key]
                    print(f"          [{i}]: {key} = {value}")
                return redirect(request.path)
