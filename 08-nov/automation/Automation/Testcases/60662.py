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
import base64
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from Application.Exchange.SolrSearchHelper import SolrSearchHelper
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Application.Exchange.solr_filetype_helper import SolrFiletypeHelper


class TestCase(CVTestCase):
    """Class for executing-
     Verification of search filters for (email,file) metadata,
     in Advanced search of Compliance Search from admin console"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = (f"Verification of search filters for email,file metadata, " 
                     f"in Advanced search of Compliance Search from admin console")

        # Test Case constants
        self.indexservercloud = None
        self.search_keyword = None
        self.raw_query = None
        self.sampling_rate = None
        self.solr_search_obj = None
        self.advanced_search_results = -1
        self.count_solr = -1
        self.test_case_error = None
        self.baseurl = None
        self.encoded_pwd = None
        self.q_string = None
        self.mssql = None
        self.solr_filetype_helper = None
        self.search_view = None
        self.sampling = False

    def setup(self):
        """ Initial configuration for the test case. """
        try:
            # Test Case constants
            self.indexservercloud = self.tcinputs['IndexServer']
            self.search_keyword = self.tcinputs['SearchKeyword']
            self.search_view = self.tcinputs['SearchView']
            self.raw_query = random.choice(self.tcinputs['Raw_Query'])
            self.sampling_rate = random.choice(self.tcinputs['Sampling_Rate'])
            self.baseurl = self.commcell._web_service
            if self.baseurl[-1] == '/':
                self.baseurl = self.baseurl[:-1]
            admin_pwd = self.inputJSONnode['commcell']['loginPassword']
            encoded_bytes_pwd = base64.b64encode(admin_pwd.encode("utf-8"))
            self.encoded_pwd = str(encoded_bytes_pwd, "utf-8")
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
    def query_indexserver_get_results(self):
        """
            Query IndexServer for given keyword and filter criteria
        """
        self.log.info("Getting search results count from Index Server")

        solr_url = self.solr_filetype_helper.create_solr_url(
            self.inputJSONnode['commcell']['loginUsername'],
            self.search_view,
            self.mssql
        )
        self.q_string = f'({self.raw_query})'
        params = {'start': 0, 'rows': 50, 'q': self.q_string, 'errorrate': self.sampling_rate}
        solr_results = self.solr_filetype_helper.create_query_and_get_response(
            solr_url, op_params=params)
        self.count_solr = self.solr_filetype_helper.get_count_from_json(
            solr_results.content)
        if self.count_solr == -1:
            raise CVTestStepFailure(f"Error getting results from Solr")
        self.log.info("Solr Query returns %s items", self.count_solr)

    @test_step
    def advanced_search_raw_query_sampling(self):
        """
            Perform AdvancedSearch for file filters through REST API call
            Filters: Raw query and Sampling rate with default operators
        """
        query_and_search_filters = {'raw_query': self.raw_query,
                                    'Sampling Rate': self.sampling_rate}
        internal_cloud_name = self.solr_filetype_helper.get_internal_cloud_name()

        self.advanced_search_results = self.solr_search_obj. \
            submit_advanced_search_api_request(self.baseurl,
                                               self.inputJSONnode['commcell']['loginUsername'],
                                               self.encoded_pwd, self.indexservercloud,
                                               self.search_keyword, "NONE", query_and_search_filters,
                                               self.search_view)

        self.log.info(
            "Advanced Search API returns %s items",
            self.advanced_search_results)
        if self.advanced_search_results == -1:
            raise CVTestStepFailure(f"Error getting Advanced Search results")

    @test_step
    def validate_search_results(self):
        """
           Check if the items count from AdvancedSearch and Indexserver match
        """
        self.log.info(f"Advanced Search API Returned [{self.advanced_search_results}], "
                      f"IndexServer Solr Query Returned [{self.count_solr}]")
        if int(self.advanced_search_results) != int(self.count_solr):
            self.test_case_error = (
                f"Advanced Search API Returned [{self.advanced_search_results}], "
                f"IndexServer Solr Query Returned [{self.count_solr}]")
            raise CVTestStepFailure(self.test_case_error)

    def run(self):
        try:
            self.advanced_search_raw_query_sampling()
            self.query_indexserver_get_results()
            self.validate_search_results()

        except Exception as err:
            handle_testcase_exception(self, err)
