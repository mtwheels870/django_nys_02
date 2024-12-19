from rest_framework_gis import serializers

from centralny.models import Marker

class MarkerSerializer(
    serializers.GeoFeatureModelSerializer,
):
    class Meta:
        fields = ("id", "name")
        geo_field = "location"
        model = Marker
