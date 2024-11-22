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
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper, ScanType, SoftwareCompression


class TestCase(CVTestCase):
    """Class for executing
        File System Data Protection - Full,Incremental,Differential
        This test case does the following
        Step1, Create backupset/Instance for this testcase if it doesn't exist.
        Step2, For each of the allowed scan type
                do the following on the backupset/Instance
            Step2.1,  Create subclient for the scan type if it doesn't exist.
                Step2.2, Add full data for the current run.
                Step2.3, Run a full backup for the subclient
                            and verify it completes without failures.
                Step2.4, Run a restore of the full backup data
                            and verify correct data is restored.
                Step2.5, Run a find operation for the full job
                            and verify the returned results.
                Step2.6, Add new data for the incremental
                Step2.7, Run an incremental backup for the subclient
                            and verify it completes without failures.
                Step2.8, Run a restore of the incremental backup data
                            and verify correct data is restored.
                Step2.9, Run a find operation for the incremental job
                            and verify the returned results.
                Step2.10, Perform all modifications on the existing data.
                Step2.11, Run an incremental backup for the subclient
                            and verify it completes without failures.
                Step2.12, Run a restore of the incremental backup data
                            and verify correct data is restored.
                Step2.13, Run a find operation for the incremental job
                            and verify the returned results.
                Step2.14, Add new data for the differential
                Step2.15, Run a differential backup for the subclient
                            and verify it completes without failures.
                Step2.16, Run a restore of the differential backup data
                            and verify correct data is restored.
                Step2.17, Run a find operation for the differential job
                            and verify the returned results.
                Step2.18, Add new data for the incremental
                Step2.19, Run a synthfull job
                Step2.20, Run an incremental backup after
                            synthfull for the subclient and
                            verify it completes without failures.
                Step2.21, Run a restore of the incremental backup data
                            and verify correct data is restored.
                Step2.22, Run a find operation for the incremental job
                            and verify the returned results.
                Step2.23, Perform all modifications on the existing data.
                Step2.24, Run a synthfull job
                Step2.25, Run an incremental backup after
                            synthfull for the subclient and
                            verify it completes without failures.
                Step2.26, Run a restore of the incremental backup data
                            and verify correct data is restored.
                Step2.27, Run a find operation for the incremental job
                            and verify the returned results.
                Step2.28, Add new data for differential after synthfull
                Step2.29, Run a differential backup for the subclient
                            and verify it completes without failures.
                Step2.30, Run a restore of the differential backup data
                            and verify correct data is restored.
                Step2.31, Run a find operation for the differential job
                            and verify the returned results.
                Step2.32, Run a restore of the complete subclient data
                            and verify correct data is restored.
                Step2.33, Run a find operation for the entire subclient
                            and verify the returned results.
        """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.suspend_interval_sce5 = int(self.tcinputs.get("SuspendIntervalSecsScenario5", 15))
        self.max_suspend_sce5 = int(self.tcinputs.get("MaxSuspendScenario5", 2))
        self.name = "File System Extent Level Backup - Basic Functionality"
        self.applicable_os = self.os_list.LINUX
        self.product = self.products_list.FILESYSTEM
        self.show_to_user = True
        self.tcinputs = {"TestPath": None, "StoragePolicyName": None}
        self.helper = None
        self.storage_policy = None
        self.slash_format = None
        self.test_path = None
        self.tmp_path = None
        self.runid = None
        self.id = None
        self.client_machine = None
        self.bset_name = None
        self.sc_name = None
        self.content = None
        self.run_path = None
        self.extent_path = None
        self.non_extent_path = None
        self.fsa = None
        self.enable = None
        self.slab = None
        self.slab_val = None
        self.threshold = None
        self.cleanup_run = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.helper = FSHelper(self)
        self.helper.populate_tc_inputs(self)
        self.bset_name = '_'.join(("backupset", str(self.id)))
        self.runid = str(self.runid)

        if self.client_machine.os_info == "UNIX":
            self.fsa = "FileSystemAgent"
            self.enable = "bEnableFileExtentBackup"
            self.slab = "mszFileExtentSlabs"
            self.slab_val = str(self.tcinputs.get("Slab", "101-1024=100"))
            self.test_path = "{0}{1}cv_fs_automation_{2}".format(
                self.test_path, self.slash_format, self.id)
            self.client_machine.remove_directory(self.test_path)

    def run(self):
        """Main function for test case execution"""
        try:
            def log_scenario_details(sce_num, scenario, beginning=True):
                """Prints scenario details.

                Args:
                    sce_num     (str)   --  Scenario number.

                    scenario    (str)   --  Scenario sequence.

                    beginning   (bool)  --  Determines if we're printing details
                    during the beginning or end of a scenario.

                Returns:
                    None

                Raises:
                    None

                """

                if beginning:
                    self.log.info("*************************")
                    self.log.info("{} BEGINS".format(sce_num))
                    self.log.info(scenario)
                else:
                    self.log.info("END OF {}".format(sce_num))
                    self.log.info("*************************")

            def initialize_scenario_attributes(sce_num):
                """Initializes attributes common to scenarios.

                Args:
                    sce_num (str)   --  Scenario number.

                Returns:
                    None

                Raises:
                    None

                """

                self.sc_name = '_'.join(("subclient", str(self.id), scan_type.name, sce_num))
                self.content = [self.slash_format.join((self.test_path, self.sc_name))]
                self.run_path = self.slash_format.join((self.content[0], self.runid))
                self.extent_path = self.slash_format.join((self.run_path, extent_files))
                self.non_extent_path = self.slash_format.join((self.run_path, non_extent_files))
                self.tmp_path = self.slash_format.join((self.test_path, "cvauto_tmp", self.sc_name, self.runid))

                self.common_args = {'name': self.sc_name,
                                    'content': self.content,
                                    'storage_policy': self.storage_policy,
                                    'software_compression': SoftwareCompression.OFF.value}

            self.log.info(self.__doc__)
            if self.client_machine.os_info == "UNIX":
                self.log.info("01 : Enable feature by setting {} under {} on client.".format(self.enable, self.fsa))
                self.client_machine.create_registry(self.fsa, self.enable, 1)
                self.log.info("02 : Lowering threshold by setting {} under {} on client.".format(self.slab, self.fsa))
                self.client_machine.create_registry(self.fsa, self.slab, self.slab_val)
            else:
                self.log.info("Skipping STEPS 01 and 02 since the OS is {}".format(self.client_machine.os_info))

            extent_files, non_extent_files, slash_format = "extent_files", "non_extent_files", self.slash_format
            self.log.info("03 : Create a new backupset")
            self.helper.create_backupset(self.bset_name)

            for scan_type in ScanType:
                if scan_type.name == "CHANGEJOURNAL":
                    self.log.info("{} scan method not supported, skipping test case execution".format(scan_type.name))
                    continue

                # *****************************************************
                # SCENARIO 1 BEGINS
                # *****************************************************
                sce_num = "SCENARIO_1_ACCEPTANCE"
                scenario = "Full -> OOP Restore -> Modify -> Incr. -> OOP Restore -> Synth. Full -> OOP Restore"
                log_scenario_details(sce_num, scenario)
                initialize_scenario_attributes(sce_num)

                self.log.info("4.01. Create a new subclient.")
                self.helper.create_subclient(scan_type=scan_type, **self.common_args)

                self.log.info("4.02. Create files that qualify for extent level backup as well as files that don't.")
                source_list = self.add_data_to_path(self.extent_path, extent_files=True, sparse=False, )
                self.add_data_to_path(self.non_extent_path, extent_files=False, sparse=False)

                self.log.info("4.03. Run a full backup and let it complete.")
                full_bkp = self.helper.run_backup_verify(backup_level="Full")[0]
                self.helper.run_find_verify(self.content[0], full_bkp)

                self.log.info("4.04. Ensure that the large file(s) are present in CollectTot*.cvf")
                res = self.helper.verify_collect_extent_acl(source_list, "FULL", acl=1)
                if not res:
                    raise Exception("Extent level validation failed, failing the test case")

                self.log.info("4.05. Restore the data backed up in the previous backup job out of place and verify.")
                self.helper.run_restore_verify(slash_format, self.run_path, self.tmp_path, self.runid, full_bkp)

                self.log.info("4.06. Modify content of the large files and run an incremental backup.")
                self.client_machine.modify_test_data(self.extent_path, modify=True)
                self.client_machine.modify_test_data(self.non_extent_path, modify=True)
                inc_bkp = self.helper.run_backup_verify(backup_level="Incremental")[0]

                self.log.info("4.07. Ensure that the large file(s) are present in CollectInc*.cvf.")
                res = self.helper.verify_collect_extent_acl(source_list, "INCREMENTAL", acl=1)
                if not res:
                    raise Exception("Extent level validation failed, failing the test case")

                self.log.info("4.08. Restore the data backed up in the previous backup job out of place and verify.")
                self.helper.run_restore_verify(slash_format, self.extent_path, self.tmp_path, extent_files, inc_bkp)

                self.log.info("4.09. Run a synthetic full backup.")
                sfull_bkp = self.helper.run_backup_verify(backup_level="Synthetic_full")[0]

                self.log.info("4.10. Restore the data backed up in the previous backup job out of place and verify.")
                self.helper.run_restore_verify(slash_format, self.run_path, self.tmp_path, self.runid, sfull_bkp)
                log_scenario_details(sce_num, scenario, beginning=False)

                # *****************************************************
                # SCENARIO 1 ENDS
                # *****************************************************

                # *****************************************************
                # SCENARIO 2 BEGINS
                # *****************************************************
                sce_num, scenario = "SCENARIO_2_THREE_STREAMS", "Full -> OOP Restore"
                log_scenario_details(sce_num, scenario)
                initialize_scenario_attributes(sce_num)

                self.log.info("5.01. Create a new subclient.")
                self.helper.create_subclient(scan_type=scan_type, data_readers=3, **self.common_args)

                self.log.info("5.02. Create a single large file that qualifies for extent level backup.")
                source_list = self.add_data_to_path(self.extent_path, extent_files=True, sparse=False)
                self.add_data_to_path(self.non_extent_path, extent_files=False, sparse=False)

                self.log.info("5.03. Run a full backup using more than 2 streams and let it complete.")
                full_bkp = self.helper.run_backup_verify(backup_level="Full")[0]
                self.helper.run_find_verify(self.content[0], full_bkp)

                self.log.info("5.04. Ensure that the large file is present in ColTot*.cvf.")
                res = self.helper.verify_collect_extent_acl(source_list, "FULL", acl=1)
                if not res:
                    raise Exception("Extent level validation failed, failing the test case")

                self.log.info("5.05.  Restore the data backed up in the previous backup job out of place and verify.")
                self.helper.run_restore_verify(slash_format, self.run_path, self.tmp_path, self.runid, full_bkp)

                log_scenario_details(sce_num, scenario, beginning=False)

                # *****************************************************
                # SCENARIO 2 ENDS
                # *****************************************************

                # ******************************************************
                # SCENARIO 3 BEGINS
                # ******************************************************
                sce_num, scenario = "SCENARIO_3_SPARSE_FILES", "Create Sparse Files -> Full -> OOP Restore"
                log_scenario_details(sce_num, scenario)
                initialize_scenario_attributes(sce_num)
                self.log.info("7.01. Create a new subclient.")
                self.helper.create_subclient(scan_type=scan_type, **self.common_args)
                self.log.info("7.02. Create a few sparse files such with the following specifications.")
                self.log.info("The sparse range spans across extents and is present in the middle of the file.")
                source_list = self.add_data_to_path(self.extent_path, extent_files=True, sparse=True)
                self.add_data_to_path(self.non_extent_path, extent_files=False, sparse=False)
                self.log.info("7.03. Run a full backup and let it complete.")
                full_bkp = self.helper.run_backup(backup_level="Full")[0]

                self.log.info("7.04. Ensure that the large file(s) are present in ColTot*.cvf.")
                res = self.helper.verify_collect_extent_acl(source_list, "FULL", acl=1)
                if not res:
                    raise Exception("Extent level validation failed, failing the test case")

                self.log.info("7.05. Restore the data backed up in the previous backup job out of place and verify")
                self.helper.run_restore_verify(slash_format, self.run_path, self.tmp_path, self.runid, full_bkp)

                log_scenario_details(sce_num, scenario, beginning=False)
                # **************************************************
                # SCENARIO 3 ENDS
                # **************************************************

                # **************************************************
                # SCENARIO 4 BEGINS
                # **************************************************

                self.current_suspend = 1
                sce_num = "SCENARIO_4_SYNTH_FULL"
                scenario = "Full -> Synthetic Full (Suspend, Resume, Suspend, Resume) -> OOP Restore -> OOP Restore"
                log_scenario_details(sce_num, scenario)
                initialize_scenario_attributes(sce_num)

                self.log.info("8.01. Create a new subclient.")
                self.helper.create_subclient(scan_type=scan_type, **self.common_args)

                self.log.info("8.02. Create files that qualify for extent level backup as well as files that don't.")
                source_list = self.add_data_to_path(self.extent_path, extent_files=True, sparse=False)
                self.add_data_to_path(self.non_extent_path, extent_files=False, sparse=False)

                self.log.info("8.03. Run a full backup and let it complete.")
                full_bkp = self.helper.run_backup(backup_level="Full")[0]

                self.log.info("8.04. Ensure that the large file(s) are present in ColTot*.cvf.")
                res = self.helper.verify_collect_extent_acl(source_list, "FULL", acl=1)
                if not res:
                    raise Exception("Extent level validation failed, failing the test case")
                self.log.info("8.05 Run incremental with scan marking")
                inc_bkp = self.helper.run_backup_verify(backup_level = "Incremental")[0]
                self.log.info("8.06. Run a synthetic full backup, suspend and resume when it's in progress.")
                sfull_bkp = self.helper.run_backup(backup_level="Synthetic_full", wait_to_complete=False)[0]
                self.current_suspend = 1
                while self.current_suspend <= self.max_suspend_sce5:
                    while True:
                        # WAIT TILL BACKUP PHASE BEGINS AND ITS STATUS IS RUNNING
                        if (sfull_bkp.status).upper() == "RUNNING":
                            break
                        elif (sfull_bkp.status).upper() == "COMPLETED" or self.current_suspend == self.max_suspend_sce5:
                            self.current_suspend = 999
                            break
                    self.log.info("Waiting {} seconds before suspending".format(self.suspend_interval_sce5))
                    sleep(self.suspend_interval_sce5)
                    self.log.info("Synthetic full will be suspended now.")
                    sfull_bkp.pause(wait_for_job_to_pause=True)
                    self.current_suspend += 1
                    sfull_bkp.resume()

                    self.log.info("Waiting {} seconds before suspending".format(self.suspend_interval_sce5))
                    sleep(self.suspend_interval_sce5)
                    self.log.info("Synthetic full will be suspended now.")
                    sfull_bkp.pause(wait_for_job_to_pause=True)
                    self.current_suspend += 1
                    sfull_bkp.resume()

                sfull_bkp.resume()
                sfull_bkp.wait_for_completion()

                self.log.info("8.07. Restore the data from the synthetic full backup out of place and verify.")
                self.helper.run_restore_verify(slash_format, self.run_path, self.tmp_path, self.runid, sfull_bkp)

                log_scenario_details(sce_num, scenario, beginning=False)
                # *****************************************************
                # SCENARIO 4 ENDS
                # *****************************************************

            # DELETING TEST DATASET
                self.client_machine.remove_directory(self.test_path)

            # DELETING BACKUPSET
            self.instance.backupsets.delete(self.bset_name)

        except Exception as excp:
            error_message = "Failed with error: {}".format(str(excp))
            self.log.error(error_message)
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        if self.client_machine.os_info == "UNIX":
            remove_msg = "Removing registry entries {} and {} under {}".format(self.enable, self.slab, self.fsa)
            self.log.info(remove_msg)
            self.client_machine.remove_registry(self.fsa, self.enable)
            self.client_machine.remove_registry(self.fsa, self.slab)

    def add_data_to_path(self, full_data_path, extent_files=False, sparse=False):
        """Add files to the folder path and return the list of files added to be Backed-up
                    Args :
                        :param extent_files:        bool       --   Creates the extent files
                        :param full_data_path:      (str)      --   Folder path to create the files
                        :param sparse:              bool       --   Creates the the sparse files
                    Return:
                        list of files to be Backed-up
            """
        machine = self.client_machine
        slash_format = self.slash_format
        list_of_files = []
        list_of_non_extent_files = []
        machine.create_directory(full_data_path)
        if extent_files:
            if sparse:
                for i in range(1, 9):
                    file_name = "{0}{1}{2}.txt".format(full_data_path, slash_format, str(i))
                    list_of_files.append(file_name)
                    command = "dd if=/dev/zero of={0} bs=2148k seek=1b count=0".format(file_name)
                    machine.execute(command)
            else:
                for i in range(1, 9):
                    file_name = "{0}{1}{2}.txt".format(full_data_path, slash_format, str(i))
                    list_of_files.append(file_name)
                    command = "dd if=/dev/urandom of={0} count=1124 bs=1048576".format(file_name)
                    machine.execute(command)
        else:
            for i in range(1, 3):
                file_name = "{0}{1}{2}.doc".format(full_data_path, slash_format, str(i))
                list_of_non_extent_files.append(file_name)
                command = "dd if=/dev/urandom of={0} count=1 bs=1048".format(file_name)
                machine.execute(command)

        self.log.info("List of files that doesnt qualify for extent backup: %s", list_of_non_extent_files)
        self.log.info("List of extent qualified files: %s", list_of_files)
        return list_of_files
