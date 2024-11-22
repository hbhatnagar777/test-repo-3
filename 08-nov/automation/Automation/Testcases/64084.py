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
from Application.Office365.solr_helper import SolrHelper
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
        self.name = 'OneDrive Automation: Cvpysdk case for delete feature'
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.CLOUDCONNECTOR
        self.feature = self.features_list.AUTOMATION
        self.show_to_user = True
        self.proxy_client = None
        self.cvcloud_object = None
        self.onedrive_items = None
        self.users = None
        self.solr = None
        self.client_name = None
        self.number_of_docs = None
        self.o365_plan = None
        self.tcinputs = {
            'ServerPlanName': None,
            'IndexServer': None,
            'AccessNode': None,
            'O365Plan': None,
            'NumberOfDocs': None,
            'Users': None,
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

    def run_backup(self):

        """ Runs backup of all users in the client """

        # Run backup of all users
        self.log.info('Running an incremental level backup job')
        backup_job = self.client.backup_all_users_in_client()

        # Verify completion
        backup_level = constants.backup_level.INCREMENTAL.value
        self.cvcloud_object.cvoperations.check_job_status(job=backup_job, backup_level_tc=backup_level)
        number_of_skipped_files = backup_job.details['jobDetail']['attemptsInfo'][0]['numSkipped']
        number_of_failed_files = backup_job.details['jobDetail']['attemptsInfo'][0]['numFailures']
        number_of_backedup_files = backup_job.details['jobDetail']['attemptsInfo'][0]['numObjects']
        if backup_job.status == 'Completed' and number_of_skipped_files == 0 and number_of_failed_files == 0:
            self.log.info("Backup completed successfully without failures")
        else:
            raise Exception(f"Backup not completed with {backup_job.pending_reason}")

        return number_of_backedup_files

    def verify_incremental(self, file1, folder1):

        """ Verifies deleted items fields for file1 and folder1 """

        # Delete one file and one folder

        self.cvcloud_object.one_drive.delete_single_file(file_name=file1, user_id=self.users[0])
        self.log.info(f"File deleted: {file1}")

        self.cvcloud_object.one_drive.delete_folder(folder_name=folder1, user_id=self.users[0])
        self.log.info(f"Folder deleted: {folder1}")

        # run backup of all users
        self.run_backup()

        files_list, files_dict = self.instance.find(file_name=file1, show_deleted=True)
        folders_list, folders_dict = self.instance.find(file_name=folder1, show_deleted=True)
        if len(files_list) == len(folders_list) == 1:
            self.log.info("Deleted file, folder found when include deleted items is enabled")
        else:
            raise Exception("Deleted file, folder is not found when include deleted items is enabled")

        files_list, files_dict = self.instance.find(file_name=file1, show_deleted=False)
        folders_list, folders_dict = self.instance.find(file_name=folder1, show_deleted=False)
        if len(files_list) == len(folders_list) == 0:
            self.log.info("Deleted file, folder is not found when include deleted items is disabled")
        else:
            raise Exception("Deleted file, folder is found when include deleted items is disabled")

    def verify_browse_delete(self, file1, file2, folder1, folder2):
        """

        Verifies the browse delete feature for normal items file2, folder2
        Verifies the browse delete feature for deleted items file1, folder1

         """
        # Delete normal file
        file2_path, file2_dict = self.instance.find(file_name=file2)
        self.instance.delete_data_from_browse(
            list(file2_dict.values())[0]['advanced_data']['browseMetaData']['indexing']['objectGUID'].lower())
        self.log.info(f"File deleted from browse: {file2}")
        time.sleep(5)

        # Delete deleted file
        file1_path, file1_dict = self.instance.find(file_name=file1, show_deleted=True)
        self.instance.delete_data_from_browse(
            list(file1_dict.values())[0]['advanced_data']['browseMetaData']['indexing']['objectGUID'].lower(),
            include_deleted_items=True)
        self.log.info(f"File deleted from browse: {file1}")
        time.sleep(5)

        # verify deleted items should not be visible in browse
        file1_list, file1_dict = self.instance.find(file_name=file1, show_deleted=True)
        file2_list, file2_dict = self.instance.find(file_name=file2, show_deleted=True)

        # Query solr field values of isVisible
        file1_solr_field = \
        self.solr.create_url_and_get_response(select_dict={'FileName': file1}).json()['response']['docs'][0][
            'IsVisible']
        file2_solr_field = \
        self.solr.create_url_and_get_response(select_dict={'FileName': file2}).json()['response']['docs'][0][
            'IsVisible']

        if len(file1_list) == len(file2_list) == 0 and not file1_solr_field and not file2_solr_field:
            self.log.info("Deleted items are not visible in browse and are correctly marked in Solr")

        # Delete normal folder
        folder2_path, folder2_dict = self.instance.find(file_name=folder2)
        djob1 = self.instance.delete_data_from_browse(
            list(folder2_dict.values())[0]['advanced_data']['browseMetaData']['indexing']['objectGUID'].lower(),
            folder=True)
        djob1.wait_for_completion()
        self.log.info(f"Folder deleted from browse: {folder2}")

        folder2_items = \
            self.onedrive_items['root'][1][0][f'{cloud_apps_constants.ONEDRIVE_FOLDER}'][1][1][f"{folder2}"][0]

        for item in folder2_items:
            item_solr_field = \
                self.solr.create_url_and_get_response(select_dict={'FileName': item}).json()['response']['docs'][0]['IsVisible']
            files_list, files_dict = self.instance.find(file_name=item, show_deleted=True)
            if not item_solr_field and len(files_list) == 0:
                self.log.info(
                    "Deleted folder item is not found even when include deleted items is enabled and Solr field is "
                    "set correctly")
            else:
                raise Exception("Deleted folder item is found even when include deleted items is enabled or Solr "
                                "field is not set correctly")

        folder2_list, folder2_dict = self.instance.find(file_name=folder2, show_deleted=True)
        folder2_solr_field = \
            self.solr.create_url_and_get_response(select_dict={'FileName': folder2}).json()['response']['docs'][0]['IsVisible']
        if len(folder2_list) == 1 and folder2_solr_field:
            self.log.info("Deleted folder hierarchy remained after delete operation and Solr field set correctly")
        else:
            raise Exception("Deleted folder hierarchy didn't remain after delete operation or Solr field "
                            "is not set correctly")

        # Delete deleted folder
        folder1_path, folder1_dict = self.instance.find(file_name=folder1, show_deleted=True)
        djob2 = self.instance.delete_data_from_browse(
            list(folder1_dict.values())[0]['advanced_data']['browseMetaData']['indexing']['objectGUID'].lower(),
            folder=True, include_deleted_items=True)
        djob2.wait_for_completion()
        self.log.info(f"Folder deleted from browse: {folder1}")

        folder1_items = \
            self.onedrive_items['root'][1][0][f'{cloud_apps_constants.ONEDRIVE_FOLDER}'][1][0][f"{folder1}"][0]

        for item in folder1_items:
            item_solr_field = \
                self.solr.create_url_and_get_response(select_dict={'FileName': item}).json()['response']['docs'][0]['IsVisible']
            files_list, files_dict = self.instance.find(file_name=item, show_deleted=True)
            if not item_solr_field and len(files_list) == 0:
                self.log.info(
                    "Deleted folder item is not found even when include deleted items is enabled and Solr field is "
                    "set correctly")
            else:
                raise Exception("Deleted folder item is found even when include deleted items is enabled or Solr "
                                "field is not set correctly")

        folder1_list, folder1_dict = self.instance.find(file_name=folder1, show_deleted=True)
        folder1_solr_field = \
            self.solr.create_url_and_get_response(select_dict={'FileName': folder1}).json()['response']['docs'][0]['IsVisible']

        if len(folder1_list) == 0 and not folder1_solr_field:
            self.log.info("Deleted folder hierarchy didn't remain after delete operation and Solr field set "
                          "correctly")
        else:
            raise Exception("Deleted folder hierarchy remained after delete operation or Solr field "
                            "is not set correctly")

    def verify_delete_user(self, user_guid, inner_folder, user_items):

        """ Verifies the browse delete feature for user """

        djob3 = self.instance.delete_data_from_browse(user_guid, folder=True)
        djob3.wait_for_completion()
        self.log.info(f"User deleted from browse: {self.users[0]}")

        for item in user_items:
            item_solr_field = \
                self.solr.create_url_and_get_response(select_dict={'FileName': item}).json()['response']['docs'][0][
                    'IsVisible']
            files_list, files_dict = self.instance.find(file_name=item, show_deleted=True)
            if not item_solr_field and len(files_list) == 0:
                self.log.info(
                    "Deleted user item is not found even when include deleted items is enabled and Solr field is "
                    "set correctly")
            else:
                raise Exception("Deleted user item is found even when include deleted items is enabled or Solr "
                                "field is not set correctly")

        # Check inner folders
        folder2_list, folder2_dict = self.instance.find(file_name=inner_folder, show_deleted=True)
        folder2_solr_field = \
            self.solr.create_url_and_get_response(select_dict={'FileName': inner_folder}).json()['response']['docs'][0][
                'IsVisible']
        if len(folder2_list) == 1 and folder2_solr_field:
            self.log.info("Inner folder remained after delete operation and Solr field set correctly")
        else:
            raise Exception("Inner folder hierarchy didn't remain after delete operation or Solr field "
                            "is not set correctly")

    def verify_post_delete_backup(self, user_items):

        """ Verifies the backup after delete operations in browse """

        numberOfItemsInBrowse1 = len(self.instance.find(file_name="*")[0])
        self.log.info(f"Number of items in browse before backup: {numberOfItemsInBrowse1}")

        # Create data in users Onedrive
        self.log.info(f'Generating new data on {self.users} OneDrive')
        for i in range(len(self.users)):
            self.log.info(f'Creating {self.number_of_docs} files in {self.users[i]}\'s OneDrive')
            self.cvcloud_object.one_drive.create_files(no_of_docs=self.number_of_docs, user=self.users[i])

        # run backup of all users
        numberOfBackedupFiles = self.run_backup()

        numberOfItemsInBrowse2 = len(self.instance.find(file_name="*")[0])

        self.log.info(f"Number of backed up files: {numberOfBackedupFiles}")
        self.log.info(f"Number of items in browse after backup: {numberOfItemsInBrowse2}")

        if numberOfBackedupFiles == (numberOfItemsInBrowse2 - numberOfItemsInBrowse1):
            self.log.info(" Only the new files are backed up")
        else:
            raise Exception("Verification of post backup stats after deletions in browse failed")

        for item in user_items:
            item_solr_field = \
            self.solr.create_url_and_get_response(select_dict={'FileName': item}).json()['response']['docs'][0][
                'IsVisible']
            files_list, files_dict = self.instance.find(file_name=item, show_deleted=True)
            if not item_solr_field and len(files_list) == 0:
                self.log.info(
                    "Deleted user item is not found after performing a backup job and Solr field is "
                    "set correctly")
            else:
                raise Exception("Deleted user item is found after performing a backup job or Solr "
                                "field is not set correctly")
    def setup(self):

        """Setup function of this test case"""

        try:
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
            self.users = self.tcinputs.get('Users')
            self.number_of_docs = self.tcinputs.get('NumberOfDocs')
            self.o365_plan = self.tcinputs.get('O365Plan')
            self.proxy_client = self.tcinputs['AccessNode']
            self.cvcloud_object = CloudConnector(self)
            self.cvcloud_object.cvoperations.cleanup()
            self.cvcloud_object.instance = self._instance
            self.solr = SolrHelper(self.cvcloud_object)
            self.log.info(self.solr.set_cvsolr_base_url())

        except Exception as exp:
            self.log.exception(exp)

    def run(self):
        """Run function of this test case"""
        try:
            self.run_and_verify_discovery()

            # Delete data on Onedrive user accounts
            for user in self.users:
                self.log.info(f'Deleting data on {user}\'s OneDrive')
                self.cvcloud_object.one_drive.delete_all_data_on_onedrive(user)

            # Add users to client
            self.log.info(f'Adding users: {self.users} to client')
            self.subclient.add_users_onedrive_for_business_client(self.users, self.o365_plan)

            # Create data in users Onedrive
            self.log.info(f'Generating new data on {self.users} OneDrive')
            for i in range(len(self.users)):
                self.log.info(f'Creating {self.number_of_docs} files in {self.users[i]}\'s OneDrive')
                self.cvcloud_object.one_drive.create_files(no_of_docs=self.number_of_docs, user=self.users[i],
                                                           folder=True)
                self.cvcloud_object.one_drive.create_files(no_of_docs=self.number_of_docs, user=self.users[i],
                                                           folder=True, word=False, pdf=True)

            self.onedrive_items = self.cvcloud_object.one_drive.get_all_onedrive_items(self.users[0])

            # run backup of all users
            self.run_backup()

            # Verify incremental backup for correct marking of deleted items
            file1 = self.onedrive_items['root'][1][0][f'{cloud_apps_constants.ONEDRIVE_FOLDER}'][0][0]
            folder1 = list(self.onedrive_items['root'][1][0][f'{cloud_apps_constants.ONEDRIVE_FOLDER}'][1][0].keys())[0]
            self.verify_incremental(file1, folder1)

            # Verify browse_delete
            file2 = self.onedrive_items['root'][1][0][f'{cloud_apps_constants.ONEDRIVE_FOLDER}'][0][1]
            folder2 = list(self.onedrive_items['root'][1][0][f'{cloud_apps_constants.ONEDRIVE_FOLDER}'][1][1].keys())[0]
            self.verify_browse_delete(file1, file2, folder1, folder2)

            # Delete user
            user_response = self.subclient.search_for_user(self.users[0])
            user_guid = user_response[0].get('user').get('userGUID')
            user_items = self.onedrive_items['root'][1][0][f'{cloud_apps_constants.ONEDRIVE_FOLDER}'][0]
            self.verify_delete_user(user_guid, folder2, user_items)

            # Verify post delete incremental backup
            self.verify_post_delete_backup(user_items)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.log.info(f'Test case status: {self.status}')

            # Delete the client
            self.cvcloud_object.cvoperations.delete_client(self.client_name)

            # Clear user's onedrive
            for user in self.users:
                self.cvcloud_object.one_drive.delete_all_data_on_onedrive(user)

            # Clear temp
            self.cvcloud_object.cvoperations.cleanup()
        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')