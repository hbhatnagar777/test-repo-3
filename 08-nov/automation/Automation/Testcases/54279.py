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

    setup()                 --  pass function

    run()                   --  run function of this test case
"""
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.SNAPUtils.unixsnaphelper import UnixSnapHelper, Restore


class TestCase(CVTestCase):
    """Class for executing

            """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Intellisnap with and without cataloging for DC and Recursive scan"
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

        self.helper = None
        self.storage_policy = None
        self.client_machine = None
        self.subclient_content = None
        self.tmp_path = None

    def setup(self):
        pass

    def run(self):
        """Main function for test case execution
            This test case does the following:
                Run the Following without and with cataloging
                      Step1, Setting intellisnap enivronment
                      Step2, Checking if the mount point is already in monitoring state for DC
                      Step3, Creating the data and running full snap backup
                      Step4, Running out of place restore and verifying the restore data
                      Step5, Running backup copy job
                      Step6, Running out of place restore and verifying the restore data
                      Step7, Creating the data and running incremental snap backup
                      Step8, Running out of place restore and verifying the restore data
                      Step9, Running backup copy job
                      Step10, Running out of place restore and verifying the restore data
                      Step11, Running synthetic full job for the subclient
                      Step12, Running out of place restore and verifying the restore data
                      Step13, Change the scan option of subclient to recursive scan
                      Step14, Creating the data and running incremental snap backup
                      Step15, Running out of place restore and verifying the restore data
                      Step16, Running backup copy job
                      Step17, Running out of place restore and verifying the restore data
                      Step18, Running synthetic full job for the subclient
                      Step19, Running out of place restore and verifying the restore data
                      Step20, Cleaning the environment.


        """
        try:
            self.log.info("***TESTCASE: %s***", self.name)
            self.log.info("Creating registry key to support synthetic full")
            self.commcell.add_additional_setting(
                "CommServDB.Console", "bEnableFSSnapSyntheticFull", 'BOOLEAN', "true")
            self.commcell.add_additional_setting(
                "CommServDB.GXGlobalParam", "FSSnapSCSynthFull", 'INTEGER', "1")
            for catalog in [False, True]:
                if not catalog:
                    self.log.info("Running test case with cataloging option")
                else:
                    self.log.info("Running test case with skip catalog option")

                self.helper = UnixSnapHelper(
                    self.commcell, self.client, self.agent, self.tcinputs)
                self.log.info("Step1, Setting intellisnap enivronment")
                self.helper.setup_snap_environment()
                if not catalog:
                    self.log.info(
                        "Sleeping the test case for 6 mins in case "
                        "DC is enabled for the first time")
                    time.sleep(360)
                self.log.info(
                    "Step2, Checking if the mount point is already in monitoring state for DC")

                for content in self.helper.contents:
                    path = content.split(self.helper.client_machine.os_sep)
                    mount_point = self.helper.client_machine.os_sep + path[1]
                    self.helper.check_volume_monitoring(mount_point)

                self.log.info(
                    "Step3, Creating the data and running full snap backup")
                job = self.helper.snap_backup(
                    constants.backup_level.FULL, option={
                        'skip_catalog': catalog})
                if not catalog:
                    if self.helper.verify_optimized_scan(job.job_id):
                        self.log.info("DC was used for scaning the content")
                    else:
                        self.log.error("DC was not used for %s " % job.job_id)
                        raise Exception("DC was not used for %s" % job.job_id)
                self.log.info(
                    "Step4, Running out of place restore and verifying the restore data")
                self.helper.restore(
                    Restore.RESTORE_FROM_SNAP.value,
                    self.helper.test_data_paths,
                    False)
                self.log.info("Restore job completed successfully")
                self.helper.verify_restore(
                    self.helper.client_machine,
                    self.helper.test_data_paths,
                    self.helper.restore_path)

                self.log.info("Step5, Running backup copy job")
                job = self.helper.backup_copy(True)
                if catalog:
                    if self.helper.verify_optimized_scan(job.job_id):
                        self.log.info("DC was used for scaning the content")
                    else:
                        self.log.error("DC was not used for %s " % job.job_id)
                        raise Exception("DC was not used for %s" % job.job_id)
                self.log.info(
                    "Step6, Running out of place restore and verifying the restore data")
                self.helper.restore(
                    Restore.RESTORE_FROM_TAPE.value,
                    self.helper.test_data_paths,
                    False)
                self.log.info("Restore job completed successfully")
                self.helper.verify_restore(
                    self.helper.client_machine,
                    self.helper.test_data_paths,
                    self.helper.restore_path)

                self.log.info(
                    "Step7, Creating the data and running incremental snap backup")
                job = self.helper.snap_backup(
                    constants.backup_level.INCREMENTAL, option={
                        'skip_catalog': catalog})
                if not catalog:
                    if self.helper.verify_optimized_scan(job.job_id):
                        self.log.info("DC was used for scaning the content")
                    else:
                        self.log.error("DC was not used for %s " % job.job_id)
                        raise Exception("DC was not used for %s" % job.job_id)
                self.log.info(
                    "Step8, Running out of place restore and verifying the restore data")
                self.helper.restore(
                    Restore.RESTORE_FROM_SNAP.value,
                    self.helper.test_data_paths,
                    False)
                self.log.info("Restore job completed successfully")
                self.helper.verify_restore(
                    self.helper.client_machine,
                    self.helper.test_data_paths,
                    self.helper.restore_path)
                self.log.info("Step9, Running backup copy job")
                job = self.helper.backup_copy(True)
                if catalog:
                    if self.helper.verify_optimized_scan(job.job_id):
                        self.log.info("DC was used for scaning the content")
                    else:
                        self.log.error("DC was not used for %s " % job.job_id)
                        raise Exception("DC was not used for %s" % job.job_id)
                self.log.info(
                    "Step10, Running out of place restore and verifying the restore data")
                self.helper.restore(
                    Restore.RESTORE_FROM_TAPE.value,
                    self.helper.test_data_paths,
                    False)
                self.log.info("Restore job completed successfully")
                self.helper.verify_restore(
                    self.helper.client_machine,
                    self.helper.test_data_paths,
                    self.helper.restore_path)

                self.log.info(
                    "Step11, Running synthetic full job for the subclient")
                self.helper.snap_backup(constants.backup_level.SYNTHETICFULL)
                self.log.info(
                    "Step12, Running out of place restore and verifying the restore data")
                self.helper.restore(
                    Restore.RESTORE_FROM_TAPE.value,
                    self.helper.test_data_paths,
                    False)
                self.log.info("Restore job completed successfully")
                self.helper.verify_restore(
                    self.helper.client_machine,
                    self.helper.test_data_paths,
                    self.helper.restore_path)

                self.log.info(
                    "Step13, Change the scan option of subclient to recursive scan")
                self.helper.subclient.scan_type = ScanType.RECURSIVE.value

                self.log.info(
                    "Step14, Creating the data and running incremental snap backup")
                job = self.helper.snap_backup(
                    constants.backup_level.INCREMENTAL, option={
                        'skip_catalog': catalog})
                if not catalog:
                    if not self.helper.verify_optimized_scan(job.job_id):
                        self.log.info(
                            "Regular scan was used for scaning the content")
                    else:
                        self.log.error("DC was used for %s " % job.job_id)
                        raise Exception("DC was used for %s" % job.job_id)
                self.log.info(
                    "Step15, Running out of place restore and verifying the restore data")
                self.helper.restore(
                    Restore.RESTORE_FROM_SNAP.value,
                    self.helper.test_data_paths,
                    False)
                self.log.info("Restore job completed successfully")
                self.helper.verify_restore(
                    self.helper.client_machine,
                    self.helper.test_data_paths,
                    self.helper.restore_path)

                self.log.info("Step16, Running backup copy job")
                job = self.helper.backup_copy(True)
                if catalog:
                    if not self.helper.verify_optimized_scan(job.job_id):
                        self.log.info(
                            "Regular scan was used for scaning the content")
                    else:
                        self.log.error("DC was used for %s " % job.job_id)
                        raise Exception("DC was used for %s" % job.job_id)
                self.log.info(
                    "Step17, Running out of place restore and verifying the restore data")
                self.helper.restore(
                    Restore.RESTORE_FROM_TAPE.value,
                    self.helper.test_data_paths,
                    False)
                self.log.info("Restore job completed successfully")

                self.helper.verify_restore(
                    self.helper.client_machine,
                    self.helper.test_data_paths,
                    self.helper.restore_path)
                self.log.info(
                    "Step18, Running synthetic full job for the subclient")
                self.helper.snap_backup(constants.backup_level.SYNTHETICFULL)
                self.log.info(
                    "Step19, Running out of place restore and verifying the restore data")
                self.helper.restore(
                    Restore.RESTORE_FROM_TAPE.value,
                    self.helper.test_data_paths,
                    False)
                self.log.info("Restore job completed successfully")
                self.helper.verify_restore(
                    self.helper.client_machine,
                    self.helper.test_data_paths,
                    self.helper.restore_path)
                self.log.info("Step20, Cleaning the environment.")
                self.helper.cleanup()

            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
