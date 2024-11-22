# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Test case for Billing: Volume Discounts with DP-X, VM-X and MBX SKU Validation
"""
from time import sleep
from typing import Dict

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

    DP_F_TB_SKU = ("DP_F_TB_UTL_59768", "SKU For Automation TC 59768","Capacity","Regular",["File System only VM","File System only Server"])
    DP_A_TB_SKU = ("DP_A_TB_UTL_59768", "SKU For Automation TC 59768", "Capacity", "Regular", "Application Server")
    VM_F_TB_SKU = ("VM_F_TB_UTL_59768","SKU For Automation TC 59768","Capacity","Regular","VM only")
    VM_A_TB_SKU = ("VM_A_TB_UTL_59768","SKU For Automation TC 59768","Capacity","Regular","Advanced VM")

    SKU_LIST = [DP_F_TB_SKU, DP_A_TB_SKU,VM_F_TB_SKU,VM_A_TB_SKU]

    CONTRACT_LIST = [(DP_F_TB_SKU[0],"Capacity",0,5,0,0,"No"),
                    (DP_A_TB_SKU[0],"Capacity",0,10,0,0,"Yes"),
                    (VM_F_TB_SKU[0],"Capacity",0,5,0,0,"No"),
                    (VM_A_TB_SKU[0],"Capacity",0,15,0,0,"Yes")]

    SKU_DESCRIPTION = "SKU For Test Case 59768"
    BILLING_GROUP_NAME = "Billing Group For Test Case 59768"
    BILLING_GROUP_DESCRIPTION = "Test Case 59768"
    BILLING_GROUP_CURRENCY = "USD"

class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Volume Discounts with DP-X, VM-X and MBX SKU Validation"
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

        for x in range(len(InputConstants.SKU_LIST)):
            if self.sku_page.is_sku_exists(InputConstants.SKU_LIST[x][0]):
                sleep(5)
                self.sku_page.delete_sku(InputConstants.SKU_LIST[x][0])
                self.log.info("Deleted sku:%s ", InputConstants.SKU_LIST[x][0])

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
        self.navigator.goto_contract_management()
        self.billing_group_options.access_manage_billing_groups()
        self.billing_group_options.access_manage_skus()

        for x in range(len(InputConstants.SKU_LIST)):
            self.webconsole.clear_all_notifications()
            sku = self.sku_page.add_sku()
            self.log.info("Creating sku:%s ", InputConstants.SKU_LIST[x][0])
            sku.set_sku_name(InputConstants.SKU_LIST[x][0])
            sku.set_description(InputConstants.SKU_LIST[x][1])
            sku.select_counting_type()
            if InputConstants.SKU_LIST[x][0] == "DP_F_TB_UTL_59768" :
                sku.add_license_types([InputConstants.SKU_LIST[x][4][0]])
                sku.add_license_types([InputConstants.SKU_LIST[x][4][1]])
            else :
                sku.add_license_types([InputConstants.SKU_LIST[x][4]])

            sku.save()
            notifications = self.webconsole.get_all_unread_notifications()
            if 'SKU saved successfully' not in notifications:
                self.log.error("Existing Notification:%s", notifications)
                self.log.error("Expected notification:SKU saved successfully")
                raise CVTestStepFailure("Failure to create sku: %s", InputConstants.SKU_LIST[x][0])

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

        for x in range(len(InputConstants.CONTRACT_LIST)):
            self.log.info("Iteration Number: %d  |  Adding SKU %s to contract ", x, InputConstants.CONTRACT_LIST[x][0])
            billing_group_panel.select_sku(InputConstants.CONTRACT_LIST[x][0])
            billing_group_panel.set_base_line(InputConstants.CONTRACT_LIST[x][2])
            billing_group_panel.set_unit_price(InputConstants.CONTRACT_LIST[x][3])
            billing_group_panel.set_lower_limit(InputConstants.CONTRACT_LIST[x][4])
            billing_group_panel.set_upper_limit(InputConstants.CONTRACT_LIST[x][5])
            billing_group_panel.include_in_volume_discount(InputConstants.CONTRACT_LIST[x][6])
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
        self.log.info("Associating Commcell Group: %s with Billing Group: %s",
                      self.commcell_group_name, InputConstants.BILLING_GROUP_NAME)
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
        self.log.info("Associated billing group: %s with Billing Group: %s", self.commcell_group_name,
                      InputConstants.BILLING_GROUP_NAME)

    @test_step
    def add_volume_discount_to_contract(self):
        """
        Edit Association and Add Volume Discount to Contract
        """
        self.log.info("Adding Volume Discount to Contract for Commcell Group: %s with Billing Group: %s",
                      self.commcell_group_name, InputConstants.BILLING_GROUP_NAME)
        self.navigator.goto_contract_management()
        self.billing_group_association = billinggroups.BillingGroupAssociation(self.webconsole)
        self.webconsole.clear_all_notifications()
        self.billing_group_association.edit_association(self.commcell_group_name,
                                                 InputConstants.BILLING_GROUP_NAME)
        self.webconsole.wait_till_loadmask_spin_load()
        notifications = self.webconsole.get_all_unread_notifications()
        if 'Association updated successfully' not in notifications:
            self.log.error("Existing Notification:%s", notifications)
            self.log.error("Expected notification:Association updated successfully")
            raise CVTestStepFailure("Failure to Add Volume Discount to Contract")
        self.log.info("Added Volume Discount for Commcell Group: %s and Billing Group: %s", self.commcell_group_name,
                      InputConstants.BILLING_GROUP_NAME)


    def _verify_downloaded_file(self):
        self.log.info("Verifying royalty report file is exported")
        self.utils.wait_for_file_to_download("pdf")
        self.log.info("Verifying size of exported file")
        self.utils.validate_tmp_files(ends_with="pdf",count=1,min_size=100)

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
        #royalty_report.generate_royalty_report(self.commcell_group_name, RoyaltyReport.BDR)
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
            self.add_volume_discount_to_contract()
            self.generate_royalty_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
