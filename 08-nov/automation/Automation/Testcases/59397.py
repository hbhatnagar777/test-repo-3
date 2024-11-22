# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from AutomationUtils import constants
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.machine import Machine
import datetime
import time


class TestCase(CVTestCase):
    """Class to verify that stubbing happens only after the job is copied to the secondary copy."""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "Redundancy Check - This testcases verifies the stubbing happens only after the job is copied to the secondary copy."
        self.base_folder_path = None
        self.OPHelper = None
        self.MAHelper = None
        self.is_nas_turbo_type = False
        self.sp = None
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None,
            "SecondaryCopyName": None,
            "SecondaryCopyLibraryName": None,
            "SecondaryMAName": None,
            "PrimaryMAName": None,
            "PrimaryCopyName": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.OPHelper = cvonepas_helper(self)
        self.MAHelper = MMHelper(self)
        self.OPHelper.populate_inputs()
        self.log.info("Test inputs populated successfully")

        if self.OPHelper.nas_turbo_type.lower() == 'networkshare':
            self.is_nas_turbo_type = True

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", True)]

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")

        self.MAHelper.configure_storage_policy(storage_policy_name=self.tcinputs.get('StoragePolicyName'),
                                               library_name=self.tcinputs.get('PrimaryCopyLibraryName'),
                                               ma_name=self.tcinputs.get('PrimaryMAName'))
        self.sp = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicyName'))
        self.MAHelper.configure_secondary_copy(sec_copy_name=self.tcinputs.get('SecondaryCopyName'),
                                               storage_policy_name=self.tcinputs.get('StoragePolicyName'),
                                               library_name=self.tcinputs.get('SecondaryCopyLibraryName'),
                                               ma_name=self.tcinputs.get('SecondaryMAName'))

        self.OPHelper.prepare_turbo_testdata(
            self.base_folder_path,
            self.OPHelper.test_file_list,
            size1=20 * 1024,
            size2=20 * 1024)
        self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(data_path=self.base_folder_path)
        self.log.info("Test data populated successfully.")

        self.OPHelper.create_archiveset(delete=True, is_nas_turbo_backupset=self.is_nas_turbo_type)
        self.OPHelper.create_subclient(delete=True, content=[self.base_folder_path])

        if self.is_nas_turbo_type:
            update_properties = self.OPHelper.testcase.subclient.properties
            update_properties['fsSubClientProp']['scanOption'] = 1
            update_properties['fsSubClientProp']['enableNetworkShareAutoMount'] = True
            update_properties['fsSubClientProp']['checkArchiveBit'] = True
            update_properties['fsSubClientProp']['preserveFileAccessTime'] = True
            update_properties['impersonateUser']['password'] = self.tcinputs.get("ImpersonatePassword")
            update_properties['impersonateUser']['userName'] = self.tcinputs.get("ImpersonateUser")
            self.OPHelper.testcase.subclient.update_properties(update_properties)

        _disk_cleanup_rules = {
            "useNativeSnapshotToPreserveFileAccessTime": False,
            "fileModifiedTimeOlderThan": 0,
            "fileSizeGreaterThan": 10,
            "stubPruningOptions": 0,
            "afterArchivingRule": 1,
            "stubRetentionDaysOld": 365,
            "fileCreatedTimeOlderThan": 0,
            "maximumFileSize": 0,
            "fileAccessTimeOlderThan": 0,
            "startCleaningIfLessThan": 100,
            "enableRedundancyForDataBackedup": True,
            "patternMatch": "",
            "stopCleaningIfupto": 100,
            "rulesToSatisfy": 1,
            "enableArchivingWithRules": True,
            'diskCleanupFileTypes': {'fileTypes': ["%Text%", '%Image%', '%Audio%']}
        }

        self.OPHelper.testcase.subclient.archiver_retention = True
        self.OPHelper.testcase.subclient.archiver_retention_days = -1

        self.OPHelper.testcase.subclient.backup_retention = False

        self.OPHelper.testcase.subclient.disk_cleanup = True
        self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules

        self.OPHelper.testcase.subclient.backup_only_archiving_candidate = True

    def run(self):
        """Run function of this test case"""

        _desc = """
        1. Configure Primary and Secondary copy. 
        2. Set the enableRedundancyForDataBackedup property to true oin subclient properties.
        3. Run Archiving Jobs on primary. 
        4. Validate Files are not stubbed.
        5. Run Auxcopy job to secondary copy.
        6. Run Archiving Jobs.
        7. Validate Files are stubbed.
        """

        try:
            self.log.info(_desc)
            self.OPHelper.run_archive(repeats=1)

            time.sleep(300)
            self.OPHelper.verify_stub(test_data_list=[("test1.txt", False), ("test2.txt", False)],
                                      is_nas_turbo_type=self.is_nas_turbo_type)

            # Commented below lines as Aux copy job is ran automatically now.
            # self.log.info("Start Running Aux Copy")
            # aux_job = self.sp.run_aux_copy(storage_policy_copy_name=self.tcinputs.get('SecondaryCopyName'),
            #                                media_agent=self.tcinputs.get('PrimaryMAName'))
            # if aux_job.wait_for_completion():
            #     self.log.info("Completed Running Aux Copy")

            self.OPHelper.run_archive(repeats=1)

            time.sleep(300)
            self.OPHelper.verify_stub(test_data_list=[("test1.txt", True), ("test2.txt", True)],
                                      is_nas_turbo_type=self.is_nas_turbo_type)

            time.sleep(200)
            self.OPHelper.recall()

            self.log.info('Redundancy Check passed.')

        except Exception as exp:
            self.log.error('Redundancy Check failed with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
