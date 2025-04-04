import logging

from pathlib import Path

from django.utils import timezone
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.geos import Point, MultiPoint
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Centroid

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from django_nys_02.asgi import application

from .consumers import CHANNEL_NAME_TASK_RESULT

from .models import (
    UsState, County, CensusTract,
    CountTract, CountCounty, CountState,
    IpRangeSurvey, IpRangePing,
    MmIpRange, DebugPowerScan,
    IpSurveyTract
)

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

logger = logging.getLogger(__name__)

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

        logger.info(f"RangeChunker.__next__(), querying [{self._range_start}, {self._range_end}]")
        ranges = MmIpRange.objects.all().order_by("id")[self._range_start:self._range_end]
        num_returned = ranges.count()
        logger.info(f"RangeChunker.__next__(), returned {num_returned} rows")
        if num_returned < SMALL_CHUNK_SIZE:
            logger.info(f"RangeChunker.__next__(), setting last chunk = True")
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
            logger.info(f"MtwChunker.__next__(), found last chunk, returning StopIteration")
            raise StopIteration

        logger.info(f"MtwChunker.__next__(), querying [{self._range_start}, {self._range_end}]")
        states = UsState.objects.all().order_by("id")[self._range_start:self._range_end]
        num_returned = states.count()
        logger.info(f"MtwChunker.__next__(), returned {num_returned} rows")
        if num_returned < MTW_CHUNK_SIZE:
            logger.info(f"MtwChunker.__next__(), setting last chunk = True")
            self._last_chunk = True
        else:
            self._range_start = self._range_end
            self._range_end = self._range_start + MTW_CHUNK_SIZE
        return states

class GeometryRangeChunker:
    def __init__(self,survey_id=0):
        self._range_start = 0
        self._range_end = self._range_start + SMALL_CHUNK_SIZE
        self._last_chunk = False
        self._survey_id = survey_id

    def __iter__(self):
        return self

    def __next__(self):
        if self._last_chunk:
            raise StopIteration

        logger.info(f"GeometryRangeChunker.__next__(), querying [{self._range_start}, {self._range_end}]")
        ranges = IpRangePing.objects.filter(ip_survey__id=self._survey_id).order_by("id")[self._range_start:self._range_end]
        num_returned = ranges.count()
        logger.info(f"GeometryRangeChunker.__next__(), returned {num_returned} rows")
        if num_returned < SMALL_CHUNK_SIZE:
            logger.info(f"GeometryRangeChunker.__next__(), setting last chunk = True")
            self._last_chunk = True
        else:
            self._range_start = self._range_end
            self._range_end = self._range_start + SMALL_CHUNK_SIZE
        return ranges

class PowerScanValueException(Exception):
    pass

