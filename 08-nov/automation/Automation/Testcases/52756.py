# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Test case to create Create Partner and generate report

"""

from time import sleep

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Billing import partners
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
    PARTNER_NAME = "Automation_Partner"
    PARTNER_DESCRIPTION = "Used by automation for test case"
    DISCOUNT_PERCENTAGE = "20"
    USE_AS_PURCHASE_ORDER = "Yes"


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Verify creating Partner and generate report"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.METRICSREPORTS
        self.feature = self.features_list.WEBCONSOLE
        self.show_to_user = False
        self.log = logger.get_log()
        self.tcinputs = {
            "ServiceProviderName": None
        }
        self.browser = None
        self.webconsole = None
        self.reports = None
        self.navigator = None
        self.billing_group_options = None
        self.manage_partners = None
        self.partners_association = None
        self.partner_panel = None
        self.associate = None
        self.utils = TestCaseUtils(self)
        self.service_provider = None

    def _delete_partner(self):
        """
        Delete partner
        """
        self.billing_group_options.access_manage_partner()
        if self.manage_partners.is_partner_exists(InputConstants.PARTNER_NAME):
            self.manage_partners.delete_partner(InputConstants.PARTNER_NAME)

    def _delete_partner_association(self):
        """
        Delete Partner association
        """
        self.navigator.goto_contract_management()
        self.billing_group_options.access_partner_royalty_reports()
        if self.manage_partners.is_partner_exists(InputConstants.PARTNER_NAME):
            self.partners_association.delete_partner_association(InputConstants.PARTNER_NAME)

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
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
            self.partners_association = partners.PartnersAssociation(self.webconsole)
            self.manage_partners = partners.ManagePartners(self.webconsole)
            self.partner_panel = partners.PartnerPanel(self.webconsole)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def create_partner(self):
        """
         Partner will be created and verify partner is created
        """
        self.webconsole.clear_all_notifications()
        self.manage_partners.add_partner(InputConstants.PARTNER_NAME,
                                         InputConstants.PARTNER_DESCRIPTION,
                                         [self.tcinputs["ServiceProviderName"]])
        notifications = self.webconsole.get_all_unread_notifications()
        if 'Partner saved successfully' not in notifications:
            self.log.error("Existing Notification:%s", notifications)
            self.log.error("Expected notification:Partner saved successfully")
            raise CVTestStepFailure("Failure to create Partner: %s" % InputConstants.PARTNER_NAME)
        self.log.info("Partner created successfully")

    def associate_partner(self):
        """
          Associate Partner
        """
        self.billing_group_options.access_partner_royalty_reports()
        self.webconsole.clear_all_notifications()
        self.partners_association.associate(InputConstants.PARTNER_NAME,
                                            InputConstants.DISCOUNT_PERCENTAGE,
                                            BillingConstants.BILLING_CYCLE_MONTHLY)
        sleep(4)
        self.webconsole.wait_till_loadmask_spin_load()
        notifications = self.webconsole.get_all_unread_notifications()
        if 'Association added successfully' not in notifications:
            self.log.error("Existing Notification:%s", notifications)
            self.log.error("Expected notification:Association added successfully")
            raise CVTestStepFailure("Failure to associate Partner")
        self.log.info("Associated Partner:%s ", InputConstants.PARTNER_NAME)

    def cleanup_test_case_configuration(self):
        """
        Clean up existing configuration
        """
        self.log.info("cleaning up previous tc configuration")
        self._delete_partner_association()
        self._delete_partner()

    def _verify_downloaded_file(self):
        self.log.info("Verifying royalty report file is exported")
        self.utils.wait_for_file_to_download("pdf")
        self.log.info("verified exported file")

    def generate_royalty_report(self):
        """
        Generates royalty report
        """
        self.log.info("Generating royalty report for the Partner association %s",
                      InputConstants.PARTNER_NAME)
        royalty_report = RoyaltyReport(self.webconsole)
        royalty_report.generate_royalty_report(InputConstants.PARTNER_NAME,
                                               RoyaltyReport.PDF)
        self._verify_downloaded_file()
        self.log.info("Generated royalty report successfully.")

    def run(self):
        try:
            self.init_tc()
            self.cleanup_test_case_configuration()
            self.create_partner()
            self.associate_partner()
            self.generate_royalty_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
