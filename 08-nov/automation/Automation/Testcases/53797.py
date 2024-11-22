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
    __init__()  --  Initialize TestCase class.

    setup()     --  Initializes pre-requisites for this test case.

    run()       --  Executes the test case steps.

    teardown()  --  Performs final clean up after test case execution.

"""
from time import sleep
from random import randint
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, CommitCondition, SoftwareCompression
from FileSystem.FSUtils.winfshelper import WinFSHelper
from FileSystem.FSUtils.unixfshelper import UnixFSHelper


class TestCase(CVTestCase):
    """Class for executing

    File System Extent Level Backup - Basic Functionality
    This test case will verify the basic functionality of FS extent level backup.
    This test case does the following.

    01. Enable feature by setting bEnableFileExtentBackup (DWORD,1) under FileSystemAgent on client.
    02. Lower threshold by setting mszFileExtentSlabs (REG_MULTI_SZ,101-1024=100) under FileSystemAgent on client.
    03. Create a new backupset

    SCENARIO 1 BEGINS
    4.01. Create a new subclient.
    4.02. Create files that qualify for extent level backup as well as files that don't.
    4.03. Run a full backup and let it complete.
    4.04. Ensure that the large file(s) are present in FileExtentEligibleNumColTot*.cvf.
    4.05. Restore the data backed up in the previous backup job out of place and verify.
    4.06. Modify content of the large files and run an incremental backup.
    4.07. Ensure that the large file(s) are present in FileExtentEligibleNumColInc*.cvf.
    4.08. Restore the data backed up in the previous backup job out of place and verify.
    4.09. Run a synthetic full backup.
    4.10. Restore the data backed up in the previous backup job out of place and verify.
    SCENARIO 1 ENDS

    SCENARIO 2 BEGINS
    5.01. Create a new subclient.
    5.02. Create a single large file that qualifies for extent level backup.
    5.03. Run a full backup using more than 2 streams and let it complete.
    5.04. Ensure that the large file is present in FileExtentEligibleNumColTot*.cvf.
    5.05. Restore the data backed up in the previous backup job out of place and verify.
    SCENARIO 2 ENDS

    SCENARIO 3 BEGINS
    6.01. Create a new subclient.
    6.02. Create files that qualify for extent level backup as well as files that don't.
    6.03. Run a full backup and commit it.
    6.04. Ensure that the large file(s) are present in FileExtentEligibleNumColTot*.cvf.
    6.05. Run an incremental backup and let it complete.
    6.06. Restore latest data out of place and verify.
    SCENARIO 3 ENDS

    SCENARIO 4 BEGINS
    7.01. Create a new subclient.
    7.02. Create a few sparse files such with the following specifications.
          The sparse range spans across extents and is present in the middle of the file.
          The sparse range is less than the size of an extent and is present in the middle of the file.
    7.03. Run a full backup and let it complete.
    7.04. Ensure that the large file(s) are present in FileExtentEligibleNumColTot*.cvf.
    7.05. Restore the data backed up in the previous backup job out of place and verify.
    SCENARIO 4 ENDS

    SCENARIO 5 BEGINS
    8.01. Create a new subclient.
    8.02. Create files that qualify for extent level backup as well as files that don't.
    8.03. Run a full backup and let it complete.
    8.04. Run a synthetic full backup, suspend and resume when it's in progress.
    8.05. Restore the data from the synthetic full backup out of place and verify.
    SCENARIO 5 ENDS

    SCENARIO 6 BEGINS
    9.01. Create a new subclient.
    9.02. Create a few files such with the hidden and/or read only attributes set.
    9.03. Run a full backup and let it complete.
    9.04. Ensure that the large file(s) are present in FileExtentEligibleNumColTot*.cvf.
    9.05. Restore the data backed up in the previous backup job out of place and verify.
    SCENARIO 6 ENDS

    SCENARIO 7 BEGINS
    10.01. Create a new subclient.
    10.02. Create a single large PST file.
    10.03. Run a full backup and let it complete.
    10.04. Ensure that the large file(s) are present in FileExtentEligibleNumColTot*.cvf.
    10.05. Restore the data backed up in the previous backup job out of place and verify.
    SCENARIO 7 ENDS
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File System Extent Level Backup - Basic Functionality"
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
        self.RETAIN_DAYS = None
        self.username = None
        self.password = None
        self.data_access_nodes = None

        # SCENARIO 1 INPUTS
        self.size_sce1 = None
        self.num_files_sce1 = None

        # SCENARIO 2 INPUTS
        self.size_sce2 = None
        self.num_streams_sc2 = None

        # SCENARIO 3 INPUTS
        self.size_sce3 = None
        self.num_files_sce3 = None
        self.commit_threshold = None

        # SCENARIO 4 INPUTS
        self.size_sce4 = None
        self.hole_size_1_sce4 = None
        self.hole_offset_1_sce4 = None
        self.hole_size_2_sce4 = None
        self.hole_offset_2_sce4 = None

        # SCENARIO 5 INPUTS
        self.size_sce5 = None
        self.num_files_sce5 = None
        self.max_suspend_sce5 = None
        self.suspend_interval_sce5 = None
        self.current_suspend = None

        # SCENARIO 6 INPUTS
        self.size_sce6 = None

        # SCENARIO 7 INPUTS
        self.size_sce7 = None

    def setup(self):
        """Initializes pre-requisites for this test case"""

        self.helper = WinFSHelper(self)
        self.helper.populate_tc_inputs(self)
        self.bset_name = '_'.join(("backupset", str(self.id)))
        self.runid = str(self.runid)

        # SCENARIO 1 INPUTS
        self.size_sce1 = int(self.tcinputs.get("FileSizeInKBScenario1", 256000))
        self.num_files_sce1 = int(self.tcinputs.get("NumFilesScenario1", 1))

        # SCENARIO 2 INPUTS
        self.size_sce2 = int(self.tcinputs.get("FileSizeInKBScenario2", 1048576))
        self.num_streams_sc2 = int(self.tcinputs.get("NumberOfStreamsScenario2", 6))

        # SCENARIO 3 INPUTS
        self.size_sce3 = int(self.tcinputs.get("FileSizeInKBScenario3", 256000))
        self.num_files_sce3 = int(self.tcinputs.get("NumFilesScenario3", 10))
        self.commit_threshold = int(self.tcinputs.get("CommitThreshold", randint(1, 4)))

        # SCENARIO 4 INPUTS
        self.size_sce4 = int(self.tcinputs.get("FileSizeInKBScenario4", 512000))
        self.hole_size_1_sce4 = int(self.tcinputs.get("HoleSize1InKBScenario4", 153600))
        self.hole_offset_1_sce4 = int(self.tcinputs.get("HoleOffset1InKBScenario4", 51200))
        self.hole_size_2_sce4 = int(self.tcinputs.get("HoleSize2InKBScenario4", 51200))
        self.hole_offset_2_sce4 = int(self.tcinputs.get("HoleOffset2InKBScenario4", 225280))

        # SCENARIO 5 INPUTS
        self.size_sce5 = int(self.tcinputs.get("FileSizeInKBScenario5", 256000))
        self.num_files_sce5 = int(self.tcinputs.get("NumFilesScenario5", 20))
        self.max_suspend_sce5 = int(self.tcinputs.get("MaxSuspendScenario5", 2))
        self.suspend_interval_sce5 = int(self.tcinputs.get("SuspendIntervalSecsScenario5", 25))
        self.current_suspend = 1

        # SCENARIO 6 INPUTS
        self.size_sce6 = int(self.tcinputs.get("FileSizeInKBScenario6", 312640))

        # SCENARIO 7 INPUTS
        self.size_sce7 = int(self.tcinputs.get("FileSizeInKBScenario7", 312640))

        self.fsa = "FileSystemAgent"
        self.enable = "bEnableFileExtentBackup"
        self.slab = "mszFileExtentSlabs"
        self.slab_val = str(self.tcinputs.get("Slab", "101-102400=100"))
        self.threshold = int(self.slab_val.split("-", maxsplit=1)[0]) * 1048576

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
                    self.log.info("**********")
                    self.log.info(f"{sce_num} BEGINS")
                    self.log.info(scenario)
                else:
                    self.log.info(f"END OF {sce_num}")
                    self.log.info("**********")

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
                if self.data_access_nodes:
                    self.common_args.update({'data_access_nodes': self.data_access_nodes})

            self.log.info(self.__doc__)

            self.log.info("01 : Disabling bEnableAutoSubclientDirCleanup")
            self.client_machine.create_registry(self.fsa, "bEnableAutoSubclientDirCleanup", 0, "DWord")

            self.log.info("02 : Enable feature by setting {} under {} on client.".format(self.enable, self.fsa))
            self.client_machine.create_registry(self.fsa, self.enable, 1, "DWord")
            self.log.info("03 : Lowering threshold by setting {} under {} on client.".format(self.slab, self.fsa))
            self.client_machine.create_registry(self.fsa, self.slab, self.slab_val, "MultiString")

            extent_files, non_extent_files, slash_format = "extent_files", "non_extent_files", self.slash_format

            self.log.info("04 : Create a new backupset")
            self.helper.create_backupset(self.bset_name)

            for scan_type in ScanType:

                if scan_type.name == "CHANGEJOURNAL":
                    self.log.info("{} scan method not supported, skipping test case execution".format(scan_type.name))
                    continue

                # *****************
                # SCENARIO 1 BEGINS
                # *****************
                sce_num = "SCENARIO_1_ACCEPTANCE"
                scenario = "Full -> OOP Restore -> Modify -> Incr. -> OOP Restore -> Synth. Full -> OOP Restore"
                log_scenario_details(sce_num, scenario)
                initialize_scenario_attributes(sce_num)

                self.log.info("5.01. Create a new subclient.")
                self.helper.create_subclient(scan_type=scan_type, **self.common_args)

                self.log.info("5.02. Create files that qualify for extent level backup as well as files that don't.")
                self.client_machine.generate_test_data(self.extent_path, 0, self.num_files_sce1, self.size_sce1)
                self.client_machine.generate_test_data(self.non_extent_path, 0)

                self.log.info("5.03. Run a full backup and let it complete.")
                full_bkp = self.helper.run_backup_verify(backup_level="Full")[0]
                self.helper.run_find_verify(self.content[0], full_bkp)

                self.log.info("5.04. Ensure that the large file(s) are present in FileExtentEligibleNumColTot*.cvf")
                res = self.helper.extent_level_validation(full_bkp, cvf_validation=True)
                if not res:
                    raise Exception("Extent level validation failed, failing the test case")

                self.log.info("5.05. Restore the data backed up in the previous backup job out of place and verify.")
                self.helper.run_restore_verify(slash_format, self.run_path, self.tmp_path, self.runid, full_bkp)

                self.log.info("5.06. Modify content of the large files and run an incremental backup.")
                self.client_machine.modify_test_data(self.extent_path, modify=True)
                inc_bkp = self.helper.run_backup_verify(backup_level="Incremental")[0]

                self.log.info("5.07. Ensure that the large file(s) are present in FileExtentEligibleNumColInc*.cvf.")
                res = self.helper.extent_level_validation(inc_bkp, cvf_validation=True)
                if not res:
                    raise Exception("Extent level validation failed, failing the test case")

                self.log.info("5.08. Restore the data backed up in the previous backup job out of place and verify.")
                self.helper.run_restore_verify(slash_format, self.extent_path, self.tmp_path, extent_files, inc_bkp)

                self.log.info("5.09. Run a synthetic full backup.")
                sfull_bkp = self.helper.run_backup_verify(backup_level="Synthetic_full")[0]

                self.log.info("5.10. Restore the data backed up in the previous backup job out of place and verify.")
                self.helper.run_restore_verify(slash_format, self.run_path, self.tmp_path, self.runid, sfull_bkp)

                log_scenario_details(sce_num, scenario, beginning=False)
                # ***************
                # SCENARIO 1 ENDS
                # ***************

                # *****************
                # SCENARIO 2 BEGINS
                # *****************
                sce_num, scenario = "SCENARIO_2_MORE_STREAMS", "Full -> OOP Restore"
                log_scenario_details(sce_num, scenario)
                initialize_scenario_attributes(sce_num)

                self.log.info("6.01. Create a new subclient.")
                self.helper.create_subclient(scan_type=scan_type, data_readers=self.num_streams_sc2, **self.common_args)

                self.log.info("6.02. Create a single large file that qualifies for extent level backup.")
                self.client_machine.generate_test_data(self.extent_path, 0, 1, self.size_sce2)
                # NOTICED ISSUES WITH DC SCAN PICKING UP THIS FILE CAUSING TEST CASE TO FAIL.
                sleep(10)
                self.client_machine.modify_test_data(self.extent_path, modify=True)

                self.log.info("6.03. Run a full backup using more than 2 streams and let it complete.")
                full_bkp = self.helper.run_backup_verify(backup_level="Full")[0]
                self.helper.run_find_verify(self.content[0], full_bkp)
                if (self.helper.get_extent_backup_stream_count(full_bkp) - 1) != self.num_streams_sc2:
                    self.log.info(f"Number of streams used by backup job {self.helper.get_extent_backup_stream_count(full_bkp)} doesn't match with expected count of streams {self.num_streams_sc2}.")

                self.log.info("6.04. Ensure that the large file is present in FileExtentEligibleNumColTot*.cvf.")
                res = self.helper.extent_level_validation(full_bkp, cvf_validation=True)
                if not res:
                    raise Exception("Extent level validation failed, failing the test case")

                self.log.info("6.05.  Restore the data backed up in the previous backup job out of place and verify.")
                self.helper.run_restore_verify(slash_format, self.run_path, self.tmp_path, self.runid, full_bkp)

                log_scenario_details(sce_num, scenario, beginning=False)
                # ***************
                # SCENARIO 2 ENDS
                # ***************

                # *****************
                # SCENARIO 3 BEGINS
                # *****************
                sce_num, scenario = "SCENARIO_3_COMMIT", "Full (Commit) -> -> Incr. -> OOP Restore"
                log_scenario_details(sce_num, scenario)
                initialize_scenario_attributes(sce_num)

                self.log.info("7.01. Create a new subclient.")
                self.helper.create_subclient(scan_type=scan_type, **self.common_args)

                self.log.info("7.02. Create files that qualify for extent level backup as well as files that don't.")
                self.client_machine.generate_test_data(self.extent_path, 0, self.num_files_sce3, self.size_sce3)
                self.client_machine.generate_test_data(self.non_extent_path, 0, 500, 1024)  # 500 * 1MB FILES

                self.log.info("7.03. Run a full backup and commit it.")
                full_bkp = self.helper.run_backup(backup_level="Full", wait_to_complete=False)[0]
                self.helper.commit_job(full_bkp, self.commit_threshold, CommitCondition.FILES)

                self.log.info("7.04. Ensure that the large file(s) are present in FileExtentEligibleNumColTot*.cvf.")
                res = self.helper.extent_level_validation(full_bkp, cvf_validation=True)
                if not res:
                    raise Exception("Extent level validation failed, failing the test case")

                self.log.info("7.05. Run an incremental backup and let it complete.")
                self.helper.run_backup_verify(backup_level="Incremental")[0]

                self.log.info("7.06. Restore latest data out of place and verify.")
                self.helper.run_restore_verify(slash_format, self.run_path, self.tmp_path, self.runid)

                log_scenario_details(sce_num, scenario, beginning=False)
                # ***************
                # SCENARIO 3 ENDS
                # ***************

                # *****************
                # SCENARIO 4 BEGINS
                # *****************
                sce_num, scenario = "SCENARIO_4_SPARSE_FILES", "Create Sparse Files -> Full -> OOP Restore"
                log_scenario_details(sce_num, scenario)
                initialize_scenario_attributes(sce_num)

                self.log.info("8.01. Create a new subclient.")
                self.helper.create_subclient(scan_type=scan_type, **self.common_args)

                self.log.info("8.02. Create a few sparse files such with the following specifications.")
                sparse_file_path_1 = "_".join((self.extent_path, "sparse", "1"))
                sparse_file_path_2 = "_".join((self.extent_path, "sparse", "2"))
                sparse_args = {'sparse': True, 'create_only': True}

                self.log.info("The sparse range spans across extents and is present in the middle of the file.")
                sparse_args.update({'sparse_hole_size': self.hole_size_1_sce4, 'hole_offset': self.hole_offset_1_sce4})
                self.client_machine.generate_test_data(sparse_file_path_1, 0, 1, self.size_sce4, **sparse_args)

                self.log.info("The sparse range spans less than an extent and is present in the middle of the file.")
                sparse_args.update({'sparse_hole_size': self.hole_size_2_sce4, 'hole_offset': self.hole_offset_2_sce4})
                self.client_machine.generate_test_data(sparse_file_path_2, 0, 1, self.size_sce4, **sparse_args)

                self.log.info("8.03. Run a full backup and let it complete.")
                full_bkp = self.helper.run_backup(backup_level="Full")[0]

                self.log.info("8.04. Ensure that the large file(s) are present in FileExtentEligibleNumColTot*.cvf.")
                res = self.helper.extent_level_validation(full_bkp, cvf_validation=True)
                if not res:
                    raise Exception("Extent level validation failed, failing the test case")

                self.log.info("8.05. Restore the data backed up in the previous backup job out of place and verify")
                self.helper.run_restore_verify(slash_format, self.run_path, self.tmp_path, self.runid, full_bkp)

                log_scenario_details(sce_num, scenario, beginning=False)
                # ***************
                # SCENARIO 4 ENDS
                # ***************

                # *****************
                # SCENARIO 5 BEGINS
                # *****************
                sce_num = "SCENARIO_5_SYNTH_FULL"
                scenario = "Full -> -> Incr -> Synthetic Full (Suspend, Resume) -> OOP Restore -> OOP Restore (Suspend, Resume)"
                log_scenario_details(sce_num, scenario)
                initialize_scenario_attributes(sce_num)

                self.log.info("9.01. Create a new subclient.")
                self.helper.create_subclient(scan_type=scan_type, **self.common_args)

                self.log.info("9.02. Create files that qualify for extent level backup as well as files that don't.")
                self.client_machine.generate_test_data(self.extent_path, 0, self.num_files_sce5, self.size_sce5)
                self.client_machine.generate_test_data(self.non_extent_path, 0, 500, 1024)  # 500 * 1MB FILES

                self.log.info("9.03. Run a Full backup and let it complete.")
                self.helper.run_backup(backup_level="Full")

                self.log.info("9.04. Run an Incremental backup (Full -> Synth. Full IS NO LONGER VALID AS OF SP23)")
                self.helper.run_backup(backup_level="Incremental")

                self.log.info("9.05. Run a synthetic full backup, suspend and resume when it's in progress.")
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
                    self.log.info(F"Waiting {self.suspend_interval_sce5} seconds before suspending")
                    sleep(self.suspend_interval_sce5)
                    self.log.info("Synthetic full will be suspended now.")
                    sfull_bkp.pause(wait_for_job_to_pause=True)
                    self.current_suspend += 1
                    sfull_bkp.resume()

                sfull_bkp.resume()
                sfull_bkp.wait_for_completion()

                self.log.info("9.06. Restore the data from the synthetic full backup out of place and verify.")
                self.helper.run_restore_verify(slash_format, self.run_path, self.tmp_path, self.runid, sfull_bkp)

                log_scenario_details(sce_num, scenario, beginning=False)
                # ***************
                # SCENARIO 5 ENDS
                # ***************

                # *****************
                # SCENARIO 6 BEGINS
                # *****************
                sce_num, scenario = "SCENARIO_6_ATTR_FILES", "Create Hidden, Read Only Files -> Full -> OOP Restore"
                log_scenario_details(sce_num, scenario)
                initialize_scenario_attributes(sce_num)

                self.log.info("10.01. Create a new subclient.")
                self.helper.create_subclient(**self.common_args)

                self.log.info("10.02. Create a few files such with the hidden and/or read only attributes set.")
                gen_data_args = {'file_path': self.extent_path, 'dirs': 0, 'files': 1, 'create_only': True}
                self.client_machine.generate_test_data(file_size=self.size_sce6, attribute_files='H', **gen_data_args)
                self.client_machine.generate_test_data(file_size=self.size_sce6, attribute_files='R', **gen_data_args)

                self.log.info("10.03. Run a full backup and let it complete.")
                full_bkp = self.helper.run_backup(backup_level="Full")[0]

                self.log.info("10.04. Ensure that the large file(s) are present in FileExtentEligibleNumColTot*.cvf.")
                res = self.helper.extent_level_validation(full_bkp, cvf_validation=True)
                if not res:
                    raise Exception("Extent level validation failed, failing the test case")

                self.log.info("10.05. Restore the data backed up in the previous backup job out of place and verify.")
                self.helper.run_restore_verify(slash_format, self.run_path, self.tmp_path, self.runid, full_bkp)

                log_scenario_details(sce_num, scenario, beginning=False)
                # ***************
                # SCENARIO 6 ENDS
                # ***************

                # *****************
                # SCENARIO 7 BEGINS
                # *****************
                sce_num, scenario = "SCENARIO_7_PST_FILES", "Create Large PST Files -> Full -> OOP Restore"
                log_scenario_details(sce_num, scenario)
                initialize_scenario_attributes(sce_num)

                self.log.info("11.01. Create a new subclient.")
                self.helper.create_subclient(**self.common_args)

                self.log.info("11.02. Create a single large PST file.")
                gen_data_args = {'file_path': self.extent_path, 'dirs': 0, 'files': 1}
                self.client_machine.generate_test_data(file_size=self.size_sce7, **gen_data_args)
                old_file_name = self.client_machine.get_files_in_path(self.extent_path)[0]
                self.client_machine.rename_file_or_folder(old_file_name, "".join((old_file_name, ".pst")))

                self.log.info("11.03. Run a full backup and let it complete.")
                full_bkp = self.helper.run_backup(backup_level="Full")[0]

                self.log.info("11.04. Ensure that the large file(s) are present in FileExtentEligibleNumColTot*.cvf.")
                res = self.helper.extent_level_validation(full_bkp, cvf_validation=True)
                if not res:
                    raise Exception("Extent level validation failed, failing the test case")

                self.log.info("11.05. Restore the data backed up in the previous backup job out of place and verify")
                self.helper.run_restore_verify(slash_format, self.run_path, self.tmp_path, self.runid, full_bkp)

                log_scenario_details(sce_num, scenario, beginning=False)
                # ***************
                # SCENARIO 7 ENDS
                # ***************

            # DELETING TEST DATASET

            if self.cleanup_run:
                self.client_machine.remove_directory(self.test_path)
                self.instance.backupsets.delete(self.bset_name)
            else:
                self.client_machine.remove_directory(self.test_path, self.RETAIN_DAYS)
            
        except Exception as excp:
            error_message = "Failed with error: {}".format(str(excp))
            self.log.error(error_message)
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        remove_msg = f"Removing registry entries {self.enable} and {self.slab} under {self.fsa}"
        self.log.info(remove_msg)
        self.client_machine.remove_registry(self.fsa, "bEnableAutoSubclientDirCleanup")
        self.client_machine.remove_registry(self.fsa, self.enable)
        self.client_machine.remove_registry(self.fsa, self.slab)
