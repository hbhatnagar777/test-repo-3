# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides operations that can be used to run testcases of Salesforce for Hub.

This file consists of only one class SalesforceHub

SalesforceHub:

    __init__()              --  Method to initialize this class
    
    perform_initial_setup() --  Handle initial setup wizard for Salesforce
"""
from Web.AdminConsole.Hub.constants import HubServices
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.Common.page_object import PageService
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue


class SalesforceHub:
    """Class for performing operations needed for Salesforce automation on Metallic Hub"""

    def __init__(self, admin_console):
        """Init method for SalesforceHub class"""
        self.__admin_console = admin_console
        
    @PageService()
    def perform_initial_setup(self):
        """Handle initial setup wizard for Salesforce"""
        service_catalogue = ServiceCatalogue(self.__admin_console, HubServices.salesforce)
        service_catalogue.click_get_started()
        service_catalogue.start_salesforce_trial()

