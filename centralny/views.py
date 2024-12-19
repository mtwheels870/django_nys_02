from django.shortcuts import render

from rest_framework import viewsets
from rest_framework_gis import filters

from centralny.models import Marker
from centralny.serializers import (
    MarkerSerializer,
)

# /maps/api/markers (through DefaultRouter)
class MarkerViewSet(
    viewsets.ReadOnlyModelViewSet):
    # print("MTW, views.MarkerViewSet()")
    bbox_filter_field = "location"
    filter_backends = [filters.InBBoxFilter]
    queryset = Marker.objects.all()
    serializer_class = MarkerSerializer
