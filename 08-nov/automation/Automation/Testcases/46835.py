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
__init__()                                      --  Initialize TestCase class

run()                                           --  run function of this test case

run_backup_cycle()                              -- function run the whole backup cycle
( Full -> Incr -> Incr -> Incr -> Synthfull -> Incr )

check_with_subclient_content_without_wild_cards	-- function will create subclient content without
wildcard i.e., /testpath/subclientName

check_with_subclient_content_with_wild_cards    -- function will create subclient content with
wildcard i.e., /testapth/**/subclientName

"""

from time import sleep
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper

class TestCase(CVTestCase):
     """
           File System Backup Scan Marking Job
            This test case does the following
            1. Create backupset for this testcase if it doesn't exist.
            2. For SubClient whcih has normal path as SubClient Content
                2.1. For all the allowed scan type do the following on the backupset
                    2.1.1  Create subclient for the scan type if it doesn't exist.
                    2.1.2  Add full data for the current run.
                    2.1.3  Run a full backup for the subclient and verify it completes without failures
                    2.1.4  Without changing any data run a Incremental Job
                    2.1.5  Add new data for the incremental
                    2.1.6  Run an incremental backup for the subclient and verify it completes without failures.
                    2.1.7  Without changing any data run a Incremental Job
                    2.1.8  Run a synthfull job
                    2.1.9  Run an incremental backup after synthfull  and verify it completes without failures.

            3. Subclient which has Subclient Content as wildcards
                3.1. For all the allowed scan type do the following on the backupset
                    3.1.1  Create subclient for the scan type if it doesn't exist.
                    3.1.2  Add full data for the current run.
                    3.1.3  Run a full backup for the subclient and verify it completes without failures
                    3.1.4  Without changing any data run a Incremental Job
                    3.1.5  Add new data for the incremental
                    3.1.6  Run an incremental backup for the subclient and verify it completes without failures.
                    3.1.7  Without changing any data run a Incremental Job
                    3.1.8  Add new data under filtered path( file not eligible for Backup )
                    3.1.9  Run an incremental backup for the subclient and verify it completes without failure
                    3.1.10 Run a synthfull job
                    3.1.11 Run an incremental backup after synthfull  and verify it completes without failures.
        """

     def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File System Backup Scan Marking Job"
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

     def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        try:
            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            log.info("""File System Backup Scan Marking Job
                            This test case does the following
                            1. Create backupset for this testcase if it doesn't exist.

                            2. For SubClient whcih has normal path as SubClient Content
                                2.1. For all the allowed scan type do the following on the backupset
                                    2.1.1  Create subclient for the scan type if it doesn't exist.
                                    2.1.2  Add full data for the current run.
                                    2.1.3  Run a full backup for the subclient and verify it completes without failures
                                    2.1.4  Without changing any data run a Incremental Job
                                    2.1.5  Add new data for the incremental
                                    2.1.6  Run an incremental backup  and verify it completes without failures.
                                    2.1.7  Without changing any data run a Incremental Job
                                    2.1.8  Run a synthfull job
                                    2.1.9  Run an incremental backup after synth and verify it completes without failure

                            3. Subclient which has Subclient Content as wildcards 
                                3.1. For all the allowed scan type do the following on the backupset
                                    3.1.1  Create subclient for the scan type if it doesn't exist.
                                    3.1.2  Add full data for the current run.
                                    3.1.3  Run a full backup for the subclient and verify it completes without failures
                                    3.1.4  Without changing any data run a Incremental Job
                                    3.1.5  Add new data for the incremental
                                    3.1.6  Run an incremental backup and verify it completes without failures.
                                    3.1.7  Without changing any data run a Incremental Job
                                    3.1.8  Add new data under filtered path( file not eligible for Backup )
                                    3.1.9  Run an incremental backup and verify it completes without failure
                                    3.1.10 Run a synthfull job
                                    3.1.11 Run an incremental backup after synth and verify it completes without failure
                        """)

            #Check with Sub client Content where content has no filters
            self.check_with_subclient_content_without_wild_cards()

            #Check with Sub client where content has filters
            self.check_with_subclient_content_with_wild_cards()

            self.status = constants.PASSED

        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED



     def check_with_subclient_content_without_wild_cards(self):
        """Runs Scan Marking Validation Case without the wild cards in Scan Content
         Return:
             None
         Raises :
            Exception:
                If Job didn't run Scan Marking Job...
        """

        test_path = self.test_path
        slash_format = self.slash_format
        helper = self.helper
        machine = self.client_machine
        if test_path.endswith(slash_format):
            test_path = str(test_path).rstrip(slash_format)
        storage_policy = self.storage_policy

        self.log.info("Create backupset for this testcase if it doesn't exist")
        backupset_name = "backupset_" + self.id
        helper.create_backupset(backupset_name)

        self.log.info("Executing steps for all the allowed scan type")
        for scan_type in ScanType:
            # Skip Change Journal for UUnx
            if (self.applicable_os != 'WINDOWS' and scan_type.value == ScanType.CHANGEJOURNAL.value):
                continue
            # Skip DC if verify_dc is not provided
            if (self.applicable_os != 'WINDOWS' and scan_type.value == ScanType.OPTIMIZED.value):
                if not self.verify_dc:
                    continue

            # Skip Classic scan if specified in inputs
            is_recursive = scan_type.value == ScanType.RECURSIVE.value
            if (self.skip_classic and is_recursive):
                continue
    
            # Check if We need to wait for I/O to get flushed
            self.should_wait = True
            if is_recursive:
                if self.applicable_os == 'UNIX':
                    if 'darwin' not in machine.os_flavour.lower():
                        self.should_wait = False
               
            self.log.info("**** Check With SubClient Content Without Filters****" )
            self.log.info("**STARTING RUN FOR " + scan_type.name + " SCAN**")
            self.log.info("Create subclient for the scan type " + scan_type.name + " if it doesn't exist.")
            
            subclient_name = ("subclient_{0}_{1}".format(self.id, scan_type.name.lower()))
            
            subclient_content = []
            subclient_content.append("{0}{1}{2}".format(test_path, slash_format, subclient_name))

            run_path = ("{0}{1}{2}".format(subclient_content[0], slash_format, str(self.runid)))

            full_data_path = ("{0}{1}full".format(run_path, slash_format))

            helper.create_subclient(name=subclient_name,
                                    storage_policy=storage_policy,
                                    content=subclient_content,
                                    scan_type=scan_type)

            self.log.info("Add full data for the current run.")

            self.log.info("Adding data under path: {0}".format(full_data_path))
            machine.generate_test_data(
                    full_data_path,
                    acls=self.acls,
                    unicode=self.unicode,
                    xattr=self.xattr,
                    long_path=self.long_path,
                    problematic=self.problematic
                )

            # wait for for journals to get flushed
            if self.should_wait:
                self.log.info("Waiting for journals to get flushed")
                sleep(self.WAIT_TIME)
    
            self.run_backup_cycle(run_path, scan_type, None)

        machine.remove_directory(test_path)



     def check_with_subclient_content_with_wild_cards(self):
        """"Runs Scan Marking Validation Case with the wild cards in Scan Content

        Return:
            None
        Raises :
            Exception:
                If Job didn't run Scan Marking Job...
        """
        test_path = self.test_path
        slash_format = self.slash_format
        helper = self.helper
        machine = self.client_machine
        if test_path.endswith(slash_format):
            test_path = str(test_path).rstrip(slash_format)
        storage_policy = self.storage_policy

        self.log.info("Create backupset for this testcase if it doesn't exist")
        backupset_name = "backupsetWithFilters_{0}".format(self.id)
        helper.create_backupset(backupset_name)

        self.log.info("Executing steps for all the allowed scan type")
        for scan_type in ScanType:
          
            # Skip Change Journal for UUnx
            if (self.applicable_os != 'WINDOWS' and scan_type.value == ScanType.CHANGEJOURNAL.value):
                continue
            # Skip DC if verify_dc is not provided
            if (self.applicable_os != 'WINDOWS' and scan_type.value == ScanType.OPTIMIZED.value):
                if not self.verify_dc:
                    continue

            # Skip Classic scan if specified in inputs
            is_recursive = scan_type.value == ScanType.RECURSIVE.value
            if (self.skip_classic and is_recursive):
                continue

            # Check if We need to wait for I/O to get flushed
            self.should_wait = True
            if is_recursive:
                if self.applicable_os == 'UNIX':
                    if 'darwin' not in machine.os_flavour.lower():
                        self.should_wait = False
                
            self.log.info("**** Check With SubClient Content With Filters****")
            self.log.info("**STARTING RUN FOR {0} SCAN**".format(scan_type.name))
            self.log.info("Create subclient for the scan type {0} if it doesn't exist.".format(scan_type.name))
            
            subclient_name = ("subclient_{0}_{1}".format(self.id, scan_type.name.lower()))
            subclient_content = []
            path = "{0}{1}ContentWithFilters".format(test_path, slash_format)

            machine.create_directory(path)

            subclient_content.append("{0}{1}**{2}{3}".format(test_path, slash_format, slash_format, subclient_name))

            sub_client_content = "{0}{1}{2}".format(path, slash_format, subclient_name)

            run_path = ("{0}{1}{2}".format(sub_client_content, slash_format, str(self.runid)))

            full_data_path = "{0}{1}full".format(run_path, slash_format)

            helper.create_subclient(name=subclient_name,
                                        storage_policy=storage_policy,
                                        content=subclient_content,
                                        scan_type=scan_type)

            self.log.info("Add full data for the current run.")

            self.log.info("Adding data under path: {0}".format(full_data_path))
            machine.generate_test_data(
                                full_data_path,
                                acls=self.acls,
                                unicode=self.unicode,
                                xattr=self.xattr,
                                long_path=self.long_path,
                                problematic=self.problematic
                                )

            # wait for for journals to get flushed
            if self.should_wait:
                self.log.info("Waiting for journals to get flushed")
                sleep(self.WAIT_TIME)

            self.run_backup_cycle(run_path, scan_type, path)

        machine.remove_directory(test_path)


     def run_backup_cycle(self, run_path, scan_type, filtered_path):
        """"Runs Whole Backup Cycle i.e., Full -> Incremental -> Incremental -> Synth Full -> Incremental
            Args :
                run_path			(str)               --  Folder which is to be backed-up

                scan_type			(ScanType)          --  scan type as one of the below
                                                    RECURSIVE
                                                    OPTIMIZED
                                                    CHANGEJOURNAL

                filtered_path		(str)				--  path which is filtered while using wildcards as Scan-content
                                                default : None

            Return:
                None

            Raises :
                    Exception:
                        If Job didn't run Scan Marking Job...
        """
        slash_format = self.slash_format
        helper = self.helper
        self.log.info("Run a full backup for the subclient and verify it completes without failures.")
        helper.run_backup_verify(scan_type, "Full")

        self.log.info("Without changing any data run a Incremental Job")
        job_incr1 = helper.run_backup_verify(scan_type, "Incremental", scan_marking=True)
        self.log.info("Job[" + job_incr1[0].job_id + "] ran as Scan Marking Job")
        self.log.info("Add new data for the incremental")
        incr_diff_data_path = run_path + slash_format + "incr_diff"
        helper.add_new_data_incr(incr_diff_data_path, slash_format, scan_type)
        self.log.info("Run an incremental job for the subclient and verify it completes without failures.")
        helper.run_backup_verify(scan_type, "Incremental")
        self.log.info("Without changing any data run a Incremental Job")
        job_incr2 = helper.run_backup_verify(scan_type, "Incremental", scan_marking=True)
        self.log.info("Job[" + job_incr2[0].job_id + "] ran as Scan Marking Job")
        if filtered_path != None:
            self.log.info("Running with Filter")
            self.log.info("Add new data for the incremental")
            helper.add_new_data_incr(filtered_path, slash_format, scan_type)
            job_incr3 = helper.run_backup_verify(scan_type, "Incremental", scan_marking=True)
            self.log.info("Incremental backup Job[" + job_incr3[0].job_id + "] after adding data under filtered path ran as Scan Marking Job")
        self.log.info("Run a synthfull job")
        helper.run_backup_verify(scan_type, "Synthetic_full")
        self.log.info("Run an incremental backup after synthfull for the subclient and verify it completes without failures.")
        job_incr4 = helper.run_backup_verify(scan_type, "Incremental", scan_marking=True)
        self.log.info("Incremental backup Job[" + job_incr4[0].job_id + "] after Synthull ran as Scan Marking Job")
