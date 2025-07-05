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
# from django.contrib import admin
from django.contrib.gis import admin

from .models import (
    County, CensusTract,
    MmIpRange, DebugPowerScan
)

@admin.register(DebugPowerScan)
class DebugPowerScanAdmin(admin.ModelAdmin):
    model = DebugPowerScan
