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

import re

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing

    Auto Mounted NFS Exports - Backup & Out Of Place Restore - Acceptance

    01. Create a new backupset for Linux FS under a Network Share client.

    02. Create a new subclient.

    03. Specify an existing NFS share as the subclient's content and
        ensure that the content is specified in the file_server:/path format.

    04. Run a Full backup and let it complete.

    05. Add new data for an Incremental backup.

    06. Run an Incremental backup and let it complete.

    07. Run a Synthetic Full backup and let it complete.

    08. Run an Out Of Place restore.

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Auto Mounted NFS Exports - Backup & Out Of Place Restore - Acceptance"
        self.tcinputs = {"TestPath": None, "StoragePolicyName": None}
        self.helper = None
        self.storage_policy = None
        self.slash_format = None
        self.test_path = None
        self.runid = None
        self.id = None
        self.client_machine = None
        self.bset_name = None
        self.sc_name = None
        self.content = None
        self.full_path = None
        self.incr_path = None
        self.run_path = None
        self.tmp_path = None
        self.RETAIN_DAYS = None
        self.server = None
        self.share = None
        self.mounted_path_for_sc_content = None
        self.browse_path = None
        self.data_access_nodes = None
        self.cleanup_run = None

    def setup(self):
        """Initializes pre-requisites for this test case"""

        self.helper = FSHelper(self)
        self.helper.populate_tc_inputs(self)
        self.bset_name = '_'.join(("backupset", str(self.id)))
        self.sc_name = '_'.join(("subclient", str(self.id)))
        match_object = re.match(r'(?P<server>[\w\d\.]*):/(?P<share>[\w\d\.\/]*)', self.test_path)
        assert match_object, 'Test path needs to be server:/path'
        self.server, self.share = match_object.group('server'), match_object.group('share')
        self.content = [self.slash_format.join((self.test_path, self.sc_name))]
        self.tmp_path = self.slash_format.join((self.test_path, "cvauto_tmp", self.sc_name, str(self.runid)))

        # BROWSE PATH WILL BE /server/share..... FOR CONTENT SPECIFIED AS server:/share
        self.browse_path = self.slash_format.join((self.server, self.share, self.sc_name, str(self.runid)))

        # mounted_path_for_sc_content IS THE PATH THAT AUTOMATION WILL USE, UNDER WHICH IT WILL GENERATE THE DATASET
        self.mounted_path_for_sc_content = self.slash_format.join((self.helper.testcase.nfs_client_mount_dir, self.sc_name, str(self.runid)))

        self.full_path = self.slash_format.join((self.mounted_path_for_sc_content, "full"))
        self.incr_path = self.slash_format.join((self.mounted_path_for_sc_content, "incr"))

        # UNMOUNTING SHARE IF IT WASN'T SUCCESSFULLY DONE SO BY PREVIOUS RUN OF THE TEST CASE
        self.log.info(f"Performing a lazy unmount of {self.helper.testcase.nfs_client_mount_dir}")
        self.client_machine.execute_command(f"umount -fl {self.helper.testcase.nfs_client_mount_dir}")

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info(self.__doc__)

            self.log.info("01. Create a new backupset for Linux FS under a Network Share client.")
            self.helper.create_backupset(self.bset_name, delete=self.cleanup_run)

            self.log.info("02. Create a new subclient.")
            self.log.info("03. Specify an existing NFS share as the subclient's content and ensure that the content is specified in the file_server:/path format.")
            self.helper.create_subclient(name=self.sc_name, storage_policy=self.storage_policy, content=self.content, data_access_nodes=self.data_access_nodes)

            self.log.info(f"04. Generating a dataset on {self.full_path} by mounting it manually first.")
            self.client_machine.mount_nfs_share(self.helper.testcase.nfs_client_mount_dir, self.server, self.share)
            self.client_machine.generate_test_data(self.full_path)

            self.log.info("05. Run a Full backup and let it complete.")
            self.helper.run_backup_verify(backup_level="Full")

            self.log.info(f"06. Adding new data for Incremental backup under {self.incr_path}")
            self.helper.add_new_data_incr(self.incr_path, self.slash_format)

            self.log.info("07. Run an Incremental backup and let it complete.")
            self.helper.run_backup_verify(backup_level="Incremental")

            self.log.info("08. Run a Synthetic Full backup and let it complete.")
            synth_full = self.helper.run_backup_verify(backup_level="Synthetic_full")[0]

            self.log.info("09. Run an Out Of Place restore.")
            self.helper.run_restore_verify(self.slash_format, self.browse_path, self.tmp_path, str(self.runid), synth_full, amr=True)

            # DELETING TEST DATASET & DELETING BACKUPSET
            if self.cleanup_run:
                self.client_machine.remove_directory(self.slash_format.join((self.helper.testcase.nfs_client_mount_dir, self.sc_name)))
                self.instance.backupsets.delete(self.bset_name)
            else:
                self.client_machine.remove_directory(self.slash_format.join((self.helper.testcase.nfs_client_mount_dir, self.sc_name)), self.RETAIN_DAYS)

        except Exception as excp:
            error_message = f"Failed with error: {str(excp)}"
            self.log.error(error_message)
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        self.log.info(f"Performing a lazy unmount of {self.helper.testcase.nfs_client_mount_dir}")
        self.client_machine.execute_command(f"umount -fl {self.helper.testcase.nfs_client_mount_dir}")
