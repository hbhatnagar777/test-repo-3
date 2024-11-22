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
    __init__()      --  Initialize TestCase class

    setup()         --  Setup function of this test case

    run()           --  Run function of this test case

    tear_down()     --  Tear down function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Application.Teams.teams_helper import TeamsHelper
from Application.Teams.user import User
from Application.Teams.teams_constants import TeamsConstants

const = TeamsConstants()

msg_type = const.MessageType


class TestCase(CVTestCase):
    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Microsoft O365 Teams Public Channels - Backup & Restore"
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.restore_job = None
        self.tcinputs = {
            "ClientName": None,
            "Office365Plan": None,
            "GlobalAdmin": None,
            "members": None
        }
        self.pub_team = None
        self.pub_team_std_ch = None
        self.destination_team = None
        self.user = None

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client)
        self.plan = self.tcinputs.get("Office365Plan")
        self.user = User(self.tcinputs.get("GlobalAdmin"))

        self.log.info("STEP 1 - Create test data.")

        self.log.info("\t1.01. Create a PUBLIC team.")
        self.pub_team = self.helper.create_public_team(members=self.tcinputs.get("members"))

        self.log.info("\t1.02. Create a STANDARD CHANNEL for the PUBLIC team.")
        self.pub_team_std_ch = self.helper.create_standard_channel(self.pub_team)

        self.log.info("\t1.03. Upload a FILE to STANDARD CHANNEL of PUBLIC team.")
        self.helper.upload_file(self.pub_team_std_ch)

        self.log.info("\t1.04. POST a few conversation items to STANDARD CHANNEL of PUBLIC team.")
        self.helper.post_text_to_channel(self.pub_team_std_ch, msg_type.TEXT, "HI")
        self.helper.post_text_to_channel(self.pub_team_std_ch, msg_type.TEXT, "GOOD MORNING")
        self.helper.post_text_to_channel(self.pub_team_std_ch, msg_type.TEXT, "THANK U")

        self.log.info("\t1.05. Create STANDARD team as destination for restore.")
        self.destination_team = self.helper.create_public_team(members=self.tcinputs.get("members"))

    def run(self):
        """Main function for test case execution."""

        self.log.info("STEP 3 - Validate teams under Client to Tenant.")
        self.log.info("\t3.01. Fetch teams from cache file.")
        teams_in_a_cache_file = sorted(list(self.helper.discover().keys()))

        self.log.info("\t3.02. Fetch teams from Tenant.")
        teams_in_a_tenant = sorted(self.helper.get_all_teams_in_tenant())

        self.log.info("\t3.03. Compare teams under Client to Tenant.")
        if teams_in_a_cache_file == teams_in_a_tenant:
            self.log.info("\tTeams discovered sucessfully.")
        else:
            raise Exception("Teams are not discovered sucessfully.")

        self.log.info("STEP 4 - Run a BACKUP, ensure it completes.")

        self.log.info('\t4.01. DISCOVERING & ADDING %s to CONTENT.', self.pub_team.name)
        self.helper.set_content([self.pub_team.mail], self.plan)

        self.log.info("\t4.02. Running a BACKUP.")
        backup_job = self.helper.backup([self.pub_team.mail])
        if backup_job.status.upper() != "COMPLETED":
            raise Exception(f"Backup job {backup_job.job_id} did not complete successfully.")
        self.log.info("\t      Backup job ID is %s\n", backup_job.job_id)

        self.log.info("STEP 5 - Restore TEAMS OUT OF PLACE, ensure it completes.")

        self.log.info("\t5.01. Running a RESTORE.")
        restore_job = self.helper.out_of_place_restore(self.pub_team.mail, self.destination_team.mail)

        self.log.info("\t      Restore job ID is %s", restore_job.job_id)

        if restore_job.status.upper() != "COMPLETED":
            raise Exception("Restore job was not completed sucessfully.")

        self.log.info("STEP 6 - Compare Source team and Destination team to check data is restored sucessfully or not."
                      )

        self.log.info("\t6.02. Compare teams.")
        if self.helper.compare_team_items(self.pub_team.name, self.destination_team.name):
            self.log.info("The team items were restored correctly.")
        else:
            raise Exception("The team items were NOT restored correctly.")

    def tear_down(self):
        """Tear down function for this testcase."""

        self.log.info("STEP 7 - Delete all created teams.")
        self.log.info("Removing Team from Content\n")
        self.helper.remove_team_association([self.pub_team.mail])

        self.log.info("\t7.01. Deleting PUBLIC team.")
        self.helper.delete_team(self.pub_team)

        self.log.info("\t7.02. Deleting DESTINATION team.")
        self.helper.delete_team(self.destination_team)
