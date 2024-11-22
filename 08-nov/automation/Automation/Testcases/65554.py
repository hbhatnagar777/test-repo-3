# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

    create_tenant() -- creates a tenant

    initialize_compliancesearch() -- initializes objects for compliance search

    validate_compliancesearch() -- Validates the results of Content Search from Compliance Search

    validate_content_indexing() -- verifies content indexing triggered after backup or not

    run_backup_store_count() -- runs backup and stores the no of successfull backed up items
"""

import time

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.GovernanceAppsPages.ComplianceSearch import ComplianceSearch, CustomFilter
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Metallic_O365_Exchange_Acceptance:
    Verification of Content Search after CI job
    """
    teststep = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.app = None
        self.ci_items_cnt = None
        self.ex_object = None
        self.name = "Metallic_O365_Exchange_Acceptance for Verification of Content Search after CI job"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.hub_utils = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.hub_dashboard = None
        self.app_type = None
        self.users = None
        self.app_name = None
        self.service_catalogue = None
        self.bkp_items_cnt = -1
        self.ci_items_cnt = 0
        self.utils = TestCaseUtils(self)

    @teststep
    def initialize_compliancesearch(self):
        """Initialize Objects for Compliance search"""
        self.app = ComplianceSearch(self.admin_console)
        gov_app = GovernanceApps(self.admin_console)

        navigator = self.admin_console.navigator
        navigator.navigate_to_governance_apps()

        gov_app.select_compliance_search()
        self.app.click_search_button()

    @teststep
    def validate_compliancesearch(self):
        """
        Validate Content Search from Compliance search page
        """
        try:
            custom_filter = CustomFilter(self.admin_console)
            custom_filter.apply_custom_filters_with_search(
                {"Client name": [self.app_name]})
        except Exception as ex:
            self.log.info(ex)
            self.log.info(f"Failed to filter with client name, check if the client is created")

        totalcount = self.app.get_total_rows_count()

        if int(totalcount) != int(self.tcinputs['ExpectedCount']):
            raise CVTestStepFailure(f'Compliance search count mismatch')
        else:
            self.log.info(f'Compliance Search count matched.')

        searchcount = self.app.get_total_rows_count(self.tcinputs['SearchKeyword'])

        if int(searchcount) != int(self.tcinputs['ExpectedSearchCount']):
            raise CVTestStepFailure(f'Compliance search ContentSearch count mismatch')
        else:
            self.log.info(f'Compliance Search count matched.')

    @teststep
    def verify_backup_and_ci_count(self):
        """
            Compares the CI items count with Backup items count
        """
        if self.ci_items_cnt != self.bkp_items_cnt:
            raise CVTestStepFailure(
                f'Backup Items[{self.bkp_items_cnt}] and CI Items[{self.ci_items_cnt}] -- Count Mismatch')
        else:
            self.log.info(f'Backup Items[{self.bkp_items_cnt}] and CI Items[{self.ci_items_cnt}] -- Count Matched!')

    @teststep
    def run_backup_store_count(self):
        """
            Run backup for client and store count for validation
        """
        try:
            self.app_name = self.office365_obj.get_app_name()
            self.office365_obj.search_and_goto_app(self.app_name)
            self.office365_obj.add_user(self.users, plan=self.tcinputs['O365_Plan'])
            bkp_job_details = self.office365_obj.run_backup()
            self.bkp_items_cnt = int(bkp_job_details['Successful messages'])
            time.sleep(30)
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def setup(self):
        self.tenant_user_name = self.tcinputs['tenant_user_name']
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tenant_user_name,
                                 self.tcinputs['tenant_password'])
        self.service = HubServices.office365
        self.app_type = O365AppTypes.exchange
        self.navigator = self.admin_console.navigator
        self.users = self.tcinputs['Users'].split(",")
        self.app_name = f"{self.tcinputs['Name']}_{str(int(time.time()))}"
        self.log.info("Creating an object for office365 helper")
        is_react = False
        if self.inputJSONnode['commcell']['isReact'] == 'true':
            is_react = True
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react)

    def run(self):
        """Main function for test case execution"""
        try:
            self.navigator.navigate_to_office365()
            self.office365_obj.create_office365_app(name=self.app_name,
                                                    global_admin=self.tcinputs['GlobalAdmin'],
                                                    password=self.tcinputs['Password'])
            self.run_backup_store_count()
            self.ci_items_cnt = self.office365_obj.validate_content_indexing(self.app_name)
            self.verify_backup_and_ci_count()
            self.initialize_compliancesearch()
            self.validate_compliancesearch()
            self.navigator.navigate_to_office365()
            self.office365_obj.delete_office365_app(self.app_name)
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
