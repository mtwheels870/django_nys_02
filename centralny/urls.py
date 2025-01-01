from django.urls import path, include
from django.views.generic import TemplateView

from . import views, api

# path("api/markers", views.MarkerViewSet.as_view({'get': 'list'}), name="markers")
# path("ping/", TemplateView.as_view(template_name="centralny/ping_strategy.html")),

# We can use this app_name inside the HTML
app_name = "app_centralny"

urlpatterns = [
    path("map/", TemplateView.as_view(template_name="centralny/map.html")),
    path("ping/", views.PingStrategyIndexView.as_view(), name="index"),
    # ex: /tutorial/5/
    path("ping/<int:pk>/", views.PingStrategyDetailView.as_view(), name="detail"),
    # ex: /tutorial/5/results/
    path("ping/<int:pk>/results/", views.PingStrategyResultsView.as_view(), name="results"),
]
#print(f"markers.urlpatterns = {urlpatterns}")
