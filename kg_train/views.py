from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.views.generic.edit import FormView

from django.utils import timezone

from prose.models import Document

from .models import TextFileStatus, TextFile
from .forms import UploadFileForm

class IndexView(generic.ListView):
    template_name = "kg_train/file_index.html"
    context_object_name = "uploaded_files_list"

    def get_queryset(self):
        """ Return the last five published questions."""
        # return TextFile.objects.filter(date_uploaded=timezone.now()).order_by("-date_uploaded")[:20]
        return TextFile.objects.all()

# Start the form on this view
#class StartForm(FormView):
#    form_class = UploadFileForm

def debug_post(dictionary):
    for index, key in enumerate(dictionary):
        value = dictionary[key]
        print(f"d_p(), key[{index}]: {key} = {value}")
    
# On hitting "upload" button, we end up here
# Actually, this view handles both GET and POST requests.
def upload_file(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # This uses the Form to create an instance (TextFile)
            text_file = form.save()
            file = form.cleaned_data['file']
            text_file.file_name = file.name
            text_file.file_size = file.size
            file_content = text_file.file.read()
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
        initial_data = {
            'file_name' : "(Extracted from file name)",
            'status' : 1
        }
        form = UploadFileForm(initial=initial_data)
        # This will fall through to the following with an empty form to be populated
    return render(request, "kg_train/file_upload.html", {"form": form})

class DetailView(generic.DetailView):
    model = TextFile
    template_name = "kg_train/file_detail.html"

    def get_object(self):
        pk = self.kwargs.get('pk')
        return TextFile.objects.get(pk=pk)

    # print(f"upload_file(), request.method = {request.method}, files: {request.FILES}")
        # debug_post(request.POST)
        # form = UploadFileForm(request.POST)
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
