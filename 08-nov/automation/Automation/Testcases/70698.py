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
    __init__()      --  initialize TestCase class
    setup()         --  setup function of this test case
    run()           --  run function of this test case
    tear_down()     --  tear down function of this test case
"""
import os
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.CloudApps import constants as cloud_apps_constants
from Application.CloudApps.cloud_connector import CloudConnector
from AutomationUtils.machine import Machine
from Application.Exchange.exchange_sqlite_helper import SQLiteHelper
from cvpysdk.constants import AdvancedJobDetailType

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name                (str)       --  name of this test case
                applicable_os   (str)       —  applicable os for this test case
                                                            Ex: self.os_list.WINDOWS
                 product            (str)     —  applicable product for this test case
                                                                 Ex: self.products_list.FILESYSTEM
                features             (str)      —  qcconstants feature_list item
                                                             Ex: self.features_list.DATAPROTECTION
                 show_to_user   (bool)    —  test case flag to determine if the test case is
                                                             to be shown to user or not
                      Accept:
                                           True    –   test case will be shown to user from commcell gui
                                           False   –   test case will not be shown to user
                        default: False
                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
        """
        super(TestCase, self).__init__()
        self.name = 'Cvpysdk case for custom categories'
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.CLOUDCONNECTOR
        self.feature = self.features_list.AUTOMATION
        self.show_to_user = True
        self.proxy_client = None
        self.cv_cloud_object = None
        self.client_name = None
        self.o365_high_ret_plan = None
        self.o365_low_ret_plan = None
        self.machine = None
        self.sqlite_helper = None
        self.subclient_job_res_dir = None
        self.custom_dict1 = None
        self.custom_dict2 = None
        self.custom_dict3 = None
        self.custom_dict4 = None
        self.custom_dict5 = None
        self.discovery_cache_path = None
        self.tcinputs = {
            'ServerPlanName': None,
            'IndexServer': None,
            'AccessNode': None,
            'HighRetPlan': None,
            'LowRetPlan': None,
            'MachineHostName': None,
            'MachineUserName': None,
            'MachinePassword': None,
            'custom_dict1': None,
            'custom_dict2': None,
            'custom_dict3': None,
            'custom_dict4': None,
            'custom_dict5': None,
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

    def run_and_verify_discovery(self):

        """Run discovery and verify its completion"""

        # Run discovery
        self.log.info(f'Running the discovery')
        self.subclient.run_subclient_discovery()

        # Verify discovery completion or wait for discovery to complete
        self.log.info(f'Waiting until discovery is complete')
        self.cv_cloud_object.cvoperations.wait_until_discovery_is_complete()

        # Verify discovery
        self.log.info(f'Verifying the discovery')
        status, res = self.subclient.verify_discovery_onedrive_for_business_client()
        if status:
            self.log.info("Discovery successful")
        else:
            raise Exception("Discovery is not successful")

    def get_common_users(self, group1_members, group2_members):

        """
        Get the members common in two groups

        Args:
            group1_members (list):   Members of first group
            group1_members (list):   Members of second group

        Returns:
            common_members (list):  List of members common to both groups

        """

        try:
            return list(set(group1_members).intersection(group2_members))
        except Exception:
            raise Exception(f'Exception while getting common members')

    def do_content_management(self, group1, group2, group1_members, group2_members):

        common_users = self.get_common_users(group1_members, group2_members)
        user_details, no_of_records = self.subclient.browse_for_content(discovery_type=1)
        for user in common_users:
            if user_details[user]['planName'] == self.tcinputs['HighRetPlan']:
                self.log.info("Common user is associated with higher retention plan")
            else:
                raise Exception("Common user is not associated with higher retention plan")

        # Disable the first group
        self.cv_cloud_object.cvoperations.update_custom_category_associations(custom_category=group1, operation=2)
        self.run_and_verify_discovery()
        time.sleep(10)
        user_details, no_of_records = self.subclient.browse_for_content(discovery_type=1)
        for user in group1_members:
            if user_details[user]['accountStatus'] == 2:
                pass
            else:
                raise Exception("All users are not disabled when their corresponding group is disabled")
        self.log.info("All users are disabled when their corresponding group is disabled")

        # Enable group
        self.cv_cloud_object.cvoperations.update_custom_category_associations(custom_category=group1, operation=0)
        self.run_and_verify_discovery()
        time.sleep(10)
        user_details, no_of_records = self.subclient.browse_for_content(discovery_type=1)
        for user in group1_members:
            if user_details[user]['accountStatus'] == 0:
                pass
            else:
                raise Exception("All users are not enabled when their corresponding group is enabled")
        self.log.info("All users are enabled when their corresponding group is enabled")

        # Delete the active group
        self.cv_cloud_object.cvoperations.update_custom_category_associations(custom_category=group1, operation=1)
        self.run_and_verify_discovery()
        time.sleep(10)
        user_details, no_of_records = self.subclient.browse_for_content(discovery_type=1, include_deleted=True)
        for user in group1_members:
            if user not in common_users:
                if user_details[user]['accountStatus'] == 1:
                    self.log.info("Non common user is deleted when it's corresponding group is deleted")
                else:
                    raise Exception("Non common user is not deleted when it's corresponding group is deleted")
            else:
                if user_details[user]['accountStatus'] == 0:
                    self.log.info("Common user remained when one of it's corresponding group is deleted")
                else:
                    raise Exception("Common user not remained when one of it's corresponding group is deleted")

        # Disable second group
        self.cv_cloud_object.cvoperations.update_custom_category_associations(custom_category=group2, operation=2)
        self.run_and_verify_discovery()
        time.sleep(10)
        user_details, no_of_records = self.subclient.browse_for_content(discovery_type=1)
        for user in group2_members:
            if user_details[user]['accountStatus'] == 2:
                pass
            else:
                raise Exception("All users are not disabled when their corresponding group is disabled")
        self.log.info("All users are disabled when their corresponding group is disabled")

        # Delete the disabled group
        self.cv_cloud_object.cvoperations.update_custom_category_associations(custom_category=group2, operation=1)
        self.run_and_verify_discovery()
        time.sleep(10)

        # Verify empty users tab and content tab
        user_dict, no_of_user_records = self.subclient.browse_for_content(discovery_type=1)
        group_dict, no_of_group_records = self.subclient.browse_for_content(discovery_type=2)

        if no_of_user_records == no_of_group_records == 0:
            self.log.info("All users/groups are removed")
        else:
            raise Exception("All users/groups are not removed")

    def add_custom_category(self, custom_dict, o365_plan, group_query):

        """
        Adds custom category to the office 365 client and then
        verifies the count of users by executing queries in discover cache

        Args:
            custom_dict (dict):   Dictionary for custom category addition
            o365_plan (str):   Office 365 plan name
            group_query (str): Query for verifying count of users stored in discovery cache

        Returns:
            group_members (list):  List of members associated with the custom category
        """

        sqlite_file = (f'{self.discovery_cache_path}' +
                       "\\DiscoveryCache\\{0}_{1}\\discover_mode_users_client{0}.db3".format(
                           self.client.client_id,
                           self.client.client_name
                       ))

        self.subclient.manage_custom_category(custom_dict, "add", o365_plan)
        self.cv_cloud_object.cvoperations.wait_until_discovery_is_complete()
        time.sleep(5)
        groups, _ = self.subclient.browse_for_content(discovery_type=31)
        group_sqlite_file = f'{self.discovery_cache_path}' + \
                            "\\DiscoveryCache\\{0}_{1}\\discover_mode_groupusers{2}_subclient{3}.db3".format(
                                 self.client.client_id,
                                 self.client.client_name,
                                 groups[custom_dict['name']]['id'],
                                 self.subclient.subclient_id
                            )

        sqlite_res = self.sqlite_helper.execute_dat_file_query(os.path.dirname(sqlite_file),
                                                               file_name=os.path.basename(sqlite_file),
                                                               query=group_query)

        group_sqlite_res = self.sqlite_helper.execute_dat_file_query(os.path.dirname(group_sqlite_file),
                                                                      file_name=os.path.basename(group_sqlite_file),
                                                                      query='select count(*) from Users')

        if len(sqlite_res) == group_sqlite_res[0][0]:
            self.log.info(f"Users corresponding to custom category: {custom_dict['name']} are added")
        else:
            raise Exception("Users corresponding to custom category: {custom_dict['name']} count is not verified")

        group_members = [item[0].split(';')[0] for item in sqlite_res]
        return group_members

    def setup(self):
        """Setup function of this test case"""

        # Create a client
        self.client_name = cloud_apps_constants.ONEDRIVE_CLIENT.format(str(int(time.time())))
        self.log.info(f'Creating OneDrive client: {self.client_name}')
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
        self.o365_high_ret_plan = self.tcinputs['HighRetPlan']
        self.o365_low_ret_plan = self.tcinputs['LowRetPlan']
        self.proxy_client = self.tcinputs['AccessNode']
        self.custom_dict1 = self.tcinputs['custom_dict1']
        self.custom_dict2 = self.tcinputs['custom_dict2']
        self.custom_dict3 = self.tcinputs['custom_dict3']
        self.custom_dict4 = self.tcinputs['custom_dict4']
        self.custom_dict5 = self.tcinputs['custom_dict5']
        self.proxy_client = self.tcinputs['AccessNode']
        self.machine = Machine(self.tcinputs['AccessNode'], self.commcell)
        self.cv_cloud_object = CloudConnector(self)
        self.cv_cloud_object.cvoperations.cleanup()
        self.subclient_job_res_dir = self.cv_cloud_object.cvoperations.get_job_results_dir()
        self.sqlite_helper = SQLiteHelper(self, proxy_machine=self.machine, username=self.tcinputs['MachineUserName'],
                                          password=self.tcinputs['MachinePassword'])
        self.discovery_cache_path = self.machine.os_sep.join(self.subclient_job_res_dir.split(self.machine.os_sep)[:-2])

    def run(self):
        """Run function of this test case"""
        try:
            self.run_and_verify_discovery()

            group1_query = 'SELECT email FROM Users WHERE license = 1'
            group1_members = self.add_custom_category(self.custom_dict1, self.o365_high_ret_plan, group1_query)

            group2_query = " SELECT email FROM Users WHERE Name LIKE 'OneDrive%User1' "
            group2_members = self.add_custom_category(self.custom_dict2, self.o365_low_ret_plan, group2_query)

            self.do_content_management(self.custom_dict1['name'], self.custom_dict2['name'], group1_members, group2_members)

            group3_query = " SELECT * FROM Users where Name GLOB '[A-N]*' AND Location = 'AU'  "
            group3_members = self.add_custom_category(self.custom_dict3, self.o365_low_ret_plan, group3_query)

            # Edit the custom category 3 to custom category 2 rules
            self.subclient.manage_custom_category(self.custom_dict5, action="edit")
            self.cv_cloud_object.cvoperations.wait_until_discovery_is_complete()
            time.sleep(5)
            users, number_of_users = self.subclient.browse_for_content(discovery_type=1)

            if number_of_users == len(group2_members):
                self.log.info("Custom category 3 is successfully edited to custom category 2 rules")
            else:
                raise Exception("Custom category 1 edit verification failed")

            group4_query = " SELECT * FROM Users WHERE Email LIKE '%user%' AND location != 'IN' "
            group4_members = self.add_custom_category(self.custom_dict4, self.o365_low_ret_plan, group4_query)

            # Run backup for custom category 4
            backup_job = self.subclient.run_user_level_backup_onedrive_for_business_client(users_list=[],
                                                                          custom_groups_list=[self.custom_dict4['name']])
            backup_job.wait_for_completion()
            advanced_details = backup_job.advanced_job_details(info_type=AdvancedJobDetailType.BKUP_INFO)
            if advanced_details['bkpInfo']['exchMbInfo']['SourceMailboxCounters']['TotalMBs'] == len(group4_members):
                self.log.info(f"Only users associated to custom category: {self.custom_dict4['name']} are backed up")
            else:
                raise Exception("Backup verification failed for specific custom category backup job")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.log.info(f'Test case status: {self.status}')

            # Delete the client
            self.cv_cloud_object.cvoperations.delete_client(self.client_name)

            # Clear temp
            self.cv_cloud_object.cvoperations.cleanup()
        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')