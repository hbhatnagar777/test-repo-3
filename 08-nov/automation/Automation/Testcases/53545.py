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

import time
import random

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):
    """Class for executing GDPR add, edit, disable and delete custom entities (
    regex, derived and keyword based); verify with crawl
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """GDPR - Entity Manager - add, edit, disable and delete
                    custom entities (regex, derived and keyword based); verify with crawl"""
        self.show_to_user = False
        self.tcinputs = {
            "UserName": None,
            "Password": None,
            "AccessNode": None,
            "HostNameToAnalyze": None,
            "FileServerDirectoryPath": None,
            "FileServerUserName": None,
            "FileServerPassword": None,
            "TestDataSQLiteDBPath": None,
            "inventory_name": None,
            "plan_name": None
        }
        # Test Case constants
        self.entities_list = None
        self.project_name = None
        self.file_server_display_name = None
        self.country_name = None
        self.browser = None
        self.admin_console = None

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing '%s' testcase" % str(self.id))

            # Test Case constants
            self.project_name = '%s_project' % self.id
            self.file_server_display_name = '%s_file_server' % self.id
            self.country_name = 'United States'
            self.entities_list = []
            wait_time = 2 * 60

            self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.tcinputs['UserName'],
                                              password=self.tcinputs['Password'])
            self.admin_console.login(username=self.tcinputs['UserName'],
                                     password=self.tcinputs['Password'])
            self.log.info("Login completed successfully.")

            gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
            gdpr_obj.create_sqlite_db_connection(
                self.tcinputs['TestDataSQLiteDBPath']
            )
            gdpr_obj.testdata_path = self.tcinputs['FileServerDirectoryPath']

            gdpr_obj.data_source_name = self.file_server_display_name

            self.log.info("Get custom entities list from SQlite DB")
            self.entities_list = gdpr_obj.db_get_custom_entity_list()
            gdpr_obj.entities_list = self.entities_list
            # *************************************
            # Clean up Code before execution begins
            # *************************************
            gdpr_obj.cleanup(
                self.project_name,
                pseudo_client_name=self.file_server_display_name)
            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_entity_manager()

            for entity_name in self.entities_list:
                if gdpr_obj.entity_manager_obj.check_if_activate_entity_exists(entity_name):
                    gdpr_obj.entity_manager_obj.entity_action(entity_name, action="Delete")

            self.log.info(
                "Deselect entities in the Plan %s" %
                self.tcinputs['plan_name'])
            self.admin_console.navigator.navigate_to_plan()
            gdpr_obj.plans_obj.select_plan(self.tcinputs['plan_name'])
            gdpr_obj.plans_obj.deselect_entities_in_data_classification_plan(
                self.tcinputs['plan_name'])
            # *******************
            # Clean up Code ends
            # *******************
            self.log.info("Navigate to Entity Manager")

            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_entity_manager()

            self.log.info("Beginning to add custom entities")
            for entity in self.entities_list:
                entity_parameters_dict = gdpr_obj.db_get_custom_entity_parameters(
                    entity)
                self.log.info(
                    "Parameters Dictionary obtained is: '{0}'".format(entity_parameters_dict))
                raw_regex = entity_parameters_dict["python_regex"]
                self.log.info("Regex is : %s" % raw_regex)
                gdpr_obj.entity_manager_obj.add_custom_entity(
                    entity_parameters_dict["entity_name"],
                    entity_parameters_dict["sensitivity"],
                    raw_regex,
                    parent_entity=entity_parameters_dict["parent_entity"],
                    keywords=entity_parameters_dict["keywords"])

            self.log.info(
                "Edit existing plan '{0}' and add entities '{1}' to it".format(
                    self.tcinputs['plan_name'], self.entities_list))
            self.admin_console.navigator.navigate_to_plan()
            gdpr_obj.plans_obj.select_plan(self.tcinputs['plan_name'])
            gdpr_obj.plans_obj.edit_data_classification_plan(
                self.tcinputs['plan_name'], self.entities_list)

            self.log.info("About to add project: %s" % self.project_name)
            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
            gdpr_obj.file_server_lookup_obj.add_project(
                self.project_name,
                self.tcinputs['plan_name'])

            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
            gdpr_obj.file_server_lookup_obj.navigate_to_project_details(
                self.project_name)

            self.log.info(
                "About to add data source: %s" %
                self.file_server_display_name)
            gdpr_obj.file_server_lookup_obj.select_add_data_source()
            gdpr_obj.file_server_lookup_obj.add_file_server(
                self.tcinputs['HostNameToAnalyze'], 'Host name',
                self.file_server_display_name, self.country_name,
                self.tcinputs['FileServerDirectoryPath'],
                username=self.tcinputs['FileServerUserName'],
                password=self.tcinputs['FileServerPassword'],
                access_node=self.tcinputs['AccessNode'])
            if not gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.file_server_display_name):
                raise Exception("Could not complete Data Source Scan")
            self.log.info("Sleeping for: '%d' seconds" % wait_time)
            time.sleep(wait_time)

            gdpr_obj.file_server_lookup_obj.select_data_source(
                self.file_server_display_name)

            self.log.info(
                "Beginning to verify discover and review pages after initial crawl")
            gdpr_obj.verify_data_source_discover()
            gdpr_obj.data_source_discover_obj.select_review()
            gdpr_obj.verify_data_source_review(unique=False)

            self.log.info("Beginning edit and disable custom entities")
            random_num_list = random.sample(range(len(self.entities_list)), 3)
            random_num1 = random_num_list[0]
            random_num2 = random_num_list[1]
            random_num3 = random_num_list[2]

            # 'old_entity' name will be preserved
            old_entity = self.entities_list[random_num1]
            self.log.info("Entity to be edited is: %s" % old_entity)
            # 'new_entity' parameters will be used with 'old_entity' name
            new_entity = self.entities_list[random_num2]
            self.log.info(
                "Entity whose parameters will be used is: %s" %
                new_entity)

            disable_entities_list = []
            disable_entities_list.append(self.entities_list[random_num3])
            self.log.info(
                "disable_entities_list is {0}".format(disable_entities_list))
            self.log.info(
                "Original entities list is {0}. Make sure this is still the same".format(
                    self.entities_list))
            gdpr_obj.disable_entities_list = disable_entities_list
            self.log.info(
                "List of Entities to be disabled is {0}".format(
                    gdpr_obj.disable_entities_list))
            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_entity_manager()
            for entity in gdpr_obj.disable_entities_list:
                if gdpr_obj.entity_manager_obj.check_if_entity_is_enabled(
                        entity):
                    gdpr_obj.entity_manager_obj.entity_action(
                        entity, 'Disable')

            self.log.info(
                "Creating a dictionary of old_entity and new_entity pairs")
            entities_replace_dict = {}
            entities_replace_dict[old_entity] = new_entity
            gdpr_obj.entities_replace_dict = entities_replace_dict
            self.log.info(
                "Dictionary of old and new entity pairs is: '{0}'".format(
                    gdpr_obj.entities_replace_dict))

            for key, value in gdpr_obj.entities_replace_dict.items():
                old_entity_parameters_dict = gdpr_obj.db_get_custom_entity_parameters(
                    key)
                if old_entity_parameters_dict["parent_entity"] is not None:
                    old_entity_type = 'derived'
                else:
                    old_entity_type = 'regex_based'
                new_entity_parameters_dict = gdpr_obj.db_get_custom_entity_parameters(
                    value)
                raw_regex = new_entity_parameters_dict["python_regex"]
                self.log.info("Regex is : %s" % raw_regex)
                self.admin_console.navigator.navigate_to_governance_apps()
                gdpr_obj.inventory_details_obj.select_entity_manager()
                gdpr_obj.entity_manager_obj.edit_entity(
                    key,
                    old_entity_type,
                    sensitivity=new_entity_parameters_dict["sensitivity"],
                    python_regex=raw_regex,
                    parent_entity=new_entity_parameters_dict["parent_entity"],
                    keywords=new_entity_parameters_dict["keywords"])

            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
            gdpr_obj.file_server_lookup_obj.navigate_to_project_details(
                self.project_name)

            gdpr_obj.file_server_lookup_obj.select_data_source(
                self.file_server_display_name)

            self.log.info(
                "Starting a full re-crawl of the datasource %s" %
                self.file_server_display_name)
            gdpr_obj.data_source_discover_obj.select_details()
            gdpr_obj.data_source_discover_obj.start_data_collection_job('full')
            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
            gdpr_obj.file_server_lookup_obj.navigate_to_project_details(
                self.project_name)
            if not gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.file_server_display_name):
                raise Exception("Could not complete Data Source Scan")

            gdpr_obj.file_server_lookup_obj.select_data_source(
                self.file_server_display_name)

            self.log.info(
                "Beginning to verify discover and review pages after re-crawl")
            gdpr_obj.verify_data_source_discover()
            gdpr_obj.data_source_discover_obj.select_review()
            gdpr_obj.verify_data_source_review(unique=False)

            # *************************
            # Clean up Code
            # *************************
            gdpr_obj.cleanup(
                self.project_name,
                pseudo_client_name=self.file_server_display_name)
            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_entity_manager()

            for entity_name in self.entities_list:
                gdpr_obj.entity_manager_obj.entity_action(
                    entity_name, action="Delete")

            self.log.info(
                "Deselect entities in the Plan %s" %
                self.tcinputs['plan_name'])
            self.admin_console.navigator.navigate_to_plan()
            gdpr_obj.plans_obj.select_plan(self.tcinputs['plan_name'])
            gdpr_obj.plans_obj.deselect_entities_in_data_classification_plan(
                self.tcinputs['plan_name'])

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            Browser.close_silently(self.browser)
