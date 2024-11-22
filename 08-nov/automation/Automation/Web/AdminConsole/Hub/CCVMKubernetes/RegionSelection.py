# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Region Tab on Metallic Hypervisor Creation

"""

class RegionSelection:
    """
    class of the Region Page
    """
    def __init__(self, wizard, adminconsole, metallic_options):
        self.__admin_console = adminconsole
        self.__driver = self.__admin_console.driver
        self.__wizard = wizard
        self.log = self.__admin_console.log
        self.metallic_options = metallic_options
        self.config()

    def config(self):
        self.log.info(f"selecting the region :  {self.metallic_options.region}")
        self.__wizard.select_drop_down_values(id="storageRegion", values=[self.metallic_options.region])
        self.__wizard.click_next()
