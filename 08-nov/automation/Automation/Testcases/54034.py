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
from AutomationUtils.unix_machine import UnixMachine
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper


class TestCase(CVTestCase):
    """Class for executing
        File System Data Protection - Full,Incremental, for backup only ACL
        This test case does the following
        Step1, Create backupset for this testcase if it doesn't exist.
        Step2, For each of the allowed scan type
                do the following on the backupset
            Step2.1,  Create subclient for the scan type if it doesn't exist.
                Step2.2, Add full data for the current run.
                Step2.3, Run a full backup for the subclient
                            and verify it completes without failures.
                Step2.4, Verify collect files if the files are backed up
                            as extents.
                Step2.5, Run a restore and verify the returned results.
                Step2.6, Change the permissions for text files for the incremental
                Step2.7, Run an incremental backup for the subclient
                            and verify it completes without failures.
                Step2.8, Verify collect files and ensure only container files are backed up
                Step2.9, Run a restore of the incremental backup data
                            and verify correct data is restored.
                Step2.10, Modify data of few files and only permissions for existing files
                Step2.11, Run incremental backup and verify it completes without failures
                step2.12, Verify collect files for newly added data and acl only list
                step2.13, Run restore and verify the returned results

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File System Data Protection" \
                    " - Full,Incremental"
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
        self.WAIT_TIME = None
        self.RETAIN_DAYS = None
        self.should_wait = None
        self.fsa = None
        self.enable = None

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

            if self.client_machine.os_info == "UNIX":
                self.fsa = "FileSystemAgent"
                self.enable = "nACLOnlyBackup"
                self.log.info("Setting ACL backup registry, Extent backup registry and extent size slab")
                self.client_machine.create_registry(self.fsa, self.enable, 1)
                self.client_machine.create_registry(self.fsa, "bEnableFileExtentBackup", 1)
                self.client_machine.create_registry(self.fsa, "mszFileExtentSlabs", "1-1024=10")
                self.test_path = "{0}{1}cv_fs_automation_{2}".format(self.test_path, self.slash_format, self.id)
                test_path = self.test_path
                self.client_machine.remove_directory(self.test_path)
            log.info("Step1, Create backupset for "
                     "this testcase if it doesn't exist")
            backupset_name = "backupset_{0}".format(self.id)
            helper.create_backupset(backupset_name)

            log.info("Step2, Executing steps for all the allowed scan type")
            for scan_type in ScanType:
                # SKip chain journal scan for Unix
                if (self.applicable_os != 'WINDOWS'
                        and scan_type.value == ScanType.CHANGEJOURNAL.value):
                    continue
                # Skip DC if verify_dc is not provided
                if (self.applicable_os != 'WINDOWS'
                        and scan_type.value == ScanType.OPTIMIZED.value):
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
                        + slash_format
                        + str(self.runid)
                )

                run_path = (subclient_content[0]
                            + slash_format
                            + str(self.runid))

                full_data_path = "{0}{1}full".format(run_path, slash_format)

                helper.create_subclient(name=subclient_name,
                                        storage_policy=storage_policy,
                                        content=subclient_content,
                                        scan_type=scan_type)

                log.info("Step 2.2 Adding data under path: {0}".format(full_data_path))
                list_of_source_files, list_text_files, list_pdf_files = \
                    self.add_data_to_path(full_data_path)

                # wait for for journals to get flushed
                if self.should_wait:
                    log.info("Waiting for journals to get flushed")
                    sleep(self.WAIT_TIME)
                #
                log.info("Step2.3,  Run a full backup for the subclient "
                         "and verify it completes without failures.")
                job_full = helper.run_backup_verify(scan_type, "Full")[0]

                log.info("Step2.4, Verify Collect files for extent based back up.")
                collect_result = self.helper.verify_collect_extent_acl(list_of_source_files, "FULL", 1)
                if not collect_result:
                    raise Exception("Collect file verification failed")
                log.info("Step2.5,  Run a restore of the full backup data "
                         "and verify correct data is restored.")

                helper.run_restore_verify(
                    slash_format,
                    full_data_path,
                    tmp_path, "full", job_full)
                log.info("Step2.6, Change permisssions on the source:")
                # Changing permissions for existing files
                for i in list_text_files:
                    self.log.info(i)
                    cmd = "chmod 777 {0}".format(i)
                    machine.execute(cmd)

                log.info("Step2.7,  Run incremental backup for the subclient "
                         "and verify it completes without failures.")
                job_Inc = helper.run_backup_verify(scan_type, "Incremental")[0]
                log.info("Step 2.8, Verify collect files for only ACLs:")
                collect_result = self.helper.verify_collect_extent_acl(list_text_files, "INCREMENTAL", 2)

                if not collect_result:
                    raise Exception("Collect file verification failed")
                log.info("Step2.9,  Run a restore of the incremental backup data"
                         " and verify correct data is restored.")

                inc_data_path = full_data_path + "/text_dir"

                helper.run_restore_verify(
                    slash_format,
                    inc_data_path,
                    tmp_path, "text_dir", job_Inc)

                log.info("Step2.10, Modifying data for few files and changing permissions for "
                         "few files under path: {0}".format(full_data_path))
                for i in list_text_files:
                    self.log.info(i)
                    cmd = "dd if=/dev/urandom of={0} count=1024 bs=10240".format(i)
                    machine.execute(cmd)

                for i in list_pdf_files:
                    cmd = "chmod 711 {0}".format(i)
                    machine.execute(cmd)

                list_of_source_files = list_pdf_files + list_text_files
                log.info("S")
                job_Inc = helper.run_backup_verify(scan_type, "Incremental")[0]
                self.log.info("list of source files: ")
                self.log.info(list_of_source_files)
                collect_result = self.helper.verify_collect_extent_acl(
                    list_of_source_files, "INCREMENTAL", 3)
                if not collect_result:
                    raise Exception("Collect file verification failed")

                self.log.info("Performing restore from incremental job:")
                helper.run_restore_verify(
                    slash_format,
                    full_data_path,
                    tmp_path, "full")
                machine.remove_directory(tmp_path)
            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED

        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        if self.client_machine.os_info == "UNIX":
            self.log.info("Removing ACL backup/Extent based backup registry")
            self.client_machine.remove_registry(self.fsa, self.enable)
            self.client_machine.remove_registry(self.fsa, "bEnableFileExtentBackup")
            self.client_machine.remove_registry(self.fsa, "mszFileExtentSlabs")
            self.client_machine.remove_directory(self.test_path)


    def add_data_to_path(self, full_data_path):
        """"Add files to the folder path and return the list of files added to be Backed-up
                    Args :
                        full_data_path      (str)           --  Folder path to create the files

                    Return:
                        list of files to be Backed-up

            """
        machine = self.client_machine

        slash_format = self.slash_format
        list_of_files = []
        list_text_files = []
        list_pdf_files = []
        machine.create_directory(full_data_path)
        text_dir = full_data_path + slash_format + "text_dir"
        machine.create_directory(text_dir)
        pdf_dir = full_data_path + slash_format + "pdf_dir"
        machine.create_directory(pdf_dir)

        for i in range(1, 5):
            file_name = "{0}{1}{2}.txt".format(text_dir, slash_format, str(i))
            list_of_files.append(file_name)
            list_text_files.append(file_name)
            command = "dd if=/dev/urandom of={0} count=1024 bs=10240".format(file_name)
            machine.execute(command)
        for i in range(1, 5):
            file_name = "{0}{1}{2}.pdf".format(pdf_dir, slash_format, str(i))
            list_of_files.append(file_name)
            list_pdf_files.append(file_name)
            command = "dd if=/dev/urandom of={0} count=1024 bs=10240".format(file_name)
            machine.execute(command)

        self.log.info("Source files:")
        self.log.info(list_of_files)
        return list_of_files, list_text_files, list_pdf_files
