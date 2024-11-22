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
import time


class TestCase(CVTestCase):
    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Microsoft O365 Teams - Acceptance"
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
        self.created_team_list = []

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client)
        self.plan = self.tcinputs.get("Office365Plan")
        self.log.info("--------------------------------------")
        self.log.info(f"STEP 1 - PREPARE TEAMS CLIENT.")
        self.log.info("--------------------------------------\n")
        self.log.info("\t1.01 - Get all associated teams with client")
        users = self.helper.get_associated_teams_type()
        if len(users['manual']) > 0:
            self.log.info("\t1.02 - Remove all manually associated teams with client")
            self.helper.remove_team_association(users['manual'])
        self.log.info("\t1.04 Removing all teams association from content")
        self.helper.remove_all_users_content()

    def run(self):
        """Main function for test case execution."""

        try:
            self.log.info("-------------------------")
            self.log.info(f"STEP 2 - VERIFY DISCOVERY AFTER ADDING A TEAM.")
            self.log.info("-------------------------\n")
            backup_team_name = f"AT_PUB_Disc1_{int(time.time())}"
            self.log.info(f"\t2.01. Create a public team: {backup_team_name}")
            self.pub_team = self.helper.create_public_team(
                backup_team_name, self.tcinputs.get("BackupTeamMembers")
            )
            self.created_team_list.append(self.pub_team)
            self.log.info(f"\t2.02. Discovering teams after creating team: {self.pub_team.name}")
            discovered_teams = self.helper.discover()
            if self.pub_team.mail not in discovered_teams:
                raise Exception(f"Discovery failed after adding team: {self.pub_team.name}")
            self.log.info("Discovery successfully verified after adding a team")
            self.log.info("--------------------------------------------------------")
            self.log.info(f"STEP 3 - VERIFY DISCOVERY AFTER DELETING A TEAM.")
            self.log.info("--------------------------------------------------------\n")
            self.log.info(f"\t3.01. Deleting team: {self.pub_team.name}")
            self.helper.delete_team(self.pub_team)
            self.log.info(f"\t3.02. Discovering teams after deleting team: {self.pub_team.name}")
            time.sleep(100)
            discovered_teams = self.helper.discover()
            self.log.info(f"\t3.03. Verifying discovery after deletion of team: {self.pub_team.name}")
            if self.pub_team.mail in discovered_teams:
                self.log.info(f"Discovery failed after deleting team: {self.pub_team.name}.\nThis might be"
                              f"due to caching of team in MS Teams")
            else:
                self.pub_team = None

            self.log.info("--------------------------------------------------------")
            self.log.info(f"STEP 4 - ADD SOME TEAMS AS MANUAL AND REST AS AUTO.")
            self.log.info("--------------------------------------------------------\n")
            discovered_teams = self.helper.discover()
            teams = []
            for team in discovered_teams.values():
                teams.append(team['smtpAddress'])
            teams_len = len(teams)
            teams_auto = teams[int(teams_len/2):] if teams_len & 1 == 0 else teams[int(teams_len/2) - 1:]
            teams_manual = teams[:int(teams_len/2)] if teams_len & 1 == 0 else teams[:int(teams_len/2) - 1]
            self.log.info("\t4.01 Adding half of the discovered teams as manual")
            self.helper.set_content(teams_manual, self.plan)
            self.log.info("\t4.02 Adding half of the discovered teams as auto")
            self.helper.set_all_users_content(self.plan)
            self.log.info("\t4.03 Verifying association of manual teams")
            if not self.helper.verify_manual_association(teams_manual):
                raise Exception("Verification of manually associated users failed")
            self.log.info("\t4.04 Verifying association of auto discovered teams")
            if not self.helper.verify_auto_association(teams_auto):
                raise Exception("Verification of auto associated users failed")

            self.log.info("--------------------------------------------------------")
            self.log.info(f"STEP 5 - ADD ALL TEAMS USING AUTO DISCOVERY.")
            self.log.info("--------------------------------------------------------\n")

            self.log.info("\t5.01 Removing previously manually associated teams")
            self.helper.remove_team_association(teams_manual)
            self.log.info("\t5.02 Removing previously auto associated teams")
            self.helper.remove_all_users_content()
            self.log.info("\t5.03 Adding teams using auto discovery")
            self.helper.set_all_users_content(self.plan)
            time.sleep(100)
            self.log.info("\t5.04 Verifying teams discovery type")
            self.helper.verify_auto_association()

            self.log.info("--------------------------------------------------------")
            self.log.info(f"STEP 6 - REMOVE ALL TEAMS USING AUTO DISCOVERY.")
            self.log.info("--------------------------------------------------------\n")

            self.log.info("\t6.01 Removing teams using auto discovery")
            self.helper.remove_all_users_content()
            self.log.info("\t6.02 Validating removal of teams using auto discovery")
            time.sleep(100)
            assoc_teams = self.helper.get_associated_teams()
            if assoc_teams and len(assoc_teams) > 0:
                raise Exception("Validation of removal of teams using auto discovery failed")
            self.log.info("--------------------------------------------------------")
            self.log.info(f"STEP 7 - EXCLUDE TEAMS FROM A CLIENT.")
            self.log.info("--------------------------------------------------------\n")

            self.log.info("\t7.01 Discovering teams")
            discovered_teams = self.helper.discover()
            teams = []
            i = 0
            for team in discovered_teams.values():
                teams.append(team['smtpAddress'])
                i += 1
                if i > 2:
                    break
            self.log.info(f"\t7.02 Adding teams: {teams} manually")
            self.helper.set_content(teams, self.plan)
            self.log.info(f"\t7.03 Excluding teams: {teams} from backup")
            self.helper.exclude_teams_from_backup(teams)
            self.log.info("\t7.04 Adding all teams through auto discovery")
            self.helper.set_all_users_content(self.plan)
            self.log.info("\t7.05 Verifying excluded teams")
            if self.helper.verify_exclude_teams(self.plan):
                self.log.info("\tExclusion of team successfully verified")
            else:
                raise Exception("\tValidation of exclusion of team failed")
        except Exception as ex:
            self.log.exception(ex)

        finally:
            if self.pub_team:
                self.helper.delete_team(self.pub_team)
