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

    run()           --  run function of this test case
"""

import dynamicindex.utils.constants as cs
from AutomationUtils.constants import AUTOMATION_BIN_PATH
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.GovernanceAppsPages.EntitlementManager import EntitlementManager

from Web.AdminConsole.GovernanceAppsPages.FileStorageOptimization import FileStorageOptimization

from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.Helper.FSOHelper import FSO
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from dynamicindex.utils.activateutils import ActivateUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of GDPR Feature"""
    test_step = TestStep()
    activate_utils = None
    utils = None

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Test case to cover revert permission in " \
                    "Entitlement Manager from AdminConsole"
        self.tc_inputs = {
            "MetadataDatabasePath": None,
            "HostNameToAnalyze": None,
            "FileServerDirectoryPath": None,
            "FileServerUserName": None,
            "FileServerPassword": None,
            "AccessNode": None,
            "IndexServerName": None,
            "NameServerAsset": None,
            "FileToBeModified": None,
            "ActiveDirectoryUserName": None
        }
        # Test Case constants
        self.inventory_name = None
        self.fs_data_source_prefix = "entitlement"
        self.plan_name = None
        self.file_server_display_name = None
        self.country_name = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.entitlement_manager = None
        self.app = None
        self.gdpr_base = None
        self.explict_wait = None
        self.test_case_error = None
        self.explict_wait = 1 * 60
        self.fso_helper = None

        self.fso_obj = None

        self.metadata_database = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.activate_utils = ActivateUtils()
            self.file_server_display_name = f"{self.fs_data_source_prefix}_test_file_server_fso"
            self.inventory_name = f"{self.id}_inventory_fso"
            self.plan_name = f"{self.id}_plan_fso"
            self.country_name = cs.USA_COUNTRY_NAME
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login()
            self.navigator = self.admin_console.navigator
            self.entitlement_manager = EntitlementManager(self.admin_console)
            self.app = GovernanceApps(self.admin_console)
            self.gdpr_base = GDPR(self.admin_console, self.commcell, self.csdb)

            self.fso_obj = FileStorageOptimization(self.admin_console)

            self.fso_helper = FSO(self.admin_console, self.commcell)
            self.metadata_database = "{}\\{}".format(AUTOMATION_BIN_PATH, self.tcinputs[
                "MetadataDatabasePath"])
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_inventory(self):
        """
        Create Inventory With Given Name server
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_inventory_manager()
        self.gdpr_base.inventory_details_obj.add_inventory(
            self.inventory_name, self.tcinputs['IndexServerName'])
        self.gdpr_base.inventory_details_obj.add_asset_name_server(
            self.tcinputs['NameServerAsset'])
        if not self.gdpr_base.inventory_details_obj.wait_for_asset_status_completion(
                self.tcinputs['NameServerAsset']):
            raise CVTestStepFailure("Could not complete Asset Scan")

    @test_step
    def create_plan(self):
        """
        Create Data Classification Plan
        """
        self.navigator.navigate_to_plan()
        self.gdpr_base.plans_obj.create_data_classification_plan(
            self.plan_name, self.tcinputs['IndexServerName'],
            None,
            content_search=False, content_analysis=False, target_app='fso')

    @test_step
    def create_fso_client(self):
        """acCreate FSO client """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.add_client(
            self.inventory_name, self.plan_name
        )

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.fso_helper.fso_cleanup(
            self.file_server_display_name,
            self.file_server_display_name,
            pseudo_client_name=self.file_server_display_name)
        self.gdpr_base.cleanup(inventory_name=self.inventory_name,
                               plan_name=self.plan_name)

    @test_step
    def select_fso_project(self):
        """
            Select FSO project from entitlement manager
        """
        self.navigator.navigate_to_governance_apps()
        self.app.select_entitlement_manager()
        self.entitlement_manager.load.load_project([self.file_server_display_name])

    @test_step
    def browse_specific_file(self, file_name):
        """
            Browse to specific file in entitlement manager
            Args :
                file_name(str) - file to browse
        """
        self.entitlement_manager.browse.expand_tree()
        self.entitlement_manager.browse.read_nodes_permissions(file_name)

    @test_step
    def add_new_user_assign_permission(self, user_name):
        """
         Add new user and assign permission to a file
        Args :
                user_name(str) - new user
        Raises:
                if user can not be assigned permissions on a file
        """
        if not self.entitlement_manager.action.perform_permission_change(user_name):
            raise Exception("Permission can not be assigned to [{}]".format(user_name))

    def get_file_name(self, current):
        """
        Get current File Name
        Args :
            current(str) - current file
        Returns :
            str - file_name
        """
        return current[self.entitlement_manager.constants.FILE_NAME]

    def get_users_permission(self, current):
        """
       Get current File users and attached permissions
        Args :
            current(str) - current file
        Returns :
            dict() - user to permission mapping
        """
        user_permission_map = {}
        for key in current.keys():
            if key is not self.entitlement_manager.constants.FILE_NAME:
                user_permission_map[key] = current[key]
        return user_permission_map

    def run(self):
        try:
            self.init_tc()
            user_name = self.tcinputs["ActiveDirectoryUserName"]
            file_name = self.tcinputs["FileToBeModified"]
            self.activate_utils.create_fso_metadata_db(self.tcinputs["FileServerDirectoryPath"],
                                                       self.metadata_database,
                                                       None, True)
            self.perform_cleanup()
            self.create_inventory()
            self.create_plan()
            self.create_fso_client()
            self.fso_helper.test_data_path = self.tcinputs['FileServerDirectoryPath']
            self.gdpr_base.file_server_lookup_obj.add_file_server(
                self.tcinputs['HostNameToAnalyze'], 'Host name',
                self.file_server_display_name, self.country_name,
                self.tcinputs['FileServerDirectoryPath'],
                username=self.tcinputs['FileServerUserName'],
                password=self.tcinputs['FileServerPassword'],
                agent_installed=False,
                access_node=self.tcinputs['AccessNode'])

            self.fso_obj.fso_data_source_details_page(
                self.file_server_display_name,
                self.file_server_display_name
            )

            self.fso_helper.fso_obj.select_details_action(self.file_server_display_name)
            self.fso_helper.fso_client_details.select_details_action(self.file_server_display_name)

            if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.file_server_display_name):
                raise Exception("Could not complete datasource scan.")

            import json
            num_mismatched = 0
            self.navigator.navigate_to_governance_apps()
            self.select_fso_project()
            self.browse_specific_file(file_name)
            old_permissions_list = self.entitlement_manager.browse.all_permissions
            self.log.info("Before {}".format(json.dumps(old_permissions_list)))
            self.add_new_user_assign_permission(user_name)
            self.entitlement_manager.browse.all_permissions = []
            self.select_fso_project()
            self.browse_specific_file(file_name)
            new_permissions_list = self.entitlement_manager.browse.all_permissions
            self.log.info("After {}".format(json.dumps(new_permissions_list)))
            if not self.entitlement_manager.action.revert_permission_to_point("admin"):
                raise Exception("Revert operation job failed.")
            self.log.info(
                "Total number of files [{}] to compare".format(len(old_permissions_list)))
            if len(old_permissions_list) > 0:
                for current in old_permissions_list:
                    try:
                        file_name = self.get_file_name(current)
                        permissions_ui = self.get_users_permission(current)
                        permissions_source = self.activate_utils. \
                            read_formatted_acl_from_database(file_name,
                                                             self.metadata_database)
                        if len(permissions_source['result']) > 0:
                            permissions_source = permissions_source["result"][0][
                                "FILE_PERMISSION_READABLE"]
                        if not self.fso_helper.verify_permission(permissions_ui,
                                                                 json.loads(
                                                                     permissions_source)):
                            num_mismatched = num_mismatched + 1
                            self.log.error(
                                "Total number of mismatch [{}]".format(num_mismatched))
                    except Exception as e:
                        self.log.error(e)

                    if num_mismatched > 0:
                        self.test_case_error = \
                            "There are [{}] files/folders for which permissions did not match". \
                                format(num_mismatched)
            self.perform_cleanup()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
