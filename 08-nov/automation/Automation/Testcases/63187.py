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

"""

from AutomationUtils.cvtestcase import CVTestCase
from Application.Teams.teams_helper import TeamsHelper
from Application.Teams.teams_constants import TeamsConstants
from AutomationUtils import constants
import time

const = TeamsConstants()

msg_type = const.MessageType


class TestCase(CVTestCase):
    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Microsoft O365 Teams - Verify out of place restore for tabs"
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.tcinputs = {
            "ClientName": None,
            "Office365Plan": None,
            "BackupTeamMembers": None,
        }
        self.pub_team = None
        self.pub_team_std_ch = None

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client)
        self.plan = self.tcinputs.get("Office365Plan")
        self.log.info("-------------------------")
        self.log.info(f"STEP 1 - Create test data.")
        self.log.info("-------------------------\n")
        try:
            backup_team_name1 = f"AutoCreateTeam_{int(time.time())}"
            self.log.info(f"\t1.01. Create a public team: {backup_team_name1}")
            self.pub_team = self.helper.create_public_team(
                backup_team_name1, self.tcinputs.get("BackupTeamMembers")
            )
            backup_team_name2 = f"AutoCreateTeam_{int(time.time())}"
            self.log.info(f"\t1.02. Create another public team: {backup_team_name2}")
            self.pub_team_out = self.helper.create_public_team(
                backup_team_name2, self.tcinputs.get("BackupTeamMembers")
            )
            self.pub_team_std_ch = self.helper.create_standard_channel(self.pub_team, "STD_CHANNEL_1")
            self.pub_team_std_ch_out = self.helper.create_standard_channel(self.pub_team_out, "STD_CHANNEL_1")
            self.log.info("\t1.03. Adding tab to standard channel of public team.")
            val=self.helper.create_custom_tab(self.pub_team,self.pub_team_std_ch.name,"OneNote","onenote")
            if val:
                self.log.info("\t1.04. Added tab Successfully.")
        except Exception as ex:
            self.helper.delete_team(self.pub_team)
            self.helper.delete_team(self.pub_team_out)
            raise Exception(ex)

    def run(self):
        """Main function for test case execution."""
        try:
            self.log.info("------------------------------------------")
            self.log.info(f"STEP 2 - Run a backup.")
            self.log.info("------------------------------------------\n")
            self.log.info(f"\t2.01. Discovering and adding {self.pub_team.name} to content.")
            self.helper.set_content([self.pub_team.mail], self.plan)
            self.log.info(f"\t2.02. Running backup job on client: {self.client}")
            backup_job = self.helper.backup([self.pub_team.mail])
            self.log.info(f"\t      Backup job ID is {backup_job.job_id}\n")
            self.log.info(f"\t2.03. Running Restore job on client: {self.client}")
            restore_job = self.helper.out_of_place_restore(self.pub_team.mail,self.pub_team_out.mail)
            self.log.info(f"\t      Restore job ID is {restore_job.job_id}\n")
            val = self.helper.compare_team_items(self.pub_team.name,self.pub_team_out.name)
            if not val:
                raise Exception("Restored Tab verification failed")
            else:
                self.log.info("Restored Tab successfully verified")
        except Exception as ex:
            self.log.exception(ex)
            self.status = constants.FAILED

        finally:
            self.helper.delete_team(self.pub_team)
            self.helper.delete_team(self.pub_team_out)

