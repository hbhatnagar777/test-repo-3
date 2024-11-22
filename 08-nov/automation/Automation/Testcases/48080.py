# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  tear down function of this test case

    run_backup()                --  runs a full backup for subclient

    trigger_grc_schedule()      --  triggers the grc monitor schedule

    verify_pushback_entities()  --  verifies the pushback entities in pod cell

    verify_job_restore()        --  verifies the new job restore in global cell

Prerequisites before executing:

    - GRC schedule must be created on Global cell
    - The monitored entities must include a subclient on a non-default backupset under some client
    - The subclient must already have some job (so library mapping can be set)
    - The commcell library mapping properties must be properly set
    - Pushback entities must be created and selected on Global cell

"""
from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

                every object variable I will setup is initialized/declared here

        """
        super(TestCase, self).__init__()
        self.global_subclient = None
        self.commcell_machine = None
        self.user_helper = None
        self.grc_schedule = None
        self.alert = None
        self.schedule_policy = None
        self.user_group = None
        self.user = None
        self.pod_subclient = None
        self.podcell = None
        self.name = "SERVER_CONFIGURATION_GRC : GRC Acceptance"
        self.tcinputs = {
            "GRC_schedule_name": None,
            "PodCS": {
                "HostName": None,
                "UserName": None,
                "Password": None
            },
            "Monitored": {
                "ClientName": None,
                "AgentName": None,
                "BackupSetName": None,
                "SubclientName": None
            },
            "Pushback": {
                "UserName": None,
                "UserGroupName": None,
                "SchedulePolicyName": None,
                "AlertName": None
            }
        }

    def setup(self):
        """Setup function of this test case"""
        self.tcinputs["PodCS"] = eval(self.tcinputs["PodCS"])
        self.tcinputs["Monitored"] = eval(self.tcinputs["Monitored"])
        self.tcinputs["Pushback"] = eval(self.tcinputs["Pushback"])
        self.podcell = Commcell(self.tcinputs["PodCS"]["HostName"],
                                self.tcinputs["PodCS"]["UserName"],
                                self.tcinputs["PodCS"]["Password"])
        self.pod_subclient = self.podcell.clients.get(self.tcinputs["Monitored"]["ClientName"]).agents \
            .get(self.tcinputs["Monitored"]["AgentName"]).backupsets \
            .get(self.tcinputs["Monitored"]["BackupSetName"]).subclients \
            .get(self.tcinputs["Monitored"]["SubclientName"])
        self.user = self.commcell.users.get(self.tcinputs["Pushback"]["UserName"])
        self.user_group = self.commcell.user_groups.get(self.tcinputs["Pushback"]["UserGroupName"])
        self.schedule_policy = self.commcell.schedule_policies.get(self.tcinputs["Pushback"]["SchedulePolicyName"])
        self.alert = self.commcell.alerts.get(self.tcinputs["Pushback"]["AlertName"])
        self.grc_schedule = self.commcell.schedules.get(self.tcinputs["GRC_schedule_name"])
        self.commcell_machine = Machine()

    def run(self):
        """Run function of this test case"""
        job_id = self.run_backup()
        sleep(30)
        self.trigger_grc_schedule()
        self.commcell.refresh()
        self.podcell.refresh()
        self.verify_pushback_entities()
        self.verify_job_restore(job_id)

    def tear_down(self):
        """Tear down function of this test case"""
        self.podcell.alerts.delete(self.tcinputs["Pushback"]["AlertName"])
        self.podcell.schedule_policies.delete(self.tcinputs["Pushback"]["SchedulePolicyName"])
        self.podcell.users.delete(self.tcinputs["Pushback"]["UserName"], "admin")
        self.podcell.user_groups.delete(self.tcinputs["Pushback"]["UserGroupName"], "admin")

    def run_backup(self):
        """Triggers full backup job, waits for completion and returns job id"""
        self.log.info("Running backup on pod cell")
        job = self.pod_subclient.backup("Incremental")
        if not job.wait_for_completion():
            raise Exception("backup job failed")
        self.log.info("Backup completed succesfully")
        return job.job_id

    def trigger_grc_schedule(self):
        """Triggers the grc schedule and waits for completion"""
        self.log.info("Triggering grc schedule")
        id = self.grc_schedule.run_now()
        if not self.commcell.job_controller.get(id).wait_for_completion():
            raise Exception("GRC schedule failed")
        self.log.info("GRC schedule successfully completed")

    def verify_pushback_entities(self):
        """Verifies the pushback entities have been imported to pod cell"""
        alert = self.podcell.alerts.get(self.tcinputs["Pushback"]["AlertName"])
        schedule_policy = self.podcell.schedule_policies.get(self.tcinputs["Pushback"]["SchedulePolicyName"])
        user = self.podcell.users.get(self.tcinputs["Pushback"]["UserName"])
        user_group = self.podcell.user_groups.get(self.tcinputs["Pushback"]["UserGroupName"])

        if alert.alert_type == self.alert.alert_type and \
                alert.alert_category == self.alert.alert_category and \
                schedule_policy.schedule_policy_name == self.schedule_policy.schedule_policy_name and \
                schedule_policy.policy_type == self.schedule_policy.policy_type and \
                user.user_name == self.user.user_name and \
                user.email == self.user.email and \
                user_group.user_group_name == self.user_group.user_group_name:
            self.log.info("Pushback Entities migration verified")
        else:
            raise Exception("Pushback Entity migration could not be verified")

    def verify_job_restore(self, job_id):
        """Verifies the migrated job is available and restoreable"""
        self.global_subclient = self.commcell.clients.get(self.tcinputs["Monitored"]["ClientName"]).agents \
            .get(self.tcinputs["Monitored"]["AgentName"]).backupsets \
            .get(self.tcinputs["Monitored"]["BackupSetName"]).subclients \
            .get(self.tcinputs["Monitored"]["SubclientName"])

        migrated_job = self.commcell.job_controller.all_jobs(self.tcinputs["Monitored"]["ClientName"])[int(job_id)]
        original_job = self.podcell.job_controller.all_jobs()[int(job_id)]
        del migrated_job['subclient_id']
        del original_job['subclient_id']

        if migrated_job != original_job:
            self.log.error("Job Stats Mismatched After Import")
            raise Exception("Destination Job does not Match Source Job")

        self.log.info("trying browse ...")
        self.global_subclient.browse(path=self.pod_subclient.content)
        self.log.info("browse is succesfull, now trying restore ...")

        temp_restore_path = f"{self.commcell_machine.tmp_dir}\\restore"

        self.commcell_machine.create_directory(temp_restore_path, True)
        job = self.global_subclient.restore_out_of_place(
            self.tcinputs["Monitored"]["ClientName"],
            temp_restore_path,
            self.pod_subclient.content,
            fs_options={'media_agent': self.commcell.commserv_name, "proxy_client": self.commcell.commserv_name}
        )
        if not job.wait_for_completion():
            raise Exception("restore job failed to complete")
        self.log.info("Restore completed successfully!")

        try:
            self.commcell_machine.remove_directory(temp_restore_path)
        except:
            self.log.error("failed to delete restore directory")
