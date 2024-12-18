from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path("viewer/", views.TemplateView.as_view(), name="map.html"),
]
