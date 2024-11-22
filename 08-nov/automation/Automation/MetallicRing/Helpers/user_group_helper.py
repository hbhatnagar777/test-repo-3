# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for performing user group related operations in Metallic Ring

    UserGroupRingHelper:

        __init__()                          --  Initializes User Group Ring Helper

        start_task()                        --  Starts the user group related tasks for metallic ring

        create_user_group                   --  Creates a user group

        add_domain                          --  Adds a domain server to the commcell

        enable_sso                          --  enables sso on a given domain server

"""
import copy
from AutomationUtils.config import get_config
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring


class UserGroupRingHelper(BaseRingHelper):
    """ contains helper class for user group ring helper related operations"""

    def __init__(self, ring_commcell):
        super().__init__(ring_commcell)
        self.user_groups = self.commcell.user_groups
        self.domains = self.commcell.domains

    def start_task(self):
        """
        Starts the user group related tasks for metallic ring
        """
        try:
            self.log.info("Starting user group helper task")
            if not self.domains.has_domain(_CONFIG.domain.netbios_name):
                self.log.info(f"Creating new domain with name [{_CONFIG.domain.name}]")
                self.add_domain(_CONFIG.domain.name, _CONFIG.domain.netbios_name, _CONFIG.domain.username,
                                _CONFIG.domain.password)
                self.log.info(f"Domain with name [{_CONFIG.domain.name}] added successfully")
            else:
                self.log.info(f"Domain with name [{_CONFIG.domain.name}] is already present")
            self.enable_sso(_CONFIG.domain.netbios_name, _CONFIG.domain.username,
                            _CONFIG.domain.password)
            security_dict = {
                'assoc1':
                    {
                        "_type_": [cs.ENTITY_TYPE_COMMCELL_ENTITY],
                        "role": [cs.ROLE_TENANT_OPERATOR]
                    }
            }
            tenant_operator_group = _CONFIG.user_group[0].tenant_operator
            tenant_admin_group = _CONFIG.user_group[1].tenant_admin
            if not self.user_groups.has_user_group(tenant_operator_group):
                self.create_user_group(tenant_operator_group, custom_association=security_dict)
            if not self.user_groups.has_user_group(f"{_CONFIG.user_group[0].mapping.domain}"
                                                   f"\\{_CONFIG.user_group[0].mapping.name}"):
                self.create_user_group(_CONFIG.user_group[0].mapping.name, domain=_CONFIG.user_group[0].mapping.domain,
                                       local_usergroup=[tenant_operator_group])
            if not self.user_groups.has_user_group(tenant_admin_group):
                tenant_admin_ug = self.create_user_group(tenant_admin_group)
            else:
                tenant_admin_ug = self.user_groups.get(tenant_admin_group)
            if not tenant_admin_ug.allow_multiple_company_members:
                tenant_admin_ug.allow_multiple_company_members = True
            hub_user_info = _CONFIG.hub_user
            if not self.users.has_user(f"{hub_user_info.domain}\\{hub_user_info.username}"):
                self.users.add(user_name=hub_user_info.username, domain=hub_user_info.domain, email="",
                               local_usergroups=[cs.UG_MASTER])
                self.log.info(f"User with name - [{hub_user_info.username}] added successfully")
            self.log.info("User group helper task complete. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute user group helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def create_user_group(self, group_name, local_usergroup=None, domain=None, custom_association=None):
        """
        Creates a user group
        Args:
            group_name(str)                 -   Name of the user group
            local_usergroup(str)            -   local usergroup to be associated to the group
            domain(str)                     -   name of the domain server
            custom_association(dict)        -   Custom association for the user group
        Returns:
            (Object)                        -   User group object
        """
        ugs = self.user_groups
        final_group_name = group_name
        if domain is not None:
            final_group_name = f"{domain}\\{group_name}"
        self.log.info(f"Request received to create user group with name [{final_group_name}]")
        if ugs.has_user_group(final_group_name):
            raise Exception(f"User group with name [{final_group_name}] already exists")
        ug = ugs.add(group_name, domain=domain, local_usergroup=local_usergroup, entity_dictionary=custom_association)
        self.log.info(f"User group with name [{final_group_name}] created successfully")
        return ug

    def add_domain(self, domain_name, netbios_name, domain_username,
                   domain_password):
        """ Adds a domain server to the commcell
                Args:
                   domain_name  (str)       --  Hostname of the domain server to be added to company

                   netbios_name (str)       --  Netbios name of the domain server

                   domain_username (str)    --  username needed to access the domain entities

                   domain_password (str)    --  password for the domain server

                Returns:
                   None:

                Raises:
                    Exception:
                        If organization with given name does not exist

                        If domain with given name already exist

        """
        self.log.info(f"Request received to create domain [{domain_name}] for company")
        if self.domains.has_domain(netbios_name):
            raise Exception(f"Domain [{domain_name}] already exist")
        self.domains.add(domain_name, netbios_name, domain_username,
                         domain_password, 0)
        self.log.info(f"Domain [{domain_name}] created")

    def enable_sso(self, domain_name, username, password):
        """
        enables sso on a given domain server
        Args:
            domain_name(str)            -   name of the domain
            username(str)               -   username for the domain
            password(str)               -   password for the domain

        """
        try:
            self.log.info(f"Request received to enable sso on domain [{domain_name}]")
            if not self.domains.has_domain(domain_name):
                raise Exception("Domain with given name doesn't exist")
            domain = self.domains.get(domain_name)
            domain.set_sso(flag=True, username=username, password=password)
            self.log.info(f"SSO enabled on Domain [{domain_name}]")
        except Exception as exp:
            self.message = f"Failed to execute user group helper. Exception - [{exp}]"
            self.log.info(self.message)
