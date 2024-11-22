# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information
# --------------------------------------------------------------------------



""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this tesc case
"""
import os
import time
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from VirtualServer.VSAUtils import VirtualServerHelper as VirtualServerhelper
from AutomationUtils import logger, constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Vmware failover and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Vmware failover validation Browse from secondary copy when primary MA is down"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.test_individual_status = True
        self.test_individual_failure_message = ''
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        try:
            log.info("Started executing %s testcase", self.id)
            log.info(
                "-------------------Initialize helper objects------------------------------------")
            auto_commcell = VirtualServerhelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            finalma = self.subclient.get_ma_associated_storagepolicy()
            VirtualServerUtils.decorative_log("-" * 25 + " Backup " + "-" * 25)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options)
            #Aux copy job
            checkauxcopyjob = auto_commcell.run_aux_copy(auto_subclient.storage_policy, None, media_agent=finalma[0])
            if not checkauxcopyjob.wait_for_completion():
                raise Exception("Failed to run job with error: "
                                +str(checkauxcopyjob.delay_reason))
            VirtualServerUtils.decorative_log("Aux copy job completed successfully")
            #stopping cvd services
            auto_subclient.stop_service(finalma[0], 'GxCVD(Instance001)')
            time.sleep(300)
            try:
                VirtualServerUtils.decorative_log(
                    "-" * 25 + " Files restores " + "-" * 25)
                fs_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                fs_restore_options.browse_from_aux_copy = True
                fs_restore_options.is_ma_specified = True
                fs_restore_options.browse_ma = self.tcinputs.get('media_agent')
                for vm in auto_subclient.vm_list:
                    auto_subclient.guest_file_restore(fs_restore_options, discovered_client=vm)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            try:
                VirtualServerUtils.decorative_log(
                    "-" * 25 + " FULL VM out of Place restores " + "-" * 25)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.browse_from_aux_copy = True
                vm_restore_options.is_ma_specified = True
                vm_restore_options.browse_ma = self.tcinputs.get('media_agent')
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            #start MA services
            auto_subclient.start_service(finalma[0], self.tcinputs.get('username'), self.tcinputs.get('password'))
        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED