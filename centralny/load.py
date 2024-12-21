from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from .models import CensusBorderCounty, CensusTract, DigitalElementIpRange

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
def run_county(verbose=True):
    county_shp = Path(COUNTY_PATH)
    lm = LayerMapping(CensusBorderCounty, county_shp, county_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)

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
def run_tracts(verbose=True):
    tract_shp = Path(TRACT_PATH)
    lm = LayerMapping(CensusTract, tract_shp, tract_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)

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
def run_ip_ranges(verbose=False, progress=1000):
    ip_range_shp = Path(IP_RANGE_PATH)
    lm = LayerMapping(DigitalElementIpRange, ip_range_shp, ip_range_mapping, transform=False)
    result = lm.save(strict=True, verbose=verbose, progress=progress)
    print(f"result = ${result}")