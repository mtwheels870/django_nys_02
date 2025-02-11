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
        id = form.fields['id']
        id.initial = 23
        agg_type = form.fields['agg_type']
        agg_type.initial = "Cherry"
        return context_data

    def post(self, request, *args, **kwargs):
        in_bbox = request.POST.get('in_bbox')
        print(f"in_bbox = {in_bbox}")
        form = SelectedCensusTractForm(request.POST)
        if form.is_valid():
            id = form.cleaned_data['id']
            agg_type = form.cleaned_data['agg_type']
            print(f"MNV.post(), id = {id}, agg_type = {agg_type}")
        else:
            print(f"MNV.post(), form is INVALID")
        print(f"Before render, path = {request.path}")
        # return HttpResponseRedirect(request.path)
        return render(request, "centralny/map_viewer.html", {'form': form})
