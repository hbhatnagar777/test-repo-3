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

    tear_down()     --  tear down function of this test case

"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """
        Testcase for checking VSS creation/deletion while backing up PST files

        Steps:
        1. Create test data (pst files) for Full backup.
        2. Run a Full backup.
        3. Check whether VSS snapshot was created and then deleted.
        4. Create test data (pst files) for Inc backup.
        5. Run Inc backup.
        6. Check whether VSS snapshot was created and then deleted.
    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "VSS for PST files"
        self.applicable_os = self.os_list.WINDOWS
        self.show_to_user = False
        self.tcinputs = {
            "StoragePolicyName": None,
            "ContentPath": None
        }
        self.storagePolicy = None
        self.contentPath = None
        self.helper = None

    def setup(self):
        """Setup function of this test case"""
        self.helper = FSHelper(self)
        self.helper.populate_tc_inputs(self, mandatory=False)
        self.storagePolicy = self.tcinputs.get("StoragePolicyName", None)
        self.contentPath = self.tcinputs.get("ContentPath", None)

    def run(self):
        """Run function of this test case"""
        contentPathInc = self.client_machine.join_path(self.contentPath, "Inc")

        try:
            self.log.info("Step 1: Populating test data for Full backup")
            if self.client_machine.check_directory_exists(self.contentPath):
                self.log.info("Deleting the existing folder")
                self.client_machine.remove_directory(self.contentPath)
            self.client_machine.create_directory(self.contentPath)
            self.log.info("Creating test PST files for Full backup")
            self.generate_pstfiles(self.contentPath, 10, 10000000)

            self.log.info("Step 2: Creating a backupset")
            backupset_name = "Test_62532"
            self.helper.create_backupset(backupset_name, delete=False)
            self.helper.create_subclient(name="pst", storage_policy=self.storagePolicy, content=[self.contentPath])

            self.log.info("Step 3: Running a Full backup")
            job_full = self.helper.run_backup(backup_level='Full', wait_to_complete=True)

            self.log.info("Step 4: Get the snapshot ID for Full job")
            snapshot_id = self.check_vss_snapshot_created(job_full[0].job_id)
            if snapshot_id == 'Not found':
                raise Exception("The snapshot wasn't created for Full backup job!")
            self.log.info(snapshot_id)

            self.log.info("Step 5: Check if the snapshot is deleted for Full job")
            self.helper.is_snapshot_deleted(snapshot_id)

            self.log.info("Step 6: Populating test data for Inc backup")
            if self.client_machine.check_directory_exists(contentPathInc):
                self.log.info("Deleting the existing folder")
                self.client_machine.remove_directory(contentPathInc)
            self.client_machine.create_directory(contentPathInc)
            self.log.info("Creating test PST files for Inc backup")
            self.generate_pstfiles(contentPathInc, 4, 10000000)

            self.log.info("Step 7: Running a Inc backup")
            job_inc = self.helper.run_backup(backup_level='Incremental', wait_to_complete=True)

            self.log.info("Step 8: Get the snapshot ID for Inc job")
            snapshot_inc_id = self.check_vss_snapshot_created(job_inc[0].job_id)
            if snapshot_inc_id == 'Not found':
                raise Exception("The snapshot wasn't created for Inc backup job!")
            self.log.info(snapshot_inc_id)

            self.log.info("Step 9: Check if the snapshot is deleted for Inc job")
            self.helper.is_snapshot_deleted(snapshot_inc_id)

            self.log.info("Test case executed succesfully")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.client_machine.remove_directory(self.contentPath)

    def generate_pstfiles(self, path=None, count=5, size=100):
        for i in range(count):
            file_name = "{0}{1}{2}{3}".format(path, self.slash_format,
                                              str(i), '.pst')
            data_to_file = str("My File Data {0}".format(file_name))
            self.client_machine.create_file(file_name, data_to_file, size)

    def check_vss_snapshot_created(self, jobid):
        response = self.client_machine.get_logs_for_job_from_file(jobid, 'clBackup.log', 'ShadowId is')

        if response is None:
            return 'Not found'
        else:
            self.log.info(response)
            arr = response.split(' ShadowId is ')
            subarr = arr[1].split(', ShadowPath is ')
            shadowId = subarr[0][1:len(subarr[0])-1]
            return shadowId
