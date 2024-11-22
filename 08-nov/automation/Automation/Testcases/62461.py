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
from AutomationUtils.machine import Machine
from Application.CloudApps import constants as cloud_apps_constants


class TestCase(CVTestCase):

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "OneDrive v2 failed items check"
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
            'item_count_to_backup': None,
            'number_of_docs': None,
            'number_of_incremental_docs': None,  # Number of new documents added for last incremental backup job
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
        self.client_name = "OD_62461"
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
        self.item_count_to_backup = self.tcinputs['item_count_to_backup']
        self.number_of_docs = self.tcinputs['number_of_docs']
        self.number_of_incremental_docs = self.tcinputs['number_of_incremental_docs']
        # Creating CloudConnector object
        self.cvcloud_object = CloudConnector(self)
        self.cvcloud_object.cvoperations.cleanup()

    def run(self):
        """Run function of this test case"""
        try:
            # Clear user's onedrive and add data to user
            self.log.info(f'Generating new data on {self.users[0]}\'s OneDrive')
            self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.users[0])
            self.cvcloud_object.one_drive.create_files(no_of_docs=self.number_of_docs, user=self.users[0])

            # Verify discovery completion or wait for discovery to complete
            self.log.info(f'Waiting until discovery is complete')
            self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()

            # Get number of files on OneDrive
            self.log.info(f'Fetching number of files on user\'s drive')
            folder_structure = self.cvcloud_object.one_drive.get_all_onedrive_items(self.users[0])
            number_of_files_one_drive = len(folder_structure['root'][1][0]['AutomationFolder'][0])  # Automation Folder

            # Add user to client
            self.log.info(f'Adding users: {self.users} to client')
            self.subclient.add_users_onedrive_for_business_client(self.users, self.o365_plan)

            # set registry key to simulate backup file failure
            self.log.info('Setting registry key on access node to simulate backup failure')
            self.machine = Machine(self.tcinputs['AccessNodes'][0], commcell_object=self.commcell)
            self.machine.create_registry(cloud_apps_constants.REG_KEY_IDATAAGENT,
                                         cloud_apps_constants.SIMULATE_FAILURE_ITEMS_KEY,
                                         self.item_count_to_backup,
                                         reg_type=cloud_apps_constants.SIMULATE_FAILURE_ITEMS_REG_TYPE)

            # Run 1st incremental backup
            self.log.info('Run 1st incremental level backup')
            backup_level = constants.backup_level.INCREMENTAL.value
            job = self.client.backup_all_users_in_client()
            self.cvcloud_object.cvoperations.check_job_status(job=job, backup_level_tc=backup_level)

            # (backed up items + failed items = files on one-drive)
            number_of_files_transferred = self.cvcloud_object.cvoperations.get_number_of_successful_items(job)
            number_of_files_failed = self.cvcloud_object.cvoperations.get_number_of_failed_items(job)
            self.log.info(f'Number of files transferred in 1st job: {number_of_files_transferred} '
                          f'Number of files failed in 1st job: {number_of_files_failed}')

            assert number_of_files_transferred + number_of_files_failed == number_of_files_one_drive-1, \
                'Sum of backed-up and failed files does not match file count on OneDrive'

            # remove registry key
            self.log.info('Remove registry key from access node')
            self.machine.remove_registry(cloud_apps_constants.REG_KEY_IDATAAGENT,
                                         cloud_apps_constants.SIMULATE_FAILURE_ITEMS_KEY)
            self.log.info('Removed the registry key successfully')

            # Run 2nd incremental backup
            self.log.info('Run 2nd incremental level backup')
            second_incremental_job = self.client.backup_all_users_in_client()
            self.cvcloud_object.cvoperations.check_job_status(job=second_incremental_job, backup_level_tc=backup_level)

            # backed up count = previous failed items count
            number_of_files_in_2nd_backup_job = self.cvcloud_object.cvoperations.get_number_of_successful_items(
                second_incremental_job)
            self.log.info(f'Files transferred in 2nd incremental backup job: {number_of_files_in_2nd_backup_job}')

            assert number_of_files_failed == number_of_files_in_2nd_backup_job, \
                'Count of files transferred in second job does not match with count of failed files in first job'

            # Add new files to drive
            self.log.info(f'Adding {self.number_of_incremental_docs} more files to OneDrive')
            self.cvcloud_object.one_drive.create_files(no_of_docs=self.number_of_incremental_docs, user=self.users[0])

            # Run 3rd incremental backup
            self.log.info('Run 3rd incremental level backup')
            third_incremental_job = self.subclient.backup(backup_level=backup_level)
            self.cvcloud_object.cvoperations.check_job_status(job=third_incremental_job, backup_level_tc=backup_level)

            # check if only newly added files are backed up
            number_of_files_in_3rd_backup_job = self.cvcloud_object.cvoperations.get_number_of_successful_items(
                third_incremental_job)
            self.log.info(f'Files transferred in 3rd incremental backup job: {number_of_files_in_3rd_backup_job}')

            assert self.number_of_incremental_docs == number_of_files_in_3rd_backup_job, \
                'Count of files transferred in third backup job does not match with count of files added to OneDrive'

        except Exception as exception:
            self.log.error(f'Failed to execute test case with error: {str(exception)}')
            self.result_string = str(exception)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            # Check if registry exists
            if self.machine.check_registry_exists(cloud_apps_constants.REG_KEY_IDATAAGENT,
                                                  cloud_apps_constants.SIMULATE_FAILURE_ITEMS_KEY):
                self.log.info('Remove registry key from access node')
                self.machine.remove_registry(cloud_apps_constants.REG_KEY_IDATAAGENT,
                                             cloud_apps_constants.SIMULATE_FAILURE_ITEMS_KEY)
                self.log.info('Removed the registry key successfully')

            if self.status == constants.PASSED:
                self.log.info(f'Test case status: {self.status}')
                # Delete the client if test case is successful
                self.cvcloud_object.cvoperations.delete_client(self.client_name)
                # Clear user's Onedrive
                self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.users[0])
                self.cvcloud_object.cvoperations.cleanup()
        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')
