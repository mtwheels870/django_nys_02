from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, reverse
# from django.urls import reverse
from django.views import generic
from django.views.generic.edit import FormView

from django.utils import timezone

from .models import TextFileStatus, TextFile
from .forms import UploadFileForm

class IndexView(generic.ListView):
    template_name = "kg_train/index.html"
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
    # print(f"upload_file(), request.method = {request.method}, files: {request.FILES}")
    if request.method == "POST":
        debug_post(request.POST)
        form = UploadFileForm(request.POST, request.FILES)
        # form = UploadFileForm(request.POST)
        if form.is_valid():
            text_file = form.save()
            # print(f"upload_file(), VALID, text_file = {text_file}")
            text_file.save()
            # print(f"upload_file(), after save, id = {text_file.id}")
            #return render(request, "kg_train/index.html")
            return reverse("app_kg_train:index")
        else:
            print(f"upload_file(), INVALID, errors = {form.errors}")
    # else, we're == GET
    else:
#        initial_data = {
#            'file_name' : "Extracted from file name",
#            'status' : 1
#        }
        form = UploadFileForm()
        # This will fall through to the following with an empty form to be populated
    return render(request, "kg_train/upload.html", {"form": form})

class DetailView(generic.DetailView):
    model = TextFile
    template_name = "kg_train/detail.html"

    def get_object(self):
        pk = self.kwargs.get('pk')
        return TextFile.objects.get(pk=pk)
