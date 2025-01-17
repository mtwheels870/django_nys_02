from django.urls import path, include
from django.views.generic import TemplateView

# path("api/markers", views.MarkerViewSet.as_view({'get': 'list'}), name="markers")
# path("ping/", TemplateView.as_view(template_name="centralny/ping_strategy.html")),

# We can use this app_name inside the HTML
app_name = "kg_admin"

urlpatterns = [
    path("", TemplateView.as_view(template_name="kg_admin/navigation.html")),
]
#print(f"markers.urlpatterns = {urlpatterns}")
