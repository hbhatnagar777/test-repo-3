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
from Application.Teams.teams_client_helper import TeamsClientHelper

const = TeamsConstants()

msg_type = const.MessageType


class TestCase(CVTestCase):
    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Teams - Automation case to backup and restore Planner Tasks"
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.client = None
        self.tcinputs = {
            "ClientName": None,
            "source_team": None,
            "members": None,
            "Office365Plan": None
        }
        self.source_team = None
        self.destination_team = None

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client)
        self.plan = self.tcinputs.get("Office365Plan")
        self.log.info("create source team from input")
        self.source_team = self.helper.create_public_team(self.tcinputs['source_team'])
        self.log.info("Create destination team")
        self.destination_team = self.helper.create_public_team(members=self.tcinputs['members'])

    def run(self):
        """Main function for test case execution."""
        self.log.info('\t DISCOVERING & ADDING %s to CONTENT.', self.source_team.mail)
        self.helper.set_content([self.source_team.mail], self.plan)
        self.log.info("\t Running a BACKUP.")
        backup_job = self.helper.backup([self.source_team.mail])
        self.log.info(f"Backup job - {backup_job.job_id}")
        restore_job = self.helper.out_of_place_restore(self.source_team.mail, self.destination_team.mail)
        self.log.info(f"Restore job - {restore_job.job_id}")
        self.log.info("compare teams plans")
        if self.helper.compare_teams_plans(self.source_team.id, self.destination_team.id):
            self.log.info("Backup and restore of planner Tasks working fine")
        else:
            raise Exception("Backup and restore of planner Tasks not working")

    def tear_down(self):
        """Tear down function for this testcase."""
        self.helper.delete_team(self.destination_team)
        self.log.info("Removing Team from Content\n")
        self.helper.remove_team_association([self.source_team.mail])

