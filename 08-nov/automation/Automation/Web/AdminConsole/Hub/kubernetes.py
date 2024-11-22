from selenium.webdriver.common.by import By

from Web.AdminConsole.Hub.CCVMKubernetes.BackupMethod import BackupMethod
from Web.AdminConsole.Hub.CCVMKubernetes.RegionSelection import RegionSelection

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides operations that can be used to run testcases of Kubernetes for Hub.

This file consists of only one class KubernetesHub

KubernetesHub:

    __init__()              --  Method to initialize this class

    configure_cloud()       --  Handle setup for Azure AKS

    add_new_cluster()       --  Handle steps for adding new cluster

    add_new_application_group()     --  Handle steps for adding new app group

    run_backup()            --  Run backup job with specified parameters

    run_restore()           --  Run restore job with specified parameters
"""

from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Hub.CCVMKubernetes.BackupGateway import BackupGateway
from Web.AdminConsole.Hub.CCVMKubernetes.CloudStorage import CloudStorage
from Web.AdminConsole.Hub.CCVMKubernetes.KubernetesDeployment import KubernetesDeployment
from Web.AdminConsole.Hub.CCVMKubernetes.LocalStorage import LocalStorage
from Web.AdminConsole.Hub.CCVMKubernetes.StoragePlan import StoragePlan
from Web.AdminConsole.Hub.utils import Utils
from Web.AdminConsole.Setup.k8s_guided_setup import KubernetesSetup
from Web.Common.page_object import PageService, WebAction


class KubernetesHub(KubernetesSetup):

    def __init__(self, admin_console, metallic_options=None, company=None):

        super().__init__(admin_console)

        self.__admin_console = admin_console
        self.__hub_utils = Utils(admin_console)
        self.__jobs = None
        self.__clusters = None
        self.__overview = None
        self.__browse = None
        self.__wizard = Wizard(admin_console)

        self.__metallic_options = metallic_options
        self.__company = company
        self.__cluster_name = None
        self.__app_group_name = None
        self.__plan_name = None
        self.__backup_gateway = None

    @WebAction()
    def __get_first_plan_name(self):
        """Get first plan from the list"""
        return self.admin_console.driver.find_element(By.XPATH, 
            "//div[contains(@class, 'wizard-step-body')]/div[contains(@class, 'MuiGrid-container')]" +
            "//ul/preceding-sibling::span"
        ).text

    @PageService()
    def select_deployment_method(self, **kwargs):
        """For Metallic OEM : Select Kubernetes deployment method

            Kwargs:

                deployment_method     (str)   :   Deployment Mode to select (Valid values: ONPREM, AKS)
        """

        deployment_method = kwargs.get("deployment_method", "ONPREM")
        self.__metallic_options.k8s_deployment_method = deployment_method.lower()

        KubernetesDeployment(
            admin_console=self.admin_console,
            wizard=self.__wizard,
            metallic_options=self.__metallic_options
        )

    @PageService()
    def configure_cloud_storage(self, **kwargs):
        """For Metallic OEM : Select Cloud Step
        """
        CloudStorage(
            admin_console=self.admin_console,
            wizard=self.__wizard,
            metallic_options=self.__metallic_options
        )

    @PageService()
    def configure_region(self, **kwargs):
        """For Metallic OEM : Select Region Step for Azure and AWS

                Kwargs:

                    region      (str)   :   Region to select
        """
        self.__metallic_options.region = kwargs.get("region", None)

        RegionSelection(
            wizard=self.__wizard,
            adminconsole=self.admin_console,
            metallic_options=self.__metallic_options
        )

    @PageService()
    def select_access_nodes(self, **kwargs):
        """Select Backup Gateway

            Kwargs:

                access_nodes        (str)   :   Name of backup gateway to select
        """
        access_nodes = kwargs.get("access_nodes", None)
        self.__metallic_options.backup_gateway = access_nodes

        BackupGateway(
            admin_console=self.admin_console,
            wizard=self.__wizard,
            metallic_options=self.__metallic_options
        )

    @PageService()
    def select_backup_method(self, **kwargs):
        """Select Backup Method
        """
        BackupMethod(
            admin_console=self.admin_console,
            wizard=self.__wizard
        )

    @PageService()
    def configure_local_storage(self, **kwargs):
        """Configure Local Storage step
        """

        LocalStorage(
            admin_console=self.__admin_console,
            wizard=self.__wizard,
            metallic_options=self.__metallic_options
        )

    @PageService()
    def select_plan(self, **kwargs):
        """
        Select plan from plan step
        Kwargs:
            plan_name   (str)   --  Name of the plan. To create a new plan, do not pass plan_name. Instead, update
                                    "optNewPlan" with the plan name in tcinputs
        """

        plan_name = kwargs.get("plan_name", None)
        get_first_plan = kwargs.get("get_first_plan", True)

        # Currently, Plan has to be selected even if one does not want to create app group
        # As a workaround, we have to select any plan in the list to proceed to next step
        # if we do not intend to create an app group
        # Hence, if the plan_name is Null, we will select the first plan in the list and proceed
        plan_name = self.__get_first_plan_name() if get_first_plan and not plan_name else plan_name

        self.__metallic_options.opt_existing_plan = plan_name

        StoragePlan(
            wizard=self.__wizard,
            admin_console=self.admin_console,
            metallic_options=self.__metallic_options
        )
        self.admin_console.check_error_message()
