import logging
from django.shortcuts import render
from django.utils import timezone
from django.views import generic

from rest_framework import viewsets
from rest_framework_gis import filters

from centralny.models import (
    Marker,
    CensusTract,
    County,
    DeIpRange,
    CountRangeTract,
    CountRangeCounty,
    IpRangePing
)

from centralny.serializers import (
    MarkerSerializer,
    CensusTractSerializer,
    CountySerializer,
    DeIpRangeSerializer,
    CountRangeTractSerializer,
    CountRangeCountySerializer
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
    template_name = "centralny/ping_strat_index.html"
    context_object_name = "latest_ping_list"

    def get_queryset(self):
        """ Return the last five published questions."""
        return IpRangePing.objects.filter(time_created__lte=timezone.now()).order_by("-time_created")[:5]

class PingStrategyDetailView(generic.DetailView):
    model = IpRangePing
    template_name = "centralny/ping_strat_detail.html"

    def get_queryset(self):
        """ Excludes any Qs that aren't published, yet.  """
        return IpRangePing.objects.filter(time_created__lte=timezone.now())

class PingStrategyResultsView(generic.DetailView):
    model = IpRangePing
    template_name = "centralny/ping_strat_results.html"

def vote(request, ip_range_pind_id):
    range_ping = get_object_or_404(IpRangePing, pk=ip_range_pind_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        # Fix the hard-coded name below (/polls/nys/)
        return render(
            request,
            "tutorial/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        # What does F() do?
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("app_tut:results", args=(question.id,)))
