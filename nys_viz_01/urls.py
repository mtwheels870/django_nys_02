from django.urls import path

from . import views

urlpatterns = [
    # ex: /nys/
    path("", views.index, name="index"),
    # ex: /nys/5/
    path("<int:question_id>/", views.detail, name="detail"),
    # ex: /nys/5/results/
    path("<int:question_id>/results/", views.results, name="results"),
    # ex: /nys/5/vote/
    path("<int:question_id>/vote/", views.vote, name="vote"),
]
