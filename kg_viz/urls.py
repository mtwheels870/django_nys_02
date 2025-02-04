from django.urls import path, include

from . import views

app_name = "app_kg_viz"
#    path("form/", views.StartForm.as_view(), name="upload_form"),
urlpatterns = [
    # ex: /tutorial/.  Note, these are all formal classes (IndexView, DetailView...) inside views.py
    path("", views.DatasetIndexView.as_view(), name="index"),

    # To view an individual file details (and start labeling)
    path("<int:pk>/", views.DatasetDetailView.as_view(), name="detail"),
]
