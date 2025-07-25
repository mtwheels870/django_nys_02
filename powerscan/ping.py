#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, PINP01NT, LLC
#
# https://pinp01nt.com/
#
# All rights reserved.

"""
Docstring here

Authors: Michael T. Wheeler (mike@pinp01nt.com)

"""
import os
import datetime

import pandas as pd
# from pyspark.sql import SparkSession
import ipaddress
import netaddr

#from cidr_trie import PatriciaTrie
#import cidr_trie.cidr_util
import pytricia

from django_nys_02.settings import DIR_ZMAP_NAME

from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    IpRangeSurvey, CountTract, IpRangePing, 
    MmIpRange, IpSurveyState, IpSurveyCounty,
    IpSurveyTract,
    County, CensusTract)

tmp_zmap_run_dir = os.getenv("ZMAP_RUN_DIRECTORY")
if not tmp_zmap_run_dir:
    zmap_run_dir = "/home/bitnami/run/exec_zmap"
else:
    zmap_run_dir = tmp_zmap_run_dir
# zmap_num_threads = os.getenv("ZMAP_NUM_THREADS")
# zmap_ping_rate = os.getenv("ZMAP_PING_RATE")
# print(f"zmap_run_dir = {zmap_run_dir}, num_threads = {zmap_num_threads}, ping_rate = {zmap_ping_rate}")
print(f"zmap_run_dir = {zmap_run_dir}")
TEMP_DIRECTORY = zmap_run_dir 
FILE_RANGE_IP = "RangeIp.csv"
FILE_WHITELIST = "Whitelist.csv"
FILE_OUTPUT = "ZmapOutput.csv"
FILE_METADATA = "Metadata.csv"
FILE_LOG = "Log.txt"
FILE_DEBUG_ZMAP = "ProcessZmapResults.txt"
FILE_ZMAP_SHELL = "run_zmap.sh"
#FILE_PATRICIA_TRIE = "PatriciaTrie.txt"

HEADER = "range_id,ip_network\n"

PD_CHUNK_SIZE = 10000

# Should rename this.  It doesn't like a Model (but it's Local to here)
class RangeIpCount:
    def __init__(self, db_range_id, ip_network, possible_hosts):
        """
        Docstring here
        """
        self.id = db_range_id
        self.ip_network = ip_network
        self.possible_hosts = possible_hosts
        self.count = 0

    def str(self):
        return f"range[{self.id}] = {self.ip_network}, count = {self.count}"
    
class TrieWrapper:
    def __init__(self):
        """
        Docstring here
        """
        self.dictionary = {}

    def _get_hashed_trie(self, ip_network, create_new=False):
        """
        Docstring here
        """
        octets = ip_network.split('.')
        first_octet = octets[0]
        if not first_octet in self.dictionary:
            if not create_new:
                raise Exception(f"No trie for octet = {first_octet}")
            return_trie = PatriciaTrie()
            self.dictionary[first_octet] = return_trie 
        else:
            return_trie = self.dictionary[first_octet]
        return return_trie

    def insert(self, ip_network, data):
        """
        Docstring here
        """
        trie = self._get_hashed_trie(ip_network, create_new=True)
        trie.insert(ip_network, data)

    def find_all(self, ip_network):
        """
        Docstring here
        """
        trie = self._get_hashed_trie(ip_network)
        return trie.find_all(ip_network)
            
    def traverse(self, ip_network):
        """
        Docstring here
        """
        trie = self._get_hashed_trie(ip_network)
        return trie.traverse(ip_network)

