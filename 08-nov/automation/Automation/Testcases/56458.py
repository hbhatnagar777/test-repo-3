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
from Application.Exchange.SolrSearchHelper import SolrSearchHelper
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.GovernanceAppsPages.CaseManager import CaseManager
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.Components.table import Table


class TestCase(CVTestCase):
    """Class for Verification of search within Case of Case Manager"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verification of search within Case of Case Manager"
        self.data_collection = 'Continuous'
        self.data_type = 'Exchange mailbox'
        self.is_emails_num = 0
        self.case_name = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.activate = None
        self.case_manager = None
        self.jobs = None
        self.index_copy_job_id = None
        self.tcinputs = {
            "CaseName": None,
            "DCPlan": None,
            "ServerPlan": None,
            "Custodians": None,
            "Keyword": None,
            "SearchKeyword": None,
            "SQLServerName": None,
            "SQLUsername": None,
            "SQLPassword": None
        }
        self.mssql = None
        self.emails_num = None
        self.table = None
        self.solr_search_obj = None
        self.solr_helper_obj = None
        self.ex_object = None
        self.custodians = None
        self.keyword_search = None
        self.is_keyword_search = None

    def init_tc(self):
        """Initial configuration for the test case"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode['commcell']['loginUsername'],
                self.inputJSONnode['commcell']['loginPassword'])

            self.activate = GovernanceApps(self.admin_console)
            self.case_manager = CaseManager(self.admin_console)
            self.jobs = Jobs(self.admin_console)
            self.ex_object = ExchangeMailbox(self)
            self.solr_search_obj = SolrSearchHelper(self)
            self.table = Table(self.admin_console)

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()

            self.case_name = self.tcinputs['CaseName'] + str(int(time.time()))
            self.custodians = self.tcinputs['Custodians']

            server_name = self.tcinputs['SQLServerName']
            user = self.tcinputs['SQLUsername']
            password = self.tcinputs['SQLPassword']
            self.mssql = MSSQL(
                server_name,
                user,
                password,
                'CommServ',
                as_dict=False)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def create_case_manager_client(self):
        """Enter basic details, custodians, keyword and save it"""
        try:
            self.case_manager.select_add_case()
            self.case_manager.enter_case_details(
                self.case_name,
                self.data_type,
                self.data_collection,
                self.custodians,
                self.tcinputs['DCPlan'],
                self.tcinputs['ServerPlan'],
                self.tcinputs['Keyword']
            )
            self.log.info('Case Added')
        except Exception:
            raise CVTestStepFailure("Error entering details")

    @test_step
    def verify_job_complete(self):
        """Verifying whether the Case Manager Index Copy Job has been submitted"""
        try:
            self.case_manager.submit_collection_job()
            self.index_copy_job_id = str(
                self.case_manager.get_index_copy_job_id())
            self.index_copy_details = self.jobs.job_completion(self.index_copy_job_id)
            if not self.index_copy_details['Status'] == 'Completed':
                exp = "Indexcopy job  not completed successfully"
                raise CVTestStepFailure(exp)
        except BaseException:
            raise CVTestStepFailure(
                "Error Verifying whether job has been submitted")

    @test_step
    def verify_case_manager_page(self):
        """Verifying that the case with the given name is listed in 'Case Manager' page"""
        try:
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            if self.table.is_entity_present_in_column('Name', self.case_name):
                self.log.info(
                    'VERIFIED: Case with given name listed in Case Manager page')
            else:
                raise CVTestStepFailure(
                    "Case with given name not listed in Case Manager page")
        except BaseException:
            raise CVTestStepFailure(
                "Error Verifying whether case listed in Case Manager page")

    @test_step
    def perform_ui_keyword_search(self):
        """Perform Keyword Search on the UI"""

        self.case_manager.select_case(self.case_name)
        self.case_manager.open_search_tab()
        self.keyword_search = self.case_manager.get_keyword_email_count(
            self.tcinputs['SearchKeyword'] + '\n')
        self.log.info('Identified number of emails with keyword "%s" as %s',
                      self.tcinputs['SearchKeyword'], self.keyword_search)

    @test_step
    def perform_solr_keyword_search(self):
        """Perform keyword search on Solr"""
        dest_app_id = self.solr_search_obj.get_app_id(
            self.case_name + '-definition',
            'destination',
            self.inputJSONnode['commcell']['loginUsername'],
            self.mssql)
        app_id = '(' + ','.join(dest_app_id) + ')'
        url, cloud_id = self.solr_search_obj.get_ci_server_url(
            self.mssql, app_id)
        self.ex_object.index_server = self.solr_search_obj.get_index_server_name(
            cloud_id[0])
        query_url = url[0]['ciServer'] + '/select?'
        self.solr_helper_obj = SolrHelper(self.ex_object, query_url)
        solr_results = self.solr_helper_obj.create_url_and_get_response(
            {'keyword': self.tcinputs['SearchKeyword']})
        self.is_keyword_search = self.solr_helper_obj.get_count_from_json(
            solr_results.content)
        self.log.info('Solr query return %s items for keyword "%s"',
                      self.is_keyword_search, self.tcinputs['SearchKeyword'])

    @test_step
    def validate_keyword_search(self):
        """Validates keyword search"""
        if self.keyword_search != self.is_keyword_search:
            raise CVTestStepFailure(
                'Email count mismatch during keyword search')

    def run(self):
        """
        Testcase execution starts from here
        """
        try:
            self.init_tc()
            self.create_case_manager_client()
            self.verify_job_complete()
            self.verify_case_manager_page()
            self.perform_ui_keyword_search()
            self.perform_solr_keyword_search()
            self.validate_keyword_search()
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            self.case_manager.delete_case(self.case_name)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
