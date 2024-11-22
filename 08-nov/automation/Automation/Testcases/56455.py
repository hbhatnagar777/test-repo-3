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
import datetime

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
from Web.AdminConsole.Components.table import Table, Rtable


class TestCase(CVTestCase):
    """Class for Verification of case creation from Case
    Manager page with 'One time only' data collection"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("Verification of case creation from Case Manager"
                     "page with 'One time only' data collection")
        self.data_collection = 'One time only'
        self.is_emails_num = 0
        self.current_time = int(time.time())
        self.delete_cases_older_than = 3
        self.case_name = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.activate = None
        self.case_manager = None
        self.tcinputs = {
            "CaseName": None,
            "DCPlan": None,
            "ServerPlan": None,
            "DataType": None,
            "Custodians": None,
            "Keyword": None,
            "SQLServerName": None,
            "SQLUsername": None,
            "SQLPassword": None,
            "SearchKeyword":None
        }
        self.mssql = None
        self.custodians_num = None
        self.emails_num = None
        self.solr_search_obj = None
        self.solr_helper_obj = None
        self.ex_object = None
        self.custodians = None
        self.keyword_search=None
        self.index_copy_details=None
        self.reference_copy_details=None
        self.content_indexing_details=None

    def init_tc(self):
        """Initial configuration for the test case"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open(maximize=True)
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode['commcell']['loginUsername'],
                self.inputJSONnode['commcell']['loginPassword'])

            self.activate = GovernanceApps(self.admin_console)
            self.case_manager = CaseManager(self.admin_console)
            self.ex_object = ExchangeMailbox(self)
            self.ex_object.cvoperations.client_name=self.client.client_name
            self.solr_search_obj = SolrSearchHelper(self)
            self.rtable = Rtable(self.admin_console)
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            self.case_name = self.tcinputs['CaseName'] + str(int(time.time()))
            self.custodians = self.tcinputs['Custodians']

            server_name = self.tcinputs['SQLServerName']
            user = self.tcinputs['SQLUsername']
            password = self.tcinputs['SQLPassword']
            self.keyword_search=self.tcinputs['SearchKeyword']
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
                self.tcinputs['DataType'],
                self.data_collection,
                self.custodians,
                self.tcinputs['DCPlan'],
                self.tcinputs['ServerPlan'],
                self.tcinputs['Keyword']
            )
            self.log.info('Case Added')
        except Exception:
            raise CVTestStepFailure(f"Error entering details")

    @test_step
    def verify_case_manager_page(self):
        """Verifying that the case with the given name is listed in 'Case Manager' page"""
        try:
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()

            if self.rtable.is_entity_present_in_column('Name', self.case_name):
                self.log.info(
                    'VERIFIED: Case with given name listed in Case Manager page')
            else:
                raise CVTestStepFailure(
                    "Case with given name not listed in Case Manager page")
        except BaseException:
            raise CVTestStepFailure(
                "Error Verifying whether case listed in Case Manager page")

    @test_step
    def get_no_of_custodians_and_emails(self):
        """Getting the number of custodians and emails """
        try:
            self.case_manager.select_case(self.case_name)
            self.custodians_num = self.case_manager.get_custodian_count(self.case_name)
            self.log.info(
                'Identified number of custodians as %s',
                self.custodians_num)
            self.case_manager.open_search_tab()
            self.case_manager.click_search_button()
            self.emails_num = int(self.rtable.get_total_rows_count())
            self.log.info('Identified number of emails as %s', self.emails_num)
        except Exception:
            raise CVTestStepFailure(
                f"Error getting the number of custodians and emails")

    @test_step
    def verify_reference_copy_job(self):
        """Verification of Case Manager Reference Copy Job"""
        if int(self.reference_copy_details['Number of files transferred']) != self.emails_num:
            raise CVTestStepFailure(
                'Verification of Reference Copy Job Failed')

    @test_step
    def verify_content_indexing_job(self):
        """Verification of Case Manager Content Indexing Job"""
        messages = (int(self.content_indexing_details['Number of files transferred']))
        if messages >= self.emails_num:
            raise CVTestStepFailure(
                'Verification of Content Indexing Job failed')

    @test_step
    def get_emails_from_index_server(self):
        """To query the number of emails from index server"""
        try:
            app_id_list = self.solr_search_obj.get_app_id(
                'CaseDef_'+self.case_name,
                'source',
                self.inputJSONnode['commcell']['loginUsername'],
                self.mssql)
            app_id = '(' + ','.join(app_id_list) + ')'
            details_list, distinct_cloud_ids = self.solr_search_obj.get_ci_server_url(
                self.mssql, app_id)
            cloud_name = dict()
            for cloud_id in distinct_cloud_ids:
                cloud_name[cloud_id] = self.solr_search_obj.get_index_server_name(
                    cloud_id)
            for item in details_list:
                self.ex_object.index_server = cloud_name[item['cloudId']]
                query_url = item['ciServer'] + '/select?'
                self.solr_helper_obj = SolrHelper(self.ex_object, query_url)
                custodian_list = []
                for custodian in self.custodians:
                    custodian_list.append('*' + custodian + '*')
                if (item['serverType'] == '1' and
                        (item['schemaVersion'] == '0' or item['schemaVersion'] == '1')):
                    solr_results = self.solr_helper_obj.create_url_and_get_response(
                        {'cvownerdisp': custodian_list,
                         'keyword': self.tcinputs['Keyword']})
                    self.is_emails_num += self.solr_helper_obj.get_count_from_json(
                        solr_results.content)
                elif item['serverType'] == '5' or (item['serverType'] == '1' and item['schemaVersion'] == '2'):
                    solr_results = self.solr_helper_obj.create_url_and_get_response(
                        {'OwnerName': custodian_list,
                         'keyword': self.tcinputs['Keyword']})
                    self.is_emails_num += self.solr_helper_obj.get_count_from_json(
                        solr_results.content)
            self.log.info("Solr Query returns %s items", self.is_emails_num)
        except Exception:
            raise CVTestStepFailure(f'Error Querying the index server')

    @test_step
    def verify_number_of_emails(self):
        """Verify the number of emails by comparing the value got from
        the search tab by the value queried from the Index Server"""
        if self.emails_num != self.is_emails_num:
            raise CVTestStepFailure('EMAIL COUNT MISMATCH')

    @test_step
    def verify_number_of_custodians(self):
        """Verify the number of custodians by comparing the value got from the
         search tab by the length of the list of custodians given as input"""
        if self.custodians_num != len(self.custodians):
            raise CVTestStepFailure('CUSTODIAN COUNT MISMATCH')
    @test_step
    def perform_ui_keyword_search(self):
        """Perform Keyword Search on the search tab"""
        self.case_manager.open_search_tab()
        self.keyword_search = self.case_manager.get_keyword_email_count(
            self.tcinputs['SearchKeyword'] + '\n')
        self.log.info('Identified number of emails with keyword "%s" as %s',
                      self.tcinputs['SearchKeyword'], self.keyword_search)

    @test_step
    def perform_solr_keyword_search(self):
        """Perform keyword search on Solr"""
        dest_app_id = self.solr_search_obj.get_app_id(
            'CaseDef_'+self.case_name,
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
            self.index_copy_details=self.case_manager.index_copy_job(case_name=self.case_name)
            self.reference_copy_details=self.case_manager.reference_copy_job(case_name=self.case_name)
            self.content_indexing_details=self.case_manager.content_index_job(case_name=self.case_name)
            self.verify_case_manager_page()
            self.get_no_of_custodians_and_emails()
            self.verify_reference_copy_job()
            self.verify_content_indexing_job()
            self.get_emails_from_index_server()
            self.verify_number_of_emails()
            self.verify_number_of_custodians()
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