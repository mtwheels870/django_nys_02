from pathlib import Path

from django.utils import timezone
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.geos import Point, MultiPoint
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Centroid

from .models import (
    UsState, County, CensusTract,
    CountTract, CountCounty, 
    IpRangeSurvey, IpRangePing,
    MmIpRange)

mapping_state = {
    "state_fp": "STATEFP",
    "state_name": "NAME",
    "interp_lat": "INTPTLAT",
    "interp_long": "INTPTLON",
    "mpoly": "MULTIPOLYGON",
}

mapping_county = {
    "county_fp" : "COUNTYFP",
    "county_name": "NAME",
    "us_state" :  {"state_fp": "STATEFP"},
    "geoid": "GEOID",
    "interp_lat": "INTPTLAT",
    "interp_long": "INTPTLON",
    "mpoly": "MULTIPOLYGON",
}

def process_shape_feature(feature):
    geoid = feature.get("GEOID")
    state_fp = geoid[0:1]
    county_fp = geoid[2:4]
    county = County.objects.filter(county_fp=county_fp).filter(state_fp=state_fp)
    return { "county" : county }

#    "county": {"county_fp": "COUNTYFP"},     # Foreign key field
#    "county": process_shape_feature,     # Foreign key field
mapping_tract = {
    # "THIS_FIELD" : { FIELD_IN_COUNTY (model) : OUR_FIELD_FROM_SHAPE }
    "county" : {"geoid" : "cty_geoid"},
    "tract_id": "TRACTCE",
    "name": "NAME",
    "interp_lat": "INTPTLAT",
    "interp_long": "INTPTLON",
    "geoid": "GEOID",
    "mpoly": "MULTIPOLYGON",
}

mapping_maxm_range = {
    "ip_network" : "network",
    "geoname_id" : "geoname_id",
    "zip_code" : "postal_cod",
    "mm_latitude" : "latitude",
    "mm_longitude" : "longitude",
    # "FIELD_THIS_MODEL" : { FIELD_IN_TRACT (model) : OUR_FIELD_FROM_SHAPE }
    "census_tract": {"geoid": "GEOID"},     # Foreign key field
    "accuracy" : "accuracy_r",
    "mpoint" : "MULTIPOINT",
}

#    "PATH_STATE" : "/home/bitnami/Data/PowerScan/Geo/tl_2024_us_state.shp",
#    "PATH_COUNTY" : "/home/bitnami/Data/PowerScan/Geo/Counties_Clipped_02.shp",
loc_config = {
    "PATH_STATE" : "/home/bitnami/Data/PowerScan/Geo/2024_US_State_02.shp",
    "PATH_COUNTY" : "/home/bitnami/Data/PowerScan/Geo/Counties_03.shp",
    "PATH_TRACTS" : "/home/bitnami/Data/PowerScan/Geo/Tracts_All_02.shp",
    "PATH_IP_RANGES" : "/home/bitnami/Data/PowerScan/IP/MM_Southeast_05.shp"
}

ny_config = {
    "COUNTY_PATH" : "/home/bitnami/Data/NY/County/NY_Counties_04.shp",
    "TRACT_PATH" : "/home/bitnami/Data/NY/County/CensusTracts_03.shp",
# IP_RANGE_PATH = "/home/bitnami/Data/IP/FiveCounties_Minimal.shp"
    "IP_RANGE_PATH" : "/home/bitnami/Data/NY/IP/NA_All_DBs_01.shp"
}

maxm_config = {
    "IP_RANGE_PATH" : "/home/bitnami/Data/LA/IP/CityBlocks_LA_01.shp",
}

CHUNK_SIZE = 200000
SMALL_CHUNK_SIZE = 10000

class RangeChunker:
    def __init__(self):
        self._range_start = 0
        self._range_end = self._range_start + SMALL_CHUNK_SIZE
        self._last_chunk = False

    def __iter__(self):
        return self

    def __next__(self):
        if self._last_chunk:
            raise StopIteration

        print(f"RangeChunker.__next__(), querying [{self._range_start}, {self._range_end}]")
        ranges = MmIpRange.objects.all().order_by("id")[self._range_start:self._range_end]
        num_returned = ranges.count()
        print(f"RangeChunker.__next__(), returned {num_returned} rows")
        if num_returned < SMALL_CHUNK_SIZE:
            print(f"RangeChunker.__next__(), setting last chunk = True")
            self._last_chunk = True
        else:
            self._range_start = self._range_end
            self._range_end = self._range_start + SMALL_CHUNK_SIZE
        return ranges

