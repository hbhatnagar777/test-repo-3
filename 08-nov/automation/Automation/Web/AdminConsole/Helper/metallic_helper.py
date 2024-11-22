# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run Metallic
AdminConsole Automation test cases.

Class:

    Metallic()

Functions:

    mark_solutions_complete() --  Marks all the available solutions as complete
    compare_solutions() -- Compares the solutions visible to that of given list of solutions
    get_cs_hostname_from_current_url() -- Returns the cs hostname from the current url
    get_commcell_details() -- Returns a dictionary of items for the current logged in CS
    validate_commcell() -- Verifies the current redirected commcell by validating the items
                            to compare
    verify_solutions_redirect() -- Verifies if solution redirected to metallic and validates
                                    based on the items to compare
    update_users_with_roles() -- Associates/Dissociates given users with the given role at
                                                                                commcell level
    verify_users_in_user_group() -- Verifies if the given list of users are in the provided
                                                                        user group of the commcell
    set_login_username() -- Sets the given login name
    set_login_password() -- Sets the given password
    add_additional_settings() -- Adds metallic prerequisite additional settings
    delete_additional_settings() -- Deletes metallic prerequisite additional settings

"""
from urllib.parse import urlparse

from AutomationUtils import logger

from Web.AdminConsole.Setup.getting_started import GettingStarted
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.AdminConsolePages.Metallic import Metallic
from Web.AdminConsole.AdminConsolePages.service_commcell import ServiceCommcell

class MetallicMain:
    """ Metallic helper """

    def __init__(self, admin_console=None, commcell=None, csdb=None):
        """ A class that represents Metallic functions that can be performed
            for AdminConsole Automation
        :param driver: the browser object
        :param commcell: the commcell object
        :param csdb: the commcell database object
        """
        self.__admin_console = admin_console
        self.commcell = commcell
        self.csdb = csdb
        self.log = logger.get_log()

        self.driver = self.__admin_console.driver
        self.getting_started = GettingStarted(self.__admin_console)
        self.__panelinfo = RPanelInfo(self.__admin_console)
        self.metallic = Metallic(self.__admin_console)
        self.service_commcell = ServiceCommcell(self.__admin_console)
        self.metallic_name = 'Metallic'
        self.solution_correction_dict = {'Databases':'Database'}
        self.tenant_admin = 'Tenant Admin'
        self.tenant_users = 'Tenant Users'

    def mark_solutions_complete(self):
        """
        Marks all the available solutions as complete
        Returns a list of solutions which were marked as complete
        """
        orig_url = self.__admin_console.current_url()
        solutions_dict = self.getting_started.get_solutions_listed()
        for solution_name, solution_status in solutions_dict.items():
            if not solution_status:
                self.getting_started.mark_solution_complete(solution_name)
                self.__admin_console.navigate(orig_url)
                self.getting_started.expand_solutions()
        # Get updated status for all solutions
        solutions_dict = self.getting_started.get_solutions_listed()
        return [self.solution_correction_dict[k] if k in self.solution_correction_dict \
                else k for k,v in solutions_dict.items() if v]

    def compare_solutions(self, solutions):
        """
        Compares the solutions visible to that of given list of solutions
        Args:
            list of solutions to compare against
        Returns True if same. Else False
        """
        solutions = sorted([solution.lower() for solution in solutions])
        solutions_obtained = self.metallic.get_solutions()
        solutions_obtained = sorted([solution.lower() for solution in solutions_obtained])
        return solutions==solutions_obtained

    def get_cs_hostname_from_current_url(self):
        """Returns the cs hostname from the current url"""
        return urlparse(self.__admin_console.current_url()).netloc

    def get_commcell_details(self, input_cs_items):
        """
        Returns a dictionary of items for the current logged in CS based on the given input dict
        Args:
            input_cs_items
            Dictionary of items to be checked against. Below are the supported keys:
                hostname
                username
                service_commcell_name
        """
        cs_items = {}
        if 'hostname' in input_cs_items:
            cs_items['hostname'] = self.get_cs_hostname_from_current_url()
        if 'username' in input_cs_items:
            cs_items['username'] = self.__admin_console.get_login_name()
        if 'service_commcell_name' in input_cs_items:
            cs_items['service_commcell_name'] = self.__admin_console.get_service_commcell_name()
        return cs_items

    def validate_commcell(self, cs_items):
        """
        Verifies the current redirected commcell by validating the items to compare
        Args:
            cs_items
            Dictionary of items to be compared against. Below are the supported keys:
                hostname
                username
                service_commcell_name
        Returns:
            True if validation succeeds or False if fails
        """
        status = True
        cs_items_obtained = self.get_commcell_details(cs_items)

        # Convert the dictionary values to lower for comparision
        cs_items_obtained = {k:v.lower() for k,v in cs_items_obtained.items()}
        cs_items = {k:v.lower() for k,v in cs_items.items()}

        if 'hostname' in cs_items:
            if cs_items['hostname'] != cs_items_obtained['hostname']:
                self.log.error('Unexpected hostname')
                status = False
        if 'username' in cs_items:
            if cs_items['username'] != cs_items_obtained['username']:
                self.log.error('Unexpected UserName')
                status = False
        if 'service_commcell_name' in cs_items:
            if cs_items['service_commcell_name'] != cs_items_obtained['service_commcell_name']:
                self.log.error('Unexpected company name')
                status = False
        return status

    def verify_solutions_redirect(self, solutions, **cs_items):
        """
        Verifies if solution redirected to metallic and validates based on the items to compare
        Args:
            List of Solutions
            Dictionary of items to be compared against. Below are the supported keys:
                hostname
                username
                service_commcell_name
        Returns:
            True if validation succeeds or False if fails
        """
        # To store the original/on-prem cs details
        orig_cs_items = self.get_commcell_details(cs_items)
        self.log.info(f'CS items obtained to verify are: [{cs_items}] ')
        for solution in solutions:
            self.log.info(f'Validating solution [{solution}]')
            self.metallic.select_solution(solution)
            if not self.validate_commcell(cs_items):
                return False
            self.__admin_console.navigator.switch_service_commcell(orig_cs_items['service_commcell_name'])
            if not self.validate_commcell(orig_cs_items):
                return False
            self.__admin_console.navigator.navigate_to_metallic()
        return True

    def update_users_with_roles(self, cs_obj, users, roles, request_type):
        """Associates/Dissociates given users with the given role at commcell level
        Args:
            cs_obj       (obj)    --  Commcell object
            users        (list)   --  List of Users
            roles        (list)   --  List of Roles
            request_type (str)    --  Decides whether to UPDATE, DELETE or
                                        OVERWRITE user security association.
        """
        for user in users:
            self.log.info(f'{request_type} user: {user} to roles: {roles}')
            entity_dictionary = {
                'assoc1': {
                    'commCellName': [cs_obj.commserv_name],
                    'role': roles
                }
            }
            cs_obj.users.get(user).update_security_associations(entity_dictionary, request_type)

    def verify_users_in_user_group(self, cs_obj, user_group, users):
        """Verifies if the given list of users are in the provided user group of the commcell
        Args:
            cs_obj       (obj)    --  Commcell object
            user_group   (str)    --  User Group name to be searched in
            users        (list)   --  Users List
        """
        ug_obj = cs_obj.user_groups.get(user_group)
        ug_obj.refresh()
        users_obtained = [user.lower() for user in ug_obj.users]
        self.log.info(f"Users to check: {users}")
        self.log.info(f"Users obtained: {users_obtained}")
        return all(user.lower() in users_obtained for user in users)

    def add_additional_settings(self, cs_obj, metallic_hostname):
        """Adds metallic prerequisite additional settings
        Args:
            cs_obj       (obj)    --  Metallic Commcell object
            metallic_hostname   (str)    --  Metallic Hostname
        """
        self.log.info("Adding Metallic Prerequisite additional settings")
        cs_obj.add_additional_setting('WebConsole', 'enableCloudServices', 'STRING', 'true')
        metallic_cloud_service_url = (f"http://{metallic_hostname}/webconsole")
        cs_obj.add_additional_setting('WebConsole', 'metallicCloudServiceUrl',
                                                  'STRING', metallic_cloud_service_url)

    def delete_additional_settings(self, cs_obj):
        """Deletes metallic prerequisite additional settings
        Args:
            cs_obj       (obj)    --  Metallic Commcell object
        """
        self.log.info("Deleting Metallic Prerequisite additional settings")
        cs_obj.delete_additional_setting('WebConsole', 'enableCloudServices')
        cs_obj.delete_additional_setting('WebConsole', 'metallicCloudServiceUrl')
