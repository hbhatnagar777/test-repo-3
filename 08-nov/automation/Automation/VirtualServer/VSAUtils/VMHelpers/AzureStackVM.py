# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Does all the Operation for Azure stack vm"""

from VirtualServer.VSAUtils.VMHelper import HypervisorVM
from .AzureVM import AzureVM


class AzureStackVM(AzureVM, HypervisorVM):
    """
    This is the main file for all AzureStack VM operations
    """

    def __init__(self, Hvobj, vm_name):
        """
        Initialization of AzureStack VM properties

        Args:

            Hvobj           (obj):  Hypervisor Object

            vm_name         (str):  Name of the VM

        """
        import requests
        super(AzureStackVM, self).__init__(Hvobj, vm_name)
        self.azure_baseURL = 'https://management.local.azurestack.external'
        self.api_version = "?api-version=2015-06-15"