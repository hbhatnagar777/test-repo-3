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
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.GovernanceAppsPages.CaseManager import CaseManager
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """Class for Verification of Case Manager Reference
    Copy Job with 'Continuous' data collection"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ('Verification of Case Manager Reference Copy '
                     'Job with "Continuous" data collection')
        self.data_collection = 'Continuous'
        self.data_type = 'Exchange mailbox'
        self.case_name = None
        self.custodians = None
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
            "Custodians": None,
            "Keyword": None,
            "SQLServerName": None,
            "SQLUsername": None,
            "SQLPassword": None
        }
        self.mssql = None
        self.rtable = None
        self.ex_object = None
        self.solr_search_obj = None
        self.solr_helper_obj = None
        self.ref_copy_job_id = None
        self.db_afile_id = None
        self.solr_afile_id = None
        self.emails_num = None
        self.is_emails_num = None
        self.index_copy_details=None
        self.reference_copy_details=None


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
            self.rtable = Rtable(self.admin_console)
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
    def get_email_count(self):
        """Get the count of emails to verify"""
        try:
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            if self.rtable.is_entity_present_in_column('Name', self.case_name):
                self.case_manager.select_case(self.case_name)
            self.case_manager.open_search_tab()
            self.case_manager.click_search_button()
            try:
                self.emails_num = int(self.rtable.get_total_rows_count())
            except IndexError:
                self.emails_num = 0
        except BaseException:
            raise CVTestStepFailure('Error getting count of emails')

    @test_step
    def verify_arch_file_id(self):
        """Verifying the Archive File Id"""
        try:
            self.db_afile_id = self.solr_search_obj.get_archfile_id(
                self.case_manager.reference_copy_job_id)

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
            query_url = url[0]['ciServer'] + '/select?'
            self.solr_helper_obj = SolrHelper(self.ex_object, query_url)
            solr_results = self.solr_helper_obj.create_url_and_get_response(
                {'AchiveFileId': self.db_afile_id,
                 'CMStatus': 2,
                 'keyword': '*'})
            self.is_emails_num = self.solr_helper_obj.get_count_from_json(
                solr_results.content)
            self.log.info(
                'No of emails obtained from Solr is %s',
                self.is_emails_num)
            if self.is_emails_num != self.emails_num:
                raise CVTestStepFailure('COUNT MISMATCH')
        except BaseException:
            raise CVTestStepFailure(
                'Error verifying Archive file Id and CMStatus')

    def run(self):
        """
        Testcase execution starts from here
        """
        try:
            self.init_tc()
            self.create_case_manager_client()
            self.index_copy_details=self.case_manager.index_copy_job(case_name=self.case_name)
            self.reference_copy_details=self.case_manager.reference_copy_job(case_name=self.case_name)
            self.get_email_count()
            self.verify_arch_file_id()
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            self.case_manager.delete_case(self.case_name)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
