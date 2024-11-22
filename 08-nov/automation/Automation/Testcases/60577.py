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
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from VirtualServer.VSAUtils import VirtualServerHelper as VirtualServerhelper
from AutomationUtils import logger, constants
import time

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Vmware failover and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Vmware failover validation with Commserver service restart for backupcopy job"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.test_individual_status = True
        self.tcinputs = {
        "username": None,
        "password": None
    }

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing %s testcase", self.id)
            log.info(
                "-------------------Initialize helper objects------------------------------------")
            auto_commcell = VirtualServerhelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            proxy_list = self.subclient.subclient_proxy
            Indexservername = auto_subclient.get_index_name()
            finalma = auto_subclient.get_final_ma()
            #check services are up on all proxies and media agents
            machinenames = [proxy_list[1], proxy_list[0], Indexservername, finalma[0]]
            for eachname in machinenames:
                auto_subclient.start_service(eachname,
                                             self.tcinputs.get('username'), self.tcinputs.get('password'))
            #checking if any jobs to be backup ied
            checkbackupcopyjob = auto_commcell.run_backup_copy(auto_subclient.storage_policy)
            if not checkbackupcopyjob.wait_for_completion():
                raise Exception("Failed to run job with error: "
                                +str(checkbackupcopyjob.delay_reason))
            VirtualServerUtils.decorative_log("Back up job completed successfully")
            #Running snap job
            VirtualServerUtils.decorative_log("Starting Snap Job")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options)
            #Running backup copy job
            backupcopyjob = auto_commcell.run_backup_copy(auto_subclient.storage_policy)
            VirtualServerUtils.decorative_log('checking Database for child job complete status')
            time.sleep(120)
            #restaring services
            self._commcell.commserv_client.restart_services()
            if not backupcopyjob.wait_for_completion():
                raise Exception("Failed to run job with error: "
                                +str(backupcopyjob.delay_reason))
            VirtualServerUtils.decorative_log("Back up job completed successfully")
            #Validating if all the child jobs ran as incremental
            vmjobs = auto_subclient.get_vm_lastcompleted_job()
            #Validating if all the child jobs ran as incremental
            auto_subclient.validate_child_job_type(vmjobs, 'INCREMENTAL')
            VirtualServerUtils.decorative_log('All failover validations succeeded')
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