from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.views.generic.edit import FormView

from django.utils import timezone

from prose.models import Document

from .models import TextFileStatus, TextFile, TextFolder
from .forms import UploadFolderForm

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
    pattern = r"(\w+)@(\w+)\.(\w+)"
    directory_name = os.path.basename(directory_path)
    print(f"read_directory(), directory_name = {directory_name}")
    files = [f for f in os.listdir(directory) if f.endswith(".txt")]
    for file in files:
        name = file.name
        match = re.search(pattern, name)
        if match:
            print(f"read_directory(), name: {name} matched")
            page_file[name] = 23

    return page_files

def read_page_files(text_folder, page_files):
    for i, key in enumerate(page_files):
        page_number = page_files[key]
        print(f"r_p_f(), page[{key}] = {page_number}")

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
            page_files = read_directory(directory_path)
            text_folder.time_uploaded = timezone.now()
            text_folder.total_pages = len(page_files)
            text_folder.save()
            print(f"upload_file(), path = {directory_path}, num_pages = {text_folder.total_pages}")

            # Now, read the individual pages
            read_page_files(text_folder, page_files)
kk
    time_uploaded = models.DateTimeField(null=True)
    total_pages = models.IntegerField("Total pages in original", null=True)
        fields = [ '' ]
            text_file.file_name = file.name
            text_file.file_size = file.size
            file_content = str(text_file.file.read())
            print(f"upload_file(), (cleaned) file_name = {file.name}, file_size ={file.size}")
            body_document = Document.objects.create(content=file_content)
            text_file.body = body_document
            # Should overwrite file_name here
            text_file.save()
            return HttpResponseRedirect(reverse("app_kg_train:index"))
        else:
            print(f"upload_file(), INVALID, errors = {form.errors}")
    # else, we're == GET
    else:
        form = UploadFolderForm()
        # This will fall through to the following with an empty form to be populated
    return render(request, "kg_train/folder_upload.html", {"form": form})

class TextFolderDetailView(generic.DetailView):
    model = TextFolder
    template_name = "kg_train/folder_detail.html"

    def get_object(self):
        pk = self.kwargs.get('pk')
        return TextFolder.objects.get(pk=pk)

    # print(f"upload_file(), request.method = {request.method}, files: {request.FILES}")
        # debug_post(request.POST)
        # form = UploadFolderForm(request.POST)
            # print(f"upload_file(), VALID, text_file = {text_file}")
            # print(f"upload_file(), after save, id = {text_file.id}")
            #return render(request, "kg_train/index.html")
            # return render(request, reverse("app_kg_train:index"))

def edit_file(request, pk):
    text_file = get_object_or_404(TextFile, pk=pk)
    file_content = text_file.file.read()
    initial_content = file_content[:100]
    print(f"initial_content:\n{initial_content}")
    return render(request, reverse("app_kg_train:prose"), {"content": file_content})
