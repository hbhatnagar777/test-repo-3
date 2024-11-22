# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on user groups page from Cloud console.

Class:
GCMUserGroupHelper -> UserGroupMain

GCMUserGroupHelper:
    __init__()                          --      Initialize instance of the GCMUserGroupsHelper class

    validate_create_propagation()       --      Method to check if user group created from cloud console are propagated selected service commcells

    get_entity_status()                 --      Method to get user group entity status after creation on service commcells
"""

from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Helper.UserGroupHelper import UserGroupMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.GlobalConfigManager.Helper.gcm_helper import GCMHelper


class GCMUserGroupHelper(UserGroupMain, GCMHelper):
    """Helper class to automate user group related tasks on cloud console"""
    CREATE_OPERATION = 'Create User group'

    def __init__(self, admin_console: AdminConsole) -> None:

        """Initializes GCMUserGroupHelper class"""
        super().__init__(admin_console)
        self.admin_console = admin_console
        self.table = Rtable(self.admin_console)
        self.navigator = admin_console.navigator
        self._service_commcells = []
        self.admin_console.load_properties(self)
        self.log = self.admin_console.log

    def validate_create_propagation(self, service_commcells=None):
        """Helper Method to check if user group created from cloud console are propagated selected service commcells

        Args:
            service_commcells (list[dict]): list of service commcells information
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
        """
        service_commcells_objects = self.get_service_commcells_object(service_commcells)
        usergroup_objects = []

        for commcell in service_commcells_objects:
            usergroup_objects.append(commcell.user_groups)

        super().validate_create_propagation(self, usergroup_objects, service_commcells)

    def get_entity_status(self) -> dict:
        """Method to get entity status after creation

        Returns:
            dict: {
                    "In progress": [commcell1, commcell2],
                    "Failed": [commcell3, commcell4]
                }
        """
        self.navigator.navigate_to_user_groups()
        self.table.view_by_title(self.admin_console.props['label.all'])
        self.table.access_link(self.group_name)
        return super().get_entity_status()
