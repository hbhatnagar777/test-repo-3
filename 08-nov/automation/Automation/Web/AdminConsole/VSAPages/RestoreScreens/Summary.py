# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Summary Section on the Restore Wizard of VSA Hypervisors

"""


class Summary:
    """
    class to handle summary section on the restore wizard
    """
    def __init__(self, wizard):
        self.__wizard = wizard
        self.config()

    def config(self):
        self.__wizard.click_submit()
