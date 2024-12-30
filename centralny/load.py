from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.geos import Point, MultiPoint
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Centroid
from .models import County, CensusTract, DeIpRange, Marker, CountRangeTract, CountRangeCounty

MARKER_PATH = "/home/bitnami/Data/IP/Markers_02.shp"
marker_mapping = {
    "id", "id",
    "name", "Name",
    "location", "MULTIPOINT",
}

# Field from models.py, mapped to field names from the shape file
    # COUNTY
    # STATE
    # COUNTY_1
    # STATE_1
county_mapping = {
    "county_name": "COUNTY",
    "state_name": "STATE",
    "county_code": "COUNTY_1",
    "state_code": "STATE_1",
    "pop2000": "POP2000",
    "mpoly": "MULTIPOLYGON",
}
COUNTY_PATH = "/home/bitnami/Data/County/NY_Counties_04.shp"

tract_mapping = {
    "county_code": {"county_code": "COUNTYFP"},     # Foreign key field
    "state_code": "STATEFP",
    "tract_id": "TRACTCE",
    "short_name": "NAME",
    "long_name": "NAMELSAD",
    "interp_lat": "INTPTLAT",
    "interp_long": "INTPTLON",
    "mpoly": "MULTIPOLYGON",
}
TRACT_PATH = "/home/bitnami/Data/County/CensusTracts_03.shp"

ip_range_mapping = {
    "ip_range_start" : "start-ip",
    "ip_range_end" : "end-ip",
    "pp_city" : "pp-city",
    "pp_cxn_speed" : "pp-conn-sp",
    "pp_cxn_type" : "pp-conn-ty",
    "pp_latitude" : "pp-latitud",
    "pp_longitude" : "pp-longitu",
    "de_company_name" : "digel_comp",
    "mpoint" : "MULTIPOINT",
}

# IP_RANGE_PATH = "/home/bitnami/Data/IP/FiveCounties_Minimal.shp"
IP_RANGE_PATH = "/home/bitnami/Data/IP/NA_All_DBs_01.shp"

class Loader():
    def __init__(self):
        self.counter = 0

    def run_markers(self, verbose=True):
        marker_shp = Path(MARKER_PATH)
        self.lm_markers = LayerMapping(Marker, marker_shp, marker_mapping, transform=False)
        self.lm_markers.save(strict=True, verbose=verbose)

    def run_county(self, verbose=True):
        county_shp = Path(COUNTY_PATH)
        self.lm_county = LayerMapping(County, county_shp, county_mapping, transform=False)
        self.lm_county.save(strict=True, verbose=verbose)

    def run_tracts(self, verbose=False, progress=500):
        tract_shp = Path(TRACT_PATH)
        self.lm_tracts = LayerMapping(CensusTract, tract_shp, tract_mapping, transform=False)
        self.lm_tracts.save(strict=True, verbose=verbose, progress=progress)

    def run_ip_ranges(self, verbose=False, progress=1000):
        ip_range_shp = Path(IP_RANGE_PATH)
        self.lm_ranges = LayerMapping(DeIpRange, ip_range_shp, ip_range_mapping, transform=False)
        # Throws exception, should wrap in a try{}
        self.lm_ranges.save(strict=True, verbose=verbose, progress=progress)
        index = 0
        for ip_range in DeIpRange.objects.all():
            point = Point(float(ip_range.pp_longitude), float(ip_range.pp_latitude))
            #print(f"\nlooking up point = {point}") 
            for tract in CensusTract.objects.all():
                # print(f"checking tract: = {tract.short_name}") 
                found = tract.mpoly.contains(point)
                if (found) :
                    print(f"point[{index}]: {point}, in tract: {tract.short_name}")
                    # ip_range.mpoint = point
                    ip_range.census_tract = tract
                    ip_range.save()
                    break
            index = index + 1

    def _create_tract_count(self, census_tract):
        print(f"create_tract_count(), creating new, {census_tract}")
        tract_count = CountRangeTract()
        tract_count.census_tract = census_tract
        tract_count.mpoint = MultiPoint(Point(float(census_tract.interp_long), 
            float(census_tract.interp_lat)))
        self.hash_tracts[census_tract.tract_id] = tract_count
        return tract_count

    def aggregate_tracts(self, verbose=False):
        self.hash_tracts = {}
        for range in DeIpRange.objects.all():
            tract = range.census_tract
            #print(f"Looking up tract: {tract}")
            if tract.tract_id in self.hash_tracts:
                tract_count = self.hash_tracts[tract.tract_id]
            else:
                tract_count = self._create_tract_count(tract)
            tract_count.range_count = tract_count.range_count + 1 
        # Should save here
        for tract_id, tract_count in self.hash_tracts.items():
            print(f"save[{tract_id}]: count = {tract_count.range_count}")
            tract_count.save()

    def _create_county_counter(self, county):
        county_counter = CountRangeCounty()
        county_counter.county_code = county
        num_polys = len(county.mpoly)
        print(f"_create_county_count(), creating new, {county}, num_polys: {num_polys}")
        if (num_polys >= 1):
            first_polygon = county.mpoly[0]
            first_centroid = first_polygon.centroid
            print(f"_create_county_count(), creating new, {county}, centroid = {first_centroid}")
            county_counter.centroid = first_centroid
        self.hash_counties[county.county_code] = county_counter
        return county_counter

    def aggregate_counties(self, verbose=False):
        self.hash_counties = {}
        for tract_range in CountRangeTract.objects.all():
            county = tract_range.census_tract.county_code
            code = county.county_code
            print(f"tract: {tract_range.census_tract.tract_id}, Looking up county: {code}")
            if code in self.hash_counties:
                county_counter = self.hash_counties[code]
            else:
                county_counter = self._create_county_counter(county)
            # +1 here counts the number of tracts, we want the number of IP ranges
            county_counter.range_count = county_counter.range_count + tract_range.range_count
        # Should save here
        for county_code, county_counter in self.hash_counties.items():
            print(f"save[{county_code}]: count = {county_counter.range_count}")
            county_counter.save()
