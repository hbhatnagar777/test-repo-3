# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

    __init__()  --  Initialize TestCase class.

    setup()     --  Initializes pre-requisites for this test case.

    run()       --  Executes the test case steps.

    teardown()  --  Performs final clean up after test case execution.


"""


from Application.Teams.teams_client_helper import TeamsClientHelper
from AutomationUtils.cvtestcase import CVTestCase
from  Application.Teams.token import Token
from Application.Teams.teams_helper import TeamsHelper
from Reports.utils import TestCaseUtils
from Application.Teams.teams_constants import TeamsConstants
from AutomationUtils import constants


class TestCase(CVTestCase):
    """
    Class for executing Test Case for Basic gcc high cloud client creation and verification of backup, restore

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic gcc high cloud client creation and verification of backup, restore"
        self.hub_utils = None
        self.utils = TestCaseUtils(self)
        self.teams_client_helper = None
        self.client = None
        self.teams_helper = None
        self.source_team = None
        self.destination_team = None

    def run(self):
        try:
            self.teams_client_helper = TeamsClientHelper(self.commcell)
            self.teams_client_helper.delete_client(self.tcinputs['clientname'])
            self.client = self.teams_client_helper.create_client(client_name=self.tcinputs['clientname'],
                                                                 server_plan=self.tcinputs['ServerPlan'],
                                                                 index_server=self.tcinputs['index_server'],
                                                                 access_nodes_list=[self.tcinputs['access_node']],
                                                                 cloud_region=TeamsConstants.CloudRegion.GccHigh)
            token = Token.get_token_instance(Token)

            self.teams_helper = TeamsHelper(self.client)
            Token.cloud_region = TeamsConstants.CloudRegion.GccHigh
            token.refresh()
            self.log.info("Creating source team")
            self.source_team = self.teams_helper.create_public_team(members=self.tcinputs['members'])
            self.log.info("Creating destination team")
            self.destination_team = self.teams_helper.create_public_team(members=self.tcinputs['members'])
            general_channel = self.source_team.channels['General']
            self.log.info("post messages to the general channel")
            for _ in range(10):
                self.teams_helper.post_text_to_channel(general_channel, message_type=TeamsConstants.MessageType.TEXT)
            self.log.info("upload files to the channel")
            for _ in range(5):
                self.teams_helper.upload_file(general_channel)
            self.log.info(f"Adding {self.source_team.mail} to the content")
            self.teams_helper.set_content([self.source_team.mail], self.tcinputs['Office365Plan'])
            self.log.info("Running a backup job")
            backup_job = self.teams_helper.backup([self.source_team])
            self.log.info(f"Backup job - {backup_job.job_id}")
            if backup_job.status.upper() != "COMPLETED":
                raise Exception("backup job not completed successfully")
            self.log.info("Running a restore job")
            restore_job = self.teams_helper.restore_posts_to_html(self.source_team.mail, self.destination_team.mail)
            self.log.info(f"Restore job - {restore_job.job_id}")
            if restore_job.status.upper() != "COMPLETED":
                raise Exception("restore job not completed successfully")
            self.log.info("Backup and restore working fine")

        except Exception as ex:
            self.log.info(ex)
            self.status = constants.FAILED

    def tear_down(self):
        self.teams_helper.delete_team(self.source_team)
        self.teams_helper.delete_team(self.destination_team)
        self.teams_client_helper.delete_client(self.tcinputs['clientname'])



