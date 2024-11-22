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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper, ScanType

from FileSystem.FSUtils.winfshelper import WinFSHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Subclient Directory Cleanup - Disable Feature with bEnableAutoSubclientDirCleanup set to 0"
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.skip_classic = None
        self.client_machine = None
        self.verify_dc = None
        self.only_dc = None
        self.folders_created = []

    def setup(self):
        """Setup for automation -
            1. Poplulate testcase inputs
            2. Create backupset with name - auto_backupset_<tc_id>
        """
        # keep a volume as the test path for Optimized
        self.log.info("*" * 20)
        self.log.info("Executing testcase {}".format(self.id))
        self.log.info("*" * 20)

        self.log.info("""Setup for automation - 
            1. Poplulate testcase inputs
            2. Create backupset with name - auto_backupset_<tc_id>
            3. Creating regkeys CopySubclientJobResultsFolderAfterScan, bEnableAutoSubclientDirCleanup
        """)

        if self.client.os_info.upper().find("WINDOWS") != -1:
            self.helper = WinFSHelper(self)
        else:
            self.helper = FSHelper(self)
        self.helper.populate_tc_inputs(self)

        self.log.info("Setting up backupsets and subclients.")

        if self.test_path.endswith(self.slash_format):
            self.test_path = str(self.test_path).rstrip(self.slash_format)

        self.log.info("Creating backupset, subclient and initializing the content")

        backupset_name = "auto_backupset_{}".format(self.id)

        self.log.info("Creating new backup set with name {} if it does not exist".format(backupset_name))
        self.helper.create_backupset(
            name=backupset_name,
            delete=True
        )

        # Additional setting - CopySubclientJobResultsFolderAfterScan
        self.client.add_additional_setting(
            "FileSystemAgent",
            "CopySubclientJobResultsFolderAfterScan",
            "INTEGER",
            "1"
        )
        self.log.info("Additional Setting CopySubclientJobResultsFolderAfterScan created")

        self.client.add_additional_setting(
            "FileSystemAgent",
            "bEnableAutoSubclientDirCleanup",
            "INTEGER",
            "0"
        )
        self.log.info("Additional Setting bEnableAutoSubclientDirCleanup created with value 0")

        # Restarting services on the client for regkeys to take effect
        self.client.restart_services(wait_for_service_restart=True, timeout=2)
        self.log.info("Restarted CommVault Services on Client")

        self.log.info("SETUP COMPLETE : Test data created in client machine, created backupset and subclient.")

    def run(self):

        self.log.info("""Do the following operations for each scan type (Recursive, Optimized, ChangeLog)-
                                Step 1.
                                    1.1. Run Full Job
                                    1.2. Validate job specific file cleanup in subclient directory
                                Step 2.
                                    2.1. Run Incremental Job
                                    2.2. Validate job specific file cleanup in subclient directory
                                Step 3.
                                    3.1. Run Differential Job
                                    3.2. Validate job specific file cleanup in subclient directory
                                Step 4.
                                    4.1. Run Synthetic Full Job
                                    4.2. Validate job specific file cleanup in subclient directory
                    """)

        helper = self.helper
        try:
            for scan_type in ScanType:

                if (self.applicable_os != 'WINDOWS'
                        and
                        scan_type.value == ScanType.CHANGEJOURNAL.value):
                        continue
                if (self.applicable_os == 'WINDOWS'
                        and
                        scan_type.value == ScanType.CHANGEJOURNAL.value):
                    if self.only_dc:
                        self.log.info("ONLY DC is Selected so skipped CJ ")
                        continue
                # Skip DC if verify_dc is not provided
                if (self.applicable_os != 'WINDOWS'
                        and
                        scan_type.value == ScanType.OPTIMIZED.value):
                    if not self.verify_dc:
                        continue

                if (scan_type.value == ScanType.RECURSIVE.value):
                    if (self.only_dc):
                            self.log.info("ONLY DC is selected skipping recursive")
                            continue

                self.log.info("*" * 20)
                self.log.info("OS : {} Scan Type : {}".format(self.applicable_os, scan_type.name))
                self.log.info("*" * 20)

                subclient_name = "auto_subclient_{}_{}".format(scan_type.name, self.id)
                self.log.info("Creating new subclient for scan type with name {}".format(subclient_name))

                self.helper.create_subclient(
                    name=subclient_name,
                    content=[self.test_path],
                    storage_policy=self.storage_policy,
                    trueup_option=True,
                    scan_type=scan_type
                )

                # Step 1. -->
                self.log.info("*" * 20)
                self.log.info("STEP 1 :")
                self.log.info("1.1. Run Full Job")
                self.log.info("1.2. Validate job specific file cleanup in subclient directory")
                self.log.info("*" * 20)

                self.log.info("Creating test data...")
                helper.generate_testdata([".txt"], path=self.test_path + self.slash_format + scan_type.name + "_FULL_1",
                                         no_of_files=5)
                self.folders_created.append(self.test_path + self.slash_format + scan_type.name + "_FULL_1")

                self.log.info("Running Backup Job...")
                job_full = helper.run_backup_verify(
                    scan_type=scan_type,
                    backup_level="Full",
                )[0]

                if not job_full.wait_for_completion():
                    raise Exception(
                        "Failed to run FULL Job with reason: {}".format(job_full.delay_reason)
                    )
                else:
                    self.log.info("Successfully ran FULL Job with ID : {}".format(job_full.job_id))
                    self.log.info("Vaidating Subclient Directory Cleanup...")
                    helper.validate_subclient_dir_cleanup(job_full)

                self.log.info("*" * 20)
                self.log.info("Step 1 complete.")
                self.log.info("*" * 20)

                # Step 2. -->
                self.log.info("*" * 20)
                self.log.info("STEP 2 :")
                self.log.info("2.1. Run Incremental Job")
                self.log.info("2.2. Validate job specific file cleanup in subclient directory")
                self.log.info("*" * 20)

                self.log.info("Adding new files for incremental backup...")

                helper.add_new_data_incr(self.test_path + self.slash_format + scan_type.name + "_INC_1",
                                         self.slash_format, scan_type=scan_type)
                helper.mod_data_incr(scan_type)
                self.folders_created.append(self.test_path + self.slash_format + scan_type.name + "_INC_1")

                self.log.info("Running Backup Job...")
                job_inc = helper.run_backup_verify(
                    scan_type=scan_type,
                    backup_level="Incremental",
                )[0]

                if not job_inc.wait_for_completion():
                    raise Exception(
                        "Failed to run INCREMENTAL Job with reason: {}".format(job_inc.delay_reason)
                    )
                else:
                    self.log.info("Successfully ran INCREMENTAL Job with ID : {}".format(job_inc.job_id))
                    self.log.info("Vaidating Subclient Directory Cleanup...")
                    helper.validate_subclient_dir_cleanup(job_inc)

                self.log.info("*" * 20)
                self.log.info("Step 2 complete.")
                self.log.info("*" * 20)

                # Step 3 -->
                self.log.info("*" * 20)
                self.log.info("STEP 3 :")
                self.log.info("3.1. Run Differential Job")
                self.log.info("3.2. Validate job specific file cleanup in subclient directory")
                self.log.info("*" * 20)

                self.log.info("Running Backup Job...")
                job_diff = helper.run_backup_verify(
                    scan_type=scan_type,
                    backup_level="Differential",
                    incremental_backup=True
                )[0]

                if not job_diff.wait_for_completion():
                    raise Exception(
                        "Failed to run INCREMENTAL Job with reason: {}".format(job_diff.delay_reason)
                    )
                else:
                    self.log.info("Successfully ran INCREMENTAL Job with ID : {}".format(job_diff.job_id))
                    self.log.info("Vaidating Subclient Directory Cleanup...")
                    helper.validate_subclient_dir_cleanup(job_diff)

                self.log.info("*" * 20)
                self.log.info("Step 3 complete.")
                self.log.info("*" * 20)

                # Step 4. -->
                self.log.info("*" * 20)
                self.log.info("STEP 4 :")
                self.log.info("4.1. Run Synthetic Full Job")
                self.log.info("4.2. Validate job specific file cleanup in subclient directory")
                self.log.info("*" * 20)

                self.log.info("Running Backup Job...")
                job_synth = helper.run_backup_verify(
                    scan_type=scan_type,
                    backup_level="Synthetic_full",
                )[0]

                if not job_synth.wait_for_completion():
                    raise Exception(
                        "Failed to run SYNTHETIC FULL Job with reason: {}".format(job_synth.delay_reason)
                    )
                else:
                    self.log.info("Successfully ran SYNTHETIC FULL Job with ID : {}".format(job_synth.job_id))
                    helper.validate_subclient_dir_cleanup(job_synth)

                self.log.info("*" * 20)
                self.log.info("Step 4 complete.")
                self.log.info("*" * 20)

                if self.backupset.subclients.has_subclient(subclient_name):
                    self.backupset.subclients.delete(subclient_name)

                self.log.info("*" * 20)
                self.log.info("All steps complete for scan type {}.".format(scan_type.name))
                self.log.info("*" * 20)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:

            # Clear folders created for test data
            for folder in self.folders_created:
                self.client_machine.remove_directory(folder)

            self.log.info("Cleared folders created for test data.")
            self.folders_created.clear()

    def tear_down(self):

        self.log.info("Deleting additional settings added for the testcase...")
        self.client.delete_additional_setting(
            "FileSystemAgent",
            "CopySubclientJobResultsFolderAfterScan",
        )
        # Removing created regkey bEnableAutoSubclientDirCleanup from client and restarting services
        self.client.delete_additional_setting(category="FileSystemAgent", key_name="bEnableAutoSubclientDirCleanup")
        self.client.restart_services(wait_for_service_restart=True, timeout=2)
        self.log.info("Restarted CommVault Services on Client")

        self.log.info("Deleting backupset created for automation...")
        self.agent.backupsets.delete(self.backupset.backupset_name)

        self.log.info("*" * 20)
        self.log.info("Testcase {} execution complete".format(self.id))
        self.log.info("STATUS : {}".format(self.status))
        self.log.info("*" * 20)
