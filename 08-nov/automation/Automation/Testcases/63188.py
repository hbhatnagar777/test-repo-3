# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------

"""
Main file for executing this test case.

TestCase is the only class defined in this file.

TestCase:
    - __init__(): initialize TestCase class
    - setup(): setup function of this test case
    - run(): run function of this test case
    - tear_down(): tear down function of this test case
"""

import os.path
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config
from AutomationUtils import constants
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Basic test case for Sensitive Keywords detection from Commvault Log File"""

    def __init__(self):
        """Initializing the Test case file"""
        super(TestCase, self).__init__()
        self.name = "Sensitive Keywords detection from Commvault Log Files"
        self.tcinputs = {}

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        self.keyspath = self.config_json.sensitivedatapath        
        self.cs_machine = Machine(
            machine_name=self.config_json.Install.commserve_client.machine_host,
            username=self.config_json.Install.commserve_client.machine_username,
            password=self.config_json.Install.commserve_client.machine_password
        )
        self.commserv_client = self.commcell.commserv_client
        self.keywords = []
        with open(self.keyspath, "r") as fileobj:
            self.keywords = fileobj.readlines()

        if len(self.keywords) <= 0:
            self.log.error("No keywords found in the file")
            self.status = constants.FAILED
            raise Exception("No keywords found in the file")

    def run(self):
        """Runs the test case"""
        try:
            display_coll = {}
            collect_dict = {}
            sensitivedata = False
            commserv_client_logs_location = self.commserv_client.log_directory
            paths = self.cs_machine.get_files_in_path(commserv_client_logs_location)
            self.log.info(f"Total number of log files: {len(paths)}")

            for file in paths:
                if file.endswith(".log"):
                    try:
                        self.log.info(f"Processing file: {file}")
                        file_content = self.cs_machine.read_file(file)                        
                        key_dict = {}
                        keywords = []
                        for line in file_content.splitlines():
                            for keyword in self.keywords:
                                if str(line).lower().find(keyword.strip().lower()) >= 0:
                                    key_dict.setdefault(keyword, []).append(line)
                                    keywords.append(keyword)
                                    sensitivedata = True
                        collect_dict.setdefault(file, []).append(key_dict)
                        if len(keywords) > 0:
                            display_coll.setdefault(file, []).append(keywords)
                    except Exception as err:
                        self.log.error(f"Failed to read file {file}")
                        self.log.error(f"Error {err}")
                        continue

            try:
                with open(os.path.join(os.path.dirname(self.keyspath), "Sensitivedata_results.txt"), "w",
                          encoding='utf-8', errors='ignore') as fileobj:
                    for key, values in display_coll.items():
                        flag = False
                        for value in values:
                            if value:
                                if not flag:
                                    fileobj.write("################" + str(key) + "################")
                                    fileobj.write(2 * "\n")
                                    flag = True
                                fileobj.write(str((set(value))))
                                fileobj.write(2 * "\n")
            except Exception as err:
                self.log.error("Failed to write to file")

            try:
                with open(os.path.join(os.path.dirname(self.keyspath), "Sensitivedata_fulldetails.txt"), "w",
                          encoding='utf-8', errors='ignore') as fileobj:
                    for key, values in collect_dict.items():
                        fileobj.write("################" + str(key) + "################")
                        fileobj.write(2 * "\n")
                        for value in values:
                            for newk, newv in value.items():
                                fileobj.write("\t\t$$$" + str(newk) + "$$$")
                                fileobj.write("\n")
                                count = 0
                                for newline in newv:
                                    fileobj.write(str(newline))
                                    fileobj.write("\n")
                                    count += 1
                                    if count >= 5:
                                        break
            except Exception as err:
                self.log.error("Failed to write to file")

            if sensitivedata:
                self.result_string = "Sensitive data found in logs"
                self.log.error(self.result_string)
                self.status = constants.FAILED
            else:
                self.result_string = "No sensitive data found in logs"
                self.log.info(self.result_string)
                self.status = constants.PASSED
        except Exception as exp:
            self.log.error('Failed with error: {0} exp '.format(str(exp)))
            self.result_string = str(exp)
            self.status = constants.FAILED