MTW_CHUNK_SIZE = 3
class MtwChunker:
    def __init__(self):
        self._range_start = 0
        self._range_end = self._range_start + MTW_CHUNK_SIZE
        self._last_chunk = False

    def __iter__(self):
        return self

    def __next__(self):
        if self._last_chunk:
            print(f"MtwChunker.__next__(), found last chunk, returning StopIteration")
            raise StopIteration

        print(f"MtwChunker.__next__(), querying [{self._range_start}, {self._range_end}]")
        states = UsState.objects.all().order_by("id")[self._range_start:self._range_end]
        num_returned = states.count()
        print(f"MtwChunker.__next__(), returned {num_returned} rows")
        if num_returned < MTW_CHUNK_SIZE:
            print(f"MtwChunker.__next__(), setting last chunk = True")
            self._last_chunk = True
        else:
            self._range_start = self._range_end
            self._range_end = self._range_start + MTW_CHUNK_SIZE
        return states

class Loader():
    def __init__(self):
        self.counter = 0
        self.tracts = None

    def chunk_states(self, verbose=True):
        index = 0
        chunk_count = 0
        for chunk in MtwChunker():
            if chunk:
                print(f"chunk_state(), getting chunk: {chunk_count}")
                for us_state in chunk:
                    print(f"chunk_state(), [{index}]: {us_state}")
                    index = index + 1
                chunk_count = chunk_count + 1

    def run_state(self, verbose=True):
        state_shp = Path(loc_config["PATH_STATE"])
        print(f"run_state(), state_shp = {state_shp}, mapping = {mapping_state}")
        self.lm_state = LayerMapping(UsState, state_shp, mapping_state, transform=False)
        self.lm_state.save(strict=True, verbose=verbose)

    def run_county(self, verbose=True):
        county_shp = Path(loc_config["PATH_COUNTY"])
        self.lm_county = LayerMapping(County, county_shp, mapping_county, transform=False)
        self.lm_county.save(strict=True, verbose=verbose)

    def run_tracts(self, verbose=False, progress=500):
        tract_shp = Path(loc_config["PATH_TRACTS"])
        self.lm_tracts = LayerMapping(CensusTract, tract_shp, mapping_tract, transform=False)
        self.lm_tracts.save(strict=True, verbose=verbose, progress=progress)

    # I don't know why we do this as a two-step thing.  Seems like we should be able to do the county
    # lookup on the LayerMapping()
    def run_ip_ranges_maxm(self, verbose=False, progress=1000):
        ip_range_shp = Path(loc_config["PATH_IP_RANGES"])
        self.lm_ranges = LayerMapping(MmIpRange, ip_range_shp, mapping_maxm_range, transform=False)
        # Throws exception, should wrap in a try{}
        self.lm_ranges.save(strict=True, verbose=verbose, progress=progress)
        print(f"ranges saved, now run: map_ranges_census_maxm()")

    def _create_tract_count(self, census_tract):
        print(f"create_tract_count(), creating new, {census_tract}")
        tract_count = CountTract()
        tract_count.census_tract = census_tract
        tract_count.mpoint = MultiPoint(Point(float(census_tract.interp_long), 
            float(census_tract.interp_lat)))
        #tract_count.ip_source = ip_range_source
        self.hash_tracts[census_tract.tract_id] = tract_count
        return tract_count

    def _aggregate_range(self, range):
        tract = range.census_tract
        #print(f"Looking up tract: {tract}")
        if tract.tract_id in self.hash_tracts:
            tract_count = self.hash_tracts[tract.tract_id]
        else:
            tract_count = self._create_tract_count(tract)
        tract_count.range_count = tract_count.range_count + 1 


        # Should save here
        for tract_id, tract_count in self.hash_tracts.items():
            print(f"aggregate_tracts(), save[{tract_id}]: count = {tract_count.range_count}")
            tract_count.save()

    # Build a big hash of census tract(id) to an empty count
    def _create_hash_tract_counts(self):
        print(f"_create_hash_tract_counts(), creating hash of empty counts")
        self.hash_tracts = {}
        #point = Point(float(range.mm_longitude), float(range.mm_latitude))
        index = 0
        for tract in CensusTract.objects.all().order_by("id"):
            long = tract.interp_long
            if not long:
                print(f"_create_hash_tract_counts(), tract = {tract.id}, long = {long}")
                break
            lat = tract.interp_lat
            if not lat:
                print(f"_create_hash_tract_counts(), tract = {tract.id}, lat = {lat}")
                break
            mpoint = MultiPoint(Point(float(long), float(lat)))
            if index % 1000 == 0:
                print(f"_create_hash_tract_counts(), [{index}], creating count from {tract}")
            new_counter = CountTract(census_tract=tract, mpoint=mpoint)
            self.hash_tracts[tract.id] = new_counter 
            index = index + 1

    def _save_hash_tract_counts(self):
        print(f"_save_hash_tract_counts(), iterating through dictionary...")
        for tract_id, new_counter in self.hash_tracts.items():
            if new_counter.range_count > 0:
                print(f"_save_hash_tract_counts(), tract_id[{tract_id}] = {new_counter.range_count}")
                new_counter.save()

    def aggregate_tracts_maxm(self, verbose=False):
        # Create empty counts
        self._create_hash_tract_counts()
        index = 0
        print(f"aggregate_tracts_maxm(), starting iteration...")
        for chunk in RangeChunker():
            for range in chunk:
                if not range.census_tract.id in self.hash_tracts:
                    first = "aggregate_tracts_maxm(), could not find census_tract.id = "
                    second = f"{range.census_tract.id} in hash table (ignoring!)"
                    print(first + second)
                    continue
                count = self.hash_tracts[range.census_tract.id]
                if index % 1000 == 0:
                    print(f"range[{index}] = ip: {range}, tract(counter): {count}")
                if not count:
                    raise Exception(f"aggregate_tracts_maxm(), could not find census_tract.id = {range.census_tract.id}")
                count.range_count = count.range_count + 1
                index = index + 1

        # Save non-zero counts
        self._save_hash_tract_counts()

    def _create_county_counter(self, county, ip_range_source):
        county_counter = CountCounty()
        county_counter.county_code = county
        #county_counter.ip_source = ip_range_source
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
        print(f"aggregate_counties()")
        #ip_range_source = IpRangeSource.objects.get(pk=source_id)
        self.hash_counties = {}
        chunker = RangeChunker()
        
        # for tract_range in CountTract.objects.filter(ip_source__id=source_id):
        for tract_range in CountTract.objects.all():
            county = tract_range.census_tract.county_code
            code = county.county_code
            print(f"tract: {tract_range.census_tract.tract_id}, Looking up county: {code}")
            if code in self.hash_counties:
                county_counter = self.hash_counties[code]
            else:
                county_counter = self._create_county_counter(county, ip_range_source)
            # +1 here counts the number of tracts, we want the number of IP ranges
            county_counter.range_count = county_counter.range_count + tract_range.range_count
        # Should save here
        for county_code, county_counter in self.hash_counties.items():
            print(f"save[{county_code}]: source = {ip_range_source}, count = {county_counter.range_count}")
            county_counter.save()


