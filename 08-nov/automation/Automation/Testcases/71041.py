# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

import time
import requests
import random
from Application.CloudApps.cloud_connector import CloudConnector
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import TestStep
from Application.CloudApps import constants as cloud_apps_constants
from Reports.utils import TestCaseUtils
from Application.CloudApps.csdb_helper import CSDBHelper
from Application.Office365.solr_helper import SolrHelper
from AutomationUtils import constants
from AutomationUtils.database_helper import MSSQL
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure




class TestCase(CVTestCase):
    """
    Class for executing this test case
    """
    TestStep = TestStep()

    def __init__(self):
        """ Initializes test case class object """
        super().__init__()
        self.name = "OneDrive Licensing case"
        self.client_name = None
        self.cvcloud_object = None
        self.utils = TestCaseUtils(self)
        self.o365_plan = None
        self.subclient_id = None
        self.client_id = None
        self.csdb_helper = None
        self.db_helper = None
        self.solr_url = None
        self.U1_root_dict = None
        self.U1_folder_dict = None
        self.U2_root_dict = None
        self.U2_folder_dict = None
        self.initial_active_allversions = None
        self.backupset_id = None
        self.tcinputs = {
            'ServerPlanName': None,
            'IndexServer': None,
            'AccessNode': None,
            'O365Plan': None,
            'Users': None,
            'application_id': None,
            'application_key_value': None,
            'azure_directory_id': None,
        }

    @TestStep
    def _initialize_sdk_objects(self):
        """Initializes the sdk objects after client creation"""

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
        """
        Setup function of this test case
        """
        self.log.info("setup function of the case")
        self.client_name = "OD_71041"
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
                                                         'access_nodes_list': [self.tcinputs.get('AccessNode')]
                                                     })

        # Verify client creation
        if self.commcell.clients.has_client(self.client_name):
            self.log.info("Client is created.")
        self._initialize_sdk_objects()
        self.client_id = self.client.client_id
        self.subclient_id = self.subclient.subclient_id
        self.backupset_id =self.backupset.backupset_id
        self.users = self.tcinputs['Users']
        self.o365_plan = self.tcinputs['O365Plan']
        self.log.info(f"client id : {self.client_id} and subclient id : {self.subclient_id} and backupset id : {self.backupset_id}")
        self.cvcloud_object = CloudConnector(self)
        self.csdb_helper = CSDBHelper(self)
        self.db_helper = MSSQL(self.tcinputs["sqlInstanceName"],
                               self.tcinputs["SqlUserName"],
                               self.tcinputs["SqlPassword"],
                               "CommServ")

    def initialize_solr(self):
        """
        initializing the solr objects
        """
        try:
            self.solr_url = self.csdb_helper.get_index_server_url(self.db_helper, client_name=self.client_name)
            self.solr_serch_obj = SolrHelper(self.cvcloud_object, self.solr_url + '/select?')
            self.solr_update_url =  self.solr_url + '/update?&commit=true&wt=json'
        except Exception:
            raise CVTestStepFailure(f'initializing the solr objects failed')

    def delete_LastVersionRetentionTime(self, client_id):
        """
        To delete LastVersionRetentionTime row in the csdb for a particular client
        Args:
            client_id(int)             : client id of the client

        """
        query = f"DELETE FROM App_ClientProp WHERE attrName like '%LastVersionRetentionTime%' and componentNameId = {client_id}"
        self.log.info("Executing the query to delete LastVersionRetentionTime row in csdb for a particular client")
        self.log.info(f"query {query}")
        self.db_helper.execute(query)

    def update_field(self, content_id, field_name, field_value):
        """Updates specified field having specified content id
                   Args:

                       content_id(str)                --  content id of the item
                       Example: "c8d2d2ebab2a86290f37cd6ae2ecba91!0c6932ab50bf08fa68596dacb6259f8d

                       field_name(str)                --  Name of the field to be updated

                       field_value                    --  Value of the field to be updated

               """
        try:
            request_json = [{
                "contentid": content_id,
                field_name: {
                    "set": field_value
                }
            }]
            response=requests.post(url=self.solr_update_url, json=request_json)

        except Exception as ex:
            raise Exception(ex)

    def get_root_and_folder_files(self,user):
        """
        gets the item properties of a user from solr

        Args:
            user(str)              : user smtp for which item properties are to be featched

        Retruns:
            U_root_dict (dict)     : dict containing properties of root level items
            U_folder_dict(dict)    : dict containing properties of items inside folder
        """
        root_items, folder_items = set(), set()
        U_root_dict, U_folder_dict = dict(), dict()

        user_items = self.solr_serch_obj.create_url_and_get_response(
            select_dict={"OwnerName": "*" + user + "*", "DocumentType": "1"},
            attr_list={"contentid", "BackupStartTime", "FolderName", "FileName"}, op_params={"rows": 100})

        for item in user_items.json()['response']['docs']:
            if item['FolderName'] == "\\My Drive":
                root_items.add(item['FileName'])
            else:
                folder_items.add(item['FileName'])

        for item in root_items:
            U_root_dict[item] = self.solr_serch_obj.create_url_and_get_response(
                select_dict={"OwnerName": "*" + user + "*", "FileName": item},
                attr_list={"contentid", "BackupStartTime", "FileName"}, op_params={"rows": 100}).json()['response'][
                'docs']

        for item in folder_items:
            U_folder_dict[item] = self.solr_serch_obj.create_url_and_get_response(
                select_dict={"OwnerName": "*" + user + "*", "FileName": item},
                attr_list={"contentid", "BackupStartTime", "FileName"}, op_params={"rows": 100}).json()['response'][
                'docs']

        return U_root_dict, U_folder_dict

    def modify_time_and_update_field(self,items,months=0,version=0,no_of_files=2):
        """
        mofifies the backup start time and updates the field in solr

        Args:
            items(dict)              : dict containing the file properties
            months(int)              : Modify backup start time by specified No. of months
            version(int)             : Modify the specified version when multiple versions are present
            no_of_files(int)         : Count of files to modify backup start time
        """

        count=0
        for item in items.keys():
            if count < no_of_files:
                self.log.info(f'changing backupstarttime for {items[item][version]["BackupStartTime"]} ')
                items[item][version]["BackupStartTime"]=self.solr_serch_obj.subtract_retention_time(items[item][version]["BackupStartTime"],months*30)
                self.log.info(f'updated backupstarttime is {items[item][version]["BackupStartTime"]} ')
                self.log.info(f'updating backupstarttime in solr for file - {items[item][version]["FileName"]} ,  {items[item][version]["contentid"]}')
                self.update_field(items[item][version]["contentid"],"BackupStartTime",items[item][version]["BackupStartTime"])
            else:
                break
            count += 1

    def enable_version_retention_at_client_level(self,authcode):
        """
        runs qscript QS_SetClientProperty.sql to enable version at client level

        Args:
            authcode(int)              : returns the authcode

        """
        qscript = f"-sn QS_SetClientProperty.sql -si '{self.client_name}' -si 'EnableVersionRetention' -si 'true' -si '{authcode}'"
        self.log.info("Executing qoperation execscript {0}".format(qscript))
        response = self.commcell._qoperation_execscript(qscript)
        self.log.info(f"qscript output - {str(response)}")

    def perform_version_retention(self,months=0,version=0,no_of_files=2):
        """
        performs version retention on specified no of file versions

        Args:
            months(int)              : Modify backup start time by specified No. of months
            version(int)             : Modify the specified version when multiple versions are present
            no_of_files(int)         : Count of files to modify backup start time
        """

        self.modify_time_and_update_field(self.U1_root_dict, months, version, no_of_files)
        self.modify_time_and_update_field(self.U1_folder_dict, months, version, no_of_files)
        self.modify_time_and_update_field(self.U2_root_dict, months, version, no_of_files)
        self.modify_time_and_update_field(self.U2_folder_dict, months, version, no_of_files)
        time.sleep(5) # sleep time for solr index to sync

        self.delete_LastVersionRetentionTime(client_id=self.client_id)
        self.log.info("performing refresh retention stats and sleeping for 300 seconds")
        self.subclient.refresh_retention_stats(self.subclient_id)
        time.sleep(300) # sleep time for version retention to run on the client

    def verify_version_retention(self,users,expected_prune_count):
        """
        verifies version retention for all the users

        Args:
            users(list)              : list of all users associated to the client
            expected_prune_count(int): expected count of versions to be pruned
        """
        user_items = {}
        pruned_count = 0
        for user in users :
            user_items[user] = self.solr_serch_obj.create_url_and_get_response(
                select_dict={"OwnerName": "*" + user + "*", "DocumentType": "1", "IsVisible": "false"},
                attr_list={"contentid", "BackupStartTime", "FileName","Size"}, op_params={"rows": 100}).json()[
                      'response']['docs']
            pruned_count += self.solr_serch_obj.create_url_and_get_response(
                select_dict={"OwnerName": "*" + user + "*", "DocumentType": "1", "IsVisible": "false"},
                attr_list={"contentid", "BackupStartTime", "FileName","Size"}, op_params={"rows": 100}).json()[
                      'response']['numFound']
        size = 0
        for user in user_items.keys():
            if user_items[user] != []:
                for item in user_items[user]:
                    size += int(item['Size'])

        self.log.info(f"pruned versions count : {pruned_count}")

        if expected_prune_count!=pruned_count:
            raise Exception(f"Version retention failed. Expected No. of versions to be pruned = {expected_prune_count},"
                            f" No. of versions pruned = {pruned_count}")
        else:
            self.log.info(f"No. of versions correctly pruned")

        self.log.info(f"pruned data size  : {size}")

        self.log.info("performing client level refresh stats and sleeping for 60 seconds")
        self.subclient.refresh_client_level_stats(self.subclient_id)
        time.sleep(60) # sleep time for refreshing client level stats
        self.log.info("successfully refreshed client level stats")

        curret_active_allversions = self.subclient.get_client_level_stats(self.backupset_id)['office365ClientOverview']['activeAllVersionsStats']
        self.log.info(f" Update client level stats for all versions : {curret_active_allversions['backupSize']}")

        if self.initial_active_allversions['backupSize'] - size != curret_active_allversions['backupSize'] and size != 0:
            raise Exception(f"Size is incorrectly updated after performing version retention at client level . Initial client "
                            f"level size ={self.initial_active_allversions['backupSize']}, client level size after version"
                            f"retention = {curret_active_allversions['backupSize']}")
        else:
            self.log.info(f"Initial backup size {self.initial_active_allversions['backupSize']} - pruned size {size} = "
                          f"Update client level stats {curret_active_allversions['backupSize']}")
            self.log.info(f"Client level stats are correctly updated after version retention and refresh client level stats")

    def run(self):
        """ Main function for test case execution """
        try:

            # Adding entry in client prop table to enable version retention at client level
            commcell_number = self.csdb_helper.get_commcell_number()
            authcode = self.csdb_helper.get_authcode_setclientproperty(self.client_id, commcell_number)
            self.enable_version_retention_at_client_level(authcode)


            # Verify discovery completion or wait for discovery to complete
            self.log.info(f'Waiting until discovery is complete')
            self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()

            # Add users to client
            self.log.info(f'Adding users: {self.users[0]} to client with  {self.o365_plan[0]}')
            self.subclient.add_users_onedrive_for_business_client([self.users[0]], self.o365_plan[0])
            self.log.info(f'Adding users: {self.users[1]} to client with plan {self.o365_plan[1]}')
            self.subclient.add_users_onedrive_for_business_client([self.users[1]], self.o365_plan[1])

            # Run initial backup
            backup_level = constants.backup_level.INCREMENTAL.value
            self.log.info('Run first sub-client level backup')
            backup_job1 = self.client.backup_all_users_in_client()
            self.cvcloud_object.cvoperations.check_job_status(job=backup_job1, backup_level_tc=backup_level)

            # initialize solr objects
            self.initialize_solr()

            # run multiple inplace unconditional restores and backups to have multiple file versions
            self.log.info('Run first inplace unconditional Overwrite restore for user 1')
            restore_job1 = self.subclient.in_place_restore_onedrive_for_business_client(users=[self.users[0]], overwrite=True)
            self.cvcloud_object.cvoperations.check_job_status(job=restore_job1, backup_level_tc='Restore')

            self.log.info('Run first inplace unconditional Overwrite restore for user 2')
            restore_job1 = self.subclient.in_place_restore_onedrive_for_business_client(users=[self.users[1]], overwrite=True)
            self.cvcloud_object.cvoperations.check_job_status(job=restore_job1, backup_level_tc='Restore')

            self.log.info('Run second sub-client level backup')
            backup_job2 = self.client.backup_all_users_in_client()
            self.cvcloud_object.cvoperations.check_job_status(job=backup_job2, backup_level_tc=backup_level)

            self.log.info('Run second inplace unconditional Overwrite restore for user 1')
            restore_job2 = self.subclient.in_place_restore_onedrive_for_business_client(users=[self.users[0]], overwrite=True)
            self.cvcloud_object.cvoperations.check_job_status(job=restore_job2, backup_level_tc='Restore')

            self.log.info('Run second inplace unconditional Overwrite restore for user 2')
            restore_job1 = self.subclient.in_place_restore_onedrive_for_business_client(users=[self.users[1]], overwrite=True)
            self.cvcloud_object.cvoperations.check_job_status(job=restore_job1, backup_level_tc='Restore')

            self.log.info('Run third sub-client level backup')
            backup_job3 = self.client.backup_all_users_in_client()
            self.cvcloud_object.cvoperations.check_job_status(job=backup_job3, backup_level_tc=backup_level)

            self.log.info(f" get initial client level stats for all versions ")
            self.initial_active_allversions = self.subclient.get_client_level_stats(self.backupset_id)['office365ClientOverview']['activeAllVersionsStats']
            self.log.info(f" initial client level stats for all versions : {self.initial_active_allversions['backupSize']}")
            self.U1_root_dict, self.U1_folder_dict = self.get_root_and_folder_files(self.users[0])
            self.U2_root_dict, self.U2_folder_dict = self.get_root_and_folder_files(self.users[1])

            self.log.info("perform version retention by modifying backup start time to 60 days ago ")
            self.perform_version_retention(2, 0, 2)

            self.log.info("verify version retention after modifying backup start time to 60 days ago")
            self.verify_version_retention(self.users,4)

            self.log.info("perform version retention by modifying backup start time to 120 days ago")
            self.perform_version_retention(4, 1, 2)

            self.log.info("verify version retention after modifying backup start time to 120 days ago")
            self.verify_version_retention(self.users, 12)

            self.log.info("perform version retention by modifying backup start time to 60 days ago")
            self.perform_version_retention(2,2,3)

            self.log.info("verify version retention after modifying backup start time to 60 days ago")
            self.verify_version_retention(self.users, 14)

        except Exception as exception:
            self.log.error(f'Failed to execute test case with error: {str(exception)}')
            self.result_string = str(exception)
            self.status = constants.FAILED

    def tear_down(self):
        """ Teardown function of this test case """
        self.log.info("Executing tear down function")
        if self.status == constants.PASSED:
            self.log.info(f'Test case status: {self.status}')
            self.cvcloud_object.cvoperations.delete_client(self.client_name)
            self.cvcloud_object.cvoperations.cleanup()
        else:
            self.log.info("Testcase failed")
