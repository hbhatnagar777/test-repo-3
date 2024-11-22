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
from Application.Teams.solr_helper import SolrHelper
import time

const = TeamsConstants()

msg_type = const.MessageType


class TestCase(CVTestCase):
    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Create different types of Posts, backup and restore them to cross tenant and verify the integrity"
        self.show_to_user = True
        self.source_helper = None
        self.destination_helper = None
        self.destination_client_obj = None
        self.plan = None
        self.tcinputs = {"ClientName": None, "Office365Plan": None, "DestinationDetails": None}
        self.pub_team = None
        self.pub_team_std_ch = None
        self.destination_team = None
        self.destination_members = None
        self.no_of_objects = 0

    def setup(self):
        """Setup function of this test case."""
        self.plan = self.tcinputs.get("Office365Plan")
        self.source_helper = TeamsHelper(self.client, self)
        self.destination_members = self.tcinputs.get("DestinationDetails").get("TeamMembers")
        self.destination_client_obj = self.commcell.clients.get(
            self.tcinputs.get("DestinationDetails").get("ClientName"))
        self.destination_helper = TeamsHelper(self.destination_client_obj)
        self.log.info('Creating Public Team\n')
        source_team_name = f"AutoCreateTeam_{int(time.time())}"
        self.pub_team = self.source_helper.create_public_team(source_team_name, self.tcinputs.get("SourceMembers"))
        if self.pub_team:
            self.no_of_objects += 7

        self.log.info('Creating Standard Channel for Public Team\n')
        self.pub_team_std_ch = self.source_helper.create_standard_channel(self.pub_team)
        if self.pub_team_std_ch:
            self.no_of_objects += 4

        self.log.info(f'Posting Posts to Channel {self.pub_team_std_ch.name} of Team {self.pub_team.name}\n')
        self.source_helper.post_text_to_channel(self.pub_team_std_ch, msg_type.TEXT)
        self.source_helper.post_text_reply_to_channel(self.pub_team_std_ch, msg_type.TEXT)
        self.source_helper.post_text_to_channel(self.pub_team_std_ch, msg_type.IMAGE)

        self.log.info(f'Uploading Files to Channel {self.pub_team_std_ch.name} of Team {self.pub_team.name}\n')
        self.source_helper.upload_file(self.pub_team_std_ch)
        self.source_helper.upload_file(self.pub_team_std_ch)
        self.log.info(f"Create STANDARD team as destination for restore.\n")
        destination_team_name = f"AutoCreateTeam_{int(time.time())}"
        self.destination_team = self.destination_helper.create_public_team(destination_team_name,
                                                                           self.destination_members,
                                                                           cross_tenant_details=
                                                                           self.tcinputs.get("DestinationDetails"))

    def run(self):
        """Main function for test case execution."""
        try:
            self.log.info(f"Discovering and Adding Team {self.pub_team.name} To Content\n")
            self.source_helper.set_content([self.pub_team.mail], self.plan)

            self.log.info("Run a backup Job\n")
            backup_job = self.source_helper.backup([self.pub_team.mail])
            self.log.info(f"Backup job ID - {backup_job.job_id} \n")

            if backup_job.status.upper() != "COMPLETED":
                raise Exception(f"Backup job {backup_job.job_id} did not complete successfully.")

            self.log.info("Checking if playback succeeded")
            solrhelper_obj = SolrHelper(self.source_helper)
            if solrhelper_obj._check_all_items_played_successfully(backup_job.job_id):
                self.log.info(f"Playback successful for Job ID {backup_job.job_id}")
            else:
                raise Exception(f"Playback failed for Job ID {backup_job.job_id}")

            self.log.info("Restore TEAMS OUT OF PLACE, ensure it completes.\n")
            restore_job = self.source_helper.out_of_place_restore(self.pub_team.mail, self.destination_team.mail,
                                                                  dest_helper_obj=self.destination_helper)
            self.log.info(f"Restore job ID - {restore_job.job_id} \n")
            if restore_job.status.upper() != "COMPLETED":
                raise Exception(f"Restore job {restore_job.job_id} did not complete successfully.")
            self.log.info("cross tenant restore verified ")
        except Exception as ex:
            self.log.exception(ex)
        finally:
            self.log.info("Removing Team from Content\n")
            self.source_helper.remove_team_association([self.pub_team.mail])
            self.log.info("Deleting All Teams")
            self.source_helper.delete_team(self.pub_team)
            self.destination_helper.delete_team(self.destination_team, cross_tenant_details=self.tcinputs.get("DestinationDetails"))
