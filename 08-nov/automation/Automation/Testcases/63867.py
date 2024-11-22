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
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.CloudApps import constants as cloud_apps_constants
from Application.CloudApps.cloud_connector import CloudConnector
from Web.Common.exceptions import CVTestCaseInitFailure
from cvpysdk.instance import Instance


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """

        super(TestCase, self).__init__()
        self.name = "Verification of discovery status and index status"
        self.users = None
        self.o365_plan = None
        self.navigator = None
        self.onedrive = None
        self.client_name = None
        self.number_of_docs = None,
        self.curr_time = None,
        self.cvcloud_object = None
        self.tcinputs = {
            'ServerPlanName': None,
            'IndexServer': None,
            'AccessNodes': None,
            'O365Plan': None,
            'Users': None,
            'number_of_docs': None,
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

    def setup(self):
        """Initial configuration for the testcase."""
        try:
            self.curr_time = int(time.time())
            self.log.info(f'Current timestamp is {self.curr_time}')

            self.client_name = cloud_apps_constants.ONEDRIVE_CLIENT.format(str(int(time.time())))
            self.log.info(f'Creating OneDrive client : {self.client_name}')
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
            self.number_of_docs = self.tcinputs['number_of_docs']
            self.cvcloud_object = CloudConnector(self)
            self.cvcloud_object.instance = Instance(self._agent, self._instance.instance_name, self._instance.instance_id)
            self.cvcloud_object.cvoperations.cleanup()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """"Run function for the testcase."""
        try:
            # Get the backupsetId of the client
            bkpsetid = self._backupset.backupset_id

            # Delete Data on source user's OneDrive
            self.log.info(f'Deleting data on {self.users[0]}\'s OneDrive')
            self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.users[0])

            # Run and verify discovery
            self.log.info(f'Discovering the users for the {self.client_name}')
            self.subclient.run_subclient_discovery()
            self.subclient.verify_discovery_onedrive_for_business_client()
            self.log.info(f'Discovered users successfully')

            # Add user to client
            self.log.info(f'Adding users: {self.users} to client')
            self.subclient.add_users_onedrive_for_business_client([self.users[0]], self.o365_plan)

            # Create data on user's onedrive
            self.log.info(f'Generating new data on {self.users[0]}\'s OneDrive')
            self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.users[0])
            self.cvcloud_object.one_drive.create_files(no_of_docs=self.number_of_docs, user=self.users[0],new_folder=False)

            # Run backup of user
            self.log.info('Run 1st incremental level backup')
            backup_level = constants.backup_level.INCREMENTAL.value
            backup_job = self.client.backup_all_users_in_client()
            self.cvcloud_object.cvoperations.check_job_status(job=backup_job, backup_level_tc=backup_level)
            time.sleep(10)
            self.cvcloud_object.cvoperations.check_playback_completion(backup_job.job_id)
            self.log.info(f'Backup job played back successfully.')

            # Verify whether discovery status and index status is updated
            url = self.client._services['GET_CLIENT_OVERVIEW'] % (bkpsetid)
            flag, response = self.client._cvpysdk_object.make_request('GET', url)
            if flag:
                if response.json():
                    response = response.json()

                    if response.get('errorCode', 0) != 0:
                        error_message = response.json()['errorMessage']
                        o_str = 'Failed to fetch details.\nError: "{0}"'.format(error_message)
                        raise Exception(o_str)

                    last_discovered_time = response["office365ClientOverview"]["summary"]["discoverState"]["lastCacheUpdateTime"]
                    last_playback_time = response["office365ClientOverview"]["summary"]["lastPlayedJobSummary"]["lastPlayedBkpJobTime"]

                    self.log.info(f'Verifying whether the discovery status is updated or not')
                    if last_discovered_time > self.curr_time:
                        self.log.info(f'Discovery status updated successfully.')
                    else:
                        raise Exception(f'Discovery status is not updated')

                    self.log.info(f'Verifying whether the index status is updated or not')
                    if last_playback_time > self.curr_time:
                        self.log.info(f'Index status updated successfully')
                    else:
                        raise Exception(f'Index status is not updated')

                else:
                    raise Exception(f'Response: {response}')
            else:
                raise Exception(f'Response: {response}')


        except Exception as exception:
            self.log.error(f'Failed to execute test case with error: {str(exception)}')
            self.result_string = str(exception)
            self.status = constants.FAILED

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.log.info(f'Test case status: {self.status}')
                # Delete the client if test case is successful
                self.cvcloud_object.cvoperations.delete_client(self.client_name)
                # Clear user's onedrive
                self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.users[0])
                self.cvcloud_object.cvoperations.cleanup()
        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')