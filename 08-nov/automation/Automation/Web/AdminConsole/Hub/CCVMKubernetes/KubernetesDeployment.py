# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Deployment Method step on Metallic for Kubernetes

"""
from Web.AdminConsole.Hub.constants import KubernetesDeploymentTypes
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (
    PageService
)


class KubernetesDeployment:
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
        if self.metallic_options.k8s_deployment_method.lower() == KubernetesDeploymentTypes.AKS.value.lower():
            self.azure_aks()
        elif self.metallic_options.k8s_deployment_method.lower() == KubernetesDeploymentTypes.ONPREM.value.lower():
            self.backup_via_gateway()
        elif self.metallic_options.k8s_deployment_method.lower() == KubernetesDeploymentTypes.EKS.value.lower():
            self.amazon_eks()
        else:
            raise CVWebAutomationException(
                f"Invalid selection for Kubernetes Deployment Type. Supported values " +
                f"{[k8s.value for k8s in KubernetesDeploymentTypes]}"
            )
        self.__admin_console.submit_form()

    @PageService()
    def azure_aks(self):
        """
        Select AKS method
        Returns:
            None
        """
        self.log.info("Selecting Deployment method as Azure AKS")
        self.__admin_console.select_radio(id="cloudStorage")

    @PageService()
    def amazon_eks(self):
        """
        Select EKS method
        Returns:
            None
        """
        self.log.info("Selecting Deployment method as Amazon EKS")
        self.__admin_console.select_radio(id="cloudStorageAmazon")

    @PageService()
    def backup_via_gateway(self):
        """
        Select backup gateway method
        Returns:
            None
        """
        self.log.info("Selecting Deployment method as Backup via Backup Gateway")
        self.__admin_console.select_radio(id="accessNode")
