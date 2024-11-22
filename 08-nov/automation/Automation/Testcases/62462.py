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
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "OneDrive v2 different types of file backup/restore test"
        self.users = None
        self.cvcloud_object = None
        self.out_of_place_destination_user = None
        self.o365_plan = None
        self.client_name = None
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
        self.client_name = "OD_62462"
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
        self.proxy_client = self.tcinputs['proxy_client']

        # Creating CloudConnector object
        self.cvcloud_object = CloudConnector(self)
        self.cvcloud_object.cvoperations.cleanup()

    def run(self):
        """Run function of this test case"""
        try:
            # Verify discovery completion or wait for discovery to complete
            self.log.info(f'Waiting until discovery is complete')
            self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()

            # Add users to client
            self.log.info(f'Adding users: {self.users} to client')
            self.subclient.add_users_onedrive_for_business_client(self.users, self.o365_plan)

            # Run incremental backup
            self.log.info('Run sub-client level backup')
            backup_level = constants.backup_level.INCREMENTAL.value
            job = self.client.backup_all_users_in_client()
            self.cvcloud_object.cvoperations.check_job_status(job=job, backup_level_tc=backup_level)

            restore_level = 'RESTORE'
            # Loop over users and check for out-of-place and disk restores
            for user in self.users:
                # Delete data on destination user's OneDrive
                self.log.info(f'Deleting data on destination user\'s drive [{self.out_of_place_destination_user}]')
                self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.out_of_place_destination_user)

                # Out-of-place restore
                self.log.info(f'Run out-of-place restore for user: {user} to : {self.out_of_place_destination_user}')
                out_of_place_restore = self.client.out_of_place_restore([user], self.out_of_place_destination_user)
                self.cvcloud_object.cvoperations.check_job_status(job=out_of_place_restore,
                                                                  backup_level_tc=restore_level)

                # check out-of-place restore data
                self.log.info(f'Verify that restore was successful for user {user}')
                self.cvcloud_object.one_drive.compare_content_of_two_folders(
                    user_id1=user,
                    user_id2=self.out_of_place_destination_user,
                    check_folder_level=False)

                # Delete directory on proxy if exists
                destination_user_path = f'{cloud_apps_constants.DESTINATION_TO_DISK}\\{user}'
                proxy_client = Machine(self.proxy_client, self.commcell)
                if proxy_client.check_directory_exists(destination_user_path):
                    proxy_client.remove_directory(destination_user_path)

                # Disk restore
                self.log.info(f'Run disk restore for user: {user} to client : [{self.proxy_client}]')
                disk_restore = self.client.disk_restore(self.users,
                                                        self.proxy_client,
                                                        cloud_apps_constants.DESTINATION_TO_DISK)
                self.cvcloud_object.cvoperations.check_job_status(job=disk_restore, backup_level_tc=restore_level)

                # check disk restore data
                self.cvcloud_object.one_drive.compare_file_properties(oop=True, to_disk=True, user_id=user)

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
                # Clear data on destination user's drive
                self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.out_of_place_destination_user)
                self.cvcloud_object.cvoperations.cleanup()
        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')
