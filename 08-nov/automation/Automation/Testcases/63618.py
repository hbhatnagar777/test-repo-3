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
    __init__()                  --  initialize TestCase class

    setup()                     --  sets up the variables required for running the testcase

    run()                       --  run function of this test case

    teardown()                  --  tears down the things created for running the testcase

    _initialize_sdk_objects()   --  initializes the sdk objects after app creation

"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.CloudApps.cloud_connector import CloudConnector
from Application.CloudApps import constants as cloud_apps_constants


class TestCase(CVTestCase):

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "OneDrive Client creation with Multiple Nodes and Express configuration and modification of configuration ,Cases Related to Manual Discovery"
        self.users = None
        self.cvcloud_object = None
        self.folder_structure = None
        self.machine = None
        self.item_count_to_backup = None
        self.client_name = None
        self.o365_plan = None
        self.number_of_docs = None
        self.number_of_incremental_docs = None
        self.tcinputs = {
            'ServerPlanName': None,
            'IndexServer': None,
            'AccessNodes': None,
            'O365Plan': None,
            'Users': None,
            'application_id': None,
            'application_key_value': None,
            'azure_directory_id': None,
        }

    def _initialize_sdk_objects(self):
        """Initializes the sdk objects after app creation"""

        self.log.info(f'Create client object for: {self.client_name}')
        self._client = self.commcell.clients.get(self.client_name)

        self.log.info(f'Create agent object for: {cloud_apps_constants.ONEDRIVE_AGENT}')
        self._agent = self._client.agents.get(cloud_apps_constants.ONEDRIVE_AGENT)

        self.log.info(f'Create instance object for: {cloud_apps_constants.ONEDRIVE_INSTANCE}')
        self._instance = self._agent.instances.get(cloud_apps_constants.ONEDRIVE_INSTANCE)

        self.log.info(f'Create backupset object for: {cloud_apps_constants.ONEDRIVE_BACKUPSET}')
        self._backupset = self._instance.backupsets.get(cloud_apps_constants.ONEDRIVE_BACKUPSET)

        self.log.info(f'Create sub-client object for: {cloud_apps_constants.ONEDRIVE_SUBCLIENT}')
        self._subclient = self._backupset.subclients.get(cloud_apps_constants.ONEDRIVE_SUBCLIENT)

    def setup(self):
        """Setup function of this test case"""
        self.client_name = "OD_63618"
        self.log.info(f'Checking if OneDrive client : {self.client_name} already exists')
        if self.commcell.clients.has_client(self.client_name):
            self.log.info(f'OneDrive client : {self.client_name} already exists, deleting the client')
            self.commcell.clients.delete(self.client_name)
            self.log.info(f'Successfully deleted OneDrive client : {self.client_name} ')
        else:
            self.log.info(f'OneDrive client : {self.client_name} does not exists')
        self.log.info(f'Creating new OneDrive client : {self.client_name}')
        self.commcell.clients.add_onedrive_for_business_client(client_name=self.client_name,
                                                     server_plan=self.tcinputs.get('ServerPlanName'),
                                                     azure_directory_id=self.tcinputs.get("azure_directory_id"),
                                                     azure_app_id=self.tcinputs.get("application_id"),
                                                     azure_app_key_id=self.tcinputs.get("application_key_value"),
                                                     **{
                                                         'index_server': self.tcinputs.get('IndexServer'),
                                                         'access_nodes_list': self.tcinputs.get('AccessNodes'),
                                                         'shared_jr_directory': self.tcinputs.get('shared_jr_directory'),
                                                         'user_name': self.tcinputs.get('user_name'),
                                                         'user_password': self.tcinputs.get('user_password'),
                                                     })
        self._initialize_sdk_objects()

        self.users = self.tcinputs['Users'].split(",")
        self.o365_plan = self.tcinputs['O365Plan']
        # Creating CloudConnector object
        self.cvcloud_object = CloudConnector(self)
        self.cvcloud_object.cvoperations.cleanup()

    def run(self):
        """Run function of this test case"""
        try:

            # Verify discovery completion or wait for discovery to complete
            self.log.info(f'Waiting until discovery is complete')
            self.subclient.run_subclient_discovery()
            self.subclient.verify_discovery_onedrive_for_business_client()

            # Add user to client
            self.log.info(f'Adding users: {self.users} to client')
            self.subclient.add_users_onedrive_for_business_client(self.users, self.o365_plan)

            # Modify configuration
            self.log.info('Modify configuration of client')
            self.subclient.data_readers=self.tcinputs['modified_streams_count']
            self.log.info(f'Streams Count Modified Successfully')
            self.client.modify_server_plan(self.tcinputs['ServerPlanName'],self.tcinputs['modified_server_plan'])
            self.log.info(f'Server Plan Modified Successfully')
            self.instance.modify_index_server(self.tcinputs['modified_index_server'])
            self.log.info(f'Index Server Modified Successfully')
            self.instance.modify_accessnodes(self.tcinputs['modified_accessnodes_list'],self.tcinputs['modified_user_name'],self.tcinputs['modified_user_password'])
            self.log.info(f'Accessnodes Modified Successfully')
            self.client.modify_job_results_directory(self.tcinputs['modified_shared_jr_directory'])
            self.log.info(f'Job Results Directory Modified Successfully')


        except Exception as exception:
            self.log.error(f'Failed to execute test case with error: {str(exception)}')
            self.result_string = str(exception)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.status == constants.PASSED:
                self.log.info(f'Test case status: {self.status}')
                # Delete the client if test case is successful
                self.cvcloud_object.cvoperations.delete_client(self.client_name)
                self.cvcloud_object.cvoperations.cleanup()
        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')
