# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for Roles related operations in Metallic Ring

    RolesRingHelper:

        __init__()                      --  Initializes Roles Ring Helper

        start_task                      --  Starts the roles related tasks for metallic ring

        create_role                     --  Creates a given role with set of permissions and category

"""

from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs


class RolesRingHelper(BaseRingHelper):
    """ helper class for Roles related operations in Metallic Ring"""

    def __init__(self, ring_commcell):
        super().__init__(ring_commcell)
        self.roles = self.commcell.roles

    def start_task(self):
        """
        Starts the Roles related tasks for metallic ring
        """
        try:
            self.log.info("Starting Role related operation")
            if not self.roles.has_role(cs.ROLE_CC_ADMIN):
                self.create_role(cs.ROLE_CC_ADMIN, cs.ROLE_CC_ADMIN_PERMISSION, cs.ROLE_CC_ADMIN_CATEGORY)
            self.log.info("Role helper task complete. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute role helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def create_role(self, role_name, permission=None, category=None):
        """
        Creates a new role with given name, permissions and categories provided
        Args:
            role_name(str)              -   name of the role to be created
            permission(list)            -   permissions for the role to be used
            category(list)              -   Category for the role to be used
        Raises:
            Exception:
                When role with given name already exists
        """
        if category is None:
            category = []
        if permission is None:
            permission = []
        if self.roles.has_role(role_name):
            raise Exception(f"role with given name [{role_name}] already exists")
        self.log.info(f"Received request to create new role [{role_name}]")
        self.roles.add(role_name, permission, category)
        self.log.info(f"Role - {role_name} created successfully")
