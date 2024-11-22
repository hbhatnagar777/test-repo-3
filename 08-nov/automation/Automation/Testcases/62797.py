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
        self.name = "Teams - kill the job while processing the team."
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.tcinputs = {"ClientName": None, "username": None, "password": None, "Office365Plan": None, "BackupTeamMembers": None}
        self.teams_obj_list = []
        self.teams_mail_list = []
        self.members = None
        self.no_of_teams_to_create = 6
        self.status = constants.FAILED

    def setup(self):
        """Setup function of this test case."""
        self.plan = self.tcinputs.get("Office365Plan")
        self.helper = TeamsHelper(self.client, self)
        self.members = self.tcinputs.get("BackupTeamMembers")

        self.log.info('--------------------\n')
        self.log.info('Setting Up Test Data\n')
        self.log.info('--------------------\n')

        self.log.info('Creating Multiple Public Teams\n')
        for team in range(self.no_of_teams_to_create):
            self.teams_obj_list.append(self.helper.create_public_team(f"AutoCreateTeam_{int(time.time())}", self.members))

        for team in self.teams_obj_list:
            self.teams_mail_list.append(team.mail)
            self.log.info(f'Creating Standard channel for team {team.name}')
            self.helper.create_standard_channel(team)
            for channel in team.channels:
                self.log.info(f'Uploading some posts and files to channel {team.channels.get(channel).name} of team {team.name}')
                self.helper.post_text_to_channel(team.channels.get(channel), msg_type.TEXT)
                self.helper.upload_file(team.channels.get(channel))

    def run(self):
        """Main function for test case execution."""
        try:

            self.helper._subclient.update_properties({"commonProperties": {"numberOfBackupStreams": 1}})

            self.log.info(f"Discovering and Adding All Teams To Content\n")
            self.helper.set_content(self.teams_mail_list, self.plan)

            self.log.info("Run a backup Job\n")
            backup_job = self.helper.backup(self.teams_mail_list, False)
            self.log.info(f"Backup job ID - {backup_job.job_id} \n")

            if self.helper.get_folders_in_jr(4, backup_job.job_id):
                backup_job.kill()
                if backup_job.wait_for_completion() and backup_job.status.upper() == 'COMMITTED':
                    self.log.info("Backup Job successfully killed and items got committed")
                else:
                    raise Exception("Status is not the expected one")
            else:
                raise Exception("Folders not matching the required ones")

            full_job_db_values = self.helper.match_delta_token({}, self.tcinputs.get("username"),
                                                               self.tcinputs.get("password"))
            if full_job_db_values:
                for team in self.teams_obj_list:
                    for channel in team.channels:
                        self.log.info(f'Uploading some posts and files to channel {team.channels.get(channel).name} of team {team.name}')
                        self.helper.post_text_to_channel(team.channels.get(channel), msg_type.TEXT)
                        self.helper.upload_file(team.channels.get(channel))

                self.log.info("Run a backup Job\n")
                backup_job = self.helper.backup(self.teams_mail_list)
                self.log.info(f"Backup job ID - {backup_job.job_id} \n")

                incr_job_db_values = self.helper.match_delta_token(full_job_db_values, self.tcinputs.get("username"),
                                                                   self.tcinputs.get("password"), delete_folders_at_end=True)
                if incr_job_db_values:
                    self.status = constants.PASSED
                    self.log.info("Test case passed successfully")
                else:
                    raise Exception("Test case failed due to mismatch in Incremental Job DB values")
            else:
                raise Exception("Test case failed due to mismatch in Full Job DB values")

        except Exception as ex:
            self.log.exception(ex)

        finally:
            self.log.info("Removing Team from Content\n")
            self.helper.remove_team_association(self.teams_mail_list)

            self.log.info("Deleting Source Teams")
            for i in self.teams_obj_list:
                self.helper.delete_team(i)

