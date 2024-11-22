# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

import time
import random
import copy
from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.FSOHelper import FSO
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.GovernanceAppsPages.EntitlementManager import EntitlementManager
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from dynamicindex.utils.activateutils import ActivateUtils
from dynamicindex.utils.constants import BASIC_WINDOWS_PERMISSIONS, INDIA_COUNTRY_NAME

test_step = TestStep()


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
        self.name = "Broken permission report : Acceptance Case"
        self.tcinputs = {
            "HostToAnalyze": None,
            "IndexServerName": None,
            "UserName": None,
            "Password": None
        }
        self.file_count = 5
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.fso_helper = None
        self.gdpr_helper = None
        self.activate_utils = None
        self.machine_name = None
        self.machine_obj = None
        self.root_path = None
        self.disabled_inheritance_folder = None
        self.disabled_inheritance_share = None
        self.disabled_inheritance_unc = None
        self.broken_folder = None
        self.broken_folder_share = None
        self.broken_folder_unc = None
        self.dc_plan_name = None
        self.fso_datasource_name = None
        self.original_permissions = None
        self.modified_permissions = None
        self.entitlement_manager = None
        self.original_permissions_inheritance = None

    def setup(self):
        """Setup function of this test case"""
        self.machine_name = self.tcinputs['HostToAnalyze']
        self.fso_datasource_name = f"broken_folder_datasource_{self.id}"
        self.dc_plan_name = f"FSO Plan {self.id}"
        self.machine_obj = Machine(machine_name=self.machine_name, commcell_object=self.commcell)
        drive_selector = OptionsSelector(self.commcell)
        self.activate_utils = ActivateUtils(self.commcell)
        drive_name = drive_selector.get_drive(machine=self.machine_obj)
        self.root_path = drive_name + "broken_folder_test"

    @test_step
    def initialize_browser(self):
        """Initializes the cvbrowser"""
        self.log.info(f"Checking if {self.root_path} is present on machine")
        if not self.machine_obj.check_directory_exists(self.root_path):
            self.log.info(f"Creating {self.root_path}")
            self.machine_obj.create_directory(self.root_path)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                          username=self.tcinputs['UserName'],
                                          password=self.tcinputs['Password'])
        self.admin_console.login(username=self.tcinputs['UserName'],
                                 password=self.tcinputs['Password'])
        self.log.info("Login completed successfully.")
        self.navigator = self.admin_console.navigator
        self.fso_helper = FSO(admin_console=self.admin_console, commcell=self.commcell)
        self.fso_helper.data_source_name = self.fso_datasource_name
        self.gdpr_helper = GDPR(admin_console=self.admin_console, commcell=self.commcell)
        self.gdpr_helper.data_source_name = self.fso_datasource_name
        self.entitlement_manager = EntitlementManager(self.admin_console)

    @test_step
    def create_inheritance_disabled_folder(self):
        """Generates folder with inheritance disabled"""
        self.disabled_inheritance_share = "disabled_inheritance"
        self.disabled_inheritance_folder = self.root_path + f"\\{self.disabled_inheritance_share}"
        self.log.info(f"Checking if {self.disabled_inheritance_folder} is present on machine")
        if not self.machine_obj.check_directory_exists(self.disabled_inheritance_folder):
            self.log.info(f"Creating {self.disabled_inheritance_folder} and sharing it")
            self.machine_obj.create_directory(self.disabled_inheritance_folder)
            try:
                self.machine_obj.share_directory(share_name=self.disabled_inheritance_share,
                                                 directory=self.disabled_inheritance_folder)
            except Exception:
                self.machine_obj.unshare_directory(share_name=self.disabled_inheritance_share)
                self.machine_obj.share_directory(share_name=self.disabled_inheritance_share,
                                                 directory=self.disabled_inheritance_folder)
        self.disabled_inheritance_unc = f"\\\\{self.machine_name}\\{self.disabled_inheritance_share}"
        self.activate_utils.sensitive_data_generation(database_path=self.disabled_inheritance_unc,
                                                      number_files=self.file_count)
        self.original_permissions_inheritance: dict = self.activate_utils.get_access_control_list(
            path=self.disabled_inheritance_unc,
            target_machine_name=self.machine_name)
        self.machine_obj.change_inheritance(folder_path=self.disabled_inheritance_folder,
                                            disable_inheritance=True)

    @test_step
    def create_broken_permission_folder(self):
        """Generates folder with mismatched permissions with parent folder"""
        self.broken_folder_share = "broken_folder"
        self.broken_folder = self.root_path + f"\\{self.broken_folder_share}"
        self.log.info(f"Checking if {self.broken_folder} is present on machine")
        if not self.machine_obj.check_directory_exists(self.broken_folder):
            self.log.info(f"Creating {self.broken_folder} and sharing it")
            self.machine_obj.create_directory(self.broken_folder)
            try:
                self.machine_obj.share_directory(share_name=self.broken_folder_share,
                                                 directory=self.broken_folder)
            except Exception:
                self.machine_obj.unshare_directory(share_name=self.broken_folder_share)
                self.machine_obj.share_directory(share_name=self.broken_folder_share,
                                                 directory=self.broken_folder)
        self.broken_folder_unc = f"\\\\{self.machine_name}\\{self.broken_folder_share}"
        self.activate_utils.sensitive_data_generation(database_path=self.broken_folder_unc,
                                                      number_files=self.file_count)
        self.original_permissions: dict = self.activate_utils.get_access_control_list(
            path=self.broken_folder_unc,
            target_machine_name=self.machine_name)
        self.modified_permissions = copy.deepcopy(self.original_permissions)
        self.log.info(f"Modifying permissions on folder {self.broken_folder} to mismatch it from parent")
        random_user = random.choice(list(self.original_permissions.keys()))
        self.log.info(f"Going to modify {random_user} permissions on folder {self.broken_folder}")
        existing_basic_permissions = set([
            basic_permission for basic_permission in
            self.original_permissions.get(random_user).intersection(set(BASIC_WINDOWS_PERMISSIONS))])
        new_basic_permissions = existing_basic_permissions
        while new_basic_permissions == existing_basic_permissions:
            new_basic_permissions = set(random.choices(
                BASIC_WINDOWS_PERMISSIONS, k=random.randint(1, len(BASIC_WINDOWS_PERMISSIONS))))
        self.modified_permissions[random_user] = new_basic_permissions
        self.activate_utils.apply_new_permissions(
            machine_name=self.machine_name, path=self.broken_folder, user=random_user,
            access_permissions=new_basic_permissions, grant=False)
        self.log.info(f"Original permissions : {self.original_permissions}")
        self.log.info(f"New permissions : {self.modified_permissions}")

    @test_step
    def cleanup(self):
        """Performs cleanup"""
        self.log.info(f"Checking for existing crawl data on machine {self.machine_name}")
        if self.machine_obj.check_directory_exists(self.root_path):
            self.log.info(f"Deleting existing crawl data from machine {self.machine_name}")
            self.machine_obj.remove_directory(self.root_path)
            self.log.info("Crawl data deleted successfully")
        self.fso_helper.fso_cleanup(client_name=self.machine_obj.client_object.client_name,
                                    datasource_name=self.fso_datasource_name)
        self.gdpr_helper.cleanup(plan_name=self.dc_plan_name)

    @test_step
    def create_plan(self):
        """Creates a FSO DC Plan to be used to create the data source"""
        self.navigator.navigate_to_plan()
        self.gdpr_helper.plans_obj.create_data_classification_plan(
            self.dc_plan_name, self.tcinputs['IndexServerName'],
            content_analysis=False, target_app='fso')

    @test_step
    def create_fso_client(self):
        """Create FSO Datasource"""
        self.navigator.navigate_to_governance_apps()
        self.fso_helper.fso_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.add_client(None, self.dc_plan_name)
        self.log.info("Creating a new FSO datasource now")
        self.fso_helper.file_server_lookup.add_file_server(
            self.machine_name, 'Host name',
            self.fso_datasource_name, INDIA_COUNTRY_NAME, self.root_path,
            agent_installed=True, live_crawl=True)
        self.log.info("FSO datasource created successfully")

    @test_step
    def wait_for_crawl_to_complete(self):
        """Waits for the crawl job to complete"""
        self.navigator.navigate_to_governance_apps()
        self.fso_helper.fso_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.select_details_action(self.machine_obj.client_object.client_name)
        self.fso_helper.fso_client_details.select_details_action(self.fso_datasource_name)
        if not self.fso_helper.file_server_lookup.wait_for_data_source_status_completion(self.fso_datasource_name):
            raise Exception("Could not complete Datasource scan.")

    @test_step
    def open_broken_permission_report(self):
        """Navigates to broken permission report and selects the client"""
        self.navigator.navigate_to_governance_apps()
        self.fso_helper.fso_obj.select_entitlement_manager()
        self.entitlement_manager.select_review()
        self.admin_console.wait_for_completion()
        self.entitlement_manager.load.load_project(
            self.machine_obj.client_object.client_name)

    @test_step
    def run_fix_permission_job_and_verify(self):
        """Runs a fix permission job on broken folder and validates if its fixed"""
        self.log.info("Checking for mismatched permissions folders list")
        self.entitlement_manager.broken.select_mismatched_permission()
        folders_to_review = self.entitlement_manager.broken.get_folder_to_review_count()
        if folders_to_review == 0:
            self.log.info("No folders found with mismatched permissions")
            raise Exception("No folders found with mismatched permissions")
        self.log.info(f"Folder to review count found on UI is : {folders_to_review}")
        self.log.info(f"Fixing the broken permissions on folder {self.broken_folder}")
        self.entitlement_manager.broken.run_fix_permission_job(self.broken_folder)
        self.log.info("Sleeping for 30 seconds")
        time.sleep(30)
        self.entitlement_manager.broken.refresh_report()
        folders_to_review = self.entitlement_manager.broken.get_folder_to_review_count()
        if folders_to_review != 0:
            self.log.info("Broken folders still found on the report")
            raise Exception("Fix permissions job failed to fix permissions")
        self.log.info(f"Folder to review count found on UI is : {folders_to_review}")
        self.log.info("Permissions on broken folder were fixed successfully. Passing the test")

    @test_step
    def validate_permissions_on_filer(self):
        """Verifies if the broken permissions and inheritance was fixed on the windows filer or not"""
        fixed_permissions: dict = self.activate_utils.get_access_control_list(
            path=self.broken_folder_unc,
            target_machine_name=self.machine_name)
        if fixed_permissions != self.original_permissions:
            self.log.info("Broken folders still found on the file system")
            raise Exception("Fix permissions job failed to fix permissions")
        self.log.info("Broken permissions fixed successfully")
        fixed_inheritance_permissions: dict = self.activate_utils.get_access_control_list(
            path=self.disabled_inheritance_unc,
            target_machine_name=self.machine_name
        )
        if fixed_inheritance_permissions != self.original_permissions_inheritance:
            self.log.info("Disabled inheritance folders still found on the file system")
            raise Exception("Fix permissions job failed to fix permissions")
        self.log.info("Inheritance permissions fixed successfully")

    def run(self):
        """Run function of this test case"""
        self.initialize_browser()
        self.cleanup()
        self.create_inheritance_disabled_folder()
        self.create_broken_permission_folder()
        self.create_plan()
        self.create_fso_client()
        self.wait_for_crawl_to_complete()
        self.open_broken_permission_report()
        self.run_fix_permission_job_and_verify()
        self.validate_permissions_on_filer()

    def tear_down(self):
        """Tear down function of this test case"""
        self.cleanup()
        self.browser.close()
