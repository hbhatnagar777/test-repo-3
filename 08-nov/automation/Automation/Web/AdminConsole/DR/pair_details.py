# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the functions or operations that can be performed on the
continuous pair details page
"""

from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.table import Table


class PairDetailsOperations:
    """Class for overview tab of the group details page"""

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__table = Table(admin_console)
        self.__admin_console.load_properties(self, unique=True)
        self.__label = self.__admin_console.props[self.__class__.__name__]

    @WebAction()
    def __delete_testboot_vm(self, testboot_vm_name):
        """
        Deletes the active test boot VM
        Args:
            testboot_vm_name(str)     : Specify the testfailover VM name
        """
        self.__table.access_action_item(testboot_vm_name, self.__admin_console.props['label.delete'])
        self.__admin_console.click_button('Yes')

    @PageService()
    def continuous_delete_testboot(self, testboot_vm_name):
        """
        This method deletes the test failover for continuous pair
        Args:
            testboot_vm_name(str)     : Specify the testfailover VM name
        """
        self.__delete_testboot_vm(testboot_vm_name)
