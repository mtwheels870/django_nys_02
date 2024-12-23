from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.geos import Point
import django.contrib.gis.db.models 
from .models import CensusBorderCounty, CensusTract, DeIpRange, Marker

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

IP_RANGE_PATH = "/home/bitnami/Data/IP/FiveCounties_Minimal.shp"

class Loader():
    def __init__(self):
        self.counter = 0

    def run_markers(self, verbose=True):
        markers_shp = Path(MARKER_PATH)
        self.lm_markers = LayerMapping(Marker, marker_shp, marker_mapping, transform=False)
        self.lm_markers.save(strict=True, verbose=verbose)

    def run_county(self, verbose=True):
        county_shp = Path(COUNTY_PATH)
        self.lm_county = LayerMapping(CensusBorderCounty, county_shp, county_mapping, transform=False)
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

#        for feature in self.lm_tracts.layer:
#            g = feature.geom
#            description = feature.fid
#            print(f"f.fid = {description}, g = ...")
