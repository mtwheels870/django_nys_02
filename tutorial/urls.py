from django.urls import path

from . import views

app_name = "app_tut"
urlpatterns = [
    # ex: /tutorial/.  Note, these are all formal classes (IndexView, DetailView...) inside views.py
    path("", views.IndexView.as_view(), name="index"),
    # ex: /tutorial/5/
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    # ex: /tutorial/5/results/
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    # ex: /tutorial/5/vote/
    path("<int:question_id>/vote/", views.vote, name="vote"),
]
