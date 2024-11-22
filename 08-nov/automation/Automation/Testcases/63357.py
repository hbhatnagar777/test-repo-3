# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for Verification of Retention Criteria

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

import time
import requests

from Application.CloudApps.cloud_connector import CloudConnector
from Application.CloudApps import constants as CloudConstants
from Application.CloudApps.csdb_helper import CSDBHelper
from Application.Office365.solr_helper import SolrHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components.panel import ModalPanel
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.onedrive import OneDrive
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception



class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.name = "OneDrive v2: Verification of retention criteria"
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
        self.solr_update_url=None
        self.index_app_type_id=None
        self.index_server_client_name=None

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
            self.tcinputs['Name'] = "OD_63357"
            self.user = self.tcinputs['Users'].split(",")
            self.plan = self.tcinputs['Office365Plan']
            self.index_server_client_name = self.tcinputs["IndexServer"]

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
            self.cvcloud_object.one_drive.create_folder(folder_name="folder_1",user_id=self.user[0],location="root")
            self.cvcloud_object.one_drive.create_folder(folder_name="folder_2",user_id=self.user[0],location="root")
            self.cvcloud_object.one_drive.create_files(
                user=self.user[0],
                no_of_docs=5,new_folder=False,folder_path="folder_1")
            self.cvcloud_object.one_drive.create_files(
                user=self.user[0],
                no_of_docs=1,pdf=True, new_folder=False, folder_path="root")
            self.cvcloud_object.one_drive.create_files(
                user=self.user[0],
                no_of_docs=5,new_folder=False,folder_path="folder_2")
            self.cvcloud_object.one_drive.create_folder(folder_name="folder_3",user_id=self.user[0],location="folder_1")
            self.cvcloud_object.one_drive.create_files(
                user=self.user[0],
                no_of_docs=5, new_folder=False, folder_path="folder_1/folder_3")
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
            # Create object of the
            # Backupset class
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
    def add_users_and_run_backup(self, user, plan):
        """
        adding users and running backup
        Args:
                users (list)       --   list of users
                plan (str)         --   Office365 plan
        """
        try:
            self.onedrive.refresh_cache()
            time.sleep(30) #time to refresh
            self.onedrive.add_user(user, plan)
            self.onedrive.run_backup()
        except Exception:
            raise CVTestStepFailure(f'Adding users and starting backup failed')

    @test_step
    def delete_items_and_run_backup(self):
        """
        Deleting some files and folders then running backup
        """
        try:
            self.cvcloud_object.one_drive.delete_folder(folder_name="folder_1", user_id=self.user[0])
            response = self.solr_helper_obj.create_url_and_get_response(select_dict={"FileName":"*.pdf"})
            deleted_item = response.json()['response']['docs'][0]['FileName']
            folder_id = self.cvcloud_object.one_drive.get_folder_id_from_graph(user_id=self.user[0], folder='root')
            self.log.info(f'Fetching items from root folder')
            file_content=self.cvcloud_object.one_drive._get_files_list(user_id=self.user[0], folder_id=folder_id, save_to_db=False)
            for each_item in file_content:
                if each_item['name'] == deleted_item:
                    deleted_file_id = each_item['id']
                    break
            self.cvcloud_object.one_drive.delete_single_file(file_id=deleted_file_id,user_id=self.user[0])
            self.onedrive.run_backup()
        except Exception:
            raise CVTestStepFailure(f'Deleting some files and folders then running backup failed')

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

    @test_step
    def initialize_solr(self):
        """
        initializing the solr objects
        """
        try:
            query_url = self.csdb_helper.get_index_server_url(self.mssql, client_name=self.tcinputs['Name'])
            self.index_app_type_id=CloudConstants.ONEDRIVE_INDEX_APPTYPE_ID
            self.solr_update_url=query_url
            query_url += '/select?'
            self.solr_helper_obj = SolrHelper(self.cvcloud_object, query_url)
        except Exception:
            raise CVTestStepFailure(f'initializing the solr objects failed')

    def update_field(self, content_id, field_name, field_value):
        """Updates specified field having specified content id
                   Args:

                       content_id(str)                --  content id of the item
                       Example: "c8d2d2ebab2a86290f37cd6ae2ecba91!0c6932ab50bf08fa68596dacb6259f8d

                       field_name(str)                --  Name of the field to be updated

                       field_value                    --  Value of the field to be updated

               """
        try:
            self.solr_update_url += '/update?&commit=true&wt=json'
            request_json = [{
                "contentid": content_id,
                field_name: {
                    "set": field_value
                }
            }]
            response=requests.post(url=self.solr_update_url, json=request_json)
        except Exception as ex:
            raise Exception(ex)


    @test_step
    def process_index_retention(self, index_app_type_id, index_server_client_name):
        """
         Makes API call to process index retention rules
         Args:
            index_app_type_id                 (int)   --  app type id
            index_server_client_name          (str)   --  client name of index server
        """
        try:
            self._subclient.process_index_retention_rules(index_app_type_id,index_server_client_name)
        except Exception:
            raise CVTestStepFailure(f'process index retention rules failed')

    @test_step
    def change_time_and_update_field(self,deleted_items_list):
        """
        changing the deleted time and updating in solr
         Args:
            deleted_items_list (list)   --  list of deleted items
        """
        try:
            for each_item in deleted_items_list:
                new_date_as_int = self.solr_helper_obj.subtract_retention_time(each_item["DateDeleted"], 500)
                self.update_field(each_item["contentid"], "DateDeleted", new_date_as_int)
        except Exception:
            raise CVTestStepFailure(f'changing the deleted time and updating in solr failed')

    @test_step
    def check_isvisible(self,deleted_items_list_after_update):
        """
        checking isvisible flag for deleted items in solr
         Args:
            deleted_items_list_after_update (list)   --  list of deleted items which time is updated
        """
        try:
            for each_item in deleted_items_list_after_update:
                if each_item['IsVisible'] != False:
                    raise Exception('IsVisible flag is not set to false')
            self.log.info(f'IsVisible flag verified successfully')
        except Exception:
            raise CVTestStepFailure(f'checking isvisible flag for deleted items in solr failed')

    def delete_remaining_file(self):
        """to delete single remaining file"""
        try:
            folder_id = self.cvcloud_object.one_drive.get_folder_id_from_graph(user_id=self.user[0], folder='root')
            self.log.info(f'Fetching item from root folder')
            file_content = self.cvcloud_object.one_drive._get_files_list(user_id=self.user[0], folder_id=folder_id,save_to_db=False)
            deleted_file_id=file_content[0]['id']
            self.cvcloud_object.one_drive.delete_single_file(file_id=deleted_file_id, user_id=self.user[0])
        except Exception as ex:
            raise Exception(ex)

    def run(self):
        """Run function of this test case"""
        try:
            self.add_users_and_run_backup(self.user, self.plan)
            self.admin_console.driver.back()  # to navigate back to users tab
            self.select_users_and_open_browse()
            total_items=self.onedrive.get_browse_count()
            self.initialize_solr()
            self.admin_console.driver.back()  #to navigate back to users tab
            self.delete_items_and_run_backup()
            self.admin_console.driver.back()  # to navigate back to users tab
            self.select_users_and_open_browse()
            total_items_after_deletion=self.onedrive.get_browse_count(show_deleted=True)
            self.admin_console.driver.back()
            self.log.info(f'Items Before Delete: {total_items[0]};'
                          f'Items After Delete: {total_items_after_deletion[0]};'
                          f'Items After Delete And Applying Show Deleted: {total_items_after_deletion[1]}')
            if total_items[0]!=total_items_after_deletion[1] or total_items_after_deletion[0]!=total_items[0]-(total_items_after_deletion[1]-total_items_after_deletion[0]):
                raise Exception('Deleted Flag Not Set')
            response=self.solr_helper_obj.create_url_and_get_response(select_dict={"DateDeleted":"*"},attr_list={"contentid","DateDeleted","IsVisible"},op_params = {"rows": 100})
            deleted_items_list=response.json()['response']['docs']
            self.change_time_and_update_field(deleted_items_list)
            self.process_index_retention(self.index_app_type_id,self.index_server_client_name)
            time.sleep(120) #time to process index retention rules
            self.select_users_and_open_browse()
            total_items_after_update = self.onedrive.get_browse_count(show_deleted=True)
            if total_items_after_update[0] != total_items_after_update[1]:
                raise Exception('Deleted items are still present in browse')
            response = self.solr_helper_obj.create_url_and_get_response(select_dict={"DateDeleted": "*"},attr_list={"contentid", "DateDeleted","IsVisible"},op_params = {"rows": 100})
            deleted_items_list_after_update = response.json()['response']['docs']
            self.check_isvisible(deleted_items_list_after_update)

        except Exception as err:
            handle_testcase_exception(self, err)


    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.status == constants.PASSED:
                self.cvcloud_object.one_drive.delete_folder(folder_name="folder_2", user_id=self.user[0])
                self.delete_remaining_file()
                self.cvcloud_object.cvoperations.cleanup()
                self.navigator.navigate_to_office365()
                self.onedrive.delete_office365_app(self.tcinputs['Name'])
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
