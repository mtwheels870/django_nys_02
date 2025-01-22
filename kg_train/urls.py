from django.urls import path

from . import views

app_name = "app_kg_train"
#    path("form/", views.StartForm.as_view(), name="upload_form"),
urlpatterns = [
    # ex: /tutorial/.  Note, these are all formal classes (IndexView, DetailView...) inside views.py
    path("", views.IndexView.as_view(), name="index"),

    # To upload a new file to the server (GET and POST)
    path("upload/", views.upload_file, name="upload_file"),

    # To view an individual file details (and start labeling)
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),

    path("<int:pk>/", views.DetailView.as_view(), name="detail"),

    path("edit/", views.edit_file, name="edit_file"),

    # This breaks out to our editor
    path("edit/prose/", include("prose.urls"), name="prose"),

    # ex: /tutorial/5/
]
#    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    # ex: /tutorial/5/results/
#    path("<int:pk>/label/", views.ResultsView.as_view(), name="label"),
