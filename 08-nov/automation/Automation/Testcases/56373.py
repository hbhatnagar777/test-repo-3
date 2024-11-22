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
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper
from Application.Exchange.SolrSearchHelper import SolrSearchHelper
from Web.AdminConsole.GovernanceAppsPages.ComplianceSearch import ComplianceSearch
from AutomationUtils.database_helper import MSSQL
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps


class TestCase(CVTestCase):
    """Class for executing TestCase: Verify that preferences are
    getting saved for Compliance Search from admin console"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = "Verify that preferences are getting saved " \
                    "for Compliance Search from admin console"
        self.test_individual_failure_message = ""
        self.browser = None
        self.indexservercloud = None
        self.accessnodes = None
        self.globaladmin = None
        self.password = None
        self.tcinputs = {
            "IndexServerList": None,
            "SearchKeyword": None
        }
        # Test Case constants
        self.browser = None
        self.app_name = None
        self.search_keyword = None
        self.ex_object = None
        self.solr_search_obj = None
        self.solrquery_params = None
        self.solr_helper_obj = None
        self.count_compliance_search = -1
        self.count_solr = -1
        self.test_case_error = None
        self.gov_app = None
        self.app = None
        self.page = None
        self.navigator = None
        self.admin_console = None
        self.indexserver_cloud_list = []
        self.mssql = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            # Test Case constants
            self.app_name = str(self.id) + "_app"
            self.indexserver_cloud_list = self.tcinputs['IndexServerList']
            self.search_keyword = self.tcinputs['SearchKeyword']
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.inputJSONnode['commcell']['webconsole_url'])
            self.admin_console.login(self.inputJSONnode['commcell']['loginUsername'],
                                     self.inputJSONnode['commcell']['loginPassword'])
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_governance_apps()
            self.page = self.admin_console.navigator

            self.app = ComplianceSearch(self.admin_console)
            self.gov_app = GovernanceApps(self.admin_console)

            self.gov_app.select_compliance_search()
            self.ex_object = ExchangeMailbox(self)

            self.solr_search_obj = SolrSearchHelper(self)
            self.solrquery_params = {'start': 0, 'rows': 50}
            server_name = self.tcinputs['SQLServerName']
            user = self.tcinputs['SQLUsername']
            password = self.tcinputs['SQLPassword']
            self.mssql = MSSQL(
                server_name,
                user,
                password,
                'CommServ',
                as_dict=False,
                use_pyodbc=False)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def set_indexserver_perform_compliancesearch(self, indexserver):
        """
            Search for Keyword in Compliance Search UI
            Args:
                indexserver (str)  - index_server to be set
        """
        self.count_compliance_search = self.app.search_for_keyword_get_results(
            indexserver, self.search_keyword)
        self.log.info(
            "Compliance Search returns %s items",
            self.count_compliance_search)
        if self.count_compliance_search == -1:
            raise CVTestStepFailure(f"Error getting Compliance Search results")

    @test_step
    def query_indexserver_get_results(self, indexserver):
        """
            Query IndexServer with given keyword
            Args:
                indexserver (str)  - index_server to be set
        """
        search_base_url = self.solr_search_obj.construct_virtual_index_query(
            'Mailbox Index', self.inputJSONnode['commcell']['loginUsername'], self.mssql,
            indexservercloud=indexserver)
        self.solr_helper_obj = SolrHelper(self.ex_object, search_base_url)
        solr_results = self.solr_helper_obj.create_url_and_get_response(
            {'keyword': self.search_keyword}, op_params=self.solrquery_params)
        self.count_solr = int(
            self.solr_helper_obj.get_count_from_json(
                solr_results.content))
        self.log.info("Solr Query returns %s items", self.count_solr)
        if self.count_solr == -1:
            raise CVTestStepFailure(f"Error getting IndexServer results")

    @test_step
    def validate_search_results(self, indexserver):
        """
           Check if the items count from ComplianceSearch and Indexserver match
           Args:
                indexserver (str)  - index_server to be set
        """
        self.log.info(
            "Compliance Search Returned [%s], IndexServer Solr Query "
            "Returned [%s] for IndexServer [%s]",
            self.count_compliance_search,
            self.count_solr,
            indexserver)
        if int(self.count_compliance_search) != int(self.count_solr):
            raise CVTestStepFailure("Result count mismatch")

    def run(self):
        try:
            self.init_tc()
            for indexserver in self.indexserver_cloud_list:
                self.set_indexserver_perform_compliancesearch(indexserver)
                self.query_indexserver_get_results(indexserver)
                self.validate_search_results(indexserver)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
