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
                    "with spool retention for Multiple Subscription "

        self.schedule_helper = None
        self.common_utils = None
        self.vsa_commcell = None
        self.vsa_client = None
        self.vsa_instance = None
        self.vsa_backupset = None
        self.vsa_subclient = None
        self.schedule_name = None
        self.client2 = None
        self.agent2 = None
        self.instance2 = None
        self.backupset2 = None
        self.subclient2 = None
        self.vsa_client2 = None
        self.vsa_instance2 = None
        self.vsa_backupset2 = None
        self.vsa_subclient2 = None
        self.wait = 8
        self.start_timer = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.common_utils = CommonUtils(self.commcell)

    def snap_backup(self, auto_subclient, backuptype='INCREMENTAL'):
        """performs snap backup followed by backupcopy Job
               args :
                   backuptype (str): type of backup to be performed
               returns :
                   backup_job (obj):  Job object for snap backup
               """
        try:
            self.log.info("Submitting backup job for {0}".format(auto_subclient.subclient))
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            _adv = {"create_backup_copy_immediately": True}
            backup_options.advance_options = _adv
            backup_options.backup_type = backuptype
            backup_options.backup_method = "SNAP"
            backup_job = auto_subclient.subclient.\
                backup(backup_options.backup_type,
                       backup_options.run_incr_before_synth,
                       backup_options.incr_level,
                       backup_options.collect_metadata,
                       backup_options.advance_options)

            self.log.info("Started snap backup Job : {0}".format(backup_job.job_id))
            return backup_job
        except Exception as err:
            raise Exception("An Exception occurred %s" % err)

    def monitor_job(self, job_list):
        """
            monitor the snap and corresponding backup copy job to completion
             Args:
                 job_list   (list): list of object of job  to be monitored

             Returns    (bool): True if all jobs competed else false

             """
        status = True
        try:
            for job in job_list:
                if not job.wait_for_completion():
                    self.log.error("Failed to run backup with error: %s",
                                   str(job.delay_reason))
                    status = False
                if "errors" in job.status:
                    self.log.error("Backup Job completed with one or more errors failing testcase")
                    status = False
                time.sleep(60)
                backupcopyid = self.common_utils.get_backup_copy_job_id(job.job_id)
                backupcopy_job = Job(self.commcell, backupcopyid)
                self.log.info("Backup Copy Job {0} :".format(backupcopy_job))
                if not backupcopy_job.wait_for_completion():
                    status = False
                    self.log.error("Failed to run backup copy job with error:{0} "
                                   .format(backupcopy_job.delay_reason))
            return status
        except Exception as err:
            raise Exception("An Exception occurred %s" % err)

    def validate(self, list_of_job, auto_subclient):
        """Validates the snapshot clean up and db cleanup
                args:
                    list_of_job  (list): list containing the Job objects
                     raises exception:
                                if error occurs
        """
        try:
            self.log.info("Performing validations on  {0}".format(auto_subclient.subclient))
            content = auto_subclient.vm_list
            self.wait = self.wait if self.wait >= 1 else 1
            for vm in content:
                self.log.info("Validation snapshots on VM : {0}".format(vm))
                auto_subclient.hvobj.VMs = vm
                vm_obj = auto_subclient.hvobj.VMs[vm]
                snapcheck_1 = True
                while self.wait > 0:
                    snapcheck_1 = vm_obj.check_disk_snapshots_by_jobid(job_obj=list_of_job[0],
                                                                       all_snap=True)[0]
                    if not snapcheck_1:
                        break
                    self.log.info("sleeping for 10 min ")
                    time.sleep(600)
                    self.wait -= 1
                if snapcheck_1:
                    self.log.error("snapshot clean up check  failed!")
                    raise Exception("Snapshot clean up validation failed")
                self.log.info("Snapshot clean up check  passed!")
                snapcheck_2 = vm_obj.check_disk_snapshots_by_jobid(job_obj=list_of_job[1],
                                                                   all_snap=True)[0]
                if not snapcheck_2:
                    self.log.error("snapshot existence check failed !")
                    raise Exception("snapshot existence check failed")

            self.log.info("checking db clean up")
            wait = 6
            checkdb = True
            while wait > 0:
                checkdb = auto_subclient.check_snapshot_entry_for_job(list_of_job[0].job_id)
                if not checkdb:
                    break
                self.log.info("sleeping for 10 min for cleanup!")
                time.sleep(600)
                wait = wait - 1
            if checkdb:
                self.log.error("DB cleanup check has failed")
                raise Exception("DB clean up check failed")
            self.log.info("DB cleanup check passed!")
            if not auto_subclient.check_snapshot_entry_for_job(list_of_job[1].job_id):
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
        self.client2 = self.commcell.clients.get(self.tcinputs['ClientName2'])
        self.agent2 = self.client2.agents.get(self.tcinputs['AgentName'])
        self.instance2 = self.agent2.instances.get(self.tcinputs['InstanceName'])
        self.backupset2 = self.instance2.backupsets.get(self.tcinputs['BackupsetName2'])
        self.subclient2 = self.backupset2.subclients.get(self.tcinputs['SubclientName2'])
        self.vsa_client2 = AutoVSAVSClient(self.vsa_commcell, self.client2)
        self.vsa_instance2 = AutoVSAVSInstance(self.vsa_client2, self.agent2, self.instance2)
        self.vsa_backupset2 = AutoVSABackupset(self.vsa_instance2, self.backupset2)
        self.vsa_subclient2 = AutoVSASubclient(self.vsa_backupset2, self.subclient2)

    def run(self):
        """Main function for test case execution"""
        try:
            self.source_vm_object_creation()
            snap_backup1 = [self.snap_backup(self.vsa_subclient, "FULL"), self.snap_backup(self.vsa_subclient2, "FULL")]
            if not self.monitor_job(snap_backup1):
                self.log.error("One or more backup jobs have failed please check the logs")
                raise Exception("One or more backup jobs failed")
            snap_backup2 = [self.snap_backup(self.vsa_subclient), self.snap_backup(self.vsa_subclient2)]
            if not self.monitor_job(snap_backup2):
                self.log.error("One or more backup jobs have failed please check the logs")
                raise Exception("One or more backup jobs failed")
            job_list = [[job1, job2] for job1, job2 in zip(snap_backup1, snap_backup2)]
            time.sleep(120)
            data_aging_job = self.commcell.run_data_aging()
            if not data_aging_job.wait_for_completion():
                raise Exception(
                    "data aging  Job failed with error: " + data_aging_job.delay_reason
                )
            self.log.info('data aging job: %s completed successfully', data_aging_job.job_id)
            self.validate(job_list[0], self.vsa_subclient)
            self.validate(job_list[1], self.vsa_subclient2)

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        try:
            if self.status != constants.FAILED:
                for subclient in [self.vsa_subclient, self.vsa_subclient2]:
                    for vm in subclient.vm_list:
                        subclient.hvobj.VMs = vm
                        vm_obj = subclient.hvobj.VMs[vm]
                        vm_obj.clean_up_snapshots(self.start_timer)
                        vm_obj.power_off()
        except Exception as exp:
            self.log.warning("Exception in tear down %s" % exp)
