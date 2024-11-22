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

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    source_vm_object_creation() --  To create basic VSA SDK objects

    snap_backup()      -- To run snap backup

    validate()         -- To perform validation

"""

import time
from cvpysdk.job import Job
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.idautils import CommonUtils
from VirtualServer.VSAUtils import OptionsHelper
from VirtualServer.VSAUtils.VirtualServerHelper import (
    AutoVSACommcell,
    AutoVSAVSClient,
    AutoVSAVSInstance,
    AutoVSABackupset,
    AutoVSASubclient
)


class TestCase(CVTestCase):
    """Class for configuring and monitoring Live Sync of VSA"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Virtual Server - AzureRM" \
                    " Snapshot clean up case for storage policy" \
                    "with spool retention"

        self.schedule_helper = None
        self.common_utils = None
        self.vsa_commcell = None
        self.vsa_client = None
        self.vsa_instance = None
        self.vsa_backupset = None
        self.vsa_subclient = None
        self.schedule_name = None
        self.start_timer = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.common_utils = CommonUtils(self.commcell)

    def snap_backup(self, backuptype='INCREMENTAL'):
        """performs snap backup followed by backupcopy Job
               args :
                   backuptype (str): type of backup to be performed
               returns :
                   backup_job (obj):  Job object for snap backup
               """
        try:
            backup_options = OptionsHelper.BackupOptions(self.vsa_subclient)
            _adv = {"create_backup_copy_immediately": True}
            backup_options.advance_options = _adv
            backup_options.backup_type = backuptype
            backup_options.backup_method = "SNAP"
            backup_job = self.subclient.backup(backup_options.backup_type,
                                               backup_options.run_incr_before_synth,
                                               backup_options.incr_level,
                                               backup_options.collect_metadata,
                                               backup_options.advance_options)
            self.log.info("Starting backup Job : {0}".format(backup_job.job_id))
            if not backup_job.wait_for_completion():
                raise Exception("Failed to run backup with error: {0}"
                                .format(backup_job.delay_reason))
            if "errors" in backup_job.status:
                raise Exception("Backup Job completed with one or more errors")
            self.log.info("Backup Job {0} completed successfully"
                          "Checking if Job type is Expected for job ID {0}".
                          format(backup_job.job_id))
            time.sleep(30)
            backupcopyid = self.common_utils.get_backup_copy_job_id(backup_job.job_id)
            backupcopy_job = Job(self.commcell, backupcopyid)
            self.log.info("Backup Copy Job {0} :".format(backupcopy_job))
            if not backupcopy_job.wait_for_completion():
                raise Exception("Failed to run backup copy job with error:{0} "
                                .format(backupcopy_job.delay_reason))
            return self.vsa_subclient.get_childjob_foreachvm(backup_job.job_id)
        except Exception as err:
            raise Exception("An Exception occurred %s" % err)

    def validate(self, list_of_job):
        """Validates the snapshot clean up and db cleanup
                args:
                    list_of_job  (list): list containing the Job objects
                     raises exception:
                                if error occurs
        """
        try:

            content = self.vsa_subclient.vm_list
            wait = 6
            for vm in content:
                self.log.info("Validation snapshots on VM : {0}".format(vm))
                self.vsa_subclient.hvobj.VMs = vm
                vm_obj = self.vsa_subclient.hvobj.VMs[vm]
                snapshot_rg = self.tcinputs.get("SnapshotRG", None)
                snapcheck_1 = True
                while wait > 0:
                    #snapcheck_1 = vm_obj.check_disk_snapshots_by_jobid(job_obj=list_of_job[0], all_snap=True,
                                                                      # snapshot_rg=snapshot_rg)[0]
                    child_job_obj = Job(self.commcell, list_of_job[0][vm])
                    snapcheck_1 = vm_obj.check_disk_snapshots_by_jobid(job_obj=child_job_obj,
                                                                       all_snap=True)[0]
                    if not snapcheck_1:
                        break
                    self.log.info("sleeping for 10 min ")
                    time.sleep(600)
                    wait = wait - 1
                if snapcheck_1:
                    self.log.error("snapshot clean up check  failed!")
                    raise Exception("Snapshot clean up validation failed")
                self.log.info("Snapshot clean up check  passed!")
                #snapcheck_2 = vm_obj.check_disk_snapshots_by_jobid(job_obj=list_of_job[1], all_snap=True,
                #                                                 snapshot_rg=snapshot_rg)[0]
                child_job_obj = Job(self.commcell, list_of_job[1][vm])
                snapcheck_2 = vm_obj.check_disk_snapshots_by_jobid(job_obj=child_job_obj, all_snap=True)[0]
                if not snapcheck_2:
                    self.log.error("snapshot existence check failed !")
                    raise Exception("snapshot existence check failed")

            self.log.info("checking db clean up")
            wait = 4
            for vm in content:
                checkdb = True

                while wait > 0:
                    checkdb = self.vsa_subclient.check_snapshot_entry_for_job(list_of_job[0][vm])
                    if not checkdb:
                        break
                    self.log.info("sleeping for 10 min for cleanup!")
                    time.sleep(600)
                    wait = wait - 1
                if checkdb:
                    self.log.error("Db cleanup check has failed")
                    raise Exception("DB clean up check failed")
                self.log.info("DB cleanup check passed!")
                if not self.vsa_subclient.check_snapshot_entry_for_job(list_of_job[1][vm]):
                    self.log.error("snapshot Existence check In DB failed!")
                    raise Exception("snapshot Existence check In DB failed!")

        except Exception as err:
            raise Exception("An Exception occurred %s" % err)

    def source_vm_object_creation(self):
        """To create basic VSA SDK objects"""
        self.vsa_commcell = AutoVSACommcell(self.commcell, self.csdb)
        self.vsa_client = AutoVSAVSClient(self.vsa_commcell, self.client)
        self.vsa_instance = AutoVSAVSInstance(self.vsa_client, self.agent, self.instance)
        self.vsa_backupset = AutoVSABackupset(self.vsa_instance, self.backupset)
        self.vsa_subclient = AutoVSASubclient(self.vsa_backupset, self.subclient)

    def run(self):
        """Main function for test case execution"""
        try:

            # To create basic SDK objects for VSA
            self.source_vm_object_creation()
            backup_jobs = [self.snap_backup("FULL"), self.snap_backup()]
            dataaging_job = self.commcell.run_data_aging()
            if not dataaging_job.wait_for_completion():
                raise Exception(
                    "data aging  Job failed with error: " + dataaging_job.delay_reason
                )
            self.log.info('data aging job: %s completed successfully', dataaging_job.job_id)
            self.validate(backup_jobs)

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        try:
            for vm in self.vsa_subclient.vm_list:
                self.vsa_subclient.hvobj.VMs = vm
                vm_obj = self.vsa_subclient.hvobj.VMs[vm]
                vm_obj.clean_up_snapshots(start_time=self.start_timer)
                vm_obj.power_off()
        except Exception as exp:
            self.log.warning("Exception in tear down %s" % exp)
