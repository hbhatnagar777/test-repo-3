# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Summary Section on the Restore Wizard of Kubernetes

"""
from Web.AdminConsole.Components.dialog import RModalDialog


class Summary:
    """
    class to handle summary section on the restore wizard
    """
    def __init__(self, wizard, admin_console):
        self.__wizard = wizard
        self.__admin_console = admin_console
        self.config()

    def config(self):

        self.__wizard.click_submit()
