import logging
from urllib.parse import urlencode
from django.shortcuts import render
from django.utils import timezone
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404, render, redirect
import django.dispatch

from django_tables2.config import RequestConfig
from django_tables2 import SingleTableView

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
    IpSurveyState,
    IpSurveyCounty
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

from .forms import SelectedAggregationForm, PingStrategyForm
from .tables import AggregationHistoryTable

# Import our neighbors


# These values should match the templates
KEY_ID = "id"
KEY_SURVEY_ID = "survey_id"
KEY_AGG_TYPE = "agg_type"
KEY_TIME_PINGED = "time_pinged"
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

# class MapNavigationView(generic.edit.FormView):
class MapNavigationView(SingleTableView):
    # form_class = SelectedAggregationForm
    table_class = AggregationHistoryTable
    template_name = "powerscan/map_viewer.html"
    table_pagination = {
        "per_page": 10
    }

    def _agg_type_states(self, survey):
        data_rows = []
        #for counter in IpSurveyState.objects.filter(survey__id=survey_id).order_by("id"):
        for counter in IpSurveyState.objects.filter(survey=survey).order_by("id"):
            us_state = counter.us_state
            responded = counter.num_ranges_responded 
            pinged = counter.num_ranges_pinged 
            percentage = float(responded)/pinged
            dict = {"id" : counter.id, "name" : us_state.state_name, "hosts_responded" : responded,
                    "hosts_pinged" : pinged, "percentage" : percentage}
            data_rows.append(dict)
        return data_rows

    def _agg_type_counties(self, survey_state):
        survey = survey_state.survey
        us_state = survey_state.us_state 
        data_rows = []
        for counter in IpSurveyCounty.objects.filter(survey=survey, county__us_state=us_state).order_by("id"):
            responded = counter .num_ranges_responded 
            pinged = counter.num_ranges_pinged 
            percentage = float(responded)/pinged
            dict = {"id" : counter.id, "name" : counter.county.county_name, "hosts_responded" : responded,
                "hosts_pinged" : pinged, "percentage" : percentage}
            data_rows.append(dict)
        return data_rows

    def _unused_agg_type_tracts(self, survey):
        data_rows = []
        for counter in IpSurveyTract.objects.filter(survey__id=survey_id).order_by("id"):
            responded = counter .num_ranges_responded 
            pinged = counter.num_ranges_pinged 
            percentage = float(responded)/pinged
            dict = {"id" : counter.id, "name" : "tract_name_here", "hosts_responded" : responded,
                "hosts_pinged" : pinged, "percentage" : percentage}
            data_rows.append(dict)
        return data_rows

    def _create_table(self, agg_type, id1):
        data_rows = []
        if agg_type and id1:
            print(f"_create_table(), agg_type = {agg_type}, id1 = {id1}")
            match agg_type:
                case "states":
                    survey = get_object_or_404(IpRangeSurvey, pk=id1)
                    data_rows = self._agg_type_states(survey)
                case "counties":
                    survey_state = get_object_or_404(IpSurveyState, pk=id1)
                    data_rows = self._agg_type_counties(survey_state)
                case _:
                    print(f"create_table(), unrecognized agg_type = {agg_type}")
        else:
            print(f"create_table(), agg_type = {agg_type}, id1 = {id1}")
        #table = self.table_class(data=data_rows)
        #RequestConfig(self.request, paginate=self.table_pagination).configure( table)
        return data_rows

    def get_queryset(self):
        query_params = self.request.GET
        print(f"MNV.get_queryset(), self = {self}, query_params = {query_params}")
        if "id" in query_params :
            id1 = query_params["id"]
            #field_survey_id = form.fields['survey_id']
            #field_survey_id.initial = survey_id
            #survey = get_object_or_404(IpRangeSurvey, pk=survey_id)
        else:
            id1 = None
        if "agg_type" in query_params:
            agg_type = query_params["agg_type"]
        else:
            agg_type = None
        queryset = self._create_table( agg_type, id1)
        # queryset = IpRangeSurvey.objects.order_by("-id")
        return queryset 

    def get_context_data(self, **kwargs):
        print(f"MNV.g_c_d(), kwargs = {kwargs}")
        context_data = super().get_context_data(**kwargs)
        # context_data['map_title'] = "Map Title Here"
        # form = context_data['form']
        # map_bbox = form.fields[KEY_MAP_BBOX]
        query_params = self.request.GET
        if "survey_id" in query_params :
            survey_id = query_params["survey_id"]
            #field_survey_id = form.fields['survey_id']
            #field_survey_id.initial = survey_id
            survey = get_object_or_404(IpRangeSurvey, pk=survey_id)
            #field_time_pinged = form.fields['time_pinged']
            #field_time_pinged.initial = survey.time_ping_started
            context_data[KEY_SURVEY_ID] = survey_id
            context_data[KEY_TIME_PINGED] = survey.time_ping_started
        else:
            survey = None
        #print(f"MNV.g_c_d(), 1, c_d = {context_data}")
        if "agg_type" in query_params:
            agg_type = query_params["agg_type"]
            context_data[KEY_AGG_TYPE] = agg_type
            #field_agg_type = form.fields['agg_type']
            #field_agg_type.initial = agg_type
        else:
            agg_type = None
        if "in_bbox" in query_params:
            in_bbox = query_params["in_bbox"]
            #print(f"g_c_d(), query_params = {query_params},in_bbox = {in_bbox}")
            context_data['map_bbox'] = in_bbox  
        else:
            context_data['map_bbox'] = None
        # print(f"MNV.g_c_d(), 2")

        # This is wrong.  Don't want MmIpRange() here.  Only works b/c its none()
        #table = self._create_table(agg_type, survey)
        #context_data['table'] = table
        # print(f"g_c_d(), returning here, context_data = {context_data}")
        return context_data

    def post(self, request, *args, **kwargs):
        print(f"MNV.post(), request.POST = {request.POST}")

        selected_pks = request.POST.getlist('selection')
        num_selected = len(selected_pks)
        if 'zoom_map' in request.POST:
            if num_selected > 0:
                print(f"MNV.post(zoom_map), selected ids = {ids}")
            else:
                print(f"MNV.post(zoom_map), nothing selected")
        if 'expand' in request.POST:
            if num_selected == 1:
                single_selected = selected_pks[0]
                print(f"MNV.post(zoom_map), single_selected = {single_selected}")
            else:
                print(f"MNV.post(zoom_map), num_selected = {num_selected}")
            # Pass the form back in
            new_params = {"agg_type" : "counties", "id": single_selected}
            querystring = urlencode(new_params)
            return redirect(f"/powerscan/map/?{querystring}")
        if 'show_459' in request.POST:
            # id in this instance is survey id
            new_params = {"agg_type" : "states", "id": "459"}
            querystring = urlencode(new_params)
            url = f"/powerscan/map/?{querystring}"
            return redirect(url)
        # This logic is wrong
        time_pinged = form.cleaned_data[KEY_TIME_PINGED]
        new_form = SelectedAggregationForm(initial={"id" : survey_id,
            KEY_AGG_TYPE : agg_type, KEY_TIME_PINGED : time_pinged})
        context = {"form" : new_form}
        return render(request, self.template_name, context)

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

#    def get_queryset(self):
        # For now, just hard-code with 'PR'
#        survey_id = 450
#        return SurveyUtil.last_n_surveys_state(survey_id=450, limit=30)

#    def get(self, request, *args, **kwargs):
#        query_params = self.request.GET
#        if "survey_id" in query_params:
#            survey_id = query_params["survey_id"]
#            print(f"MNV.get(), read survey_id = {survey_id},render_to_response()")
#            return self.render_to_response(self.get_context_data())
#        else:
#            print(f"MNV.get(), no survey_id, redirecting")
#            new_params = {"agg_type" : "states", "survey_id": "459"}
#            querystring = urlencode(new_params)
#            url = f"/powerscan/map/?{querystring}"
#            return redirect(url)
        # form = SelectedAggregationForm(request.POST)
#         if not form.is_valid():
 #            print(f"MNV.post(), form is INVALID")
  #           return HttpResponseRedirect(reverse("app_powerscan:map_viewer",), {'form': form});

   #      survey_id = form.cleaned_data[KEY_SURVEY_ID]
    #     agg_type = form.cleaned_data[KEY_AGG_TYPE]
