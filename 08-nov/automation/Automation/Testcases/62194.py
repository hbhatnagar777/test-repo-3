# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for OneDrive v2 to verify single-user restore, multiple user restore, restore to disk,
in-place restore and Out-Of-Place restore

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""


import time

from Application.CloudApps.cloud_connector import CloudConnector
from Application.CloudApps.one_drive import OneDrive
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages import constants as o365_constants
from Application.CloudApps.constants import ONEDRIVE_FOLDER
from Web.AdminConsole.Office365Pages.onedrive import OneDrive
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = ("OneDrive v2: verify  single-user restore, multiple user restore, "
                     "restore to disk, in-place restore and Out-Of-Place restore")
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.onedrive = None
        self.client_name = None
        self.users = None
        self.cvcloud_object = None
        self.jobs = None
        self.folderslist = None

    def setup(self):
        """Initial configuration for the testcase."""
        try:

            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword'])

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.tcinputs['Name'] += str(int(time.time()))
            self.users = self.tcinputs['Users'].split(",")

            self.log.info("Creating an object for office365 helper")
            self.tcinputs['office_app_type'] = OneDrive.AppType.one_drive_for_business

            # Create one drive client
            self.onedrive = OneDrive(self.tcinputs, self.admin_console)

            self.onedrive.create_office365_app()
            self._initialize_sdk_objects()

            self.folderslist = set([ONEDRIVE_FOLDER])

            # Data generation
            for user in self.users:

                self.cvcloud_object.one_drive.delete_all_data_on_onedrive(user)
                self.cvcloud_object.one_drive.create_files(
                    user=user,
                    no_of_docs=o365_constants.OneDrive.INITIAL_DOC_COUNT.value)

            # Create Folder1 for user3 only
            self.cvcloud_object.one_drive.create_files(
                user=self.users[2],
                no_of_docs=o365_constants.OneDrive.INITIAL_DOC_COUNT.value,
                new_folder=False,
                folder_path='Folder1')
            self.folderslist.add('Folder1')

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def _initialize_sdk_objects(self):
        """Initializes the sdk objects after app creation"""
        self.commcell.refresh()
        self.log.info("Create client object for: %s", self.tcinputs['Name'])
        self._client = self.commcell.clients.get(self.tcinputs['Name'])
        self.log.info("Create agent object for: %s", self.tcinputs['AgentName'])
        self._agent = self._client.agents.get(self.tcinputs['AgentName'])
        if self._agent is not None:
            # Create object of Instance, if instance name is provided in the JSON
            if 'InstanceName' in self.tcinputs:
                self.log.info("Create instance object for: %s", self.tcinputs['InstanceName'])
                self._instance = self._agent.instances.get(self.tcinputs['InstanceName'])
            # Create object of the Backupset class
            if 'BackupsetName' in self.tcinputs:
                self.log.info("Creating backupset object for: %s",
                              self.tcinputs['BackupsetName'])
                # If instance object is not initialized, then instantiate backupset object
                # from agent
                # Otherwise, instantiate the backupset object from instance
                if self._instance is None:
                    self._backupset = self._agent.backupsets.get(
                        self.tcinputs['BackupsetName']
                    )
                else:
                    self._backupset = self._instance.backupsets.get(
                        self.tcinputs['BackupsetName']
                    )
            # Create object of the Subclient class
            if 'SubclientName' in self.tcinputs:
                self.log.info("Creating subclient object for: %s",
                              self.tcinputs['SubclientName'])
                # If backupset object is not initialized, then try to instantiate subclient
                # object from instance
                # Otherwise, instantiate the subclient object from backupset
                if self._backupset is None:
                    if self._instance is None:
                        pass
                    else:
                        self._subclient = self._instance.subclients.get(
                            self.tcinputs['SubclientName']
                        )
                else:
                    self._subclient = self._backupset.subclients.get(
                        self.tcinputs['SubclientName']
                    )

        # Creating CloudConnector object
        self.cvcloud_object = CloudConnector(self)
        self.cvcloud_object.cvoperations.cleanup()


    def run(self):
        try:
            user1 = self.users[0]
            user2 = self.users[1]
            user3 = self.users[2]
            user4 = self.users[3]

            # Addition of users to Office 365 App and initiation of backup
            self.onedrive.add_user()

            # Run Full backup
            self.onedrive.run_backup()

            # User1
            self.cvcloud_object.one_drive.get_file_properties(user=user1)

            # For one user, delete all data in onedrive user account.
            user1_folder_id = self.cvcloud_object.one_drive.get_folder_id_from_graph(user1)
            files_in_user1 = self.cvcloud_object.one_drive._get_files_list(
                user1, user1_folder_id, save_to_db=False)
            self.log.info(f'Folders in user1 : {files_in_user1}')

            self.log.info(f'Delete all items in one drive for user1 : {user1}')
            self.cvcloud_object.one_drive.delete_all_data_on_onedrive(user1)

            self.navigator.navigate_to_office365()
            self.onedrive.access_office365_app(self.tcinputs['Name'])

            # Run restore for user one
            self.onedrive.run_restore(
                destination=o365_constants.RestoreType.IN_PLACE,
                users = [user1],
                restore_option = o365_constants.RestoreOptions.SKIP)

            self.cvcloud_object.one_drive._compare_files(user_id=user1)

            # User2
            # For second user, modify few files.
            self.log.info(f'Modify few items in one drive for user2 : {user2}')
            user2_folder_id = self.cvcloud_object.one_drive.get_folder_id_from_graph(user2)
            files_in_user2 = self.cvcloud_object.one_drive._get_files_list(
                user2, user2_folder_id, save_to_db=False)
            self.log.info(f'Folders in user2 : {files_in_user2}')

            modified_files = []
            for i, item in enumerate(files_in_user2):
                # Modify two files
                if i < 2:
                    file_name = item['name']
                    modified_files.append(file_name)
                    self.log.info(f'Modify file: {file_name}')
                    self.cvcloud_object.one_drive.modify_file_content(user2, file_name)

            self.cvcloud_object.one_drive.get_file_properties(user=user2)
            self.navigator.navigate_to_office365()
            self.onedrive.access_office365_app(self.tcinputs['Name'])

            # Run restore
            self.onedrive.run_restore(
                destination=o365_constants.RestoreType.IN_PLACE,
                users=[user2],
                restore_option=o365_constants.RestoreOptions.SKIP)

            # Check files are modified after restore
            for each_file in modified_files:
                self.cvcloud_object.one_drive._compare_file(user_id=user2, file_name=each_file)

            # User3
            # For third user, add few folders and delete few folders.
            self.log.info(f'Add few folders in one drive for user3 : {user3}')
            for i in range(1, 2):
                # Add one folder - Folder2
                folder_name = f'Folder{i + 1}'
                self.folderslist.add(folder_name)
                self.cvcloud_object.one_drive.create_files(
                    user=user3,
                    no_of_docs=o365_constants.OneDrive.INITIAL_DOC_COUNT.value,
                    new_folder=False,
                    folder_path= folder_name)

            # Iterate folders list and index all folders
            for folder in self.folderslist:
                self.cvcloud_object.one_drive.get_file_properties(
                    user=user3, folder=folder, save_to_db_folder=True)

            self.log.info(f'Delete few folders in one drive for user3 : {user3}')
            for i in range(1):
                # Delete  folder , Folder1
                folder_name = f'Folder{i + 1}'
                self.cvcloud_object.one_drive.delete_folder(user_id=user3,folder_name= folder_name)


            self.navigator.navigate_to_office365()
            self.onedrive.access_office365_app(self.tcinputs['Name'])

            # Run restore
            self.onedrive.run_restore(
                destination=o365_constants.RestoreType.IN_PLACE,
                users=[user3],
                restore_option=o365_constants.RestoreOptions.COPY)

            # Iterate folders list and compare against indexed folders for all folders
            for folder in self.folderslist:
                restore_as_copy = True if (folder == ONEDRIVE_FOLDER) else False
                self.cvcloud_object.one_drive.compare_files_with_db(
                    user_id=user3, folder=folder, restore_as_copy=restore_as_copy)

            # User4
            self.cvcloud_object.one_drive.get_file_properties(user=user4)
            self.log.info(f'Do nothing for user4 : {user4}')
            self.navigator.navigate_to_office365()
            self.onedrive.access_office365_app(self.tcinputs['Name'])

            # Run restore
            self.onedrive.run_restore(
                destination=o365_constants.RestoreType.IN_PLACE,
                users=[user4],
                restore_option=o365_constants.RestoreOptions.OVERWRITE)

            self.cvcloud_object.one_drive._compare_files(user_id=user4)

            # OOP restore - User1, User4
            self.log.info(f'Run OOP restore for user : {user4}')
            self.navigator.navigate_to_office365()
            self.onedrive.access_office365_app(self.tcinputs['Name'])

            new_folder = 'Restore_OOP'
            self.onedrive.run_restore(
                destination=o365_constants.RestoreType.OOP,
                users=[user4],
                user_name= user1,
                dest_path=new_folder)

            self.cvcloud_object.one_drive.compare_onedrive_data_of_two_users(
                user_id1=user1, user_id2=user4, folder1=new_folder, folder_list2=self.folderslist)

            # Disk Restore - User2, User4
            self.log.info(f'Run disk restore for users : {user2}, {user4}')
            self.cvcloud_object.one_drive.get_file_properties(user=user2)
            self.cvcloud_object.one_drive.get_file_properties(user=user4)

            self.navigator.navigate_to_office365()
            self.onedrive.access_office365_app(self.tcinputs['Name'])

            # Delete directory on proxy if exists
            proxy_client = Machine(
                self.tcinputs['FileServer'],
                self.commcell)

            if proxy_client.check_directory_exists(self.tcinputs['DestPath']):
                proxy_client.remove_directory(self.tcinputs['DestPath'])

            self.onedrive.run_restore(
                destination=o365_constants.RestoreType.TO_DISK,
                users=[user2, user4],
                file_server=self.tcinputs['FileServer'],
                dest_path=self.tcinputs['DestPath'])

            for user in [user2, user4]:
                self.cvcloud_object.one_drive.compare_file_properties(
                    oop=True, to_disk=True, user_id=user)

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.navigator.navigate_to_office365()
                self.onedrive.delete_office365_app(self.tcinputs['Name'])
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
