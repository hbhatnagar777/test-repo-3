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

"""

import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Server.Scheduler.schedulerhelper import SchedulerHelper
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
        self.name = "Virtual Server - HyperV to AzureRM - Live sync - Basic FULL backup, after backup replication and validation"

        self.schedule_helper = None

        self.vsa_commcell = None
        self.vsa_client = None
        self.vsa_instance = None
        self.vsa_backupset = None
        self.vsa_subclient = None
        self.schedule_name = None


    def setup(self):
        """Initializes pre-requisites for this test case"""
        # To create a schedule helper object
        self.schedule_name = self.tcinputs.get('ScheduleName')
        self.schedule = self.client.schedules.get(self.schedule_name)
        self.schedule_helper = SchedulerHelper(self.schedule, self.commcell)

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
            # To run a basic Full backup before configuring
            backup_options = OptionsHelper.BackupOptions(self.vsa_subclient)
            backup_options.backup_type = "INCREMENTAL"
            self.vsa_subclient.backup(backup_options, msg='INCR BACKUP')
            # To sleep for 30 seconds for the schedule to be triggered
            self.log.info('Sleeping for 30 seconds')
            time.sleep(30)

            # To get the latest replication job
            job = self.schedule_helper.get_jobid_from_taskid()

            if not job.wait_for_completion():
                raise Exception(
                    "Replication Job failed with error: " + job.delay_reason
                )
            self.log.info('Replication job: %s completed successfully', job.job_id)

            # To validate live sync
            self.vsa_subclient.validate_live_sync(self.schedule_name, schedule=self.schedule)

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
