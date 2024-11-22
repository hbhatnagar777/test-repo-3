# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Use this module to configure recovery group and add VMs to the group
"""
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.browse import RContentBrowse as RB
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.DR.virtualization_replication import _ReplicationGroupCommonConfig
from Web.AdminConsole.Components.panel import RDropDown
from Web.Common.exceptions import CVWebAutomationException


class _RecoveryGroup:
    """

    """
    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        self._admin_console: AdminConsole = admin_console
        self._wizard = Wizard(admin_console)
        self._table = Rtable(admin_console)
        self._browse = RB(admin_console)
        self._replication_config = _ReplicationGroupCommonConfig(admin_console)
        self._dropdown = RDropDown(admin_console)

    @PageService()
    def add(self):
        """Click on add"""
        self._table.access_toolbar_menu("Add")

    @PageService()
    def set_recovery_group_name(self, name):
        """
        To set a recovery group name
        Args:
            name      (str):   Name of the replication group

        """
        self._admin_console.fill_form_by_id(element_id="name", value=name)

    @PageService()
    def select_target(self, target):
        """
        Selects the target from the dropdown
        """
        self._dropdown.select_drop_down_values(values=[target], drop_down_id="recoveryTargetDropdown")

    @PageService()
    def recovery_point(self, recovery_point):
        """
        Selects the recovery point from dropdown
        """
        self._dropdown.select_drop_down_values(drop_down_id="rpOption", values=[recovery_point])

    @PageService()
    def save(self):
        """ To click on next button """
        self._admin_console.click_save()

    @PageService()
    def add_vms(self, vm_info: dict | list, view_mode: str = None, expand_folder: bool = True):
        """
        Select content for subclient from the browse tree

        Args:
            vm_info (dict | list): Information about the VMs to be selected.
                - If `vm_info` is a dictionary, it should be in the format:
                    {"region_1": ['vm_1', 'vm_2'], "region_2": ['vm_3']}
                - If `vm_info` is a list, it should be a list of paths to be selected.

            view_mode (str, optional): The view mode to be set (e.g., "Instance View", "Region View", "Tags View").
                Defaults to None.

            expand_folder (bool, optional): Whether to expand the folders in the browse tree. Defaults to True.
        """
        self.add()
        self._table.access_menu_from_dropdown("Virtual machines")

        if view_mode:
            self._dropdown.select_drop_down_values(
                drop_down_id="browseTypeDropdown", values=[view_mode])
        self._replication_config._select_from_tree(vm_info, expand_folder)
        self._admin_console.click_button("Add")

    @PageService()
    def has_recovery_group(self, recovery_group):
        """
        Check Recovery target exists
        Args:
            recovery_group(str): Specify recovery target name
        Returns(bool):True if target exists else returns false
        """
        return self._table.is_entity_present_in_column('Name', recovery_group)

    @PageService()
    def delete_recovery_group(self, group_name):
        """Delete recovery target"""
        if self.has_recovery_group(group_name):
            self._table.access_action_item(group_name, 'Delete')
            self._admin_console.click_button('Yes')
            self._admin_console.refresh_page()
        else:
            raise CVWebAutomationException("Target [%s] does not exists to delete" % group_name)





