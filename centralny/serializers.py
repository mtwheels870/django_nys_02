from rest_framework_gis import serializers

from centralny.models import Marker, CensusTract, CensusBorderCounty

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
        model = CensusBorderCounty