class PingSurveyManager:
    def __init__(self, survey_id, debug, create_new=True, linked_survey_id=None):
        """
        Docstring here
        """
        self._survey_id = survey_id
        self._debug = debug
        if create_new:
            self._create_directory(linked_survey_id)
        else:
            # This is duplicative (with the find() call below)
            survey_dir_name = PingSurveyManager._build_survey_name(survey_id)
            full_path = os.path.join(TEMP_DIRECTORY, DIR_ZMAP_NAME, survey_dir_name)
            # print(f"PSM.__init__(), TEMP_DIR = {str(TEMP_DIRECTORY)}, full_path = {str(full_path)}")
            self.directory = full_path
        # In either init() [create or read existing], we want to configure the files
        self._configure_whitelist_files()

    @staticmethod
    def find(survey_id_string, debug):
        """
        Docstring here
        """
        survey_id = survey_id_string
        return PingSurveyManager._find_survey(survey_id, debug)
        
    @staticmethod
    def _build_survey_name(survey_id) -> str:
        """
        Docstring here
        """
        folder_snapshot = f"Survey_{survey_id:05d}"
        return folder_snapshot

    @staticmethod
    def _find_survey(survey_id, debug):
        """
        Docstring here
        """
        survey_dir_name = PingSurveyManager._build_survey_name(survey_id)
        full_path = os.path.join(TEMP_DIRECTORY, DIR_ZMAP_NAME, survey_dir_name)
        #print(f"PSM._find_survey(), full_path = {str(full_path)}")
        if not os.path.exists(full_path):
            print(f"PingSurveyManager._find_survey(), could not find path: {full_path}")
            return None
        psm = PingSurveyManager(survey_id, debug, create_new=False)
        return psm

    @staticmethod
    def link_survey(survey_id, parent_survey_id):
        """
        Docstring here
        """
        links_created = 0
        parent_psm = PingSurveyManager._find_survey(parent_survey_id, False)
        # print(f"PSM.link_survey(), parent_psm = {parent_psm}")
        if not parent_psm:
            return
        child_psm = PingSurveyManager(survey_id, False, create_new=True, linked_survey_id=parent_survey_id)
        if os.path.exists(child_psm.path_range_ip):
            print(f"PSM.link_survey(), RangeIp path {child_psm.path_range_ip} already exists!")
        else:
            os.link(parent_psm.path_range_ip, child_psm.path_range_ip)
            links_created = links_created + 1
        if os.path.exists(child_psm.path_whitelist):
            print(f"PSM.link_survey(), RangeIp path {child_psm.path_whitelist} already exists!")
        else:
            os.link(parent_psm.path_whitelist, child_psm.path_whitelist)
            links_created = links_created + 1
        # print(f"PSM.link_survey(), created {links_created} links...")

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

    def _create_directory(self, linked_survey_id):
        """
        Docstring here
        """
        # now = datetime.datetime.now()
        # folder_snapshot = now.strftime("%Y%m%d_%H%M%S")
        # folder_snapshot = f"Survey_{self._survey_id:05d}"
        folder_snapshot = PingSurveyManager._build_survey_name(self._survey_id)
        if not TEMP_DIRECTORY:
            print(f"_create_directory(), TEMP_DIRECTORY is not set!")
            return
        if not DIR_ZMAP_NAME:
            print(f"_create_directory(), DIR_ZMAP_NAME is not set!")
            return
        full_path = os.path.join(TEMP_DIRECTORY, DIR_ZMAP_NAME, folder_snapshot)
        # print(f"PSM.create_directory(), directory = {str(full_path)}")
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        elif linked_survey_id:
            print(f"PSM._create_directory(), directory already exists!")
        self.directory = full_path

    def _debug_directory(self, county):
        """
        Docstring here
        """
        print(f"Found debug county = {county.id},{county.county_name}")
        cleaned_name = county.county_name.replace(" ","_")
        directory_name = f"{county.id:04}_{cleaned_name}"
        self._debug_dir = os.path.join(self.directory, directory_name)
        if not os.path.exists(self._debug_dir):
            print(f"_debug_directory(), creating directory: {str(self._debug_dir)}")
            os.makedirs(self._debug_dir)

        whitelist_file = os.path.join(self._debug_dir, FILE_WHITELIST)
        self._debug_writer = open(whitelist_file, "w+")

    def _debug_add_range(self, range1, string1):
        """
        Docstring here
        """
        self._debug_writer.write(string1)

    def _debug_close_files(self):
        """
        Docstring here
        """
        print(f"_debug_close_files()")
        self._debug_writer.close()

    def _traverse_geography(self):
        """
        Docstring here
        """
        debug_county_id = 1175
        self._debug_county = None

        survey = IpRangeSurvey.objects.get(pk=self._survey_id)
        #print(f"PSM._traverse_geography(), survey = {survey}")
        
        selected_survey_states = IpSurveyState.objects.filter(survey_id=self._survey_id)
        num_states = selected_survey_states.count()

        state_abbrevs = [s.us_state.state_abbrev for s in selected_survey_states]
        # debugger.print_array("PSM._traverse_geography(), selected_survey_states:", selected_survey_states)

        if self._debug:
            print(f"PSM._traverse_geography(), survey_id: {self._survey_id}, states = {state_abbrevs}")


        #state_ids = []
        #for survey_state in selected_survey_states :
        #    state_ids.append(survey_state.us_state.id)
        total_ranges = 0
        num_counties = 0
        for survey_state in selected_survey_states :
            county_set = survey_state.us_state.county_set.all()
            num_counties = num_counties + county_set.count()
            for county in county_set:
                survey_county = IpSurveyCounty(survey=survey, county=county)
                survey_county.save()
                if county.id == debug_county_id:
                    self._debug_directory(county)
                    self._debug_county = county
                    add_to_debug = True
                else:
                    add_to_debug = False
                ranges_added = self._county_ranges_whitelist(county, add_to_debug)
                total_ranges = total_ranges + ranges_added

