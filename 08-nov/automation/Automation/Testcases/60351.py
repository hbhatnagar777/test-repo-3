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
        self.name = "Microsoft O365 Teams - Acceptance"
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.tcinputs = {"ClientName": None, "Office365Plan": None, "BackupTeamMembers": None}
        self.pub_team = None
        self.pub_team_std_ch = None
        self.pub_team_pvt_ch = None
        self.pvt_team = None
        self.pvt_team_std_ch = None
        self.pvt_team_pvt_ch = None
        self.destination_team = None

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client)
        self.plan = self.tcinputs.get("Office365Plan")

        self.log.info("-------------------------")
        self.log.info(f"STEP 1 - Create test data.")
        self.log.info("-------------------------\n")

        self.log.info("\t1.01. Create a PUBLIC team.")
        self.pub_team = self.helper.create_public_team(members=self.tcinputs.get("BackupTeamMembers"))

        self.log.info("\t1.02. Create a PRIVATE team.")
        self.pvt_team = self.helper.create_private_team(members=self.tcinputs.get("BackupTeamMembers"))

        self.log.info("\t1.03. Create a STANDARD CHANNEL for the PUBLIC team.")
        self.pub_team_std_ch = self.helper.create_standard_channel(self.pub_team)

        self.log.info("\t1.04.  Create a STANDARD CHANNEL for the PRIVATE team.")
        self.pvt_team_std_ch = self.helper.create_standard_channel(self.pvt_team)

        self.log.info("\t1.05. Upload a FILE to STANDARD CHANNEL of PUBLIC team.")
        self.helper.upload_file(self.pub_team_std_ch)

        self.log.info("\t1.06. Upload a FILE to STANDARD CHANNEL of PRIVATE team.")
        self.helper.upload_file(self.pvt_team_std_ch)

        self.log.info("\t1.07. POST a few conversation items to STANDARD CHANNEL of PUBLIC team.")
        self.helper.post_text_to_channel(self.pub_team_std_ch, msg_type.TEXT)
        self.helper.post_text_to_channel(self.pub_team_std_ch, msg_type.IMAGE)
        self.helper.post_text_to_channel(self.pub_team_std_ch, msg_type.TEXT)

        self.log.info("\t1.08. POST a few conversation items to STANDARD CHANNEL of PRIVATE team.")
        self.helper.post_text_to_channel(self.pvt_team_std_ch, msg_type.TEXT)
        self.helper.post_text_to_channel(self.pvt_team_std_ch, msg_type.IMAGE)
        self.helper.post_text_to_channel(self.pvt_team_std_ch, msg_type.TEXT)

        self.log.info("\t1.09. Create a PRIVATE CHANNEL for the PUBLIC team.")
        self.pub_team_pvt_ch = self.helper.create_private_channel(self.pub_team)

        self.log.info("\t1.10. Create a PRIVATE CHANNEL for the PUBLIC team.\n")
        self.pvt_team_pvt_ch = self.helper.create_private_channel(self.pvt_team)

        self.log.info(f"\t1.11. Create STANDARD team as destination for restore.")
        self.destination_team = self.helper.create_public_team(members=self.tcinputs.get("BackupTeamMembers"))

    def run(self):
        """Main function for test case execution."""

        self.log.info("------------------------------------------")
        self.log.info(f"STEP 2 - Run a BACKUP, ensure it completes.")
        self.log.info("------------------------------------------\n")

        self.log.info(f"\t2.01. DISCOVERING & ADDING {self.pub_team.name} & {self.pvt_team.name} to CONTENT.")
        self.helper.set_content([self.pub_team.mail, self.pvt_team.mail], self.plan)

        self.log.info("\t2.02. Running a BACKUP.")
        backup_job = self.helper.backup([self.pub_team.mail, self.pvt_team.mail])
        self.log.info(f"\t      Backup job ID is {backup_job.job_id}\n")

        self.log.info("\t2.03. POST a conversation item to PRIVATE CHANNELS of PUBLIC & PRIVATE team.")
        self.helper.post_text_to_channel(self.pub_team_pvt_ch, msg_type.TEXT,
                                         message="INCREMENTAL BACKUP 1 MESSAGE")
        self.helper.post_text_to_channel(self.pvt_team_pvt_ch, msg_type.TEXT,
                                         message="INCREMENTAL BACKUP 1 MESSAGE")

        self.log.info("\t2.04. Waiting for 30 seconds.")
        time.sleep(30)

        self.log.info("\t2.05. Running another BACKUP.")
        backup_job = self.helper.backup([self.pub_team.mail, self.pvt_team.mail])
        self.log.info(f"\t      Backup job ID is {backup_job.job_id}\n")

        self.log.info("---------------------------------------------------------")
        self.log.info(f"STEP 3 - Restore TEAMS OUT OF PLACE, ensure it completes.")
        self.log.info("---------------------------------------------------------\n")

        self.log.info("\t3.01. Running a RESTORE.")
        restore_job = self.helper.out_of_place_restore(self.pub_team.mail, self.destination_team.mail)

        if restore_job.status.upper() == "COMPLETED" or restore_job.status.upper() == "COMPLETED W/ ONE OR MORE " \
                                                                                      "ERRORS":
            if self.helper.compare_team_items(self.pub_team.name, self.destination_team.name):
                self.log.info("The team items were restored correctly for Public Team.")
            else:
                self.log.info("The team items were NOT restored correctly for Public Team.")
        else:
            raise Exception(f"Restore job {restore_job.job_id} did not complete successfully.")
