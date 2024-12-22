from django.contrib import admin
from django.contrib.gis import admin

from centralny.models import Marker, CensusBorderCounty, CensusTract, DeIpRange

@admin.register(Marker)
class MarkerAdmin(admin.GISModelAdmin):
    list_display = ("name", "location")

@admin.register(CensusBorderCounty)
class CensusBorderCountyAdmin(admin.GISModelAdmin):
    list_display = ("name", "location")

@admin.register(CensusTract)
class CensusTractAdmin(admin.GISModelAdmin):
    list_display = ("name", "location")

@admin.register(DeIpRange)
class DeIpRangeAdmin(admin.GISModelAdmin):
    list_display = ("name", "location")
