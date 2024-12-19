from django.contrib import admin
from django.contrib.gis import admin

from centralny.models import Marker

@admin.register(Marker)
class MarkerAdmin(admin.GISModelAdmin):
    list_display = ("name", "location")

# Register your models here.
