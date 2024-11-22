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


import os
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerUtils, OptionsHelper
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA Nutanix AHV backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Nutanix AHV SNAP PIT restores " \
                    "using Windows proxy and Unix MA"
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
                #Run 1st INCREMENTAL Job
                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                _adv = {"create_backup_copy_immediately": True}
                backup_options.advance_options = _adv
                backup_options.backup_type = "INCREMENTAL"
                backup_options.backup_method = "SNAP"
                auto_subclient.backup(backup_options)
                job_id = auto_subclient.current_job
                incr1_path = auto_subclient.testdata_path
                incr1_timestamp = auto_subclient.timestamp

                # Run 2nd INCREMENTAL Job
                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                _adv = {"create_backup_copy_immediately": True}
                backup_options.advance_options = _adv
                backup_options.backup_type = "INCREMENTAL"
                backup_options.backup_method = "SNAP"
                backup_options.cleanup_testdata_before_backup = False
                auto_subclient.backup(backup_options)

            except Exception as exp:
                self.log.exception(exp)
                self.result_string = str(exp)
                self.status = constants.FAILED

            try:
                VirtualServerUtils.decorative_log("PIT FULL VM out of Place "
                                                  "restore from 1st incremental SNAP")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.restore_backup_job = job_id
                auto_subclient.virtual_machine_restore(vm_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("PIT FULL VM out of Place "
                                                  "restore from 1st incremental Backup copy")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.restore_backup_job = job_id
                vm_restore_options.browse_from_snap = False
                vm_restore_options.browse_from_backup_copy = True
                auto_subclient.virtual_machine_restore(vm_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.log.exception(exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
                auto_subclient.testdata_path = incr1_path
                auto_subclient.timestamp = incr1_timestamp
                auto_subclient.cleanup_testdata(backup_options)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
