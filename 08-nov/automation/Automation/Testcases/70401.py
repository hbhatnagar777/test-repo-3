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
