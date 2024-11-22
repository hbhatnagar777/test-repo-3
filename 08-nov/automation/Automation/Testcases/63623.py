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
    __init__()                                  --  initialize TestCase class

    setup()                                     --  sets up the variables required for running the testcase

    run()                                       --  run function of this test case

    teardown()                                  --  tears down the things created for running the testcase

"""
import json
from datetime import datetime
import time
from Application.Office365.solr_helper import SolrHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.plan import Plans
from Web.Common.exceptions import CVTestCaseInitFailure
from Application.CloudApps import constants as cloud_apps_constants
from Application.CloudApps.cloud_connector import CloudConnector
from cvpysdk.job import JobController, Job


class TestCase(CVTestCase):
    """Class for executing this test case"""
    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name                (str)       --  name of this test case
                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
        """
        super(TestCase, self).__init__()
        self.name = "OneDrive V2 Verification of backup and backup stats of all users scheduled backup and disk restore of a user"
        self.plan = None
        self.tcinputs = {
            'StorageName': None,
            'IndexServer': None,
            'AccessNodes': None,
            'O365Plan': None,
            'number_of_docs': None,
            'ADGroup': None,
            'application_id': None,
            'application_key_value': None,
            'azure_directory_id': None
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

    def create_server_plan_with_specified_rpo(self, plan_name, storage_name, start_time):
        """

            Method to create a default server plan with specified RPO

            Args:
                plan_name (str)             --  Name of the plan to create

                storage_name (str)          --  Backup destination storage name

                start_time (int)                   --  Schedule start time from now in minutes

        """
        backup_destinations = {"storage_name": storage_name}
        schedules = [{
            "backupType": "INCREMENTAL",
            "schedulePattern": {
                "scheduleFrequencyType": "DAILY",
                "startTime": (datetime.now() - datetime.now().replace(hour=0, minute=0,
                                                                      second=0)).seconds + 60 * start_time,
                "frequency": 1
            }
        }]

        self.plan.create_server_plan(plan_name, backup_destinations, schedules)

    def run_and_verify_discovery(self):

        """Run discovery and verify its completion"""

        # Run discovery
        self.log.info(f'Running the discovery')
        self.subclient.run_subclient_discovery()

        # Verify discovery
        self.log.info(f'Verifying the discovery')
        status, res = self.subclient.verify_discovery_onedrive_for_business_client()
        if (status):
            self.log.info("Discovery successful")
        else:
            raise Exception("Discovery is not successful")

    def delete_data_and_add_users(self):

        """ Deletes data in Onedrive users and adds the AD group to client and creates new data in them"""

        # Delete Data on source users OneDrive
        for i in range(len(self.users)):
            self.log.info(f'Deleting data on {self.users[i]}\'s OneDrive')
            self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.users[i])

        # Add users to client
        self.log.info(f'Adding AD Group: {self.ad_group} to client')
        self.subclient.add_ad_group_onedrive_for_business_client(self.ad_group, self.o365_plan)

        if self.ad_group in self.subclient.groups:
            self.log.info(f"Content of client: {self.subclient.groups}")

        # Create data in users Onedrive
        self.log.info(f'Generating new data on {self.users} OneDrive')
        for i in range(len(self.users)):
            self.log.info(f'Creating {self.number_of_docs} files in {self.users[i]}\'s OneDrive')
            self.cvcloud_object.one_drive.create_files(no_of_docs=self.number_of_docs, user=self.users[i])

    def verify_scheduled_backup(self):

        """Verifies whether scheduled backup launched or not and then verify its completion and statistics"""

        # Catch the job
        self.jobs = self.jobC.all_jobs(client_name=self.client_name, lookup_time=1, job_filter='Backup')
        if self.jobs:
            self.log.info('Backup job is triggered')
        self.log.debug(f'Jobs: {self.jobs}')
        self.log.debug(f"JobId: {list(self.jobs.keys())[0]}")
        self.job = Job(self._commcell, list(self.jobs.keys())[0])

        # Verify completion
        backup_level = constants.backup_level.INCREMENTAL.value
        self.cvcloud_object.cvoperations.check_job_status(job=self.job, backup_level_tc=backup_level)
        number_of_skipped_files = self.job.details['jobDetail']['attemptsInfo'][0]['numSkipped']
        number_of_failed_files = self.job.details['jobDetail']['attemptsInfo'][0]['numFailures']
        if self.job.status == 'Completed' and number_of_skipped_files == 0 and number_of_failed_files == 0:
            self.log.info("Backup completed successfully without failures")
        else:
            raise Exception(f"Backup not completed with {self.job.pending_reason}")

        # Verify backup stats
        # Number
        number_of_backedup_files = self.cvcloud_object.cvoperations.get_number_of_successful_items(self.job)
        number_of_created_files = self.number_of_docs * len(self.users)
        number_of_files_indexed = self.solr.create_url_and_get_response(select_dict={'DocumentType': 1}).json()['response']['numFound']

        if number_of_backedup_files == number_of_files_indexed == number_of_created_files:
            self.log.info("The number of files created, backed up matches with number of files in index")
        else:
            raise Exception(f"Verification of backup failed")

    def verify_restore(self):

        """Performs disk restore of an user and verify restore completion and statistics"""

        # Perform restore
        self.log.info(f'Run restore for user: {self.users[2]}')
        self.restore_job = self.subclient.disk_restore_onedrive_for_business_client(users=[self.users[2]],
                                                                   destination_client=self.tcinputs['AccessNodes'][0],
                                                                   destination_path=cloud_apps_constants.DESTINATION_TO_DISK)

        # Verify restore job completion
        self.cvcloud_object.cvoperations.check_job_status(job=self.restore_job, backup_level_tc='Restore')
        if self.restore_job.status == 'Completed':
            self.log.info("Restore completed")
        else:
            raise Exception(f"Restore not completed with {self.restore_job.pending_reason}")

        # Verify restore stats

        # Sizes
        self.cvcloud_object.one_drive.get_file_properties(user=self.users[2],save_to_db_folder=False)
        self.cvcloud_object.one_drive.compare_file_properties(oop=True, to_disk=True, incremental=True,
                                                              user_id=self.users[2])

        # Numbers
        number_of_restored_files = self.cvcloud_object.cvoperations.get_number_of_successful_items(self.restore_job)
        SolrResponse = self.solr.create_url_and_get_response(select_dict={'OwnerName': f'*{self.users[2]}*'}).json()
        number_of_items_for_user_in_index = SolrResponse['response']['numFound']
        if number_of_restored_files == number_of_items_for_user_in_index:
            self.log.info("The number of files restored matches with number of files in index")
        else:
            raise Exception(
                f"Restore verification is not success: {number_of_restored_files} {number_of_items_for_user_in_index} not matched")


    def setup(self):
        """Setup function of this test case"""
        try:
            # Server plan creation
            self.plan_name = "TestPlan_%s" % str(int(time.time()))
            self.log.info(f'Creating server plan')
            self.plan = Plans(self._commcell)
            self.create_server_plan_with_specified_rpo(self.plan_name, self.tcinputs['StorageName'], 10)

            # Verify server plan creation
            if self.plan.has_plan(self.plan_name):
                self.log.info("Plan is created.")

            # Client creation
            self.client_name = cloud_apps_constants.ONEDRIVE_CLIENT.format(str(int(time.time())))
            self.log.info(f'Creating OneDrive client : {self.client_name}')
            self.commcell.clients.add_onedrive_for_business_client(client_name=self.client_name,
                                                         server_plan=self.plan_name,
                                                         azure_directory_id=self.tcinputs.get("azure_directory_id"),
                                                         azure_app_id=self.tcinputs.get("application_id"),
                                                         azure_app_key_id=self.tcinputs.get("application_key_value"),

                                                         **{
                                                             'index_server': self.tcinputs.get('IndexServer'),
                                                             'access_nodes_list': self.tcinputs.get('AccessNodes')
                                                         })

            # Verify client creation
            if self.commcell.clients.has_client(self.client_name):
                self.log.info("Client is created.")

            self._initialize_sdk_objects()
            self.proxy_client = self.tcinputs['AccessNodes'][0]
            self.ad_group = self.tcinputs['ADGroup']
            self.o365_plan = self.tcinputs['O365Plan']
            self.number_of_docs = self.tcinputs['number_of_docs']
            self.jobC = JobController(self._commcell)

            # Creating CloudConnector object
            self.cvcloud_object = CloudConnector(self)
            self.cvcloud_object.cvoperations.cleanup()
            self.cvcloud_object.instance = self._instance
            self.solr = SolrHelper(self.cvcloud_object)
            self.log.info(self.solr.set_cvsolr_base_url())

            # Discover group members
            self.cvcloud_object.one_drive.discover_group_members(group_name=self.ad_group)
            f = open('Application/CloudApps/onedrive_db.json')
            data = json.load(f)
            self.users = [data[f'{self.ad_group}_members_list'][str(i)]['userPrincipalName'] for i in
                          range(1, len(data[f'{self.ad_group}_members_list']) + 1)]


        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """Run function of this test case"""
        try:
            self.run_and_verify_discovery()
            self.delete_data_and_add_users()
            # Wait for scheduled backup to start
            time.sleep(600)
            self.verify_scheduled_backup()
            self.verify_restore()

        except Exception as exception:
            self.log.error(f'Failed to execute test case with error: {str(exception)}')
            self.result_string = str(exception)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.log.info(f'Test case status: {self.status}')
            # Delete the client
            self.cvcloud_object.cvoperations.delete_client(self.client_name)
            # Deleting server plan
            self.plan.delete(self.plan_name)
            # Clear user's onedrive
            for user in self.users:
                self.cvcloud_object.one_drive.delete_all_data_on_onedrive(user)
            self.cvcloud_object.cvoperations.cleanup()
        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')
