from rest_framework_gis import serializers

from centralny.models import Marker, CensusTract, County, DeIpRange, CountRangeTract, CountRangeCounty

class MarkerSerializer(
    serializers.GeoFeatureModelSerializer):
    class Meta:
        fields = ("id", "name")
        geo_field = "location"
        model = Marker

class CensusTractSerializer(
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

class DeIpRangeSerializer(
    serializers.GeoFeatureModelSerializer):
    class Meta:
        fields = ("id", "ip_range_start", "de_company_name")
        geo_field = "mpoint"
        model = DeIpRange

class CountRangeTractSerializer(
    serializers.GeoFeatureModelSerializer):
    class Meta:
        fields = ("id", "census_tract", "range_count")
        geo_field = "mpoint"
        model = CountRangeTract

class CountRangeCountySerializer(
    serializers.GeoFeatureModelSerializer):
    class Meta:
        fields = ("id", "county_code", "range_count")
        geo_field = "centroid"
        model = CountRangeCounty

