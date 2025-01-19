from django.urls import path

from . import views

app_name = "app_kg_train"
urlpatterns = [
    # ex: /tutorial/.  Note, these are all formal classes (IndexView, DetailView...) inside views.py
    path("", views.IndexView.as_view(), name="index"),
    # ex: /tutorial/5/
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    # ex: /tutorial/5/results/
    path("<int:pk>/label/", views.ResultsView.as_view(), name="label"),
]
