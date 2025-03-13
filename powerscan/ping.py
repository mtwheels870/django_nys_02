import os
import datetime

import pandas as pd
import ipaddress
import netaddr

from cidr_trie import PatriciaTrie
import cidr_trie.cidr_util

from django.utils import timezone

from .models import (
    IpRangeSurvey, CountTract, IpRangePing, 
    MmIpRange, IpSurveyState, IpSurveyCounty,
    IpSurveyTract,
    County, CensusTract)

TEMP_DIRECTORY = "/tmp/exec_zmap/"
FILE_RANGE_IP = "RangeIp.csv"
FILE_WHITELIST = "Whitelist.csv"
FILE_OUTPUT = "ZmapOutput.csv"
FILE_METADATA = "Metadata.csv"
FILE_LOG = "Log.txt"
FILE_TRAVERSE_GEO = "TraverseGeo.txt"
FILE_CIDR_TRIE = "CidrTrie.txt"

HEADER = "range_id,ip_network\n"

class RangeIpCount:
    def __init__(self, db_range_id, ip_network, possible_hosts):
        self.id = db_range_id
        self.ip_network = ip_network
        self.possible_hosts = possible_hosts
        self.count = 0

    def str(self):
        return f"range[{self.id}] = {self.ip_network}, count = {self.count}"

    
