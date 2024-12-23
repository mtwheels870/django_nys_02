from rest_framework import routers

from centralny.views import (
    MarkerViewSet,
    CensusTractViewSet,
)

# MTW: This is in global space (no class)
router = routers.DefaultRouter()
# /maps/api/markers/
router.register(r"markers", MarkerViewSet)
router.register(r"tracts", CensusTractViewSet)

urlpatterns = router.urls
# print(f"api.py: urlpatterns = {urlpatterns}")
