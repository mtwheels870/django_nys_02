import os
import pathlib
import re

from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
# from django.views.generic import SingleObjectMixin
from django.views.generic.edit import FormView

from django.utils import timezone

# from prose.models import Document
# import django_tables2 as tables
from django_tables2 import SingleTableView

from .models import TextFileStatus, TextFile, TextFolder
from .forms import UploadFolderForm, EditorForm
from .tables import TextFileTable

class IndexView(generic.ListView):
    template_name = "kg_train/folder_index.html"
    context_object_name = "uploaded_folders_list"

    def get_queryset(self):
        """ Return the last five published questions."""
        # return TextFile.objects.filter(date_uploaded=timezone.now()).order_by("-date_uploaded")[:20]
        return TextFolder.objects.all()

# Start the form on this view
#class StartForm(FormView):
#    form_class = UploadFileForm

def debug_post(dictionary):
    for index, key in enumerate(dictionary):
        value = dictionary[key]
        print(f"d_p(), key[{index}]: {key} = {value}")
    
# Returns a dictionary of: path : page number
def read_directory(directory_path):
    page_files = {}
    pattern = r"(\d+)_(\d+)\.txt"
    path = pathlib.PurePath(directory_path)
    directory_name = path.name
    max_page_num = None
    # print(f"read_directory(), path = {directory_path}, directory_name = {directory_name}")
    files = [f for f in os.listdir(directory_path) if f.endswith(".txt")]
    for file_name in files:
        # print(f"read_directory(), checking file name {file_name}")
        match = re.search(pattern, file_name)
        if match:
            page_num = int(match.group(1))
            if not max_page_num:
                max_page_num = int(match.group(2))
            else:
                new_max = int(match.group(2))
                if new_max != max_page_num:
                    print(f"WARNING! Previous max = {max_page_num}, new max = {new_max}")
            # print(f"read_directory(), name: {file_name} matched, page = {page_num}")
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
        print(f"TFDW.get_context_data(), folder_id = {self.folder_id}")
        return context

    def get_queryset(self):
        self.folder_id = self.kwargs.get('folder_id')
        return TextFile.objects.filter(folder_id=self.folder_id).order_by("page_number")

    def post(self, request, *args, **kwargs):
        selected_pks = request.POST.getlist('selection')
        print(f"DEBUG: TFDV.post(), selected_pks = {selected_pks}")
        num_selected = len(selected_pks)
        if num_selected  == 0:
            print(f"TFDV.post(), no selected rows")
            return redirect(request.path)
        elif num_selected > 1:
            print(f"TFDV.post(), >1 selected rows")
            return redirect(request.path)
        else:
            # Good case (1 selected)
            request.method = "GET"
            # selected_rows = TextFile.objects.filter(pk__in=selected_pks)
            #file_id = selected_rows[0]
            file_id = selected_pks[0]
            print(f"Selected file id: {file_id}")
            return HttpResponseRedirect(reverse("app_kg_train:edit_view", args=(file_id,)))

def edit_file(request, file_id):
    print(f"edit_file(), method = {request.method}, file_id = {file_id}:")
    text_file = get_object_or_404(TextFile, pk=file_id)
    if request.method == "POST":
        # form = UploadFolderForm(request.POST, request.FILES)
        form = EditorForm(request.POST)
        if form.is_valid():
            # This is NOT a model based ford (so no save)
            text_editor_data = form.cleaned_data['text_editor']
            print(f"edit_file(), text_editor_data = {text_editor_data}")
            # print(f"edit_file(), new_text_area = {new_text_area}")
        else:
            print(f"ERROR: upload_file(), INVALID, errors = {form.errors}")
        folder_id = text_file.folder.id
        # This should go back to the folder view (with all of the pages)
        return HttpResponseRedirect(reverse("app_kg_train:detail", args=(folder_id,)))
    # else, we're == GET
    else:
        initial_text = "Four score and seven years ago"
        form = EditorForm(initial={'text_editor': initial_text})
        # print(f"Before render, form = {form}")
        # This will fall through to the following with an empty form to be populated
        print(f"edit_file(), setting up context here, form = {form}")
        context = {"form": form, "file_id": file_id}
        # return render(request, "kg_train/file_edit.html", context)
        result = HttpResponseRedirect(reverse("app_kg_train:edit_file", args=(file_id,)))
        print(f"edit_file(), result = {result}")
        return result

class TextFileEditView(generic.edit.FormView):
    # model = TextFile
    form_class = EditorForm
    template_name = "kg_train/file_edit.html"
    success_url = "kg_train/index.html"

    def get_initial(self):
        initial = super().get_initial()
        print(f"TFEV.get_initial()")
        initial["text_editor"] = "Four score and seven years ago"
        return initial


# attrs = dir(form)
# print(f"attrs: {attrs}")
#            print(f"TFDV.post(), cleaned_data:")
#            for i, key in enumerate(cleaned_data):
#                value = cleaned_data[key]
#                print(f"{i}: [{key}] = {value}")
