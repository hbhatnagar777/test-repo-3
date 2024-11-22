# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    get_all_volumes()   --  gets volume drive list for a machine

    remove_volume_guid_reg_key() --  removes all volume guids from Data [Claasification/configuration]

    check_if_threads_disabled() --  checks if monitoring threads are disabled.

"""

import time
import re
from datetime import datetime
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.winfshelper import WinFSHelper
from FileSystem.FSUtils.fs_constants import WIN_DATA_CLASSIFIER_CONFIG_REGKEY
from FileSystem.FSUtils.fshelper import ScanType

"""
Example-
"59161": {
                                "AgentName": "",
                                "ClientName": "",
                                "TestPath": "",
                                "StoragePolicyName": "",
                                "CleanupRun": 								
                },
"""

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Verify ServiceEnabled Reg. Key"
        self.client_machine = None
        self.helper = None
        self.cleanup_run = None
        self.tcinputs = {"TestPath": None, "StoragePolicyName": None}


    def setup(self):
        """Setup function of this test case"""
        self.client_machine = Machine(self.client)
        self.helper = WinFSHelper(self)

    def get_all_volumes(self):
        """
            fetches list of drive letters from client machine

            Return:
                all_volumes (list) -- list of drive letter without colon
        """
        all_volumes = []
        output = self.client_machine.execute_command("Get-Volume")
        f_out = output.formatted_output
        for item in f_out:
            if len(item[0]) == 1:
                all_volumes.append(item[0])

        return all_volumes

    def remove_volume_guid_reg_key(self, drive_volume_list):
        """
            Removes all guid keys under [Data Classification\\Configuration\\] reg key
            Args:
                drive_volume_list(list) - List of drive letters
        """
        for drive_letter in drive_volume_list:
            guid_path = self.client_machine.join_path(WIN_DATA_CLASSIFIER_CONFIG_REGKEY,
                                                      self.helper.get_volume_guid(drive_letter=drive_letter))
            if self.client_machine.check_registry_exists(key=guid_path):
                self.client_machine.remove_registry(key=guid_path)

    @staticmethod
    def check_if_threads_disabled(logs):
        """
            Checks if threads are disabled
            Args:
                logs  (list) - list of log lines

            Return:
                bool -- True if threads disabled/ False if not
        """
        for line in logs:
            if re.search("Monitoring change journals for 0 volumes", line):
                return True

        return False

    def run(self):
        """Run function of this test case"""
        try:
            self.helper.populate_tc_inputs(self)

            # backup set

            backupset_name = "backupset_" + self.id
            self.helper.create_backupset(backupset_name, delete=self.cleanup_run)
            self.backupset_name = backupset_name

            # setting subclient content
            self.subclient_name = "subclient59161"
            subclient_content = [self.test_path]
            self.helper.create_subclient(name="subclient59161",
                                         storage_policy=self.storage_policy,
                                         content=subclient_content,
                                         scan_type=ScanType.OPTIMIZED)
            #creating data
            self.client_machine.generate_test_data(self.test_path, dirs=5, files=10)
            self.log.info("Generating data")
            # performing backup
            self.log.info("Running Incremental backup job on subclient %s", self.subclient_name)
            self.helper.run_backup()

            # updating reg .keys
            self.log.info("Updating ServiceEnabled Registry Key")
            if not self.client_machine.check_registry_exists(key=WIN_DATA_CLASSIFIER_CONFIG_REGKEY,
                                                             value="ServiceEnabled"):
                self.client_machine.create_registry(key=WIN_DATA_CLASSIFIER_CONFIG_REGKEY,
                                                    value="ServiceEnabled",
                                                    data=0,
                                                    reg_type="DWord")
            else:
                self.client_machine.update_registry(key=WIN_DATA_CLASSIFIER_CONFIG_REGKEY,
                                                    value="ServiceEnabled",
                                                    data=0,
                                                    reg_type="DWord")

            # clearing all guids under [Data Classfication\Configuration] reg. key
            all_volumes = self.get_all_volumes()
            self.remove_volume_guid_reg_key(drive_volume_list=all_volumes)

            time_t = datetime.now()
            self.log.info("Waiting 5 minutes for reg. keys to take effect.")
            time.sleep(300)

            # fetching log lines from GXDC log after time_t
            self.log.info("Fetching Logs from [GXDC] log file")
            logs = self.client_machine.get_logs_after_time_t(log_file_name="GXDC.log",
                                                             time_t=time_t,
                                                             search_function="CDataClassifierThread::CheckVolumes")

            self.log.info("Verifying if threads disabled")
            if self.check_if_threads_disabled(logs):
                self.log.info("Monitoring Threads Disabled.")
            else:
                self.log.info("Failed to disable Monitoring Threads")
                raise Exception("Failed to disable Monitoring Threads")

            self.client_machine.remove_registry(key=WIN_DATA_CLASSIFIER_CONFIG_REGKEY,
                                                value="ServiceEnabled")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
