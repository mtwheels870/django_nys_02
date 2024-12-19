from django.urls import path, include
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("markers.api")),
    path("viewer/", TemplateView.as_view(template_name="markers/map.html")),
]