#            state_ids.append(survey_state.us_state.id)

        # debugger.print_array("PSM._traverse_geography(), state_ids:", state_ids)

#        county_ids = []

        # Could also do:
        # counties = state.county_set.all()
        # counties_in_state = County.objects.filter(us_state__id__in=state_ids)
#        total_ranges = 0
#        counties_in_states = County.objects.filter(us_state__id__in=state_ids)
#        for county in counties_in_states:
            # county_ids.append(county.id)
        #print(f"PSM._traverse_geography(), county_ids = {county_ids}")
        # debugger.print_array("PSM._traverse_geography(), county_ids:", county_ids)


        # file_name = debugger.get_file()
        # debugger.close()
        #num_states = len(state_ids)
        #num_counties = len(county_ids)
        # num_tracts = len(tract_ids)
        if self._debug:
            first = "PSM._traverse_geography(), created (s/c/r) = "
            second = f"{num_states}/{num_counties}/{total_ranges:,}"
            print(first + second)
        if self._debug_county:
            self._debug_close_files()
        return num_states, num_counties, total_ranges

    def _tract_ranges_whitelist(self, tract, add_to_debug):
        """
        Docstring here
        """
        # Use the set() notation
        ip_ranges = tract.mmiprange_set.all()
        # print(f"_t_r_w(), tract(county) = {tract}, num_ranges = {ip_ranges.count()}")
        for range1 in ip_ranges:
            string1 = f"{range1.id},{range1.ip_network}\n"
            self.writer_range_ip.write(string1)
            whitelist_string = f"{range1.ip_network}\n"
            self.writer_whitelist.write(whitelist_string)
            if add_to_debug:
                self._debug_add_range(range1, whitelist_string)
        ranges_added = ip_ranges.count()
        return ranges_added

    # Exactly the same (as above), but we change the names to start to generalize
    def _county_ranges_whitelist(self, county, add_to_debug):
        """
        Docstring here
        """
        return self._tract_ranges_whitelist(county, add_to_debug)

    # Return the number of ranges
    def _configure_whitelist_files(self):
        self.path_range_ip = os.path.join(self.directory, FILE_RANGE_IP)
        """
        Docstring here
        """
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
        """
        Docstring here
        """
        # range_ip is how we get back to the databaes (ip_range_id (in the database), to network).
        self.writer_range_ip = open(self.path_range_ip, "w+")
        self.writer_range_ip.write(HEADER)
        self.writer_whitelist = open(self.path_whitelist, "w+")
        self.writer_log = open(self.path_log, "w+")

    def build_whitelist(self):
        """
        Docstring here
        """
        self._create_writers()
        # num_states, num_counties, num_tracts, num_ranges = self._traverse_geography()
        num_states, num_counties, num_ranges = self._traverse_geography()
        return num_states, num_counties, num_ranges

    def unused_add(self, index, range_id, ip_network):
        if index == 0:
            self.writer_range_ip.write(HEADER)
        string1 = f"{range_id},{ip_network}\n"
        self.writer_range_ip.write(string1)
        self.writer_whitelist.write(f"{ip_network}\n")

    def get_zmap_files(self):
        """
        Docstring here
        """
        return self.directory, self.path_whitelist, self.path_output, self.path_metadata, self.path_log 

    def _calculate_possible(self, cidr):
        """
        Docstring here
        """
        ip_network = ipaddress.ip_network(cidr)
        return 1 << (ip_network.max_prefixlen - ip_network.prefixlen)

    # Build a radix tree of the ip address
    def _build_radix_tree(self):
        """
        Docstring here
        """
        self.pyt = pytricia.PyTricia()
        df = self.df_ranges = pd.read_csv(self.path_range_ip)
        column_names = df.columns.tolist()
        for index, row in df.iterrows():
            range_id = row['range_id']
            ip_network = row['ip_network']
            possible_hosts = self._calculate_possible(ip_network)
            # Hang a counter on the tree
            range_ip = RangeIpCount(range_id, ip_network, possible_hosts)
            self.pyt.insert(ip_network, range_ip)

    def debug_matches(self, ip_network):
        """
        Docstring here
        """
        print(f"_debug_matches(), calling traverse on {ip_network}")
        index = 0
        # for node in self.trie_wrapper.traverse(ip_network):
        for node in self.pyt.traverse(ip_network):
            print(f"_debug_matches(), node[{index} = {node}")
            index = index + 1

    def _match_zmap_replies(self):
        """
        Docstring here
        """
        index_chunk = 0
        for chunk in pd.read_csv(self.path_output, chunksize=PD_CHUNK_SIZE):
            column_names = chunk.columns.tolist()
            for index, row in chunk.iterrows():
                saddr = row['saddr']
                timestamp = row['timestamp-ts']
                # self._writer_cidr_trie.write(f"Trie_lookup: {saddr}\n")
                range_counter = self.pyt.get(saddr)
                if not range_counter:
                    first = "Ping._match_zmap_replies(), could not find range counter for: "
                    second = f"{saddr}"
                    self.file_debugger.print_error(first + second, error=True)
                else:
                    range_counter.count = range_counter.count + 1
            index_chunk = index_chunk + 1 
        #print(f"_match_zmap_replies(), debug_file {FILE_PATRICIA_TRIE}")

    def _save_to_db(self, survey):
        """
        Docstring here
        """
        # print(f"_save_to_db(), size (of tree): {self.trie.size}")
        # Iterate the entire tree
        index = 0

        # Walk through our dataframe again
        ranges_updated = hosts_pinged = hosts_responded = 0
        for index, row in self.df_ranges.iterrows():
            range_id = row['range_id']
            ip_network = row['ip_network']
            range_counter = self.pyt.get(ip_network)
            count = range_counter.count
            if count > 0:
                # Pull up the original range object, so we can get the database reference
                ip_range = MmIpRange.objects.get(pk=range_counter.id)
                possible_hosts = range_counter.possible_hosts
                range_ping = IpRangePing(ip_survey=survey,
                    ip_range=ip_range,
                    hosts_pinged=possible_hosts,
                    hosts_responded=count,
                    time_pinged=timezone.now())
                range_ping.save()
                ranges_updated = ranges_updated + 1
                hosts_pinged = hosts_pinged + possible_hosts
                hosts_responded = hosts_responded + count
        # print(f"_save_to_db(), saved {saved_to_db} objects to database")
        #self._writer_cidr_trie.close()
        return ranges_updated, hosts_responded, hosts_pinged

    # Returns the number of pings (hosts) saved to the database (count > 0)
    def process_results(self, survey):
        """
        Docstring here
        """
        self.file_debugger = self.FileDebugger(self.directory, "UnusedName")
        #self.trie_wrapper = TrieWrapper()
        self._unmatched_list = []
        self._build_radix_tree()
        self._match_zmap_replies()
        self.file_debugger.close()
        ranges_updated, hosts_responded, hosts_pinged = self._save_to_db(survey)
        return ranges_updated, hosts_responded, hosts_pinged
        
    def close(self):
        """
        Docstring here
        """
        if self.writer_range_ip:
            self.writer_range_ip.close()

        if self.writer_whitelist:
            self.writer_whitelist.close()

        if self.writer_log:
            self.writer_log.close()

    # Embedded class: PingSurveyManager.FileDebugger
    class FileDebugger:
        def __init__(self, directory, name):
            """
            Docstring here
            """
            self._error_count = 0
            self._full_path = os.path.join(directory, FILE_DEBUG_ZMAP)
            self._writer = open(self._full_path, "w+")

        def close(self):
            """
            Docstring here
            """
            if self._error_count > 0:
                self._writer.write(f"FileDebugger.close(), {self._error_count} errors\n")
            else:
                self._writer.write(f"FileDebugger.close(), matched all replies\n")
            self._writer.close()

        def get_file(self):
            """
            Docstring here
            """
            return self._full_path

        def print_array_line(self, sub_array):
            """
            Docstring here
            """
            sub_array_strings = map(str, sub_array)
            array_string = ", ".join(sub_array_strings)
            self._writer.write(array_string + "\n")

        def print_array(self, description, array_output):
            """
            Docstring here
            """
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
                self.print_array_line(sub_array)
                # Print subarray here
                index = end
                array_len = array_len - sub_array_len

        def print_error(self, string1, error=False):
            """
            Docstring here
            """
            self._writer.write(string1+ "\n")
            if error:
                self._error_count = self._error_count + 1

#        tract_ids = []
#        tracts_in_counties = CensusTract.objects.filter(county__id__in=county_ids)
#        for tract in tracts_in_counties:
#            tract_ids.append(tract.id)
#            if tract.county == self._debug_county:
#                # self._debug_tracts.append(tract.id)
#                add_to_debug = True
#            else:
#                add_to_debug = False
#            survey_tract = IpSurveyTract(survey=survey, tract=tract)
#            survey_tract.save()
#            ranges_added = self._tract_ranges_whitelist(tract, add_to_debug)
#            total_ranges = total_ranges + ranges_added
#        # debugger.print_array("PSM._traverse_geography(), tract_ids:", tract_ids)
