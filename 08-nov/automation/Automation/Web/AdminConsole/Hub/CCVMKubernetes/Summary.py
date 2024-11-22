# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Summary Tab on Metallic

"""

class Summary:
    """
    class of the Summary Page
    """
    def __init__(self, wizard, admin_console, metallic_options):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.log = self.__admin_console.log
        self.__wizard = wizard
        self.metallic_options = metallic_options
        self.config()

    def config(self):
        self.__wizard.click_finish()
        self.__admin_console.wait_for_completion()
