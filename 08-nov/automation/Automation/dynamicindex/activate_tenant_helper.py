# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for content analyzer related operations

    ActivateTenantHelper:

        __init__(testcase)                      --  Initialize the ActivateTenantHelper object

        add_company()                           --  Creates a new company

        add_plan()                              --  Create a new plan

        add_storage_pool()                      --  Creates a new storage pool

        change_company_user_password()          --  Changes the password for a given user in the company

        add_activate_to_company()               --  Adds activate as supported solution for the company

        move_client_to_company                  --  Moves the client to the specified company

        remove_client_association               --  Removes the client association to the company

        add_domain_to_company                   --  Adds a domain name server to the company

        add_user                                --  Adds a new user to the company

        add_data_governance_user_group          --  Creates a new user group with data governance
                                                    capability on the company

        delete_company                          --  Deletes a company present in the commcell

        delete_storage_pool                     --  Deletes the given storage pool from the commcell

        delete_plan                             --  Deletes the given plan from the commcell

        delete_user()                           --  Deletes the given user from the commcell

        add_user_as_operator()                  --  Assigns the user as tenant operator for the company

        associate_user_to_user_group_with_view_permission()   --  Provides view access on a given user to a user group

        delete_domain()                         --  deletes a domain server present in the commcell/company

        cleanup_safe()                          --  Calls the function passed as argument with the
                                                    args/kwargs passed

        cleanup_all()                           --  Cleans up all the entities created as part of the
                                                    tenant activate test case

