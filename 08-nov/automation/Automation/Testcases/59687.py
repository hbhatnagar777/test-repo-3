# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for OneDrive v2 Verification of Office365 Plan Configuration

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""


import json
import re
import time

from Application.CloudApps.cloud_connector import CloudConnector
from Application.CloudApps.one_drive import OneDrive
from Application.CloudApps.csdb_helper import CSDBHelper
from Application.Office365.solr_helper import SolrHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages import constants as o365_constants
from Web.AdminConsole.Office365Pages.onedrive import OneDrive
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.name = "Onedrive v2: Verification of Office365 Plan Configuration"
        self.time = str(int(time.time()))
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.onedrive = None
        self.users = None
        self.cvcloud_object = None
        self.csdb_helper = None
        self.solr_helper_obj = None
        self.mssql = None
        self.jobs = None
        self.file_server = None
        self.dest_path = None
        self.plan = None
        self.include_plan = None
        self.exclude_plan = None
        self.len_exclude_folders = None
        self.len_include_folders = None
        self.solr_query_params = {'start': 0, 'rows': 500}

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

            self.csdb_helper = CSDBHelper(self)
            self.jobs = Jobs(self.admin_console)

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_plan()
            self.plan = Plans(self.admin_console)
            filters = {'include_folders': self.tcinputs['IncludeFolders'],
                       'include_files': self.tcinputs['IncludeFiles']}
            self.include_plan = 'Automation_IncludeFilters_' + self.time
            self.plan.create_office365_plan(plan_name=self.include_plan,
                                            onedrive_filters=filters)
            self.navigator.navigate_to_plan()
            filters = {'exclude_folders': self.tcinputs['ExcludeFolders'],
                       'exclude_files': self.tcinputs['ExcludeFiles']}
            self.exclude_plan = 'Automation_ExcludeFilters_' + self.time
            self.plan.create_office365_plan(plan_name=self.exclude_plan,
                                            onedrive_filters=filters)

            self.tcinputs['Name'] += "_OD_59687"
            self.users = self.tcinputs['Users'].split(",")
            self.file_server = self.tcinputs['FileServer']
            self.dest_path = self.tcinputs['DestPath']

            self.navigator.navigate_to_office365()
            self.log.info("Creating an object for office365 helper")
            self.tcinputs['office_app_type'] = OneDrive.AppType.one_drive_for_business
            self.onedrive = OneDrive(self.tcinputs, self.admin_console)

            self.mssql = MSSQL(
                self.tcinputs['SQLServerName'],
                self.tcinputs['SQLUserName'],
                self.tcinputs['SQLPassword'],
                'CommServ',
                as_dict=False)

            self.onedrive.create_office365_app()
            self._initialize_sdk_objects()

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

    @test_step
    def get_doc_list_from_index(self, user):
        """
        Query Index Server wrt Job Id to get Document count

        Args:
            user:   Email id of user

        """
        try:
            query_url = self.csdb_helper.get_index_server_url(
                self.mssql, client_name=self.tcinputs['Name'])
            query_url += '/select?'
            self.solr_helper_obj = SolrHelper(self.cvcloud_object, query_url)
            solr_results = self.solr_helper_obj.create_url_and_get_response(
                {'OwnerName': f'*{user}*'}, op_params=self.solr_query_params)
            user_guid = self.csdb_helper.get_user_guid(
                client_name=self.tcinputs['Name'], user_name=user)

            file_names = list()
            folder_names = list()
            for file in json.loads(solr_results.content)['response']['docs']:
                if file['DocumentType'] == 1:
                    file_names.append(file['FileName'])
                elif file['DocumentType'] == 4:
                    if file['FileName'] not in ['My Drive', user_guid]:
                        folder_names.append(file['FileName'])

            file_names = list(set(file_names))
            folder_names = list(set(folder_names))
            self.log.info(f'List of files obtained from Index: {file_names}')
            self.log.info(f'List of folders obtained from Index: {folder_names}')
            return file_names, folder_names
        except Exception:
            raise CVTestStepFailure(f'Error while querying index')

    def traverse_folders(self, folders):
        """
        Traverse Folder hierarchy recursively

        Args:
            folders:

        Returns:

        """
        try:
            file_list = list()
            folder_list = list()
            for key, value in folders.items():
                folder_list.append(key)
                file_list += value[0]
                for items in value[1]:
                    if isinstance(items, dict):
                        files, folder = self.traverse_folders(items)
                        file_list += files
                        folder_list += folder
            return file_list, folder_list
        except Exception:
            raise CVTestStepFailure('Exception while traversing folders')

    @test_step
    def apply_include_filters(self):
        """Applies include filters on the list of files and folder in OneDrive"""
        try:
            # Gets the list of all files and folders in OneDrive
            file_names = list()
            folder_list = list()
            root = self.cvcloud_object.one_drive.get_all_onedrive_items(self.users[0])

            # Gets the list of folders to be included and the files present in those folders
            for folder in root['root'][1]:
                if list(folder.keys())[0] in self.tcinputs['IncludeFolders']:
                    file_names, folder_list = self.traverse_folders(folder)
                    folder_list.append(list(folder.keys())[0])
            folder_list = set(folder_list)

            # Applies filters on the list of files present in those folders
            file_filters = '|'.join(self.tcinputs['IncludeFiles'])
            file_filters = file_filters.replace('.', '\\.')
            file_filters = file_filters.replace('*', '\\w*')
            self.log.info(f'file_filters: {file_filters}')
            file_list = list()
            pattern = re.compile(file_filters)
            for file in file_names:
                if pattern.search(file):
                    file_list.append(file)
            file_list = set(file_list)

            self.log.info(f'File List after applying Include Filters: {file_list}')
            self.log.info(f'Folder List after applying Include Filters: {folder_list}')
            self.len_include_folders = int(len(folder_list))
            return list(file_list), list(folder_list)
        except Exception:
            raise CVTestStepFailure('Exception while applying Include Filters')

    @test_step
    def apply_exclude_filters(self):
        """Applies exclude filters on the list of files and folder in OneDrive"""
        try:
            # Get the list of all files and folders in OneDrive
            exclude_file_names = list()
            exclude_folder_list = list()
            root = self.cvcloud_object.one_drive.get_all_onedrive_items(self.users[1])
            all_files_list, all_folders_list = self.traverse_folders(root)
            all_folders_list.remove('root')

            # Get the list of folders to be excluded and files
            # present in those folders which are also to be excluded
            for folder in root['root'][1]:
                exclude_folder_list.append(list(folder.keys())[0])
                if list(folder.keys())[0] in self.tcinputs['ExcludeFolders']:
                    exclude_file_names, exclude_folder_list = self.traverse_folders(folder)
                    exclude_folder_list.append(list(folder.keys())[0])
            exclude_folder_list = set(exclude_folder_list)

            # Gets the list of files to be excluded according to the filters
            file_filters = '|'.join(self.tcinputs['ExcludeFiles'])
            file_filters = file_filters.replace('.', '\\.')
            file_filters = file_filters.replace('*', '\\w*')
            self.log.info(f'file_filters: {file_filters}')
            pattern = re.compile(file_filters)
            for file in all_files_list:
                if pattern.search(file):
                    exclude_file_names.append(file)
            exclude_file_names = set(exclude_file_names)

            # Removes the files and folders to be excluded from the list of all files
            for file in exclude_file_names:
                if file in all_files_list:
                    all_files_list.remove(file)
            for item in exclude_folder_list:
                if item in all_folders_list:
                    all_folders_list.remove(item)

            self.log.info(f'File List after applying Exclude Filters: {all_files_list}')
            self.log.info(f'Folders List after applying Exclude Filters: {all_folders_list}')
            self.len_exclude_folders = int(len(all_folders_list))
            return list(all_files_list), list(all_folders_list)
        except Exception:
            raise CVTestStepFailure('Exception while applying Exclude Filters')

    @test_step
    def compare_lists(self, index_list, onedrive_list):
        """
        Compare lists obtained from Index and OneDrive and verify that they are equal
        Args:
            index_list (list):      List obtained from index
            onedrive_list (list):   List obtained from user's OneDrive

        Returns:

        """
        try:
            # We are not checking if the lists are equal since a
            # few items could have failed during backup
            for item in index_list:
                if item not in onedrive_list:
                    self.log.error(f'{item} found in list obtained from index but not '
                                   f'found in filtered list obtained from OneDrive')
                    raise Exception('List obtained from Index and OneDrive don\'t match')
        except Exception:
            raise CVTestStepFailure('List obtained from Index and OneDrive don\'t match')

    @test_step
    def verify_restore_docs_count(self, job_details):
        """
        Verify count of documents restored against count of documents in index
        """
        try:
            query_url = self.csdb_helper.get_index_server_url(
                self.mssql, client_name=self.tcinputs['Name'])
            query_url += '/select?'
            self.solr_helper_obj = SolrHelper(self.cvcloud_object, query_url)
            solr_results = self.solr_helper_obj.create_url_and_get_response(
                {'DocumentType': '1'})
            doc_count = int(self.solr_helper_obj.get_count_from_json(solr_results.content))
            self.log.info(f'Document Count obtained from Index: {doc_count}')

            # removing folder count, user guid and my drive count

            restore_count = (int(job_details['No of files restored']) -
                             (self.len_include_folders + self.len_exclude_folders + 2*len(self.users)))
            self.log.info(f'Documents in index: {doc_count};'
                          f' Documents restored: {restore_count}')
            if doc_count != restore_count:
                raise Exception('Count Mismatch for Restore of all documents in client')
        except Exception:
            raise CVTestStepFailure(f'Verification of count FAILED')

    def run(self):
        try:
            # Addition of users to Office 365 App and initiation of backup
            self.onedrive.add_user(
                users=[self.users[0]], plan=self.include_plan)
            self.onedrive.add_user(
                users=[self.users[1]], plan=self.exclude_plan)
            self.onedrive.run_backup()

            time.sleep(30)  # Wait for Playback to complete

            index_files, index_folders = self.get_doc_list_from_index(self.users[0])
            onedrive_files, onedrive_folders = self.apply_include_filters()
            self.compare_lists(index_files, onedrive_files)
            self.compare_lists(index_folders, onedrive_folders)

            index_files, index_folders = self.get_doc_list_from_index(self.users[1])
            onedrive_files, onedrive_folders = self.apply_exclude_filters()
            self.compare_lists(index_files, onedrive_files)
            self.compare_lists(index_folders, onedrive_folders)

            self.navigator.navigate_to_office365()
            self.onedrive.access_office365_app(self.tcinputs['Name'])
            restore_job = self.onedrive.run_restore(
                destination=o365_constants.RestoreType.TO_DISK,
                file_server=self.tcinputs['FileServer'],
                dest_path=self.tcinputs['DestPath'])
            self.verify_restore_docs_count(restore_job)

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.log.info("Testcase Passed")
                self.navigator.navigate_to_office365()
                self.onedrive.delete_office365_app(self.tcinputs['Name'])
                self.navigator.navigate_to_plan()
                self.plan.delete_plan(self.include_plan)
                self.plan.delete_plan(self.exclude_plan)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
