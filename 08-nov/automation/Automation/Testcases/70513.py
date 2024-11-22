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
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.CloudApps import constants as cloud_apps_constants
from Application.CloudApps.cloud_connector import CloudConnector
from AutomationUtils.machine import Machine

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
        self.name = 'OneDrive Automation case for RFC restore'
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.CLOUDCONNECTOR
        self.feature = self.features_list.AUTOMATION
        self.show_to_user = True
        self.proxy_client = None
        self.cv_cloud_object = None
        self.users = None
        self.client_name = None
        self.number_of_docs = None
        self.o365_plan = None
        self.machine_object = None
        self.job_res_dir = None
        self.tcinputs = {
            'ServerPlanName': None,
            'IndexServer': None,
            'AccessNode': None,
            'O365Plan': None,
            'NumberOfDocs': None,
            'Users': None,
            'MachineHostName': None,
            'MachineUserName': None,
            'MachinePassword': None,
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

        # Verify discovery
        self.log.info(f'Verifying the discovery')
        status, res = self.subclient.verify_discovery_onedrive_for_business_client()
        if status:
            self.log.info("Discovery successful")
        else:
            raise Exception("Discovery is not successful")

    def run_backup_after_delete(self,
                                delete_file=None,
                                number_of_files=0
                                ):

        """Deletes specified files and Runs backup of all users in the client """

        user_guid_list = self.subclient._get_user_guids(self.users)
        user_guid_folder_name = user_guid_list[0].lower().replace('x', '-')

        if delete_file == 'CloudUserInfo':
            # delete clouduserinfo.db3
            self.machine_object.delete_file(self.machine_object.join_path(self.job_res_dir, user_guid_folder_name, 'CloudUserInfo.db3'))

        if delete_file == 'ExMsgListPreviousJobFailedMsgs':
            # delete ExMsgListPreviousJobFailedMsgs.xml
            self.machine_object.delete_file(self.machine_object.join_path(self.job_res_dir, user_guid_folder_name, 'ExMsgListPreviousJobFailedMsgs.xml'))

        if delete_file == 'FilesPendingTobeBackedup':
            # delete FilesPendingTobeBackedup.txt
            self.machine_object.delete_file(self.machine_object.join_path(self.job_res_dir,  user_guid_folder_name, 'FilesPendingTobeBackedup.txt'))

        if delete_file == 'ExMBJobInfo':
            # delete ExMBJobInfo.dat
            self.machine_object.delete_file(self.machine_object.join_path(self.job_res_dir, 'ExMBJobInfo.dat'))

        if delete_file == 'user_guid':
            # delete user guid
            self.machine_object.remove_directory(self.machine_object.join_path(self.job_res_dir, user_guid_folder_name))

        if delete_file == 'subclient':
            # delete subclient folder
            self.machine_object.remove_directory(self.job_res_dir)

        # Run backup of all users
        self.log.info('Running an incremental level backup')
        backup_job = self.client.backup_all_users_in_client()

        backup_level = constants.backup_level.INCREMENTAL.value
        self.cv_cloud_object.cvoperations.check_job_status(job=backup_job, backup_level_tc=backup_level)
        number_of_skipped_files = backup_job.details['jobDetail']['attemptsInfo'][0]['numSkipped']
        number_of_failed_files = backup_job.details['jobDetail']['attemptsInfo'][0]['numFailures']
        if backup_job.status == 'Completed' and number_of_skipped_files == 0 and number_of_failed_files == 0:
            self.log.info("Backup completed successfully without failures")
        else:
            raise Exception(f"Backup not completed with {backup_job.pending_reason}")

        number_of_backed_up_files = self.cv_cloud_object.cvoperations.get_number_of_successful_items(backup_job)

        # Verify backup
        if number_of_backed_up_files == number_of_files:
            self.log.info("The number of files expected, backed up matches")
        else:
            raise Exception(f"Verification of backup failed with numbers {number_of_backed_up_files} {number_of_files}")

    def setup(self):
        """Setup function of this test case"""

        # Create a client
        self.client_name = "OD_70513"
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
        self.machine_object = Machine(self.tcinputs['AccessNode'], self.commcell)
        self.users = self.tcinputs.get('Users')
        self.number_of_docs = self.tcinputs.get('NumberOfDocs')
        self.o365_plan = self.tcinputs.get('O365Plan')
        self.proxy_client = self.tcinputs['AccessNode']
        self.cv_cloud_object = CloudConnector(self)
        self.cv_cloud_object.cvoperations.cleanup()
        self.job_res_dir = self.cv_cloud_object.cvoperations.get_job_results_dir()

    def run(self):
        """Run function of this test case"""
        try:
            self.run_and_verify_discovery()

            # Delete Data on source users OneDrive
            for i in range(len(self.users)):
                self.log.info(f'Deleting data on {self.users[i]}\'s OneDrive')
                self.cv_cloud_object.one_drive.delete_all_data_on_onedrive(self.users[i])

            # Create data in users Onedrive
            self.log.info(f'Generating new data on {self.users} OneDrive')
            for i in range(len(self.users)):
                self.log.info(f'Creating {self.number_of_docs} files in {self.users[i]}\'s OneDrive')
                self.cv_cloud_object.one_drive.create_files(no_of_docs=self.number_of_docs, user=self.users[i])

            # Add users to client
            self.log.info(f'Adding users: {self.users} to client')
            self.subclient.add_users_onedrive_for_business_client(self.users, self.o365_plan)

            # Run and verify first backup
            self.run_backup_after_delete(number_of_files=self.number_of_docs)
            self.log.info(
                f"Sub-client results directory created: {self.job_res_dir} with {self.machine_object.get_items_list(self.job_res_dir)}")

            # Create new data in users Onedrive
            self.log.info(f'Generating new data on {self.users} OneDrive')
            for i in range(len(self.users)):
                self.log.info(f'Creating {self.number_of_docs} files in {self.users[i]}\'s OneDrive')
                self.cv_cloud_object.one_drive.create_files(no_of_docs=self.number_of_docs, user=self.users[i])

            # Run and verify second backup
            self.run_backup_after_delete(number_of_files=self.number_of_docs)

            # delete ExMBJobInfo and verify backup
            self.run_backup_after_delete(delete_file='ExMBJobInfo', number_of_files=self.number_of_docs)

            # delete clouduserinfo.db3 and backup
            self.run_backup_after_delete(delete_file='CloudUserInfo', number_of_files=self.number_of_docs)

            # delete failedmsgsxml and verify backup
            self.run_backup_after_delete(delete_file='ExMsgListPreviousJobFailedMsgs', number_of_files=self.number_of_docs)

            # delete FilesPendingToBeBackedup and verify backup
            self.run_backup_after_delete(delete_file='FilesPendingTobeBackedup', number_of_files=self.number_of_docs)

            # delete User guid folder and verify backup
            self.run_backup_after_delete(delete_file='user_guid', number_of_files=self.number_of_docs)

            # delete subclient folder and verify backup
            self.run_backup_after_delete(delete_file='subclient', number_of_files=self.number_of_docs)

            # delete nothing and verify backup
            self.run_backup_after_delete(number_of_files=0)

            # Create new data in users Onedrive
            self.log.info(f'Generating new data on {self.users} OneDrive')
            for i in range(len(self.users)):
                self.log.info(f'Creating {self.number_of_docs} files in {self.users[i]}\'s OneDrive')
                self.cv_cloud_object.one_drive.create_files(no_of_docs=self.number_of_docs, user=self.users[i])

            # verify last backup with newly created files
            self.run_backup_after_delete(number_of_files=self.number_of_docs)

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
                self.cv_cloud_object.cvoperations.delete_client(self.client_name)

            # Delete data on onedrive
            for user in self.users:
                self.cv_cloud_object.one_drive.delete_all_data_on_onedrive(user)

            # Clear temp
            self.cv_cloud_object.cvoperations.cleanup()
        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')
