# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Main file for executing this test case

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
const = TeamsConstants()

msg_type = const.MessageType
file_type = const.FileType


class TestCase(CVTestCase):
    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Microsoft O365 Teams Convert Job To Full Verification"
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.backup_job = None
        self.tcinputs = {
            "ClientName": None,
            "Office365Plan": None,
            "members": None
        }
        self.pub_team = None
        self.pub_team_gnl_ch = None

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client, self)
        self.plan = self.tcinputs['Office365Plan']
        self.log.info("1.create a public team.")
        self.pub_team = self.helper.create_public_team(members=self.tcinputs['members'])
        self.log.info("2.create a General channel.")
        self.pub_team_gnl_ch = self.pub_team.channels['General']
        self.log.info("3.Upload 5 files to public team.")
        for _ in range(5):
            self.helper.upload_file(self.pub_team_gnl_ch)

    def run(self):
        """Main function for test case execution."""
        self.log.info(f"4.Adding {self.pub_team.mail} to the content.")
        self.helper.set_content([self.pub_team.mail], self.plan)
        self.log.info(f"5.Running backup job for {self.pub_team.mail}.")
        self.backup_job = self.helper.backup([self.pub_team.mail])
        self.log.info("BACKUP JOB ID is %s", self.backup_job.job_id)
        self.log.info("6.Upload 5 files to public team.")
        for _ in range(5):
            self.helper.upload_file(self.pub_team_gnl_ch)
        self.log.info(f"7.Running incremental backup job for {self.pub_team.mail}.")
        incremental_job = self.helper.backup([self.pub_team.mail])
        self.log.info("incremental BACKUP JOB ID is %s", incremental_job.job_id)
        self.log.info(f"8.Running full job for {self.pub_team.mail}")
        full_job = self.helper.backup([self.pub_team.mail], convert_job_to_full=True)
        self.log.info("FULL BACKUP JOB ID is %s", full_job.job_id)
        self.log.info(f"9. Compare No Of items backed up in {self.backup_job.job_id} + {incremental_job.job_id} to "
                      f"{full_job.job_id}")
        if self.backup_job.num_of_files_transferred + incremental_job.num_of_files_transferred != \
                full_job.num_of_files_transferred:
            self.status = constants.FAILED
            raise Exception("No of items backed up was not matched")
        else:
            self.log.info("Convert Job to Full was working fine.")

    def tear_down(self):
        self.log.info(f"8. Deleting {self.pub_team.mail} team")
        self.helper.delete_team(self.pub_team)