#    def load_ip_source(self, verbose=True):
#        # Census tract 222, \n 217
#        sources = ["Dig El", "Max Mind"]
#        for index, name in enumerate(sources):
#            range_source = IpRangeSource(description=name)
#            range_source.save()

#    def map_ranges_census_maxm(self, verbose=False, progress=1000):
#        self.tracts = CensusTract.objects.all()
#        self.error_count = 0
#        print(f"map_ranges_census_maxm(), read {self.tracts.count()} census tracts")
#        ranges = MmIpRange.objects.all().exclude(census_tract_id__isnull=False).order_by("id")
#        index_range = 0
#        for range in ranges:
#            self._map_single_range_digel(range, index_range, 2)
#            index_range = index_range + 1

#
# CUT
# 
    def aggregate_tracts_digel(self, verbose=False):
        self.hash_tracts = {}
        self.error_count = 0
        index_chunk = 0
        range_start = 0
        range_end = range_start + SMALL_CHUNK_SIZE
        index_range = 0
        self.error_count = 0
        while True:
            # Find ranges w/ no census tract ID (mapped)
            ranges = DeIpRange.objects.all().order_by("id")[range_start:range_end]
            ranges_returned = ranges.count()
            print(f"aggregate_tracts_digel(), querying [{range_start},{range_end},{ranges_returned}]")
            for range in ranges:
                if index_range % 1000 == 0:
                    print(f"a_t_d(), aggregating range = {index_range}")
                self._aggregate_range(range)
                index_range = index_range + 1
                #print(f"Looking up tract: {tract}")
            if ranges_returned < SMALL_CHUNK_SIZE or self.error_count > 3:
                print(f"aggregate_tracts_digel(), ranges_returned = {ranges_returned}, error_count = {self.error_count}, breaking")
                # We didn't get a full batch and we've iterated over it
                break
            range_start = range_start + SMALL_CHUNK_SIZE
            range_end = range_end + SMALL_CHUNK_SIZE

    def map_ranges_census_digel(self, verbose=False, progress=1000):
        self.tracts = CensusTract.objects.all()
        self.error_count = 0
        print(f"map_ranges_census_digel(), read {self.tracts.count()} census tracts")
        index_chunk = 0
        range_start = 0
        range_end = range_start + CHUNK_SIZE
        index_range = 0
        num_objects = DeIpRange.objects.count()
        while True:
            # Find ranges w/ no census tract ID (mapped)
            ranges = DeIpRange.objects.all().exclude(census_tract_id__isnull=False).order_by("id")[range_start:range_end]
            ranges_returned = ranges.count()
            print(f"map_ranges_census_digel(), querying [{range_start},{range_end},{ranges_returned}]")
            for range in ranges:
                self.__map_single_range(range, index_range)
                index_range = index_range + 1
                #print(f"Looking up tract: {tract}")
            if ranges_returned < CHUNK_SIZE or self.error_count > 3:
                print(f"map_ranges_census_digel(), ranges_returned = {ranges_returned}, error_count = {self.error_count}, breaking")
                # We didn't get a full batch and we've iterated over it
                break
            range_start = range_start + CHUNK_SIZE
            range_end = range_end + CHUNK_SIZE

    # I don't know why we do this as a two-step thing.  Seems like we should be able to do the county
    # lookup on the LayerMapping()
    def run_ip_ranges_digel(self, verbose=False, progress=1000):
        ip_range_shp = Path(loc_config["IP_RANGE_PATH"])
        self.lm_ranges = LayerMapping(DeIpRange, ip_range_shp, digel_ip_range_mapping, transform=False)
        # Throws exception, should wrap in a try{}
        self.lm_ranges.save(strict=True, verbose=verbose, progress=progress)
        print(f"ranges saved, now run: map_ranges_census()")

    def _map_single_range(self, range, index_range):
        #point = Point(float(range.mm_longitude), float(range.mm_latitude))
        #else:
        #    raise Exception(f"_map_single_range(), invalid ip_range_source = {ip_range_source}")

        index_tract = 0
        found_in_tract = False
        for tract in self.tracts:
            # print(f"map_single_range(), checking tract: {tract}")
            found_this_tract= tract.mpoly.contains(point)
            if (found_this_tract) :
                if index_range % 1000 == 0:
                    print(f"point[{index_range}]: {point}, in tract: {tract.short_name}")
                range.census_tract = tract
                range.save()
                found_in_tract = True
                break
            index_tract = index_tract + 1
        if not found_in_tract:
            print(f"_map_single_range() index = {index_range}, could not map point {point} to a census tract!")
            self.error_count = self.error_count + 1
        return found_in_tract
