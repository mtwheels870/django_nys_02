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

from django_nys_02.celery import app as celery_app, QUEUE_NAME

from .tasks import build_whitelist, zmap_from_file, tally_results

from .models import (
    CensusTract,
    County,
    CountTract,
    MmIpRange,
    CountCounty,
    IpRangePing,
    IpRangeSurvey,
    WorkerLock,
    UsState
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
from .tables import DeIpRangeTable

# Import our neighbors

KEY_ID = "id"
KEY_AGG_TYPE = "agg_type"
KEY_MAP_BBOX = "map_bbox"
KEY_LEAFLET_MAP = "leaflet_map"

FIELD_CELERY_DETAILS = "celery_stuff"

# For our test case, we just use 15s
# PING_RESULTS_DELAY = 15
PING_RESULTS_DELAY = 15 * 60

class StateViewSet(
    viewsets.ReadOnlyModelViewSet):
    # print("MTW, views.MarkerViewSet()")
    bbox_filter_field = "mpoly"
    filter_backends = [filters.InBBoxFilter]
    queryset = UsState.objects.all()
    # AQUI
    serializer_class = CountySerializer

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
    
class CountTractViewSet(
    viewsets.ReadOnlyModelViewSet):
    bbox_filter_field = "mpoint"
    filter_backends = [filters.InBBoxFilter]
    # queryset = CountRangeTract.objects.all()
    #queryset = CountTract.objects.filter(ip_source__id=IP_RANGE_SOURCE)
    queryset = CountTract.objects.all()
    serializer_class = CountTractSerializer
    
class CountCountyViewSet(
    viewsets.ReadOnlyModelViewSet):
    bbox_filter_field = "centroid"
    filter_backends = [filters.InBBoxFilter]
    # queryset = CountRangeCounty.objects.all()
    #queryset = CountCounty.objects.filter(ip_source__id=IP_RANGE_SOURCE)
    queryset = CountCounty.objects.all()
    serializer_class = CountCountySerializer

class PingStrategyIndexView(generic.ListView):
    template_name = "powerscan/ps_index.html"
    context_object_name = "latest_strategy_list"

    def get_queryset(self):
        """ Return the last five published IP surveys."""
        return IpRangeSurvey.objects.filter(time_created__lte=timezone.now()).order_by("-time_created")[:5]

class PingStrategyDetailView(generic.DetailView):
    model = IpRangeSurvey
    template_name = "powerscan/ps_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # pk = self.kwargs.get('pk')  # Or 'product_id' if you customized the parameter name
        # Use pk to access the object or do other operations
        # print(f"PingStrategyDetailView.get_context_data(), pk = {pk}")
        return context

class PingStrategyResultsView(generic.DetailView):
    model = IpRangeSurvey
    template_name = "powerscan/ps_results.html"

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
    table_class = DeIpRangeTable
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
        print(f"g_c_d(), map_bbox = {map_bbox}")
        # We need this, so it's in the Django templates (for the search parms)
        context_data['map_bbox'] = map_bbox
        table = self.create_table(DeIpRange.objects.none())
        context_data['table'] = table
        return context_data

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
            return HttpResponseRedirect(reverse("app_cybsen:map_viewer",), {'form': form});

    # These labels are in static/cb_layer.js
    def build_table(self, agg_type, id):
        table = None
        match agg_type:
            case "CountRangeTract":
                count_range_tract = get_object_or_404(CountRangeTract, pk=id)
                census_tract = count_range_tract.census_tract
                # print(f"build_table(), agg_type = {agg_type}, id = {id}, census_tract_id = {census_tract.id}")
                queryset = DeIpRange.objects.filter(census_tract__id=census_tract.id)
                table = queryset
                # table = DeIpRangeTable(data=queryset)
            case "DeIpRange":
                table = DeIpRange.objects.none()
            case "CountCounty":
                count_range_county = get_object_or_404(CountCounty, pk=id)
                county = count_range_county.county_code 
                print(f"Found county: {county}")
                # tract_id_set = count_range_county count_range_county 
                table = DeIpRange.objects.none()
            case _:
                print(f"build_table(), unrecognized agg_type = {agg_type}")
        return table

class ConfigurePingView(generic.edit.FormView):
    # model = TextFile
    form_class = PingStrategyForm
    template_name = "powerscan/ps_detail.html"

    def _get_celery_details(self):
        return f"App name: '{celery_app.main}', queue = '{QUEUE_NAME}'"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        # There's an unbound, empty form in context_data...
        # File stuff
        context_data[FIELD_CELERY_DETAILS] = self._get_celery_details()

        return context_data

    def post(self, request, *args, **kwargs):
        #print(f"CPV.post(), kwargs = {kwargs}")
        form = PingStrategyForm(request.POST)
        if form.is_valid():
            my_field = form.cleaned_data['my_field']
            #print(f"CPV.post(), my_field = {my_field}")
        else:
            print(f"CPV.post(), form is INVALID")

        if 'return_to_map' in request.POST:
            return HttpResponseRedirect(reverse("app_cybsen:map_viewer"))

        if 'build_whitelist' in request.POST:
            print(f"CPV.post(), build_whitelist")
            lock = WorkerLock()
            lock.save()
            # MaxM ranges
            async_result = build_whitelist.apply_async(
                kwargs={"worker_lock_id" : lock.id},
                    #"ip_source_id": IP_RANGE_SOURCE },
                queue=QUEUE_NAME,
                routing_key='ping.tasks.build_whitelist')
            # Fall through

        if 'start_ping' in request.POST:
            #print(f"CPV.post(), start_ping...")
            survey = IpRangeSurvey()
            survey.save()
            async_result = zmap_from_file.apply_async(
                kwargs={"survey_id" : survey.id},
                    #"ip_source_id": IP_RANGE_SOURCE },
                queue=QUEUE_NAME,
                routing_key='ping.tasks.zmap_from_file')
            metadata_file = async_result.get()
            print(f"CPV.post(), async_result.metadata_file = {metadata_file}")

            now = timezone.now()
            print(f"CPV.post(), calling tally_results (delayed), now = {now}, seconds = {PING_RESULTS_DELAY}")
            # Fire off the counting task
            async_result2 = tally_results.apply_async(
                countdown=PING_RESULTS_DELAY,
                #"ip_source_id": IP_RANGE_SOURCE,
                kwargs={"survey_id": survey.id,
                    "metadata_file": metadata_file} )
            # Fall through

        # Load up the celery details for the next form
        celery_details = self._get_celery_details()
        context = {"form" : form, FIELD_CELERY_DETAILS : celery_details}
        return render(request, self.template_name, context)

#
# CRUFT
#
# /maps/api/markers (through DefaultRouter)
#class MarkerViewSet(
#    viewsets.ReadOnlyModelViewSet):
    # print("MTW, views.MarkerViewSet()")
#    bbox_filter_field = "location"
#    filter_backends = [filters.InBBoxFilter]
#    queryset = Marker.objects.all()
#    serializer_class = MarkerSerializer

#class DeIpRangeViewSet(
#    viewsets.ReadOnlyModelViewSet):
#    bbox_filter_field = "mpoint"
#    filter_backends = [filters.InBBoxFilter]
#    queryset = DeIpRange.objects.all()
#    serializer_class = DeIpRangeSerializer
#MAP_BBOX_INITIAL_VALUE = "a=b"

# Use Maxmind
#IP_RANGE_SOURCE = 2
