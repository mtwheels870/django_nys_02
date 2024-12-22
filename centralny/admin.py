from django.contrib import admin
from django.contrib.gis import admin

from centralny.models import Marker, CensusBorderCounty, CensusTract, DeIpRange

@admin.register(Marker)
class MarkerAdmin(admin.GISModelAdmin):
    list_display = ("name", "location")

@admin.register(CensusBorderCounty)
class CensusBorderCountyAdmin(admin.GISModelAdmin):
    fieldsets = [
        (None, {"fields": ["county_name", "county_code", "pop2000"]}),
        ("Geography", {"fields": ["mpoly"], 
            "classes": ["collapse"]}),
    ]
#    list_display = ("county_name", "county_code", "pop2000", "mpoly")

@admin.register(CensusTract)
class CensusTractAdmin(admin.GISModelAdmin):
    fieldsets = [
        (None, {"fields": ["county_code", "short_name"]}),
        ("Geography", {"fields": ["mpoly"], 
            "classes": ["collapse"]}),
    ]

@admin.register(DeIpRange)
class DeIpRangeAdmin(admin.GISModelAdmin):
    list_display = ("ip_range_start", "ip_range_end", "mpoint")
