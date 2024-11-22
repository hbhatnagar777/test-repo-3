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

    tear_down()     --  tear down
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.fshelper import FSHelper
from FileSystem.FSUtils.fshelper import SoftwareCompression
from functools import partial

config_constants = config.get_config()


class TestCase(CVTestCase):
    """
    Class for executing

    Multi Node Extent Level Backup - Acceptance
    This test case will verify the basic functionality of FS extent level backup on change list based filers.
    This test case does the following.

    01 : Create a new backupset.
    02 : Create a new subclient.
    03 : Disabling bEnableAutoSubclientDirCleanup.
    04 : Enable feature by setting EnableFileExtentBackup under FileSystemAgent on client.
    05 : Lowering threshold by setting mszFileExtentSlabs under FileSystemAgent on client.
    06 : Generate the test data.
    07 : Run a Full backup and let it complete.
    08 : Ensure that the large file(s) are present in FileExtentEligibleNumColTot*.cvf.
    09 : Ensure that the files were backed up off the the snapshot.
    10 : Ensure that multiple nodes were used.
    11 : Modify some files, Add some files.
    12 : Run an Incremental backup and let it complete.
    13 : Ensure that the large file(s) are present in FileExtentEligibleNumColTot*.cvf
    14 : Restore the data backed up in the previous backup job and verify.

    """

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Multi Node Extent Level Backup - Acceptance"
        self.helper = None
        self.client_machine = None
        self.sc_name = None
        self.bset_name = None
        self.tcinputs = {"TestPath": None, "StoragePolicyName": None}
        self.data_access_nodes = None
        self.username = None
        self.password = None
        self.slab = None
        self.slab_val = None
        self.threshold = None
        self.content = None
        self.run_path = None
        self.ppath = None
        self.tmp_path = None
        self.common_args = None

    def setup(self):
        """Setup function of this test case"""

        self.helper = FSHelper(self)
        self.helper.populate_tc_inputs(self, mandatory=False)
        self.sc_name = '_'.join(("subclient", str(self.id)))
        self.bset_name = '_'.join(("backupset", str(self.id)))
        self.username = self.tcinputs.get('ImpersonateUserName', config_constants.FileSystem.WINDOWS.TestPathUserName)
        self.password = self.tcinputs.get('ImpersonatePassword', config_constants.FileSystem.WINDOWS.TestPathPassword)
        self.slab_val = str(self.tcinputs.get("Slab", "101-102400=100"))
        self.threshold = int(self.slab_val.split("-", maxsplit=1)[0]) * 1048576
        self.content = [self.client_machine.join_path(self.test_path, self.sc_name)]
        self.run_path = self.client_machine.join_path(self.content[0], str(self.runid))
        self.tmp_path = self.client_machine.join_path(self.content[0], "cvauto_tmp", str(self.runid))
        self.ppath = partial(self.client_machine.join_path, self.run_path)
        self.common_args = {'name': self.sc_name,
                            'content': self.content,
                            'storage_policy': self.storage_policy,
                            'software_compression': SoftwareCompression.OFF.value,
                            'impersonate_user': {'username': self.username, 'password': self.password},
                            'data_access_nodes': self.data_access_nodes}

        self.generate_test_data_args = {'dirs': 1, 'files': 5, 'username': self.username, 'password': self.password}

    def run(self):
        """Run function of this test case"""
        try:

            self.log.info("01 : Create a new backupset.")
            self.helper.create_backupset(self.bset_name)

            self.log.info("02 : Create a new subclient.")
            self.helper.create_subclient(**self.common_args)
            self.helper.update_subclient(data_access_nodes=self.common_args['data_access_nodes'])

            self.log.info("03 : Disabling bEnableAutoSubclientDirCleanup.")
            self.client_machine.create_registry("FileSystemAgent", "bEnableAutoSubclientDirCleanup", 0, "DWord")

            self.log.info("04 : Enable feature by setting EnableFileExtentBackup under FileSystemAgent on client.")
            self.client_machine.create_registry("FileSystemAgent", "bEnableFileExtentBackup", 1, "DWord")

            self.log.info("05 : Lowering threshold by setting mszFileExtentSlabs under FileSystemAgent on client.")
            self.client_machine.create_registry("FileSystemAgent", "mszFileExtentSlabs", self.slab_val, "MultiString")

            self.log.info("06 : Generate the test data.")
            self.client_machine.generate_test_data(self.ppath("FULL", "EXTENT"), file_size=256000, **self.generate_test_data_args)
            self.client_machine.generate_test_data(self.ppath("FULL", "NON_EXTENT"), file_size=256, **self.generate_test_data_args)

            self.log.info("07 : Run a Full backup and let it complete.")
            job = self.helper.run_backup(backup_level="Full")[0]

            self.log.info("08 : Ensure that the large file(s) are present in FileExtentEligibleNumColTot*.cvf.")
            if not self.helper.extent_level_validation(job, cvf_validation=True, node=self.data_access_nodes[0]):
                raise Exception("Validation failed, failing the test case.")

            self.log.info("09 : Ensure that the files were backed up off the the snapshot.")
            search_term = self.helper.get_logs_for_job_from_file(job_id=job.job_id, log_file_name="FileScan.log", search_term="Successfully created snapshot")
            if ('SNAP' or 'SNAPSHOT' or 'SNAPUUID') in search_term.upper():
                self.log.info(f"Files were backed up off snapshot INDICATED BY LOG LINE --> {search_term}")

            self.log.info("10 : Ensure that multiple nodes were used.")
            for node in self.data_access_nodes:
                if not Machine(node, self.commcell).get_logs_for_job_from_file(job_id=job.job_id, log_file_name="clBackup.log", search_term="CFSBackupWorker::DoBackup"):
                    raise Exception(f"Did not detect any logging on {node}, failing the test case.")

            self.log.info("11 : Modify some files, Add some files.")
            self.client_machine.modify_test_data(self.ppath("FULL", "NON_EXTENT"), modify=True)
            self.client_machine.generate_test_data(self.ppath("INCR", "NON_EXTENT"), **self.generate_test_data_args)

            self.log.info("12 : Run an Incremental backup and let it complete.")
            job = self.helper.run_backup(backup_level="Incremental")[0]

            self.log.info("13 : Ensure that the large file(s) are present in FileExtentEligibleNumColTot*.cvf.")
            if not self.helper.extent_level_validation(job, cvf_validation=True, node=self.data_access_nodes[0]):
                raise Exception("Validation failed, failing the test case.")

            self.log.info("14 : Restore the data backed up in the previous backup job and verify.")
            self.helper.run_restore_verify(self.slash_format, data_path=self.run_path, tmp_path=self.tmp_path, data_path_leaf=str(self.runid), in_place=True, restore_nodes=self.data_access_nodes)

        except Exception as exp:
            self.log.error(f'Failed to execute test case with error: {exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED
