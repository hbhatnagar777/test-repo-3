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
import uuid
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Reports.utils import TestCaseUtils
from Web.AdminConsole.GovernanceAppsPages.ExchangeServerLookup import ExchangeServerLookup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from dynamicindex.utils.activateutils import ActivateUtils


class TestCase(CVTestCase):
    """Class For executing basic acceptance test of GDPR Feature"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = ("Basic Acceptance Test for Sensitive Data Analysis\
        using  Exchange Server as Data Source")

        self.product = self.products_list.CONTENTINDEXING
        self.feature = self.features_list.GDPR
        self.show_to_user = False
        self.activate_utils = ActivateUtils()
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyzer": None,
            "NameServerAsset": None,
            "HostNameToAnalyze": None,
            "ExchangeMailboxesAlias": None,
            "TestDataSQLiteDBPath": None,
            "ClientName": None,
            "AgentName": None,
            "BackupSetName": None,
            "SubclientName": None,
            "SensitiveMailAPI": None
        }
        # Test Case constants
        self.cleanup = False
        self.inventory_name = None
        self.plan_name = None
        self.entities_list = None
        self.project_name = None
        self.exchange_server_display_name = None
        self.country_name = None
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.gdpr_obj = None
        self.build_id = None
        self.build_id = uuid.uuid1().hex
        self.build_id = self.build_id[0:8]
        self.navigator = None
        self.mailboxes_smtp = None
        self.test_case_error = None
        self.wait_time = 2 * 60
        self.exchange_server_lookup = None
        self.entities_list = [
            'Email',
            'Credit card number',
            'IP address'
        ]
        self.entities_list_map = {
            "Email": "Email",
            "Credit card number": "Credit Card Number",
            "IP address": "IP Address"
        }

    def generate_sensitive_mails(self):
        """
        Generate Random Sensitive Mails
        :return:
        """
        self.activate_utils.mail_generate_and_send(self.tcinputs['ExchangeMailboxesAlias'],
                                                   self.tcinputs["SensitiveMailAPI"])

    def db_get_sensitive_mails_list(self):
        """
        Returns all the sensitive mails present in DB
        """
        data = self.entities_list_map
        temp_list = []
        e_list = self.entities_list
        for index, item in enumerate(e_list):
            temp_list.insert(index, data[item])

        query = f'SELECT Subject from Entity where\
         (not "{temp_list[0]}" is null'
        for entity in temp_list[1:]:
            query = query + f' or not "{entity}" is null'
        query = query + ') and Flag = 1'

        self.log.info(f"Executing Query {query}")
        result = self.gdpr_obj.sqlitedb.execute(query)
        sensitive_mails_subject_list = result.rows
        sensitive_mails_subject_list = [subject[0] for subject in sensitive_mails_subject_list]
        sensitive_mails_subject_list = sorted(sensitive_mails_subject_list, key=str.lower)
        self.log.info(f"Sensitive Mail Subject List {sensitive_mails_subject_list}")
        return sensitive_mails_subject_list

    def db_get_entities_exchange(self, subject, entities_list_map, entity_separator):
        """
        Get Entities From DAtabase
        """
        entities_dict = {}
        temp_list = []
        data = entities_list_map
        e_list = self.entities_list
        for index, item in enumerate(e_list):
            temp_list.insert(index, data[item])

        query = 'SELECT '
        for index, entity in enumerate(temp_list):
            query = query + f'"{entity}"'
            if index + 1 < len(temp_list):
                query = query + ','
        query = query + f' from Entity where Subject = "{subject}"'
        result = self.gdpr_obj.sqlitedb.execute(query)
        for index, entity in enumerate(result.columns):
            if result.rows[0][index] is not None:
                entities_dict[str(entity).lower()] = result.rows[0][index].split(entity_separator)
        self.log.info(f"Database Entities Dictionary for Subject {subject} is  {entities_dict}")
        return entities_dict

    def init_tc(self):
        """Initial Configuration For Testcase"""
        try:
            self.exchange_server_display_name = f'{self.id}_test_exchange_server_{self.build_id}'
            self.browser = BrowserFactory().create_browser_object()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login()
            self.navigator = self.admin_console.navigator
            self.exchange_server_lookup = ExchangeServerLookup(self.admin_console)
            self.gdpr_obj = GDPR(self.browser.driver, self.commcell, self.csdb)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def create_inventory(self):
        """
        Create Inventory With Given Nameserver
        """
        self.inventory_name = f'{self.id}_inventory_{self.build_id}'
        self.gdpr_obj.inventory_details_obj.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.add_inventory(
            self.inventory_name, self.tcinputs['IndexServerName'])

        self.gdpr_obj.inventory_details_obj.add_asset_name_server(
            self.tcinputs['NameServerAsset'])
        if not self.gdpr_obj.inventory_details_obj.wait_for_asset_status_completion(
                self.tcinputs['NameServerAsset']):
            raise CVTestStepFailure("Could not complete Asset Scan")

    @test_step
    def create_plan(self):
        """
        Create Data Classification Plan
        """
        self.plan_name = f'{self.id}_plan_{self.build_id}'
        self.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            self.plan_name, self.tcinputs['IndexServerName'],
            self.tcinputs['ContentAnalyzer'], self.entities_list)

    @test_step
    def create_sda_project(self):
        """
        Create SDA Project And Run Analysis
        """
        self.project_name = f'{self.id}_project_{self.build_id}'
        self.country_name = 'United States'
        self.gdpr_obj.data_source_name = self.exchange_server_display_name
        self.gdpr_obj.entities_list = self.entities_list
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name, self.inventory_name
        )

    @test_step
    def add_exchange_datasource(self):
        """
        Add Exchange DataSource
        """
        self.exchange_server_lookup.add_data_source.select_add_data_source()
        self.exchange_server_lookup.select_exchange_obj.\
            select_exchange_host(self.tcinputs["HostNameToAnalyze"], "Client name")
        self.exchange_server_lookup.configure_exchange_obj.\
            configure_exchange_host(self.exchange_server_display_name, self.country_name,
                                    list_of_mailboxes=self.mailboxes_smtp)

    @test_step
    def review_exchange_datasource(self):
        """
        Review Added Exchange DataSource
        """
        self.gdpr_obj.verify_data_source_name()
        db_sensitive_mail_subject_list = self.db_get_sensitive_mails_list()
        self.log.info("Verifying Sensitive Data for Each mail according to test data")
        for subject in db_sensitive_mail_subject_list:
            self.exchange_server_lookup.review_exchange_data_source.select_mail(subject)
            self.log.info(f"Verifying Sensitivity for mail {subject}")

            db_entities_dict = self.db_get_entities_exchange(subject, self.entities_list_map, "****")
            entities_dict = self.gdpr_obj.data_source_review_obj.get_entities()
            for key, value in entities_dict.items():
                for key1, value1 in self.entities_list_map.items():
                    if str(key).lower() == str(key1).lower():
                        entities_dict.pop(key)
                        entities_dict[value1.lower()] = value

            if db_entities_dict != entities_dict:
                self.log.info(f"Entities Value Mismatched For Subject {subject}")
                self.test_case_error = "Entities Value Mismatched"
            else:
                self.log.info(f'Entity Values matched for Subject {subject}')
            self.gdpr_obj.data_source_review_obj.close_file_preview()

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.gdpr_obj.cleanup(self.project_name,
                              self.inventory_name,
                              self.plan_name,
                              pseudo_client_name=self.exchange_server_display_name)

    def run(self):
        """Run Function For Test Case Execution"""

        try:
            self.init_tc()
            self.generate_sensitive_mails()
            self.mailboxes_smtp = self.activate_utils.run_backup_mailbox_job(
                self.commcell, self.tcinputs['ClientName'],
                self.tcinputs['AgentName'], self.tcinputs['BackupSetName'],
                self.tcinputs['SubclientName'], self.tcinputs['ExchangeMailboxesAlias'])

            self.create_inventory()
            self.create_plan()
            self.create_sda_project()
            self.gdpr_obj.create_sqlite_db_connection(self.tcinputs['TestDataSQLiteDBPath'])
            self.add_exchange_datasource()

            if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                    self.exchange_server_display_name):
                raise Exception("Could Not Complete Data Source Scan")
            self.log.info(f"Sleeping for {str(self.wait_time)} Seconds")
            time.sleep(self.wait_time)

            self.gdpr_obj.file_server_lookup_obj.select_data_source(
                self.exchange_server_display_name)
            self.gdpr_obj.data_source_discover_obj.select_review()
            self.review_exchange_datasource()
            if self.test_case_error is not None:
                raise CVTestStepFailure(self.test_case_error)
            self.cleanup = True
            self.perform_cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)
            if not self.cleanup and \
                    self.project_name is not None or\
                    self.plan_name is not None or\
                    self.inventory_name is not None:
                self.perform_cleanup()
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
