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
from AutomationUtils.options_selector import OptionsSelector
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper
from Application.Exchange.SolrSearchHelper import SolrSearchHelper
from Web.AdminConsole.GovernanceAppsPages.ComplianceSearch import ComplianceSearch, CustomFilter
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.Common.cvbrowser import BrowserFactory, Browser


class TestCase(CVTestCase):
    """Class for executing
    Verification of search filter with multiple values, for Compliance Search from admin console"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verification of search filter with multiple values, " \
                    "for Compliance Search from admin console"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.accessnodes = None
        self.globaladmin = None
        self.password = None
        self.show_to_user = False
        self.tcinputs = {
            "IndexServer": None,
            "SearchKeyword": None,
            "Custodian_Users": None
        }
        # Test Case constants
        self.browser = None
        self.app_name = None
        self.indexservercloud = None
        self.search_keyword = None
        self.sender_users_list = None
        self.has_attach_list = None
        self.custodian_users_list = None
        self.size_range_list = None
        self.modified_date_range_list = None
        self.clients_filter_list = None
        self.test_folders_list = None
        self.ex_object = None
        self.solr_search_obj = None
        self.solrquery_params = None
        self.solr_helper_obj = None
        self.count_compliance_search = -1
        self.count_solr = None
        self.test_case_error = None
        self.gov_app = None
        self.app = None
        self.navigator = None
        self.admin_console = None
        self.db_obj = None
        self.fq_string = None
        self.custom_filter = None
        self.mssql = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            # Test Case constants
            self.app_name = str(self.id) + "_app"
            self.indexservercloud = self.tcinputs['IndexServer']
            self.search_keyword = self.tcinputs['SearchKeyword']
            self.sender_users_list = self.tcinputs['SenderFieldTestUsers']
            self.has_attach_list = self.tcinputs['has_attach_Testvalue']
            self.custodian_users_list = self.tcinputs['Custodian_Users']
            self.clients_filter_list = self.tcinputs['ClientsFilter_Values']
            self.test_folders_list = self.tcinputs['TestFolders']
            self.modified_date_range_list = self.tcinputs['ModifiedDate_TestRanges']
            self.size_range_list = self.tcinputs['size_TestRanges']
            self.db_obj = OptionsSelector(self.commcell)

            self.browser = BrowserFactory().create_browser_object()
            self.browser.open(maximize=True)
            self.admin_console = AdminConsole(
                self.browser, self.inputJSONnode['commcell']['webconsole_url'])

            self.admin_console.login(self.inputJSONnode['commcell']['loginUsername'],
                                     self.inputJSONnode['commcell']['loginPassword'])

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_governance_apps()
            self.app = ComplianceSearch(self.admin_console)
            self.custom_filter = CustomFilter(self.admin_console)
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
    def compliancesearch_keyword_search(self):
        """
            Search for Keyword in Compliance Search UI
        """
        self.count_compliance_search = self.app.search_for_keyword_get_results(
            self.indexservercloud, self.search_keyword)
        self.log.info(
            "Compliance Search returns %s items",
            self.count_compliance_search)
        if self.count_compliance_search == -1:
            raise CVTestStepFailure(f"Error getting Compliance Search results")

    @test_step
    def query_indexserver_get_results(self):
        """
            Query IndexServer for given keyword and filter criteria
        """
        self.log.info("Getting search results count from Index Server")
        params = {'start': 0, 'rows': 50, 'fq': self.fq_string}
        search_base_url = self.solr_search_obj.construct_virtual_index_query(
            "Mailbox Index", self.inputJSONnode['commcell']['loginUsername'], self.mssql,
            indexservercloud=self.indexservercloud)
        self.solr_helper_obj = SolrHelper(self.ex_object, search_base_url)
        solr_results = self.solr_search_obj.create_url_with_debug_query_and_get_response(
            self.solr_helper_obj, {'keyword': self.search_keyword}, op_params=params)
        self.count_solr = self.solr_helper_obj.get_count_from_json(
            solr_results.content)
        self.log.info("Solr Query returns %s items", self.count_solr)

    @test_step
    def apply_search_filters_from_clientname_attachment_custodian(self):
        """
           Apply filter for from, clientname, attachment and custodian ;
            fire compliancesearch and perform Indexserver query
        """
        from_user_list = random.sample(self.sender_users_list, 2)

        clients_list = random.sample(self.clients_filter_list, 2)

        client_id_list = []

        for client_name in clients_list:
            client_id = self.solr_search_obj.get_client_id(client_name)
            client_id_list.append(str(client_id))

        hasattach_list = random.sample(self.has_attach_list, 2)

        custodian_user_list = random.sample(self.custodian_users_list, 2)

        filters_list = {
            "From": from_user_list,
            "Client name": clients_list,
            "Attachment": hasattach_list,
            "Custodian": custodian_user_list}

        parameters_search = self.custom_filter.apply_custom_filters_with_search(
            filters_list)
        self.count_compliance_search = self.app.get_total_rows_count()

        if self.count_compliance_search == -1:
            raise CVTestStepFailure(
                "Error getting Compliance Search results after filters")

        # Include only applied filters in Solr query.
        # With one filter applied, other filter may disappear in the UI

        self.fq_string = ""

        if parameters_search["From"]:
            from_fq_search_string = "(FromDisplay_idx:\"" + from_user_list[0]\
                                    + "\" OR " + "FromDisplay_idx:\"" + from_user_list[1] + "\")"
            self.fq_string = self.fq_string + from_fq_search_string + " AND "

        if parameters_search["Custodian"]:
            custodian_fq_search_string = "(OwnerName_idx:\""\
                                         + custodian_user_list[0] + "\" OR "\
                                         + "OwnerName_idx:\"" + custodian_user_list[1] + "\")"
            self.fq_string = self.fq_string + custodian_fq_search_string + " AND "

        if parameters_search["Client name"]:
            client_fq_search_string = "(ClientId:" + client_id_list[0]\
                                      + " OR " + "ClientId:" + client_id_list[1] + ")"
            self.fq_string = self.fq_string + client_fq_search_string + " AND "

        if parameters_search["Attachment"]:
            hasattach_fq_search_string = "(HasAttachment:" + hasattach_list[0]\
                                         + " OR " + "HasAttachment:" + hasattach_list[1] + ")"
            self.fq_string = self.fq_string + hasattach_fq_search_string
        else:
            self.fq_string = self.fq_string[:-5]

    @test_step
    def apply_search_filters_custodian_folder_modified_date_size(self):
        """
           Apply filter for custodian, folder, modified date and size ;
           fire compliancesearch and perform Indexserver query
        """

        custodian_user_list = random.sample(self.custodian_users_list, 2)

        folders_list = random.sample(self.test_folders_list, 2)

        date_list = random.sample(self.modified_date_range_list, 2)

        size_list = random.sample(self.size_range_list, 2)

        filters_list = {"Custodian":custodian_user_list,
                        "Email folder":folders_list}

        parameters_search = self.custom_filter.apply_custom_filters_with_search(filters_list)
        if self.custom_filter.apply_date_filters(date_list):
            parameters_search["Modified date"] = True
        else:
            parameters_search["Modified date"] = False

        if self.custom_filter.apply_size_filters(size_list):
            parameters_search["Size"] = True
        else:
            parameters_search["Size"] = False

        self.count_compliance_search = self.app.get_total_rows_count()

        if not self.count_compliance_search:
            raise CVTestStepFailure\
                ("Error getting Compliance Search results after filters")

        # Include only applied filters in Solr query. With one filter applied,
        # other filter may disappear in the UI

        solr_date_range = self.solr_search_obj.get_date_range(date_list)
        solr_size_range = self.solr_search_obj.get_size_range(size_list)

        self.fq_string = ""
        if parameters_search["Custodian"]:
            custodian_fq_search_string = "(OwnerName_idx:\"" + custodian_user_list[0]\
                                         + "\" OR " + "OwnerName_idx:\"" + custodian_user_list[1] + "\")"
            self.fq_string = self.fq_string + custodian_fq_search_string + " AND "

        if parameters_search["Email folder"]:
            folder_fq_search_string = "(Folder_sort:\"" + folders_list[0]\
                                      + "\" OR " + "Folder_sort:\"" + folders_list[1] + "\")"
            self.fq_string = self.fq_string + folder_fq_search_string + " AND "

        if parameters_search["Modified date"]:
            date_fq_search_string = "(ReceivedTime:" + solr_date_range[0]\
                                    + " OR " + "ReceivedTime:" + solr_date_range[1] + ")"
            self.fq_string = self.fq_string + date_fq_search_string + " AND "

        if parameters_search["Size"]:
            size_fq_search_string = "(Size:" + solr_size_range[0]\
                                    + " OR " + "Size:" + solr_size_range[1] + ")"
            self.fq_string = self.fq_string + size_fq_search_string
        else:
            self.fq_string = self.fq_string[:-5]

    @test_step
    def validate_search_results(self):
        """
           Check if the items count from ComplianceSearch and Indexserver match
        """
        self.log.info(
            "Compliance Search Returned [%s], IndexServer Solr Query Returned [%s]",
            self.count_compliance_search,
            self.count_solr)
        if int(self.count_compliance_search) != int(self.count_solr):
            self.test_case_error = (
                "Compliance Search Returned [%s], "
                "IndexServer Solr Query Returned [%s]. ",
                self.count_compliance_search,
                self.count_solr)
            raise CVTestStepFailure(self.test_case_error)

    def run(self):
        try:
            self.init_tc()
            self.compliancesearch_keyword_search()
            self.apply_search_filters_from_clientname_attachment_custodian()
            self.query_indexserver_get_results()
            self.validate_search_results()
            self.navigator.navigate_to_governance_apps()
            self.gov_app.select_compliance_search()
            self.compliancesearch_keyword_search()
            self.apply_search_filters_custodian_folder_modified_date_size()
            self.query_indexserver_get_results()
            self.validate_search_results()
        except Exception as err:
            handle_testcase_exception(self, err)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
