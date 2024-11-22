# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Add Content Tab on Metallic

"""
import time
from selenium.webdriver.common.by import By
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.table import Rtable
from Web.Common.page_object import (
    WebAction,
    PageService
)


class VMContentSelection:
    """
    class for handling all the options on Content Selection Page
    """
    def __init__(self, wizard, admin_console, metallic_options):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.log = self.__admin_console.log
        self.metallic_options = metallic_options
        self.__wizard = wizard
        self.config()

    def config(self):

        self.add_content()
        if self.metallic_options.snap_backup:
            self.__enable_intellisnap()
        self.__wizard.click_next()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    def create_aws_vm_group(self):
        self.__admin_console.fill_form_by_id(element_id="name", value="automation-test")
        for vm in self.metallic_options.content_list:
            self.__admin_console.click_by_id(id="ADD_VIRTUALMACHINES")
            self.__admin_console.search_vm(vm)
            self.__admin_console.click_button("OK")
            time.sleep(10)

    @PageService()
    def add_content(self):
        """
        add the content to back up and restore
        """
        self.__wizard.fill_text_in_field(id='name', text=self.metallic_options.vm_group_name)
        self.log.info("adding the content for backup")
        self.delete_content()
        for vm in self.metallic_options.content_list:
            self.__select_content_category(content_category=self.metallic_options.content_category)
            self.__admin_console.wait_for_completion()
            if self.metallic_options.content_category == 'Content':
                self.vm_based_content(vm)
            else:
                vm = vm.strip()
                self.rule_based_content(vm)

    def delete_content(self):
        """
        delete the current content on vm-groups-content table on the page
        """
        content_table = Rtable(admin_console=self.__admin_console, id='addvmgroup-rules-content')
        if content_table.get_total_rows_count() != 0:
            content_table.select_all_rows()
            content_table.access_toolbar_menu('Delete')

    def vm_based_content(self, vm):
        """
        select the content by vm content
        """
        vm_content_dialog = RModalDialog(self.__admin_console, 'Add content')
        self.wait_for_elements("(//div[contains(text(),'Loading')] | //li[contains(text(),'Loading')])")
        vm_content_dialog.select_dropdown_values('vmBrowseView', [self.metallic_options.content_type])
        self.__admin_console.wait_for_completion()
        self.__admin_console.search_vm(vm)
        self.__admin_console.click_button("Save")
        self.__admin_console.wait_for_completion()

    def rule_based_content(self, vm):
        """
        select the content by rule
        """
        rule_content_dialog = RModalDialog(self.__admin_console, 'Add rule')
        rule_content_dialog.fill_text_in_field(element_id='rules[0].ruleName', text=vm)
        rule_content_dialog.click_button_on_dialog(text='Save')

    @WebAction()
    def __select_content_category(self, content_category='Content'):
        """
        select the category to add as content

        Returns:
            None
        """
        self.__wizard.click_button('Add')
        self.__admin_console.wait_for_completion()
        self.__wizard.select_dropdown_list_item(content_category)
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __enable_intellisnap(self):
        """
        Enable Intellisnap on VM Group while creation

        Returns:
            None
        """
        self.__wizard.enable_toggle('IntelliSnap')

    def wait_for_elements(self, elements_xpath):
        import time
        ele = self.__driver.find_elements(By.XPATH, elements_xpath)
        while len(ele):
            time.sleep(60)
            self.log.info("waiting for 1 min, for the loading of elements")
            ele = self.__driver.find_elements(By.XPATH, elements_xpath)
