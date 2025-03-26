from django.urls import path, include
from django.views.generic import TemplateView
from django.shortcuts import redirect

from . import views, views_ping, api

# path("api/markers", views.MarkerViewSet.as_view({'get': 'list'}), name="markers")
# path("ping/", TemplateView.as_view(template_name="centralny/ping_strategy.html")),

# We can use this app_name inside the HTML
app_name = "app_powerscan"

urlpatterns = [
    path("map/", views.MapNavigationView.as_view(), name="map_viewer"),

    path("ping/<int:survey_id>", views_ping.ConfigurePingView.as_view(), name="ping_strat_index"),
    path("ping/", redirect("app_powerscan:ping", args=(0,)), name="ping_strat_index"),
    path("surveys/", views_ping.RecentSurveyView.as_view(), name="survey_table"),
    path("tasks/", views_ping.CeleryTasksView.as_view(), name="task_table"),
    path("schedule-survey/<int:pk>", views_ping.ScheduleSurveyView.as_view(), name="schedule_survey"),
    # ex: /tutorial/5/
]
    #path("chat/", views.chat_index, name="chat_index"),
    #path("chat/<str:room_name>/", views.chat_room, name="chat_room"),
#print(f"markers.urlpatterns = {urlpatterns}")
#    path("map/", TemplateView.as_view(template_name="centralny/map_viewer.html")),
#    path("ping/<int:pk>/", views.PingStrategyDetailView.as_view(), name="ping_strat_detail"),
    # ex: /tutorial/5/results/
#    path("ping/<int:pk>/results/", views.PingStrategyResultsView.as_view(), name="ping_strat_results"),
    # ex: /tutorial/5/vote/
#    path("ping/<int:id>/approve", views.approve_ping, name="approve_ping"),
