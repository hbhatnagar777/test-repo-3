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
import json
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.CloudApps import constants as cloud_apps_constants
from Application.CloudApps.cloud_connector import CloudConnector

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
        self.name = 'OneDrive Automation: Cvpysdk case for Content Management'
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.CLOUDCONNECTOR
        self.feature = self.features_list.AUTOMATION
        self.show_to_user = True
        self.proxy_client = None
        self.cvcloud_object = None
        self.users = None
        self.groups = None
        self.group1_members = None
        self.group2_members = None
        self.client_name = None
        self.number_of_docs = None
        self.o365_plan = None
        self.tcinputs = {
            'ServerPlanName': None,
            'IndexServer': None,
            'AccessNode': None,
            'NumberOfDocs': None,
            'Users': None,
            'Groups': None,
            'HighRetPlan': None,
            'LowRetPlan': None,
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
        self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()

        # Verify discovery
        self.log.info(f'Verifying the discovery')
        status, res = self.subclient.verify_discovery_onedrive_for_business_client()
        if status:
            self.log.info("Discovery successful")
        else:
            raise Exception("Discovery is not successful")

    def get_group_members(self, group):

        """Get the members of a given group"""

        try:
            self.cvcloud_object.one_drive.discover_group_members(group_name=group)
            f = open('Application/CloudApps/onedrive_db.json')
            data = json.load(f)
            group_members = [data[f'{group}_members_list'][str(i)]['userPrincipalName'] for i in
                             range(1, len(data[f'{group}_members_list']) + 1)]
            return group_members
        except Exception:
            raise Exception(f'Unable to obtain group member details for group {group}')

    def get_common_users(self, group1, group2):

        """
        Get the members common in two groups

        Args:
            group1 (str):   Name of first group
            group2 (str):   Name of second group

        Returns:
            common_members (list):  List of members common to both groups

        """

        try:
            self.group1_members = self.get_group_members(group1)
            self.group2_members = self.get_group_members(group2)
            return list(set(self.group1_members).intersection(self.group2_members))
        except Exception:
            raise Exception(f'Exception while getting common '
                                    f'members between {group1} and {group2}')

    def setup(self):

        """Setup function of this test case"""

        try:
            # Create a client
            self.client_name = "OD_70571"
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
            self.users = self.tcinputs.get('Users')
            self.groups = self.tcinputs.get('Groups')
            self.number_of_docs = self.tcinputs.get('NumberOfDocs')
            self.proxy_client = self.tcinputs['AccessNode']
            self.cvcloud_object = CloudConnector(self)
            self.cvcloud_object.cvoperations.cleanup()

        except Exception as exp:
            self.log.exception(exp)

    def run(self):
        """Run function of this test case"""
        try:
            self.run_and_verify_discovery()

            # Add users to client
            self.log.info(f'Adding users: {self.users} to client')
            self.subclient.add_users_onedrive_for_business_client(self.users, self.tcinputs['HighRetPlan'])

            # Disable the first user
            self.log.info("Disabling first user and verifying")
            self.cvcloud_object.cvoperations.update_user_associations(users_list=[self.users[0]], operation=3)

            # Enable the first user
            self.log.info("Enabling first user and verifying")
            self.cvcloud_object.cvoperations.update_user_associations(users_list=[self.users[0]], operation=2)

            # Delete the first user
            self.log.info("Deleting first user and verifying")
            self.cvcloud_object.cvoperations.update_user_associations(users_list=[self.users[0]], operation=4)

            # Disable and delete the second user and verify
            self.log.info("Disabling and deleting second user and verifying")
            self.cvcloud_object.cvoperations.update_user_associations(users_list=[self.users[1]], operation=3)
            self.cvcloud_object.cvoperations.update_user_associations(users_list=[self.users[1]], operation=4)

            # Content Tab Manage Options

            # Add groups and verify that common user is
            # associated to group with higher retention plan

            self.log.info(f'Adding AD Group: {self.groups[0]} to client')
            self.subclient.add_ad_group_onedrive_for_business_client(self.groups[0], self.tcinputs['HighRetPlan'])
            self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()
            self.log.info(f'Adding AD Group: {self.groups[1]} to client')
            self.subclient.add_ad_group_onedrive_for_business_client(self.groups[1], self.tcinputs['LowRetPlan'])
            self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()

            common_users = self.get_common_users(self.groups[0], self.groups[1])
            user_details, no_of_records = self.subclient.browse_for_content(discovery_type=1)
            for user in common_users:
                if user_details[user]['planName'] == self.tcinputs['HighRetPlan']:
                    self.log.info("Common user is associated with higher retention plan")
                else:
                    raise Exception("Common user is not associated with higher retention plan")

            # Disable the first group
            self.cvcloud_object.cvoperations.update_group_associations(groups_list=[self.groups[0]], operation=3)
            self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()
            time.sleep(10)
            user_details, no_of_records = self.subclient.browse_for_content(discovery_type=1)
            for user in self.group1_members:
                if user_details[user]['accountStatus'] == 2:
                    pass
                else:
                    raise Exception("All users are not disabled when their corresponding group is disabled")
            self.log.info("All users are disabled when their corresponding group is disabled")

            # Enable group
            self.cvcloud_object.cvoperations.update_group_associations(groups_list=[self.groups[0]], operation=2)
            self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()
            time.sleep(10)
            user_details, no_of_records = self.subclient.browse_for_content(discovery_type=1)
            for user in self.group1_members:
                if user_details[user]['accountStatus'] == 0:
                    pass
                else:
                    raise Exception("All users are not enabled when their corresponding group is enabled")
            self.log.info("All users are enabled when their corresponding group is enabled")

            # Delete the active group
            self.cvcloud_object.cvoperations.update_group_associations(groups_list=[self.groups[0]], operation=4)
            self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()
            time.sleep(10)
            user_details, no_of_records = self.subclient.browse_for_content(discovery_type=1, include_deleted=True)
            for user in self.group1_members:
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
            self.cvcloud_object.cvoperations.update_group_associations(groups_list=[self.groups[1]], operation=3)
            self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()
            time.sleep(10)
            user_details, no_of_records = self.subclient.browse_for_content(discovery_type=1)
            for user in self.group2_members:
                if user_details[user]['accountStatus'] == 2:
                    pass
                else:
                    raise Exception("All users are not disabled when their corresponding group is disabled")
            self.log.info("All users are disabled when their corresponding group is disabled")

            # Delete the disabled group
            self.cvcloud_object.cvoperations.update_group_associations(groups_list=[self.groups[1]], operation=4)
            self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()
            time.sleep(10)
            user_details, no_of_records = self.subclient.browse_for_content(discovery_type=1, include_deleted=True)

            # Verify empty users tab and content tab
            user_dict, no_of_user_records = self.subclient.browse_for_content(discovery_type=1)
            group_dict, no_of_group_records = self.subclient.browse_for_content(discovery_type=2)

            if no_of_user_records == no_of_group_records == 0:
                self.log.info("All users/groups are removed")
            else:
                raise Exception("All users/groups are not removed")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.log.info(f'Test case status: {self.status}')

            # Delete the client
            if self.status == constants.PASSED:
                self.cvcloud_object.cvoperations.delete_client(self.client_name)

            # Clear temp
            self.cvcloud_object.cvoperations.cleanup()
        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')
