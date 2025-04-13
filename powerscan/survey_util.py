import sys
import logging

from django.shortcuts import get_object_or_404

from django.contrib.gis.geos import MultiPolygon

logger = logging.getLogger(__name__)
#print(f"SurveyUtil: name = {__name__}, logger = {logger}")

SMALL_CHUNK_SIZE = 10000

class SurveyUtil:
    @staticmethod
    def copy_geography(survey_id, parent_survey_id):
        from .models import (IpRangeSurvey, IpSurveyState, IpSurveyCounty, IpSurveyTract)

        survey = get_object_or_404(IpRangeSurvey, pk=survey_id)
        parent_survey = get_object_or_404(IpRangeSurvey, pk=parent_survey_id)

        state_set = parent_survey.ipsurveystate_set.all()
        for parent_state in state_set:
            new_survey_state = IpSurveyState(survey=survey,us_state=parent_state.us_state)
            new_survey_state.save()

        county_set = parent_survey.ipsurveycounty_set.all()
        for parent_county in county_set:
            new_survey_county = IpSurveyCounty(survey=survey, county=parent_county.county)
            new_survey_county.save()

        tract_set = parent_survey.ipsurveytract_set.all()
        for parent_tract in tract_set:
            new_survey_tract = IpSurveyTract(survey=survey,tract=parent_tract.tract)
            new_survey_tract.save()

        survey.ranges_pinged = parent_survey.ranges_pinged

    @staticmethod
    def _delete_surveys(survey_ids):
        from .models import (IpRangeSurvey, IpSurveyCounty, IpSurveyTract)

        logger.warn(f"PSM._delete_surveys(), surveys: {survey_ids}")
        for survey_id in survey_ids:
            logger.warn(f"   deleting survey = {survey_id}")
            survey = get_object_or_404(IpRangeSurvey, pk=survey_id)

            iprange_set = survey.iprangeping_set.all()
            for range1 in iprange_set:
                range1.delete()

            tract_set = survey.ipsurveytract_set.all()
            for tract in tract_set:
                tract.delete()

            county_set = survey.ipsurveycounty_set.all()
            for county in county_set:
                county.delete()

            state_set = survey.ipsurveystate_set.all()
            for state in state_set:
                state.delete()

            num_tracts = tract_set.count()
            num_counties = county_set.count()
            num_states = state_set.count()
            logger.warn(f"      deleted s/c/t: {num_states}/{num_counties}/{num_tracts}")
            survey.delete()
        return True

    @staticmethod
    def link_file_string(survey_id, parent_survey_id):
        from .ping import PingSurveyManager

        return PingSurveyManager.link_survey(survey_id, int(parent_survey_id))

    @staticmethod
    def calculate_bbox(survey_id):
        from .models import (IpRangeSurvey)

        survey = get_object_or_404(IpRangeSurvey, pk=survey_id)
        # print(f"SurveyUtil.calculate_bbox about to call logger.info()")
        # logger.info(f"(LOGGER) calculate_bbox(), create empty")
        mpoly_combined = MultiPolygon()

        state_set = survey.ipsurveystate_set.all()
#        num_states = state_set.count()
#        if num_states > 1:
#            logger.warn(f"(LOGGER) calculate_bbox(), for now, just taking the first state!")
#        first_state = state_set[0]
        for state in state_set:
            us_state = state.us_state
            mpoly = us_state.mpoly
            for poly in mpoly:
                mpoly_combined.append(poly)
        bbox = mpoly_combined.extent
        logger.info(f"(LOGGER)  calculate_bbox(), final extent: {bbox}")
        return bbox

    @staticmethod
    def last_n_surveys_state(survey_id, limit):
        survey = get_object_or_404(IpRangeSurvey, pk=survey_id)
        state_set = survey.ipsurveystate_set.all()
        num_states = state_set.count()
        if num_states > 1:
            logger.warn(f"(LOGGER) last_n_surveys_state(), for now, just taking the first state!")
        first_state = state_set[0]
        logger.info(f"(LOGGER) last_n_surveys_state(), first_state = {first_state}")

class GeometryRangeChunker:
    def __init__(self,survey_id=0):
        self._range_start = 0
        self._range_end = self._range_start + SMALL_CHUNK_SIZE
        self._last_chunk = False
        self._survey_id = survey_id

    def __iter__(self):
        return self

    def __next__(self):
        from .models import (IpRangePing)

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

