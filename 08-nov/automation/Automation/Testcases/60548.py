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
    """Class for executing Verification of Search filters with single facet values in
    Email/File View, for Compliance Search from Admin Console"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = (f'Verification of Search filters with single facet values in '
                     f'Email/File View for Compliance Search from Admin Console')
        self.browser = None
        self.indexservercloud = None
        self.searchview = None

        # Test Case constants
        self.solr_search_obj = None
        self.solr_filetype_helper = None
        self.size_range = None
        self.modified_date_range = None
        self.clients_filter = None
        self.datatype_filter = None
        self.filetype_filter = None
        self.custodian_filter = None
        self.from_filter = None
        self.email_folder_filter = None
        self.has_attachment = None
        self.count_cs_size_filter = -1
        self.count_cs_datatype_filter = -1
        self.count_cs_date_filter = -1
        self.count_cs_clientname_filter = -1
        self.count_cs_filetype_filter = -1
        self.count_cs_custodian_filter = -1
        self.count_cs_from_filter = -1
        self.count_cs_email_folder_filter = -1
        self.count_has_attachment = -1
        self.solr_count_size_filter = -1
        self.solr_count_datatype_filter = -1
        self.solr_count_date_filter = -1
        self.solr_count_clientname_filter = -1
        self.solr_count_filetype_filter = -1
        self.solr_count_custodian_filter = -1
        self.solr_count_from_filter = -1
        self.solr_count_email_folder_filter = -1
        self.solr_count_has_attachment = -1
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
        self.fq_datatype_string = None
        self.fq_filetype_string = None
        self.fq_custodian_string = None
        self.fq_from_string = None
        self.fq_email_folder_string = None
        self.fq_has_attachment = None
        self.facet_list = {}

    def setup(self):
        """ Initial configuration for the test case. """
        try:
            # Test Case constants
            self.indexservercloud = self.tcinputs['IndexServer']
            self.searchview = self.tcinputs['SearchView']
            self.modified_date_range = random.choice(self.tcinputs['ModifiedDate_TestRanges'])
            self.size_range = random.choice(self.tcinputs['size_TestRanges'])
            self.clients_filter = random.choice(self.tcinputs['ClientsFilter_Values'])
            self.datatype_filter = random.choice(self.tcinputs['DatatypeFilter_Values'])
            self.filetype_filter = random.choice(self.tcinputs['FiletypeFilter_Values'])
            self.custodian_filter = random.choice(self.tcinputs['CustodianFilter_Values'])
            self.from_filter = random.choice(self.tcinputs['FromFilter_Values'])
            self.email_folder_filter = random.choice(self.tcinputs['EmailFolderFilter_Values'])
            self.has_attachment = random.choice(self.tcinputs['HasAttachment_Value'])
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
        self.facet_list["Size"] = self.custom_filter.apply_size_filters([self.size_range])
        if self.facet_list["Size"]:
            self.count_cs_size_filter = self.app.get_total_rows_count()
            self.clear_and_log(self.count_cs_size_filter, "Size")

    @test_step
    def compliancesearch_date_filter(self):
        """
            Search using modified date filter in Compliance Search UI
        """
        self.facet_list["Modified date"] = self.custom_filter.apply_date_filters(
            [self.modified_date_range])
        if self.facet_list["Modified date"]:
            self.count_cs_date_filter = self.app.get_total_rows_count()
            self.clear_and_log(self.count_cs_date_filter, "Modified date")

    @test_step
    def compliancesearch_datatype_filter(self):
        """
            Search using data type filter in Compliance Search UI
        """
        self.facet_list.update(self.custom_filter.apply_custom_filters({
            "Data type": [self.datatype_filter]}))
        if self.facet_list["Data type"]:
            self.count_cs_datatype_filter = self.app.get_total_rows_count()
            self.clear_and_log(self.count_cs_datatype_filter, "Data type")

    @test_step
    def compliancesearch_clientname_filter(self):
        """
            Search using client name filter in Compliance Search UI
        """
        self.facet_list.update(self.custom_filter.apply_custom_filters({
            "Client name": [self.clients_filter]}))
        if self.facet_list["Client name"]:
            self.count_cs_clientname_filter = self.app.get_total_rows_count()
            self.clear_and_log(self.count_cs_clientname_filter, "Client name")

    @test_step
    def compliancesearch_filetype_filter(self):
        """
            Search using filetype filter in Compliance Search UI
        """
        self.facet_list["File type"] = self.custom_filter.apply_filetype_filters(
            self.filetype_filter)
        if self.facet_list["File type"]:
            self.count_cs_filetype_filter = self.app.get_total_rows_count()
            self.clear_and_log(self.count_cs_filetype_filter, "File type")

    @test_step
    def compliancesearch_custodian_filter(self):
        """
            Search using custodian filter in Compliance Search UI
        """
        self.facet_list.update(self.custom_filter.apply_custom_filters({
            "Custodian": [self.custodian_filter]}))
        if self.facet_list["Custodian"]:
            self.count_cs_custodian_filter = self.app.get_total_rows_count()
            self.clear_and_log(self.count_cs_custodian_filter, "Custodian user")

    @test_step
    def compliancesearch_from_filter(self):
        """
            Search using the sender email account in Compliance Search UI
        """
        self.facet_list.update(self.custom_filter.apply_custom_filters({
            "From": [self.from_filter]}))
        if self.facet_list["From"]:
            self.count_cs_from_filter = self.app.get_total_rows_count()
            self.clear_and_log(self.count_cs_from_filter, "From User")

    @test_step
    def compliancesearch_email_folder_filter(self):
        """
            Search using email folder filter in Compliance Search UI
        """
        self.facet_list.update(self.custom_filter.apply_custom_filters({
            "Email folder": [self.email_folder_filter]}))
        if self.facet_list["Email folder"]:
            self.count_cs_email_folder_filter = self.app.get_total_rows_count()
            self.clear_and_log(self.count_cs_email_folder_filter, "Email Folder")

    @test_step
    def compliancesearch_has_attachment_filter(self):
        """
            Filter based on whether emails have attachment or not
        """
        self.facet_list.update(self.custom_filter.apply_custom_filters({
            "Attachment": [self.has_attachment]}))
        if self.facet_list["Attachment"]:
            self.count_has_attachment = self.app.get_total_rows_count()
            self.clear_and_log(self.count_has_attachment, "Attachment")

    def clear_and_log(self, count, filter_name):
        """
            Helper function to clear filter, verify and log count information
        """
        self.custom_filter.clear_custodian_filter()
        self.log.info(
            "Compliance Search using %s filter returns %s items",
            filter_name, count)
        if count == -1:
            raise CVTestStepFailure(f"Error getting Compliance Search results")

    @test_step
    def query_indexserver_get_results(self):
        """
            Query IndexServer with provided facets
        """
        self.log.info("Getting search results count from Index Server")
        solr_url = self.solr_filetype_helper.create_solr_url(
            self.inputJSONnode['commcell']['loginUsername'],
            self.searchview,
            self.mssql
        )

        if self.facet_list["Size"]:
            solr_size_range = self.solr_search_obj.get_size_range([self.size_range])
            self.fq_size_string = "Size:" + solr_size_range[0]
            size_params = {'start': 0, 'rows': 50, 'fq': self.fq_size_string, 'q': 'ContentIndexingStatus:1'}
            solr_size_response = self.solr_filetype_helper.create_query_and_get_response(
                solr_url, op_params=size_params)
            self.solr_count_size_filter = self.solr_filetype_helper.get_count_from_json(
                solr_size_response.content)
            self.log.info(
                "Solr query using size filter returns %s items",
                self.solr_count_size_filter)

        if self.facet_list["Modified date"]:
            solr_date_range = self.solr_search_obj.get_date_range([self.modified_date_range])
            self.fq_date_string = "ModifiedTime:" + solr_date_range[0]
            date_params = {'start': 0, 'rows': 50, 'fq': self.fq_date_string, 'q': 'ContentIndexingStatus:1'}
            solr_date_response = self.solr_filetype_helper.create_query_and_get_response(
                solr_url, op_params=date_params)
            self.solr_count_date_filter = self.solr_filetype_helper.get_count_from_json(
                solr_date_response.content)
            self.log.info(
                "Solr query using Modified time filter returns %s items",
                self.solr_count_date_filter)

        if self.facet_list["Data type"]:
            if self.datatype_filter == "Files":
                self.fq_datatype_string = "DocumentType:1"
            else:
                self.fq_datatype_string = "DocumentType:2"
            datatype_params = {
                'start': 0,
                'rows': 50,
                'fq': self.fq_datatype_string,
                'q': 'ContentIndexingStatus:1'
            }
            solr_datatype_response = self.solr_filetype_helper.create_query_and_get_response(
                solr_url, op_params=datatype_params)
            self.solr_count_datatype_filter = self.solr_filetype_helper.get_count_from_json(
                solr_datatype_response.content)
            self.log.info(
                "Solr query using data type filter returns %s items",
                self.solr_count_datatype_filter)

        if self.facet_list["Client name"]:
            client_id = self.solr_search_obj.get_client_id(self.clients_filter)
            self.fq_clientname_string = "ClientId:" + client_id
            clientname_params = {
                'start': 0,
                'rows': 50,
                'fq': self.fq_clientname_string,
                'q': 'ContentIndexingStatus:1'
            }
            solr_clientname_response = self.solr_filetype_helper.create_query_and_get_response(
                solr_url, op_params=clientname_params)
            self.solr_count_clientname_filter = self.solr_filetype_helper.get_count_from_json(
                solr_clientname_response.content)
            self.log.info(
                "Solr query using Client name filter returns %s items",
                self.solr_count_clientname_filter
            )

        if self.facet_list["File type"]:
            self.fq_filetype_string = "FileExtension_idx:" + self.filetype_filter
            filetype_params = {
                'start': 0,
                'rows': 50,
                'fq': self.fq_filetype_string,
                'q': 'ContentIndexingStatus:1'
            }
            solr_filetype_response = self.solr_filetype_helper.create_query_and_get_response(
                solr_url, op_params=filetype_params)
            self.solr_count_filetype_filter = self.solr_filetype_helper.get_count_from_json(
                solr_filetype_response.content)
            self.log.info(
                "Solr query using File type filter returns %s items",
                self.solr_count_filetype_filter
            )

        if self.facet_list["Custodian"]:
            self.fq_custodian_string = "OwnerName_idx:\"" + self.custodian_filter
            custodian_params = {
                'start': 0,
                'rows': 50,
                'fq': self.fq_custodian_string,
                'q': 'ContentIndexingStatus:1'
            }
            solr_custodian_response = self.solr_filetype_helper.create_query_and_get_response(
                solr_url, op_params=custodian_params)
            self.solr_count_custodian_filter = self.solr_filetype_helper.get_count_from_json(
                solr_custodian_response.content)
            self.log.info(
                "Solr query using Custodian filter returns %s items",
                self.solr_count_custodian_filter
            )

        if self.facet_list["From"]:
            self.fq_from_string = "FromDisplay_idx:\"" + self.from_filter
            from_params = {
                'start': 0,
                'rows': 50,
                'fq': self.fq_from_string,
                'q': 'ContentIndexingStatus:1'
            }
            solr_from_response = self.solr_filetype_helper.create_query_and_get_response(
                solr_url, op_params=from_params)
            self.solr_count_from_filter = self.solr_filetype_helper.get_count_from_json(
                solr_from_response.content)
            self.log.info(
                "Solr query using From filter returns %s items",
                self.solr_count_from_filter
            )

        if self.facet_list["Email folder"]:
            self.fq_email_folder_string = "Folder_sort:\"" + self.email_folder_filter
            email_folder_params = {
                'start': 0,
                'rows': 50,
                'fq': self.fq_email_folder_string,
                'q': 'ContentIndexingStatus:1'
            }
            solr_email_folder_response = self.solr_filetype_helper.create_query_and_get_response(
                solr_url, op_params=email_folder_params)
            self.solr_count_email_folder_filter = self.solr_filetype_helper.get_count_from_json(
                solr_email_folder_response.content)
            self.log.info(
                "Solr query using Email folder filter returns %s items",
                self.solr_count_email_folder_filter
            )

        if self.facet_list["Attachment"]:
            self.fq_has_attachment = "HasAttachment:" + self.has_attachment
            has_attachment_params = {
                'start': 0,
                'rows': 50,
                'fq': self.fq_has_attachment,
                'q': 'ContentIndexingStatus:1'
            }
            solr_has_attachment_response = self.solr_filetype_helper.create_query_and_get_response(
                solr_url, op_params=has_attachment_params)
            self.solr_count_has_attachment = self.solr_filetype_helper.get_count_from_json(
                solr_has_attachment_response.content)
            self.log.info(
                "Solr query using Attachment filter returns %s items",
                self.solr_count_has_attachment
            )

    @test_step
    def validate_search_results(self):
        """
           Check if the items count from ComplianceSearch and Indexserver match
        """
        if self.facet_list["Size"]:
            self.log.info(
                "Compliance Search with size filter Returned [%s], IndexServer Solr Query Returned [%s]",
                self.count_cs_size_filter,
                self.solr_count_size_filter)
            self.validation_helper(
                self.count_cs_size_filter,
                self.solr_count_size_filter)

        if self.facet_list["Modified date"]:
            self.log.info(
                "Compliance Search with date filter Returned [%s], IndexServer Solr Query Returned [%s]",
                self.count_cs_date_filter,
                self.solr_count_date_filter)
            self.validation_helper(
                self.count_cs_date_filter,
                self.solr_count_date_filter)

        if self.facet_list["Data type"]:
            self.log.info(
                "Compliance Search with Data type filter Returned [%s], IndexServer Solr Query Returned [%s]",
                self.count_cs_datatype_filter,
                self.solr_count_datatype_filter)
            self.validation_helper(
                self.count_cs_datatype_filter,
                self.solr_count_datatype_filter)

        if self.facet_list["Client name"]:
            self.log.info(
                "Compliance Search with Client name filter Returned [%s], IndexServer Solr Query Returned [%s]",
                self.count_cs_clientname_filter,
                self.solr_count_clientname_filter)
            self.validation_helper(
                self.count_cs_clientname_filter,
                self.solr_count_clientname_filter)

        if self.facet_list["File type"]:
            self.log.info(
                "Compliance Search with File type filter Returned [%s], IndexServer Solr Query Returned [%s]",
                self.count_cs_filetype_filter,
                self.solr_count_filetype_filter)
            self.validation_helper(
                self.count_cs_filetype_filter,
                self.solr_count_filetype_filter)

        if self.facet_list["Custodian"]:
            self.log.info(
                "Compliance Search with Custodian filter Returned [%s], IndexServer Solr Query Returned [%s]",
                self.count_cs_custodian_filter,
                self.solr_count_custodian_filter)
            self.validation_helper(
                self.count_cs_custodian_filter,
                self.solr_count_custodian_filter)

        if self.facet_list["From"]:
            self.log.info(
                "Compliance Search with From filter Returned [%s], IndexServer Solr Query Returned [%s]",
                self.count_cs_from_filter,
                self.solr_count_from_filter)
            self.validation_helper(
                self.count_cs_from_filter,
                self.solr_count_from_filter)

        if self.facet_list["Email folder"]:
            self.log.info(
                "Compliance Search with Email Folder filter Returned [%s], IndexServer Solr Query Returned [%s]",
                self.count_cs_email_folder_filter,
                self.solr_count_email_folder_filter)
            self.validation_helper(
                self.count_cs_email_folder_filter,
                self.solr_count_email_folder_filter)

        if self.facet_list["Attachment"]:
            self.log.info(
                "Compliance Search with Attachment filter Returned [%s], IndexServer Solr Query Returned [%s]",
                self.count_has_attachment,
                self.solr_count_has_attachment)
            self.validation_helper(
                self.count_has_attachment,
                self.solr_count_has_attachment)

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
            self.compliancesearch_datatype_filter()
            self.compliancesearch_filetype_filter()
            self.compliancesearch_custodian_filter()
            self.compliancesearch_from_filter()
            self.compliancesearch_email_folder_filter()
            self.compliancesearch_has_attachment_filter()
            self.query_indexserver_get_results()
            self.validate_search_results()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
