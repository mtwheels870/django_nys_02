from django.urls import path, include

from . import views

app_name = "app_kg_viz"
#    path("form/", views.StartForm.as_view(), name="upload_form"),
urlpatterns = [
    # ex: /tutorial/.  Note, these are all formal classes (IndexView, DetailView...) inside views.py
    path("", views.IndexView.as_view(), name="index"),

    # To view an individual file details (and start labeling)
    path("<int:dataset_id>/", views_folder.DatasetDetailView.as_view(), name="detail"),

]
