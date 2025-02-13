import logging
from django.shortcuts import render
from django.utils import timezone
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404, render
import django.dispatch

from rest_framework import viewsets
from rest_framework_gis import filters

from centralny.models import (
    Marker,
    CensusTract,
    County,
    DeIpRange,
    CountRangeTract,
    CountRangeCounty,
    IpRangePing,
    IpRangeSurvey
)

from centralny.serializers import (
    MarkerSerializer,
    CensusTractSerializer,
    CountySerializer,
    DeIpRangeSerializer,
    CountRangeTractSerializer,
    CountRangeCountySerializer
)

from .forms import SelectedCensusTractForm

# Import our neighbors

KEY_ID = "id"
KEY_AGG_TYPE = "agg_type"
KEY_MAP_BBOX = "map_bbox"
KEY_LEAFLET_MAP = "leaflet_map"

MAP_BBOX_INITIAL_VALUE = "a=b"

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
    bbox_filter_field = "mpoint"
    filter_backends = [filters.InBBoxFilter]
    queryset = DeIpRange.objects.all()
    serializer_class = DeIpRangeSerializer
    
class CountTractViewSet(
    viewsets.ReadOnlyModelViewSet):
    bbox_filter_field = "mpoint"
    filter_backends = [filters.InBBoxFilter]
    queryset = CountRangeTract.objects.all()
    serializer_class = CountRangeTractSerializer
    
class CountCountyViewSet(
    viewsets.ReadOnlyModelViewSet):
    bbox_filter_field = "centroid"
    filter_backends = [filters.InBBoxFilter]
    queryset = CountRangeCounty.objects.all()
    serializer_class = CountRangeCountySerializer

class PingStrategyIndexView(generic.ListView):
    template_name = "centralny/ps_index.html"
    context_object_name = "latest_strategy_list"

    def get_queryset(self):
        """ Return the last five published IP surveys."""
        return IpRangeSurvey.objects.filter(time_created__lte=timezone.now()).order_by("-time_created")[:5]

class PingStrategyDetailView(generic.DetailView):
    model = IpRangeSurvey
    template_name = "centralny/ps_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # pk = self.kwargs.get('pk')  # Or 'product_id' if you customized the parameter name
        # Use pk to access the object or do other operations
        # print(f"PingStrategyDetailView.get_context_data(), pk = {pk}")
        return context

class PingStrategyResultsView(generic.DetailView):
    model = IpRangeSurvey
    template_name = "centralny/ps_results.html"

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
    template_name = "centralny/map_viewer.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['map_title'] = "Map Title Here"
        form = context_data['form']
        print(f'MNV.g_c_d(), form = {form}')
        print(f'MNV.g_c_d(), kwargs = {kwargs}')
        if 'id' in kwargs:
            kw_id = kwargs['id']
            print(f'MNV.g_c_d(), found kw_id = {kw_id}')
            field_id = form.fields[KEY_ID]
            field_id.initial = kw_id
            
        #id = form.fields[KEY_ID]
        #id.initial = 23
        #agg_type = form.fields[KEY_AGG_TYPE]
        #agg_type.initial = "Cherry"
#        map_bbox = form.fields[KEY_MAP_BBOX]
        # print(f"MNV.g_c_d(), map_bbox = {map_bbox}")
#        if KEY_LEAFLET_MAP  in self.request.session:
#            leaflet_map_dict = self.request.session.pop(KEY_LEAFLET_MAP, default=None)
#            print(f"g_c_d(), Found: leaflet_map_dict = {leaflet_map_dict}")
#            map_bbox_value = leaflet_map_dict[KEY_MAP_BBOX]
#        else:
#            map_bbox_value = MAP_BBOX_INITIAL_VALUE 
#        map_bbox.initial = map_bbox_value 
        # context_data['map_bbox'] = map_bbox_value 
        return context_data

    def post(self, request, *args, **kwargs):
        form = SelectedCensusTractForm(request.POST)
        print(f"MNV.post(), checking form here")
        if form.is_valid():
            id = form.cleaned_data[KEY_ID]
            agg_type = form.cleaned_data[KEY_AGG_TYPE]
            map_bbox = form.cleaned_data[KEY_MAP_BBOX]
            print(f"MNV.post(), id = {id}, agg_type = {agg_type}, map_bbox = {map_bbox}")
            # return HttpResponseRedirect(reverse("app_centralny:map_viewer",kwargs={'id': id, 'agg_type': agg_type}));
            return render(request, "centralny/map_viewer.html", {'id': id, 'agg_type': agg_type});
        else:
            print(f"MNV.post(), form is INVALID")
            return HttpResponseRedirect(reverse("app_centralny:map_viewer",), {'form': form});
        # Save the map_bbox across the reverse so we can zoom in our map appropriately
        #request.session[KEY_LEAFLET_MAP] = {KEY_MAP_BBOX : map_bbox }
