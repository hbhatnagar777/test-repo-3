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

    snap_backup()      -- To run snap back up

    validate()         -- To perform validation

    validate_db_cleanup() -- To validate db clean up

    validate_snapcleanup() -- to validate snapshot clean up

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
        self.name = "Virtual Server - AzureRM - Snapshot cleanup test, after" \
                    " deleting VM"
        self.vsa_commcell = None
        self.vsa_client = None
        self.vsa_instance = None
        self.vsa_backupset = None
        self.vsa_subclient = None
        self.vm_deleted = False
        self.common_utils = None
        self.vm_restore_options = None
        self.wait = 6
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
                raises exception :
                        If  error occurs
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
                raise Exception("Failed to run backup with error: %s",
                                str(backup_job.delay_reason))
            if "errors" in backup_job.status:
                raise Exception("Backup Job completed with one or more errors")
            self.log.info("Backup Job %s completed successfully"
                          "Checking if Job type is Expected for job ",
                          str(backup_job.job_id))
            time.sleep(30)
            backupcopyid = self.common_utils.get_backup_copy_job_id(backup_job.job_id)
            backupcopy_job = Job(self.commcell, backupcopyid)
            self.log.info("Backup Copy Job {0} :".format(backupcopy_job))
            if not backupcopy_job.wait_for_completion():
                raise Exception("Failed to run backup copy job with error:{0} "
                                .format(backupcopy_job.delay_reason))
            #return backup_job
            return self.vsa_subclient.get_childjob_foreachvm(backup_job.job_id)
        except Exception as err:
            raise Exception("An Exception occurred %s" % err)

    def validate_db_cleanup(self, job):
        """Validates DB cleanup for the job
        args:
            job (obj): Job object of backup job to be validated
        """
        content = self.vsa_subclient.vm_list

        self.log.info("Validating DB clean up for Job: {0}".format(job.job_id))
        checkdb = True
        while self.wait > 0:
            #checkdb = self.vsa_subclient.check_snapshot_entry_for_job(job[0][vm])
            checkdb = self.vsa_subclient.check_snapshot_entry_for_job(job.job_id)
            if not checkdb:
                break
            self.log.info("sleeping for 10 min ")
            time.sleep(600)
            self.wait -= 1
        if checkdb:
            self.log.error("Db cleanup check has failed")
            raise Exception("DB clean up check failed")

    def validate_snapcleanup(self, vm_obj, job):
        """Validates snapshot cleanup for the job
               args:
                    vm_obj (obj): vm obj of vm to be validated
                   job (obj): Job object of backup job to be validated
        """
        metadata = self.vsa_commcell.get_snapshot_metadata_forjob(job.job_id)
        snapshot_rg = self.tcinputs.get("SnapshotRG", None)
        while self.wait > 0:
            #snapcheck = vm_obj.check_disk_snapshots_by_jobid(job_obj=job, all_snap=True, snapshot_rg=snapshot_rg)[0]
            snapcheck = vm_obj.check_disk_snapshots_by_jobid(job_obj=job, all_snap=True)[0]
            snapcheck_from_db = vm_obj.check_snapshot_bymetadta_forjob(metadata)
            if not (snapcheck or snapcheck_from_db):
                break
            self.log.info("sleeping for 10 min for snapshot to get cleaned up")
            time.sleep(600)
            self.wait -= 1
        if snapcheck or snapcheck_from_db:
            self.log.error("snapshot clean up check  failed!")
            raise Exception("Snapshot clean up validation failed")
        self.log.info("Snapshot clean up check  passed!")

    def run_dataaging(self):
        """Runs data aging job on cs"""
        dataaging_job = self.commcell.run_data_aging()
        if not dataaging_job.wait_for_completion():
            raise Exception(
                "data aging  Job failed with error: " + dataaging_job.delay_reason
            )
        self.log.info('data aging job: %s completed successfully', dataaging_job.job_id)

    def run_restore(self):
        """Perform restore of subclient"""
        try:
            self.log.info("Performing Restore")
            self.subclient._subclient_properties = None
            self.subclient._get_subclient_properties()
            job = self.subclient.full_vm_restore_in_place(overwrite=True,
                                                          power_on=False,
                                                          copy_precedence=self.vm_restore_options.copy_precedence)

            if not job.wait_for_completion():
                raise Exception(
                    "Restore Job failed with error: " + job.delay_reason
                )
            if "errors" in job.status:
                raise Exception("Restore Job completed with one or more errors")
            self.log.info('Restore job: %s completed successfully', job.job_id)
        except Exception as err:
            raise Exception("Error while performing restore " + str(err))

    def validate(self, list_of_job):
        """Validates the snapshot clean up and db cleanup
              args:
                  list_of_job  (list): list containing the Job objects
              raises exception:
                        if error occurs
        """
        try:
            self.vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.vsa_subclient, self)
            self.vm_restore_options.browse_from_backup_copy = True
            content = self.vsa_subclient.vm_list
            vm_objlist = []
            for vm in content:
                self.log.info("Deleting VM : %s", str(vm))
                self.vsa_subclient.hvobj.VMs = vm
                vm_obj = self.vsa_subclient.hvobj.VMs[vm]
                vm_objlist.append(vm_obj)
                if vm_obj.managed_disk:
                    vm_obj.clean_up()
                else:
                    vm_obj.clean_up(clean_up_disk=False)
            time.sleep(120)
            self.vm_deleted = True
            self.run_dataaging()
            for vm_obj in vm_objlist:
                child_job1 = Job(self.commcell, list_of_job[0][vm_obj.vm_name])
                self.log.info("validating snapshot clean up on %s for"
                              " Job %s", str(vm_obj.vm_name), str(child_job1))
                self.validate_snapcleanup(vm_obj, child_job1)
                self.wait = 6
                self.validate_db_cleanup(child_job1)
            time.sleep(120)
            self.run_restore()
            self.vm_deleted = False
            self.snap_backup()
            time.sleep(120)
            self.run_dataaging()
            #job2 = list_of_job[1]
            self.wait = 6
            for vm_obj in vm_objlist:
                child_job2 = Job(self.commcell, list_of_job[1][vm_obj.vm_name])
                self.log.info("validating snapshot clean up on %s for Job %s", str(vm_obj.vm_name), str(child_job2))
                self.validate_snapcleanup(vm_obj, child_job2)
                if not vm_obj.managed_disk:
                    vm_obj.clean_up_disk(vm_obj.disk_info)
            self.validate_db_cleanup(child_job2)

        except Exception as err:
            if self.vm_deleted:
                self.run_restore()
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
            self.validate(backup_jobs)

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        try:
            if self.status != constants.FAILED:
                for vm in self.vsa_subclient.vm_list:
                    self.vsa_subclient.hvobj.VMs = vm
                    vm_obj = self.vsa_subclient.hvobj.VMs[vm]
                    vm_obj.update_vm_info(force_update=True)
                    vm_obj.clean_up_snapshots(start_time=self.start_timer)
                    vm_obj.power_off()
        except Exception as exp:
            self.log.warning("Exception in tear down %s" % exp)
