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

    run()           --  run function of this test case
"""
import os
import time

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.GovernanceAppsPages.RequestManager import RequestManager
from Web.AdminConsole.GovernanceAppsPages.ReviewRequest import ReviewRequest
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep
from dynamicindex.utils.activateutils import ActivateUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of GDPR Feature"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.activateutils = ActivateUtils()
        self.testcaseutils = CVTestCase
        self.name = "Basic Acceptance Test for Delete Request in Request Manager in AdminConsole"
        self.tcinputs = {
            "IndexServerName": None,
            "ContentAnalyzer": None,
            "NameServerAsset": None,
            "HostNameToAnalyze": None,
            "FileServerDirectoryPath": None,
            "FileServerUserName": None,
            "FileServerPassword": None,
            "Approver": None,
            "Reviewer": None,
            "Requester": None
        }
        # Test Case constants
        self.inventory_name = None
        self.plan_name = None
        self.project_name = None
        self.file_server_display_name = None
        self.country_name = None
        self.request_name = None
        self.sensitive_entity = None
        self.sensitive_file = None
        self.adminconsole = None
        self.browser = None
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.request_manager = None
        self.review = None
        self.app = None
        self.gdpr_base = None
        self.explict_wait = None
        self.file_count_before_review = None
        self.entity_delimiter = "****"
        self.test_case_error = None
        self.explict_wait = 1 * 60

    def generate_sensitive_data(self):
        """
            Generate sensitive files with PII entities
        """
        self.activateutils.sensitive_data_generation(
            self.tcinputs['FileServerDirectoryPath'], number_files=20)

    def get_sensitive_file_details(self):
        """
            Get the sensitive file with entity
        """

        this_dir = os.path.dirname(os.path.realpath('__file__'))
        filename = os.path.join(this_dir, 'CompiledBins')
        database_file_path = "{0}\\Entity.db".format(filename)
        entities_dict = self.activateutils.db_get_entities_dict_from_sqllite(
            database_file_path)
        dict_used = entities_dict.pop('result')
        self.log.info(dict_used)
        __entity = ""
        __file = ""
        for i in range(len(dict_used)):
            __file = dict_used.__getitem__(i).get('FilePath')
            __entity = dict_used.__getitem__(i).get('Email')
            if __entity is not None:
                if self.entity_delimiter in __entity:
                    temp = __entity.split(self.entity_delimiter)
                    __entity = temp[0]
                    break
                else:
                    __entity = __entity
                    break

        self.sensitive_entity = __entity
        self.sensitive_file = __file

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.request_name = '{}_request'.format(self.id)
            self.inventory_name = '{}_inventory'.format(self.id)
            self.plan_name = '{}_plan'.format(self.id)
            self.project_name = '{}_project'.format(self.id)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login()
            self.navigator = self.admin_console.navigator
            self.request_manager = RequestManager(self.admin_console)
            self.review = ReviewRequest(self.admin_console)
            self.navigator.navigate_to_governance_apps()
            self.app = GovernanceApps(self.admin_console)
            self.gdpr_base = GDPR(self.admin_console, self.commcell, self.csdb)
            self.cleanup()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_inventory(self):
        """
            Create inventory with a nameserver
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_inventory_manager()
        self.gdpr_base.inventory_details_obj.add_inventory(
            self.inventory_name, self.tcinputs['IndexServerName'])

        self.gdpr_base.inventory_details_obj.add_asset_name_server(
            self.tcinputs["NameServerAsset"])
        self.admin_console.log.info("Sleeping for [%s]", self.explict_wait)
        time.sleep(self.explict_wait)
        if not self.gdpr_base.inventory_details_obj.wait_for_asset_status_completion(
                self.tcinputs['NameServerAsset']):
            raise CVTestStepFailure("Could not complete Asset Scan")

    @test_step
    def create_plan(self):
        """
            Create plan
        """

        self.navigator.navigate_to_plan()
        self.gdpr_base.plans_obj.create_data_classification_plan(self.plan_name, self.tcinputs[
            'IndexServerName'], self.tcinputs['ContentAnalyzer'],
                                                                 self.request_manager.constants.entities_list)

    @test_step
    def create_sda_project(self):
        """
            Create a project and run analysis
        """
        self.file_server_display_name = '{}_file_server'.format(self.id)
        self.country_name = 'United States'
        self.gdpr_base.testdata_path = self.tcinputs['FileServerDirectoryPath']
        self.gdpr_base.entities_list = self.request_manager.constants.entities_list
        self.gdpr_base.data_source_name = self.file_server_display_name
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_base.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name)
        self.gdpr_base.file_server_lookup_obj.select_add_data_source()
        self.gdpr_base.file_server_lookup_obj.add_file_server(
            self.tcinputs['HostNameToAnalyze'], 'Host name',
            self.file_server_display_name, self.country_name,
            self.tcinputs['FileServerDirectoryPath'],
            username=self.tcinputs['FileServerUserName'],
            password=self.tcinputs['FileServerPassword'], inventory_name=self.inventory_name)
        self.log.info("Sleeping for: '[%s]' seconds", self.explict_wait)
        time.sleep(self.explict_wait)
        if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name, timeout=60):
            raise CVTestStepFailure("Could not complete Data Source Scan")
        self.log.info("Sleeping for: '[%s]' seconds", self.explict_wait)
        time.sleep(self.explict_wait)
        self.file_count_before_review = self.gdpr_base.data_source_discover_obj. \
            get_total_number_after_crawl()

    @test_step
    def create_request(self):
        """Create a request in request manager"""
        _nsuccess = False
        self.navigator.navigate_to_governance_apps()
        self.app.select_request_manager()
        requester = self.tcinputs['Requester']
        entity_type = self.request_manager.constants.entities_list[2]
        entity = self.sensitive_entity
        request_type = self.request_manager.constants.DELETE
        _nsuccess = self.request_manager.create.add_request(self.request_name, requester,
                                                            entity_type,
                                                            entity,
                                                            request_type)
        if not _nsuccess:
            raise CVTestStepFailure(f"Request {self.request_name} creation failed")

    @test_step
    def configure_request(self):
        """Configure a request in request manager"""
        _nsuccess = False
        approver = self.tcinputs['Approver']
        reviewer = self.tcinputs['Reviewer']
        project_name = self.project_name
        _nsuccess = self.request_manager.configure.assign_reviewer_approver(self.request_name,
                                                                            approver,
                                                                            reviewer, project_name)
        if not _nsuccess:
            if not _nsuccess:
                raise CVTestStepFailure(f"Could not configure request {self.request_name}")

    @test_step
    def review_request(self):
        """Review a request in request manager"""
        self.review.review_approve_request(self.request_name, self.sensitive_file)

    @test_step
    def validate_request_operations(self):
        """
            Validate post request approval operations
        """
        self.navigator.navigate_to_jobs()
        job = self.review.fetch_request_job()
        __current__url = self.browser.driver.current_url
        __interaction_id = self.activateutils.get_workflow_interaction(self.commcell, job[0])
        __approve_url = "https://{0}/{1}&id={2}&interactionId=0&actionName=Approve".format(
            self.commcell.webconsole_hostname, self.request_manager.constants.approval_url_suffix,
            __interaction_id)
        self.log.info("Approval URL [%s]", __approve_url)
        self.browser.driver.get(__approve_url)
        time.sleep(self.explict_wait)
        self.browser.driver.get(__current__url)
        time.sleep(self.explict_wait)
        self.commcell.job_controller.get(job[0]).wait_for_completion()
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_base.file_server_lookup_obj.search_for_project(self.project_name)
        self.gdpr_base.data_source_discover_obj.navigate_to_project_details(self.project_name)
        self.gdpr_base.file_server_lookup_obj.select_data_source(self.file_server_display_name)
        self.log.info("Starting a full re-crawl of the datasource [%s]",
                      self.file_server_display_name)
        self.gdpr_base.data_source_discover_obj.select_details()
        self.gdpr_base.data_source_discover_obj.start_data_collection_job('full')
        self.navigator.navigate_to_governance_apps()
        self.gdpr_base.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_base.file_server_lookup_obj.navigate_to_project_details(
            self.project_name)
        if not self.gdpr_base.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name):
            raise Exception("Could not complete Data Source Scan")
        self.log.info("Sleeping for: '[%s]' seconds", self.explict_wait)
        time.sleep(self.explict_wait)
        file_count_after_review = self.gdpr_base.data_source_discover_obj. \
            get_total_number_after_crawl()
        if (int(self.file_count_before_review) - 1) != int(file_count_after_review):
            self.log.info(
                "Number of files before review [%s], "
                "Number of files after review [%s]", self.file_count_before_review,
                file_count_after_review)
            self.test_case_error = \
                ("Number of files before review [%s], number of files after review [%s]. "
                 "File deletion failed.", self.file_count_before_review, file_count_after_review)
        else:
            self.log.info(
                "Number of files before review [%s], "
                "Number of files after review [%s]", self.file_count_before_review,
                file_count_after_review)
            self.test_case_error = ""

    @test_step
    def cleanup(self):
        """
            Cleanup environment
        """
        self.navigator.navigate_to_governance_apps()
        self.app.select_request_manager()
        self.request_manager.delete.delete_request(self.request_name)
        self.gdpr_base.cleanup(
            self.project_name,
            self.inventory_name,
            self.plan_name, pseudo_client_name=self.file_server_display_name)

    def run(self):
        try:
            self.init_tc()
            self.generate_sensitive_data()
            self.get_sensitive_file_details()
            self.create_plan()
            self.create_inventory()
            self.create_sda_project()
            self.create_request()
            self.configure_request()
            self.review_request()
            self.validate_request_operations()
            self.cleanup()
            if "".__ne__(self.test_case_error):
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
