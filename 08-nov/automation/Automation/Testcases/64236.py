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
import time
from AutomationUtils.cvtestcase import CVTestCase, constants
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils, VirtualServerHelper as VirtualServerhelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Nutanix failover and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Nutanix failover validation with Index server MA services down"
        self.tcinputs = {"username": None,
                         "password": None}

    def run(self):
        """Main function for test case execution"""
        try:
            VirtualServerUtils.decorative_log(
                "-------------------Initialize helper objects------------------------------------")
            auto_commcell = VirtualServerhelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            proxy_list = self.subclient.subclient_proxy
            Indexservername = auto_subclient.get_index_name()
            finalma = auto_subclient.get_final_ma()
            # check services are up on all the proxies and media agents
            machinenames = [proxy_list[1], proxy_list[0], Indexservername, finalma[0]]
            for eachname in machinenames:
                auto_subclient.start_service(eachname, self.tcinputs.get('username'), self.tcinputs.get('password'))
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
            # stopping services after one vm job got completed
            vmjobs = auto_subclient.check_jobstatus_to_stop_services(Indexservername)
            if not _backup_job.wait_for_completion():
                raise Exception("Failed to run job with error: "
                                +str(_backup_job.delay_reason))
            VirtualServerUtils.decorative_log("Back up job completed successfully")
            # start MA services
            auto_subclient.start_service(Indexservername, self.tcinputs.get('username'), self.tcinputs.get('password'))
            # Validating if new job triggered after restart services for completed VMs
            vmjobs1 = auto_subclient.get_vm_lastcompleted_job()
            if set(vmjobs) == set(vmjobs1):
                VirtualServerUtils.decorative_log(
                    'No new jobs triggered for job completed VMs after restart')
            else:
                self.log.error("-----New jobs triggered for job completed VMs after restart-----")
                raise Exception
            # Validating if all the child jobs ran as incremental
            auto_subclient.validate_child_job_type(vmjobs, 'INCREMENTAL')
            # Validate if child job status is completed
            auto_commcell.check_job_completed_status(vmjobs)
            VirtualServerUtils.decorative_log('All failover validations succeeded')
            try:
                VirtualServerUtils.decorative_log(
                    "-" * 25 + " FULL VM out of Place restores " + "-" * 25)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.log.error("Restore job Failed")
                raise Exception
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
        except Exception as exp:
            self.log.error('Failed with error [{}]'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
