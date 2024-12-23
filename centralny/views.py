import logging
from django.shortcuts import render

from rest_framework import viewsets
from rest_framework_gis import filters

from centralny.models import Marker, CensusTract, County, DeIpRange

from centralny.serializers import (
    MarkerSerializer,
    CensusTractSerializer,
    CountySerializer,
    DeIpRangeSerializer
)

# /maps/api/markers (through DefaultRouter)
class MarkerViewSet(
    viewsets.ReadOnlyModelViewSet):
    # print("MTW, views.MarkerViewSet()")
    bbox_filter_field = "location"
    filter_backends = [filters.InBBoxFilter]
    queryset = Marker.objects.all()
    serializer_class = MarkerSerializer

class CensusTractViewSet(
    viewsets.ReadOnlyModelViewSet):
    # print("MTW, views.MarkerViewSet()")
    bbox_filter_field = "mpoly"
    filter_backends = [filters.InBBoxFilter]
    queryset = CensusTract.objects.all()
    serializer_class = CensusTractSerializer

class CountyViewSet(
    viewsets.ReadOnlyModelViewSet):
    # print("MTW, views.MarkerViewSet()")
    bbox_filter_field = "mpoly"
    filter_backends = [filters.InBBoxFilter]
    queryset = County.objects.all()
    serializer_class = CountySerializer

class DeIpRangeViewSet(
    viewsets.ReadOnlyModelViewSet):
    l = logging.getLogger("django.db.backends")
    l.setLevel(logging.DEBUG)
    l.addHandler(logging.StreamHandler())
    # print("MTW, views.MarkerViewSet()")
    bbox_filter_field = "mpoint"
    filter_backends = [filters.InBBoxFilter]
    queryset = DeIpRange.objects.all()
    print(f"DeIpRangeViewSet(), query: {queryset.query}")
    serializer_class = DeIpRangeSerializer
    
