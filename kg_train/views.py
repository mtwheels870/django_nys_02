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
        # print(f"TFDW.get_context_data(), folder_id = {self.folder_id}")
        return context

    def get_queryset(self):
        self.folder_id = self.kwargs.get('folder_id')
        return TextFile.objects.filter(folder_id=self.folder_id).order_by("page_number")

    def label_page(self, request, folder_id, file_id):
        print(f"TFDV.label_page(), calling command")
        return HttpResponseRedirect(reverse("app_kg_train:file_label", args=(folder_id, file_id,)))

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
                return self.label_page(request, folder_id, file_id)
            else:
                print(f"TFDV.post(), unrecognized button")
                return redirect(request.path)

class TextFileEditView(generic.edit.FormView):
    # model = TextFile
    form_class = EditorForm
    template_name = "kg_train/file_edit.html"
    success_url = "kg_train/index.html"
    initial_text = "Placeholder here"

    def get_context_data(self, **kwargs):
        # print(f"TFEV.get_context_data(*kwargs)")
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
        # print(f"TFEV.get_success_url(), folder_id = {folder_id}")
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
        print(f"TFLV.g_o(), looking up file_id (1st)")
        context_data = self.get_context_data()
        file_id = self.context_data['file_id']
        print(f"TFLV.g_o(), file_id = {file_id}")
        return TextFile.objects.filter(file_id=file_id)

    def get_context_data(self, **kwargs):
        print(f"TFLV.g_c_d(), loading other objects (2nd)")
        # print(f"TFEV.get_context_data(*kwargs)")
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

        return context_data

    def post(self, request, *args, **kwargs):
        folder_id = kwargs["folder_id"]
        file_id = kwargs["file_id"]
        return HttpResponseRedirect(reverse("app_kg_train:detail", args=(folder_id,)))

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
        result = HttpResponseRedirect(reverse("app_kg_train:file_edit", args=(file_id,)))
        print(f"edit_file(), result = {result}")
        return result

