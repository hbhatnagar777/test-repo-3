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
import json
import random
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
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """Class for Verification of Case Manager Content
    Indexing Job with 'Continuous' data collection"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ('Verification of Case Manager Content '
                     'Indexing Job with "Continuous" data collection')
        self.data_collection = 'Continuous'
        self.data_type = 'Exchange mailbox'
        self.contentid_list = [[], []]
        self.count = 0
        self.temp_count = 0
        self.case_name = None
        self.custodians = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.activate = None
        self.case_manager = None
        self.tcinputs = {
            "CaseName": None,
            "DCPlan": None,
            "ServerPlan": None,
            "Custodians": None,
            "Keyword": None,
            "SQLServerName": None,
            "SQLUsername": None,
            "SQLPassword": None
        }
        self.mssql = None
        self.ex_object = None
        self.solr_search_obj = None
        self.solr_helper_obj = None
        self.index_copy_details=None
        self.content_indexing_details=None

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
            self.ex_object = ExchangeMailbox(self)
            self.ex_object.cvoperations.client_name = self.client.client_name
            self.solr_search_obj = SolrSearchHelper(self)

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
            raise CVTestStepFailure("Error creating case")

    @test_step
    def query_server(self, custodian_label, ci_status_label, ci_status):
        """Query server and get count and contentids"""
        custodian_list = []
        for custodian in self.custodians:
            custodian_list.append('*' + custodian + '*')

        solr_results = self.solr_helper_obj.create_url_and_get_response(
            {custodian_label: custodian_list,
             ci_status_label: ci_status,
             'keyword': self.tcinputs['Keyword']})
        self.temp_count = self.solr_helper_obj.get_count_from_json(
            solr_results.content)
        self.count += self.temp_count
        if self.temp_count:
            random_no = random.choice(range(self.temp_count))
            results = json.loads(solr_results.content)
            for email in results['response']['docs']:
                self.contentid_list[ci_status].append(email['contentid'])
                if len(self.contentid_list[ci_status]) == random_no:
                    break

    @test_step
    def get_content_ids_and_count(self):
        """Getting the content ids and count from the Source Index Server"""
        try:
            app_id_list = self.solr_search_obj.get_app_id(
                'CaseDef_'+self.case_name,
                'source',
                self.inputJSONnode['commcell']['loginUsername'],
                self.mssql)
            details_list, distinct_cloud_ids = self.solr_search_obj.get_ci_server_url(
                self.mssql, '(' + ','.join(app_id_list) + ')')
            cloud_name = dict()
            for cloud_id in distinct_cloud_ids:
                cloud_name[cloud_id] = self.solr_search_obj.get_index_server_name(
                    cloud_id)
            for item in details_list:
                self.ex_object.index_server = cloud_name[item['cloudId']]
                query_url = item['ciServer'] + '/select?exclude=false&'
                self.solr_helper_obj = SolrHelper(self.ex_object, query_url)

                if (item['serverType'] == '1' and
                        (item['schemaVersion'] == '0' or item['schemaVersion'] == '1')):
                    self.query_server('cvownerdisp', 'cistatus', 0)
                    self.query_server('cvownerdisp', 'cistatus', 1)
                elif item['serverType'] == '5' or (item['serverType'] == '1' and item['schemaVersion'] == '2'):
                    self.query_server('OwnerName', 'ContentIndexingStatus', 0)
                    self.query_server('OwnerName', 'ContentIndexingStatus', 1)

                # Checking if body is searchable of mails already content
                # indexed
                for i in range(len(self.contentid_list[1])):
                    content_id = self.contentid_list[1][0]
                    solr_results = self.solr_helper_obj.create_url_and_get_response(
                        {'contentid': '*' + content_id + '*', 'keyword': '*'})
                    results = json.loads(solr_results.content)
                    if 'body' not in results['response']['docs'][0]:
                        raise CVTestStepFailure('Body not searchable')
                    self.contentid_list[1].remove(content_id)
        except Exception:
            raise CVTestStepFailure('Error verifying CI Status')

    @test_step
    def validate_count_and_cistatus(self):
        """Verifying the count and CI Status"""
        try:
            dest_app_id = self.solr_search_obj.get_app_id(
                'CaseDef_'+self.case_name,
                'destination',
                self.inputJSONnode['commcell']['loginUsername'],
                self.mssql
            )
            app_id = '(' + ','.join(dest_app_id) + ')'
            url, cloud_id = self.solr_search_obj.get_ci_server_url(
                self.mssql, app_id)
            self.ex_object.index_server = self.solr_search_obj.get_index_server_name(
                cloud_id[0])
            query_url = url[0]['ciServer'] + '/select?exclude=false&'
            self.solr_helper_obj = SolrHelper(self.ex_object, query_url)

            # Checking if body is searchable
            for item in self.contentid_list[0]:
                solr_results = self.solr_helper_obj.create_url_and_get_response(
                    {'contentid': '*' + item + '*', 'keyword': '*'})
                results = json.loads(solr_results.content)
                try:
                    ci_status = results['response']['docs'][0]['cistatus']
                except KeyError:
                    ci_status = results['response']['docs'][0]['ContentIndexingStatus']
                if ci_status != 1:
                    raise CVTestStepFailure('CI Status not set to 1')
                if 'body' not in results['response']['docs'][0]:
                    raise CVTestStepFailure('Body not searchable')

            # Checking count of CI Status=1 with count obtained from source
            solr_results = self.solr_helper_obj.create_url_and_get_response(
                {'cistatus': 1, 'keyword': '*'})
            solr_count = self.solr_helper_obj.get_count_from_json(solr_results.content)
            solr_results = self.solr_helper_obj.create_url_and_get_response(
                {'ContentIndexingStatus': 1, 'keyword': '*'})
            solr_count += self.solr_helper_obj.get_count_from_json(solr_results.content)
            if self.count != solr_count:
                raise CVTestStepFailure('COUNT MISMATCH')
        except Exception:
            raise CVTestStepFailure('Error verifying count and CI status')

    def run(self):
        """
        Testcase execution starts from here
        """
        try:
            self.init_tc()
            self.create_case_manager_client()
            self.index_copy_details = self.case_manager.index_copy_job(case_name=self.case_name)
            self.content_indexing_details = self.case_manager.content_index_job(case_name=self.case_name)
            self.get_content_ids_and_count()
            self.validate_count_and_cistatus()
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            self.case_manager.delete_case(self.case_name)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
