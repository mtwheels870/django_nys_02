from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone

from .models import TextFileStatus, TextFile

class IndexView(generic.ListView):
    template_name = "kg_train/index.html"
    context_object_name = "uploaded_files_list"

    def get_queryset(self):
        """ Return the last five published questions."""
        return TextFile.objects.filter(date_uploaded=timezone.now()).order_by("-date_uploaded ")[:20]

