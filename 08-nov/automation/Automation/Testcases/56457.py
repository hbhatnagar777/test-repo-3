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
from Web.AdminConsole.Components.panel import ModalPanel
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.GovernanceAppsPages.CaseManager import CaseManager
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """Class for Verification of Job phases in Case Manager
    Collection Job with 'Continuous' data collection"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ('Verification of Job phases in Case Manager '
                     'Collection Job with "Continuous" data collection')
        self.data_type = 'Exchange mailbox'
        self.data_collection = 'Continuous'
        self.case_name = None
        self.custodians = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.activate = None
        self.case_manager = None
        self.jobs = None
        self.job_id = None
        self.emails_num = None
        self.index_copy_details = {}
        self.content_indexing_job_id = None
        self.reference_copy_job_id = None
        self.reference_copy_details = None
        self.content_indexing_details = None
        self.tcinputs = {
            "CaseName": None,
            "DCPlan": None,
            "ServerPlan": None,
            "Custodians": None,
            "Keyword": None
        }
        self.table = None
        self.modal_panel = None

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
            self.table = Table(self.admin_console)
            self.modal_panel = ModalPanel(self.admin_console)

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            self.case_name = self.tcinputs['CaseName'] + str(int(time.time()))
            self.custodians = self.tcinputs['Custodians']
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
    def verify_collection_job_submission(self):
        """Submits collection job"""
        try:
            self.case_manager.submit_collection_job()
            self.job_id = str(self.case_manager.get_index_copy_job_id())
            self.index_copy_details = self.jobs.job_completion(self.job_id)
            if not 'Completed' == self.index_copy_details['Status']:
                exp = "Indexcopy job  not completed successfully"
                raise CVTestStepFailure(exp)
        except Exception:
            raise CVTestStepFailure(
                "Error Verifying whether collection job has been submitted")

    @test_step
    def verify_job_triggering(self):
        """Verifying triggering of Index Copy, Reference Copy and CI jobs inline"""
        try:
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            if self.table.is_entity_present_in_column('Name', self.case_name):
                self.case_manager.select_case(self.case_name)
            self.case_manager.open_job_history()
            retry = 0
            self.table.apply_filter_over_column('Status', 'Completed')
            while retry <= 6:
                time.sleep(60)
                if int(self.table.get_total_rows_count()) >= 3:
                    self.reference_copy_job_id = int(
                        self.jobs.get_job_id_by_operation('Case Manager Reference Copy'))
                    self.content_indexing_job_id = int(
                        self.jobs.get_job_id_by_operation('Content indexing'))

                    self.jobs.access_job_by_id(self.reference_copy_job_id)
                    self.reference_copy_details = self.jobs.job_details()

                    self.jobs.access_job_by_id(self.content_indexing_job_id)
                    self.content_indexing_details = self.jobs.job_details()
                    break
                self.admin_console.refresh_page()
                retry += 1
            if (not self.content_indexing_job_id) or (
                    not self.reference_copy_job_id):
                raise CVTestStepFailure(
                    'Case Manager Reference Copy Job / Content Indexing Job did not complete. Please check the logs')
        except Exception:
            raise CVTestStepFailure(
                'Error verifying whether all jobs get triggered inline')

    @test_step
    def verify_index_copy_job(self):
        """Verification of Case Manager Index Copy Job"""
        try:
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            if self.table.is_entity_present_in_column('Name', self.case_name):
                self.case_manager.select_case(self.case_name)
            self.case_manager.open_search_tab()
            try:
                self.case_manager.click_search_button()
                self.emails_num = int(self.table.get_total_rows_count())
            except IndexError:
                self.emails_num = 0
            if int(self.reference_copy_details['Number of files transferred']) != self.emails_num:
                raise CVTestStepFailure(
                    'Verification of Index Copy Job Failed')
        except Exception:
            raise CVTestStepFailure('Verification of Index Copy Job Failed')

    @test_step
    def verify_reference_copy_job(self):
        """Verification of Case Manager Reference Copy Job"""
        if int(self.reference_copy_details['Number of files transferred']) != self.emails_num:
            raise CVTestStepFailure(
                'Verification of Reference Copy Job Failed')

    @test_step
    def verify_content_indexing_job(self):
        """Verification of Case Manager Content Indexing Job"""
        messages = (int(self.content_indexing_details['Number of files transferred']))
        if messages >= self.emails_num:
            raise CVTestStepFailure(
                'Verification of Content Indexing Job failed')

    def run(self):
        """
        Testcase execution starts from here
        """
        try:
            self.init_tc()
            self.create_case_manager_client()
            self.verify_collection_job_submission()
            self.verify_job_triggering()
            self.verify_index_copy_job()
            self.verify_reference_copy_job()
            self.verify_content_indexing_job()
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            self.case_manager.delete_case(self.case_name)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
