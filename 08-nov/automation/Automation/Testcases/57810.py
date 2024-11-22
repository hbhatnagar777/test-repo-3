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

from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper
from Application.Exchange.SolrSearchHelper import SolrSearchHelper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.GovernanceAppsPages.CaseManager import CaseManager
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """Class for Verification of Case Manager Index copy job with 'continuous' data collection"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Verification of Case Manager Index copy job with "continuous" data collection'
        self.data_type = 'Exchange mailbox'
        self.case_name = None
        self.def_name = None
        self.custodians = None
        self.def_custodians = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.activate = None
        self.case_manager = None
        self.jobs = None
        self.job_id = None
        self.tcinputs = {
            "CaseName": None,
            "DCPlan": None,
            "ServerPlan": None,
            "CaseCustodians": None,
            "CaseKeyword": None,
            "DefinitionName": None,
            "DefinitionCustodians": None,
            "DefinitionKeyword": None,
            "SQLServerName": None,
            "SQLUsername": None,
            "SQLPassword": None
        }
        self.mssql = None
        self.rtable = None
        self.case_emails_num = None
        self.def_emails_num = None
        self.ex_object = None
        self.solr_search_obj = None
        self.solr_helper_obj = None
        self.index_copy_details=None

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
            self.ex_object.cvoperations.client_name = self.client.client_name
            self.solr_search_obj = SolrSearchHelper(self)
            self.rtable = Rtable(self.admin_console)

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()

            self.case_name = self.tcinputs['CaseName'] + str(int(time.time()))
            self.def_name = self.tcinputs['DefinitionName'] + \
                str(int(time.time()))
            self.custodians = self.tcinputs['CaseCustodians']
            self.def_custodians = self.tcinputs['DefinitionCustodians']

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
                'Continuous',
                self.custodians,
                self.tcinputs['DCPlan'],
                self.tcinputs['ServerPlan'],
                self.tcinputs['CaseKeyword']
            )
            self.log.info('Case Added')
        except Exception:
            raise CVTestStepFailure("Error creating case")

    def get_no_of_emails(self):
        """Getting the number of custodians and emails from admin console"""
        self.navigator.navigate_to_governance_apps()
        self.activate.select_case_manager()
        if self.rtable.is_entity_present_in_column('Name', self.case_name):
            self.case_manager.select_case(self.case_name)
        self.case_manager.open_search_tab()
        self.case_manager.click_search_button()
        try:
            email_num = int(self.rtable.get_total_rows_count())
        except IndexError:
            email_num = 0

        self.log.info('Identified number of emails as %s', email_num)
        return email_num

    @test_step
    def get_case_email_count(self):
        """Get the number of emails added by creation of case"""
        try:
            self.case_emails_num = self.get_no_of_emails()
        except BaseException:
            raise CVTestStepFailure('Error getting the number of emails')

    @test_step
    def add_definition(self):
        """Creates another definition for the case"""
        try:
            self.case_manager.open_overview_tab()
            self.case_manager.select_add_definition()
            self.case_manager.create_definition(
                self.def_name,
                self.data_type,
                'One time only',
                self.def_custodians,
                self.tcinputs['DefinitionKeyword'],
            )
            self.log.info('Definition Added')
            self.admin_console.wait_for_completion()
            self.job_id=self.case_manager.submit_collection_job()
            self.index_copy_details = self.jobs.job_completion(self.job_id)
            if not 'Completed' == self.index_copy_details['Status']:
                exp = "Indexcopy job  not completed successfully"
                raise CVTestStepFailure(exp)
        except BaseException:
            raise CVTestStepFailure('Error adding definition')

    @test_step
    def get_def_email_count(self):
        """Get the count of emails added with the definition"""
        try:
            self.def_emails_num = self.get_no_of_emails()

            if self.def_emails_num <= self.case_emails_num:
                self.def_emails_num = 0
                app_id_list = self.solr_search_obj.get_app_id(
                    self.def_name,
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
                    self.solr_helper_obj = SolrHelper(
                        self.ex_object, query_url)
                    custodian_list = []
                    for custodian in self.def_custodians:
                        custodian_list.append('*' + custodian + '*')
                    if (item['serverType'] == '1' and
                            (item['schemaVersion'] == '0' or item['schemaVersion'] == '1')):
                        solr_results = self.solr_helper_obj.create_url_and_get_response(
                            {'cvownerdisp': custodian_list,
                             'keyword': self.tcinputs['DefinitionKeyword']})
                        self.def_emails_num += self.solr_helper_obj.get_count_from_json(
                            solr_results.content)
                    elif item['serverType'] == '5' or (item['serverType'] == '1' and item['schemaVersion'] == '2'):
                        solr_results = self.solr_helper_obj.create_url_and_get_response(
                            {'OwnerName': custodian_list,
                             'keyword': self.tcinputs['DefinitionKeyword']})
                        self.def_emails_num += self.solr_helper_obj.get_count_from_json(
                            solr_results.content)
                if self.def_emails_num != 0:
                    raise CVTestStepFailure(
                        'EMAILS FROM NEW CUSTODIAN NOT ADDED')
            self.log.info('Emails from new custodian added')
        except BaseException:
            raise CVTestStepFailure('Error getting definition email count')

    def run(self):
        """
        Testcase execution starts from here
        """
        try:
            self.init_tc()
            self.create_case_manager_client()
            self.index_copy_details = self.case_manager.index_copy_job(case_name=self.case_name)
            self.get_case_email_count()
            self.add_definition()
            self.get_def_email_count()
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            self.case_manager.delete_case(self.case_name)

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)