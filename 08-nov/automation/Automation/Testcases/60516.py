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
    """Class for executing Verification of Search filters with multiple facet conditions in File View,
    for Compliance Search from Admin Console"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = (f'Verification of Search filters with multiple facet conditions in File View, '
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
        self.count_fv_compliance_search = -1
        self.solr_count_multifacet = -1
        self.test_case_error = None
        self.gov_app = None
        self.app = None
        self.navigator = None
        self.admin_console = None
        self.mssql = None
        self.custom_filter = None
        self.fq_string = None
        self.facet_list = None

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
    def apply_search_filters_date_size_filetype_clientname(self):
        """
           Apply filter for client name, file type, modified date and size ;
           fire compliancesearch and perform Indexserver query
        """

        self.facet_list = self.custom_filter.apply_custom_filters_with_search(
            {"Client name": [self.clients_filter]})

        self.facet_list["Modified date"] = self.custom_filter.apply_date_filters([self.modified_date_range])

        self.facet_list["Size"] = self.custom_filter.apply_size_filters([self.size_range])

        self.facet_list["File type"] = self.custom_filter.apply_filetype_filters(self.filetype_filter)

        self.count_fv_compliance_search = self.app.get_total_rows_count()

        self.log.info(
            "Compliance Search using multiple facet filters returns %s items",
            self.count_fv_compliance_search)

        if self.count_fv_compliance_search == -1:
            raise CVTestStepFailure(f"Error getting Compliance Search results")


    @test_step
    def query_indexserver_get_results(self):
        """
            Query IndexServer with provided facets
        """
        self.log.info("Getting search results count from Index Server")
        client_id = self.solr_search_obj.get_client_id(self.clients_filter)
        solr_date_range = self.solr_search_obj.get_date_range([self.modified_date_range])
        solr_size_range = self.solr_search_obj.get_size_range([self.size_range])

        self.fq_string = ""
        if self.facet_list["Size"]:
            size_fq_search_string = "Size:" + solr_size_range[0]
            self.fq_string = self.fq_string + size_fq_search_string + " AND "

        if self.facet_list["Modified date"]:
            date_fq_search_string = "ModifiedTime:" + solr_date_range[0]
            self.fq_string = self.fq_string + date_fq_search_string + " AND "

        if self.facet_list["File type"]:
            filetype_fq_search_string = "FileExtension_idx:" + self.filetype_filter
            self.fq_string = self.fq_string + filetype_fq_search_string + " AND "

        if self.facet_list["Client name"]:
            client_fq_search_string = "ClientId:" + client_id
            self.fq_string = self.fq_string + client_fq_search_string
        else:
            self.fq_string = self.fq_string[:-5]
        params = {'start': 0, 'rows': 50, 'fq': self.fq_string, 'q': 'ContentIndexingStatus:1'}

        solr_url = self.solr_filetype_helper.create_solr_url(
            self.inputJSONnode['commcell']['loginUsername'],
            self.searchview,
            self.mssql
        )

        solr_response = self.solr_filetype_helper.create_query_and_get_response(
            solr_url, op_params=params)
        self.solr_count_multifacet = self.solr_filetype_helper.get_count_from_json(
            solr_response.content)
        self.log.info(
            "Solr query using multiple facets returns %s items",
            self.solr_count_multifacet)

    @test_step
    def validate_search_results(self):
        """
           Check if the items count from ComplianceSearch and Indexserver match
        """
        self.log.info(
            f"Compliance Search Returned [{self.count_fv_compliance_search}],"
            f" IndexServer Solr Query Returned [{self.solr_count_multifacet}]")

        if int(
                self.count_fv_compliance_search) != int(
                self.solr_count_multifacet):
            self.test_case_error = (
                f"Compliance Search Returned [{self.count_fv_compliance_search}], "
                f"IndexServer Solr Query Returned [{self.solr_count_multifacet}]")
            raise CVTestStepFailure(self.test_case_error)

    def run(self):
        try:
            self.set_preferences()
            self.apply_search_filters_date_size_filetype_clientname()
            self.query_indexserver_get_results()
            self.validate_search_results()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
