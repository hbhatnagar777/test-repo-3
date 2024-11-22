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

import random
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from Application.Exchange.solr_filetype_helper import SolrFiletypeHelper
from Application.Exchange.SolrSearchHelper import SolrSearchHelper
from Web.AdminConsole.GovernanceAppsPages.ComplianceSearch import ComplianceSearch, CustomFilter
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps


class TestCase(CVTestCase):
    """Class for executing Verification of Search filters with single facet values in File View,
    for Compliance Search from Admin Console"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = (f'Verification of Search filters with single facet values in File View, '
                     f'for Compliance Search from Admin Console')
        self.browser = None
        self.indexservercloud = None
        self.searchview = None

        # Test Case constants
        self.solr_search_obj = None
        self.solr_filetype_helper = None
        self.size_range = None
        self.modified_date_range = None
        self.clients_filter = None
        self.filetype_filter = None
        self.count_cs_size_filter = -1
        self.count_cs_filetype_filter = -1
        self.count_cs_date_filter = -1
        self.count_cs_clientname_filter = -1
        self.solr_count_size_filter = -1
        self.solr_count_filetype_filter = -1
        self.solr_count_date_filter = -1
        self.solr_count_clientname_filter = -1
        self.test_case_error = None
        self.gov_app = None
        self.app = None
        self.navigator = None
        self.admin_console = None
        self.mssql = None
        self.custom_filter = None
        self.fq_size_string = None
        self.fq_date_string = None
        self.fq_clientname_string = None
        self.fq_filetype_string = None
        self.clientname_filter_applied = None
        self.filetype_filter_applied = None
        self.date_filter_applied = None
        self.size_filter_applied = None

    def setup(self):
        """ Initial configuration for the test case. """
        try:
            # Test Case constants
            self.indexservercloud = self.tcinputs['IndexServer']
            self.searchview = self.tcinputs['SearchView']
            self.modified_date_range = random.choice(self.tcinputs['ModifiedDate_TestRanges'])
            self.size_range = random.choice(self.tcinputs['size_TestRanges'])
            self.clients_filter = random.choice(self.tcinputs['ClientsFilter_Values'])
            self.filetype_filter = random.choice(self.tcinputs['FiletypeFilter_Values'])
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)

            self.admin_console.login(
                self.inputJSONnode['commcell']['loginUsername'],
                self.inputJSONnode['commcell']['loginPassword'])

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_governance_apps()

            self.app = ComplianceSearch(self.admin_console)
            self.custom_filter = CustomFilter(self.admin_console)
            self.gov_app = GovernanceApps(self.admin_console)

            self.gov_app.select_compliance_search()

            self.solr_search_obj = SolrSearchHelper(self)
            server_name = self.tcinputs['SQLServerName']
            user = self.tcinputs['SQLUsername']
            password = self.tcinputs['SQLPassword']
            self.mssql = MSSQL(
                server_name,
                user,
                password,
                'CommServ',
                as_dict=False)
            self.solr_filetype_helper = SolrFiletypeHelper(self)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def set_preferences(self):
        """
            Set the Index Server and Search View in Preferences tab
        """
        self.app.set_indexserver_and_searchview_preference(
            self.indexservercloud, self.searchview)
        self.app.get_total_rows_count(search_keyword='*')

    @test_step
    def compliancesearch_size_filter(self):
        """
            Search using size filter in Compliance Search UI
        """

        self.size_filter_applied = self.custom_filter.apply_size_filters([self.size_range])
        self.count_cs_size_filter = self.app.get_total_rows_count()
        self.app.clear_custodian_filter_all()
        self.log.info(
            f"Compliance Search using Size filter returns {self.count_cs_size_filter} items")
        if self.count_cs_size_filter == -1:
            raise CVTestStepFailure(f"Error getting Compliance Search results")

    @test_step
    def compliancesearch_date_filter(self):
        """
            Search using modified date filter in Compliance Search UI
        """

        self.date_filter_applied = self.custom_filter.apply_date_filters([self.modified_date_range])
        self.count_cs_date_filter = self.app.get_total_rows_count()
        self.app.clear_custodian_filter_all()
        self.log.info(
            f"Compliance Search using Modified Date filter returns {self.count_cs_date_filter} items")
        if self.count_cs_date_filter == -1:
            raise CVTestStepFailure(f"Error getting Compliance Search results")

    @test_step
    def compliancesearch_filetype_filter(self):
        """
            Search using filetype filter in Compliance Search UI
        """

        self.filetype_filter_applied = self.custom_filter.apply_filetype_filters(self.filetype_filter)
        self.count_cs_filetype_filter = self.app.get_total_rows_count()
        self.app.clear_custodian_filter_all()
        self.log.info(
            f"Compliance Search using File type filter returns {self.count_cs_filetype_filter} items")
        if self.count_cs_filetype_filter == -1:
            raise CVTestStepFailure(f"Error getting Compliance Search results")

    @test_step
    def compliancesearch_clientname_filter(self):
        """
            Search using client name filter in Compliance Search UI
        """

        self.clientname_filter_applied = self.custom_filter.apply_custom_filters_with_search(
            {"Client name": [self.clients_filter]})
        self.count_cs_clientname_filter = self.app.get_total_rows_count()
        self.app.clear_custodian_filter_all()
        self.log.info(
            f"Compliance Search using Client name filter returns {self.count_cs_clientname_filter} items")
        if self.count_cs_clientname_filter == -1:
            raise CVTestStepFailure(f"Error getting Compliance Search results")

    @test_step
    def query_indexserver_get_results(self):
        """
            Query IndexServer with provided facets
        """

        self.log.info("Getting search results count from Index Server")
        if self.size_filter_applied is not False:
            solr_size_range = self.solr_search_obj.get_size_range([self.size_range])
            self.fq_size_string = "Size:" + solr_size_range[0]
        if self.date_filter_applied is not False:
            solr_date_range = self.solr_search_obj.get_date_range([self.modified_date_range])
            self.fq_date_string = "ModifiedTime:" + solr_date_range[0]
        if self.filetype_filter_applied is not False:
            self.fq_filetype_string = "FileExtension_idx:" + self.filetype_filter
        if self.clientname_filter_applied['Client name'] is not False:
            client_id = self.solr_search_obj.get_client_id(self.clients_filter)
            self.fq_clientname_string = "ClientId:" + client_id

        size_params = {'start': 0, 'rows': 50, 'fq': self.fq_size_string, 'q': 'ContentIndexingStatus:1'}
        date_params = {'start': 0, 'rows': 50, 'fq': self.fq_date_string, 'q': 'ContentIndexingStatus:1'}
        filetype_params = {
            'start': 0,
            'rows': 50,
            'fq': self.fq_filetype_string,
            'q': 'ContentIndexingStatus:1'}
        clientname_params = {
            'start': 0,
            'rows': 50,
            'fq': self.fq_clientname_string,
            'q': 'ContentIndexingStatus:1'}

        solr_url = self.solr_filetype_helper.create_solr_url(
            self.inputJSONnode['commcell']['loginUsername'],
            self.searchview,
            self.mssql
        )

        solr_size_response = self.solr_filetype_helper.create_query_and_get_response(
            solr_url, op_params=size_params)
        self.solr_count_size_filter = self.solr_filetype_helper.get_count_from_json(
            solr_size_response.content)
        self.log.info(
            f"Solr query using size filter returns {self.solr_count_size_filter} items")

        solr_filetype_response = self.solr_filetype_helper.create_query_and_get_response(
            solr_url, op_params=filetype_params)
        self.solr_count_filetype_filter = self.solr_filetype_helper.get_count_from_json(
            solr_filetype_response.content)
        self.log.info(
            f"Solr query using filetype filter returns {self.solr_count_filetype_filter} items")

        solr_date_response = self.solr_filetype_helper.create_query_and_get_response(
            solr_url, op_params=date_params)
        self.solr_count_date_filter = self.solr_filetype_helper.get_count_from_json(
            solr_date_response.content)
        self.log.info(
            f"Solr query using Modified time filter returns {self.solr_count_date_filter} items")

        solr_clientname_response = self.solr_filetype_helper.create_query_and_get_response(
            solr_url, op_params=clientname_params)

        self.solr_count_clientname_filter = self.solr_filetype_helper.get_count_from_json(
            solr_clientname_response.content)
        self.log.info(
            f"Solr query using Client name filter returns {self.solr_count_clientname_filter} items")

    @test_step
    def validate_search_results(self):
        """
           Check if the items count from ComplianceSearch and Indexserver match
        """

        self.log.info(f"Compliance Search with size filter Returned [{self.count_cs_size_filter}],"
                      f" IndexServer Solr Query Returned [{self.solr_count_size_filter}]")
        self.validation_helper(
            self.count_cs_size_filter,
            self.solr_count_size_filter)

        self.log.info(f"Compliance Search with date filter Returned [{self.count_cs_date_filter}],"
                      f" IndexServer Solr Query Returned [{self.solr_count_date_filter}]")
        self.validation_helper(
            self.count_cs_date_filter,
            self.solr_count_date_filter)

        self.log.info(f"Compliance Search with filetype filter Returned [{self.count_cs_filetype_filter}],"
                      f" IndexServer Solr Query Returned [{self.solr_count_filetype_filter}]")
        self.validation_helper(
            self.count_cs_filetype_filter,
            self.solr_count_filetype_filter)

        self.log.info(f"Compliance Search with Client name filter Returned [{self.count_cs_clientname_filter}],"
                      f" IndexServer Solr Query Returned [{self.solr_count_clientname_filter}]")
        self.validation_helper(
            self.count_cs_clientname_filter,
            self.solr_count_clientname_filter)

    def validation_helper(self, cs_count, solr_count):
        """
        Helper function for validating ComplianceSearch and Indexserver results match
        """
        if int(cs_count) != int(solr_count):
            self.test_case_error = (
                f"Compliance Search Returned [{cs_count}], "
                f"IndexServer Solr Query Returned [{solr_count}]")
            raise CVTestStepFailure(self.test_case_error)

    def run(self):
        try:
            self.set_preferences()
            self.compliancesearch_clientname_filter()
            self.compliancesearch_size_filter()
            self.compliancesearch_date_filter()
            self.compliancesearch_filetype_filter()
            self.query_indexserver_get_results()
            self.validate_search_results()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
