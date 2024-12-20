from django.contrib import admin

from .models import WorldBorder

class WorldBorderAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["name", "iso3"]}),
        ("Additional Information", {"fields": ["area", "pop2005", "region", "lon", "lat"], 
            "classes": ["collapse"]}),
    ]

# Register your models here.
admin.site.register(WorldBorder, WorldBorderAdmin)
