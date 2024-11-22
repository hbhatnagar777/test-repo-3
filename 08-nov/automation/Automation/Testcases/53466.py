
# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

import os, copy
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, VirtualServerUtils, OptionsHelper
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA Nutanix AHV backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Nutanix AHV Incremental SNAP restores from modified " \
                    "and deleted data using Windows proxy and Unix MA"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONNUTANIX
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.test_individual_status = True
        self.test_individual_failure_message = ""


    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)

            try:
                VirtualServerUtils.decorative_log("Backup")
                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                _adv = {"create_backup_copy_immediately": True}
                backup_options.advance_options = _adv
                backup_options.backup_type = "INCREMENTAL"
                backup_options.backup_method = "SNAP"
                auto_subclient.backup(backup_options)

                # deepcopy
                dest_auto_client = copy.deepcopy(auto_subclient.auto_vsaclient)
                dest_auto_instance = VirtualServerHelper.AutoVSAVSInstance \
                    (dest_auto_client, self.agent, self.instance, self.tcinputs)
                dest_auto_backupset = VirtualServerHelper.AutoVSABackupset \
                    (dest_auto_instance, self.backupset)
                dest_auto_subclient = VirtualServerHelper.AutoVSASubclient \
                    (dest_auto_backupset, self.subclient)

                # Run 2nd INCREMENTAL Job
                backup_options = OptionsHelper.BackupOptions(dest_auto_subclient)
                _adv = {"create_backup_copy_immediately": True}
                backup_options.advance_options = _adv
                backup_options.backup_type = "INCREMENTAL"
                backup_options.backup_method = "SNAP"
                backup_options.modify_data = True
                backup_options.delete_data = True
                backup_options.cleanup_testdata_before_backup = False
                dest_auto_subclient.backup(backup_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("File level restore from 1st incremental SNAP")
                fs_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                fs_restore_options.browse_from_snap = True
                VirtualServerUtils.set_inputs(self.tcinputs, fs_restore_options)
                auto_subclient.guest_file_restore(fs_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("File level restore from 2nd incremental SNAP")
                fs_restore_options = OptionsHelper.FileLevelRestoreOptions(dest_auto_subclient)
                fs_restore_options.browse_from_snap = True
                VirtualServerUtils.set_inputs(self.tcinputs, fs_restore_options)
                dest_auto_subclient.guest_file_restore(fs_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("File level restore from 1st "
                                                  "incremental Backup copy")
                fs_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                fs_restore_options.browse_from_snap = False
                fs_restore_options.browse_from_backup_copy = True
                VirtualServerUtils.set_inputs(self.tcinputs, fs_restore_options)
                auto_subclient.guest_file_restore(fs_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("File level restore from 2nd "
                                                  "incremental Backup copy")
                fs_restore_options = OptionsHelper.FileLevelRestoreOptions(dest_auto_subclient)
                fs_restore_options.browse_from_snap = False
                fs_restore_options.browse_from_backup_copy = True
                VirtualServerUtils.set_inputs(self.tcinputs, fs_restore_options)
                dest_auto_subclient.guest_file_restore(fs_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
                try:
                    dest_auto_subclient.cleanup_testdata(backup_options)
                except Exception as exp:
                    self.log.exception(exp)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
