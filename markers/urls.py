from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path(
        "viewer/", views.TemplateView.as_view(), name="map.html"),
    ),
]