class GeoCountUpdater:
    def __init__(self, survey_id):
        self._survey_id = survey_id
        
    def _unused_update_tract_counts(self):
        # 1. build mapping
        for tract_counter in IpSurveyTract.objects.filter(survey__id=self._survey_id):
            hosts_pinged = tract_counter.hosts_pinged
            if hosts_pinged != 0:
                print(f"_update_tract_counts(), hosts_pinged = {hosts_pinged}! (aborting, already values)")
                return 0
            # Build the hash table
            self._tract_mapper[tract_counter.tract] = tract_counter
            
        # 2. Update counts
        index_chunk = 0
        total_ranges_responded = 0
        for chunk in GeometryRangeChunker(survey_id=self._survey_id):
            print(f"_update_tract_counts(), processing chunk[{index_chunk}]")
            for range_ping in chunk:
                hosts_pinged = range_ping.hosts_pinged
                hosts_responded = range_ping.hosts_responded
                tract = range_ping.ip_range.census_tract
                if tract in self._tract_mapper:
                    counter = self._tract_mapper[tract]
                    counter.hosts_pinged = counter.hosts_pinged + hosts_pinged
                    counter.hosts_responded = counter.hosts_responded + hosts_responded
                    total_ranges_responded = total_ranges_responded + 1
                else:
                    print(f"_u_t_c(), could not find tract: {tract}")
            index_chunk = index_chunk + 1
        thousands = total_ranges_responded / 1000.0
        print(f"_update_tract_counts(), non-zero ranges: {thousands:.2f}, num_tracts = {len(self._tract_mapper)}")

        # 3. Now, iterate through the hash table and save everything with counts
        total_hosts_responded = 0
        zero_tracts = 0
        for i, tract in enumerate(self._tract_mapper):
            counter = self._tract_mapper[tract]
            hosts_pinged = counter.hosts_pinged
            hosts_responded = counter.hosts_responded
            if hosts_responded == 0:
                zero_tracts = zero_tracts + 1
            total_hosts_responded = total_hosts_responded + hosts_responded
            # print(f"_update_tract_counts(), saving tract {tract.name}")
            counter.save()
        thousands = total_hosts_responded / 1000.0
        print(f"_update_tract_counts(), total_hosts = {thousands:.1f}k, zero tracts = {zero_tracts}")
        return total_ranges_responded 

    def _update_county_counts(self):
        from .models import (IpSurveyCounty)

        func_name = sys._getframe().f_code.co_name
        # 1: Set up the mapping, Map the counties to the count objects
        county_count = 0
        county_set = IpSurveyCounty.objects.filter(survey__id=self._survey_id)
        for county_counter in county_set:
            hosts_pinged = county_counter.hosts_pinged
            if hosts_pinged != 0:
                print(f"{func_name}(), hosts_pinged = {hosts_pinged}! (aborting, already values)")
                return 0 
            county = county_counter.county
            # hash = county.__hash__()
            # print(f"_u_c_c(), county[{county_count}]: {county.county_name}, hash = {hash}")
            self._county_mapper[county_counter.county] = county_counter
            county_count = county_count + 1
        # print(f"_update_county_counts(), county_count = {county_count}")
        county_counter = None

        index_chunk = 0
        total_ranges_responded = 0
        for chunk in GeometryRangeChunker(survey_id=self._survey_id):
            print(f"{func_name}(), processing chunk[{index_chunk}]")
            for range_ping in chunk:
                hosts_pinged = range_ping.hosts_pinged
                hosts_responded = range_ping.hosts_responded
                county = range_ping.ip_range.county
                if county in self._county_mapper:
                    counter = self._county_mapper[county]
                    counter.hosts_pinged = counter.hosts_pinged + hosts_pinged
                    counter.hosts_responded = counter.hosts_responded + hosts_responded
                    total_ranges_responded = total_ranges_responded + 1
                else:
                    print(f"{func_name}(), could not find county: {county}")
            index_chunk = index_chunk + 1

        # 3: Go back to counties, save to DB
        zero_counties = 0
        for i, county in enumerate(self._county_mapper):
            county_counter = self._county_mapper[county]
            # print(f"_update_county_counts(), pulling county[{index_county}]: {county.county_name}")
            hosts_responded = county_counter.hosts_responded
            if hosts_responded == 0:
                zero_counties = zero_counties + 1
            # Save to the db
            # print(f"_update_county_counts(), saving county {county.county_name}")
            county_counter.save()
            #county_counter.save()
        if zero_counties > 0:
            print(f"{func_name}(), processed {county_set.count()} counties, {zero_counties} zeros")
        else:
            print(f"{func_name}(), processed {county_set.count() } counties, no zeroes")
        return total_ranges_responded

    def _update_state_counts(self):
        from .models import (IpSurveyState)

        # Map the states to the count objects
        state_count = 0
        # 1: Set up the mapping, Map the states to the count objects
        state_set = IpSurveyState.objects.filter(survey__id=self._survey_id)
        for state_counter in state_set:
            us_state = state_counter.us_state 
            # hash = us_state.__hash__()
            # print(f"_u_c_c(), county[{county_count}]: {county.county_name}, hash = {hash}")
            self._state_mapper[state_counter.us_state] = state_counter
            #state_count = state_count + 1
        # print(f"_update_county_counts(), county_count = {county_count}")

        # 2: Bubble counts up, Walk through all of the counties and update the corresponding states
        for i, county in enumerate(self._county_mapper):
            county_counter = self._county_mapper[county]
            # print(f"_update_county_counts(), pulling county[{index_county}]: {county.county_name}")
            state_counter = self._state_mapper[us_state]
            hosts_pinged = county_counter.hosts_pinged 
            hosts_responded = county_counter.hosts_responded
            state_counter.hosts_pinged = state_counter.hosts_pinged + \
                hosts_pinged
            state_counter.hosts_responded = state_counter.hosts_responded + \
                hosts_responded

        # 3. Save to DB
        for i, us_state in enumerate(self._state_mapper):
            state_counter = self._state_mapper[us_state]
            state_counter.save()
            # print(f"_update_state_counts(), saving state: {us_state.state_name}")
        print(f"_update_states_counts(), processed {state_set.count()} states")

    def propagate_counts(self):
        print(f"propagate_counts(), scanning survey_id: {self._survey_id}")
            # self._exec_db = False

        #self._tract_mapper = {}
        #ranges_responded = self._update_tract_counts()
        #if ranges_responded == 0:
        #    continue

        self._county_mapper = {}
        ranges_processed = self._update_county_counts()
        if ranges_processed > 0:
            self._state_mapper = {}
            self._update_state_counts()
        
