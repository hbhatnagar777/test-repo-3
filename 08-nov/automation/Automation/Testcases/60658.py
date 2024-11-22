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
from datetime import datetime, timezone
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from Application.Exchange.SolrSearchHelper import SolrSearchHelper
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Application.Exchange.solr_filetype_helper import SolrFiletypeHelper


class TestCase(CVTestCase):
    """Class for executing-
     Verification of search filters for file metadata,
     in Advanced search of Compliance Search from admin console"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = (f"Verification of search filters for file metadata, " 
                     f"in Advanced search of Compliance Search from admin console")

        # Test Case constants
        self.indexservercloud = None
        self.search_keyword = None
        self.folders_list = None
        self.size_range = None
        self.modified_date_range = None
        self.filetype_filter = None
        self.filename_filter = None
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
        self.fq_string = None
        self.sampling = False

    def setup(self):
        """ Initial configuration for the test case. """
        try:
            # Test Case constants
            self.indexservercloud = self.tcinputs['IndexServer']
            self.search_keyword = self.tcinputs['SearchKeyword']
            self.search_view = self.tcinputs['SearchView']
            self.folders_list = random.sample(self.tcinputs['Folder'], 2)
            self.modified_date_range = self.tcinputs['ModifiedDate_TestRanges']
            self.size_range = self.tcinputs['Size_TestRanges']
            self.raw_query = self.tcinputs['Raw_Query']
            self.sampling_rate = random.choice(self.tcinputs['Sampling_Rate'])
            self.filetype_filter = random.sample(self.tcinputs['FiletypeFilter_Values'], 2)
            self.filename_filter = random.sample(self.tcinputs['FileNameFilter_Values'], 2)
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
    def advanced_search_filename_size_date_filetype_folder_default(
            self):
        """
            Perform AdvancedSearch for file filters through REST API call
            Filters: File Name, Size, File type, Modified date and Folder with default operators
        """
        file_filters = {}

        str1 = ';'.join(self.filename_filter)
        filename_str = "OR;" + str1
        file_filters['FILE_NAME'] = filename_str

        str1 = ';'.join(self.size_range)
        size_str = "RANGE;" + str1
        file_filters['SIZEINKB'] = size_str

        str1 = ';'.join(self.filetype_filter)
        filetype_str = "OR;" + str1
        file_filters['EXT_NAME'] = filetype_str

        modified_date_unix = self.get_epochtime(self.modified_date_range)
        str1 = ';'.join(modified_date_unix)
        modified_date_str = "RANGE;" + str1
        file_filters['MODIFIEDTIME'] = modified_date_str

        str1 = ';'.join(self.folders_list)
        folder_str = "OR;" + str1
        file_filters['FILE_FOLDER'] = folder_str

        internal_cloud_name = self.solr_filetype_helper.get_internal_cloud_name()

        self.advanced_search_results = self.solr_search_obj.\
            submit_advanced_search_api_request(self.baseurl,
                                               self.inputJSONnode['commcell']['loginUsername'],
                                               self.encoded_pwd, self.indexservercloud,
                                               self.search_keyword, "AND", file_filters,
                                               self.search_view)
        self.log.info(
            "Advanced Search API returns %s items",
            self.advanced_search_results)
        if self.advanced_search_results == -1:
            raise CVTestStepFailure(f"Error getting Advanced Search results")

        fq_size_string = f"(Size:[{self.size_range[0]} TO {self.size_range[1]}])"

        fq_filename_string = (f"((FileName_idx:{self.filename_filter[0]}) OR "
                              f"(FileName_idx:{self.filename_filter[1]}))")

        fq_filetype_string = (f"((FileExtension_idx:{self.filetype_filter[0]}) OR "
                              f"(FileExtension_idx:{self.filetype_filter[1]}))")

        fq_date_string = (f"(ModifiedTime:[{self.modified_date_range[0]} TO "
                          f"{self.modified_date_range[1]}])")

        fq_folder_string = (f"((FolderName_idx:{self.folders_list[0]}) OR "
                            f"(FolderName_idx:{self.folders_list[1]}))")

        self.fq_string = (f'{fq_size_string} AND {fq_filename_string} AND {fq_filetype_string} '
                          f'AND {fq_date_string} AND {fq_folder_string}')

    @test_step
    def advanced_search_filename_size_date_filetype_folder_non_default(
            self):
        """
            Perform AdvancedSearch for file filters through REST API call
            Filters: File Name, Size, File type, Modified date and Folder
            without default operators
        """
        file_filters = {}

        str1 = ';'.join(self.filename_filter)
        filename_str = "NOT;" + str1
        file_filters['FILE_NAME'] = filename_str

        str1 = ';'.join(self.size_range)
        size_str = "RANGE;" + str1
        file_filters['SIZEINKB'] = size_str

        str1 = ';'.join(self.filetype_filter)
        filetype_str = "NOT;" + str1
        file_filters['EXT_NAME'] = filetype_str

        modified_date_unix = self.get_epochtime(self.modified_date_range)
        str1 = ';'.join(modified_date_unix)
        modified_date_str = "RANGE;" + str1
        file_filters['MODIFIEDTIME'] = modified_date_str

        str1 = ';'.join(self.folders_list)
        folder_str = "NOT;" + str1
        file_filters['FILE_FOLDER'] = folder_str

        internal_cloud_name = self.solr_filetype_helper.get_internal_cloud_name()

        self.advanced_search_results = self.solr_search_obj.\
            submit_advanced_search_api_request(self.baseurl,
                                               self.inputJSONnode['commcell']['loginUsername'],
                                               self.encoded_pwd, self.indexservercloud,
                                               self.search_keyword, "OR", file_filters,
                                               self.search_view)
        self.log.info(
            "Advanced Search API returns %s items",
            self.advanced_search_results)
        if self.advanced_search_results == -1:
            raise CVTestStepFailure(f"Error getting Advanced Search results")

        fq_size_string = f"(Size:[{self.size_range[0]} TO {self.size_range[1]}])"

        fq_filename_string = (f"((FileName_idx:{self.filename_filter[0]}) OR "
                              f"(FileName_idx:{self.filename_filter[1]}))")

        fq_filetype_string = (f"((FileExtension_idx:{self.filetype_filter[0]}) OR "
                              f"(FileExtension_idx:{self.filetype_filter[1]}))")

        fq_date_string = (f"(ModifiedTime:[{self.modified_date_range[0]} TO "
                          f"{self.modified_date_range[1]}])")

        fq_folder_string = (f"((FolderName_idx:{self.folders_list[0]}) OR "
                            f"(FolderName_idx:{self.folders_list[1]}))")

        self.fq_string = (f'{fq_size_string} OR {fq_date_string} NOT {fq_filename_string}'
                          f' NOT {fq_filetype_string} NOT {fq_folder_string}')

    @test_step
    def advanced_search_raw_query_sampling(self):
        """
            Perform AdvancedSearch for file filters through REST API call
            Filters: Raw query and Sampling rate with default operators
        """
        query_and_search_filters = {'raw_query': self.raw_query[0],
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

        self.sampling = True
        self.q_string = f'({self.raw_query[0]})'
        self.fq_string = None

    def get_epochtime(self, time_list):
        """
        Converts date to unix epoch timestamp
        :param time_list: List of dates in the format of string
        :return: List of dates in unix epoch time format
        """
        epoch_t = []
        for datetime_val in time_list:
            date_obj = datetime.strptime(datetime_val, "%Y-%m-%dT%H:%M:%SZ")
            unix_time = int(date_obj.replace(tzinfo=timezone.utc).timestamp())
            epoch_t.append(str(unix_time))
        return epoch_t

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

        params = {'start': 0, 'rows': 50, 'fq': self.fq_string}
        if self.sampling:
            params['errorrate'] = self.sampling_rate
            params['q'] = self.q_string
        solr_results = self.solr_filetype_helper.create_query_and_get_response(
            solr_url, op_params=params)
        self.count_solr = self.solr_filetype_helper.get_count_from_json(
            solr_results.content)
        if self.count_solr == -1:
            raise CVTestStepFailure(f"Error getting results from Solr")
        self.log.info("Solr Query returns %s items", self.count_solr)

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
            self.advanced_search_filename_size_date_filetype_folder_default()
            self.query_indexserver_get_results()
            self.validate_search_results()
            self.advanced_search_filename_size_date_filetype_folder_non_default()
            self.query_indexserver_get_results()
            self.validate_search_results()
            self.advanced_search_raw_query_sampling()
            self.query_indexserver_get_results()
            self.validate_search_results()

        except Exception as err:
            handle_testcase_exception(self, err)
