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

    clear_folders_created()     -- clear folders created for test data

    init_tcinputs() --  initialize the values that would have been initialized in FSHelper.populate_tcinputs()

"""
from AutomationUtils import constants
from AutomationUtils.config import ConfigReader
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.windows_machine import WindowsMachine
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.unixfshelper import UnixFSHelper

from FileSystem.FSUtils.winfshelper import WinFSHelper


class TestCase(CVTestCase):
    """Class for executing this test case
        Test case for Subclient Directory Cleanup - Multi-node backup basic acceptance with Scan Marking
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Subclient Directory Cleanup - Multi-node backup basic acceptance with Scan Marking"
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None,
            "DataAccessNodes": []
        }
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.skip_classic = None
        self.client_machine = None
        self.verify_dc = None
        self.data_access_nodes = None
        self.impersonate_username = None
        self.impersonate_password = None
        self.impersonate_user = {}
        self.config_reader = ConfigReader()
        self.is_client_network_share = True
        self.skiplink = True
        self.is_client_big_data_apps = False
        self.folders_created = []
        self.unicode = None
        self.acls = None
        self.xattr = None
        self.hlinks = None
        self.slinks = None
        self.sparse = None
        self.file_rename = None
        self.find_verify = None
        self.long_path = None
        self.problematic = None
        self.dirtime = None
        self.cluster_type = None
        self.WAIT_TIME = None
        self.RETAIN_DAYS = 10
        self.should_wait = True
        self.no_of_streams = None

    def init_tcinputs(self):
        """
        Populate tcinput values that would have been populated in FSHelper().populate_tcinputs.
        We are not calling populate_tcinputs as this is a testcase for multi-node, so Ping would not work.
        """
        self.unicode = self.tcinputs.get('Unicode', False)
        self.acls = self.tcinputs.get('ACLS', False)
        self.xattr = self.tcinputs.get('XATTR', False)
        self.hlinks = self.tcinputs.get('hlinks', True)
        self.slinks = self.tcinputs.get('slinks', True)
        self.sparse = self.tcinputs.get('sparse', True)
        self.file_rename = self.tcinputs.get('FileRename', True)
        self.find_verify = self.tcinputs.get('FindVerify', True)
        self.long_path = self.tcinputs.get('LongPath', False)
        self.verify_dc = self.tcinputs.get('VerifyDC', False)
        self.problematic = self.tcinputs.get('Problematic', False)
        self.dirtime = self.tcinputs.get('FolderTimeStamp', False)
        self.skiplink = self.tcinputs.get('SkipLink', False)
        self.skip_classic = self.tcinputs.get('SkipClassic', False)
        self.test_path = self.tcinputs.get("TestPath", None)
        self.storage_policy = self.tcinputs.get("StoragePolicyName", None)
        self.data_access_nodes = self.tcinputs.get("DataAccessNodes", None)

        self.instance = self.agent.instances.get(
            "DefaultInstanceName"
        )
        # wait time after populating the data for journals to catch up
        self.WAIT_TIME = self.tcinputs.get('WaitTime', 30)

        # no of days to retain test data on the machine.

        if self.data_access_nodes:
            self.client_machine = Machine(self.commcell.clients.get(self.data_access_nodes[0]))
        else:
            raise Exception("Backup Nodes is Empty")

        if isinstance(self.client_machine, WindowsMachine):
            self.applicable_os = self.os_list.WINDOWS
        else:
            self.applicable_os = self.os_list.UNIX

        if self.applicable_os == "WINDOWS":
            self.slash_format = '\\'
        else:
            self.slash_format = '/'

        self.no_of_streams = 2 * len(self.data_access_nodes)

        if self.applicable_os == "WINDOWS":
            self.config_reader = self.config_reader.get_config()
            self.impersonate_username = self.config_reader.Network[0]
            self.impersonate_password = self.config_reader.Network[1]

            self.impersonate_user = {
                "username": self.impersonate_username,
                "password": self.impersonate_password
            }

        if self.test_path.endswith(self.slash_format):
            self.test_path = str(self.test_path).rstrip(self.slash_format)

    def setup(self):
        """Setup for automation -
            1. Poplulate testcase inputs
            2. Create backupset with name - auto_backupset_<tc_id>
            3. Creating regkeys CopySubclientJobResultsFolderAfterScan
        """
        # keep a volume as the test path for Optimized
        self.log.info("*" * 20)
        self.log.info("Executing testcase {}".format(self.id))
        self.log.info("*" * 20)

        self.log.info("""Setup for automation - 
            1. Poplulate testcase inputs
            2. Create backupset with name - auto_backupset_<tc_id>
            3. Creating regkeys CopySubclientJobResultsFolderAfterScan
        """)

        self.init_tcinputs()
        if self.applicable_os == "WINDOWS":
            self.helper = WinFSHelper(self)
        else:
            self.helper = UnixFSHelper(self)

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
        self.log.info("Additional Setting {} created".format(
            "CopySubclientJobResultsFolderAfterScan"
            )
        )

        self.log.info("SETUP COMPLETE : Test data created in client machine, created backupset and subclient.")

    def clear_folders_created(self):
        for folder in self.folders_created:
            self.client_machine.remove_directory(folder)

        self.log.info("Cleared folders created for test data.")
        self.folders_created.clear()

    def check_if_all_node_participated_in_backup(self, job):
        """
            Checks if all node participated in backup
            Args:
                job (Job Instance) - job for this need to be verified

            Returns:
                True/False - if all participated/Not participated
        """

        if self.helper.verify_scan_marking(job.job_id):
            self.log.info("This is scan marking job..")
            return

        for node in self.data_access_nodes:

            machine = Machine(self.commcell.clients.get(node))

            if self.applicable_os == "WINDOWS":
                logs = machine.get_logs_for_job_from_file(job_id=job.job_id,
                                                          log_file_name="clBackup.log",
                                                          search_term="STARTING Controller")
            else:
                logs = machine.get_logs_for_job_from_file(job_id=job.job_id,
                                                          log_file_name="uxfsCtrl.log",
                                                          search_term="STARTING Controller")

            if not logs:
                self.log.error("[%s] Node not participated in Backup", node)
                raise Exception("[%s] Node not participated in Backup", node)
        else:
            self.log.info("All nodes participated in backup.")
        return True

    def run(self):

        self.log.info("""Do the following operations for Recursive scan type -
                                Step 1.
                                    1.1. Run Full Job
                                    1.2. Validate job specific file cleanup in subclient directory
                                Step 2.
                                    2.1. Run Incremental Job
                                    2.2. Validate job specific file cleanup in subclient directory
                                Step 3.
                                    3.1. Run Synthetic Full Job
                                    3.2. Run Incremental Job
                                    3.3. Validate job specific file cleanup in subclient directory
                                Step 4.
                                    4.1. Run Incremental Job
                                    4.2. Validate job specific file cleanup in subclient directory
                    """)

        helper = self.helper
        try:
            scan_type = ScanType.RECURSIVE

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
                data_access_nodes=self.data_access_nodes,
                impersonate_user=self.impersonate_user
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
                self.check_if_all_node_participated_in_backup(job_full)
                self.log.info("Vaidating Subclient Directory Cleanup...")
                helper.validate_subclient_dir_cleanup(job_full, multi_node=True)

            self.log.info("*" * 20)
            self.log.info("Step 1 complete.")
            self.log.info("*" * 20)

            # Step 2. -->
            self.log.info("*" * 20)
            self.log.info("STEP 2 :")
            self.log.info("2.1. Run Incremental Job")
            self.log.info("2.2. Validate job specific file cleanup in subclient directory")
            self.log.info("*" * 20)

            self.log.info("Adding new files and modifying some files for incremental backup...")

            helper.add_new_data_incr(self.test_path + self.slash_format + scan_type.name + "_INC_1",
                                     self.slash_format, scan_type, **self.impersonate_user)
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
                self.check_if_all_node_participated_in_backup(job_inc)
                self.log.info("Vaidating Subclient Directory Cleanup...")
                helper.validate_subclient_dir_cleanup(job_inc, multi_node=True)

            self.log.info("*" * 20)
            self.log.info("Step 2 complete.")
            self.log.info("*" * 20)

            # Step 3. -->
            self.log.info("*" * 20)
            self.log.info("STEP 3 :")
            self.log.info("3.1. Run Synthetic Full Job")
            self.log.info("3.2. Run Incremental Job")
            self.log.info("3.3. Validate job specific file cleanup in subclient directory")
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

            self.log.info("Adding new files and modifying some files for incremental backup...")
            helper.add_new_data_incr(self.test_path + self.slash_format + scan_type.name + "_INC_2",
                                     self.slash_format, scan_type, **self.impersonate_user)
            helper.mod_data_incr(scan_type)
            self.folders_created.append(self.test_path + self.slash_format + scan_type.name + "_INC_2")

            self.log.info("Running Backup Job...")
            job_inc = helper.run_backup_verify(
                scan_type=scan_type,
                backup_level="Incremental",
                incremental_backup=True,
                incremental_level="AFTER_SYNTH"
            )[0]

            if not job_inc.wait_for_completion():
                raise Exception(
                    "Failed to run INCREMENTAL Job with reason: {}".format(job_inc.delay_reason)
                )
            else:
                self.log.info("Successfully ran INCREMENTAL Job with ID : {}".format(job_inc.job_id))
                self.check_if_all_node_participated_in_backup(job_inc)
                self.log.info("Vaidating Subclient Directory Cleanup...")
                helper.validate_subclient_dir_cleanup(job_inc, multi_node=True)

            self.log.info("*" * 20)
            self.log.info("Step 3 complete.")
            self.log.info("*" * 20)

            # Step 4 -->
            self.log.info("*" * 20)
            self.log.info("STEP 4 :")
            self.log.info("4.1. Run Incremental Job ( Scan Marking )")
            self.log.info("4.2. Validate job specific file cleanup in subclient directory")
            self.log.info("*" * 20)

            self.log.info("Running Backup Job...")
            job_inc = helper.run_backup_verify(
                scan_type=scan_type,
                backup_level="Incremental",
                incremental_backup=True
            )[0]

            if not job_inc.wait_for_completion():
                raise Exception(
                    "Failed to run Incremental Job with reason: {}".format(job_inc.delay_reason)
                )
            else:
                self.log.info("Successfully ran INCREMENTAL Job with ID : {}".format(job_inc.job_id))
                self.check_if_all_node_participated_in_backup(job_inc)
                self.log.info("Vaidating Subclient Directory Cleanup...")
                helper.validate_subclient_dir_cleanup(job_inc, multi_node=True)

            self.log.info("*" * 20)
            self.log.info("Step 4 complete.")
            self.log.info("*" * 20)

            if self.backupset.subclients.has_subclient(subclient_name):
                self.backupset.subclients.delete(subclient_name)

            self.log.info("*" * 20)
            self.log.info("All steps complete for scan type {}.".format(scan_type.name))
            self.log.info("*" * 20)

            self.clear_folders_created()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            # Clear folders created for test data
            self.clear_folders_created()

    def tear_down(self):

        self.log.info("Deleting additional settings added for the testcase...")
        self.client.delete_additional_setting(
            "FileSystemAgent",
            "CopySubclientJobResultsFolderAfterScan",
        )

        self.log.info("Deleting backupset created for automation...")
        if self.agent.backupsets.has_backupset(self.backupset.backupset_name):
            self.agent.backupsets.delete(self.backupset.backupset_name)

        self.log.info("*" * 20)
        self.log.info("Testcase {} execution complete".format(self.id))
        self.log.info("STATUS : {}".format(self.status))
        self.log.info("*" * 20)
