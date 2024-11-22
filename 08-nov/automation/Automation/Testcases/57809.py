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

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.GovernanceAppsPages.CaseManager import CaseManager
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Applications.ExchangeAppHelper import ExchangeAppHelper
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """Class for Verification of case manager data collection types"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verification of case manager data collection types"
        self.continuous_case = None
        self.one_time_only_case = None
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
            "DataType": None,
            "OTO_Custodians": None,
            "C_Custodians": None,
            "Keyword": None
        }
        self.emails_num = None
        self.rtable = None
        self.ex_app_helper = None
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
            self.rtable = Rtable(self.admin_console)
            self.ex_app_helper = ExchangeAppHelper(self.admin_console)

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()

            self.one_time_only_case = (self.tcinputs['CaseName'] +
                                       'OneTimeOnly' + str(int(time.time())))
            self.continuous_case = (self.tcinputs['CaseName'] +
                                    'Continuous' + str(int(time.time())))
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def create_one_time_only_client(self):
        """Create a case with data collection as 'One time only'"""
        try:
            self.case_manager.select_add_case()
            self.case_manager.enter_case_details(
                self.one_time_only_case,
                self.tcinputs['DataType'],
                'One time only',
                self.tcinputs['OTO_Custodians'],
                self.tcinputs['DCPlan'],
                self.tcinputs['ServerPlan'],
                self.tcinputs['Keyword']
            )
            self.log.info('Case Added')

        except Exception:
            raise CVTestStepFailure("Error creating case")

    def get_email_num(self, case_name):
        """Get the number of emails
            case_name:- name of the case manager client
        """
        emails_num = 0
        self.navigator.navigate_to_governance_apps()
        self.activate.select_case_manager()

        if self.rtable.is_entity_present_in_column('Name', case_name):
            self.case_manager.select_case(case_name)
            self.case_manager.open_search_tab()
            self.case_manager.click_search_button()
            try:
                emails_num = int(self.rtable.get_total_rows_count())
            except IndexError:
                emails_num = 0
        return emails_num

    @test_step
    def get_one_time_only_emails(self):
        """One-time only - get the number of emails"""
        try:
            self.emails_num = self.get_email_num(self.one_time_only_case)
            self.log.info('Identified number of emails as %s', self.emails_num)
        except Exception:
            raise CVTestStepFailure("Error getting the number of emails")

    @test_step
    def edit_one_time_only_definition(self):
        """Edit the case definition to add one more custodian"""
        try:
            self.case_manager.open_overview_tab()
            self.case_manager.add_custodian_to_definition(
                "CaseDef_"+self.one_time_only_case,
                self.tcinputs['OTO_Add_Custodians']
            )
            self.log.info('Definition edited')
            self.admin_console.wait_for_completion()
            self.job_id=self.case_manager.submit_collection_job()
            self.index_copy_details = self.jobs.job_completion(self.job_id)
            if not 'Completed' == self.index_copy_details['Status']:
                exp = "Indexcopy job  not completed successfully"
                raise CVTestStepFailure(exp)
        except Exception:
            raise CVTestStepFailure('Error editing definition')

    @test_step
    def verify_one_time_only_case(self):
        """Verify that data is collected only once"""
        try:
            if self.emails_num != self.get_email_num(self.one_time_only_case):
                raise CVTestStepFailure(
                    'Data is collected more than once for "One time only"')
        except Exception:
            raise CVTestStepFailure(
                'Error verifying that data is collected only once')

    @test_step
    def create_continuous_client(self):
        """Create a case with datatype as 'Continuous'"""
        try:
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            self.case_manager.select_add_case()
            self.case_manager.enter_case_details(
                self.continuous_case,
                self.tcinputs['DataType'],
                'Continuous',
                self.tcinputs['C_Custodians'],
                self.tcinputs['DCPlan'],
                self.tcinputs['ServerPlan'],
                self.tcinputs['Keyword']
            )
            self.log.info('Case Added')
        except Exception:
            raise CVTestStepFailure("Error creating case")

    @test_step
    def verify_continuous_case(self):
        """Verify if the server plan is associated with the case"""
        try:
            if not self.ex_app_helper.is_client_associated_with_plan(
                    self.continuous_case, self.tcinputs['ServerPlan']):
                raise CVTestStepFailure('Case not associated with Server Plan')
        except Exception:
            raise CVTestStepFailure(
                'Error verifying whether plan is associated to the case')

    def run(self):
        """
        Testcase execution starts from here
        """
        try:
            self.init_tc()
            self.create_one_time_only_client()
            self.index_copy_details = self.case_manager.index_copy_job(case_name=self.one_time_only_case)
            self.get_one_time_only_emails()
            self.edit_one_time_only_definition()
            self.verify_one_time_only_case()
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            self.case_manager.delete_case(self.one_time_only_case)
            self.create_continuous_client()
            self.verify_continuous_case()
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            self.case_manager.delete_case(self.continuous_case)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)