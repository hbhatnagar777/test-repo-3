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

import sys

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Application.Teams.teams_helper import TeamsHelper
from Application.Teams.teams_constants import TeamsConstants

const = TeamsConstants()
msg_type = const.MessageType


class TestCase(CVTestCase):
    """Class for Teams - Verify incremental backups"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "MS Teams: Verify incremental job doesn't pick up old backed up data,by creating new channel in existing team"
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.tcinputs = {
            "ClientName": None,
            "Office365Plan": None,
            "BackupTeamMembers": None
        }
        self.created_team_list = []
        self.created_channel_list = {}

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client)
        self.plan = self.tcinputs.get("Office365Plan")
        self.log.info(f"STEP 1 - PREPARE TEAMS CLIENT.\n")
        self.log.info("\t1.01 - Remove all teams association from client")
        self.helper.remove_all_users_association()
        self.helper.remove_all_users_content()
        self.log.info(f"STEP 2 - CREATE TEST DATA.\n")
        self.log.info(f"\t2.01. Creating Public Teams")
        try:
            for i in range(2):
                self.created_team_list.append(
                    self.helper.create_public_team(members=self.tcinputs.get("BackupTeamMembers"))
                )
                self.log.info(f"\tCreated public team: {self.created_team_list[i].name}")
                self.log.info(f"\tCreating channel under team: {self.created_team_list[i].name}")
                channel_obj = self.helper.create_standard_channel(self.created_team_list[i])
                self.created_channel_list[self.created_team_list[i].name] = [channel_obj]
                self.log.info(f"\tCreating post under channel: {channel_obj.name}")
                self.helper.post_text_to_channel(
                    channel_obj, message_type=msg_type.TEXT,
                    message=f"Team Name- {self.created_team_list[i].name}, Channel: {channel_obj.name}"
                            f"This is post number:1")
                self.helper.post_text_to_channel(
                    channel_obj, message_type=msg_type.IMAGE
                )
                self.helper.post_text_to_channel(
                    channel_obj, message_type=msg_type.EMOJI
                )
                self.helper.upload_file(channel_obj)

        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            for team in self.created_team_list:
                self.helper.delete_team(team)
            self.helper.remove_all_users_association()
            self.helper.remove_all_users_content()
            raise Exception(ex)

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info(f"STEP 3 - ASSOCIATING CREATED TEAMS TO CLIENT.\n")
            self.log.info(f"\t3.01. Adding part of created teams to content.")
            created_teams_name = [team.mail for team in self.created_team_list]
            self.helper.set_content(created_teams_name, self.plan)
            self.log.info(f"\t4. Running backup job on client: {self.client.name}")
            full_job = self.helper.backup(created_teams_name)
            num_items_in_full_job = full_job.details['jobDetail']['detailInfo']['numOfObjects']
            self.log.info(f"Number of items in full job: {num_items_in_full_job}")
            self.log.info(f"Creating new channel in existing team")
            channel_obj = self.helper.create_standard_channel(self.created_team_list[0])
            self.created_channel_list[self.created_team_list[0].name].append(channel_obj)
            self.log.info(f"\tCreating post under channel: {channel_obj.name}")
            self.helper.post_text_to_channel(
                channel_obj, message_type=msg_type.TEXT,
                message=f"Team Name- {self.created_team_list[0].name}, Channel: {channel_obj.name}"
                        f"This is post number: 1")
            self.helper.post_text_to_channel(
                channel_obj, message_type=msg_type.IMAGE
            )
            self.helper.post_text_to_channel(
                channel_obj, message_type=msg_type.EMOJI
            )
            self.helper.upload_file(channel_obj)
            created_teams_name = [team.mail for team in self.created_team_list]
            self.helper.set_content(created_teams_name, self.plan)
            self.log.info(f"\t4. Running backup job on client: {self.client.name}")
            incremental_job = self.helper.backup(created_teams_name)
            num_items_in_inc_job = incremental_job.details['jobDetail']['detailInfo']['numOfObjects']
            self.log.info(f"Number of items in incremental job: {num_items_in_inc_job}")
            if num_items_in_inc_job > num_items_in_full_job or num_items_in_inc_job != 5:  # No.of Items Added Before Incremental Job are 5
                raise Exception("Incremental job ran as full")
            self.log.info("Incremental job running as expected")

        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            self.result_string = str(ex)
            self.status = constants.FAILED

        finally:
            for team in self.created_team_list:
                self.helper.delete_team(team)
            self.helper.remove_all_users_association()
            self.helper.remove_all_users_content()
