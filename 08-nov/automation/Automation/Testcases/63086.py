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
import time

const = TeamsConstants()

msg_type = const.MessageType


class TestCase(CVTestCase):
    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Microsoft O365 Teams - Verify basic restore posts to html feature, for out of place restore"
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
            self.log.info("\t1.03. Create a standard channels in each team.")
            self.pub_team_std_ch = self.helper.create_standard_channel(self.pub_team,"STD_CHANNEL_1")
            self.pub_team_std_ch_out = self.helper.create_standard_channel(self.pub_team_out,"STD_CHANNEL_1")
            self.log.info("\t1.04. Post conversation items to standard channel of public team.")
            for i in range(15):
                self.helper.post_text_to_channel(
                    self.pub_team_std_ch, msg_type.TEXT, message=
                    f"Team Name- {self.pub_team.name}, Channel: {self.pub_team_std_ch.name}"
                    f"Post Number:{i + 1}")
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
            f_list = self.helper.get_list_of_folders_in_channel(self.pub_team, self.pub_team_std_ch.name)
            self.log.info("---------------------------------------------------------")
            self.log.info(f"STEP 3 - Restore teams with post to HTML option")
            self.log.info("---------------------------------------------------------\n")

            self.log.info("\t3.01. Running restore job with restore posts to HTML option.")
            restore_job = self.helper.restore_posts_to_html([self.pub_team.mail],self.pub_team_out.mail)
            if restore_job.status.upper() != "COMPLETED":
                raise Exception(f"Restore job {restore_job.job_id} did not complete successfully.")

            self.log.info("---------------------------------------------------------")
            self.log.info(f"STEP 4 - Comparing restored HTML.")
            self.log.info("---------------------------------------------------------\n")

            val = self.helper.restore_html_posts_cmp(self.pub_team_out, f_list, self.pub_team_std_ch_out.name)
            if not val:
                raise Exception("Restored HTML verification failed")
            else:
                self.log.info("Restored HTML successfully verified")
        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            self.result_string = str(ex)
            self.status = constants.FAILED

        finally:
            self.helper.delete_team(self.pub_team)
            self.helper.delete_team(self.pub_team_out)
