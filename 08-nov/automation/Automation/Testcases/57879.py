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
from cvpysdk.commcell import Commcell
from cvpysdk.job import Job, JobController
from AutomationUtils.cvtestcase import CVTestCase, logger, constants
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA Nutanix AHV backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Nutanix AHV CBT and SNAP retention validation and " \
                    "Restore Cases using Windows proxy and Unix MA"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONNUTANIX
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.test_individual_status = True
        self.test_individual_failure_message = None

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing {0} testcase".format(self.id))

            log.info("-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)
            auto_subclient.validate_inputs("windows", "unix")

            log.info("Set CBT status on the subclient")
            value = auto_subclient.subclient.cbtvalue
            if not value:
                auto_subclient.subclient.cbtvalue = 1

            try:
                log.info("-" * 25 + " Full Backup " + "-" * 25)
                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                _adv = {"create_backup_copy_immediately": True}
                backup_options.advance_options = _adv
                backup_options.backup_method = "SNAP"
                backup_options.backup_type = "FULL"
                auto_subclient.backup(backup_options)

                self.log.info("-" * 25 + " CBT validation " + "-" * 25)
                auto_subclient.verify_cbt_backup("FULL", "SNAP")

                log.info("-" * 25 + " Incremental Backup " + "-" * 25)

                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                _adv = {"create_backup_copy_immediately": True}
                backup_options.advance_options = _adv
                backup_options.backup_method = "SNAP"
                backup_options.backup_type = "INCREMENTAL"
                auto_subclient.backup(backup_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            self.log.info("-" * 25 + " CBT validation " + "-" * 25)
            auto_subclient.verify_cbt_backup("INCREMENTAL", "SNAP")

            '#--------------------Run SNAP backup--------------------------'
            try:
                log.info("-" * 25 + " Run Snap backup for snap retention validation " + "-" * 25)

                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                _adv = {"create_backup_copy_immediately": True}
                backup_options.advance_options = _adv
                backup_options.backup_method = "SNAP"
                backup_options.backup_type = "INCREMENTAL"
                auto_subclient.backup(backup_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            '#------------Run DATA AGING before snap validation----------------'
            try:
                log.info("-" * 25 + " Run DATA AGING before snap validation " + "-" * 25)

                cs_name = self.inputJSONnode['commcell']['webconsoleHostname']
                cs_username = self.inputJSONnode['commcell']['commcellUsername']
                cs_password = self.inputJSONnode['commcell']['commcellPassword']
                da = Commcell(cs_name, cs_username, cs_password)
                da.run_data_aging()
                da_status = JobController(self.commcell)
                da_jobid = da_status.active_jobs()
                self.log.info("all the jobs {0} ".format(da_jobid))

                for j_id, j_info in da_jobid.items():
                    print("\njob ID:", j_id)

                    for key in j_info:
                        if j_info[key] == 'Data Aging':
                            jobid = j_id
                            break
                self.log.info("DATA AGING JOB: {0}".format(jobid))

                da_job = Job(self.commcell, int(jobid))
                if not da_job.wait_for_completion():
                    raise Exception("Failed to run DATA AGING with error: {}"
                                    .format(da_job.delay_reason))
                self.log.info("DATA AGING job {} is completed successfully".format(da_job))

            except Exception as err:
                self.log.exception('Exception while running DATA AGING job: %s', str(err))
                raise err

            '#---------------SNAP retention validation------------------------'
            try:
                log.info("-" * 25 + " SNAP retention validation " + "-" * 25)

                for vm in auto_instance.hvobj.VMs:
                    snap_count = auto_instance.hvobj.\
                        get_v3snap_count(auto_instance.hvobj.VMs[vm].guid)
                job_id = auto_subclient.current_job
                self.log.info(f"job_id TYPE: {type(job_id)}")
                self.log.info("job_id: {}".format(job_id))
                snap_retention = auto_commcell.get_copy_retention(int(job_id))
                self.log.info("SNAP RETENTION: {}".format(snap_retention))
                self.log.info("SNAP COUNT: {}".format(snap_count))

                if (int(snap_retention)) != 0:
                    if (int(snap_retention)) >= snap_count:
                        self.log.info("Validation PASSED. Number of snaps {0} is equal to "
                                      "{1} retention on storage policy."
                                      .format(snap_count, snap_retention))
                    else:
                        self.log.info("Validation FAILED. Number of snaps {0} is NOT equal to "
                                      "or less than {1} snaps retention set on storage policy."
                                      .format(snap_count, snap_retention))
                        raise Exception("SNAP validation failed")

                else:
                    if snap_count == 1:
                        self.log.info("Validation PASSED for a SPOOL configuration. "
                                      "Number of snaps is equal to {}. ".format(snap_count))
                    else:
                        self.log.info("Validation FAILED. Number of snaps are {} which is more "
                                      "than 1 for a SPOOL configuration.".format(snap_count))
                        raise Exception("SNAP validation failed")

            except Exception as err:
                self.log.exception('Exception while snap validation: %s', str(err))
                raise err

            '#---------------------Restores from snap------------------------'

            try:
                log.info("-" * 15 + " FULL VM out of Place restores from Snap " + "-" * 15)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.browse_from_snap = True
                auto_subclient.virtual_machine_restore(vm_restore_options)

                log.info("-" * 15 + " FULL VM out of Place restores from Backup copy " + "-" * 15)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.browse_from_backup_copy = True
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
