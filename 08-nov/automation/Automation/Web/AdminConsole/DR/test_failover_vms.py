# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the page services for working with Test failover VMs page on the Command center
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List

from collections import defaultdict
from DROrchestration.DRUtils.DRConstants import TimePeriod
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import PageService

if TYPE_CHECKING:
    from Web.AdminConsole.adminconsole import AdminConsole


class TestFailoverVMs:
    """ Class for test failover VMs provisioning grid """
    def __init__(self, admin_console: AdminConsole) -> None:
        """
        Constructor for initializing all component classes
        Args:
            admin_console (AdminConsole): The admin console object to provide base functions
        """
        self._admin_console: AdminConsole = admin_console

        self._table: Rtable = Rtable(self._admin_console, id="vmProvisioningTable")
        self._panel: RPanelInfo = RPanelInfo(self._admin_console)
        self._dialog: RModalDialog = RModalDialog(self._admin_console)

        self._admin_console.load_properties(self, unique=True)
        self._labels: dict = self._admin_console.props[self.__class__.__name__]

    @PageService()
    def delete_vm(self, vm_name: str) -> None:
        """
        Perform the delete VM action and then wait for action to complete
        Args:
            vm_name (str): The name of the test failover VM to be deleted
        """
        self._table.access_action_item(vm_name, self._labels['action.delete'])
        self._dialog.click_submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def renew_vm(self, vm_name: str, extension_duration: int, extension_unit : str = TimePeriod.HOURS.value) -> None:
        """
        Perform the renew VM action and allow to set extended expiration value in hours
        Args:
            vm_name             (str): The name of the test failover VM to be renewed
            num_hours    (int or str): The number of hours to extend VM by
        """
        self._table.access_action_item(vm_name, self._labels['action.renew'])
        self._dialog.fill_text_in_field(element_id="retentionPeriod", text=extension_duration)
        self._dialog.select_dropdown_values(drop_down_id="retentionPeriodUnit",
                                             values=[extension_unit],
                                             partial_selection=True,
                                             case_insensitive=True)
        self._panel.save()

    @PageService()
    def refresh_vm(self, vm_name: str) -> None:
        """
        Perform the refresh VM action and refresh the VM properties on the table
        Args:
            vm_name             (str): The name of the test failover VM to be refreshed/synchronized
        """
        self._table.access_action_item(vm_name, self._labels['action.synchronize'])
        self._admin_console.wait_for_completion()
    
    def _format_clone_info(self, table_data: str) -> dict:
        """
        Get the information for a test failover VM
        Args:
            vm_name (str): The name of the test failover VM to get information for
        Returns:
            dict: The information for the test failover VM
        """
        transposed_table_data = []
        num_rows = self._table.get_total_rows_count()
        for row_idx in range(num_rows):
            row_data = {
                column: table_data[column][row_idx]
                for column in table_data
            }
            transposed_table_data.append(row_data)

        # No test failover VMs
        if len(transposed_table_data) == 1 and not any(transposed_table_data[0].values()):
            transposed_table_data = []

        return transposed_table_data

    @PageService()
    def get_all_vms_info(self, source_vms : list = []):
        """Get the information for all test failover VMs"""

        cloned_vm_data = defaultdict(list)
        if len(source_vms) > 0:
            for vm in source_vms:
                self._table.apply_filter_over_column(self._labels["label.name"], vm)
                table_data : dict = self._table.get_table_data()
                table_data.pop('Actions')
                cloned_vm_data[vm] = self._format_clone_info(table_data=table_data)
                self._table.clear_column_filter(self._labels["label.name"], vm)
        else:
            cloned_vm_data = {vm: [] for vm in source_vms}

        return cloned_vm_data
