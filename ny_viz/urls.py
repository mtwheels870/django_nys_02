from django.urls import path

from . import views

app_name = "nys"
urlpatterns = [
    # ex: /nys/
    path("", views.IndexView.as_view(), name="index"),
    # ex: /nys/5/
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    # ex: /nys/5/results/
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    # ex: /nys/5/vote/
    path("<int:question_id>/vote/", views.vote, name="vote"),
]
