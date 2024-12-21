from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from .models import CensusBorderCounty, CensusTract, DeIpRange

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
    "mpoint" : "MULTIPOINT",
}

IP_RANGE_PATH = "/home/bitnami/Data/IP/FiveCounties_Minimal.shp"

class Loader():
    def __init__(self):
        self.counter = 0

    def run_county(self, verbose=True):
        county_shp = Path(COUNTY_PATH)
        self.lm_county = LayerMapping(CensusBorderCounty, county_shp, county_mapping, transform=False)
        self.lm_county.save(strict=True, verbose=verbose)

    def run_tracts(self, verbose=False, progress=500):
        tract_shp = Path(TRACT_PATH)
        self.lm_tracts = LayerMapping(CensusTract, tract_shp, tract_mapping, transform=False)
        self.lm_tracts.save(strict=True, verbose=verbose, progress=progress)
        for feature in self.lm_tracts.layer:
            g = feature.geom
            description = str(feature)
            print(f"d = {description}, g = {g}")

    def run_ip_ranges(self, verbose=False, progress=1000):
        ip_range_shp = Path(IP_RANGE_PATH)
        self.lm_ranges = LayerMapping(DigitalElementIpRange, ip_range_shp, ip_range_mapping, transform=False)
        # Throws exception, should wrap in a try{}
        self.lm_ranges.save(strict=True, verbose=verbose, progress=progress)
        print(f"lm.num_feat = {lm.layer.num_feat}")
        for feauture in self.lm_tracts.layer:
            g = feature.geom
            description = str(feature)
            print(f"d = {description}, g = {g}")
