# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This Module provides the methods to available for doing operations on Tags Page on Cloud Console.

GCMTagsHelper: Helper class for performing UI operations related to Tags page on cloud console

Class:
    GCMTagsHelper -> EntityTagsHelper
    GCMTagsHelper -> GCMHelper

GCMUserGroups:
    __init__()                          --      Initialize instance of the GCMTagsHelper class

    validate_create_propagation()       --      Method to check if tag created from cloud console are propagated selected service commcells

    get_entity_status()                 --      Method to get tag entity status after creation on service commcells

"""
from Web.AdminConsole.GlobalConfigManager.Helper.gcm_helper import GCMHelper
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Helper.tags_helper import EntityTagsHelper
from Web.AdminConsole.adminconsole import AdminConsole


class GCMTagsHelper(EntityTagsHelper, GCMHelper):
    """Class to perform User group listing related operations from cloud console"""
    CREATE_OPERATION = 'Create tag'

    def __init__(self, admin_console: AdminConsole) -> None:
        """Method to initialize GCMTagsHelper class
        Args:
            admin_console (AdminConsole): AdminConsole object
        """
        super().__init__(admin_console)
        self.admin_console = admin_console
        self.navigator = self.admin_console.navigator
        self.table = Rtable(self.admin_console)
        self.log = self.admin_console.log
        self.admin_console.load_properties(self)

    def validate_create_propagation(self, service_commcells=None):
        """Helper Method to check if tag created from cloud console are propagated selected service commcells

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
        tags_objects = []

        for commcell in service_commcells_objects:
            tags_objects.append(commcell.tags)

        super().validate_create_propagation(self, tags_objects, service_commcells)

    def get_entity_status(self) -> dict:
        """Method to get entity status after creation

        Returns:
            dict: {
                    "In progress": [commcell1, commcell2],
                    "Failed": [commcell3, commcell4]
                }
        """
        self.navigator.navigate_to_tags(True)
        self.table.view_by_title(self.admin_console.props['label.all'])
        self.table.access_link(self.tag_name)
        return super().get_entity_status()
