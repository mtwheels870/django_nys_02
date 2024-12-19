from django.urls import path, include
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path("viewer/", TemplateView.as_view(template_name="markers/map.html")),
    path("api/", include("./api")),
]