class Loader():
    def __init__(self):
        self.counter = 0
        self.tracts = None

    def chunk_states(self, verbose=True):
        index = 0
        chunk_count = 0
        for chunk in MtwChunker():
            if chunk:
                logger.info(f"chunk_state(), getting chunk: {chunk_count}")
                for us_state in chunk:
                    logger.info(f"chunk_state(), [{index}]: {us_state}")
                    index = index + 1
                chunk_count = chunk_count + 1

    def run_state(self, verbose=True):
        state_shp = Path(loc_config["PATH_STATE"])
        logger.info(f"run_state(), state_shp = {state_shp}, mapping = {mapping_state}")
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
        logger.info(f"ranges saved, now run: map_ranges_census_maxm()")

    # Build a big hash of census tract(id) to an empty count
    def _create_hash_tract_counts(self):
        logger.info(f"_create_hash_tract_counts(), creating hash of empty counts")
        self.hash_tracts = {}
        #point = Point(float(range.mm_longitude), float(range.mm_latitude))
        index = 0
        for tract in CensusTract.objects.all().order_by("id"):
            long = tract.interp_long
            if not long:
                logger.info(f"_create_hash_tract_counts(), tract = {tract.id}, long = {long}")
                break
            lat = tract.interp_lat
            if not lat:
                logger.info(f"_create_hash_tract_counts(), tract = {tract.id}, lat = {lat}")
                break
            mpoint = MultiPoint(Point(float(long), float(lat)))
            if index % 1000 == 0:
                logger.info(f"_create_hash_tract_counts(), [{index}], creating count from {tract}")
            new_counter = CountTract(census_tract=tract, mpoint=mpoint)
            self.hash_tracts[tract.id] = new_counter 
            index = index + 1

    def _save_hash_tract_counts(self):
        print(f"_save_hash_tract_counts(), iterating through dictionary...")
        for tract_id, new_counter in self.hash_tracts.items():
            if new_counter.range_count > 0:
                logger.info(f"_save_hash_tract_counts(), tract_id[{tract_id}] = {new_counter.range_count}")
                new_counter.save()

    def aggregate_tracts_maxm(self, verbose=False):
        # Create empty counts
        self._create_hash_tract_counts()
        index = 0
        logger.info(f"aggregate_tracts_maxm(), starting iteration...")
        for chunk in RangeChunker():
            for range in chunk:
                if not range.census_tract.id in self.hash_tracts:
                    first = "aggregate_tracts_maxm(), could not find census_tract.id = "
                    second = f"{range.census_tract.id} in hash table (ignoring!)"
                    logger.info(first + second)
                    continue
                count = self.hash_tracts[range.census_tract.id]
                if index % 1000 == 0:
                    logger.info(f"range[{index}] = ip: {range}, tract(counter): {count}")
                if not count:
                    raise Exception(f"aggregate_tracts_maxm(), could not find census_tract.id = {range.census_tract.id}")
                count.range_count = count.range_count + 1
                index = index + 1

        # Save non-zero counts
        self._save_hash_tract_counts()

    def _create_county_counter(self, county):
        county_counter = CountCounty()
        county_counter.county = county
        long = county.interp_long
        if not long:
            raise PowerScanValueException(f"_create_county_counter(), county = {county_fp}, long = {long}")
        lat = county.interp_lat
        if not lat:
            raise PowerScanValueException(f"_create_county_counter(), county = {county_fp}, lat = {lat}")
        # mpoint = MultiPoint(Point(float(long), float(lat)))
        point = Point(float(long), float(lat))
        county_counter.centroid = point
        self.hash_counties[county.geoid] = county_counter
        return county_counter

    def aggregate_counties(self, verbose=False):
        logger.info(f"aggregate_counties()")
        #ip_range_source = IpRangeSource.objects.get(pk=source_id)
        self.hash_counties = {}
        
        index_tract = 0
        # for tract_range in CountTract.objects.filter(ip_source__id=source_id):
        for tract_counter in CountTract.objects.all():
            county = tract_counter.census_tract.county
            geoid = county.geoid 
            if index_tract % 100 == 0:
                logger.info(f"tract[{index_tract}], id: {tract_counter.census_tract.tract_id}, Looking up county: {geoid}")
            try:
                if geoid in self.hash_counties:
                    county_counter = self.hash_counties[geoid]
                else:
                    county_counter = self._create_county_counter(county)
                # +1 here counts the number of tracts, we want the number of IP ranges
                county_counter.range_count = county_counter.range_count + tract_counter.range_count
            except PowerScanValueException as e:
                logger.error(f"aggregate_counties(), e: {e}")
            index_tract = index_tract + 1
        # Should save here
        index_county = 0
        for geoid, county_counter in self.hash_counties.items():
            logger.info(f"county[{index_county}], save[{geoid}]: count = {county_counter.range_count}")
            county_counter.save()
            index_county = index_county + 1

    def _create_state_counter(self, us_state):
        state_counter = CountState()
        state_counter.us_state = us_state
        long = us_state.interp_long
        if not long:
            raise PowerScanValueException(f"_create_state_counter(), state = {us_state.state_name}, long = {long}")
        lat = us_state.interp_lat
        if not lat:
            raise PowerScanValueException(f"_create_state_counter(), state = {us_state.state_name}, lat = {lat}")
        point = Point(float(long), float(lat))
        state_counter.centroid = point
        self.hash_states[us_state.state_fp] = state_counter
        return state_counter

    def aggregate_states(self, verbose=False):
        logger.info(f"aggregate_states()")
        #ip_range_source = IpRangeSource.objects.get(pk=source_id)
        self.hash_states = {}
        
        index_county = 0
        # for tract_range in CountTract.objects.filter(ip_source__id=source_id):
        for county_counter in CountCounty.objects.all():
            county = county_counter.county
            state = county.us_state
            state_fp = state.state_fp 
            if index_county % 100 == 0:
                logger.info(f"county[{index_county}], id: {county.geoid}, Looking up state: {state_fp}")
            try:
                if state_fp in self.hash_states:
                    state_counter = self.hash_states[state_fp]
                else:
                    state_counter = self._create_state_counter(state)
                # +1 here counts the number of tracts, we want the number of IP ranges
                state_counter.range_count = state_counter.range_count + county_counter.range_count
            except PowerScanValueException as e:
                logger.error(f"aggregate_states(), e: {e}")
            index_county = index_county + 1
        # Should save here
        for _, state_counter in self.hash_states.items():
            logger.info(f"Saving state: {state_counter.us_state.state_name}, {state_counter.range_count}")
            state_counter.save()

    def load_state_counts(self, verbose=False):
        # ('78',      34),
        counts = [
            ('01', 52689),
            ('12', 224637),
            ('13', 105332),
            ('22',  31860),
            ('28',  18817),
            ('37', 153162),
            ('45',  50655),
            ('48', 322290),
            ('72',   3512),
            ]
        for count in counts:
            state_fp = count[0]
            estimated_count = count[1]
            logger.info(f"load_state_counts(), looking for state = {state_fp}")
            us_state = UsState.objects.get(state_fp=state_fp)
            state_counter = CountState.objects.get(us_state=us_state)
            state_counter.estimated_ranges = estimated_count
            state_counter.save()

            logger.info(f"load_state_counts(), found state_counter = {state_counter.id}, setting to {estimated_count}")
        

    # Try and get the Django channels stuff working (works w/ a Django worker, but not with celery.
    # Was hoping that Django would serve the WSGI channel name stuff (since we're running w/ daphne now).
    def ping_c(self):
        try:
            channel_layer = get_channel_layer()
            logger.info(f"ping_c(), channel_layer = {channel_layer}")
                #"background_tasks",
            # This should probably use a group_send (to be consistent)
            #result = async_to_sync(channel_layer.send) (
            channel_layer.group_send(CHANNEL_GROUP_CONTROLLERS,
                CHANNEL_NAME_TASK_RESULT,
                {
                    # This should match the method name
                    "type": "process_task_result",
                    "task_result_data": "some sample data here",
                })
        except Exception as e:
            logger.error(f"ping_c(), exception {e}")
        logger.info(f"   result = {result}")


    def mil_state(self, verbose=False):
        path01 = "/home/bitnami/Data/PowerScan/Military/Military_State.shp"
        state_shp = Path(path01)
        military_state = {
            "state_fp": "STATEFP",
            "state_name": "NAME",
            "interp_lat": "INTPTLAT",
            "interp_long": "INTPTLON",
            "mpoly": "MULTIPOLYGON",
            "state_abbrev": "STATE_ABBR",
        }
        # Need to set virtual to True in here!
        lm = LayerMapping(UsState, state_shp, military_state, transform=False)
        lm.save(strict=True, verbose=verbose)

    def fix_names(self, verbose=True):
        index = 0
        for survey in IpRangeSurvey.objects.all():
            # print(f"fix_name(), survey[{index}] = {survey.id}")
            states = survey.ipsurveystate_set.all()
            f = lambda state_survey: state_survey.us_state.state_abbrev
            abbrevs = [f(x) for x in states]
            state_string = ",".join(abbrevs)
            # print(f"      name = {state_string}")
            survey.name = state_string
            # print(f"SURVEY SAVE, 3")
            survey.save()
            index = index + 1

    def create_debug(self):
        debug_power = DebugPowerScan(profile_name="Primary")
        debug_power.save()

    def _update_tract_counts(self):
        for tract_counter in IpSurveyTract.objects.filter(survey__id=self._survey_id):
            ranges_pinged = tract_counter.num_ranges_pinged
            if ranges_pinged != 0:
                print(f"_update_tract_counts(), ranges_pinged = {ranges_pinged}! (aborting)")
                return
            # Build the hash table
            self._tract_mapper[tract_counter.tract] = tract_counter
            
        index_chunk = 0
        total_ranges_responded = 0
        for chunk in GeometryRangeChunker(survey_id=self._survey_id):
            print(f"_update_tract_counts(), processing chunk[{index_chunk}]")
            for range_ping in chunk:
                num_ranges_responded = range_ping.num_ranges_responded
                if num_ranges_responded > 0:
                    tract = range_ping.ip_range.census_tract
                    if tract in self._tract_mapper:
                        counter = self._tract_mapper[tract]
                        counter.num_ranges_pinged = counter.num_ranges_pinged + range_ping.num_ranges_pinged
                        counter.num_ranges_responded = counter.num_ranges_responded + range_ping.num_ranges_responded
                    total_ranges_responded = total_ranges_responded + 1
            index_chunk = index_chunk + 1
        thousands = total_ranges_responded / 1000.0
        print(f"_update_tract_counts(), num_ranges with non-zero = {thousands:.2f}")

        # Now, iterate through the hash table and save everything with counts
        total_hosts_responded = 0
        total_zero_tracts = 0
        for i, tract in enumerate(self._tract_mapper):
            counter = self._tract_mapper[tract]
            num_ranges_responded = counter.num_ranges_responded
            if num_ranges_responded == 0:
                total_zero_tracts = total_zero_tracts + 1
            else:
                num_ranges_pinged = models.IntegerField(default=0)
                total_hosts_responded = total_hosts_responded + num_ranges_responded
        thousands = total_hosts_responded / 1000.0
        print(f"_update_tract_counts(), total_hosts = {thousands:.1f}, zero tracts = {total_zero_tracts}")

    def _update_county_counts(self):
        # Map the counties to the count objects
        for county_counter in IpSurveyCounty.objects.filter(survey__id=self._survey_id):
            self._county_mapper[county_counter.county] = county_counter

        for i, tract in enumerate(self._tract_mapper):
            tract_counter = tract_mapper[tract]
            num_ranges_responded = tract_counter.num_ranges_responded
            if num_ranges_responded > 0:
                county = county_counter.county
                if county not in self._county_mapper:
                    print(f"_update_county_counts(), could not find county {county}, bailing!")
                    return
                county_counter = self._county_mapper[county]
                county_counter.num_ranges_pinged = county_counter.num_ranges_pinged + \
                    tract_counter.num_ranges_pinged 
                county_counter.num_ranges_responded = county_counter.num_ranges_responded + \
                    tract_counter.num_ranges_responded 

        zero_counties = 0
        index_county = 0
        for i, county in self._county_mapper.enumerate(self._county_mapper):
            counter = self._county_mapper[county]
            num_ranges_responded = counter.num_ranges_responded
            if num_ranges_responded == 0:
                zero_counties = zero_counties + 1
            else:
                num_ranges_pinged = counter.num_ranges_pinged
                responded_k = num_ranges_responded / 1000.0
                pinged_k = num_ranges_pinged
                print(f"_update_county_counts(), county[{index_county}], {responded_k:.1f}/{pinged_k:.1f}")
                index_county = index_county + 1
        if zero_counties > 0:
            print(f"_update_county_counts(), {zero_counties} zero counties")

    def update_geo_counts(self, verbose=True):
        self._survey_id = 450
        self._exec_db = False

        self._tract_mapper = {}
        self._update_tract_counts()

        self._county_mapper = {}
        self._update_county_counts()



            

        

