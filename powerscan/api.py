#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, PINP01NT, LLC
#
# https://pinp01nt.com/
#
# All rights reserved.

"""
Docstring here

Authors: Michael T. Wheeler (mike@pinp01nt.com)

"""
from rest_framework import routers

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
router.register(r"state_counts", CountStateViewSet)
router.register(r"county_counts", CountCountyViewSet)
router.register(r"tract_counts", CountTractViewSet)
router.register(r"ip_ranges", MmIpRangeViewSet)

urlpatterns = router.urls
