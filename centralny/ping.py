TEMP_DIRECTORY = "/tmp/exec_zmap/"
FILE_RANGE_IP = "RangeIp.csv"
FILE_WHITELIST = "Whitelist.csv"

HEADER = "range_id, ip_network\n"

class PingSurveyManager:
    def __init__(self):
        self._create_directory()
        self._create_whitelist()

    def _create_directory(self):
        now = datetime.datetime.now()
        folder_snapshot = now.strftime("%Y%m%d_%H%M%S")
        full_path = os.path.join(TEMP_DIRECTORY, folder_snapshot)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        self.directory = full_path

    # Open two files
    def _create_whitelist(self):
        path_range_ip = os.path.join(self.directory, FILE_RANGE_IP)
        self.writer_range_ip = open(path_range_ip, "w+")

        path_whitelist = os.path.join(self.directory, FILE_WHITELIST)
        self.writer_whitelist = open(path_whitelist, "w+")
        
    def add(self, index, range_id, ip_network):
        if index == 0:
            self.writer_range_ip.write(HEADER)
        string1 = f"{range_id}, {ip_network}")
        self.writer_range_ip.write(string1)
        self.writer_whitelist.write("ip_network")

    def close():
        self.writer_range_ip.close()
        self.writer_whitelist.close()