#TRACT_PATH = "/home/bitnami/Data/County/CensusTracts_03.shp"

#    "company_name" : "company_na",
#    "naics_code" : "naics_code",
#    "organization" : "organizati",
#    "srs_company_name" : "srs_compan",
#    "srs_issuer_id" : "srs_issuer",
#    "srs_latitude" : "srs_latitu",
#    "srs_longitude" : "srs_longit",
#    "srs_strength" : "srs_streng",
# Check use of transform, lookup_function (for census_tract), make non-null
#digel_ip_range_mapping = {
#    "ip_range_start" : "start-ip",
#    "ip_range_end" : "end-ip",
#    "pp_cxn_speed" : "pp-conn-sp",
#    "pp_cxn_type" : "pp-conn-ty",
#    "pp_latitude" : "pp-latitud",
#    "pp_longitude" : "pp-longitu",
#    "mpoint" : "MULTIPOINT",
#}
#MARKER_PATH = "/home/bitnami/Data/IP/Markers_02.shp"
#marker_mapping = {
#    "id", "id",
#    "name", "Name",
#    "location", "MULTIPOINT",
#}

# Field from models.py, mapped to field names from the shape file
    # COUNTY
    # STATE
    # COUNTY_1
    # STATE_1
# Regular county: "county_name": "COUNTY", "county_code": "COUNTY_1",
#    "pop2000": "POP2000",
# These align with the GU CountyOrEquivalent (USGS, National Map)
