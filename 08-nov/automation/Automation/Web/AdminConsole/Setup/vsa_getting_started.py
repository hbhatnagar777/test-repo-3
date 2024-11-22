from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to Virtualization getting started page
Virtualization : This class provides methods for Virtualization configuration

Virtualization
==============

    add_hypervisor()        -- To add a new VMware vCenter hypervisor

    add_vm_group()          -- To add a new VM group

    run_backup()            -- To run first Backup

"""

from Web.Common.page_object import PageService


class Virtualization:
    """
    Class for virtualization getting started page in Admin console

    """
    def __init__(self, admin_console):
        self.admin_console = admin_console
        self.driver = self.admin_console.driver
        self.log = self.admin_console.log

    @PageService(hide_args=True)
    def add_hypervisor(
            self,
            hostname=None,
            hypervisor_name=None,
            username=None,
            password=None):
        """
        To add a new VMware vCenter hypervisor

        Args:
            hostname        (str)   -- Full hostname of the machine

            hypervisor_name (str)   -- Name of the hypervisor machine

            username        (str)   -- username to access the machine

            password        (str)   -- Password for accessing the machine

        """
        try:
            self.admin_console.cv_single_select('Select vendor', "VMware vCenter")
        except:
            self.admin_console.select_value_from_dropdown("vendorType", "VMware vCenter")
        self.admin_console.fill_form_by_id('hostname', hostname)
        self.admin_console.fill_form_by_id('serverName', hypervisor_name)
        self.admin_console.fill_form_by_id('vsUserName', username)
        self.admin_console.fill_form_by_id('vsPassword', password)

        # To click on the save button
        self.driver.find_element(By.XPATH, '//span[text()="Save"]/..').click()
        self.admin_console.wait_for_completion()

        # To check if there is any error message
        self.admin_console.check_error_message()

    @PageService()
    def add_vm_group(
            self,
            group_name=None,
            virtual_machines=None):
        """
        To add a new VM group

        Args:
            group_name              (str)   -- Name for the VM group

            virtual_machines        (list)  -- List of virtual_machines to select

        """
        self.admin_console.fill_form_by_id('name', group_name)

        for machine in virtual_machines:
            self.admin_console.search_vm(machine)

        self.admin_console.submit_form()

        # To check for error messages
        self.admin_console.check_error_message()

    @PageService()
    def run_backup(self):
        """
        To run first Backup

        """
        self.admin_console.click_button('Backup now')
