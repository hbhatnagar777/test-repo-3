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
import subprocess
import time
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper, VMHelper, VirtualServerUtils
from VirtualServer.VSAUtils import VirtualServerHelper as VirtualServerhelper
from AutomationUtils import logger, constants
from AutomationUtils.windows_machine import WindowsMachine
from AutomationUtils.idautils import CommonUtils
from cvpysdk.client import Client
from AutomationUtils.machine import Machine
import time




class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Vmware failover and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Vmware failover validation by suspending and resuming streaming job"
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
            try:
                VirtualServerUtils.decorative_log(
                    "-" * 15 + " INCREMENTAL  Backup" + "-" * 15)
                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                backup_options.backup_type = "INCREMENTAL"
                auto_subclient.vsa_discovery(backup_options, dict())
                VirtualServerUtils.decorative_log("----------Starting Backup Job----------")
                _backup_job = self.subclient.backup(backup_options.backup_type,
                                                    backup_options.run_incr_before_synth,
                                                    backup_options.incr_level,
                                                    backup_options.collect_metadata,
                                                    backup_options.advance_options)
                VirtualServerUtils.decorative_log("Back Up Job ID = {}".format(_backup_job.job_id))
            except Exception as err:
                self.log.error("Backup job Failed")
                raise Exception
            time.sleep(120)
            #suspend and resume job
            auto_subclient.service_operation(4, 1, jobidobj = _backup_job)
            if not _backup_job.wait_for_completion():
                raise Exception("Failed to run job with error: "
                                +str(_backup_job.delay_reason))
            VirtualServerUtils.decorative_log("Back up job completed successfully")
            #Validating if all the child jobs ran as incremental
            vmjobs = auto_subclient.get_vm_lastcompleted_job()
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