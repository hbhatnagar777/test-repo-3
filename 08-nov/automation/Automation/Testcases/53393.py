# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case5
"""
import os
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from AutomationUtils import logger, constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA GCP backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Google cloud Synthetic Full Backup and Restore " \
                    "[to a project with no source vm and project] Cases"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONGCCLOUD
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.show_to_user = True
        self.tcinputs = {
            "ProjectID": None
        }

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "SYNTHETIC_FULL"
            auto_subclient.backup(backup_options)

            try:
                VirtualServerUtils.decorative_log("Out of place full vm restore")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                VirtualServerUtils.set_inputs(self.tcinputs, vm_restore_options)
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log("Files restores - v2 Indexing")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                VirtualServerUtils.set_inputs(self.tcinputs, file_restore_options)
                for vm in auto_subclient.vm_list:
                    auto_subclient.guest_file_restore(file_restore_options, discovered_client=vm)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                if not self.test_individual_status:
                    self.result_string = self.test_individual_failure_message
                    self.status = constants.FAILED
                else:
                    auto_subclient.cleanup_testdata(backup_options)
                auto_subclient.post_restore_clean_up(vm_restore_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