class PingSurveyManager:
    class FileDebugger:
        def __init__(self, directory, name):
            self._full_path = os.path.join(directory, FILE_TRAVERSE_GEO)
            self._writer = open(self._full_path, "w+")

        def close(self):
            self._writer.close()

        def get_file(self):
            return self._full_path

        def print_one_line(self, sub_array):
            sub_array_strings = map(str, sub_array)
            array_string = ", ".join(sub_array_strings)
            self._writer.write(array_string + "\n")

        def print(self, description, array_output):
            array_len = len(array_output)
            print(f"FileDebugger.print(), description = {description}, array_len = {array_len}")
            self._writer.write(description + "\n")
            index = 0
            while array_len > 0:
                end = index + 15
                sub_array = array_output[index:end]
                sub_array_len = len(sub_array)
                # print(f"FileDebugger.print(), array_len = {array_len}, querying [{index},{end}],
                #      sub_array_len = {sub_array_len}")
                if sub_array_len == 0:
                    # Shouldn't get here
                    break
                self.print_one_line(sub_array)
                # Print subarray here
                index = end
                array_len = array_len - sub_array_len

    def __init__(self, survey_id, create_new=True, linked_survey_id=None):
        self._survey_id = survey_id
        if create_new:
            self._create_directory()
        else:
            # This is duplicative (with the find() call below)
            survey_dir_name = PingSurveyManager._build_survey_name(survey_id)
            full_path = os.path.join(TEMP_DIRECTORY, survey_dir_name)
            self.directory = full_path
        # In either init() [create or read existing], we want to configure the files
        self._configure_whitelist_files()

    @staticmethod
    def find(survey_id_string):
        survey_id = survey_id_string
        return PingSurveyManager._find_survey(survey_id)
        
    @staticmethod
    def _build_survey_name(survey_id) -> str:
        folder_snapshot = f"Survey_{survey_id:05d}"
        return folder_snapshot

    @staticmethod
    def _find_survey(survey_id):
        survey_dir_name = PingSurveyManager._build_survey_name(survey_id)
        full_path = os.path.join(TEMP_DIRECTORY, survey_dir_name)
        if not os.path.exists(full_path):
            print(f"PingSurveyManager._find_survey(), could not find path: {full_path}")
            return None
        psm = PingSurveyManager(survey_id, create_new=False)
        return psm

    @staticmethod
    def _unused_load_all_surveys():
        most_recent_dir = None
        with os.scandir(TEMP_DIRECTORY) as entries:
            for entry in entries:
                if entry.is_file():
                    continue
                if not most_recent_dir :
                    most_recent_dir = entry
                elif entry.name > most_recent_dir.name:
                    most_recent_dir = entry
        if not most_recent_dir:
            raise Exception(f"_load_latest(), could not find a data directory in: {TEMP_DIRECTORY}")
        print(f"_load_latest(), using most_recent_dir {most_recent_dir.name}")
        self.directory = most_recent_dir.path

    def _create_directory(self):
        # now = datetime.datetime.now()
        # folder_snapshot = now.strftime("%Y%m%d_%H%M%S")
        # folder_snapshot = f"Survey_{self._survey_id:05d}"
        folder_snapshot = PingSurveyManager._build_survey_name(self._survey_id)
        full_path = os.path.join(TEMP_DIRECTORY, folder_snapshot)
        print(f"PSM.create_directory(), directory = {str(full_path)}")
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        self.directory = full_path

    def _traverse_geography(self):
        debugger = self.FileDebugger(self.directory, "TraverseGeography")
        survey = IpRangeSurvey.objects.get(pk=self._survey_id)
        print(f"PSM._traverse_geography(), survey = {survey}")
        
        selected_survey_states = IpSurveyState.objects.filter(survey_id=self._survey_id)

        # debugger.print("PSM._traverse_geography(), selected_survey_states:", selected_survey_states)

        print(f"PSM._traverse_geography(), selected_survey_states = {selected_survey_states}")

        state_ids = []
        for survey_state in selected_survey_states :
            state_ids.append(survey_state.us_state.id)

        debugger.print("PSM._traverse_geography(), state_ids:", state_ids)

        county_ids = []

        # Could also do:
        # counties = state.county_set.all()
        counties_in_state = County.objects.filter(us_state__id__in=state_ids)
        for county in counties_in_state:
            county_ids.append(county.id)
            survey_county = IpSurveyCounty(survey=survey, county=county)
            survey_county.save()
        #print(f"PSM._traverse_geography(), county_ids = {county_ids}")
        debugger.print("PSM._traverse_geography(), county_ids:", county_ids)

        total_ranges = 0
        tract_ids = []
        tracts_in_counties = CensusTract.objects.filter(county__id__in=county_ids)
        for tract in tracts_in_counties:
            tract_ids.append(tract.id)
            survey_tract = IpSurveyTract(survey=survey, tract=tract)
            survey_tract.save()
            ranges_added = self._tract_ranges_whitelist(tract)
            total_ranges = total_ranges + ranges_added
        debugger.print("PSM._traverse_geography(), tract_ids:", tract_ids)

        file_name = debugger.get_file()
        debugger.close()
        print(f"PSM._traverse_geography(), file output: {file_name}, total_ranges = {total_ranges}")
        return total_ranges

    def _tract_ranges_whitelist(self, tract):
        # Use the set() notation
        ip_ranges = tract.mmiprange_set.all()
        for range in ip_ranges:
            string1 = f"{range.id},{range.ip_network}\n"
            self.writer_range_ip.write(string1)
            self.writer_whitelist.write(f"{range.ip_network}\n")
        ranges_added = ip_ranges.count()
        return ranges_added

    # Return the number of ranges
    def _configure_whitelist_files(self):
        self.path_range_ip = os.path.join(self.directory, FILE_RANGE_IP)
        self.path_whitelist = os.path.join(self.directory, FILE_WHITELIST)
        self.path_output = os.path.join(self.directory, FILE_OUTPUT)
        self.path_metadata = os.path.join(self.directory, FILE_METADATA)
        self.path_log = os.path.join(self.directory, FILE_LOG)

        # By default, set these to None
        self.writer_range_ip = None
        self.writer_whitelist = None
        self.writer_log = None

    # Return the number of ranges
    def _create_writers(self):
        # range_ip is how we get back to the databaes (ip_range_id (in the database), to network).
        self.writer_range_ip = open(self.path_range_ip, "w+")
        self.writer_range_ip.write(HEADER)
        self.writer_whitelist = open(self.path_whitelist, "w+")
        self.writer_log = open(self.path_log, "w+")

    def build_whitelist(self):
        self._create_writers()
        num_ranges = self._traverse_geography()
        return num_ranges

    def unused_add(self, index, range_id, ip_network):
        if index == 0:
            self.writer_range_ip.write(HEADER)
        string1 = f"{range_id},{ip_network}\n"
        self.writer_range_ip.write(string1)
        self.writer_whitelist.write(f"{ip_network}\n")

    def get_zmap_files(self):
        return self.path_whitelist, self.path_output, self.path_metadata, self.path_log 

    def _calculate_possible(self, cidr):
        ip_network = ipaddress.ip_network(cidr)
        return 1 << (ip_network.max_prefixlen - ip_network.prefixlen)

    # Build a radix tree of the ip address
    def _build_radix_tree(self):
        full_path = os.path.join(self.directory, FILE_CIDR_TRIE)
        self._writer_cidr_trie = open(full_path, "w+")
        self.trie = PatriciaTrie()
        df = self.df_ranges = pd.read_csv(self.path_range_ip)
        column_names = df.columns.tolist()
        #print(f"_build_radix_tree(), num_rows = {df.shape[0]}, columns = {column_names}")
        for index, row in df.iterrows():
            range_id = row['range_id']
            ip_network = row['ip_network']
            #print(f"RangeIp({range_id},{ip_network})")
            possible_hosts = self._calculate_possible(ip_network)
            # Hang a counter on the tree
            range_ip = RangeIpCount(range_id, ip_network, possible_hosts)
            self._writer_cidr_trie.write(f"Trie_insert: {ip_network}")
            self.trie.insert(ip_network, range_ip)

    def _match_zmap_replies(self):
        df = pd.read_csv(self.path_output)
        column_names = df.columns.tolist()
        #print(f"_match_zmap_replies(), num_rows = {df.shape[0]}, column_names = {column_names}")
        for index, row in df.iterrows():
            saddr = row['saddr']
            timestamp = row['timestamp-ts']
            self._writer_cidr_trie.write(f"Trie_lookup: {saddr}")
            print(f"_match_zmap_replies(), saddr = {saddr}")
            results = self.trie.find_all(saddr)
            num_results = len(results)
            #if index < 20:
            #    print(f"[{index}], saddr = {saddr}, timestamp = {timestamp}, results = {results}")
            #    print(f"        results = {results}")
            if num_results == 0:
                print(f"_match_zmap_replies(), no Trie results for {saddr}!")
            elif num_results > 1:
                print(f"_match_zmap_replies(), multiple Trie results for {saddr}!")
            else:
                address = results[0][0]
                counter = results[0][1]
                #if index < 20:
                #    print(f"    found ONE, address = {address}, counter = {counter}")
                counter.count = counter.count + 1
        self._writer_cidr_trie.close()
        print(f"_match_zmap_replies(), debug_file {FILE_CIDR_TRIE}")

    def _save_to_db(self, survey):
        # print(f"_save_to_db(), size (of tree): {self.trie.size}")
        # Iterate the entire tree
        index = 0

        saved_to_db = 0
        # Walk through our dataframe again
        for index, row in self.df_ranges.iterrows():
            range_id = row['range_id']
            ip_network = row['ip_network']
            
            #print(f"_save_to_db(), looking up [{range_id}], ip_network {ip_network}")
            network_parts = cidr_trie.cidr_util.cidr_atoi(ip_network) 
            target_mask = network_parts[1]
            # Now, look up each network in our trie
            index = 0
            for node in self.trie.traverse(ip_network):
                # print(f"_save_to_db(), traverse[{index}] = ip: x{node.ip:08X}, bit = {node.bit}, masks = {node.masks}")
                ip_string = cidr_trie.cidr_util.ip_itoa(node.ip, False)
                #print(f"_save_to_db(), traverse[{index}] = ip: {ip_string}, bit = {node.bit}, masks = {node.masks}")
                if target_mask in node.masks:
                    ip_range_counter = node.masks[target_mask]
                    count = ip_range_counter.count
                    if count > 0:
                        ip_range = MmIpRange.objects.get(pk=ip_range_counter.id)
                        possible_hosts = ip_range_counter.possible_hosts
                        range_ping = IpRangePing(ip_survey=survey,ip_range=ip_range,
                            num_ranges_pinged=possible_hosts,
                            num_ranges_responded=count,
                            time_pinged=timezone.now())
                        range_ping.save()
                        saved_to_db = saved_to_db + 1
                    break
                #ip_range = node.masks
                #print(f"           count = {ip_range.count}")
                index = index + 1
        print(f"_save_to_db(), saved {saved_to_db} objects to database")
        return saved_to_db

    # Returns the number of pings saved to the database (count > 0)
    def process_results(self, survey):
        self._unmatched_list = []
        self._build_radix_tree()
        self._match_zmap_replies()
        return self._save_to_db(survey)
        
    def close(self):
        if self.writer_range_ip:
            self.writer_range_ip.close()

        if self.writer_whitelist:
            self.writer_whitelist.close()

        if self.writer_log:
            self.writer_log.close()
