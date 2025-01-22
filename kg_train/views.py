from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
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

# On hitting "upload" button, we end up here
# Actually, this view handles both GET and POST requests.
def upload_file(request):
    print(f"upload_file(), request.method = {request.method}, files: {request.FILES}")
    if request.method == "POST":
        # form = UploadFileForm(request.POST, request.FILES)
        form = UploadFileForm(request.POST)
        if form.is_valid():
            print(f"upload_file(), VALID")
            form.save()
            handle_uploaded_file(request.FILES["file"])
            return render("success.html")
        else:
            print(f"upload_file(), INVALID")
    # else, we're == GET
    else:
        form = UploadFileForm()
        # This will fall through to the following
    return render(request, "kg_train/upload.html", {"form": form})
