import logging
from django.shortcuts import render
from django.utils import timezone
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404, render, redirect
import django.dispatch

from  django_tables2.config import RequestConfig

from rest_framework import viewsets
from rest_framework_gis import filters

from .models import (
    UsState,
    County,
    CensusTract,
    CountState,
    CountCounty,
    CountTract,
    MmIpRange,
    IpRangePing,
    IpRangeSurvey,
    IpSurveyState
)

from .serializers import (
    TractSerializer,
    CountySerializer,
    MmIpRangeSerializer,
    CountTractSerializer,
    CountCountySerializer,
    UsStateSerializer,
    CountStateSerializer,
)

from .forms import SelectedCensusTractForm, PingStrategyForm
from .tables import MmIpRangeTable

# Import our neighbors

KEY_ID = "id"
KEY_AGG_TYPE = "agg_type"
KEY_MAP_BBOX = "map_bbox"
KEY_LEAFLET_MAP = "leaflet_map"

class UsStateViewSet(
    viewsets.ReadOnlyModelViewSet):
    # print("MTW, views.MarkerViewSet()")
    bbox_filter_field = "mpoly"
    filter_backends = [filters.InBBoxFilter]
    queryset = UsState.objects.all()
    # AQUI
    serializer_class = UsStateSerializer

class CountyViewSet(
    viewsets.ReadOnlyModelViewSet):
    # print("MTW, views.MarkerViewSet()")
    bbox_filter_field = "mpoly"
    filter_backends = [filters.InBBoxFilter]
    queryset = County.objects.all()
    serializer_class = CountySerializer

class CensusTractViewSet(
    viewsets.ReadOnlyModelViewSet):
    # print("MTW, views.MarkerViewSet()")
    bbox_filter_field = "mpoly"
    filter_backends = [filters.InBBoxFilter]
    queryset = CensusTract.objects.all()
    serializer_class = TractSerializer

class MmIpRangeViewSet(
    viewsets.ReadOnlyModelViewSet):
    bbox_filter_field = "mpoint"
    filter_backends = [filters.InBBoxFilter]
    queryset = MmIpRange.objects.all()
    serializer_class = MmIpRangeSerializer
    
class CountStateViewSet(
    viewsets.ReadOnlyModelViewSet):
    bbox_filter_field = "centroid"
    filter_backends = [filters.InBBoxFilter]
    # queryset = CountRangeCounty.objects.all()
    #queryset = CountCounty.objects.filter(ip_source__id=IP_RANGE_SOURCE)
    queryset = CountState.objects.all()
    serializer_class = CountStateSerializer

class CountCountyViewSet(
    viewsets.ReadOnlyModelViewSet):
    bbox_filter_field = "centroid"
    filter_backends = [filters.InBBoxFilter]
    # queryset = CountRangeCounty.objects.all()
    #queryset = CountCounty.objects.filter(ip_source__id=IP_RANGE_SOURCE)
    queryset = CountCounty.objects.all()
    serializer_class = CountCountySerializer

class CountTractViewSet(
    viewsets.ReadOnlyModelViewSet):
    bbox_filter_field = "mpoint"
    filter_backends = [filters.InBBoxFilter]
    # queryset = CountRangeTract.objects.all()
    #queryset = CountTract.objects.filter(ip_source__id=IP_RANGE_SOURCE)
    queryset = CountTract.objects.all()
    serializer_class = CountTractSerializer
    
# Reverse mapping from clicking on a index, detail
def approve_ping(request, id):
    # print(f"Views.approve_ping(), {id}")
    survey = get_object_or_404(IpRangeSurvey, pk=id)
    survey.approve()
    # ping_strat_results is the name from urls.py
    return HttpResponseRedirect(reverse("app_my_scheduler:schedule_survey_detail", args=(id,)))

class MapNavigationView(generic.edit.FormView):
    # model = TextFile
    form_class = SelectedCensusTractForm
    table_class = MmIpRangeTable
    template_name = "powerscan/map_viewer.html"
    table_pagination = {
        "per_page": 10
    }

    def create_table(self, queryset):
        table = self.table_class(data=queryset)
        RequestConfig(self.request, paginate=self.table_pagination).configure( table)
        return table

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['map_title'] = "Map Title Here"
        form = context_data['form']
        map_bbox = form.fields[KEY_MAP_BBOX]
        #print(f"g_c_d(), map_bbox = {map_bbox}")
        # We need this, so it's in the Django templates (for the search parms)
        context_data['map_bbox'] = map_bbox
        table = self.create_table(MmIpRange.objects.none())
        context_data['table'] = table
        return context_data

    def get(self, request, *args, **kwargs):
        print(f"MNV.get(), request = {request}")
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        form = SelectedCensusTractForm(request.POST)
        # print(f"MNV.post(), checking form here: {form}")
        if form.is_valid():
            id = form.cleaned_data[KEY_ID]
            agg_type = form.cleaned_data[KEY_AGG_TYPE]
            map_bbox = form.cleaned_data[KEY_MAP_BBOX]

        # print(f"MNV.g_c_d(), map_bbox = {map_bbox}")
            queryset = self.build_table(agg_type, id)
            table = self.create_table(queryset)
            print(f"MNV.post(), id = {id}, agg_type = {agg_type}, map_bbox = {map_bbox}")
            print(f"          table = {table}")

            # Pass the form back in
            return render(request, "powerscan/map_viewer.html",
                {'form': form, 'table': table, 'map_bbox' : map_bbox});
        else:
            print(f"MNV.post(), form is INVALID")
            return HttpResponseRedirect(reverse("app_powerscan:map_viewer",), {'form': form});

    # These labels are in static/cb_layer.js
    def build_table(self, agg_type, id):
        table = None
        match agg_type:
            case "CountRangeTract":
                count_range_tract = get_object_or_404(CountRangeTract, pk=id)
                census_tract = count_range_tract.census_tract
                # print(f"build_table(), agg_type = {agg_type}, id = {id}, census_tract_id = {census_tract.id}")
                queryset = MmIpRange.objects.filter(census_tract__id=census_tract.id)
                table = queryset
            case "MmIpRange":
                table = MmIpRange.objects.none()
            case "CountCounty":
                count_range_county = get_object_or_404(CountCounty, pk=id)
                county = count_range_county.county_code 
                print(f"Found county: {county}")
                # tract_id_set = count_range_county count_range_county 
                table = MmIpRange.objects.none()
            case _:
                print(f"build_table(), unrecognized agg_type = {agg_type}")
        return table

def chat_index(request):
    return render(request, "powerscan/chat_index.html")

def chat_room(request, room_name):
    return render(request, "powerscan/chat_room.html", {"room_name": room_name})
