from django.urls import path, include
from django.views.generic import TemplateView

# from . import views, api

#print(f"markers.urlpatterns = {urlpatterns}")
admin.autodiscover()

urlpatterns = [
    path(r'', TemplateView.as_view(template_name="homepage.html"),),
    path(r'schedule/', include('schedule.urls')),
    path(r'fullcalendar/', TemplateView.as_view(template_name="fullcalendar.html"), name='fullcalendar'),
    path(r'admin/', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path(r'__debug__/', include(debug_toolbar.urls)),
    ]
