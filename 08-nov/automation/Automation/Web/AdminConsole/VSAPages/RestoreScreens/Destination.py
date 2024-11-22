# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Destination Section on the Restore Wizard of VSA Hypervisors

"""

from selenium.common.exceptions import NoSuchElementException
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.exceptions import (
    CVWebAutomationException
)
from AutomationUtils import logger
from Web.Common.page_object import (
    PageService,
    WebAction
)
from VirtualServer.VSAUtils.VirtualServerConstants import HypervisorDisplayName


class Destination:
    """
    class to handle Destination page on restore screen wizard
    """
    def __init__(self, wizard, restore_options, admin_console):
        self.wizard = wizard
        self.__restore_options = restore_options
        self.log = logger.get_log()
        self.__admin_console = admin_console
        self._accessnode_partial_match = getattr(restore_options, "accessnode_partial_match", False)
        self.config()

    def config(self):
        """
        configure the destination options for restore
        """
        self.restore_type()
        if self.__restore_options.restore_type == "Out of place":
            self.restore_as()
            self.destination()
        if not self.__restore_options.end_user:
            self.access_node()
        self.wizard.click_next()

    @PageService()
    def restore_type(self, restore_type=None):
        """
        select the restore type eg: inplace / out of place

        """
        if not restore_type:
            restore_type = self.__restore_options.restore_type
        if restore_type == "In place":
            restore_type_id = "inPlaceRadio"
        else:
            restore_type_id = "outOfPlaceRadio"
        self.wizard.select_radio_button(id=restore_type_id)

    @PageService()
    def access_node(self, access_node=None):
        """
        select the access node from restore options
        """
        if not access_node:
            access_node = self.__restore_options.access_node
        self.wizard.select_drop_down_values(id='accessNodeDropdown', values=[access_node],
                                            partial_selection=self._accessnode_partial_match)

    @PageService()
    def restore_as(self, restore_as=None):
        """
        select restore as for out of place restore
        Args:
            restore_as: hypervisor type
        """
        if not restore_as:
            restore_as = self.__restore_options.restore_as
        if not restore_as:
            return
        self.wizard.select_drop_down_values(id='restoreVmDestination', values=[restore_as])

    @PageService()
    def destination(self, destination_hypervisor=None):
        """
        select the destination hypervisor for out of place restore
        Args:
            destination_hypervisor: (str) name of the hypervisor
        """
        if (self.__restore_options.type == HypervisorDisplayName.VIRTUAL_CENTER and
                self.__restore_options.different_vcenter):
            self.wizard.select_drop_down_values(id='hypervisorsDropdown',
                                                values=["Select a different vCenter (optional)"])
            diff_vc_modal = RModalDialog(admin_console=self.__admin_console, title="Edit vCenter credentials")
            diff_vc_modal.fill_text_in_field("vcenterHostName",
                                             self.__restore_options.different_vcenter_info["vcenter_hostname"])
            diff_vc_modal.fill_text_in_field("vcenterUsername",
                                             self.__restore_options.different_vcenter_info["vcenter_username"])
            diff_vc_modal.fill_text_in_field("vcenterPassword",
                                             self.__restore_options.different_vcenter_info["vcenter_password"])
            diff_vc_modal.click_submit()
        else:
            if not destination_hypervisor:
                destination_hypervisor = self.__restore_options.destination_hypervisor
            if destination_hypervisor:
                self.wizard.select_drop_down_values(id='hypervisorsDropdown', values=[destination_hypervisor])
            else:
                self.log.warning(f"going with default destination hypervisor, as the destination hypervisor is "
                                 f"{destination_hypervisor}")