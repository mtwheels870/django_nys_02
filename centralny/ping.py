import os
import datetime

import pandas as pd
import ip_network
import netaddr

from cidr_trie import PatriciaTrie
import cidr_trie.cidr_util

from django.utils import timezone

from .models import (
    IpRangeSurvey, CountRangeTract, IpRangePing, DeIpRange, WorkerLock,
    MmIpRange)

TEMP_DIRECTORY = "/tmp/exec_zmap/"
FILE_RANGE_IP = "RangeIp.csv"
FILE_WHITELIST = "Whitelist.csv"
FILE_OUTPUT = "ZmapOutput.csv"
FILE_METADATA = "Metadata.csv"
FILE_LOG = "Log.txt"

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
    def __init__(self, create_new=True):
        if create_new:
            self._create_directory()
            self._create_whitelist()
        else:
            self._load_latest()
            self._create_whitelist(write_mode=False)

    def _create_directory(self):
        now = datetime.datetime.now()
        folder_snapshot = now.strftime("%Y%m%d_%H%M%S")
        full_path = os.path.join(TEMP_DIRECTORY, folder_snapshot)
        print(f"PSM.create_directory(), directory = {str(full_path)}")
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        self.directory = full_path

    # Open two files
    def _create_whitelist(self, write_mode=True):
        self.path_range_ip = os.path.join(self.directory, FILE_RANGE_IP)
        self.path_whitelist = os.path.join(self.directory, FILE_WHITELIST)
        self.path_output = os.path.join(self.directory, FILE_OUTPUT)
        self.path_metadata = os.path.join(self.directory, FILE_METADATA)
        self.path_log = os.path.join(self.directory, FILE_LOG)
        if write_mode:
            self.writer_range_ip = open(self.path_range_ip, "w+")
            self.writer_whitelist = open(self.path_whitelist, "w+")
            self.writer_log = open(self.path_log, "w+")

    def _load_latest(self):
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
        
    def add(self, index, range_id, ip_network):
        if index == 0:
            self.writer_range_ip.write(HEADER)
        string1 = f"{range_id},{ip_network}\n"
        self.writer_range_ip.write(string1)
        self.writer_whitelist.write(f"{ip_network}\n")

    def get_zmap_files(self):
        return self.path_whitelist, self.path_output, self.path_metadata, self.path_log 

    def _calculate_possible(self, cidr):
        ip_network = ipaddress.ip_network(cidr)
        return 1 << (ip_network.max_prefixlen - prefixlen)

    # Build a radix tree of the ip address
    def _build_radix_tree(self):
        self.trie = PatriciaTrie()
        df = self.df_ranges = pd.read_csv(self.path_range_ip)
        column_names = df.columns.tolist()
        print(f"_build_radix_tree(), num_rows = {df.shape[0]}, columns = {column_names}")
        for index, row in df.iterrows():
            range_id = row['range_id']
            ip_network = row['ip_network']
            print(f"RangeIp({range_id},{ip_network})")
            possible_hosts = self._calculate_possible(ip_network)
            # Hang a counter on the tree
            range_ip = RangeIpCount(range_id, ip_network, possible_hosts)
            self.trie.insert(ip_network, range_ip)

    def _match_zmap_replies(self):
        df = pd.read_csv(self.path_output)
        column_names = df.columns.tolist()
        print(f"_match_zmap_replies(), num_rows = {df.shape[0]}, column_names = {column_names}")
        for index, row in df.iterrows():
            saddr = row['saddr']
            timestamp = row['timestamp-ts']
            results = self.trie.find_all(saddr)
            num_results = len(results)
            if index < 20:
                print(f"[{index}], saddr = {saddr}, timestamp = {timestamp}, results = {results}")
                print(f"        results = {results}")
            if num_results == 0:
                print(f"_match_zmap_replies(), no Trie results for {saddr}!")
            elif num_results > 1:
                print(f"_match_zmap_replies(), multiple Trie results for {saddr}!")
            else:
                address = results[0][0]
                counter = results[0][1]
                if index < 20:
                    print(f"    found ONE, address = {address}, counter = {counter}")
                counter.count = counter.count + 1

    def _save_to_db(self, survey):
        print(f"_save_to_db(), size (of tree): {self.trie.size}")
        # Iterate the entire tree
        index = 0

        # Walk through our dataframe again
        for index, row in self.df_ranges.iterrows():
            range_id = row['range_id']
            ip_network = row['ip_network']
            
            print(f"_save_to_db(), looking up [{range_id}], ip_network {ip_network}")
            network_parts = cidr_trie.cidr_util.cidr_atoi(ip_network) 
            target_mask = network_parts[1]
            # Now, look up each network in our trie
            index = 0
            saved_to_db = 0
            for node in self.trie.traverse(ip_network):
                # print(f"_save_to_db(), traverse[{index}] = ip: x{node.ip:08X}, bit = {node.bit}, masks = {node.masks}")
                ip_string = cidr_trie.cidr_util.ip_itoa(node.ip, False)
                print(f"_save_to_db(), traverse[{index}] = ip: {ip_string}, bit = {node.bit}, masks = {node.masks}")
                if target_mask in node.masks:
                    ip_range_counter = node.masks[target_mask]
                    count = ip_range_counter.count
                    if count != 0:
                        ip_range = MmIpRange.objects.get(pk=ip_range_counter.range_id)
                        possible_hosts = ip_range_counter.possible_hosts
                        range_ping = IpRangePing(ip_survey=survey,ip_range=ip_range,
                            num_ranges_pinged=possible_hosts
                            num_ranges_responded=count,
                            time_pinged=timezone.now())
                        range_ping.save()
                        saved_to_db = saved_to_db + 1
                    break
                #ip_range = node.masks
                #print(f"           count = {ip_range.count}")
                index = index + 1
            print(f"_save_to_db(), saved {saved_to_db} objects to database")

    def process_results(self, survey):
        self._unmatched_list = []
        self._build_radix_tree()
        self._match_zmap_replies()
        self._save_to_db(survey)
        
    def close(self):
        self.writer_range_ip.close()
        self.writer_whitelist.close()
        self.writer_log.close()
