from django.urls import path, include
from django.views.generic import TemplateView

from . import views, api

# path("api/markers", views.MarkerViewSet.as_view({'get': 'list'}), name="markers")
urlpatterns = [
    path("viewer/", TemplateView.as_view(template_name="markers/map.html")),
]
#print(f"markers.urlpatterns = {urlpatterns}")
