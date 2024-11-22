# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This Module provides the methods to available for doing operations on Plans Page on Cloud Console.

GCMPlanHelper: Helper class for performing UI operations related to Plans page on cloud console

Class:
    GCMPlanHelper -> PlanMain
    GCMPlanHelper -> GCMHelper

GCMPlanHelper:
    __init__()                          --      Initialize instance of the GCMPlanHelper class

    validate_create_propagation()       --      Method to check if plan created from cloud console are propagated selected service commcells

    get_entity_status()                 --      Method to get plan status after creation on service commcells

    get_common_storage_pool()           --      Method to get a common storage pool between service commcells
"""
import time
from random import choice

from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.GlobalConfigManager.Helper.gcm_helper import GCMHelper
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.GlobalConfigManager import constants


class GCMPlanHelper(PlanMain, GCMHelper):
    """Class to perform Plan listing related operations from cloud console"""
    CREATE_OPERATION = 'Create server plan'

    def __init__(self, admin_console: AdminConsole, service_commcells=None) -> None:
        """Method to initialize GCMPlanHelper class
        Args:
            admin_console (AdminConsole): AdminConsole object

            service_commcells (list[dict]): list of service commcells information
                Example: [
                    {
                        "name"        : "serviceC1",
                        "webconsoleEP": "serviceC1.testlab.commvault.com",
                        "username"    : admin
                        "password"    : your_secret_password1
                    },
                    {
                        "name"        : "serviceC2",
                        "webconsoleEP": "serviceC2.testlab.commvault.com",
                        "username"    : admin
                        "password"    : your_secret_password2
                    }
                ]
                Note: service commcell dict can be passed in init, such that we don't need it while calling methods everytime

        """
        super().__init__(admin_console)
        self.admin_console = admin_console
        self.navigator = self.admin_console.navigator
        self.table = Rtable(self.admin_console)
        self._service_commcell_objects = None
        self._service_commcell_info = service_commcells
        self.__plans = Plans(self.admin_console)
        self.log = self.admin_console.log
        self.admin_console.load_properties(self)

    @property
    def service_commcell_objects(self):
        """returns list service commcells objects"""
        if not self._service_commcell_objects:
            self._service_commcell_objects = self.get_service_commcells_object(self._service_commcell_info)

        return self._service_commcell_objects

    def validate_create_propagation(self, service_commcells=None):
        """Helper Method to check if plan created from cloud console are propagated selected service commcells

        Args:
            service_commcells (list[dict]): list of service commcells information
                Eg: [
                    {
                        "name"        : "serviceC1",
                        "webconsoleEP": "serviceC1.testlab.commvault.com",
                        "username"    : admin
                        "password"    : your_secret_password1
                    },
                    {
                        "name"        : "serviceC2",
                        "webconsoleEP": "serviceC2.testlab.commvault.com",
                        "username"    : admin
                        "password"    : your_secret_password2
                    }
                ]
        """
        if service_commcells:
            self._service_commcell_info = service_commcells
            self._service_commcell_objects = None

        service_commcells_objects = self.service_commcell_objects
        plans_objects = []

        for commcell in service_commcells_objects:
            plans_objects.append(commcell.plans)

        super().validate_create_propagation(self, plans_objects, self._service_commcell_info)

    def get_entity_status(self) -> dict:
        """Method to get entity status after creation

        Returns:
            dict: {
                    "In progress": [commcell1, commcell2],
                    "Failed": [commcell3, commcell4]
                }
        """
        self.navigator.navigate_to_plan()
        self.table.view_by_title(self.admin_console.props['label.all'])
        self.table.access_link(self.plan_name)
        return super().get_entity_status()

    def get_common_storage_pool(self, service_commcells=None):
        """Method to get a common storage pool between service commcells

        Args:
            service_commcells (list[dict]): list of service commcells information
                Eg: [
                    {
                        "name"        : "serviceC1",
                        "webconsoleEP": "serviceC1.testlab.commvault.com",
                        "username"    : admin
                        "password"    : your_secret_password1
                    },
                    {
                        "name"        : "serviceC2",
                        "webconsoleEP": "serviceC2.testlab.commvault.com",
                        "username"    : admin
                        "password"    : your_secret_password2
                    }
                ]
            """
        if not service_commcells and not self._service_commcell_info:
            raise CVWebAutomationException("There are no service commcell information to get storage pool")

        self._service_commcell_info = service_commcells
        common_storage_pool = set()
        processed = False
        for commcell in self.service_commcell_objects:
            if not common_storage_pool and not processed:
                common_storage_pool = set(commcell.storage_pools.all_storage_pools)
            elif common_storage_pool:
                common_storage_pool = common_storage_pool.intersection(commcell.storage_pools.all_storage_pools)
            else:
                raise CVWebAutomationException("There are no common storage pools across service commcells to create a "
                                               "plan; Create atleast one common storage pool to continue")
            processed = True

        return choice(list(common_storage_pool))

    def create_gcm(self, service_commcell=None) -> str:
        """Method to create gcm plan from cloud console

        Args:
            service_commcell (list[dict]): list of service commcells information
                Eg: [
                    {
                        "name"        : "serviceC1",
                        "webconsoleEP": "<FQDN of webconsole>",
                        "username"    : admin
                        "password"    : your_secret_password1
                    },
                    {
                        "name"        : "serviceC2",
                        "webconsoleEP": "<FQDN of webconsole>",
                        "username"    : admin
                        "password"    : your_secret_password2
                    }
                ]

        Returns:
            Created global plan name
        """
        self.storage = self.get_common_storage_pool()
        self.plan_name = plan_name = "GCM" + f"Plan{str(time.time()).split('.')[0]}"

        if service_commcell:
            self.service_commcells = service_commcell
        else:
            self.service_commcells = ['All']

        self.admin_console.navigator.navigate_to_plan()
        self.__plans.create_server_plan(plan_name=plan_name,
                                        storage={'name': self.storage},
                                        service_commcells=service_commcell)

        self.admin_console.wait_for_completion()
        self.admin_console.check_error_message()

        # This is needed, because when check on service commcells global plan has (global) appended to it
        return plan_name + constants.GLOBAL_ENTITIES_EXT
