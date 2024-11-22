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
from AutomationUtils import idautils
from Web.Common.page_object import handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole

class TestCase(CVTestCase):
    """Class for executing GDPR Of NER With Backed up data Crawl"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "GDPR Of NER With Backed up data Crawl"
        self.show_to_user = False
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyzer": None,
            "NameServerAsset": None,
            "HostNameToAnalyze": None,
            "UserName": None,
            "Password": None,
            "FileServerLocalTestDataPath": None,
            "FileServerDirectoryPath": None,
            "TestDataSQLiteDBPath": None,
            "StoragePolicy": None
        }
        # Test Case constants
        self.inventory_name = None
        self.plan_name = None
        self.entities_list = None
        self.ner_entities_list = None
        self.project_name = None
        self.file_server_display_name = None
        self.country_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.browser = None
        self.admin_console = None

    def run(self):
        """Main function for test case execution"""
        log = self.log

        try:
            log.info("Started executing '%s' testcase" % str(self.id))

            # Test Case constants
            self.inventory_name = '%s_inventory' % self.id
            self.plan_name = '%s_plan' % self.id
            self.project_name = '%s_project' % self.id
            self.file_server_display_name = '%s_file_server' % self.id
            self.country_name = 'United States'
            self.entities_list = ['Person Name']
            self.ner_entities_list = ['Person Name']
            self.backupset_name = '%s_backupset' % self.id
            self.subclient_name = '%s_subclient' % self.id
            wait_time = 2 * 60

            log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.tcinputs['UserName'],
                                              password=self.tcinputs['Password'])
            self.admin_console.login(username=self.tcinputs['UserName'],
                                     password=self.tcinputs['Password'])
            log.info("Login completed successfully.")

            gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
            gdpr_obj.create_sqlite_db_connection(
                self.tcinputs['TestDataSQLiteDBPath']
            )
            gdpr_obj.testdata_path = self.tcinputs['FileServerDirectoryPath']
            gdpr_obj.entities_list = self.entities_list
            gdpr_obj.data_source_name = self.file_server_display_name

            gdpr_obj.cleanup(
                self.project_name,
                self.inventory_name,
                self.plan_name,
                delete_backupset_for_client=self.tcinputs['HostNameToAnalyze'],
                backupset_names_list=[self.backupset_name],
                pseudo_client_name=self.file_server_display_name)

            idautils_obj = idautils.CommonUtils(self.commcell)

            log.info('Creating backupset for client: "%s" under agent: "%s"'\
                     %(self.client.client_name, self.agent.agent_name))
            backupset_obj = self.agent.backupsets.add(self.backupset_name)
            log.info('Successfully created backupset: "%s"', backupset_obj.backupset_name)
            log.info('Creating subclient under this backupset now')
            subclient_obj = backupset_obj.subclients.add(
                self.subclient_name, self.tcinputs['StoragePolicy'])
            log.info('Successfully created subclient: "%s"', subclient_obj.subclient_name)
            subclient_obj.content = [self.tcinputs['FileServerLocalTestDataPath']]
            log.info('Successfully set subclient content: "%s"', subclient_obj.content)

            idautils_obj.subclient_backup(subclient_obj, "FULL")

            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_entity_manager()
            for entity_name in self.ner_entities_list:
                if not gdpr_obj.entity_manager_obj.check_if_entity_is_enabled(
                        entity_name):
                    gdpr_obj.entity_manager_obj.entity_action(
                        entity_name, action="Enable")

            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_inventory_manager()
            gdpr_obj.inventory_details_obj.add_inventory(
                self.inventory_name, self.tcinputs['IndexServerName'])

            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_inventory_manager()
            gdpr_obj.inventory_details_obj.navigate_to_inventory_details(
                self.inventory_name)

            gdpr_obj.inventory_details_obj.add_asset_name_server(
                self.tcinputs['NameServerAsset'])
            log.info("Sleeping for: '%d' seconds" % wait_time)
            time.sleep(wait_time)
            if not gdpr_obj.inventory_details_obj.wait_for_asset_status_completion(
                    self.tcinputs['NameServerAsset']):
                raise Exception("Could not complete Asset Scan")

            self.admin_console.navigator.navigate_to_plan()
            gdpr_obj.plans_obj.create_data_classification_plan(
                self.plan_name, self.tcinputs['IndexServerName'],
                self.tcinputs['ContentAnalyzer'], self.entities_list)

            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
            gdpr_obj.file_server_lookup_obj.add_project(
                self.project_name, self.plan_name)

            gdpr_obj.file_server_lookup_obj.select_add_data_source()
            gdpr_obj.file_server_lookup_obj.add_file_server(
                self.tcinputs['HostNameToAnalyze'], 'Host name',
                self.file_server_display_name, self.country_name,
                directory_path=self.tcinputs['FileServerLocalTestDataPath'],
                agent_installed=True, backup_data_import=True,
                inventory_name=self.inventory_name)
            log.info("Sleeping for: '%d' seconds" % wait_time)
            time.sleep(wait_time)
            if not gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.file_server_display_name, timeout=60):
                raise Exception("Could not complete Data Source Scan")
            log.info("Sleeping for: '%d' seconds" % wait_time)
            time.sleep(wait_time)

            gdpr_obj.file_server_lookup_obj.select_data_source(
                self.file_server_display_name)

            gdpr_obj.verify_data_source_discover(skip_total_files=True)
            gdpr_obj.data_source_discover_obj.select_review()
            gdpr_obj.verify_data_source_review(
                folder_path=self.tcinputs['FileServerLocalTestDataPath'],
                unique=False)

            # *************************
            # Clean up Code
            # *************************
            gdpr_obj.cleanup(
                self.project_name,
                self.inventory_name,
                self.plan_name,
                delete_backupset_for_client=self.tcinputs['HostNameToAnalyze'],
                backupset_names_list=[self.backupset_name],
                pseudo_client_name=self.file_server_display_name)
            self.admin_console.navigator.navigate_to_governance_apps()
            gdpr_obj.inventory_details_obj.select_entity_manager()
            for entity_name in self.ner_entities_list:
                if gdpr_obj.entity_manager_obj.check_if_entity_is_enabled(
                        entity_name):
                    gdpr_obj.entity_manager_obj.entity_action(
                        entity_name, action="Disable")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            Browser.close_silently(self.browser)
