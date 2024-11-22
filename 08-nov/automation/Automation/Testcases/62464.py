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
        self.name = "OneDrive v2 OneNote backup/restore verification"
        self.users = None
        self.cvcloud_object = None
        self.o365_plan = None
        self.client_name = None
        self.out_of_place_destination_user = None
        self.tcinputs = {
            'ServerPlanName': None,
            'IndexServer': None,
            'AccessNodes': None,
            'O365Plan': None,
            'Users': None,
            'application_id': None,
            'application_key_value': None,
            'azure_directory_id': None,
            'out_of_place_destination_user': None
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
        self.client_name = "OD_62464"
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
                                                         'access_nodes_list': self.tcinputs.get('AccessNodes')
                                                     })
        self._initialize_sdk_objects()

        self.users = self.tcinputs['Users'].split(",")
        self.o365_plan = self.tcinputs['O365Plan']
        self.out_of_place_destination_user = self.tcinputs['out_of_place_destination_user']

        # Creating CloudConnector object
        self.cvcloud_object = CloudConnector(self)
        self.cvcloud_object.cvoperations.cleanup()

    def run(self):
        """Run function of this test case"""
        try:
            # Delete and generate new OneNote data
            self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.users[0])
            self.cvcloud_object.one_drive.generate_onenote_data(user_id=self.users[0],
                                                                notebook_count=2,
                                                                section_group_count=1,
                                                                section_group_depth=2,
                                                                section_count=1,
                                                                page_count=1)

            # Get metadata of Notebooks folder
            metadata = self.cvcloud_object.one_drive.list_onenote_items(self.users[0])

            # Verify discovery completion or wait for discovery to complete
            self.log.info(f'Waiting until discovery is complete')
            self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()

            # Add users to client
            self.log.info(f'Adding users: {self.users} to client')
            self.subclient.add_users_onedrive_for_business_client(self.users, self.o365_plan)

            # backup user
            self.log.info('Run sub-client level backup')
            backup_level = constants.backup_level.INCREMENTAL.value
            job = self.client.backup_all_users_in_client()
            self.cvcloud_object.cvoperations.check_job_status(job=job, backup_level_tc=backup_level)

            # Delete Data on OneDrive Notebook folder
            self.log.info('Deleting data on in-place user\'s onedrive')
            self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.users[0])

            # in-place restore
            restore_level = 'RESTORE'
            self.log.info(f'Run in-place restore for user: {self.users}')
            in_place_restore_job = self.client.in_place_restore(self.users)
            self.cvcloud_object.cvoperations.check_job_status(job=in_place_restore_job,
                                                              backup_level_tc=restore_level)

            # cross check restored data
            self.cvcloud_object.one_drive.compare_onenote_restore_metadata(self.users[0], metadata)

            # Out of place + skip option
            # Delete data on out-of-place user's OneDrive
            self.log.info('Deleting data on out-of-place user\'s onedrive')
            self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.out_of_place_destination_user)

            # Run out-of-place restore
            self.log.info(f'Run out-of-place restore for user: {self.users}')
            out_of_place_restore_job = self.client.out_of_place_restore(self.users, self.out_of_place_destination_user)
            self.cvcloud_object.cvoperations.check_job_status(job=out_of_place_restore_job,
                                                              backup_level_tc=restore_level)

            # Get metadata for out-of-place user
            self.log.info('Fetch one-note metadata after out-of-place restore')
            out_of_place_metadata = self.cvcloud_object.one_drive.list_onenote_items(self.out_of_place_destination_user)

            # cross check restored data
            self.cvcloud_object.one_drive.compare_onenote_restore_metadata(self.users[0], out_of_place_metadata)

            # TODO: Implement skip, overwrite and restore as copy options

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
                # Clear user's Onedrive
                self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.users[0])
                # Clear data on destination user's drive
                self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.out_of_place_destination_user)
                self.cvcloud_object.cvoperations.cleanup()
        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')
