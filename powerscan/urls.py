#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, PINP01NT, LLC
#
# https://pinp01nt.com/
#
# All rights reserved.

"""
Docstring here

Authors: Michael T. Wheeler (mike@pinp01nt.com)

"""
from django.urls import path, include
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.views.generic.base import RedirectView

from . import views, views_ping, api

# path("api/markers", views.MarkerViewSet.as_view({'get': 'list'}), name="markers")
# path("ping/", TemplateView.as_view(template_name="centralny/ping_strategy.html")),

# We can use this app_name inside the HTML
app_name = "app_powerscan"

urlpatterns = [
    path("map/", views.MapNavigationView.as_view(), name="map_viewer"),
    path("survey-new/", views_ping.CreateNewSurveyView.as_view(), name="ping_strat_index"),
    path("survey-table/", views_ping.RecentSurveyView.as_view(), name="survey_table"),
    path("task-table/", views_ping.CeleryTasksView.as_view(), name="task_table"),
    path("schedule-survey/<int:pk>", views_ping.ScheduleSurveyView.as_view(), name="schedule_survey"),
    # ex: /tutorial/5/
]
# Cool redirect, wrong page
# path("ping/", RedirectView.as_view(url="ping/0", permanent=True)),
