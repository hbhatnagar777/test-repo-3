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
    setup()         --  sets up the variables required for running the testcase
    run()           --  run function of this test case
    teardown()      --  tears down the things created for running the testcase
"""
import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole, Browser
from Web.AdminConsole.Applications.ExchangeAppHelper import ExchangeAppHelper
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing SMTP_Automation: ContentStore Mailbox creation from command center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = "SMTP_Automation: ContentStore Mailbox creation from command center"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.indexservercloud = None
        self.accessnodes = None
        self.show_to_user = False
        self.tcinputs = {
            "IndexServer": None,
            "ServerPlan": None,
            "ProxyServers": None,
            "SMTPDisplayName": None,
            "SMTPEmailAddress": None,
            "ExchangePlan": None,
            "SMTPServerList": None,
            "SMTPCacheLocList": None
        }
        # Test Case constants
        self.browser = None
        self.app_name = None
        self.test_case_error = None
        self.app = None
        self.navigator = None
        self.admin_console = None
        self.exch_helper_obj = None
        self._utility = None
        self.smtp_display_name = None
        self.smtp_address = None
        self.serverplan = None
        self.exchange_plan = None
        self.smtpserver_list = None
        self.cache_loc_list = None
        self.ip_addresses = None
        self.certificate_file_loc = None
        self.certificate_file_pwd = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            # Test Case constants
            self.app_name = str(self.id) + "_app"
            self.indexservercloud = self.tcinputs['IndexServer']
            self.serverplan = self.tcinputs['ServerPlan']
            self.accessnodes = self.tcinputs['ProxyServers']
            self.smtp_display_name = self.tcinputs['SMTPDisplayName']
            self.smtp_address = self.tcinputs['SMTPEmailAddress']
            self.exchange_plan = self.tcinputs['ExchangePlan']
            self.smtpserver_list = self.tcinputs['SMTPServerList']
            self.cache_loc_list = self.tcinputs['SMTPCacheLocList']
            self.ip_addresses = self.tcinputs['WhiteListIpAddresses']
            self.certificate_file_loc = self.tcinputs['CertificateFileLocation']
            self.certificate_file_pwd = self.tcinputs['CertificateFilePassword']
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open(maximize=True)
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_exchange()
            self.exch_helper_obj = ExchangeAppHelper(self.admin_console)
            self._utility = OptionsSelector(self.commcell)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_smtp_journal_client(self):
        """
        Create Exchange- SMTP Journaling client
        """
        self.exch_helper_obj.create_smtp_journaling_client \
            (self.app_name, self.serverplan, self.indexservercloud, self.accessnodes)

    @test_step
    def verify_client_in_exchange_page(self):
        """
        Verify that the created client appears in the list of Exchange clients
        """
        self.navigator.navigate_to_exchange()
        if not self.exch_helper_obj.isexchange_client_listed(self.app_name):
            raise CVTestStepFailure \
                ("SMTP Journal Client is not listed in Exchange Clients page")

    @test_step
    def verify_mailbox_in_app(self):
        """
        Verify that mailbox added is listed in the app
        """
        if not self.exch_helper_obj.ismailbox_listed_in_app(self.smtp_display_name):
            raise CVTestStepFailure("SMTP Mailbox created is not listed in Client page")

    @test_step
    def add_mailbox_to_smtp_client(self):
        """
        Add mailbox to smtp client
        """
        mailbox_attributes = {"Display Name": self.smtp_display_name,
                              "SMTP Address": self.smtp_address,
                              "Exchange Plan": self.exchange_plan,
                              "SMTP Servers": self.smtpserver_list,
                              "Cache Locations": self.cache_loc_list,
                              "IP addresses": self.ip_addresses,
                              "Certificate Location": self.certificate_file_loc,
                              "Certification Password": self.certificate_file_pwd}
        self.exch_helper_obj.add_smtp_mailbox(self.app_name, mailbox_attributes)

    @test_step
    def verify_client_association_with_plan(self):
        """
        Verify that client is associated with the plan
        """
        self.exch_helper_obj.is_client_associated_with_plan(self.app_name, self.serverplan)

    def run(self):
        try:
            self.init_tc()
            self.create_smtp_journal_client()
            self.verify_client_in_exchange_page()
            self.add_mailbox_to_smtp_client()
            self.verify_mailbox_in_app()
            time.sleep(5)
            self.verify_client_association_with_plan()
            self._utility.delete_client(self.app_name)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
