# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case

    verify_iscsi_mount     -- TO verify iscsi browse
"""

from time import sleep
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper, IndexEnabled
from AutomationUtils.database_helper import get_csdb


class TestCase(CVTestCase):
    """Class for executing Blocklevel  Data Protection - Full,Incremental,Synthfull
        This test case does the following
        Step1, Create backupset for this testcase if it doesn't exist.
            Step2, For each of the allowed scan type
                    do the following on the backupset
                Step3, For each of the allowed index_type (Meta data colection Enabled/Not)
                    do the following on the backupset
                        Step3.1,  Create subclient for the scan type if it doesn't exist and enable
                            blocklevel and metadata collection options.
                            Step3.2, Add full data for the current run.
                            Step3.3, Run a full backup for the subclient
                                and verify it completes without failures.
                            Step3.4, Run a Volume level Restore
                                and verify correct data is restored.
                            Step3.5, Run a File level Restore with iscsi option
                                and verify correct data is restored.
                            Step3.6 , Validate iscsi mount
                            Step3.7, Add new data for the incremental
                            Step3.8, Run an incremental backup for the subclient
                                and verify it completes without failures.
                            Step3.9, Run a Volume level Restore
                                and verify correct data is restored.
                            Step4.0, Run a File level Restore with iscsi option
                                and verify correct data is restored.
                            Step4.1 , Validate iscsi mount
                            Step4.2, Run an synthfull for the subclient and
                                verify it completes without failures
                            Step4.3, Run a Volume level Restore
                                and verify correct data is restored.
                            Step4.4, Run a File level Restore with iscsi option
                                and verify correct data is restored.
                            Step4.5 , Validate iscsi mount

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Windows Blocklevel  Data Protection" \
                    " - Full,Incremental,Synthetic Full"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "TestPath": None,
            "TestPath2": None,
            "RestorePath": None,
            "IscsiServer": None,
            "StoragePolicyName": None
        }
        self.client_name = ""
        self.client_machine = None
        self.runid = ""
        self.slash_format = ""
        self.test_path = ""
        self.test_path2 = ""
        self.test_path3 = ""
        self.restore_path = ""
        self.storage_policy = None
        self.verify_dc = None
        self.wait_time = 30
        self.iscsi_server = ""
        self.proxy_client = ""
        self.helper = FSHelper(TestCase)

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        try:
            # Initialize test case inputs

            FSHelper.populate_tc_inputs(self)

            test_path = self.test_path
            slash_format = self.slash_format
            helper = self.helper
            if test_path.endswith(slash_format):
                test_path = str(test_path).rstrip(slash_format)
            storage_policy = self.storage_policy

            log.info(""" Blocklevel  Data Protection - Full,Incremental,Synthfull
                    This test case does the following
                    Step1, Create backupset for this testcase if it doesn't exist.
                        Step2, For each of the allowed scan type
                                do the following on the backupset
                            Step3, For each of the allowed index_type (Meta data colection Enabled/Not)
                                do the following on the backupset
                                    Step3.1,  Create subclient for the scan type if it doesn't exist and enable
                                        blocklevel and metadat collection options.
                                        Step3.2, Add full data for the current run.
                                        Step3.3, Run a full backup for the subclient
                                            and verify it completes without failures.
                                        Step3.4, Run a Volume level Restore
                                            and verify correct data is restored.
                                        Step3.5, Run a File level Restore
                                            and verify correct data is restored.
                                        Step3.6, Add new data for the incremental
                                        Step3.7, Run an incremental backup for the subclient
                                            and verify it completes without failures.
                                        Step3.8, Run a Volume level Restore
                                            and verify correct data is restored.
                                        Step3.9, Run a File level Restore
                                            and verify correct data is restored.
                                        Step3.10, Run an synthfull for the subclient and
                                            verify it completes without failures
                                        Step3.11, Run a Volume level Restore
                                            and verify correct data is restored.
                                        Step3.12, Run a File level Restore
                                            and verify correct data is restored""")

            log.info("Step1, Create backupset for "
                     "this testcase if it doesn't exist")
            backupset_name = "backupset_" + self.id
            helper.create_backupset(backupset_name)

            log.info("Step2, For each of the allowed scan type Create all operations")

            for scan_type in ScanType:
                log.info(
                    "Step3, For each of the allowed index_type"
                    "Meta data colection Enabled/Not do operatons")
                for index_type in IndexEnabled:
                    if scan_type.name == 'CHANGEJOURNAL':
                        continue
                    elif scan_type.name == 'OPTIMIZED' and index_type.name == 'NOINDEX':
                        log.info(
                            "Skipping Optimised scan as all operations done on Classic Scan")
                        continue
                    else:
                        # Assigning mountpoint as content based on Scan and Index type
                        if scan_type.name == 'RECURSIVE' and index_type.name == 'INDEX':
                            test_path = self.test_path2
                            helper = self.helper
                            if test_path.endswith(slash_format):
                                test_path = str(test_path).rstrip(slash_format)
                        elif scan_type.name == 'RECURSIVE' and index_type.name == 'NOINDEX':
                            test_path = self.test_path
                            helper = self.helper
                            if test_path.endswith(slash_format):
                                test_path = str(test_path).rstrip(slash_format)

                        log.info("Running operations on Scan Type: %s", str(scan_type))
                        log.info("Running operations on Index Type: %s", str(index_type))

                        # SKip chain journal scan for Unix
                        if (self.applicable_os != 'WINDOWS'
                                and
                                scan_type.value == ScanType.CHANGEJOURNAL.value):
                            continue

                        # Skip DC if verify_dc is not provided
                        if (self.applicable_os != 'WINDOWS'
                                and scan_type.value == ScanType.OPTIMIZED.value):
                            if not self.verify_dc:
                                continue

                        log.info("Step3.1,  Create subclient for the scan type %s "
                                 "Index type if it doesn't exist.", scan_type.name)

                        subclient_name = ("subclient_%s_%s_%s" % \
                                          (self.id, scan_type.name.lower(), index_type.name.lower()))

                        subclient_content = []
                        subclient_content.append(test_path)
                        restore_path = self.restore_path
                        slash_format = self.slash_format
                        helper = self.helper
                        if restore_path.endswith(slash_format):
                            restore_path = str(restore_path).rstrip(slash_format)

                        tmp_path = ("%s%scvauto_tmp%s%s%s%s" % \
                                    (restore_path, slash_format, slash_format, subclient_name, \
                                     slash_format, str(self.runid)))

                        synthfull_tmp_path = ("%s%scvauto_tmp%s%s%s%s" % \
                                              (restore_path, slash_format, slash_format, \
                                               subclient_name, slash_format, str(self.runid)))

                        synthfull_run_path = ("%s%s%s" % (subclient_content[0], \
                                                          slash_format, str(self.runid)))
                        synthfull_datapath = synthfull_run_path

                        run_path = ("%s%s%s" % (subclient_content[0], slash_format, str(self.runid)))

                        vlr_source = ("%s%s%s" % (str(test_path), slash_format, str(self.runid)))
                        vlr_destination = ("%s%s%s" % (str(restore_path), slash_format, \
                                                       str(self.runid)))
                        full_data_path = ("%s%sfull" % (run_path, slash_format))

                        log.info("Step3.1,  Create subclient for the scan type if it doesn't exist")

                        # Create Subclient if doesnt exist

                        helper.create_subclient(
                            name=subclient_name,
                            storage_policy=storage_policy,
                            content=subclient_content,
                            scan_type=scan_type
                        )
                        # Update Subclient with blocklevel value if not set
                        log.info("Enabling BlockLevel Option")
                        helper.update_subclient(content=subclient_content,
                                                block_level_backup=1)

                        # Update Subclient with Meta data value if not set

                        if index_type.name == "INDEX":
                            log.info("Enabling Metadata collection")
                            helper.update_subclient(content=subclient_content,
                                                    createFileLevelIndex=True)

                        log.info("Step3.2, Add full data for the current run")

                        log.info("Adding data under path: %s", full_data_path)
                        self.client_machine.generate_test_data(
                            full_data_path
                        )
                        #wait for for journals to get flushed
                        if not scan_type.value == ScanType.RECURSIVE.value:
                            log.info("Waiting for journals to get flushed")
                            sleep(self.wait_time)

                        log.info(
                            "Step3.3,Run a full backup for the subclient"
                            "and verify it completes without failures")

                        job_full = helper.run_backup_verify(scan_type, "Full")[0]
                        log.info(
                            "Step3.4, Run a Volume level Restore"
                            "and verify correct data is restored.")
                        helper.volume_level_restore(vlr_source, vlr_destination, \
                                                    client_name=self.client_name)
                        # Compare Source and Destination and check files restored.

                        log.info("Step3.5, Run a File level Restore"
                                 "and verify correct data is restored.")

                        restore_jobid = helper.run_restore_verify(
                            slash_format,
                            full_data_path,
                            tmp_path, "full", job_full, proxy_client=self.proxy_client, \
                            iscsi_server=self.iscsi_server)
                        log.info("Restore Jobid %s", str(restore_jobid.job_id))

                        if index_type.name == 'NOINDEX':
                            sleep(200)
                            log.info("validate mount is done with  iscsi or not  ")
                            self.verify_iscsi_mount(restore_jobid.job_id)
                            log.info("Iscsi check validated ")

                        log.info("<<<<<<< Cycle 1 completed >>>>>>")

                        log.info("** %s SCAN TYPE USED", scan_type.name)
                        log.info("** %s INDEXTYPE USED", index_type.name)
                        log.info("RUN COMPLETED SUCCESFULLY")

                        self.client_machine.remove_directory(tmp_path)
            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED

        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def verify_iscsi_mount(self, restore_jobid):
        """Check data size backedup since last incremental"""
        log = logger.get_log()
        log.info("Restore job id = %s", str(restore_jobid))
        log.info("validate mount")
        _query1 = "select count(*) from SMMountVolumeDeleted with(NOLOCK) " \
                  "                                where MountJobId IN (%s)" \
                  " and MountFlags IN (32,64) " % (str(restore_jobid))
        # _query1 = "select count(*) from SMMountVolumeDeleted with(NOLOCK)
        #                 where MountJobId IN (%s) and MountFlags IN (32,64)
        #                                            " % (int(restore_jobid))
        log.info(_query1)
        csdb = get_csdb()
        csdb.execute(_query1)
        _results_1 = csdb.fetch_all_rows()
        log.info(_results_1)
        log.info("No.of iscsi Entries in DB : %s", _results_1[0][0])

        if int(_results_1[0][0]) > 0:
            log.info("ISCSI MOUNT CHECK SUCCESSFULL ")

        else:
            log.info("ISCSI MOUNT CHECK FAILED")
            raise Exception(" iscsi check has failed items")
