from rest_framework_gis import serializers

from .models import CensusTract, County, MmIpRange, CountTract, CountCounty, CountState

#class MarkerSerializer(
#    serializers.GeoFeatureModelSerializer):
#    class Meta:
#        fields = ("id", "name")
#        geo_field = "location"
#        model = Marker

class TractSerializer(
    serializers.GeoFeatureModelSerializer):
    class Meta:
        fields = ("id", "short_name")
        geo_field = "mpoly"
        model = CensusTract

class CountySerializer(
    serializers.GeoFeatureModelSerializer):
    class Meta:
        fields = ("id", "county_code", "county_name")
        geo_field = "mpoly"
        model = County

#class DeIpRangeSerializer(
#    serializers.GeoFeatureModelSerializer):
#    class Meta:
#        fields = ("id", "ip_range_start", "company_name")
#        geo_field = "mpoint"
#        model = DeIpRange

class MmIpRangeSerializer(
    serializers.GeoFeatureModelSerializer):
    class Meta:
        fields = ("id", "ip_network", "geoname_id ")
        geo_field = "mpoint"
        model = MmIpRange

class CountStateSerializer(
    serializers.GeoFeatureModelSerializer):
    class Meta:
        fields = ("id", "us_state.name", "range_count")
        geo_field = "centroid"
        model = CountState

class CountCountySerializer(
    serializers.GeoFeatureModelSerializer):
    class Meta:
        fields = ("id", "county.name", "range_count")
        geo_field = "centroid"
        model = CountCounty

class CountTractSerializer(
    serializers.GeoFeatureModelSerializer):
    class Meta:
        fields = ("id", "census_tract", "range_count")
        geo_field = "mpoint"
        model = CountTract


