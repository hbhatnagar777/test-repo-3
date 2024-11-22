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
                            VSA - Snap Backup, backup Copy, Restores etc."""

import time
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from VirtualServer.SNAPUtils.vsa_snaphelper import VSASNAPHelper
from VirtualServer.SNAPUtils.vsa_snapconstants import VSASNAPConstants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of backup copy on latest snap"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.tcinputs = {
            "browse_ma": None,
            "ArrayName": None,
            "ArrayPassword": None,
            "ArrayUserName": None,
            "ControlHost": None,
            "SnapEngineAtArray": None,
            "SubclientName": None
        }
        self.name = """ Basic acceptance test for backup copy on latest snap copy"""

    # Function to run the snap backups with multiple Job cycles
    def snap_backups(self, method, jobtype):

        VirtualServerUtils.decorative_log(jobtype)
        self.backup_options.backup_method = method
        self.backup_options.backup_type = jobtype
        self.vsa_snapconstants.auto_subclient.backup(self.backup_options)
        return self.vsa_snapconstants.auto_subclient.backup_job.job_id

    # Extracting VM client jobs from Parent Job.
    def get_child_job_id(self, cycle):
        childjob_ids = []
        for jType in cycle:
            childjob_ids.append(self.vsa_snapconstants.auto_subclient.get_childjob_foreachvm
                                (self.snap_backups("SNAP", jType)))
        return childjob_ids

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

            # Setting up the additional setting for this feature at commcell and client group.
            self.log.info("Started executing {0} testcase".format(self.id))
            self.log.info("Adding Additional settings 'backupCopyOnlyLatestSnapJob' to enable latest snap copy feature at "
                                              "commcell and client group")
            self.clientgroup = self.commcell.client_groups.get(self.tcinputs['ClientGroupName'])
            self.commcell.add_additional_setting("CommServDB.GxGlobalParam", "backupCopyOnlyLatestSnapJob", "BOOLEAN",
                                                 "true")
            self.clientgroup.add_additional_setting("CommServDB.Client", "backupCopyOnlyLatestSnapJob", "BOOLEAN",
                                                    "true")

            if self.vsa_snapconstants.arrayname:
                self.vsa_snaphelper.add_primary_array()

            ## Initialize variables
            VMjobs = []
            child_jobID_cycle1 = []
            child_jobID_cycle2 = []

            # Setup a backup options
            self.backup_options = OptionsHelper.BackupOptions(self.vsa_snapconstants.auto_subclient)

            # Run first cycle of Full and incr Jobs
            VirtualServerUtils.decorative_log("Running first cycle of Full and incremental snap jobs")
            bkup_cycle1 = ("FULL", "INCREMENTAL", "INCREMENTAL")
            VMjobs.extend(self.get_child_job_id(bkup_cycle1))
            child_jobID_cycle1 = [value for dict in VMjobs for value in dict.values()]
            time.sleep(120)

            # Run backup copy and validate that latest snap bkup only picked by bkup copy WF
            self.vsa_snaphelper.run_backup_copy()

            # Get the Child VM jobs to validate the backup copy status
            VirtualServerUtils.decorative_log("Verifying backup copy status of latest snap from cycle1")
            bkjob_list = self.vsa_snapconstants.execute_query(
                self.vsa_snapconstants.get_backupcopy_status, {'a': tuple(child_jobID_cycle1)})
            bkup_copy_status = [item for sublist in bkjob_list for item in sublist]

            # Check if backup copy is successful for the latest snap job
            if bkup_copy_status[0] == bkup_copy_status[-1] == '100' \
                    and all(job == '101' for job in bkup_copy_status[1:-1]):
               self.log.info("Backup copy completed for latest snap job")
            else:
                raise Exception(
                    "Backup copy for latest snap copy is not honored, please check additional settings and JM logs"
                )
            # Try Restore from backup copy
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.vsa_snapconstants.auto_subclient, self)
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.unconditional_overwrite = True
            vm_restore_options.browse_from_snap = False
            vm_restore_options.browse_from_backup_copy = True

            VirtualServerUtils.decorative_log("FULL VM out of Place restores from backup copy")
            for vm in self.vsa_snapconstants.auto_subclient.vm_list:
                self.vsa_snapconstants.auto_subclient.virtual_machine_restore(vm_restore_options, discovered_client=vm)

            # Running few more cycles for validation.from
            VirtualServerUtils.decorative_log("Running more cycles of Full and incremental snap jobs")
            bkup_cycle2 = ("FULL", "INCREMENTAL", "FULL", "INCREMENTAL", "INCREMENTAL")
            VMjobs2 = []
            VMjobs2.extend(self.get_child_job_id(bkup_cycle2))
            child_jobID_cycle2 = [value for dict in VMjobs2 for value in dict.values()]
            time.sleep(120)

            # Run backup copy and validate that latest snap bkup only picked for bkup copy
            self.vsa_snaphelper.run_backup_copy()

            # Get snap backup job IDs for child VM
            VirtualServerUtils.decorative_log("Verifying backup copy status of latest snap from cycle2")
            bkjob_list = self.vsa_snapconstants.execute_query(
                self.vsa_snapconstants.get_backupcopy_status, {'a': tuple(child_jobID_cycle2)})
            bkup_copy_status = [item for sublist in bkjob_list for item in sublist]

            # check if first cycle is skipped and bakcup copy happened for Full and last incr in second cycle
            FullJb_Cycle2 = bkup_cycle2.index("FULL", bkup_cycle2.index("FULL") + 1)
            latestIncr_cycle2 = len(bkup_cycle2) - 1 - bkup_cycle2[::-1].index("INCREMENTAL")

            if bkup_copy_status[FullJb_Cycle2] == bkup_copy_status[latestIncr_cycle2] == '100' \
                    and all(status == '101' for status in bkup_copy_status if status != '100'):
                self.log.info("Backup copy completed for latest snap job from cycle2")
            else:
                raise Exception(
                    "Backup copy for latest snap copy is not honored, please check additional settings and JM logs"
                )

            # Restore from latest incr snap job.
            VirtualServerUtils.decorative_log("FULL VM out of Place restores Indexing from latest backup copy")
            for vm in self.vsa_snapconstants.auto_subclient.vm_list:
                self.vsa_snapconstants.auto_subclient.virtual_machine_restore(vm_restore_options, discovered_client=vm)

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
            self.log.warning("Testcase did not complete successfully. Cleaning up the setup")

        finally:
            try:
                # Delete additionals settings from commcell and lient group.
                VirtualServerUtils.decorative_log("Deleting Additional settings to enable latest snap copy feature at "
                                                  "CommCell and client group" )
                self.commcell.delete_additional_setting("CommServDB.GxGlobalParam", "backupCopyOnlyLatestSnapJob")
                self.clientgroup.delete_additional_setting("CommServDB.Client", "backupCopyOnlyLatestSnapJob")

                # VM data and restore VM cleanup.
                self.vsa_snapconstants.auto_subclient.cleanup_testdata(self.backup_options)
                self.vsa_snapconstants.auto_subclient.post_restore_clean_up(vm_restore_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
