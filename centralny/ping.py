import os
import datetime

TEMP_DIRECTORY = "/tmp/exec_zmap/"
FILE_RANGE_IP = "RangeIp.csv"
FILE_WHITELIST = "Whitelist.csv"
FILE_OUTPUT = "ZmapOutput.csv"
FILE_METADATA = "Metadata.csv"
FILE_LOG = "Log.txt"

HEADER = "range_id, ip_network\n"

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
            self.writer_range_ip = open(path_range_ip, "w+")
            self.writer_whitelist = open(path_whitelist, "w+")

    def _load_latest():
        most_recent_dir = None
        with os.scandir(TEMP_DIRECTORY) as entries:
            for entry in entries:
                if entry.is_file():
                    continue
                if not most_recent_dir :
                    most_recent_dir = entry
                elif entry.name > most_recent_dir.name:
                    most_recent_dir = entry
        if not most_recent_dir
            raise Exception(f"_load_latest(), could not find a data directory in: {TEMP_DIRECTORY}")
        print(f"_load_latest(), using most_recent_dir {most_recent_dir.name}")
        self.directory = most_recent_dir.path
        
    def add(self, index, range_id, ip_network):
        if index == 0:
            self.writer_range_ip.write(HEADER)
        string1 = f"{range_id}, {ip_network}\n"
        self.writer_range_ip.write(string1)
        self.writer_whitelist.write(f"{ip_network}\n")

    def get_zmap_files(self):
        return self.path_whitelist, self.path_output, self.path_metadata, self.path_log 

    def close(self):
        self.writer_range_ip.close()
        self.writer_whitelist.close()
