# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Test case to create sku, create billing group, associate billing group, and generate royalty
report.
"""
from time import sleep

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Billing import billinggroups
from Web.WebConsole.Reports.Billing import skus
from Web.WebConsole.Reports.Billing.common import BillingGroupOptions
from Web.WebConsole.Reports.Billing.common import RoyaltyReport
from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils


class InputConstants:
    """
    Billing constants used in this test case.
    """
    SKU_NAME = "Automation_sku_tc_50801"
    SKU_DESCRIPTION = "Used by automation for test case 50801"
    SKU_LICENSE_TYPE = "Server File System"
    BILLING_GROUP_NAME = "Automation billing group tc 50801"
    BILLING_GROUP_DESCRIPTION = "Automation billing groups description tc 50801"
    BILLING_GROUP_CURRENCY = "USD"
    BASE_LINE = "20"
    UNIT_PRICE = "10"
    LOWER_LIMIT = "0"


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Verify creating sku, creating billing group, generate royalty report"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.METRICSREPORTS
        self.feature = self.features_list.WEBCONSOLE
        self.show_to_user = False
        self.log = logger.get_log()
        self.tcinputs = {
            "CommcellGroupName": None
        }
        self.browser = None
        self.webconsole = None
        self.reports = None
        self.navigator = None
        self.manage_billing_groups = None
        self.sku_page = None
        self.billing_group_options = None
        self.manage_billing_groups = None
        self.billing_group_association = None
        self.utils = TestCaseUtils(self)
        self.commcell_group_name = None

    def _delete_association(self):
        """
        Delete association
        """
        self.log.info("Deleting association if already exists")
        self.navigator.goto_contract_management()
        if self.billing_group_association.is_association_exists(self.commcell_group_name):
            self.billing_group_association.delete_association(self.commcell_group_name)

    def _delete_billing_group(self):
        """
        Delete billing group
        """
        self.log.info("Deleting billing group is already exists")
        self.navigator.goto_contract_management()
        self.billing_group_options.access_manage_billing_groups()
        if self.manage_billing_groups.is_billing_group_exists(InputConstants.BILLING_GROUP_NAME):
            self.manage_billing_groups.delete_billing_group(InputConstants.BILLING_GROUP_NAME)
            self.webconsole.wait_till_load_complete()

    def _delete_sku(self):
        """
        Delete sku
        """
        self.log.info("Deleting sku if already exists")
        self.billing_group_options.access_manage_skus()
        if self.sku_page.is_sku_exists(InputConstants.SKU_NAME):
            self.sku_page.delete_sku(InputConstants.SKU_NAME)

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.commcell_group_name = self.tcinputs["CommcellGroupName"]
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
            self.manage_billing_groups = billinggroups.ManageBillingGroups(self.webconsole)
            self.billing_group_association = billinggroups.BillingGroupAssociation(self.webconsole)
            self.sku_page = skus.ManageSKU(self.webconsole)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def create_sku(self):
        """
        Sku will be created and verify sku is created
        """
        self.log.info("Creating sku:%s", InputConstants.SKU_NAME)
        self.navigator.goto_contract_management()
        self.billing_group_options.access_manage_billing_groups()
        self.billing_group_options.access_manage_skus()
        self.webconsole.clear_all_notifications()
        sku = self.sku_page.add_sku()
        sku.set_sku_name(InputConstants.SKU_NAME)
        sku.set_description(InputConstants.SKU_DESCRIPTION)
        sku.select_counting_type()
        sku.add_license_types([InputConstants.SKU_LICENSE_TYPE])
        sku.save()
        notifications = self.webconsole.get_all_unread_notifications()
        if 'SKU saved successfully' not in notifications:
            self.log.error("Existing Notification:%s", notifications)
            self.log.error("Expected notification:SKU saved successfully")
            raise CVTestStepFailure("Failure to create sku: %s", InputConstants.SKU_NAME)
        self.log.info("Sku created successfully")

    @test_step
    def create_billing_group(self):
        """
        Create billing group and verify its created
        """
        self.log.info("Creating billing group:%s", InputConstants.BILLING_GROUP_NAME)
        self.navigator.goto_contract_management()
        self.billing_group_options.access_manage_billing_groups()
        self.webconsole.clear_all_notifications()
        billing_group_panel = self.manage_billing_groups.access_add_billing_group()
        billing_group_panel.set_billing_group_name(InputConstants.BILLING_GROUP_NAME)
        billing_group_panel.set_billing_group_description(InputConstants.BILLING_GROUP_DESCRIPTION)
        billing_group_panel.select_currency(InputConstants.BILLING_GROUP_CURRENCY)
        billing_group_panel.select_sku(InputConstants.SKU_NAME)
        billing_group_panel.set_base_line(InputConstants.BASE_LINE)
        billing_group_panel.set_unit_price(InputConstants.UNIT_PRICE)
        billing_group_panel.set_lower_limit(InputConstants.LOWER_LIMIT)
        billing_group_panel.add_sku_price()
        billing_group_panel.save()
        notifications = self.webconsole.get_all_unread_notifications()
        if 'Billing group saved successfully' not in notifications:
            self.log.error("Existing Notification:%s", notifications)
            self.log.error("Expected notification:Billing group saved successfully")
            raise CVTestStepFailure("Failure to create Billing group: %s",
                                    InputConstants.BILLING_GROUP_NAME)
        self.log.info("Billing group created successfully: %s", InputConstants.BILLING_GROUP_NAME)

    @test_step
    def associate_commcell_group_and_billing_group(self):
        """
        Associate commcell group and billing group
        """
        self.log.info("Associating commcell group :%s with sku name:%s",
                      self.commcell_group_name, InputConstants.SKU_NAME)
        self.navigator.goto_contract_management()
        self.billing_group_association = billinggroups.BillingGroupAssociation(self.webconsole)
        self.webconsole.clear_all_notifications()
        self.billing_group_association.associate(self.commcell_group_name,
                                                 InputConstants.BILLING_GROUP_NAME)
        sleep(4)
        self.webconsole.wait_till_loadmask_spin_load()
        notifications = self.webconsole.get_all_unread_notifications()
        if 'Association added successfully' not in notifications:
            self.log.error("Existing Notification:%s", notifications)
            self.log.error("Expected notification:Association added successfully")
            raise CVTestStepFailure("Failure to associate commcell group and billing group")
        self.log.info("Associated billing group:%s with sku:%s", self.commcell_group_name,
                      InputConstants.SKU_NAME)

    def _verify_downloaded_file(self):
        self.log.info("Verifying royalty report file is exported")
        self.utils.wait_for_file_to_download("pdf")
        self.log.info("verified exported file")

    @test_step
    def generate_royalty_report(self):
        """
        Generates royalty report
        """
        self.log.info("Generating royalty report for the association %s",
                      self.commcell_group_name)
        self.navigator.goto_contract_management()
        royalty_report = RoyaltyReport(self.webconsole)
        royalty_report.generate_royalty_report(self.commcell_group_name, RoyaltyReport.PDF)
        self._verify_downloaded_file()
        self.log.info("Generated royalty report successfully.")

    def cleanup_test_case_configuration(self):
        """
        Clean up existing configuration
        """
        self.log.info("cleaning up previous tc configuration")
        self._delete_billing_group()
        self._delete_sku()
        self._delete_association()

    def run(self):
        try:
            self.init_tc()
            self.cleanup_test_case_configuration()
            self.create_sku()
            self.create_billing_group()
            self.associate_commcell_group_and_billing_group()
            self.generate_royalty_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
