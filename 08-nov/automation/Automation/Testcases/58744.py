# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Main file for executing this test case
TestCase is the only class defined in this file.
TestCase: Class for executing this test case
TestCase:
    __init__()          --  initialize TestCase class
    run()               --   run function of this test case calls VSA SnapHelper Class to execute and
                            Validate  Below Operations:
                            VSA - Snap Backup, Retores- Live Recovery etc.
    _log_validation     --  vsrst log validation for Live recovery

    Test Steps:
        1. Run snap backup.
        2. Perform VM recovery from VM client from snap copy
        3. Validate Restore VM and data; validate vsrst logs to confirm that
            VM restore using Live Recovery.
        4. Run backup copy.
        5. Perform VM recovery from VM client from backup copy
        6. Validate Restore VM and data; validate vsrst logs to confirm that
            VM restore using Live Recovery.
"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from VirtualServer.SNAPUtils.vsa_snaphelper import VSASNAPHelper
from VirtualServer.SNAPUtils.vsa_snapconstants import VSASNAPConstants
from AutomationUtils.machine import Machine

class TestCase(CVTestCase):
    """Class for executing Intellisnap-Vmware-VSA V2 Live VM recovery from snap and primary copy at VM client level"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.tcinputs = {
            "browse_ma": None,
            "Datastore": None,
            "Host": None,
            "InstanceName": None,
            "Network": None,
            "SubclientName": None,
            "RedirectDatastore": None,
            "DelayMigration": None
        }
        self.name = """ Intellisnap-Vmware-VSA V2 Live VM recovery from primary snap and backup copy"""

    def _log_validation(self, jobid, logline):
        try:
            _log_file = "vsrst.log"
            _vsrst_logline = logline

            # Validating Live recovery logs from vsrst.log
            VirtualServerUtils.decorative_log(f"Checking on VM live Recovery logs in job {jobid}")
            self.MAMachine = Machine(self.tcinputs.get("browse_ma"), self.commcell)
            for _job in jobid:
                vsrst_log = self.MAMachine.get_logs_for_job_from_file(_job, _log_file, _vsrst_logline)
                time.sleep(30)
                if vsrst_log is not None:
                    self.log.info("-----searched successfully for log lines  -----")
                    self.log.info("Search_term2===>{}".format(vsrst_log))
                else:
                    raise Exception
        except Exception as err:
            self.log.exception(f"---Failed to search VM live recovery logs in vsrst.log for restore job---")
            raise

    def run(self):

        try:
            VirtualServerUtils.decorative_log("Initialize constant objects")
            self.vsa_snapconstants = VSASNAPConstants(self.commcell, self.tcinputs)
            VirtualServerUtils.decorative_log("Initialize subclient objects")
            self.vsa_snapconstants.auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            self.vsa_snapconstants.auto_client = VirtualServerHelper.AutoVSAVSClient(
                self.vsa_snapconstants.auto_commcell, self.client)
            self.vsa_snapconstants.auto_instance = VirtualServerHelper.AutoVSAVSInstance(
                self.vsa_snapconstants.auto_client, self.agent, self.instance)
            self.vsa_snapconstants.auto_backupset = VirtualServerHelper.AutoVSABackupset(
                self.vsa_snapconstants.auto_instance, self.backupset)
            self.vsa_snapconstants.auto_subclient = VirtualServerHelper.AutoVSASubclient(
                self.vsa_snapconstants.auto_backupset, self.subclient)
            VirtualServerUtils.decorative_log("Initialize helper objects")
            self.vsa_snaphelper = VSASNAPHelper(self.commcell, self.tcinputs, self.vsa_snapconstants)

            self.log.info("Started executing {0} testcase".format(self.id))
            self.backup_options = OptionsHelper.BackupOptions(self.vsa_snapconstants.auto_subclient)
            self.hvobj = self.vsa_snapconstants.auto_backupset.auto_vsainstance.hvobj

            # Run full snap job.
            VirtualServerUtils.decorative_log("Running Snap job")
            self.backup_options.backup_method = "SNAP"
            self.backup_options.backup_type = "FULL"
            self.vsa_snapconstants.auto_subclient.backup(self.backup_options)

            # VM restore options for Live recovery
            vm_lvl_restore = 8
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.vsa_snapconstants.auto_subclient, self)
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.unconditional_overwrite = True
            vm_restore_options.browse_from_snap = True
            vm_restore_options.volume_level_restore = int(vm_lvl_restore)
            vm_restore_options.redirectWritesToDatastore = self.tcinputs.get("RedirectDatastore")
            vm_restore_options.delayMigrationMinutes = int(self.tcinputs.get("DelayMigration"))

            # VM live Recovery from snap copy at VM client.
            VirtualServerUtils.decorative_log("VM Live Recovery restores from snap copy at VM client ")
            _restore_jobid = []
            for vm in self.vsa_snapconstants.auto_subclient.vm_list:
                self.vsa_snapconstants.auto_subclient.virtual_machine_restore(
                                vm_restore_options, discovered_client=vm)
                _restore_jobid.append(vm_restore_options.restore_job.job_id)

            # Validate vsrst logs for VM live recovery from snap jobs
            _vsrst_string = 'Restore will use traditional mount method since this is live vm recovery'
            self._log_validation(_restore_jobid, _vsrst_string)

            # Cleanup the restored VM from ESX
            try:
                VirtualServerUtils.decorative_log("Deleting the restored VM")
                for vm in self.vsa_snapconstants.auto_subclient.vm_list:
                    _restored_vm = "del" + vm
                    self.hvobj.VMs[_restored_vm].delete_vm()
                    time.sleep(60)
                    self.log.info("--- Deleted VM {} Successfully ---".format(_restored_vm))
            except Exception as exp:
                self.log.exception("Exception occurred deletion of restored vms")
                raise exp

            # Run backup copy job
            self.vsa_snaphelper.run_backup_copy()

            time.sleep(180) # sleeping for 2 min to commit unmount cleanup on ESXi

            # VM live recovery from backup copy job at VM client.
            VirtualServerUtils.decorative_log("VM Live Recovery restores from Primary copy at VM client ")
            vm_restore_options.browse_from_snap = False
            vm_restore_options.browse_from_backup_copy = True
            _restore_jobid.clear()
            for vm in self.vsa_snapconstants.auto_subclient.vm_list:
                self.vsa_snapconstants.auto_subclient.virtual_machine_restore(
                                        vm_restore_options, discovered_client=vm)
                _restore_jobid.append(vm_restore_options.restore_job.job_id)

            # Validate vsrst logs for VM live recovery from snap jobs
            time.sleep(30)
            _vsrst_string = 'Will create live recovery export'
            self._log_validation(_restore_jobid, _vsrst_string)

            # Delete snap jobs for cleanup
            time.sleep(60)
            VirtualServerUtils.decorative_log("Deleting snapshot from snap copy")
            self.vsa_snaphelper.delete_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 1)

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
            self.log.warning ("Testcase did not complete successfully. Cleaning up the setup")

        finally:
            try:
                # VM data and restore VM cleanup.
                self.vsa_snapconstants.auto_subclient.cleanup_testdata(self.backup_options)
                self.vsa_snapconstants.auto_subclient.post_restore_clean_up(vm_restore_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
