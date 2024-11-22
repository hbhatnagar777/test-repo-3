# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase to perform DV2 Operation.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    _cleanup()                  --  Cleanup the entities created

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  teardown function of this test case

Sample Input:
"54749": {
            "ClientName": "skclient",
            "AgentName": "File System",
            "MediaAgentName": "skma",
    }
"""

import re

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import (DedupeHelper, MMHelper)


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "MA Acceptance - DV2"
        self.disk_library_name = None
        self.storage_policy_name = None
        self.storage_policy_copy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mountpath = None
        self.partition_path = None
        self.content_path = None
        self.client_machine = None
        self.ma_machine = None
        self.lib_obj = None
        self.common_util = None
        self.mmhelper = None
        self.dedupe_helper = None

    def _cleanup(self):
        """Cleanup the entities created"""

        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            # Delete backupset
            self.log.info("Deleting BackupSet: %s if exists", self.backupset_name)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Deleted BackupSet: %s", self.backupset_name)

            # Delete Storage Policy
            self.log.info("Deleting Storage Policy: %s if exists", self.storage_policy_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info("Deleted Storage Policy: %s", self.storage_policy_name)

            # Delete Library
            self.log.info("Deleting library: %s if exists", self.disk_library_name)
            if self.commcell.disk_libraries.has_library(self.disk_library_name):
                self.commcell.disk_libraries.delete(self.disk_library_name)
                self.log.info("Deleted library: %s", self.disk_library_name)

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception("Error encountered during cleanup: {0}".format(str(exp)))

        self.log.info("********************** CLEANUP COMPLETED *************************")

    def setup(self):
        """Setup function of this test case"""

        options_selector = OptionsSelector(self.commcell)
        timestamp_suffix = options_selector.get_custom_str()
        self.disk_library_name = '%s_disklib' % str(self.id)
        self.storage_policy_name = '%s_policy' % str(self.id)
        self.backupset_name = '%s_BS' % str(self.id)
        self.subclient_name = '%s_SC' % str(self.id)

        self.client_machine = options_selector.get_machine_object(self.tcinputs['ClientName'])
        self.ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgentName'])

        self.dedupe_helper = DedupeHelper(self)
        self.mmhelper = MMHelper(self)
        self.common_util = CommonUtils(self)

        self._cleanup()

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(self.client_machine, size=30 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating data")
        self.log.info('selected drive: %s', client_drive)

        # To select drive with space available in Media agent machine
        self.log.info('Selecting drive in the Media agent machine based on space available')
        ma_drive = options_selector.get_drive(self.ma_machine, size=30 * 1024)
        if ma_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', ma_drive)

        self.mountpath = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP')

        self.partition_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'DDB_%s' %
                                                        timestamp_suffix)

        self.content_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Testdata')
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)

    def run(self):
        """Run function of this test case"""

        try:
            self.lib_obj = self.mmhelper.configure_disk_library(self.disk_library_name, self.tcinputs['MediaAgentName'],
                                                                self.mountpath)

            self.dedupe_helper.configure_dedupe_storage_policy(self.storage_policy_name, self.disk_library_name,
                                                               self.tcinputs['MediaAgentName'], self.partition_path)
            self.storage_policy_copy_name = "Primary"

            self.mmhelper.configure_backupset(self.backupset_name, self.agent)
            sc_obj = self.mmhelper.configure_subclient(self.backupset_name, self.subclient_name,
                                                       self.storage_policy_name, self.content_path, self.agent)

            # Allow multiple data readers to subclient
            self.log.info("Setting Data Readers=4 on Subclient")
            sc_obj.data_readers = 4
            sc_obj.allow_multiple_readers = True

            for i in range(0, 5):
                # Create unique content
                self.log.info("Generating Data at %s", self.content_path)
                if not self.mmhelper.create_uncompressable_data(self.client_machine, self.content_path, 0.1, 10):
                    self.log.error("unable to Generate Data at %s", self.content_path)
                    raise Exception("unable to Generate Data at {0}".format(self.content_path))
                self.log.info("Generated Data at %s", self.content_path)
                self.common_util.subclient_backup(sc_obj, "full")

            self.log.info("Running DV2 job on %s", self.storage_policy_name)
            storage_policy = self.commcell.storage_policies.get(self.storage_policy_name)
            job = storage_policy.run_ddb_verification(self.storage_policy_copy_name, 'Full', 'DDB_VERIFICATION')
            self.log.info("DV2 job: %s", str(job.job_id))
            if not job.wait_for_completion():
                raise Exception("Failed to run DV2 Job: {0}".format(job.delay_reason))

            # listing all the datamovers MAs initiated
            log_file = r'AuxCopyMgr.log'
            log_line = r'Started AuxCopy process on mediaAgent'

            (matched_line, matched_string) = self.dedupe_helper.parse_log(self.commcell.commserv_name, log_file,
                                                                          log_line, jobid=job.job_id)

            if matched_line is None:
                self.log.error("Failed to list datamover MAs from AuxCopyMgr log")
                raise Exception("Failed to list datamover MAs from AuxCopyMgr log")

            malist = []
            for line in matched_line:
                self.log.info(line)
                x = re.match(r'[^[]*\[([^]]*)\]', line).groups()[0]
                malist += [x]
            self.log.info(malist)
            chunkinfo = []
            mpid_list = []
            volid_list = []
            chunkid_list = []

            # checking if the mountpaths are local to MA
            for ma in malist:

                # collecting all the chunks verified by each MA
                log_file = r'DataVerf.log'
                log_line = r'Going to validate Sfile for chnk'

                (matched_line, matched_string) = self.dedupe_helper.parse_log(ma, log_file, log_line, jobid=job.job_id)

                if matched_line is None:
                    self.log.error("Failed to collecting all the chunks verified by MA: %s from DataVerf log", ma)
                    raise Exception("Failed to collecting all the chunks verified by MA: {0}from DataVerf log"
                                    .format(ma))

                for line in matched_line:
                    self.log.info(line)
                    x = re.match(r'[^[]*\[([^]]*)\]', line).groups()[0]
                    chunkinfo += [x]

                for chunks in chunkinfo:
                    split = re.split(',', chunks)
                    mpid_list += [split[0]]
                    volid_list += [split[1].strip()]
                    chunkid_list += [split[2].strip()]

                for mp in mpid_list:

                    query = "SELECT MMDC.DeviceAccessType &(16|32|128) DeviceType FROM MMMountPath MMM, " \
                            "MMMountpathToStorageDevice MMMTS, MMDeviceController MMDC, App_Client AC " \
                            "WHERE MMM.MountPathid = MMMTS.MountPathid AND MMMTS.Deviceid = MMDC.Deviceid" \
                            " AND MMDC.clientid = AC.id AND MMM.MountPathId = {0} AND AC.name = '{1}'".format(mp, ma)
                    self.csdb.execute(query)
                    query_result = self.csdb.fetch_all_rows()
                    self.log.info(query_result[0][0])
                    if query_result[0][0] == '0':
                        query = "SELECT MMDC.folder FROM MMMountPath MMM, MMMountpathToStorageDevice MMMTS, " \
                                "MMDeviceController MMDC, App_Client AC WHERE MMM.MountPathid = MMMTS.MountPathid " \
                                "AND MMMTS.Deviceid=MMDC.Deviceid AND MMDC.clientid=AC.id AND MMM.MountPathId = {0}" \
                                "AND AC.name = '{1}'".format(mp, ma)
                        self.csdb.execute(query)
                        query_result = self.csdb.fetch_all_rows()
                        if query_result[0][0].startswith("\\"):
                            self.log.info("Path is UNC")
                            # checking if the path is local to any other ma
                            query = "SELECT count (MMDC.Folder) folder FROM MMMountPath MMM,MMMountpathToStorageDevice MMMTS," \
                                    "MMDeviceController MMDC,App_Client AC WHERE MMM.MountPathid = MMMTS.MountPathid " \
                                    "AND MMMTS.Deviceid=MMDC.Deviceid AND MMDC.clientid=AC.id AND MMM.MountPathId in {0}" \
                                    "AND MMDC.DeviceAccessType &(16|32|128) not in (16,32,128) AND " \
                                    "MMDC.Folder not like '\\%' ".format(mp)
                            self.csdb.execute(query)
                            query_result = self.csdb.fetch_all_rows()
                            if query_result[0][0] != '0':
                                self.log.info("MP is local to another MA")
                                self.log.error("MP Affinity not verified")
                            else:
                                self.log.info("MP is not local to any other MA")
                                self.log.info("MP Affinity verified")

                        else:
                            self.log.info("Path is Local")
                            self.log.info("MP Affinity verified")
                    else:
                        self.log.info("MP is Data Server IP")
                        self.log.error("MP Affinity not verified")

            self.log.info(mpid_list)
            self.log.info(volid_list)
            self.log.info(chunkid_list)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down function of this test case"""

        if self.status != constants.FAILED:
            self.log.info("Testcase shows successful execution, cleaning up the test environment ...")
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
            self._cleanup()
        else:
            self.log.error("Testcase shows failure in execution, not cleaning up the test environment ...")
