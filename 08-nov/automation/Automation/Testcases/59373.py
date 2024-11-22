# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
import os
from AutomationUtils.cvtestcase import CVTestCase, constants
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils




class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of AHV failover and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "AHV Snap/backup copy proxy failover validation with worker node services down"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONNUTANIX
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution
        Note: Reduce the numder of data readers so failover can happen when some VM's are done
        """

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)

            try:
                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                _adv = {"create_backup_copy_immediately": True}
                backup_options.advance_options = _adv
                backup_options.backup_method = "SNAP"
                backup_options.backup_type = "INCREMENTAL"
                auto_subclient.backup(backup_options, bkpcopy_job_status=True, op_id=3, entity_id=2)

            except Exception as exp:
                self.log.error('Failed with error: '+str(exp))
                raise Exception

            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.browse_from_backup_copy = True
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.power_on_after_restore = True
                auto_subclient.virtual_machine_restore(vm_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
                auto_subclient.service_operation(op_id=2, entity_id=2, username=self.tcinputs['username'],
                                                 password=self.tcinputs['password'])
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
