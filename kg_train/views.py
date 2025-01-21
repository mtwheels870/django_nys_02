from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone

from .models import TextFileStatus, TextFile
from .forms import UploadFileForm

class IndexView(generic.ListView):
    template_name = "kg_train/index.html"
    context_object_name = "uploaded_files_list"

    def get_queryset(self):
        """ Return the last five published questions."""
        return TextFile.objects.filter(date_uploaded=timezone.now()).order_by("-date_uploaded")[:20]

def upload_file(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
class UploadFileForm(forms.ModelForm):
        if form.is_valid():
            form.save()
            handle_uploaded_file(request.FILES["file"])
            return render("success.html")
    else:
        form = UploadFileForm()
    return render(request, "upload.html", {"form": form})
