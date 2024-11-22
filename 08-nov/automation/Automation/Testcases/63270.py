# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for Verification of Search and Restore

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

import time
import random

from Application.CloudApps.cloud_connector import CloudConnector
from Application.CloudApps import constants as CloudConstants
from Application.CloudApps.csdb_helper import CSDBHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components.panel import ModalPanel
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
        self.name = "OneDrive v2: Verification of Search and Restore"
        self.browser = None
        self.users = None
        self.plan = None
        self.navigator = None
        self.admin_console = None
        self.onedrive = None
        self.single_user = None
        self.jobs = None
        self.modal_panel = None
        self.file_server = None
        self.dest_path = None
        self.mssql = None
        self.csdb_helper = None
        self.solr_helper_obj = None
        self.cvcloud_object = None
        self.bkp_job_details = None
        self.rst_job_details = None
        self.user_details = None


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
            self.tcinputs['Name'] = "OD_63270"
            self.users = self.tcinputs['Users'].split(",")
            self.plan = self.tcinputs['Office365Plan']
            self.user_details = self.tcinputs['UserDetails']  #{"Mail":"UserName"}
            self.csdb_helper = CSDBHelper(self)
            self.jobs = Jobs(self.admin_console)
            self.modal_panel = ModalPanel(self.admin_console)

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

            #Data generation
            for user in self.users:
                self.cvcloud_object.one_drive.delete_folder(user_id=user)
                self.cvcloud_object.one_drive.create_files(
                    user=user,
                    no_of_docs=3,pdf=True)

            time.sleep(60)  # Give time for OneDrive sync

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
    def add_users_and_run_backup(self, users, plan):
        """
        adding users and running backup
        Args:
                users (list)       --   list of users
                plan (str)         --   Office365 plan
        """
        try:
            self.onedrive.refresh_cache()
            time.sleep(30) #time to refresh
            self.onedrive.add_user(users, plan)
            self.bkp_job_details=self.onedrive.run_backup()
        except Exception:
            raise CVTestStepFailure(f'Adding users and starting backup failed')

    @test_step
    def select_users_and_open_browse(self):
        """
        selecting users and navigating to browse section
        """
        try:
            self.onedrive._select_all_users()
            self.onedrive._click_restore(account=False)
        except Exception:
            raise CVTestStepFailure(f'Navigating to browse failed')

    def get_file_properties_from_user(self,user_id):
        """
        Method to fetch file properties from OneDrive Automation folder
        Args:
            user_id (str)   --  SMTP address of the user
        """

        folder = CloudConstants.ONEDRIVE_FOLDER
        folder_id = self.cvcloud_object.one_drive.get_folder_id_from_graph(user_id, folder)
        self.log.info(f'Fetching items from {folder} folder')
        return self.cvcloud_object.one_drive._get_files_list(user_id, folder_id, save_to_db=False)

    @test_step
    def verify_correct_file_fetched_and_verify_facets(self):
        """
        verifying the file and its facets
        """
        try:
            user=self.users[random.randrange(len(self.users))] #selecting random user
            response=self.get_file_properties_from_user(user)
            random_file=response[random.randrange(len(response))]['name'] #selecting random file
            random_file_name=f'"{random_file}"'
            browse_response = self.onedrive.apply_global_search_filter_and_get_result(random_file_name,columns=['Name'])
            result = self.onedrive.compare_file(random_file, browse_response)
            if result != "File Matched":
                raise Exception('File Not Matched')
            self.log.info(f'{result}')

            #verifying the facets of file
            dict={}
            dict["File extension"]=random_file.split(".")[-1]
            dict["User"]=self.user_details[user]
            facet_list=["File extension","User"]
            facet_dict = self.onedrive.get_facet_details_of_single_file(facet_list)
            result = self.onedrive.compare_facets_of_file(dict, facet_dict)
            if result != "Facets of File Matched":
                raise Exception('Facets of File Matched not matched')
            self.log.info(f'{result}')
        except Exception:
            raise CVTestStepFailure(f'verifying the file and its facets failed')

    @test_step
    def verify_facets_apply_correctly(self):
        """
        applying and verifying the applied facet
        """
        try:
            self.onedrive.apply_global_search_filter("*")
            extensions=["pdf","docx"]
            random_extension=extensions[random.randrange(len(extensions))] #selecting random extension
            facet_response = self.onedrive.click_facet('File extension',random_extension)
            result = self.onedrive.compare_facet_response('File extension',random_extension,facet_response)
            if result !="File extension Facet Matched":
                raise Exception('File extension facet results not matched')
            self.log.info(f'{result}')

            self.onedrive.apply_global_search_filter("*")
            user=self.users[random.randrange(len(self.users))]  #selecting random user
            random_user_name=self.user_details[user]
            facet_response = self.onedrive.click_facet('User', random_user_name)
            result = self.onedrive.compare_facet_response('User', user, facet_response)
            if result !="User Facet Matched":
                raise Exception('User facet results not matched')
            self.log.info(f'{result}')
        except Exception:
            raise CVTestStepFailure(f'Applied facet verification failed')

    @test_step
    def verify_filters_apply_correctly(self):
        """
        applying and verifying the applied filter
        """
        try:
            extensions = ["PDFs", "Documents"]
            random_extension = extensions[random.randrange(len(extensions))]  #selecting random extension
            filter_config=["searchType",random_extension]
            browse_response = self.onedrive.apply_dropdown_type_search_filter(filter_config)
            result = self.onedrive.compare_filter_response(filter_config, browse_response)
            if result != "":
                self.log.info(f'{result}')
                raise Exception('Type filter results not matched')
            self.log.info('Type filter verified successfully')

            filter_config = ["locationOption", "Path", "customLocation", "\\" + CloudConstants.ONEDRIVE_FOLDER ]
            browse_response = self.onedrive.apply_advance_search_filter(filter_config)
            result = self.onedrive.compare_filter_response(filter_config, browse_response)
            if result != "":
                self.log.info(f'{result}')
                raise Exception('location filter results not matched')
            self.log.info('location filter verified successfully')

            user = self.users[random.randrange(len(self.users))]
            filter_config = ["userNameOption", "User name", "customUserName",user]
            browse_response = self.onedrive.apply_advance_search_filter(filter_config)
            result=self.onedrive.compare_filter_response(filter_config, browse_response)
            if result != "":
                self.log.info(f'{result}')
                raise Exception('User filter results not matched')
            self.log.info('User filter verified successfully')

        except Exception:
            raise CVTestStepFailure(f'verifying the applied filter failed')

    @test_step
    def verify_restore(self):
        """
        verifying the restore
        """
        try:
            self.admin_console.refresh_page()
            backup_count=int(self.bkp_job_details['No of objects backed up'])
            self.rst_job_details=self.onedrive.run_restore(destination = o365_constants.RestoreType.IN_PLACE,restore_option = o365_constants.RestoreOptions.OVERWRITE)
            restore_count = int(self.rst_job_details['No of files restored']) - len(self.users) # Automation folder is restored for each user
            self.log.info(f'Documents selected: {backup_count};'
                          f' Documents restored: {restore_count}')
            if backup_count!=restore_count:
                raise Exception('Count Mismatch After Restore')
            self.log.info('Restore verified successfully')
        except Exception:
            raise CVTestStepFailure(f'Verifying the restore failed')

    def run(self):
        """Run function of this test case"""
        try:
            self.add_users_and_run_backup(self.users, self.plan)
            self.admin_console.driver.back()  # to navigate back to users tab
            self.select_users_and_open_browse()
            self.verify_correct_file_fetched_and_verify_facets()
            self.verify_facets_apply_correctly()
            self.verify_filters_apply_correctly()
            self.verify_restore()

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.status == constants.PASSED:
                for user in self.users:
                    self.cvcloud_object.one_drive.delete_folder(user_id=user)
                self.cvcloud_object.cvoperations.cleanup()
                self.navigator.navigate_to_office365()
                self.onedrive.delete_office365_app(self.tcinputs['Name'])
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)