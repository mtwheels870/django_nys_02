from django.contrib import admin
from django.contrib.gis import admin

from markers.models import Marker

@admin.register(Marker)
class MarkerAdmin(admin.GISModelAdmin):
    list_display = ("name", "location")

# Register your models here.
