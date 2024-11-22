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
    __init__()              --  Initialize TestCase class

    setup()                 --  create unixsnapheler object

    run()                   --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.unixsnaphelper import UnixSnapHelper, Restore
from AutomationUtils.constants import backup_level


class TestCase(CVTestCase):
    """Class for executing

            """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Intellisnap with multistream backup and restore"
        self.applicable_os = self.os_list.UNIX
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = False
        self.tcinputs = {
            "MediaAgentName": None,
            'SubclientContent': None,
            'InstanceName': None,
            'DiskLibLocation': None,
            'ArrayName': None,
            'ControlHost': None,
            'ArrayUserName': None,
            "ArrayPassword": None,
            'SnapEngine': None



        }
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.client_machine = None
        self.subclient_content = None
        self.tmp_path = None

    def setup(self):
        self.helper = UnixSnapHelper(
            self.commcell,
            self.client,
            self.agent,
            self.tcinputs)

    def run(self):
        """Main function for test case execution
        This test case does the following:
            Step1, Create intellisnap environment
            Step2, Add data to subclient content and run full job
            Step3, Run restore and verify the data restore
            Step4, Run backup copy for the subclient
            Step5, Verify expected number of streams used by backup copy
            Step6, Run multistream restore , verify the number of streams and restore data
            Step7, Add data to subclient content and run incremental job
            Step8, Run restore and verify the data restore
            Step9, Run backup copy for the subclient
            Step10, Verify expected number of streams used by backup copy
            Step11, Run multistream restore , verify the number of streams and restore data
            Step12,  Run synthetic full job for the subclient
            Step13, Run multistream restore , verify the number of streams and restore data
            Step14, Cleanup

        """
        try:
            self.log.info("***TESTCASE: %s***", self.name)
            self.log.info("Step1, Create intellisnap environment")
            self.helper.setup_snap_environment()
            self.log.info(
                "Step2, Add data to subclient content and run full job")
            self.helper.snap_backup(backup_level.FULL)
            self.log.info("Step3, Run restore and verify the data restore")
            self.helper.restore(
                Restore.RESTORE_FROM_SNAP.value,
                self.helper.test_data_paths,
                False)
            self.log.info("Restore job completed successfully")
            self.helper.verify_restore(
                self.helper.client_machine,
                self.helper.test_data_paths,
                self.helper.restore_path)
            self.log.info("Step4, Run backup copy for the subclient")
            job = self.helper.backup_copy(True)
            self.log.info(
                "Step5, Verify if expected number of streams used by backup copy")
            if len(self.helper.contents) < 4:
                expected_stream = len(self.helper.contents) + 1
            else:
                expected_stream = 4
            self.helper.verify_job_streams(
                job, expected_stream, self.helper.get_backup_stream_count(job))

            self.log.info(
                "Step6, Run multistream restore , verify the number of streams and restore data")
            self.helper.restore(
                Restore.RESTORE_FROM_TAPE.value,
                self.helper.test_data_paths,
                False,
                no_of_streams=2)

            self.helper.verify_restore(
                self.helper.client_machine,
                self.helper.test_data_paths,
                self.helper.restore_path)

            self.log.info(
                "Step7, Add data to subclient content and run incremental job")
            self.helper.snap_backup(backup_level.INCREMENTAL)
            self.log.info("Step8, Run restore and verify the data restore")
            self.helper.restore(
                Restore.RESTORE_FROM_SNAP.value,
                self.helper.test_data_paths,
                False)
            self.log.info("Restore job completed successfully")
            self.helper.verify_restore(
                self.helper.client_machine,
                self.helper.test_data_paths,
                self.helper.restore_path)
            self.log.info("Step9, Run backup copy for the subclient")
            job = self.helper.backup_copy(True)
            self.log.info(
                "Step10, Verify if expected number of streams used by backup copy")
            self.helper.verify_job_streams(
                job, expected_stream, self.helper.get_backup_stream_count(job))
            self.log.info(
                "Step11, Run multistream restore , verify the number of streams and restore data")
            self.helper.restore(
                Restore.RESTORE_FROM_TAPE.value,
                self.helper.test_data_paths,
                False,
                no_of_streams=2)
            self.helper.verify_restore(
                self.helper.client_machine,
                self.helper.test_data_paths,
                self.helper.restore_path)
            self.log.info("Step12,  Run synthetic full job for the subclient")
            self.helper.snap_backup(backup_level.SYNTHETICFULL)
            self.log.info(
                "Step13, Run multistream restore , verify the number of streams and restore data")
            self.helper.restore(
                Restore.RESTORE_FROM_TAPE.value,
                self.helper.test_data_paths,
                False,
                no_of_streams=2)
            self.helper.verify_restore(
                self.helper.client_machine,
                self.helper.test_data_paths,
                self.helper.restore_path)
            self.log.info("Step14, Cleanup")
            self.helper.cleanup()

            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
