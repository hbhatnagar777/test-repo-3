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
from AutomationUtils import logger, constants
from AutomationUtils.machine import Machine
from AutomationUtils.windows_machine import WindowsMachine
from AutomationUtils.unix_machine import UnixMachine
from AutomationUtils.idautils import CommonUtils



class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Vmware failover and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Vmware Extent validation with synthfull and incr jobs run in parallel"
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
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            #ADD registry key
            VirtualServerUtils.decorative_log('Add registry key')
            vmobj = Machine(self.subclient.subclient_proxy[0], self.commcell)
            if vmobj.os_info == 'WINDOWS':
                vmobj.create_registry('VirtualServer',
                                       'sDoNotBackupExtentsFolderPath',
                                        self.tcinputs.get('regkeyvalue'),
                                        reg_type='String')
            else:
                vmobj.create_registry('VirtualServer',
                                        'sDoNotBackupExtentsFolderPath',
                                        self.tcinputs.get('regkeyvalue'),
                                       reg_type='String')
            #Run full
            VirtualServerUtils.decorative_log("-" * 25 + " Full Backup " + "-" * 25)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "FULL"
            auto_subclient.backup(backup_options)
            #Run incremental
            VirtualServerUtils.decorative_log("-" * 25 + "  Incremental Backup " + "-" * 25)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options)
            #Remove registry key
            if vmobj.os_info == 'WINDOWS':
                vmobj.remove_registry('VirtualServer', 'sDoNotBackupExtentsFolderPath')
            else:
                vmobj.remove_registry('VirtualServer', 'bUseProxyTenantForSnapshot')
            VirtualServerUtils.decorative_log('registry key removed on proxy machine successfully')
            #Run Synthfull and incremental in parallel
            subclient_obj = CommonUtils(self.commcell).get_subclient(
                self.tcinputs.get('ClientName'),
                self.tcinputs.get('AgentName'),
                self.tcinputs.get('BackupsetName'),
                self.tcinputs.get('SubclientName'))
            synth_obj = subclient_obj.backup("Synthetic_full", incremental_backup=False)
            time.sleep(5)
            incr_obj = subclient_obj.backup("Incremental")
            synth_obj._initialize_job_properties()
            incr_obj._initialize_job_properties()
            if synth_obj.wait_for_completion():
                self._log.error(
                    "Synthfull job{0} completed which not expected".format(synth_obj.job_id))
                raise Exception
            if incr_obj.wait_for_completion():
                VirtualServerUtils.decorative_log(
                    'synthfull failed and Incremental job {0} completed successfully'.format(incr_obj.job_id))
            #Run synthfull
            VirtualServerUtils.decorative_log("-" * 25 + " synthfull Backup " + "-" * 25)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "SYNTHETIC_FULL"
            auto_subclient.backup(backup_options)
            try:
                VirtualServerUtils.decorative_log(
                    "-" * 25 + " FULL VM out of Place restores " + "-" * 25)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
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
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED