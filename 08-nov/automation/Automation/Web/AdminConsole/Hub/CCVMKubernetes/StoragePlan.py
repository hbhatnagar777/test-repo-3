# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Plan Tab on Metallic

"""
import time
from selenium.webdriver.common.by import By
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Helper.VSAMetallicHelper import VSAMetallicHelper
from Web.AdminConsole.Hub.constants import CCVMKubernetesTypes
from Web.AdminConsole.Hub.utils import Utils
from Web.Common.page_object import (
    PageService, WebAction
)


class StoragePlan:
    """
    class for the Plan Page
    """

    def __init__(self, wizard, admin_console, metallic_options):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.utils = Utils(admin_console)
        self.log = self.__admin_console.log
        self.__wizard = wizard
        self.metallic_options = metallic_options
        self.plan_dialog = RModalDialog(self.__admin_console, title='Create server backup plan')
        self.config()

    def config(self):
        if self.metallic_options.opt_existing_plan:
            self.select_existing_plan()
        else:
            self.create_new_plan()
        self.__wizard.click_next()

    @PageService()
    def select_existing_plan(self):
        """
        Select the existing plan from the options
        Returns:
            None
        """
        self.log.info("selecting existing plan named {}".format(self.metallic_options.opt_existing_plan))
        if self.is_plan_selected(self.metallic_options.opt_existing_plan):
            pass
        else:
            self.__wizard.select_plan(plan_name=self.metallic_options.opt_existing_plan)

    @WebAction()
    def is_plan_selected(self, plan_name):
        """
        check whether the plan is selected or not
        """
        xpath = f"//span[text()='{plan_name}']/ancestor::div[contains(@id,'planCard')]"
        ele = self.__driver.find_element(By.XPATH, xpath)
        self.log.info(ele.get_attribute('class'))
        if 'selectedPlan' in plan_name:
            return 1
        return 0

    @PageService()
    def create_new_plan(self):
        """
        Create a new plan
        """
        self.log.info("Creating a new plan")
        self.__wizard.click_add_icon()

        self.plan_dialog.fill_text_in_field('planNameInputFld', self.metallic_options.opt_new_plan)
        plan_id = 'default'
        if self.metallic_options.one_month_plan:
            plan_id = 'default'
        self.plan_dialog.select_radio_by_id(plan_id)
        self.metallic_options.custom_plan = None
        if self.metallic_options.custom_plan:
            self.plan_dialog.fill_text_in_field('retentionSnap', self.metallic_options.snap_retention)
            self.__wizard.select_drop_down_values('retentionPeriodUnit',
                                                  [self.metallic_options.cloud_retention_unit])
            self.plan_dialog.fill_text_in_field('retentionPeriod', self.metallic_options.cloud_retention)
            self.__wizard.select_drop_down_values('backupFrequencyUnit',
                                                  [self.metallic_options.backup_frequency_unit])
            self.plan_dialog.fill_text_in_field('backupFrequency', self.metallic_options.backup_frequency)

        self.plan_dialog.click_submit()
        self.retry_plan_submission()
        self.metallic_options.opt_existing_plan = self.metallic_options.opt_new_plan
        self.__admin_console.wait_for_completion()

    def retry_plan_submission(self):
        """
        retry submitting the plan
        """
        try:
            title = self.plan_dialog.title()
            if title == 'Create server backup plan':
                self.log.info('sleeping for 2 min and retry plan submission')
                time.sleep(120)
                self.plan_dialog.click_submit()
                self.__admin_console.check_error_message()
        except Exception as exp:
            self.log.info("this is a soft error")
            self.log.warning(exp)