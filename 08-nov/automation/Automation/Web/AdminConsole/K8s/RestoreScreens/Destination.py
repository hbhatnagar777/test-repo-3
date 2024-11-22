# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Kubernetes Section on the Restore Wizard of VSA Hypervisors

"""

from selenium.common.exceptions import NoSuchElementException
from Web.Common.exceptions import (
    CVWebAutomationException
)
from Web.Common.page_object import (
    PageService,
    WebAction
)


class Destination:
    """
    class to handle Destination page on restore screen wizard
    """

    def __init__(self, wizard, inplace, destination_cluster, access_node='Automatic'):
        self.wizard = wizard
        self.inplace = inplace
        self.access_node = access_node
        self.destination_cluster = destination_cluster
        self.config()

    def config(self):
        """
        configure the destination options for restore
        """
        self.restore_type()
        if not self.inplace:
            self.destination()
        self.select_access_node()
        self.wizard.click_next()

    @PageService()
    def restore_type(self,):
        """
        select the restore type eg: inplace / out of place

        """
        if self.inplace:
            restore_type_id = "inPlaceRadio"
        else:
            restore_type_id = "outOfPlaceRadio"
        self.wizard.select_radio_button(id=restore_type_id)

    @PageService()
    def select_access_node(self):
        """
        select the access node from restore options
        """
        self.wizard.select_drop_down_values(id='accessNodeDropdown', values=[self.access_node])

    @PageService()
    def destination(self):
        """
        select the destination hypervisor for out of place restore
        Args:
        """

        self.wizard.select_drop_down_values(id='destinationServer', values=[self.destination_cluster])
