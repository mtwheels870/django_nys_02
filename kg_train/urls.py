from django.urls import path, include

from . import views

app_name = "app_kg_train"
#    path("form/", views.StartForm.as_view(), name="upload_form"),
urlpatterns = [
    # ex: /tutorial/.  Note, these are all formal classes (IndexView, DetailView...) inside views.py
    path("", views.IndexView.as_view(), name="index"),

    # To upload a new file to the server (GET and POST)
    path("upload/", views.upload_folder, name="upload_folder"),

    # To view an individual file details (and start labeling)
    path("<int:folder_id>/", views.TextFolderDetailView.as_view(), name="detail"),

    path("<int:folder_id>/edit/", views.edit_file, name="edit_file"),

    # This breaks out to our editor
    # path("prose/attachment/", include("prose.urls"), name="prose"),

    # ex: /tutorial/5/
]
#    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    # ex: /tutorial/5/results/
#    path("<int:pk>/label/", views.ResultsView.as_view(), name="label"),
