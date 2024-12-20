from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from .models import CensusBorderCounty

# Field from models.py, mapped to field names from the shape file
    # COUNTY
    # STATE
    # COUNTY_1
    # STATE_1
shp_model_mapping = {
    "county_name": "COUNTY",
    "state_name": "STATE",
    "county_code": "COUNTY_1",
    "state_code": "STATE_1",
    "pop2000": "POP2000",
    "mpoly": "MULTIPOLYGON",
}

path_name = "/home/bitnami/Data/County/NY_Counties_04.shp"
county_shp = Path(path_name)

def run(verbose=True):
    lm = LayerMapping(CensusBorderCounty, county_shp, shp_model_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)
