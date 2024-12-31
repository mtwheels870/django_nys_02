from django.contrib.gis import admin
from django.contrib import admin

from centralny.models import Marker, County, CensusTract, DeIpRange

@admin.register(Marker)
class MarkerAdmin(admin.GeoModelAdmin):
    list_display = ("name", "location")

@admin.register(County)
class CensusBorderCountyAdmin(admin.GeoModelAdmin):
    fieldsets = [
        (None, {"fields": ["county_name", "county_code", "pop2000"]}),
        ("Geography", {"fields": ["mpoly"], 
            "classes": ["collapse"]}),
    ]
    def get_pop2000(self, obj):
        return obj.pop2000_formatted

    get_pop2000.description = "Population 2000"

#    list_display = ("county_name", "county_code", "pop2000", "mpoly")

@admin.register(CensusTract)
class CensusTractAdmin(admin.GeoModelAdmin):
    fieldsets = [
        (None, {"fields": ["county_code", "short_name"]}),
        ("Geography", {"fields": ["mpoly"], 
            "classes": ["collapse"]}),
    ]

@admin.register(DeIpRange)
class DeIpRangeAdmin(admin.GeoModelAdmin):
    #list_display = ("ip_range_start", "ip_range_end", "mpoint")
    fieldsets = [
        (None, {"fields": ["ip_range_start", "ip_range_end", "de_company_name"]}),
        ("Connection Details", {"fields": ["pp_city", "pp_cxn_speed", "pp_cxn_type"], 
            "classes": ["collapse"]}),
        ("Geography", {"fields": ["mpoint"], 
            "classes": ["collapse"]}),
    ]
