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
"""

from time import sleep
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper, IndexEnabled


class TestCase(CVTestCase):
    """Class for executing Blocklevel Filer proxy   Data Protection - Full,Incremental,Synthfull
                    This test case does the following
                    Step1, Create backupset for this testcase if it doesn't exist.
                        Step2, For each of the allowed scan type
                            do the following on the backupset
                                Step3, For each of the allowed Indextype
                                    (Meta data colection Enabled/Not)
                                    do the following on the backupset
                                    Step3.1 Enable Intelli Snap for client
                                    Step3.2,Create subclient for the scan type if it doesn't exist
                                            and enable blocklevel and metadat collection options.
                                    Step3.3, Enable Intellisnap
                                            on Client with "Netapp" Option
                                    Step3.4, Add full data for the current run.
                                    Step3.5, Run a full Snap  backup for the subclient
                                             and verify it completes without failures.
                                    Step3.6, Run a Volume level Restore
                                              and verify correct data is restored.
                                    Step3.7, Run a File level Restore
                                             and verify correct data is restored.
                                    Step3.8, Run a backup copy full backup for the subclient
                                              and verify it completes without failures.
                                    Step3.9, Run a Volume level Restore
                                            and verify correct data is restored.
                                    Step3.10, Run a File level Restore
                                            and verify correct data is restored.
                                    Step3.11, Add new data for the incremental
                                    Step3.12, Run an incremental  Snap backup for the subclient
                                              and verify it completes without failures.
                                    Step3.13, Run a Volume level Restore
                                            and verify correct data is restored.
                                    Step3.14, Run a File level Restore
                                            and verify correct data is restored.
                                    Step3.15, Run a backup copy Incremental  backup for the
                                            subclient and verify it completes without failures.
                                    Step3.16, Run a Volume level Restore
                                            and verify correct data is restored.
                                    Step3.17, Run a File level Restore
                                             and verify correct data is restored.
                                    Step3.18, Run an synthfull for the subclient and
                                            verify it completes without failures
                                    Step3.19, Run a Volume level Restore
                                            and verify correct data is restored.
                                    Step3.20, Run a File level Restore
                                            and verify correct data is restored.
                                    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Filer Blocklevel WIth Proxy  "\
            " - Backup and restore"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "TestPath": None,
            "TestPath2": None,
            "TestPath3": None,
            "RestorePath": None,
            "StoragePolicyName": None,
            "AuxCopyMediaAgent": None,
            "AuxCopyLibrary": None,
            "snapautomationoutput": None,
            "snapvendor": None,
            "snapengine": None,
            "proxy_client":None
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
        self.snap_engine = "NetApp"
        self.verify_dc = None
        self.wait_time = 30
        self.subclient = ""
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
            self.subclient = "SC_77771"
            # snaphelper= SNAPHelper(self.commcell,self.client,self.subclient,self.tcinputs)
            if test_path.endswith(slash_format):
                test_path = str(test_path).rstrip(slash_format)
            storage_policy = self.storage_policy

            log.info(""" Filer Blocklevel WIth Proxy  - Full,Incremental,Synthfull
                    This test case does the following
                    Step1, Create backupset for this testcase if it doesn't exist.
                        Step2, For each of the allowed scan type
                            do the following on the backupset
                                Step3, For each of the allowed Indextype (Meta data colection Enabled/Not)
                                    do the following on the backupset
            						Step3.1 Enable Intelli Snap for client
                                    Step3.2,Create subclient for the scan type if it doesn't exist and enable
                                            blocklevel and metadat collection options.
            						Step3.3, Enable Intellisnap on Client with "Netapp" Option
                                    Step3.4, Add full data for the current run.
                                    Step3.5, Run a full Snap  backup for the subclient
                                             and verify it completes without failures.
                                    Step3.6, Run a Volume level Restore
                                              and verify correct data is restored.
                                    Step3.7, Run a File level Restore
                                             and verify correct data is restored.
            						Step3.8, Run a backup copy full backup for the subclient
                                              and verify it completes without failures.
                                    Step3.9, Run a Volume level Restore
                                            and verify correct data is restored.
                                    Step3.10, Run a File level Restore
                                            and verify correct data is restored.
                                    Step3.11, Add new data for the incremental
                                    Step3.12, Run an incremental  Snap backup for the subclient
                                              and verify it completes without failures.
                                    Step3.13, Run a Volume level Restore
                                            and verify correct data is restored.
                                    Step3.14, Run a File level Restore
                                            and verify correct data is restored.
            						Step3.15, Run a backup copy Incremental  backup for the subclient
                                            and verify it completes without failures.
                                    Step3.16, Run a Volume level Restore
                                            and verify correct data is restored.
                                    Step3.17, Run a File level Restore
                                             and verify correct data is restored.
                                    Step3.18, Run an synthfull for the subclient and
                                            verify it completes without failures
                                    Step3.19, Run a Volume level Restore
                                            and verify correct data is restored.
                                    Step3.20, Run a File level Restore
                                            and verify correct data is restored.
                                    """)

            log.info("Step1, Create backupset for "
                     "this testcase if it doesn't exist")
            backupset_name = "backupset_" + self.id
            helper.create_backupset(backupset_name)

            log.info("Step2, Executing steps for all the allowed scan type&Index type")

            for scan_type in ScanType:
                for index_type in IndexEnabled:
                    if scan_type.name == 'CHANGEJOURNAL':
                        continue
                    elif scan_type.name == 'OPTIMIZED' and index_type.name == 'NOINDEX':
                        log.info(
                            "Without Medata collection"
                            "we dont have any metadata collection so scan type Doesnt matter"
                        )
                        continue
                    elif scan_type.name == 'OPTIMIZED' and index_type.name == 'INDEX':
                        log.info(
                            "Skipping as Index with recursive ran here "
                        )
                        continue
                    else:
                        if scan_type.name == 'RECURSIVE' and index_type.name == 'INDEX':
                            test_path = self.test_path
                            slash_format = self.slash_format
                            helper = self.helper
                            if test_path.endswith(slash_format):
                                test_path = str(test_path).rstrip(slash_format)

                        elif scan_type.name == 'RECURSIVE' and index_type.name == 'NOINDEX':
                            test_path = self.test_path3
                            slash_format = self.slash_format
                            helper = self.helper
                            if test_path.endswith(slash_format):
                                test_path = str(test_path).rstrip(slash_format)
                        # SKip chain journal scan for Unix
                        if (self.applicable_os != 'WINDOWS'
                                and
                                scan_type.value == ScanType.CHANGEJOURNAL.value):
                            continue

                        snap_engine = self.snap_engine

                        # Skip DC if verify_dc is not provided
                        if (self.applicable_os != 'WINDOWS'
                                and
                                scan_type.value == ScanType.OPTIMIZED.value):
                            if not self.verify_dc:
                                continue
                        log.info("**STARTING RUN FOR %s  SCAN**", scan_type.name)
                        log.info("**STARTING RUN FOR %s  INDEX TYPE **", index_type.name)

                        log.info("Step2.1,  Create subclient for the scan type %s "
                                 "Index type if it doesn't exist.", scan_type.name)
                        subclient_name = ("subclient_"
                                          + self.id
                                          + "_"
                                          + scan_type.name.lower()
                                          + "_"
                                          + index_type.name.lower())
                        subclient_content = []
                        subclient_content.append(test_path)
                        restore_path = self.restore_path
                        slash_format = self.slash_format
                        helper = self.helper
                        if restore_path.endswith(slash_format):
                            restore_path = str(test_path).rstrip(slash_format)

                        tmp_path = ("%s%scvauto_tmp%s%s%s%s" %
                                    (restore_path, slash_format, slash_format, subclient_name,
                                     slash_format, str(self.runid)))

                        synthfull_tmp_path = ("%s%scvauto_tmp%s%s%s%s" %
                                              (restore_path, slash_format, slash_format,
                                               subclient_name, slash_format, str(self.runid)))

                        synthfull_run_path = ("%s%s%s" % (subclient_content[0],
                                                          slash_format, str(self.runid)))

                        synthfull_datapath = synthfull_run_path

                        run_path = ("%s%s%s" %
                                    (subclient_content[0], slash_format, str(self.runid)))

                        vlr_source = ("%s%s%s" % (str(test_path), slash_format, str(self.runid)))
                        vlr_destination = ("%s%s%s" % (str(restore_path), slash_format,
                                                       str(self.runid)))
                        full_data_path = ("%s%sfull" % (run_path, slash_format))

                        log.info("Step3.1 Enable Intelli Snap for client")

                        if not self.client.is_intelli_snap_enabled:
                            self._log.info("Intelli Snap is not enabled for client, enabling it.")
                            self.client.enable_intelli_snap()

                        self._log.info("Intelli Snap for client is enabled.")

                        log.info(
                            "Step3.2,Create subclient for the scan type if it doesn't exist and"
                            " enable blocklevel and metadat collection options.")

                        helper.create_subclient(
                            name=subclient_name,
                            storage_policy=storage_policy,
                            content=subclient_content,
                            scan_type=scan_type
                        )

                        log.info("Step3.3, Enable Intellisnap on Client with Snap Engine Option")

                        # Check if intellisnap is enabled at subclient level
                        if not self.subclient.is_intelli_snap_enabled:
                            self._log.info(
                                "Intelli snap is not enabled at subclient level, enabling it.")
                            proxy_options = {}
                            proxy_options['snap_proxy'] = self.proxy_client
                            self._log.info(proxy_options)
                            self.log.info(snap_engine)
                            self.subclient.enable_intelli_snap(str(snap_engine), proxy_options)

                        self._log.info("Intelli Snap for subclient is enabled.")

                        helper.update_subclient(content=subclient_content,
                                                block_level_backup=1)

                        if index_type.name == "INDEX":
                            helper.update_subclient(content=subclient_content,
                                                    createFileLevelIndex=True)

                        log.info("Step3.4, Add full data for the current run.")

                        log.info("Adding data under path: %s", full_data_path)
                        self.client_machine.generate_test_data(
                            full_data_path, dirs=5, files=20, file_size=50
                        )
                        # wait for for journals to get flushed
                        if not scan_type.value == ScanType.RECURSIVE.value:
                            log.info("Waiting for journals to get flushed")
                            sleep(self.wait_time)

                        log.info("Step3.5,  Run a full backup for the subclient "
                                 "and verify it completes without failures.")
                        job_full = helper.run_backup_verify(scan_type, "Full")[0]

                        log.info("Step3.6,  Run a Volume level Restore"
                                 "and verify correct data is restored.")

                        helper.volume_level_restore(
                            vlr_source, vlr_destination, client_name=self.client_name)
                        # Compare Source and Destination and check files restored.

                        log.info("Step3.7, Run a File level Restore"
                                 "and verify correct data is restored.")

                        helper.run_restore_verify(
                            slash_format,
                            full_data_path,
                            tmp_path, "full", job_full, proxy_client=self.proxy_client)

                        helper.backup_copy()

                        log.info("Step3.8,  Run a restore of the full Backup copy backup data"
                                 " and verify correct data is restored.")

                        log.info("Step3.9,  Run a Volume level Restore incremental"
                                 "and verify correct data is restored.")

                        helper.volume_level_restore(
                            vlr_source, vlr_destination, client_name=self.client_name)
                        # Compare Source and Destination and check files restored.

                        log.info("Step3.10, Run a File level Restore"
                                 "and verify correct data is restored.")

                        helper.run_restore_verify(
                            slash_format,
                            full_data_path,
                            tmp_path, "full", job_full, proxy_client=self.client_name)

                        log.info("Step3.11, Add new data for the incremental")
                        incr_diff_data_path = run_path + slash_format + "incr_diff"

                        self.client_machine.generate_test_data(
                            incr_diff_data_path, dirs=5, files=20, file_size=50
                        )

                        log.info("Step3.12, Run an incremental  Snap backup for the subclient"
                                 "and verify it completes without failures")
                        job_incr1 = helper.run_backup_verify(
                            scan_type, "Incremental")[0]

                        log.info(
                            "Step3.13, Run a Volume level Restore"
                            "and verify correct data is restored."
                        )

                        helper.volume_level_restore(
                            vlr_source, vlr_destination, client_name=self.client_name)
                        # Compare Source and Destination and check files restored.

                        log.info("Step3.14, Run a File level Restore"
                                 "and verify correct data is restored.")

                        helper.run_restore_verify(
                            slash_format,
                            incr_diff_data_path,
                            tmp_path, "incr_diff", job_incr1, proxy_client=self.client_name)

                        log.info(
                            "Step3.15, Run a backup copy Incremental  backup for the subclient"
                            "and verify it completes without failures.")

                        # Run backup copy
                        helper.backup_copy()

                        log.info(
                            "Step3.16, Run a Volume level Restore"
                            "and verify correct data is restored"
                        )

                        helper.volume_level_restore(
                            vlr_source, vlr_destination, client_name=self.client_name)
                        # Compare Source and Destination and check files restored.

                        log.info("Step3.17, Run a File level Restore"
                                 "and verify correct data is restored.")

                        helper.run_restore_verify(
                            slash_format,
                            incr_diff_data_path,
                            tmp_path, "incr_diff", job_incr1, proxy_client=self.client_name)

                        log.info(
                            "Step3.18, Run an synthfull for the subclient and"
                            "verify it completes without failures"
                        )

                        helper.run_backup_verify(scan_type, "Synthetic_full")

                        log.info("Step3.19, Run a Volume level Restore"
                                 "and verify correct data is restored.")

                        helper.volume_level_restore(
                            vlr_source, vlr_destination, client_name=self.client_name)
                        # Compare Source and Destination and check files restored.

                        log.info("Step3.20, Run a File level Restore"
                                 "and verify correct data is restored.")

                        helper.run_restore_verify(
                            slash_format,
                            synthfull_datapath,
                            synthfull_tmp_path, str(self.runid), proxy_client=self.client_name)

                        log.info("<<<<<<< Cycle 1 completed >>>>>>")


                        self.client_machine.remove_directory(
                            subclient_content[0])

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