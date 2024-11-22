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
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils import OptionsHelper
from VirtualServer.VSAUtils.LiveSyncUtils import LiveSyncUtils
from Server.Scheduler.schedulerhelper import SchedulerHelper


class TestCase(CVTestCase):
    """Class to perform full backup of aws instance, to run aux copy, to configure livesync replication and
            to validate livesync replication between two different regions"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "To perform full backup, run aux copy, to configure livesync and to validate livesync replication"
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
        to perform full backup of amazon subclient
        to run aux copy
        to configure livesync replication
        to validate livesync replication
        """

        try:

            auto_subclient = VirtualServerUtils.subclient_initialize(self)

            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "FULL"
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

            copy_precedence = storage_policy.get_copy(self.aux_copy_name).get_copy_Precedence()
            self.live_sync_options = OptionsHelper.LiveSyncOptions(auto_subclient, self)
            self.live_sync_options.unconditional_overwrite = True
            self.live_sync_options.power_on_after_restore = True
            self.live_sync_options.schedule_name = self.tcinputs["ScheduleName"]
            self.live_sync_options.copy_precedence = copy_precedence
            self.live_sync_options.data_center = self.tcinputs["data_center"]
            self.live_sync_options.region = self.tcinputs["region"]
            self.live_sync_options.security_groups = self.tcinputs["security_groups"]
            self.live_sync_options.network = self.tcinputs["nics"]

            self.log.info(f"copy_precedence: {copy_precedence}")
            auto_subclient.configure_live_sync(self.live_sync_options)
            self.log.info("successfully configured livesync")
            self.log.info('Sleeping for 90 seconds')
            time.sleep(90)

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
