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
                            VSA - Snap Backup, Backup copy, Retores- Live Recovery from backup copy etc.

    Test Steps:
        1. Run snap backup.
        2. Perform Aux copy job to copy snapshot to replica copy
        2. Perform VM recovery from VM client from Replica snap copy
        3. Validate Restore VM and data; validate vsrst logs to confirm that
            VM restore using Live Recovery.
"""

import time
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from VirtualServer.SNAPUtils.vsa_snaphelper import VSASNAPHelper
from VirtualServer.SNAPUtils.vsa_snapconstants import VSASNAPConstants
from AutomationUtils.machine import Machine

class TestCase(CVTestCase):
    """Class for executing Intellisnap-Vmware-VSA V2 Live VM recovery from Replica copy at VM group level"""

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
        self.name = """ Intellisnap-Vmware-VSA V2 Live VM recovery from secondary snap copy """

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
            self.vsa_snaphelper.update_storage_policy(3)

            # Run full snap job.
            VirtualServerUtils.decorative_log("*" * 10 + " Snap job " + "*" * 10)
            self.backup_options.backup_method = "SNAP"
            self.backup_options.backup_type = "FULL"
            self.vsa_snapconstants.auto_subclient.backup(self.backup_options)

            # Run the Aux copy
            VirtualServerUtils.decorative_log("*" * 10 + " Aux Copy job " + "*" * 10)
            self.vsa_snaphelper.run_aux_copy()

            # VM restore options for Live VM recovery
            vm_lvl_restore = 8
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.vsa_snapconstants.auto_subclient, self)
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.unconditional_overwrite = True
            vm_restore_options.browse_from_snap = True
            vm_restore_options.volume_level_restore = int(vm_lvl_restore)
            vm_restore_options.redirectWritesToDatastore = self.tcinputs.get("RedirectDatastore")
            vm_restore_options.delayMigrationMinutes = int(self.tcinputs.get("DelayMigration"))

            # VM live Recovery from Backup copy at VM client.
            for _copy_precedence in self.vsa_snapconstants.secondary_copies:
                VirtualServerUtils.decorative_log(f'Live VM Recovery from Replica Copy {_copy_precedence}')
                vm_restore_options.copy_precedence = _copy_precedence
                self.vsa_snapconstants.auto_subclient.virtual_machine_restore(vm_restore_options)

            # VM live recovery log validation in vsrst log.
            try:
                _log_file = "vsrst.log"
                _vsrst_string = 'Restore will use traditional mount method since this is live vm recovery'

                # Validating Live recovery logs from vsrst.log
                _restore_jobid = vm_restore_options.restore_job.job_id
                VirtualServerUtils.decorative_log(f"Checking on VM live Recovery logs in restore job {_restore_jobid} ")
                self.MAMachine = Machine(self.tcinputs.get("browse_ma"), self.commcell)
                vsrst_log = self.MAMachine.get_logs_for_job_from_file(_restore_jobid, _log_file, _vsrst_string)
                time.sleep(30)
                if vsrst_log is not None:
                    self.log.info("-----searched successfully for log lines  -----")
                    self.log.info("Search_term2===>{}".format(vsrst_log))
                else:
                    raise Exception

                time.sleep(180)  # sleeping for umount cleanup happened after restore complete
                # Deleting snapshot
                VirtualServerUtils.decorative_log("Deleting snapshot from snap copy")
                self.vsa_snaphelper.delete_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 1)

                VirtualServerUtils.decorative_log("Deleting snapshot from Replica copy")
                self.vsa_snaphelper.delete_snap(self.vsa_snapconstants.auto_subclient.backup_job.job_id, 3)

            except Exception as err:
                self.log.exception(f"---Failed to search VM live recovery logs in vsrst.log for jobid# {_restore_jobid}---")
                raise

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
