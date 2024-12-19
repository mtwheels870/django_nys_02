from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from .models import WorldBorder

# Field from models.py, mapped to field names from the shape file
world_mapping = {
    "fips": "FIPS",
    "iso2": "ISO2",
    "iso3": "ISO3",
    "un": "UN",
    "name": "NAME",
    "area": "AREA",
    "pop2005": "POP2005",
    "region": "REGION",
    "subregion": "SUBREGION",
    "lon": "LON",
    "lat": "LAT",
    "mpoly": "MULTIPOLYGON",
}

path_name = "/home/bitnami/Data/world/TM_WORLD_BORDERS-0.3.shp"
world_shp = Path(path_name)

def run(verbose=True):
    lm = LayerMapping(WorldBorder, world_shp, world_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)
