# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
TestCase is the only class defined in this file.
"""
from AutomationUtils.cvtestcase import CVTestCase
from Application.CloudApps import cloud_connector
import re
from Application.CloudApps import constants
from AutomationUtils import constants as const
import collections


class TestCase(CVTestCase):
    """
        Class for OneDrive AutoDiscovery Regex patterns and Azure AD groups
    """

    def __init__(self):

        super(TestCase, self).__init__()
        self.name = "Basic verification for One Drive AutoDiscovery"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.CLOUDCONNECTOR
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "application_id": "",
            "application_key_value": "",
            "azure_directory_id": "",
            "regex_values": [],
            "ADGroup_values": []
        }
        self._client = None
        self._agent = None
        self._instance = None
        self._subclient = None

        self.cvcloud_object = None
        self.headers = {
            'Content-Type': 'application/json',
            'Host': 'graph.microsoft.com'
        }

    def setup(self):
        """Setup method for the testcase"""
        self._initialize_sdk_objects()
        self.cvcloud_object = cloud_connector.CloudConnector(self)

    def _initialize_sdk_objects(self):
        """This method initializes the sdk objects after client creation"""
        self.commcell.refresh()
        details = {
            "azure_directory_id": self.tcinputs.get("azure_directory_id"),
            "application_id": self.tcinputs.get("application_id"),
            "application_key_value": self.tcinputs.get("application_key_value")
        }

        if self._commcell.clients.has_client(self.tcinputs.get('client_name')):
            self.log.info('Deleting the Client as it already exists')
            self._commcell.clients.delete(client_name=self.tcinputs.get('client_name'))

        self.log.info('Create client object for: %s', self.tcinputs.get("client_name"))
        self._commcell.clients.add_onedrive_client(client_name=self.tcinputs.get("client_name"),
                                                   instance_name=self.tcinputs.get("instance_name"),
                                                   server_plan=self.tcinputs.get("server_plan"),
                                                   connection_details=details,
                                                   access_node=self.tcinputs.get("access_node"))
        self._client = self._commcell.clients.get(self.tcinputs.get("client_name"))

        self.log.info('Create agent object for: %s', self.tcinputs.get("agent_name"))
        self._agent = self.client.agents.get(self.tcinputs.get("agent_name"))

        if self._agent is not None:
            self.log.info('Create instance object for: %s', self.tcinputs.get("instance_name"))
            self._instance = self._agent.instances.get(self.tcinputs.get("instance_name"))

            self.log.info('Create subclient object for: %s', self.tcinputs.get("subclient_name"))
            self._instance.subclients.add_onedrive_subclient(subclient_name=self.tcinputs.get("subclient_name"),
                                                             server_plan=self.tcinputs.get("server_plan"))
            self._subclient = self._instance.subclients.get(self.tcinputs.get("subclient_name"))

    def get_regex_users(self, value):
        """Method to filter the users in AD with regex pattern

            Args:
                value (list) -- list of regex patterns

            Returns:
                results (list) -- Users in AD matching with regex pattern
        """
        results = []
        files_list = self.cvcloud_object.sqlite.get_discover_users_local_db()

        for pattern in value:
            p = re.compile(pattern)
            for user in files_list:
                if p.search(user):
                    results.append(user)
        self.log.info('Total number of users matching with Regex pattern : [{0}]'.format(len(results)))
        return results

    def get_group_users(self, value):
        """Method to browse the subclient and gets the number of backup files

                Args:
                    value (list) -- list of AD Groups

                Returns:
                    users (list) -- list of users from all given AD groups
        """
        group_id = []
        group_endpoint = f'{constants.MS_GRAPH_ENDPOINT}'f'groups'
        while True:
            resp = self.cvcloud_object.one_drive.request(method='GET', url=group_endpoint, headers=self.headers)
            group_endpoint = resp.get('@odata.nextLink')
            for group in resp['value']:
                if group['displayName'] in value:
                    group_id.append(group['id'])
            if not resp.get('@odata.nextLink'):
                break
        users = []
        for id_ in group_id:
            member_endpoint = f'{constants.MS_GRAPH_ENDPOINT}'f'groups/{id_}/members'
            resp = self.cvcloud_object.one_drive.request(method='GET', url=member_endpoint, headers=self.headers)
            str_ = resp["value"]
            for member in str_:
                users.append(member["mail"])
        users = set(users)
        self.log.info('Total number of users in the AD group : [{0}]'.format(len(users)))
        return users

    def run(self):
        """"Run method for the testcase"""
        try:
            self._instance.enable_auto_discovery(mode='REGEX')
            self.log.info(
                f"AutoDiscovery Status : {self._instance.auto_discovery_status} , "
                f"AutoDiscovery Mode : {self._instance.auto_discovery_mode}")

            # Adding Regex pattern to Subclient
            regex_value = self.tcinputs.get("regex_values")
            self._subclient.set_auto_discovery(value=regex_value)
            self._subclient.run_subclient_discovery()
            self._subclient.refresh()

            users = self._subclient.get_subclient_users
            self.log.info('Users in Subclient after adding Regex pattern : [{0}]'.format(len(users)))

            regex_users = self.get_regex_users(value=regex_value)

            if collections.Counter(users) != collections.Counter(regex_users):
                raise Exception("Failed to match all the Regex pattern users")

            self._instance.subclients.delete(subclient_name=self.tcinputs.get("subclient_name"))
            self.log.info('Subclient Deleted')

            # Creating new subclient to verify AD Group AutoDiscovery
            self.log.info('Create subclient object for: %s', self.tcinputs.get("subclient_name"))
            self._instance.subclients.add_onedrive_subclient(subclient_name=self.tcinputs.get("subclient_name"),
                                                             server_plan=self.tcinputs.get("server_plan"))
            self._subclient = self._instance.subclients.get(self.tcinputs.get("subclient_name"))

            self._instance.enable_auto_discovery(mode='GROUP')
            self.log.info(
                f"AutoDiscovery Status : {self._instance.auto_discovery_status} , "
                f"AutoDiscovery Mode : {self._instance.auto_discovery_mode}")

            # Adding AD Group to Subclient
            group_value = self.tcinputs.get("ADGroup_values")
            self._subclient.add_AD_group(value=group_value)
            self._subclient.run_subclient_discovery()
            self._subclient.refresh()

            users = self._subclient.get_subclient_users
            self.log.info('Users in Subclient after adding AD Group : [{0}]'.format(len(users)))

            group_users = self.get_group_users(value=group_value)

            if collections.Counter(users) != collections.Counter(group_users):
                raise Exception('Failed to match all the AD Group users')

            self._instance.subclients.delete(subclient_name=self.tcinputs.get("subclient_name"))

        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = const.FAILED

    def tear_down(self):
        """TearDown method of the testcase"""
        if self.status == const.PASSED:
            self._commcell.clients.delete(client_name=self.tcinputs.get('client_name'))
        del self.cvcloud_object
