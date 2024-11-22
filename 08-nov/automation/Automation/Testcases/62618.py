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

    update_reg_keys() --  updates required  registry keys

    verify_logs() --  verifies logs to conclude

"""

import re
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.winfshelper import WinFSHelper
from FileSystem.FSUtils.fs_constants import WIN_DATA_CLASSIFIER_CONFIG_REGKEY
from FileSystem.FSUtils.fshelper import ScanType
import sys


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
        self.name = "Checking subclient creation options"
        self.client_machine = None
        self.helper = None
        self.tcinputs = {
            "TestPath": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.helper = WinFSHelper(self)
        self.client_machine = Machine(self.client)

    def update_reg_keys1(self):
        self.client_machine.create_registry(key="FileSystemAgent",
                                                value="bEnableAutoSubclientDirCleanup",
                                                data=0,
                                                reg_type="DWord")

    def update_reg_keys2(self):
        self.client_machine.create_registry(key="FileSystemAgent",
                                                value="bEnableAutoSubclientDirCleanup",
                                                data=1,
                                                reg_type="DWord")
    def verify_scan(self, job, scan):
        logs = self.client_machine.get_logs_for_job_from_file(job_id=job.job_id,
                                                              log_file_name="FileScan.log",
                                                              search_term="ScanType")
        result = re.search(r"ScanType=\[[A-Z]*\]", logs)
        print(result)
        res = result.group(0)[10:12]
        if (res == scan):
            return True
        return False

    def maxdiff(self, A):
        diff = -sys.maxsize
        n = len(A)
        if(n == 0):
            return diff
        for i in range(n-1):
            for j in range(i+1,n):
                if(A[j] > A[i]):
                    diff = max(diff,A[j])
        return diff

    def run(self):
        """Run function of this test case"""
        try:

            self.helper.populate_tc_inputs(self)
            # backup set
            backupset_name = "backupset_" + self.id
            self.helper.create_backupset(backupset_name, delete=self.cleanup_run)
            self.backupset_name = backupset_name

            # creating data
            self.client_machine.generate_test_data(self.test_path, dirs=5, files=10)
            self.log.info("Generating data")
            self.update_reg_keys1()
            filterc = ["E:\\10000\\dir5"]

            # setting subclient content
            subclient_content = [self.test_path]
            self.helper.create_subclient(name="subclient62618",
                                         storage_policy=self.storage_policy,
                                         content=subclient_content,
                                         scan_type=ScanType.RECURSIVE,
                                         allow_multiple_readers=True,
                                         data_readers=1,
                                         filter_content=filterc)
                             

            self.helper.update_subclient(scan_type=ScanType.RECURSIVE,
                                         allow_multiple_readers=True,
                                         data_readers=1,
                                         filter_content=filterc)

            # performing full backup
            self.log.info("Running Full backup job on subclient %s", self.subclient.subclient_name)
            job = self.helper.run_backup(backup_level="Full")
            if (self.verify_scan(job=job[0], scan="FF") == False):
                self.log.error("Wrong scan type")
            else:
                self.log.info("Correct scan type")

            job_det = job[0].details['jobDetail']['detailInfo']
            job_size_media = job_det['sizeOfMediaOnDisk']
            stream_count = job_det['numOfStreams']
            items = self.client_machine.get_items_list(data_path=self.test_path)


            cvf_path = self.client_machine.join_path(
                self.client.job_results_directory,
                "CV_JobResults\iDataAgent\FileSystemAgent", "2",
                self.subclient.subclient_id)

            job_files = self.client_machine.get_items_list(data_path=cvf_path)
            i=0
            col=[]
            for file in job_files:
                # print(file)
                if("NumColTot" not in file):
                    continue
                else:
                    col.append(file)

            match = []
            leng=[]
            for i in range(len(col)):
                entries = self.client_machine.read_file(cvf_path+"\\NumColTot"+str(i+1)+".cvf")
                match = match + re.findall(r"\?\?\?(.*?)\|<FILE>",entries)
                # match = match + re.findall(r"(?<=\*\?\?).*(?=\|\<FILE\>)", entries)
                leng.append(len(re.findall(r"\?\?\?(.*?)\|<FILE>",entries)))
                fol = re.findall(r"\?\?\?(.*?)\|<DIR>",entries)
                # fol = re.findall(r"(?<=\*\?\?).*(?=\|\<DIR\>)", entries)
                for f in range(len(fol)):
                    fol[f] = fol[f][:-1]
                match = match + fol

            temp = 0
            items2 = []
            for item in items:
                if(filterc[0] in item):
                    continue
                else:
                    items2.append(item)
       
            for item in items2:
                if(item not in match):
                    temp = 1

            if(temp == 1):
                self.log.error("Failed to validate collect files")
                raise Exception("Failed to validate collect files")
            else:
                self.log.info("Validation successful")

            if(len(col)==stream_count*2 and self.maxdiff(leng)<3):
                self.log.info("Splitting of collect files successful")
            else:
                self.log.error("Splitting unsuccessful")
                raise Exception("Splitting unsuccessful")
            self.update_reg_keys2()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
