from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path("viewer/", TemplateView.as_view(template_name="map.html")),
]
