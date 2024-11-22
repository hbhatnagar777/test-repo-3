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

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):
    """Class for executing GDPR editing system entities and verify with recrawl"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "GDPR - Entity Manager - edit system entity and verify with recrawl"
        self.show_to_user = False
        self.tcinputs = {
            "UserName": None,
            "Password": None,
            "IndexServerName": None,
            "AccessNode": None,
            "ContentAnalyzer": None,
            "HostNameToAnalyze": None,
            "FileServerDirectoryPath": None,
            "FileServerUserName": None,
            "FileServerPassword": None,
            "TestDataSQLiteDBPath": None,
            "inventory_name": None,
        }
        # Test Case constants
        self.plan_name = None
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
            self.plan_name = '%s_plan' % self.id
            self.project_name = '%s_project' % self.id
            self.file_server_display_name = '%s_file_server' % self.id
            self.country_name = 'United States'
            self.entities_list = ['French INSEE']
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
            gdpr_obj.entities_list = self.entities_list

            # *************************************
            # Clean up Code before execution begins
            # *************************************
            gdpr_obj.cleanup(
                self.project_name,
                plan_name=self.plan_name,
                pseudo_client_name=self.file_server_display_name)
            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_entity_manager()
            gdpr_obj.entity_manager_obj.edit_entity(
                self.entities_list[0],
                'system',
                sensitivity='High',
                keywords=[
                    "Personal",
                    "National",
                    "henkilötunnus",
                    "personbeteckning",
                    "numéro d'inscription au répertoire",
                    "numéro de sécurité sociale"])

            # *******************
            # Clean up Code ends
            # *******************

            self.log.info("About to add plan: %s" % self.plan_name)
            self.admin_console.navigator.navigate_to_plan()
            gdpr_obj.plans_obj.create_data_classification_plan(
                self.plan_name, self.tcinputs['IndexServerName'],
                self.tcinputs['ContentAnalyzer'], self.entities_list)

            self.log.info("About to add project: %s" % self.project_name)
            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
            gdpr_obj.file_server_lookup_obj.add_project(
                self.project_name, self.plan_name, self.tcinputs['inventory_name'])

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

            self.log.info("Beginning to edit system entity")
            self.log.info(
                "Entity whose parameters will be edited is: {}".format(
                    self.entities_list[0]))

            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_entity_manager()
            gdpr_obj.entity_manager_obj.edit_entity(
                self.entities_list[0],
                'system',
                sensitivity='Moderate',  # original value is High
                keywords=["FrenchINSEEafterEdit"])

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
            self.log.info("Sleeping for: '%d' seconds" % wait_time)

            time.sleep(wait_time)

            self.log.info(
                "Creating a dictionary of actual entity and edited entity pairs.")
            entities_replace_dict = {}
            entities_replace_dict['French INSEE'] = 'French INSEE Edit'
            gdpr_obj.entities_replace_dict = entities_replace_dict
            self.log.info(
                "Dictionary of actual entity and edited entity pairs is: '{0}'".format(
                    gdpr_obj.entities_replace_dict))

            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
            gdpr_obj.file_server_lookup_obj.navigate_to_project_details(
                self.project_name)
            gdpr_obj.file_server_lookup_obj.select_data_source(
                self.file_server_display_name)

            self.log.info(
                "Beginning to verify discover and review pages after re-crawl")
            gdpr_obj.verify_data_source_discover()
            gdpr_obj.data_source_discover_obj.select_review()
            gdpr_obj.verify_data_source_review(
                unique=False, edit_system_entity=True)

            # *************************
            # Clean up Code
            # *************************
            gdpr_obj.cleanup(
                self.project_name,
                plan_name=self.plan_name,
                pseudo_client_name=self.file_server_display_name)
            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_entity_manager()
            gdpr_obj.entity_manager_obj.edit_entity(
                self.entities_list[0],
                'system',
                sensitivity='High',
                keywords=[
                    "Personal",
                    "National",
                    "henkilötunnus",
                    "personbeteckning",
                    "numéro d'inscription au répertoire",
                    "numéro de sécurité sociale"])
            # *******************
            # Clean up Code ends
            # *******************

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            Browser.close_silently(self.browser)
