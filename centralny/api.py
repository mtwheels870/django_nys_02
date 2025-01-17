from rest_framework import routers

from centralny.views import (
    MarkerViewSet,
    CensusTractViewSet,
    CountyViewSet,
    DeIpRangeViewSet,
    CountTractViewSet,
    CountCountyViewSet
)

# MTW: This is in global space (no class)
router = routers.DefaultRouter()
# /maps/api/markers/
router.register(r"markers", MarkerViewSet)
router.register(r"tracts", CensusTractViewSet)
router.register(r"counties", CountyViewSet)
router.register(r"ip_ranges", DeIpRangeViewSet)
router.register(r"tract_counts", CountTractViewSet)
router.register(r"county_counts", CountCountyViewSet)

urlpatterns = router.urls
# print(f"api.py: urlpatterns = {urlpatterns}")
