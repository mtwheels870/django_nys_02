"""
URL configuration for DJANGO project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

# I don't understand why: path("map/api/", can't me moved to the markers/ level, but include("api") won't work
urlpatterns = [
    path('admin/', admin.site.urls),
    path("powerscan/", include("powerscan.urls")),
    path("powerscan/api/", include("powerscan.api")),
    path("kg_admin/", include("kg_admin.urls")),
    path("kg_train/", include("kg_train.urls")),
    path("kg_viz/", include("kg_viz.urls")),
    path('admin/statuscheck/', include('celerybeat_status.urls'))
]
#print(f"project.urlpatterns = {urlpatterns}")
