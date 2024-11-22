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
import _thread
import os,msvcrt
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper


class TestCase(CVTestCase):
    """Class for executing
        File System Data Protection - Full,Incremental,Differential
        This test case does the following
        Step1, Create backupset/Instance for this testcase if it doesn't exist.
        Step2, For each of the allowed scan type
                do the following on the backupset/Instance
                Step2.1,  Create subclient for the scan type if it doesn't exist.
                 Step2.2,  Add full data for the current run.
                Step2.3,  Run a full backup for the subclient
                        and verify it completes without failures.
                Step2.4,  Lock List of files ..
                Step2.5, Validate Failures
                Step2.6, Wait until lock on files released
                Step2.7,  Add new data for the incremental
                Step2.8,  Run an incremental backup for the subclient
                        and verify it completes without failures.
                Step2.9, Validate Failures added back to collect
                Step2.10,  Run a restore of the  backup data
                        and verify correct data is restored.
                Step2.11, Run a synthfull job
                Step2.12,  Run a restore of the  backup data
                        and verify correct data is restored
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File System Data Protection"\
            " Failed Files "
        self.applicable_os = self.os_list.UNIX
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.verify_dc = None
        self.skip_classic = None
        self.client_machine = None
        self.acls = None
        self.unicode = None
        self.xattr = None
        self.long_path = None
        self.problematic = None
        self.WAIT_TIME = None
        self.RETAIN_DAYS = None
        self.should_wait = None
        self.is_client_big_data_apps = None
        self.is_client_network_share = None
        self.master_node = None
        self.data_access_nodes = None
        self.no_of_streams = None
        self.instance_name = None
        self.cleanup_run = None
        self.backupset_name = None

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        try:
            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            test_path = self.test_path
            slash_format = self.slash_format
            helper = self.helper
            machine = self.client_machine
            if test_path.endswith(slash_format):
                test_path = str(test_path).rstrip(slash_format)
            storage_policy = self.storage_policy



            log.info(
                """File System Data Protection - Full,Incremental,Differential
                This test case does the following
                Step1, Create backupset/Instance for this testcase if it doesn't exist.
                Step2, For all the allowed scan type do the following on the backupset/Instance
                Step2.1,  Create subclient for the scan type if it doesn't exist.
                 Step2.2,  Add full data for the current run.
                Step2.3,  Run a full backup for the subclient
                        and verify it completes without failures.
                Step2.4,  Lock List of files ..
                Step2.5, Validate Failures
                Step2.6, Wait until lock on files released
                Step2.7,  Add new data for the incremental
                Step2.8,  Run an incremental backup for the subclient
                        and verify it completes without failures.
                Step2.9, Validate Failures added back to collect 
                Step2.10,  Run a restore of the  backup data
                        and verify correct data is restored.
                Step2.11, Run a synthfull job
                Step2.12,  Run a restore of the  backup data
                        and verify correct data is restored
            """)

            if self.is_client_big_data_apps:
                log.info("Step1, Create Instance for "
                         "this testcase if it doesn't exist")
                instance_name = "Instance_" + self.id
                helper.create_instance(instance_name, delete=self.cleanup_run)
                self.instance_name = instance_name
            else:
                log.info("Step1, Create backupset for "
                         "this testcase if it doesn't exist")
                backupset_name = "backupset_" + self.id
                helper.create_backupset(backupset_name)
                self.backupset_name = backupset_name

            log.info("Step2, Executing steps for all the allowed scan type")
            for scan_type in ScanType:
                if scan_type.value == ScanType.OPTIMIZED.value:
                    continue
                elif scan_type.value == ScanType.CHANGEJOURNAL.value:
                    continue
                log.info("**STARTING RUN FOR " + scan_type.name + " SCAN**")
                log.info("Step2.1,  Create subclient for the scan type "
                         + scan_type.name + " if it doesn't exist.")
                subclient_name = ("subclient_"
                                  + self.id
                                  + "_"
                                  + scan_type.name.lower())
                subclient_content = []
                subclient_content.append(test_path
                                         + slash_format
                                         + subclient_name)

                tmp_path = (
                    test_path
                    + slash_format
                    + 'cvauto_tmp'
                    + slash_format
                    + subclient_name
                )

                run_path = (subclient_content[0]
                            + slash_format
                            + str(self.runid))

                full_data_path = run_path + slash_format + "full"

                helper.create_subclient(
                                        name=subclient_name,
                                        storage_policy=storage_policy,
                                        content=subclient_content,
                                        scan_type=scan_type
                                        )

                log.info("Step2.2,  Add full data for the current run.")

                log.info("Adding data under path:" + full_data_path)

                list_of_file_extentions=['.txt','.xml']
                helper.generate_testdata(list_of_file_extentions,path=full_data_path,no_of_files=10)
                full_data_path=full_data_path+"\\"
                list_of_paths = machine.get_items_list(full_data_path)
                sublist = []
                files_to_lock = []

                for file in list_of_paths:
                    filename, file_extension = os.path.splitext(file)

                    if file_extension == ".txt":
                        sublist.append(file)

                count_of_files = len(sublist)

                for x in range(0, (int(count_of_files)//2)):
                    files_to_lock.append(sublist[x])

                log.info("Files to be locked{}".format(files_to_lock))
                elements =len(files_to_lock)

                log.info ("Step2.3,  Lock List of files ..")

                # log.info("88888888888888888launching thread@@@@@@@@@@@@@@@@@@@@")
                # _thread.start_new_thread(machine.lock_files, ([files_to_lock]))
                machine.lock_files(files_to_lock)
                # wait for for journals to get flushed
                if self.should_wait:
                    log.info("Waiting for journals to get flushed")
                    sleep(self.WAIT_TIME)

                log.info("Step2.4,  Run a full backup for the subclient "
                         "and verify it completes without failures.")
                job_full = helper.run_backup_verify(scan_type, "Full", failed_case=True)[0]

                log.info("Step2.5, Validate Failures")
                log.info("Failed Files Validation Running")

                helper.validate_failed_files(files_to_lock,job="Failed")
                log.info("Failed Files Validation Successful")

                log.info("Step2.6, Wait until lock on files released, sleeping for 5 mins")
                sleep(400)

                log.info("Step2.7,  Add new data for the incremental")
                incr_diff_data_path = run_path + slash_format + "incr_diff"
                helper.add_new_data_incr(
                    incr_diff_data_path,
                    slash_format,
                    scan_type)

                log.info("Step2.8,  Run an incremental job for the subclient"
                         " and verify it completes without failures.")
                job_incr1 = helper.run_backup_verify(
                    scan_type, "Incremental")[0]

                log.info("**"
                         + scan_type.name
                         + " SCAN RUN COMPLETED SUCESSFULLY**")

                log.info("Step2.9, Validate Failures added back to collect")

                helper.validate_failed_files(files_to_lock)

                log.info(
                    "Step2.10,  Run a restore of the  backup data"
                    " and verify correct data is restored."
                )
                helper.run_restore_verify(
                    slash_format,
                    subclient_content[0],
                    tmp_path, subclient_name)

                log.info("Step2.11 Running Synthfull")

                helper.run_backup_verify(scan_type, "Synthetic_full")

                log.info("Running Restore from Synthfull")

                tmp_path = (
                    test_path
                    + slash_format
                    + 'cvauto_tmp'
                    + slash_format
                    + subclient_name
                )

                synthfull_restore_path = (
                    tmp_path
                    +slash_format
                    + 'Synthfull'
                )

                log.info(
                    "Step2.12,  Run a restore of the Synthfull  backup data"
                    " and verify correct data is restored."
                )
                helper.run_restore_verify(
                    slash_format,
                    subclient_content[0],
                    synthfull_restore_path, subclient_name)

            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED

        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED




