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
from FileSystem.FSUtils.fshelper import FSHelper
from FileSystem.FSUtils.fshelper import ScanType
import sys
import os
import base64

'''
Answer File Example- 
    "62619": {
                                "AgentName": "Windows File System",
                                "ClientName": "",
                                "StoragePolicyName": "",
                                "TestPath": "<path>",
                                "MAMachineName": "",
                                "ImpersonateUser": "<user>",
                                "ImpersonatePassword": "<pas>>",
                                "DataAccessNodes": "",
                                "NetworkSharePath" : "<path>",
                                "Username": "<user>",
                                "Password": "<path>",
                                "Hostname": "<host>"
                },
'''
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

    def get_base64_string(self, string):
        return base64.b64encode(string.encode("ascii")).decode("ascii")

    def getListOfFiles(self, dirName):
        # create a list of file and sub directories
        # names in the given directory
        listOfFile = os.listdir(dirName)
        allFiles = list()
        # Iterate over all the entries
        for entry in listOfFile:
            # Create full path
            fullPath = os.path.join(dirName, entry)
            # If entry is a directory then get the list of files in this directory
            if os.path.isdir(fullPath):
                allFiles = allFiles + self.getListOfFiles(fullPath)
            else:
                allFiles.append(fullPath)

        return allFiles
    def setup(self):
        """Setup function of this test case"""
        self.helper = FSHelper(self)
        self.helper.populate_tc_inputs(self, mandatory=False)
        self.ma_machine_name = self.tcinputs.get("MAMachineName", None)
        self.backupset_name = "backupset_" + str(self.id)
        self.subclient_name = "subclient_" + str(self.id)

        data_readers = int(self.tcinputs.get("DataReaders", 3))
        file_size_mb = int(self.tcinputs.get("FileSizeMB", 1))
        number_of_files = int(self.tcinputs.get("NumberOfFiles", 1000))

        self.log.info("Initializing base_folder_path")
        self.base_folder_path = self.client_machine.join_path(self.test_path, str(self.helper.testcase.id))  # DHI
        self.origin_folder_path = self.client_machine.join_path(self.base_folder_path, 'origin')  # DHI

        if self.base_folder_path.startswith("\\\\"):
            self.is_nas_turbo_type = True

        self.cl_machine = Machine(self.tcinputs.get("Hostname"),
                             username=self.tcinputs.get("Username"),
                             password=self.tcinputs.get("Password"))

        if self.cl_machine.check_directory_exists(self.base_folder_path):
            self.log.info("Removing subclient content %s", self.base_folder_path)
        self.cl_machine.clear_folder_content(folder_path=self.base_folder_path)
        self.cl_machine.remove_directory(self.base_folder_path)

        self.cl_machine.create_directory(self.base_folder_path, force_create=True)
        self.cl_machine.generate_test_data(file_path=self.origin_folder_path,
                                      files=number_of_files, dirs=1,
                                      file_size=1024 * file_size_mb, slinks=False,
                                      hlinks=False, sparse=False, zero_size_file=False,
                                      username=self.tcinputs.get("ImpersonateUser"),
                                      password=self.tcinputs.get("ImpersonatePassword"))

        self.log.info("Test Data generated.")

        # Create Backupset
        self.helper.create_backupset(name="newtestbackupset62619",
                                     is_nas_turbo_backupset=self.is_nas_turbo_type, delete=True)

        # Create Subclient
        self.helper.create_subclient(name="newtestsubclient", data_readers=data_readers,
                                     storage_policy=self.storage_policy, allow_multiple_readers=True,
                                     content=[self.base_folder_path],
                                     data_access_nodes=self.data_access_nodes)

        self.log.info("Subclient Created.")

        self.log.info("Subclient: {}".format(self.helper.testcase.subclient))
        self.log.info("ImpersonateUser: {}".format(self.tcinputs.get("ImpersonateUser")))
        self.log.info("ImpersonatePassword: {}".format(self.tcinputs.get("ImpersonatePassword")))

        if self.is_nas_turbo_type:
            update_properties = self.helper.testcase.subclient.properties
        self.log.info("Original SC Properties: {}".format(self.helper.testcase.subclient.properties))
        update_properties['impersonateUser']['password'] = self.get_base64_string(
            self.tcinputs.get("ImpersonatePassword")
        )
        update_properties['impersonateUser']['userName'] = self.tcinputs.get("ImpersonateUser")
        self.helper.testcase.subclient.update_properties(update_properties)
        self.log.info("Update Properties: {}".format(update_properties))

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

    def verify_classic_scan(self, job):
        logs = self.client_machine.get_logs_for_job_from_file(job_id=job.job_id,
                                                              log_file_name = "FileScan.log",
                                                              search_term="CumulativeScanModeAndReason=CLASSIC")
        if(logs):
            return True
        return False

    def maxdiff(self, A):
        diff= -sys.maxsize
        n=len(A)
        if(n==0):
            return diff
        for i in range(n-1):
            for j in range(i+1,n):
                if(A[j]>A[i]):
                    diff=max(diff,A[j])
        return diff

    def verify_backup_win_nas(self, job):

        if (self.verify_classic_scan(job=job[0]) == True):
            self.log.info("ScanType fell through to Classic")

        job_info = job[0].details['jobDetail']['detailInfo']
        num_streams = job_info['numOfStreams']
        back_type = job[0].backup_level
        self.username = self.tcinputs.get("ImpersonateUser")
        self.password = self.tcinputs.get("ImpersonatePassword")
        if(back_type=="Full"):
            items3 = self.getListOfFiles(self.base_folder_path)
        if(back_type=="Incremental"):
            items3 = self.getListOfFiles(self.inc_folder_path)

        '''items = self.client_machine.get_items_list(data_path=self.origin_folder_path)'''
        self.danode = self.tcinputs.get("DataAccessNodes")
        self.mastern = self.commcell.clients.get(self.danode)
        cvf_path = self.client_machine.join_path(
            self.mastern.job_results_directory,
            "CV_JobResults\iDataAgent\FileSystemAgent", "2",
            self.subclient.subclient_id)

        job_files = self.client_machine.get_items_list(data_path=cvf_path)
        col = []
        if(back_type=="Full"):
            coltype="NumColTot"
        if(back_type=="Incremental"):
            coltype="NumColInc"
        for file in job_files:
            # print(file)
            if (coltype not in file):
                continue
            else:
                col.append(file)
        match = []
        leng = []
        for i in range(len(col)):
            entries = self.client_machine.read_file(cvf_path + "\\" + coltype + str(i + 1) + ".cvf")
            match = match + re.findall(r"\?\?\?(.*?)\|<FILE>", entries)
            # match = match + re.findall(r"(?<=\*\?\?).*(?=\|\<FILE\>)", entries)
            leng.append(len(re.findall(r"\?\?\?(.*?)\|<FILE>", entries)))
            fol = re.findall(r"\?\?\?(.*?)\|<DIR>", entries)
            # fol = re.findall(r"(?<=\*\?\?).*(?=\|\<DIR\>)", entries)
            for f in range(len(fol)):
                fol[f] = fol[f][:-1]
            match = match + fol
        for m in range(len(match)):
            match[m] = match[m][7:]
            match[m] = "\\\\" + match[m]
        check = 0

        for item in items3:
            if (item not in match):
                check = 1

        if (check == 1):
            self.log.error("Failed to validate collect files")
            raise Exception("Failed to validate collect files")
        else:
            self.log.info("Validation successful")
        if (len(col) == num_streams * 2 and self.maxdiff(leng) < 3):
            self.log.info("Splitting of collect files successful")
        else:
            self.log.error("Splitting unsuccessful")
            raise Exception("Splitting unsuccessful")

    def run(self):
        """Run function of this test case"""
        try:
            self.helper.populate_tc_inputs(self)

            self.update_reg_keys1()
            # performing full backup
            self.log.info("Running Full backup job on subclient %s", self.subclient.subclient_name)
            self.helper.update_subclient(scan_type=ScanType.OPTIMIZED, allow_multiple_readers=True, data_readers=2)
            job1 = self.helper.run_backup(backup_level="Full")
            self.verify_backup_win_nas(job1)

            self.log.info("Adding new files")
            self.inc_folder_path = self.client_machine.join_path(self.base_folder_path, 'inc')
            self.cl_machine.generate_test_data(file_path=self.inc_folder_path,
                                               files=200, dirs=1,
                                               file_size=1024, slinks=False,
                                               hlinks=False, sparse=False, zero_size_file=False,
                                               username=self.tcinputs.get("ImpersonateUser"),
                                               password=self.tcinputs.get("ImpersonatePassword"))
            job2 = self.helper.run_backup(backup_level="Incremental")

            self.verify_backup_win_nas(job2)
            self.log.info("check")

            self.restore_path = self.base_folder_path.replace("\\\\", "\\UNC-NT_")
            self.log.info("Deleting subclient content")
            # self.cl_machine.remove_directory(self.origin_folder_path)
            items3 = self.getListOfFiles(self.base_folder_path)
            self.cl_machine.clear_folder_content(folder_path=self.base_folder_path)
            items4 = self.getListOfFiles(self.base_folder_path)
            if(len(items4)==0):
                self.log.info("Successfully Deleted")
            else:
                self.log.error("Not Deleted")
            self.helper.restore_in_place(proxy_client=self.danode, paths=[self.restore_path])
            items5 = self.getListOfFiles(self.base_folder_path)
            self.update_reg_keys2()
            check=0
            for item in items3:
                if item not in items5:
                    check=1
            if(check==1):
                self.log.error("Restore in place was not successful")
                raise Exception("Restore in place was not successful")
            else:
                self.log.info("Restore in place was successful")
            self.res_dest = self.tcinputs.get("RestoreDestination")
            self.client_machine.create_directory(directory_name=self.res_dest, force_create=True)
            self.helper.restore_out_of_place(proxy_client=self.danode, client=self.danode, paths=[self.restore_path],
                                             destination_path=self.res_dest)
            #items6 is the list of files and folders in the out of place restore destination
            #items3 is the list of files and folders in actual subclient content
            items6 = self.client_machine.get_items_list(data_path=self.res_dest+'\\62619')
            items6 = [x.replace(self.res_dest+'\\62619','') for x in items6]
            items3 = [x.replace(self.base_folder_path, '') for x in items3]
            check=0
            for item in items3:
                if item not in items6:
                    check=1
            if(check==1):
                self.log.error("Restore out of place was not successful")
                raise Exception("Restore out of place was not successful")
            else:
                self.log.info("Restore out of place was successful")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
