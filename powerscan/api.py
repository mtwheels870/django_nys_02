from rest_framework import routers

    #DeIpRangeViewSet,
from .views import (
    CensusTractViewSet,
    CountyViewSet,
    CountTractViewSet,
    CountCountyViewSet,
    CountStateViewSet,
    MmIpRangeViewSet,
    UsStateViewSet
)

# MTW: This is in global space (no class)
router = routers.DefaultRouter()
# /maps/api/markers/
#router.register(r"markers", MarkerViewSet)
router.register(r"states", UsStateViewSet)
router.register(r"counties", CountyViewSet)
router.register(r"tracts", CensusTractViewSet)
# router.register(r"ip_ranges", DeIpRangeViewSet)
router.register(r"state_counts", CountStateViewSet)
router.register(r"county_counts", CountCountyViewSet)
router.register(r"tract_counts", CountTractViewSet)
router.register(r"ip_ranges", MmIpRangeViewSet)

urlpatterns = router.urls
# print(f"api.py: urlpatterns = {urlpatterns}")