"""

from AutomationUtils import logger
from dynamicindex.utils import constants as cs


class ActivateTenantHelper:
    """ contains helper class for activate tenant related operations"""

    def __init__(self, commcell_object):
        self.commcell = commcell_object
        self.log = logger.get_log()

    def add_company(self, company_name, email, contact_name, plan_name):
        """ Adds new company with provided name to the commcell
                Args:
                    company_name  (str)     --  Name of the company to be created

                    email (str)             --  Email id for Tenant admin

                    contact_name (str)      --  Contact name of Tenant admin

                    plan_name (str)         --  Name of the plan to be associated with the company

                Returns:
                    None:

                Raises:
                    Exception:
                        If plan with given name does not exist

                        If organization with given name already exist

        """
        self.log.info(f"Received request to add new company : [{company_name}]")
        organizations = self.commcell.organizations
        if organizations.has_organization(company_name):
            raise Exception(f"Organization with name: [{company_name}] already exist")
        if not self.commcell.plans.has_plan(plan_name):
            raise Exception(f"Plan with name: [{plan_name}] does not exist")
        self.log.info(f"Organization with name: [{company_name}] doesn't exist. Creating a new one")
        organizations.add(company_name, email, contact_name, company_name, default_plans=[plan_name])
        self.log.info(f"Organization with name: [{company_name}] created successfully")

    def add_plan(self, plan_name, storage_pool_name):
        """ Adds new plan with provided name to the commcell
                Args:
                    plan_name  (str)        --  Name of the Plan to be created

                    storage_pool_name (str) --  name of the storage pool to be used for the plan

                Returns:
                    None:

                Raises:
                    Exception:
                        If plan with given name already exist

                        If storage pool with given name does not exist

        """
        self.log.info(f"Received request to add new plan : [{plan_name}]")
        plans = self.commcell.plans
        if plans.has_plan(plan_name):
            raise Exception(f"Plan with name: [{plan_name}] already exist")
        if not self.commcell.storage_pools.has_storage_pool(storage_pool_name):
            raise Exception(f"Storage Pool with name: [{storage_pool_name}] does not exist")
        self.log.info(f"Plan with name: [{plan_name}] doesn't exist. Creating a new plan")
        plans.add(plan_name, cs.SERVER, storage_pool_name)
        self.log.info(f"Plan with name: [{plan_name}] created successfully")

    def add_storage_pool(self, storage_pool_name, mount_path, media_agent, dedup_path):
        """ Adds new storage pool with provided name to the commcell
                Args:
                    storage_pool_name (str) --  name of the storage pool to be created

                    mount_path (str)        --  mount path to be used with storage pool

                    media_agent (str)       --  media agent to be used for storage pool

                    dedup_path (str)        -- path for storing deduplication data

                Returns:
                    None:

                Raises:
                    Exception:
                        If Storage Pool with given name already exist

        """
        self.log.info(f"Received request to add new storage pool : [{storage_pool_name}]")
        storage_pools = self.commcell.storage_pools
        if storage_pools.has_storage_pool(storage_pool_name):
            raise Exception(f"Storage Pool with name: [{storage_pool_name}] already exist")
        self.log.info(f"Storage Pool  with name: [{storage_pool_name}] doesn't exist. Creating a new storage Pool")
        storage_pools.add(storage_pool_name, mount_path, media_agent, media_agent, dedup_path)
        self.log.info(f"Storage pool with name: [{storage_pool_name}] created successfully")

    def change_company_user_password(self, company_user_name, new_password, logged_in_user_password):
        """ Changes the password of the company user using company name and email supplied
                Args:
                    company_user_name  (str)        --  Name of the user who belongs to the company
                                                        Ex: company_name: Commvault
                                                            user_name: admin
                                                            company_user_name = commvault\admin

                    new_password (str)              --  new password that has to be updated for user

                    logged_in_user_password(str)    --  password of the logged in user
                                                        who is changing the company user password

                Returns:
                    None:

                Raises:
                    Exception:
                        If user with given name does not exist

        """
        self.log.info(f"Request received to change Company user [{company_user_name}] password")
        self.commcell.users.refresh()
        if not self.commcell.users.has_user(company_user_name):
            raise Exception(f"User with name: [{company_user_name}] doesn't exist")
        company_user = self.commcell.users.get(company_user_name)
        company_user.update_user_password(new_password, logged_in_user_password)
        self.log.info("Password updated successfully")

    def add_activate_to_company(self, company_name):
        """ Adds activate as supported solution to the company
                Args:
                    company_name  (str)     --  Name of the company to add activate as supported solution

                Returns:
                    None:

        """
        activate_solution_constant = cs.ACTIVATE
        self.log.info(f"Adding activate as the supported solution for the company [{company_name}]")
        organization_obj = self.commcell.organizations.get(company_name)
        if not organization_obj.supported_solutions & activate_solution_constant == activate_solution_constant:
            organization_obj.supported_solutions = organization_obj.supported_solutions + \
                                                   activate_solution_constant
            self.log.info("Successfully added activate solution to the Company")
        else:
            self.log.info("Activate is already part of supported solutions")

    def move_client_to_company(self, company_name, client_name):
        """ Associates the given client to the company
                Args:
                    company_name  (str)     --  Name of the company to be associated to client

                    client_name (str)       --  Name of the client to move to company

                Returns:
                    None:

                Raises:
                    Exception:
                        If Client with given name does not exist

                        If Organization with given name does not exist

        """
        if not self.commcell.organizations.has_organization(company_name):
            raise Exception(f"Organization with name [{company_name}] does not exist")
        if not self.commcell.clients.has_client(client_name):
            raise Exception(f"Client with name [{client_name}] does not exist")
        organization_obj = self.commcell.organizations.get(company_name)
        self.log.info(f"Moving client [{client_name}] to company [{company_name}]")
        organization_obj.add_client_association(client_name)
        self.log.info(f"Successfully moved client [{client_name}] to company [{company_name}]")

    def remove_client_association(self, company_name, client_name):
        """ De-associates the given client to the company
                Args:
                   company_name  (str)     --  Name of the company to de-associate the client

                   client_name (str)       --  Name of the client to move out the of company

                Returns:
                   None:

                Raises:
                    Exception:
                        If Client with given name does not exist

                        If Organization with given name does not exist

        """
        if not self.commcell.organizations.has_organization(company_name):
            raise Exception(f"Organization with name [{company_name}] does not exist")
        if not self.commcell.clients.has_client(client_name):
            raise Exception(f"Client with name [{client_name}] does not exist")
        self.log.info(f"Received request to remove company [{company_name}] association for client [{client_name}]")
        organization_obj = self.commcell.organizations.get(company_name)
        self.log.info(f"Removing company association for client [{client_name}]")
        organization_obj.remove_client_association(client_name)
        self.log.info(f"Successfully removed company association for client [{client_name}]")

    def add_domain_to_company(self, domain_name, netbios_name, domain_username,
                              domain_password, company_name):
        """ Adds a domain server to the company
                Args:
                   domain_name  (str)       --  Hostname of the domain server to be added to company

                   netbios_name (str)       --  Netbios name of the domain server

                   domain_username (str)    --  username needed to access the domain entities

                   domain_password (str)    --  password for the domain server

                   company_name (str)       --  Name of the company to add domain server

                Returns:
                   None:

                Raises:
                    Exception:
                        If organization with given name does not exist

                        If domain with given name already exist

        """
        self.log.info(f"Request received to create domain [{domain_name}] for company [{company_name}]")
        if self.commcell.domains.has_domain(netbios_name):
            raise Exception(f"Domain [{domain_name}] already exist")
        if not self.commcell.organizations.has_organization(company_name):
            raise Exception(f"Organization with name [{company_name}] does not exist")
        self.log.info(f"Domain [{domain_name}] doesn't exist. Proceeding with creation")
        organization_obj = self.commcell.organizations.get(company_name)
        self.commcell.domains.add(domain_name, netbios_name, domain_username,
                                  domain_password, int(organization_obj.organization_id))
        self.log.info(f"Domain [{domain_name}] created for company [{company_name}]")

    def add_user(self, user_name, email, full_name, password):
        """ Adds a given user to the company
                Args:
                   user_name  (str)     --  Name of the user to be created

                   email (str)          --  Email of the user to be created

                   full_name (str)      --  Full name of the user to be created

                   password (str)       --  password of the user to be created

                Returns:
                   None:

                Raises:
                    Exception:
                        If User with given name already exist
        """
        users = self.commcell.users
        self.log.info(f"Creating User [{user_name}]")
        if users.has_user(f"{user_name}"):
            raise Exception(f"User with name [{user_name}] already exist")
        self.log.info(f"User with name [{user_name}] doesn't exist")
        users.add(user_name, email, full_name=full_name, password=password)
        self.log.info(f"User with name [{user_name}] created successfully")

    def add_data_governance_user_group(self, user_group_name, company_name, users_list):
        """ Creates a new user group with a list of users to the company with data governance roles
                Args:
                   user_group_name  (str)   --  Name of the user group to be created

                   company_name (str)       --  Name of the company on which the user group will be created

                   users_list (str)         --  List of users to be added to the user group

                Returns:
                   None:

                Raises:
                    Exception:
                        If organization with given name does not exist

                        If user group with given name already exist
        """
        if self.commcell.user_groups.has_user_group(f'{company_name}\\{user_group_name}'):
            raise Exception(f"User group [{company_name}\\{user_group_name}] already exist")
        if not self.commcell.organizations.has_organization(company_name):
            raise Exception(f"Organization with name [{company_name}] does not exist")
        self.log.info(f"Creating User group [{user_group_name}] with data controller role for company [{company_name}]")
        security_dict = {
            'assoc1':
                {
                    cs.PROVIDER_DOMAIN_NAME: [company_name],
                    cs.ROLE: [cs.DATA_CONTROLLER_ROLE]
                }
        }
        ug_nav_items = ["ediscovery", "profile", "analytics",
                        "gdpr", "caseManager", "gettingStarted"]
        self.log.info(f"User group [{company_name}\\{user_group_name}] doesn't exist. Creating a new group")
        user_group = self.commcell.user_groups.add(user_group_name, company_name, users_list,
                                                   entity_dictionary=security_dict)
        self.log.info(f"User group [{company_name}\\{user_group_name}] created successfully")
        self.log.info(f"Setting the navigation preferences for user group [{user_group_name}]  "
                      f"with [{','.join(ug_nav_items)}]")
        user_group.update_navigation_preferences(ug_nav_items)
        self.log.info(f"Successfully updated the navigation preferences for user group [{user_group_name}] "
                      f" with [{','.join(ug_nav_items)}]")

    def add_compliance_user_group(self, user_group_name, company_name, users_list):
        """ Creates a new user group with a list of users to the company with data governance roles
                Args:
                   user_group_name  (str)   --  Name of the user group to be created

                   company_name (str)       --  Name of the company on which the user group will be created

                   users_list (str)         --  List of users to be added to the user group

                Returns:
                   None:

                Raises:
                    Exception:
                        If organization with given name does not exist

                        If user group with given name already exist
        """
        if self.commcell.user_groups.has_user_group(f'{company_name}\\{user_group_name}'):
            raise Exception(f"User group [{company_name}\\{user_group_name}] already exist")
        if not self.commcell.organizations.has_organization(company_name):
            raise Exception(f"Organization with name [{company_name}] does not exist")
        self.log.info(f"Creating User group [{user_group_name}] with Compliance role for company [{company_name}]")
        security_dict = {
            'assoc1':
                {
                    cs.PROVIDER_DOMAIN_NAME: [company_name],
                    cs.ROLE: [cs.COMPLIANCE_ROLE]
                }
        }
        ug_nav_items = [cs.EDISCOVERY, cs.PROFILE, cs.ANALYTICS, cs.GDPR, cs.CASE_MANAGER, cs.GETTING_STARTED]
        self.log.info(f"User group [{company_name}\\{user_group_name}] doesn't exist. Creating a new group")
        user_group = self.commcell.user_groups.add(user_group_name, company_name, users_list,
                                                   entity_dictionary=security_dict)
        self.log.info(f"User group [{company_name}\\{user_group_name}] created successfully")
        self.log.info(f"Setting the navigation preferences for user group [{user_group_name}]  "
                      f"with [{','.join(ug_nav_items)}]")
        user_group.update_navigation_preferences(ug_nav_items)
        self.log.info(f"Successfully updated the navigation preferences for user group [{user_group_name}] "
                      f" with [{','.join(ug_nav_items)}]")
        self.log.info("Restarting commcell services")
        cc_obj = self.commcell.commserv_client
        cc_obj.restart_services()
        self.log.info("Restart of Commcell services complete.")

    def delete_company(self, company_name):
        """ Deletes the given company from the commcell
                Args:
                   company_name  (str)  --  Name of the company to be deleted

                Returns:
                   None:

                Raises:
                    Exception:
                        If organization with given name does not exist

        """
        self.log.info(f"Trying to delete company with name: [{company_name}]")
        if not self.commcell.organizations.has_organization(company_name):
            raise Exception(f"Company with name: [{company_name}] doesn't exist")
        self.commcell.organizations.delete(company_name)
        self.log.info(f"Company with name: [{company_name}] deleted successfully")

    def delete_storage_pool(self, storage_pool):
        """ Deletes the given storage pool from the commcell
                Args:
                   storage_pool  (str)  --  Name of the storage pool to be deleted

                Returns:
                   None:

                Raises:
                    Exception:
                        If Storage pool with given name does not exist

        """
        self.log.info(f"Trying to delete storage pool with name: [{storage_pool}]")
        self.commcell.storage_pools.refresh()
        if not self.commcell.storage_pools.has_storage_pool(storage_pool):
            raise Exception(f"Storage pool with name: [{storage_pool}] doesn't exist")
        self.commcell.storage_pools.delete(storage_pool)
        self.log.info(f"Storage pool with name: [{storage_pool}] deleted successfully")

    def delete_plan(self, plan_name):
        """ Deletes the given plan from the commcell
                Args:
                   plan_name  (str)  --  Name of the plan to be deleted

                Returns:
                   None:

                Raises:
                    Exception:
                        If Plan with given name does not exist

        """
        self.log.info(f"Trying to delete plan with name: [{plan_name}]")
        if not self.commcell.plans.has_plan(plan_name):
            raise Exception(f"Plan with name: [{plan_name}] doesn't exist")
        self.commcell.plans.delete(plan_name)
        self.log.info(f"Plan with name: [{plan_name}] deleted successfully")

    def delete_user(self, user_name, new_user=None):
        """ Deletes the given user from the commcell
                Args:
                    user_name  (str)    --  Name of the user to be deleted
                    new_user (str)      --  name of the target user, whom the ownership
                                            of entities should be transferred
                Returns:
                   None:

                Raises:
                    Exception:
                        If user with given name does not exist

        """
        self.log.info(f"Trying to delete user with name: [{user_name}]")
        self.commcell.users.refresh()
        if not self.commcell.users.has_user(user_name):
            raise Exception(f"User with name: [{user_name}] doesn't exist")
        self.commcell.users.delete(user_name, new_user=new_user)
        self.log.info(f"User with name: [{user_name}] deleted successfully")

    def add_user_as_operator(self, user_name, company_name):
        """
        Assigns the user as tenant operator for the company
            Args:
                user_name  (str)  --  Name of the user to be assigned as operator

                company_name (str) -- Name of the company

            Returns:
               None:

            Raises:
                Exception:
                    If user with given name does not exist
                    If company with given name does not exist
        """
        self.log.info(f"Request received to associate user [{user_name}] as "
                      f"tenant operator for company [{company_name}]")
        if not self.commcell.organizations.has_organization(company_name):
            raise Exception(f"Organization with name [{company_name}] does not exist")
        if not self.commcell.users.has_user(user_name):
            raise Exception(f"User with name [{user_name}] does not exist")
        org_obj = self.commcell.organizations.get(company_name)
        org_obj.add_users_as_operator([user_name], cs.UPDATE)
        self.log.info(f"User [{user_name}] successfully associated as "
                      f"tenant operator for company [{company_name}]")

    def associate_user_to_user_group_with_view_permission(self, user_name, user_group_name):
        """
        Provides view access on a given user to a user group
            Args:
               user_name  (str)         --  Name of the user on which the group wants view access

               user_group_name (str)    --  Name of the user group to update associations

            Returns:
               None:

            Raises:
                Exception:
                    If user group with given name does not exist

                    If user with given name does not exist
        """
        self.log.info(f"Request received to provide view access on user [{user_name}] "
                      f"for user group [{user_group_name}]")
        if not self.commcell.user_groups.has_user_group(f'{user_group_name}'):
            raise Exception(f"User group [{user_group_name}] does not exist")
        if not self.commcell.users.has_user(user_name):
            raise Exception(f"User with name [{user_name}] does not exist")
        security_dict = {
            'assoc1':
                {
                    cs.USER_NAME: [user_name],
                    cs.ROLE: [cs.VIEW_ROLE]
                }
        }
        user_group = self.commcell.user_groups.get(user_group_name)
        user_group.update_security_associations(security_dict, cs.UPDATE)
        self.log.info(f"View access for user [{user_name}] "
                      f"on user group [{user_group_name}] is provided successfully")

    def delete_domain(self, domain_name):
        """ deletes a domain server present in the commcell/company
            Args:
                domain_name  (str)  --  Netbios name of the domain server

            Returns:
               None:

            Raises:
                Exception:
                    If domain with given name doesn't exist

        """
        self.log.info(f"Request received to delete domain [{domain_name}]")
        if not self.commcell.domains.has_domain(domain_name):
            raise Exception(f"Domain [{domain_name}] doesn't exist")
        self.commcell.domains.delete(domain_name)
        self.log.info(f"Domain [{domain_name}] deleted successfully")

    def cleanup_safe(self, func, *args, **kwargs):
        """
        Calls the function passed as argument with the args/kwargs passed safely
        Args:
            func        - name of the function to be called
            args/kwargs - arguments to be passed to func
                          For Kwargs refer func cleanup_all
        """
        try:
            if kwargs.get("company_name") is not None and kwargs.get("client_name") is not None:
                func(**kwargs)
            else:
                func(*args)
        except Exception as e:
            self.log.info(f"[{e}] \n Ignoring the exception as we are force cleaning up the entries for current run")

    def cleanup_all(self, company_name, index_server, client_name, plan_name, storage_pool, **kwargs):
        """
        Cleans up all the entities created as part of the tenant activate test case
            Args:
               company_name  (str)  --  Name of the company to be deleted
               index_server (str)   --  Name of the index server to be removed from company association
               client_name (str)    --  Name of the client to be removed from company association
               plan_name (str)      --  Name of the plan to be deleted
               storage_pool (str)   --  Name of the storage pool to be deleted

           kwargs (dict)        --  Dictionary of optional parameters
               backupset (str)          --  Name of the backupset to be deleted
               agent (Agent)            --  Agent object to which the backupset belongs to
               tenant_operator (str)    --  Name of the tenant operator to be deleted
               domain_name (str)        --  Name of the domain to be deleted

            Returns:
               None
        """
        for key, value in kwargs.items():
            if key == "backupset":
                self.log.info(f"Trying to delete the backupset [{value}]")
                self.cleanup_safe(kwargs.get("agent").backupsets.delete, value)
                self.log.info(f"Successfully deleted backupset [{value}]")
            elif key == "tenant_operator":
                self.log.info(f"Trying to delete the tenant operator user [{value}]")
                self.cleanup_safe(self.delete_user, value, "admin")
                self.log.info(f"Successfully deleted backupset [{value}]")
            elif key == "domain_name":
                self.log.info(f"Trying to delete the domain [{value}]")
                self.cleanup_safe(self.delete_domain, value)
                self.log.info(f"Successfully deleted domain [{value}]")
        self.cleanup_safe(self.remove_client_association, company_name=company_name, client_name=index_server)
        self.cleanup_safe(self.remove_client_association, company_name=company_name, client_name=client_name)
        self.cleanup_safe(self.delete_company, company_name)
        self.cleanup_safe(self.delete_plan, plan_name)
        self.cleanup_safe(self.delete_storage_pool, storage_pool)
        self.log.info("Cleaned up all the entities required for successful run of the test case")
