# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on Subclient Policies page.

To begin, create an instance of SubclientPoliciesMain for SubclientPolicy test case.

To initialize the class variables, pass the instance object to the appropriate
definition of AdminConsoleInfo

Call the required definition using the instance object.

navigate_to_subclient_policies_page             --- To access subclient policies page

navigate_to_subclient_policy_details            --- To access subclient policy details page

navigate_to_subclient_policy_subclient_details  --- To access subclient policy subclient details page

add_subclient_policy                            ---    Add a new windows or unix subclient policy

edit_subclient_policy                           --- edit the subclient policy details

add_subclient                                   --- creates a new subclient and added it to the subclient policy

delete_subclient                                --- delete the subclient associated to the subclient policy

delete_subclient_policy                         --- deletes the subclient policy added by create_subclient_policy
                                                    method

"""

from Web.AdminConsole.AdminConsolePages.subclient_policies import SubclientPolicies
from Web.AdminConsole.AdminConsolePages.subclient_policy_details import SubclientPolicyDetails
from Web.AdminConsole.AdminConsolePages.subclient_policy_subclient_details import SubclientPolicySubclientDetails


class SubclientPoliciesMain(object):
    """Admin console helper for subclient policy operations"""
    def __init__(self, admin_console):
        """
        Helper for subclient policy related files

        Args:
            testcase    (object)    -- object of TestCase class

        """
        self._admin_console = admin_console
        self.driver = admin_console.driver
        self._subclient_policy_name = None
        self._subclient_name = None
        self._storage_policy_name = None
        self.agent_type = None
        self._associations = None
        self._new_subclient_policy_name = None
        self._new_associations = None
        self._new_subclient_name = None
        self._subclient_path = None
        self._new_subclient_path = None
        self._new_storage_policy_name = None
        self.subclient_policies = None
        self.subclient_policy_details = None
        self.subclient_policy_subclient_details = None

    @property
    def subclient_policy_name(self):
        """ Get subclient policy name"""
        return self._subclient_policy_name

    @subclient_policy_name.setter
    def subclient_policy_name(self, value):
        """ Set subclient policy name"""
        self._subclient_policy_name = value

    @property
    def new_subclient_policy_name(self):
        """ Get new subclient policy name """
        return self._new_subclient_policy_name

    @new_subclient_policy_name.setter
    def new_subclient_policy_name(self, value):
        """ Set new subclient policy name"""
        self._new_subclient_policy_name = value

    @property
    def subclient_name(self):
        """ Get subclient name"""
        return self._subclient_name

    @subclient_name.setter
    def subclient_name(self, value):
        """ Set subclient name"""
        self._subclient_name = value

    @property
    def new_subclient_name(self):
        """ Get new subclient name"""
        return self._new_subclient_name

    @new_subclient_name.setter
    def new_subclient_name(self, value):
        """ Set new subclient name"""
        self._new_subclient_name = value

    @property
    def storage_policy_name(self):
        """ Get storage policy name"""
        return self._storage_policy_name

    @storage_policy_name.setter
    def storage_policy_name(self, value):
        """ Set storage policy name"""
        self._storage_policy_name = value

    @property
    def new_storage_policy_name(self):
        """ Get new storage policy name"""
        return self._new_storage_policy_name

    @new_storage_policy_name.setter
    def new_storage_policy_name(self, value):
        """ Set new storage policy name"""
        self._new_storage_policy_name = value

    @property
    def associations(self):
        """ Get subclient policy associations"""
        return self._associations

    @associations.setter
    def associations(self, value):
        """ Set subclient policy associations"""
        self._associations = value

    @property
    def new_associations(self):
        """ Get new set of subclient policy associations"""
        return self._new_associations

    @new_associations.setter
    def new_associations(self, value):
        """ Set new set of subclient policy associations"""
        self._new_associations = value

    @property
    def subclient_path(self):
        """ Get subclient path"""
        return self._subclient_path

    @subclient_path.setter
    def subclient_path(self, value):
        """ Set subclient path"""
        self._subclient_path = value

    @property
    def new_subclient_path(self):
        """ Get new subclient path"""
        return self._new_subclient_path

    @new_subclient_path.setter
    def new_subclient_path(self, value):
        """ Set new subclient path"""
        self._new_subclient_path = value

    def navigate_to_subclient_policies_page(self):
        """ To navigate to the subclient policies page of the admin console
        """
        if not self.subclient_policies:
            self.subclient_policies = SubclientPolicies(self._admin_console)

        self.subclient_policies.navigate_to_subclient_policies()
        self.subclient_policies.wait_for_completion()

    def navigate_to_subclient_policy_details(self):
        """ To navigate to the subclient policy details page of the admin console
        """
        if not self.subclient_policy_details:
            self.subclient_policy_details = SubclientPolicyDetails(self._admin_console)

        self.navigate_to_subclient_policies_page()
        self.subclient_policies.select_subclient_policy(self.subclient_policy_name)
        self.subclient_policy_details.wait_for_completion()

    def navigate_to_subclient_policy_subclient_details(self):
        """ To navigate to the subclient policy subclient details page of the admin console
        """
        if not self.subclient_policy_subclient_details:
            self.subclient_policy_subclient_details = SubclientPolicySubclientDetails(self._admin_console)

        self.navigate_to_subclient_policies_page()
        self.navigate_to_subclient_policy_details()
        self.subclient_policy_details.open_subclient(self.subclient_name)
        self.subclient_policy_details.wait_for_completion()

    def add_subclient_policy(self):
        """ Calls create_subclient_policy function from SubclientPolicies Class and
             generates subclient policy in admin console"""
        self.navigate_to_subclient_policies_page()
        self.subclient_policies.create_subclient_policy(
            self.subclient_policy_name,
            self.agent_type,
            self.storage_policy_name,
            self.associations
        )

    def edit_subclient_policy(self):
        """Method to edit subclient policy details"""
        self.navigate_to_subclient_policy_details()
        self.subclient_policy_details.edit_subclient_policy_name(self.subclient_policy_name,
                                                                 self.new_subclient_policy_name)
        self.subclient_policy_name = self.new_subclient_policy_name
        self.subclient_policy_details.edit_subclient_policy_association(self.new_associations)
        self.subclient_policy_details.add_subclient(
            self.subclient_name, self.storage_policy_name, self.subclient_path
        )

    def edit_subclient(self):
        """Method to edit the subclient details inside a subclient policy"""
        self.navigate_to_subclient_policy_subclient_details()
        self.subclient_policy_subclient_details.edit_subclient_content(self.subclient_path,
                                                                       self.new_subclient_path)
        self.subclient_policy_subclient_details.edit_storage_policy(self.storage_policy_name,
                                                                    self.new_storage_policy_name)
        self.subclient_policy_subclient_details.edit_subclient_name(self.subclient_name, self.new_subclient_name)
        self.subclient_name = self.new_subclient_name

    def delete_subclient(self):
        """Method to delete subclient from subclient policy details page"""
        self.navigate_to_subclient_policy_details()
        self.subclient_policy_details.delete_subclient(self.subclient_name)

    def delete_subclient_policy(self):
        """Calls the delete_subclient_policy function from SubclientPolicyDetails Page and delete the
               subclient policy"""
        self.navigate_to_subclient_policies_page()
        self.subclient_policies.delete_subclient_policy(self.subclient_policy_name)
