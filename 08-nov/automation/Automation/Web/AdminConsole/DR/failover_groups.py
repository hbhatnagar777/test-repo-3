# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Failover Groups page of the AdminConsole

"""
from time import sleep

from Web.AdminConsole.Components.browse import Browse
from Web.AdminConsole.Components.table import CVTable, Table
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.panel import (PanelInfo, DropDown, ModalPanel)
from Web.AdminConsole.Components.dialog import ModalDialog


class FailoverGroup:
    """Class for Replication Groups Page"""
    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__table = Table(self.__admin_console)
        self.__cvtable = CVTable(self.__admin_console)
        self.__browse = Browse(self.__admin_console)
        self.__drop_down = DropDown(self.__admin_console)
        self.__dialog = ModalDialog(self.__admin_console)

        self.__admin_console.load_properties(self, unique=True)
        self.__label = self.__admin_console.props[self.__class__.__name__]

    @PageService()
    def add_failover_group(self, group_name: str, source_hypervisor: str, source_vms: list = None):
        """Add the Failover Group"""
        self.__admin_console.navigator.navigate_to_failover_groups()
        self.__admin_console.access_menu("Add failover group")
        self.__admin_console.click_by_id(1)

        self.__admin_console.fill_form_by_id('groupName', group_name)
        self.__drop_down.select_drop_down_values(0, [source_hypervisor])

        for instance in source_vms:
            self.__cvtable.search_for(instance)
            self.__cvtable.select_checkbox(1)

        self.__admin_console.click_button(id="failoverGroupCreate_button_#4312")

    @PageService()
    def get_column_details(self,
                           column_name: str = 'Name',
                           failover_group: str = None,
                           view_tf: bool = False,
                           navigate: bool = False):
        """Verifies the details of the failover group"""
        if navigate:
            self.__admin_console.navigator.navigate_to_failover_groups()
            self.__table.access_link(failover_group)

        if view_tf:
            self.__admin_console.access_menu_from_dropdown('View test failover VMs')

        return list(set(self.__cvtable.get_column_data(column_name)))

    @PageService()
    def get_values_from_table(self, source_vms: list = None):
        """Verifies the details of the failover group"""
        return self.__cvtable.get_values_from_table(source_vms)

    @PageService()
    def delete_failover_group(self, failover_group: str):
        """Deletes the Failover Group"""
        self.__admin_console.navigator.navigate_to_failover_groups()

        if self.__admin_console.check_if_entity_exists('link', failover_group):
            self.__table.access_link(failover_group)
            self.__admin_console.access_menu('Delete')
            self.__admin_console.click_button(value="Yes")
            self.__admin_console.wait_for_completion()
            sleep(30)
            self.__admin_console.refresh_page()

        if self.__admin_console.check_if_entity_exists('link', failover_group):
            raise CVWebAutomationException("Replication group [%s] not found in replications "
                                           "group page")

    @PageService()
    def run_test_failover(self, failover_group: str):
        """Runs the Test Failover operation"""
        self.__admin_console.navigator.navigate_to_failover_groups()
        self.__table.access_link(failover_group)
        self.__admin_console.access_menu_from_dropdown('Test failover')
        self.__admin_console.click_button(id="modal_button_#6362")
        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def get_cloned_vm_names(self, failover_group: str, navigate: bool = True):
        """View the test failover VMs associated with the Failover Group"""
        return self.get_column_details("Name", failover_group, view_tf=True, navigate=navigate)

    @PageService()
    def get_vm_names(self, failover_group: str = None, navigate: bool = False):
        """View the test failover VMs associated with the Failover Group"""
        return self.get_column_details("Name", failover_group, navigate=navigate)

    @PageService()
    def get_vm_sync_statuses(self, failover_group: str, navigate: bool = False):
        """View the test failover VMs associated with the Failover Group"""
        return self.get_column_details("Sync status", failover_group, navigate=navigate)

    @PageService()
    def run_testboot(self, failover_group: str):
        """Runs the Failover operation"""
        self.__admin_console.navigator.navigate_to_failover_groups()
        self.__table.access_link(failover_group)
        self.__admin_console.access_menu_from_dropdown(self.__label['label.testBoot'])
        self.__dialog.click_submit()
        return self.__admin_console.get_jobid_from_popup()
