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
from Application.Teams.teams_helper import TeamsHelper
from Reports.utils import TestCaseUtils
from AutomationUtils import constants
from Application.Teams.solr_helper import SolrHelper
from Application.Teams.teams_constants import TeamsConstants
import json


class TestCase(CVTestCase):
    """
    Class for executing Test Case for Microsoft O365 Teams - Verify retention

    """
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Microsoft O365 Teams - Verify retention"
        self.hub_utils = None
        self.utils = TestCaseUtils(self)
        self.teams_client_helper = None
        self.client = None
        self.teams_helper = None
        self.source_team = None
        self.solr_helper = None

    def verify_retention_for_item(self, item_id):
        self.solr_helper = SolrHelper(self.teams_helper)
        response = self.solr_helper.create_url_and_get_response(
            select_dict={'TeamsItemId': item_id},
            op_params={'wt': 'json'})
        response = json.loads(response.content)
        response = response["response"]
        document = response['docs'][0]
        if document['IsVisible'] != False:
            raise Exception("Retention not working properly")
        self.log.info("Retention working properly")

    def update_item_property_in_solr(self, field_name, field_value, content_id):
        try:
            update_values={}
            update_values[field_name] = field_value
            self.solr_helper.update_document(content_id, update_values)
        except Exception as ex:
            raise Exception(ex)

    def run(self):
        try:
            self.teams_client_helper = TeamsClientHelper(self.commcell)
            self.teams_client_helper.delete_client(self.tcinputs['clientname'])
            self.client = self.teams_client_helper.create_client(client_name=self.tcinputs['clientname'],
                                                                 server_plan=self.tcinputs['ServerPlan'],
                                                                 index_server=self.tcinputs['IndexServer'],
                                                                 access_nodes_list=[self.tcinputs['access_node']])

            self.teams_helper = TeamsHelper(self.client, self)
            self.log.info("Creating source team")
            self.source_team = self.teams_helper.create_public_team(members=self.tcinputs['members'])
            general_channel = self.source_team.channels['General']
            self.log.info("upload files to the channel")
            flag, resp = self.teams_helper.upload_file(general_channel)
            file_id = resp['id']
            file_name = resp['name']
            self.log.info(f"Adding {self.source_team.mail} to the content")
            self.teams_helper.set_content([self.source_team], self.tcinputs['Office365Plan'])
            self.log.info("Running a backup job")
            backup_job = self.teams_helper.backup([self.source_team])
            self.log.info(f"Backup job - {backup_job.job_id}")
            if backup_job.status.upper() != "COMPLETED":
                raise Exception("backup job not completed successfully")
            self.log.info(f'deleting file with {file_id}')
            general_channel.delete_item(file_id)
            self.log.info('Run a backup job again')
            backup_job = self.teams_helper.backup([self.source_team])
            self.log.info(f"Backup job - {backup_job.job_id}")
            if backup_job.status.upper() != "COMPLETED":
                raise Exception("backup job not completed successfully")
            self.solr_helper = SolrHelper(self.teams_helper)
            response = self.solr_helper.create_url_and_get_response(
                select_dict={'TeamsItemId': file_id},
                op_params={'wt': 'json'})
            response = json.loads(response.content)
            response = response["response"]
            document = response['docs'][0]
            new_date_as_int = self.solr_helper.subtract_retention_time(document["DateDeleted"], 500)
            self.update_item_property_in_solr('DateDeleted', new_date_as_int, document['contentid'])
            self.teams_helper._subclient.process_index_retention_rules(TeamsConstants.INDEX_APP_TYPE,
                                                                       self.tcinputs['IndexServer'])
            self.verify_retention_for_item(file_id)

        except Exception as ex:
            self.log.info(ex)
            self.status = constants.FAILED

    def tear_down(self):
        self.teams_helper.delete_team(self.source_team)
        self.teams_client_helper.delete_client(self.tcinputs['clientname'])



