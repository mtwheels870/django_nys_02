from django.urls import path

from . import views

app_name = "app_kg_train"
urlpatterns = [
    # ex: /tutorial/.  Note, these are all formal classes (IndexView, DetailView...) inside views.py
    path("", views.IndexView.as_view(), name="index"),

    path("kgtrain/upload/", "kg_train/upload_form.html", name="upload_form"),

    path("kgtrain/upload_submit/", views.upload_file, name="upload_file"),
    # ex: /tutorial/5/
]
#    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    # ex: /tutorial/5/results/
#    path("<int:pk>/label/", views.ResultsView.as_view(), name="label"),
