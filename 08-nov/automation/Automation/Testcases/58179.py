# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils import OptionsHelper
from VirtualServer.VSAUtils.LiveSyncUtils import LiveSyncUtils
from Server.Scheduler.schedulerhelper import SchedulerHelper


class TestCase(CVTestCase):
    """Class to perform incremental backup of aws instance and to validate livesync replication"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "To perform incremental backup, run aux-copy and to validate livesync replication"
        self.show_to_user = True
        self.tcinputs = {
            "ScheduleName": "",
            "data_center": "",
            "region": "",
            "security_groups": {},
            "nics": {},
            "proxy_client": "proxy_oregon",
            "AuxCopyName": None
        }
        self.live_sync_options = None
        self.live_sync_utils = None
        self.schedule_helper = None
        self.schedule_obj = None
        self.aux_copy_name = None

    def run(self):
        """Run function of this test case"""
        """
        description:
        to perform incremental backup of existing amazon subclient
        to validate livesync replication
        """

        try:

            auto_subclient = VirtualServerUtils.subclient_initialize(self)

            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options)
            self.log.info("backup successfull")

            self.aux_copy_name = self.tcinputs.get('AuxCopyName')
            storage_policy = self.commcell.storage_policies.get(self.subclient.storage_policy)
            job = storage_policy.run_aux_copy(self.aux_copy_name)

            if not job.wait_for_completion():
                raise Exception(
                    "Aux copy Job failed with error: " + job.delay_reason
                )
            self.log.info('Aux copy job: %s completed successfully', job.job_id)

            self.live_sync_options = OptionsHelper.LiveSyncOptions(auto_subclient, self)
            self.live_sync_options.schedule_name = self.tcinputs["ScheduleName"]

            self.live_sync_utils = LiveSyncUtils(auto_subclient=auto_subclient, schedule_name=self.live_sync_options.schedule_name)
            # Get latest replication job from schedule
            job = self.live_sync_utils.get_recent_replication_job()
            self.log.info(f"Replication Job: {job.job_id}")
            if not job.wait_for_completion():
                self.log.info(f"Replication job with job id: {job.job_id} failed")
                raise Exception("Replication Failed")

            schedule = self.client.schedules.get(self.live_sync_options.schedule_name)
            self.schedule_helper = SchedulerHelper(schedule, self.commcell)
            self.schedule_obj = self.schedule_helper.schedule_object
            try:
                self.live_sync_utils.validate_live_sync(schedule=self.schedule_obj)
            except Exception as exp:
                self.log.error(exp)
                raise Exception("Failed to complete live sync validation.")

        except Exception as exp:
            self.status = constants.FAILED
            self.log.error('Failed to execute test case with error')
            raise exp

    def tear_down(self):
        """Tear down function of this test case"""
        pass
