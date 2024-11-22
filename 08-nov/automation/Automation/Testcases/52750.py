# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Test case to create Create Service Provider and generate report

"""

from time import sleep


from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Billing import serviceprovider
from Web.WebConsole.Reports.Billing.common import BillingGroupOptions
from Web.WebConsole.Reports.Billing.common import BillingConstants
from Web.WebConsole.Reports.Billing.common import RoyaltyReport
from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils


class InputConstants:
    """
      Billing constants used in this test case.
    """
    SERVICE_PROVIDER_NAME = "Automation_Service_Provider"
    SERVICE_PROVIDER_DESCRIPTION = "Used by automation for test case"
    MINIMUM_FEE = "20"
    USE_AS_PURCHASE_ORDER = "Yes"


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Verify creating service provider and generate report"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.METRICSREPORTS
        self.feature = self.features_list.WEBCONSOLE
        self.show_to_user = False
        self.log = logger.get_log()
        self.tcinputs = {"CommcellGroupName": None}
        self.browser = None
        self.webconsole = None
        self.reports = None
        self.navigator = None
        self.billing_group_options = None
        self.service_provider = None
        self.service_provider_panel = None
        self.manage_service_provider = None
        self.associate = None
        self.commcell_group_name = None
        self.utils = TestCaseUtils(self)

    def _delete_association(self):
        """
        Delete association
        """
        self.navigator.goto_contract_management()
        self.billing_group_options.access_service_provider_royalty_report()
        if self.manage_service_provider.is_service_provider_exists(InputConstants.
                                                                   SERVICE_PROVIDER_NAME):
            self.service_provider.delete_association(InputConstants.
                                                     SERVICE_PROVIDER_NAME)

    def _delete_service_provider(self):
        """
        Delete Service provider
        """
        self.billing_group_options.access_manage_service_providers()
        if self.manage_service_provider.is_service_provider_exists(InputConstants.
                                                                   SERVICE_PROVIDER_NAME):
            self.manage_service_provider.delete_service_provider(InputConstants.
                                                                 SERVICE_PROVIDER_NAME)

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.commcell_group_name = self.tcinputs["CommcellGroupName"].split(',')
            self.utils.reset_temp_dir()
            download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory:%s", download_directory)
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = Navigator(self.webconsole)
            self.billing_group_options = BillingGroupOptions(self.webconsole)
            self.service_provider = serviceprovider.ServiceProvider(self.webconsole)
            self.manage_service_provider = serviceprovider.ManageServiceProvider(self.webconsole)
            self.service_provider_panel = serviceprovider.ServiceProviderPanel(self.webconsole)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def create_service_provider(self):
        """
         ServiceProvider will be created and verify ServiceProvider is created
        """
        self.webconsole.clear_all_notifications()
        self.manage_service_provider.add_service_provider(InputConstants.SERVICE_PROVIDER_NAME,
                                                          InputConstants.
                                                          SERVICE_PROVIDER_DESCRIPTION,
                                                          self.commcell_group_name)
        notifications = self.webconsole.get_all_unread_notifications()
        if 'Service Provider saved successfully' not in notifications:
            self.log.error("Existing Notification:%s", notifications)
            self.log.error("Expected notification:Service Provider saved successfully")
            raise CVTestStepFailure("Failure to create Service Provider: %s"
                                    % InputConstants.SERVICE_PROVIDER_NAME)
        self.log.info("Service Provider created successfully")

    @test_step
    def associate_service_provider(self):
        """
          Associate Service Provider
        """
        self.billing_group_options.access_service_provider_royalty_report()
        self.webconsole.clear_all_notifications()
        self.service_provider.associate(InputConstants.SERVICE_PROVIDER_NAME,
                                        InputConstants.MINIMUM_FEE,
                                        BillingConstants.BILLING_CYCLE_MONTHLY)
        sleep(4)
        self.webconsole.wait_till_loadmask_spin_load()
        notifications = self.webconsole.get_all_unread_notifications()
        if 'Association added successfully' not in notifications:
            self.log.error("Existing Notification:%s", notifications)
            self.log.error("Expected notification:Association added successfully")
            raise CVTestStepFailure("Failure to associate Service Provider")
        self.log.info("Associated Service Provider:%s ", InputConstants.SERVICE_PROVIDER_NAME)

    def cleanup_test_case_configuration(self):
        """
        Clean up existing configuration
        """
        self.log.info("cleaning up previous tc configuration")
        self._delete_association()
        self._delete_service_provider()

    def _verify_downloaded_file(self):
        self.log.info("Verifying royalty report file is exported")
        self.utils.wait_for_file_to_download("pdf")
        self.log.info("verified exported file")

    @test_step
    def generate_royalty_report(self):
        """
        Generates royalty report
        """
        self.log.info("Generating royalty report for the Service Provider association %s",
                      InputConstants.SERVICE_PROVIDER_NAME)
        royalty_report = RoyaltyReport(self.webconsole)
        royalty_report.generate_royalty_report(InputConstants.SERVICE_PROVIDER_NAME,
                                               RoyaltyReport.PDF)
        self._verify_downloaded_file()
        self.log.info("Generated royalty report successfully.")

    def run(self):
        try:
            self.init_tc()
            self.cleanup_test_case_configuration()
            self.create_service_provider()
            self.associate_service_provider()
            self.generate_royalty_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
