from django.urls import path, include
from django.views.generic import TemplateView

import debug_toolbar
# from . import views, api

#print(f"markers.urlpatterns = {urlpatterns}")
# admin.autodiscover()
#    path(r'admin/', admin.site.urls),

from . import views

app_name = "app_my_scheduler"

# Why are some things just urls and others templates?  (Need the %% expansion?)
urlpatterns = [
    path(r'', TemplateView.as_view(template_name="homepage.html"),),
    # This is "3rd party" (b/c django-scheduler)
    # File lives here:
    # /home/bitnami/.local/lib/python3.12/site-packages/schedule/urls.py
    path(r'schedule/', include('schedule.urls')),
    path(r'fullcalendar/', TemplateView.as_view(template_name="fullcalendar.html"), name='fullcalendar'),
    path(r"schedule/survey/<int:pk>/", views.ScheduleSurveyDetailView.as_view(), name="schedule_survey_detail"),
    path(r"schedule/survey/<int:pk>/schedule_type", views.set_schedule_type, name="set_schedule_type"),
    path(r"schedule/survey/<int:pk>/done", views.done, name="done"),
]

# if settings.DEBUG:
#    import debug_toolbar.... Don't think this does anything (older version of Django)
urlpatterns += [
    path(r'__debug__/', include(debug_toolbar.urls)),
]
