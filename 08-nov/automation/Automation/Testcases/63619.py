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
        self.name = "Verification of OneDrive V2 agent's user level backup and and Point in Time Restore using in place restore and out of place restore"
        self.users = None
        self.cvcloud_object = None
        self.folder_structure = None
        self.machine = None
        self.item_count_to_backup = None
        self.client_name = None
        self.o365_plan = None
        self.number_of_docs = None
        self.number_of_incremental_docs = None
        self.start_time = None
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
        self.client_name = "OD_63619"
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
        # Creating CloudConnector object
        self.cvcloud_object = CloudConnector(self)
        self.cvcloud_object.cvoperations.cleanup()

        # Data generation
        for user in self.users:
            self.cvcloud_object.one_drive.delete_all_data_on_onedrive(user)
            self.cvcloud_object.one_drive.create_files(
                user=user,
                no_of_docs=self.tcinputs['first_user_items'],
                new_folder=False)

    def run_user_level_backup_job(self,users_list):
        """
        running a backup job for selected users

        Args:
            users_list(list): list of users
        """
        job = self.subclient.run_user_level_backup_onedrive_for_business_client(users_list)
        self.log.info("Backup job: %s", str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Job {0} Failed with {1}".format(
                    job.job_id, job.delay_reason))
        self.log.info("Backup job %s is completed", job.job_id)
        return job

    def run_PIT_restore_job(self,users,time,dest_path=None):
        """
        run point in time restore job

        Args:
            users(list): list of users
            dest_path(str): SMTP address of distination user for OOP restore
        """
        if dest_path:
            job = self.subclient.point_in_time_out_of_place_restore_onedrive_for_business_client(users, end_time=time,destination_path=dest_path,overwrite=True,skip_file_permissions=True)
        else:
            job = self.subclient.point_in_time_in_place_restore_onedrive_for_business_client(users,end_time=time,overwrite=True,skip_file_permissions=True)
        self.log.info("Restore job: %s", str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Job {0} Failed with {1}".format(
                    job.job_id, job.delay_reason))
        self.log.info("Restore job %s is completed", job.job_id)
        return job

    def run(self):
        """Run function of this test case"""
        try:

            # Verify discovery completion or wait for discovery to complete
            self.log.info(f'Waiting until discovery is complete')
            self.subclient.run_subclient_discovery()
            self.subclient.verify_discovery_onedrive_for_business_client()

            # Add users to client
            self.log.info(f'Adding users: {self.users} to client')
            self.subclient.add_users_onedrive_for_business_client(self.users, self.o365_plan)

            # Running backup for first user
            first_user_full_backup_job=self.run_user_level_backup_job([self.users[0]])
            first_user_full_backup_time = first_user_full_backup_job.details["jobDetail"]["detailInfo"]["endTime"]
            items_backed_up_first_user_full_job = first_user_full_backup_job.details["jobDetail"]["detailInfo"]["numOfObjects"]
            if items_backed_up_first_user_full_job==self.tcinputs['first_user_items']:
                self.log.info(f'first user backed up successfully')
            else:
                raise Exception("first user not backed up successfully")

            # Running backup for other two users
            other_users_full_backup_job=self.run_user_level_backup_job([self.users[1],self.users[2]])
            items_backed_up_other_users_full_job = other_users_full_backup_job.details["jobDetail"]["detailInfo"]["numOfObjects"]
            if items_backed_up_other_users_full_job == self.tcinputs['other_users_items']:
                self.log.info(f'other two users backed up successfully')
            else:
                raise Exception("other two users not backed up successfully")

            # Data generation for incremental job of first user
            self.cvcloud_object.one_drive.create_files(
                user=self.users[0],
                no_of_docs=self.tcinputs['first_user_incremental_items'],
                new_folder=False)

            # Running incremental backup job for first user
            first_user_incremental_backup_job = self.run_user_level_backup_job([self.users[0]])
            items_backed_up_incremental_job = first_user_incremental_backup_job.details["jobDetail"]["detailInfo"]["numOfObjects"]
            if items_backed_up_incremental_job==self.tcinputs['first_user_incremental_items']:
                self.log.info(f'first user incremental job completed successfully')
            else:
                raise Exception("first user incremental job not completed successfully")

            # Running inplace point in time restore for first user
            in_place_restore_job=self.run_PIT_restore_job([self.users[0]],first_user_full_backup_time)
            inplace_PIT_restore_count=in_place_restore_job.details["jobDetail"]["detailInfo"]["numOfObjects"]
            if inplace_PIT_restore_count-1==items_backed_up_first_user_full_job:   # Automation folder is restored
                self.log.info(f'Inplace PIT Restore verified successfully')
            else:
                raise Exception("count mismatch in Inplace PIT Restore")

            # Running out of place point in time restore for first user
            out_of_place_restore_job=self.run_PIT_restore_job([self.users[0]],first_user_full_backup_time,self.tcinputs['destination_path'])
            OOP_PIT_restore_count=out_of_place_restore_job.details["jobDetail"]["detailInfo"]["numOfObjects"]
            if OOP_PIT_restore_count-1==items_backed_up_first_user_full_job:   # user smtp folder and Automation folder are restored
                self.log.info(f'OOP PIT Restore verified successfully')
            else:
                raise Exception("count mismatch in OOP PIT Restore")

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
                for user in self.users:
                    self.cvcloud_object.one_drive.delete_folder(user_id=user)
                self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.tcinputs['destination_path'])
                self.cvcloud_object.cvoperations.delete_client(self.client_name)
                self.cvcloud_object.cvoperations.cleanup()
        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')
