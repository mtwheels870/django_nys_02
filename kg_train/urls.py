from django.urls import path, include

from . import views_folder, views_file

PRODIGY_URL = "http://18.208.200.162:8080/"

app_name = "app_kg_train"
#    path("form/", views.StartForm.as_view(), name="upload_form"),
urlpatterns = [
    # ex: /tutorial/.  Note, these are all formal classes (IndexView, DetailView...) inside views.py
    path("", views_folder.IndexView.as_view(), name="index"),

    # To upload a new file to the server (GET and POST)
    path("upload/", views_folder.upload_folder, name="upload_folder"),

    # To view an individual file details (and start labeling)
    path("<int:folder_id>/", views_folder.TextFolderDetailView.as_view(), name="detail"),

    # path("<int:file_id>/edit/", views.edit_file, name="edit_file"),
    path("<int:folder_id>/<int:file_id>/file-edit/", views_file.TextFileEditView.as_view(), name="file_edit"),
    path("<int:folder_id>/<int:file_id>/file-label/", views_file.TextFileLabelView.as_view(), name="file_label"),

    path("labels/", views_file.NerLabelDetailView.as_view(), name="labels"),
    # This breaks out to our editor
    # path("prose/attachment/", include("prose.urls"), name="prose"),

    # ex: /tutorial/5/
]
#    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    # ex: /tutorial/5/results/
#    path("<int:pk>/label/", views.ResultsView.as_view(), name="label"),
