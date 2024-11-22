# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing Organization related operations on Commcell

OrganizationHelper:
    __init__()                  --  Initialize instance of the OrganizationHelper class

    create()                    -- Create Company

    add_domain()                -- Associate a domain to the Company

    modify_auth_code()          --  Modifies the "Requires authcode for installation" property
                                        for an organization.

    validate_client()           --  Validates on boarded client for the organization or the Commcell

    validate_usercentric_client()
                                --  Validates on boarded user centric client for the organization

    validate_no_of_devices()    --  Validate number of devices activated for the organization

    validate_clientgroup_assoc()
                                --  Validates if on boarded client gets associated to
                                        Organization's default plan &OR Commcell default plan &OR
                                        organization

    validate_client_owners()    --  Validate owners for the client are as expected

    disable_msp()               --  Disable MSP on the commcell if it is not already disabled.

    create_blacklisted_group()  --  Creates blacklisted user group

    delete_blacklisted_group()  --  Delete blacklisted user group

    add_user_to_blacklisted_group()
                                --  Adds a user to a blacklister user group

    remove_user_from_blacklisted_group()
                                --  Removes a user from a blacklister user group

    set_tenant_property()       -- Sets a tenant property for a tenant or Commcell

    is_msp()                    --  Checks if commcell is MSP

    is_client_activated()       --  Check if client is activated and associated to plan's client group

    is_device_associated()      --  Wait for device to be associated to company

    is_domain_user()            --  Checks if a user name is a domain user or local user

    delete_domain()             --  Deletes a domain from the commcell

    cleanup()                   --  Cleans up the environment modified on commcell by the helper class

    @Property
        default_plan                    --  Sets/Gets default plan for an organization

        company                         --  Sets/Gets the company object based on given company name

        commcell_default_plan           --  Sets/Gets commcell's default plan at Commcell Level

        tenant_client_group             --  Sets/Gets a Tenant company's client group name based on
                                            Default plan

        machine_count                   --  Gets the client count associated for the given company


RoleHelper:
    __init__()                          --  Initialize RoleHelper object

    create_role()                       --  Creates new role on the CommCell

    random_permissions()                --  Generates and returns 5 random permissions

    random_category()                   --  Generates and returns 3 random categories

    generate_permissions_categories()   --  Returns 5 random permissions and 3 random categories

    delete_role()                       --  Deletes the specified role on CommCell

    update_role_properties()            --  Update, Overwrite, deletes capabilities the passed

    _validate_role_permissions()        --  validates capabilities present on the role with db
                                            values

    _update_role_status()               --  Updates role status

    _update_role_description()          --  Updates role description

    _update_role_name()                 --  Updates role name

    _fetch_role_property()              --  Gets role property values from db

    @property
        role()                          --  Returns the role object of this CommCell role

    cleanup_roles()                     --  Delete roles that has provided marker / string

    validate_roles_cache_data()         --  validates the data returned from Mongo cache for roles collection

    validate_sort_on_cached_data()      --  validates sort parameter on entity cache API call

    validate_limit_on_cache()           --  validates limit parameter on entity cache API call

    validate_search_on_cache()          --  validates search parameter on entity cache API call

    validate_filter_on_cache()          --  validates fq param on entity cache API call

SecurityHelper:

    __init__                            --  Initializes RoleHelper object

    gen_random_entity_types_dict        --  Generate dictionary consisting of randomly selected dictionary types, roles

    generate_random_entity_dict         --  Generate dictionary consisting of randomly selected dictionary types, roles

    gen_entity_role_dict                --  Generates and returns entity and role association not association dictionary

    validate_security_associations      --  Validates security Associations on user and userggroup

    return_association_details          --  Returns list of lists containing entityType, entityName and permissionName

    calculate_capability_bitmask        --  Returns list of lists containing entityType, entityName and permissionName

    valid_operations_for_user           --  Generates Intended Operations for User

    can_perform_operations              --  Inserts valid and intended operations list to DB.

"""

import inspect
import time
import random
import re
import os
import locale

from cvpysdk.security.role import Roles
from cvpysdk.security.usergroup import UserGroup
from AutomationUtils.idautils import CommonUtils
from AutomationUtils import database_helper, logger, options_selector
from AutomationUtils.options_selector import OptionsSelector
from Server.Security import securityconstants


class OrganizationHelper(object):
    '''Helper class to provide Organization related operations on Commcell'''

    def __init__(self, commcell, company=None):
        """ initialize instance of the OrganizationHelper class

        Args:
            commcell (obj)    -- Commcell object

            company  (str)    -- Organization name
        """

        self._commcell = commcell
        self._company_name = company
        self._company = None
        self._commcell_default_plan = None
        self._tenant_client_group = None
        self._plan_type = 'Laptop'

        if company is not None:
            self._company_name = company
            self._company = self._commcell.organizations.get(company)
            self._machine_count = self._company.machine_count
            self._tenant_client_group = None
            default_plan = self._company.default_plan
            if default_plan is not None:
                default_plan = default_plan[0] if isinstance(default_plan, list) else default_plan
                self._tenant_client_group = default_plan + ' clients'

        self._auth_map = securityconstants.AUTH_MAP
        self._utility = OptionsSelector(self._commcell)
        self._csdb = database_helper.CommServDatabase(commcell)
        self.blacklist_user_map = {}
        self.blacklist_user_groups = []
        self.log = logger.get_log()
        self.options_selector = OptionsSelector(commcell)

    def create(self,
               name,
               email,
               contact_name,
               company_alias,
               email_domain=None,
               primary_domain=None,
               default_plans=None):
        """ Create a Tenant company
            Args:

                name            (str)    - Company name to create

                email           (str)    - Email associated to the company owner

                contact_name    (str)    - Contact name for the Company owner

                company_alias   (str)    - Company alias

                email_domain    (str)    - Email Domain

                primary_domain  (str)    - Primary domain associated to the company

                default_plans   (str)    - Default plan associated to the company

            Returns:    (obj)    - Company object

            Raises
                Exception:
                    - in case failed in any step to create company

        """
        try:
            args = [name, email, contact_name, company_alias, email_domain, primary_domain, default_plans]
            if self._commcell.organizations.has_organization(name):
                self.log.info("Company [{0}] already exists on commcell".format(name))
                self._company = self._commcell.organizations.get(name)
            else:
                self.log.info("""Creating organization [{0}], with email [{1}], contact name [{2}], company alias[{3}],
                                 email domain [{4}], primary domain [{5}], default plans [{6}]""".format(*args))
                self._company = self._commcell.organizations.add(*args)

            self._company_name = name
            self._machine_count = self._company.machine_count

            return self._company

        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def add_domain(self, domain, netbios, user, password, company_id="", ad_proxy_list=None, enable_sso=True):
        """ Create a domain for the company and associate with it

            Args:
                domain        (str)    - Domain name

                netbios       (str)    - Netbios name for the domain

                user          (str)    - Domain User

                password      (str)    - Domain user password

                company_id    (str)    - Associated company id

                ad_proxy_list (list)   - Active Domain proxy list

                enable_sso    (bool)   - Enablle SSO? (True/False)

            Returns:
                domain object for created domain (obj)

            Raises:
                Exception:
                    - In case failed at any step to create domain
        """
        try:
            args = [domain, netbios, user, password, company_id, ad_proxy_list, enable_sso]
            if self._commcell.domains.has_domain(netbios):
                self.log.info("Domain [{0}] already exists on commcell".format(domain))
                domain = self._commcell.domains.get(netbios)
            else:
                self.log.info("""Creating domain [{0}], with netbios [{1}], user [{2}], pass [{3}], company_id [{4}],
                                 ad_proxy_list [{5}], enable_sso option as [{6}]""".format(*args))
                domain = self._commcell.domains.add(*args)

            return domain

        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def modify_auth_code(self, operation=None, hardcheck=True):
        """Modifies the "Requires authcode for installation" property for an organization.

            Args:

                operation    (str)    -- enable/disable auth code for the organization.
                                            Supported : enable/disable

                hardcheck     (bool)   -- True/False based on whether the to throw exception in
                                            case of any error or to return falsy value.

            Returns:
                AuthCode    (str)      -- Modified auth code for the organization.

            Raises:
                Exception:

                    - if Unsupported operation type passed to modify_auth_code

                    - if failed to enable/disable auth code

                    - if failed during any step while enabling/disabling the auth code
        """
        try:
            company_name = self._company_name
            if operation not in self._auth_map:
                raise Exception("Unsupported operation type passed to modify_auth_code")

            self.log.info("{0} auth code for company: [{1}]. Current authcode [{2}]"
                          "".format(self._auth_map[operation]['message'], company_name,
                                    self._company.auth_code))

            getattr(self._company, self._auth_map[operation]['module'])()

            self.log.info("Successfully [{0}] auth code for company:  [{1}]. Current authcode [{2}]"
                          "".format(self._auth_map[operation]['post_message'], company_name,
                                    self._company.auth_code))

            auth_code = self._company.auth_code

            # Validation
            if operation == 'enable':
                assert isinstance(auth_code, str), "Failed to enable auth code"
            if operation == 'disable':
                assert auth_code is None, "Failed to disable auth code"

            self.log.info("Auth code validation succeeded.")

            return auth_code

        except AssertionError as aserror:
            if not hardcheck:
                return False
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(aserror)))
        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def validate_client(self, clientobj, **kwargs):
        """ Validates on boarded client for the organization

            Args:

                clientobj    (obj)         -- Client object for which validation needs to be performed.

                Supported Keywords arguments:
                -----------------------------

                clients_joined    (bool)   -- Validate number of new clients on boarded the
                                                organization (True/False)
                                                Default: True
                increment_client_count_by
                                  (int)    -- Validate number of clients on boarded the organization
                                                Default: 1

                chatter_flag (int)         -- Expected value for nChatter registry flag. (0/1)
                                                Default: 0

                nLaptopAgent (int)         -- Expected value for nLaptopAgent registry flag. (0/1)
                                                Default: 1

                fail              (bool)   -- If true, will throw exception in case of failed
                                              client validation. If false,
                                              will return False if validation fails

                client_groups (list)       -- List of user specified client groups to validate.
                                              Default is None In case of None
                                              validate_clientgroup_assoc() will assume defaults
                                              for the plan and organization.

                expected_owners (list)     -- Expected owners list for the client
                                                Default: []

                client_name    (str)       -- Client name could be different for User Centric clients.

            Returns:
                (bool)                     -- Based on validation failed/pass

            Raises:
                Exception:
                    - if validation failed
                    - if module failed to execute due to some error

        """
        try:
            client = kwargs.get('client_name', clientobj.machine_name)

            # Check if clients are ready.
            _ = self._utility.wait_until_client_ready(client)

            # Check if the clients got associated to Plan/Organization client groups/Commcell Plan
            # whichever applicable based on input types passed to the modules.
            self.validate_clientgroup_assoc(client, client_groups=kwargs.get('client_groups'), time_limit=15)

            # Validate nChatter flag registry key value
            _ = self._utility.check_reg_key(clientobj, 'Session', 'nChatterFlag', kwargs.get('chatter_flag', 0))

            # Validate laptopAgent flag registry key value
            _ = self._utility.check_reg_key(clientobj, 'FileSystemAgent', 'nLaptopAgent', kwargs.get('nLaptopAgent', 1))

            # Validate client owners
            if kwargs.get('expected_owners', []):
                self.validate_client_owners(client, kwargs.get('expected_owners', []))

            # Validate number of clients joined in the organization
            if kwargs.get('clients_joined', True):
                client_count = kwargs.get('increment_client_count_by', 1)
                self.validate_no_of_devices(client_count)

            # Validate sCCSDbStatus changes to ONLINE
            _ = self._utility.is_regkey_set(clientobj, "iDataAgent", "sCCSDbStatus", 10, 15, True, 'ONLINE')

            return True
        except AssertionError as aserror:
            if not kwargs.get('fail', True):
                return False
            self.log.error("Client validation failed")
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(aserror)))
        except Exception as excp:
            self.log.error("Client validation failed")
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def validate_usercentric_client(self, client_name, user_centric=True, **kwargs):

        """ Validates on boarded user centric client for the organization

            Args:

                client_name    (String)         -- Client name for which validation needs to be performed.

                user_centric    (bool)     -- If this flag is set, It will check if User Centric
                                              flag is set in App_client prop table
                                              default:True

                Supported Keywords arguments:
                -----------------------------
                fail              (bool)   -- If true, will throw exception in case of failed
                                              client validation. If false,
                                              will return False if validation fails

                client_groups (list)       -- List of user specified client groups to validate.
                                              Default is None In case of None
                                              validate_clientgroup_assoc() will assume defaults
                                              for the plan and organization.

                expected_owners (list)     -- Expected owners list for the client
                                                Default: []


            Returns:
                (bool)                     -- Based on validation failed/pass

            Raises:
                Exception:
                    - if validation failed
                    - if module failed to execute due to some error

        """
        try:
            # Check if clients are ready.
            _ = self._utility.wait_until_client_ready(client_name)

            # Check if the clients got associated to Plan/Organization client groups/Commcell Plan
            # whichever applicable based on input types passed to the modules.
            self.validate_clientgroup_assoc(client_name, client_groups=kwargs.get('client_groups'), time_limit=15)

            # Validate client owners
            if kwargs.get('expected_owners', []):
                self.validate_client_owners(client_name, kwargs.get('expected_owners', []))

            # Validate user centric flag
            if user_centric:
                _query = """select attrVal from APP_ClientProp where
                componentNameId=(select id from app_client where name='{0}')
                and attrName='User Centric Client'""".format(client_name)
                self._csdb.execute(_query)
                if self._csdb.fetch_one_row()[0] != '1':
                    raise Exception(f'User centric flag is not set for client [{0}] in Database'.format(client_name))
                self.log.info("User centric flag is set to 1 for client [{0}]".format(client_name))

            return True
        except AssertionError as aserror:
            if not kwargs.get('fail', True):
                return False
            self.log.error("Client validation failed")
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(aserror)))
        except Exception as excp:
            self.log.error("Client validation failed")
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def validate_deactivation(self, clientobj, reg_key):
        """ Validates deactivated client for the organization

            Args:

                clientobj    (obj)         -- Client object for which validation needs to be performed.


                reg_key (int)         --   path for bDeactivate registry key.


            Raises:
                Exception:
                    - if validation failed
                    - if module failed to execute due to some error

        """
        try:
            expected_value = '34afabe997158009d445a6d82a3dabcd6'

            client = clientobj.client_name

            # Check if the clients got associated to Plan/Organization client groups/Commcell Plan
            # whichever applicable based on input types passed to the modules.
            return_flag = self._utility.is_client_in_client_group(
                client,
                client_groups=[self._tenant_client_group]
            )

            if return_flag:

                exp = "Laptop {0} associated to plan's client group {1}"\
                        .format(clientobj.client_name, self._tenant_client_group)
                self.log.exception(exp)
                raise Exception(exp)

            self.log.info("Client [{0}] is not associated to client group: [{1}]"\
                            .format(client, self._tenant_client_group))

            # Validate bDeactivate flag registry key value
            _ = self._utility.check_reg_key(client, reg_key, 'bDeactivate', expected_value)

            # validate associated plan value in app_clientprop table
            _query = f"select attrval from APP_ClientProp where " \
                     f"componentNameId={clientobj.client_id} and attrName = 'Associated plan'"

            self._csdb.execute(_query)
            if self._csdb.fetch_one_row()[0] != '0':
                raise Exception(f'Associated plan value of the client {clientobj.client_name} is not 0 ' \
                                'upon Deactivation')

            self.log.info("Laptop deactivation updated with correct value in database")

        except Exception as excp:
            self.log.error("Client deactivation failed")
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def validate_no_of_devices(self, increment_client_count_by=1):
        """ Validate number of devices activated for the organization """
        self.log.info("Number of clients in company [{1}] *before client activation: [{0}]"
                      "".format(self._company.machine_count, self._company_name))
        pre_machine_count = self._company.machine_count
        self._company.refresh()
        post_machine_count = self._company.machine_count
        self.log.info("Number of clients post client activation: [{0}]".format(post_machine_count))

        if post_machine_count < (pre_machine_count + increment_client_count_by):
            self.log.error(
                "Number of clients in company should have increased by: [{0}]"
                .format(increment_client_count_by)
            )
            raise Exception("Validation failed for number of devices in the organization.")

        self.log.info("Validation succeeded for number of devices joining the organization.")

    def validate_clientgroup_assoc(self, client, fail=True, time_limit=15, retry_interval=30, client_groups=None):
        """ Validates if on boarded client gets associated to Organization's default plan

            Args:
                client    (str)            -- Client to check in defaults plan's/organization's
                                              client group.

                fail       (bool)          -- If true, will throw exception in case of failed
                                              client validation. If false, will return False if validation fails

                retry_interval    (int)    -- Interval (in seconds) after which job state
                                                    will be checked in a loop. Default = 10

                time_limit        (int)    -- Time limit after which job status check shall be
                                                aborted if the job does not reach the desired
                                                 state. Default (in minutes) = 15

                client_groups (list)       -- List of client groups to validate

            Returns:
                (bool)                     -- Based on validation failed/pass

            Raises:
                Exception:
                    - if validation failed
                    - if module failed to execute due to some error
        """
        try:
            if client_groups is None:
                client_groups = ['Laptop Clients']
                if self._company_name and self._tenant_client_group:
                    client_groups.extend([self._company_name, self._tenant_client_group])
            elif self._company_name:
                client_groups = [self._company_name]

            self.log.info("Validating if client [{0}] is part of client groups [{1}]".format(client, client_groups))

            time_limit = time.time() + time_limit * 60
            while True:
                flag = True

                # Validate clients are part of tenant's / company's / default plan client group
                # flag should be set to false if the validation failed for any client group.
                # Do not exit loop until succeeds for all client groups.
                for _source in client_groups:
                    args = [client, _source]
                    if not self._utility.is_client_in_client_group(client, [_source]):
                        flag = False

                if flag:
                    break

                if time.time() >= time_limit:
                    self.log.error("Timed out after [{0}min] waiting for client association".format(time_limit))
                    break
                else:
                    self.log.info("Waiting for [{0}] seconds ".format(retry_interval))
                    time.sleep(retry_interval)

            if not flag:
                raise AssertionError("Client(s) [{0}] did not get associated to client group [{1}]".format(*args))

            self.log.info("Client(s) [{0}] associated successfully to client group [{1}]".format(*args))

        except AssertionError as aserror:
            if not fail:
                return False
            raise Exception("\nFailed [{0}] [{1}]".format(inspect.stack()[0][3], str(aserror)))
        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def validate_client_owners(self, client, expected_owners=None):
        """ Validate owners for the client are as expected
        Args:
            clients    (str):        Client name

            expected_owners (list):  List of expected owners

            Returns:
                None
        """
        if expected_owners is None:
            expected_owners = []
        client_obj = self._commcell.clients.get(client)
        client_obj.refresh()
        owners = client_obj.owners
        assert owners is not None and owners, "No owners set for client [{0}]".format(client)
        client_owners = [owner.lower() for owner in owners]
        expected_owners = [exp_owner.lower() for exp_owner in expected_owners]

        self.log.info("Client's [{0}] owners: [{1}]".format(client, owners))
        self.log.info("Client's [{0}] expected owners: [{1}]".format(client, set(expected_owners)))

        assert set(client_owners) == set(expected_owners), "[Client ownership validation failed]"

        self.log.info("Client ownership validation succeeded.")

    def disable_msp(self):
        """ Disable MSP on the commcell if it is not already disabled.

            Args:
                None

            Returns:
                True    (bool)    - If the MSP is disabled on commcell

            Raises:
                Exception:
                    - if Failed to disable MSP on commcell
        """
        try:
            if self.is_msp():
                # If it is enabled, disable it and restart tomcat service
                CommonUtils(self._commcell).modify_additional_settings('IsMSPCommcell', 1)

                self.log.info("Restarting Tomcat service for the setting to take effect.")
                self._commcell.commserv_client.restart_service("GxTomcatInstance001")

                if self.is_msp():
                    raise Exception('Failed to disable MSP on commcell')

                self.log.info('Successfully disabled MSP on commcell.')
                return True

        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def create_blacklisted_group(self, blacklist_group=None):
        """ Creates blacklisted user group
            Args:
                blacklisted_group   (str):        Blacklisted user group name.

                Returns:
                    None

                Raises:
                    Exception:
                        - If module fail to execute at any step
        """
        try:
            blacklist_group = securityconstants.BLACKLIST_USER_GROUP if blacklist_group is None \
                else blacklist_group
            if not self._commcell.user_groups.has_user_group(blacklist_group):
                self.log.info("Creating blacklisted usergroup [{0}]".format(blacklist_group))
                user_group = self._commcell.user_groups.add(blacklist_group)
            else:
                self.log.info("Blacklisted usergroup [{0}] already exists".format(blacklist_group))
                user_group = self._commcell.user_groups.get(blacklist_group)

            self.blacklist_user_groups.append(blacklist_group)

            # Set blacklisted flag on the user group
            qscript = "-sn 'BlacklistUserGroup' -si '" + blacklist_group + "' -si 1"
            self.log.info("Executing qscript [{0}] to set user group as blacklisted".format(qscript))
            response = self._commcell._qoperation_execscript(qscript)
            self.log.info("qscript response: [{0}]".format(response))
            if not bool(re.search('Qscript Execution Succeeded', str(response['output']))):
                raise Exception("Failed to set user group [{0}] as blacklisted".format(
                    blacklist_group))

        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def delete_blacklisted_group(self, blacklist_group=None, new_user=None):
        """ Deletes blacklisted user group
            Args:
                blacklisted_group   (str):        Blacklisted user group name.

                new_user (str):                   User to which ownership shall be transferred
                                                    Default: admin

                Returns:
                    None

                Raises:
                    Exception:
                        - If module fail to execute at any step
        """
        try:
            blacklist_group = securityconstants.BLACKLIST_USER_GROUP if blacklist_group is None else blacklist_group
            if new_user is None:
                new_user = 'admin'
            if self._commcell.user_groups.has_user_group(blacklist_group):
                self.log.info("Deleting blacklisted usergroup [{0}]".format(blacklist_group))
                self._commcell.user_groups.delete(blacklist_group, new_user)
            else:
                self.log.info("Blacklisted usergroup [{0}] does not exists".format(blacklist_group))
            if blacklist_group in self.blacklist_user_groups:
                self.blacklist_user_groups.remove(blacklist_group)

        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def add_user_to_blacklisted_group(self, user, blacklist_group=None):
        """ Adds a user to a blacklister user group
            Args:
                user                (str):        User name

                blacklisted_group   (str):        User group to add the user

                Returns:
                    None

                Raises:
                    Exception:
                        - If module fail to execute at any step
        """
        try:
            blacklist_group = securityconstants.BLACKLIST_USER_GROUP if blacklist_group is None else blacklist_group
            ug = self._commcell.user_groups.get(blacklist_group)
            ug.update_usergroup_members(request_type='UPDATE', users_list=[user], local_usergroups=[
                blacklist_group])

            self.log.info("Added user [{0}] to blacklisted user group [{1}]".format(user,
                                                                                    blacklist_group))
            self.log.info("Users in blacklisted usergroup [{0}]: [{1}]".format(blacklist_group,
                                                                               ug.users))

            user_list = self.blacklist_user_map.get(blacklist_group, [])
            user_list.append(user)
            self.blacklist_user_map[blacklist_group] = user_list

        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def remove_user_from_blacklisted_group(self, user, blacklist_group=None):
        """ Removes a user from a blacklister user group
            Args:
                user                (str):        User name

                blacklisted_group   (str):        User group to add the user

                Returns:
                    True: If no user group exists with the specified name

                Raises:
                    Exception:
                        - If module fail to execute at any step
        """
        try:
            blacklist_group = securityconstants.BLACKLIST_USER_GROUP if blacklist_group is None else blacklist_group
            if not self._commcell.user_groups.has_user_group(blacklist_group):
                self.log.info("No user group exists with name [{0}]".format(blacklist_group))
                return True
            ug = self._commcell.user_groups.get(blacklist_group)
            ug.update_usergroup_members(request_type='DELETE', users_list=[user], local_usergroups=[
                blacklist_group])

            self.log.info("Removed user [{0}] from blacklisted user group [{1}]".format(user, blacklist_group))
            self.log.info("Users in blacklisted usergroup [{0}]: [{1}]".format(blacklist_group, ug.users))

            user_list = self.blacklist_user_map.get(blacklist_group, [])
            if user in user_list:
                user_list.remove(user)
            self.blacklist_user_map[blacklist_group] = user_list

        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def set_tenant_property(self, prop_name, prop_value, provider='Commcell'):
        """ Sets a tenant property for a tenant or Commcell
            Args:
                provider   (str):          Provider name
                                                Default: 'Commcell'  [Commcell]

                prop_name    (str):        Property name to set for the provider

                prop_value   (str):        Property valule to set for the property name

                Returns:
                    None

                Raises:
                    Exception:
                        - If module fail to execute at any step
                        - If failed to set Tenant/Commcell property
        """
        try:
            self.log.info(
                "Setting property [{0}] value [{1}] for provider [{2}]".format(prop_name, prop_value, provider)
            )
            qscript = "-sn SetCompanySetting.sql" + " -si '" + provider + "' -si '" + prop_name + "' -si '" + prop_value + "'"
            self.log.info("Executing qscript [{0}]".format(qscript))
            response = self._commcell._qoperation_execscript(qscript)
            self.log.error("Command output : [{0}]".format(response['output']))
            if not bool(re.search('Qscript Execution Succeeded', response['output'])):
                raise Exception("Failed to set property [{0}]".format(prop_name))
            self.log.info("Execution of qscript succeeded.")
            if self._company:
                self._company.refresh()
        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def is_msp(self):
        """ Checks if commcell is MSP

            Args:
                None

            Returns:
                True/False    (bool)    - If the MSP is enabled/disabled on commcell

            Raises:
                Exception:
                    - if Failed to get the MSP details from commcell.
        """
        try:
            # check if commcell is MSP
            self.log.info('Getting current value for IsMSPCommcell from GXGlobalParam')

            value = str(self._utility.get_gxglobalparam_val('IsMSPCommcell'))
            commserve_name = self._commcell.commserv_name
            if value == '0' or value == '' or value is None:
                self.log.info('Commcell [{0}] is not an MSP'.format(commserve_name))
                return False

            self.log.info('Commcell [{0}] is a MSP'.format(commserve_name))
            return True

        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def is_domain_user(self, user_name):
        """ Checks if a user name is a domain user or local user

            Args:
                user_name (str):     Username
                                        e.g testuser1

            Returns:
                True/False    (bool)    - True if user is a domain user. False if it is local.

            Raises:
                Exception:
                    - if Failed at any point during execution
        """
        try:
            if '\\' in user_name:
                self.log.info("User [{0}] is a domain user".format(user_name))
                return True

            self.log.info("User [{0}] is a local user".format(user_name))
            return False

        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def is_client_activated(self, client, plan, retry_interval=10, time_limit=12, hardcheck=True):
        """ Check if client is activated and associated to plan

            Args:
                client            (str)    -- Client name

                plan              (str)    -- Plan for which the client needs to be checked for
                                              association

                retry_interval    (int)    -- Interval (in seconds), checked in a loop. Default = 10

                time_limit        (int)    -- Time limit to check for. Default (in minutes) = 12

                hardcheck         (bool)   -- If True, function will exception out in case client is
                                              not activated. If False, function will return with
                                              non-truthy value

            Returns:
                True/False        (bool)   -- In case client gets activated/or not

            Raises:
                Exception if :

                    - failed during execution of module
                    - client is not ready

        """
        try:
            client_group = plan + ' clients'
            self.log.info(
                """Waiting for client [{0}] association with Plan's client group [{1}]""".format(
                    client, client_group)
            )
            clientgroup = self._commcell.client_groups.get(client_group)
            assoc_clients = clientgroup.associated_clients
            assoc_clients = [each_client.lower() for each_client in assoc_clients]
            time_limit = time.time() + time_limit * 60
            while True:
                if (assoc_clients and client in assoc_clients) or (time.time() >= time_limit):
                    break
                else:
                    self.log.info("Waiting for [{0}] seconds. Client not activated.".format(retry_interval))
                    time.sleep(retry_interval)
                    clientgroup.refresh()
                    assoc_clients = clientgroup.associated_clients
                    assoc_clients = [each_client.lower() for each_client in assoc_clients]

            if not (assoc_clients and client in assoc_clients):
                if not hardcheck:
                    return False

                raise Exception("Failed to activate. Client [{0}] did not get associated to plan.".format(client))

            self.log.info("Client [{0}] is activated and associated to plan [{1}]".format(client, plan))
            return True

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def is_device_associated(self, pre_machine_count, retry_interval=20, time_limit=7, hardcheck=True):
        """ Check if new device got associated to company. Before calling the module, make sure installation has
            completed on client and user is waiting for the device to get associated to company post client
            activation

            Args:

                pre_machine_count (int)    -- Machine count for company pre client installation.

                retry_interval    (int)    -- Interval (in seconds), checked in a loop. Default = 20

                time_limit        (int)    -- Time limit to check for. Default (in minutes) = 7

                hardcheck         (bool)   -- If True, function will exception out in case device is not associated
                                              If False, function will return with non-truthy value

            Returns:
                True/False        (bool)   -- In case device is/(is not) associated to company

            Raises:
                Exception if :

                    - failed during execution of module
                    - device is not associated

        """
        try:
            pre_machine_count = self._company.machine_count
            self.log.info("""Number of devices in company [{1}] *before client activation: [{0}]"""
                          .format(pre_machine_count, self._company_name))
            company = self._commcell.organizations.get(self._company_name)
            company.refresh()
            post_machine_count = company.machine_count

            time_limit = time.time() + time_limit * 60
            while True:
                if (post_machine_count > pre_machine_count) or (time.time() >= time_limit):
                    break
                else:
                    self.log.info("Waiting for [{0}] seconds. New device not associated yet.".format(retry_interval))
                    time.sleep(retry_interval)
                    company.refresh()
                    post_machine_count = company.machine_count

            if not post_machine_count > pre_machine_count:
                if not hardcheck:
                    return False

                raise Exception("Failed to associate new device to company [{0}]".format(self._company_name))

            self.log.info("New device is associated to company [{0}]".format(self._company_name))
            self.log.info("""Number of devices in company [{1}] *after association: [{0}]"""
                          .format(company.machine_count, self._company_name))
            return True

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def get_company_clients(self, port=80, protocol='http'):
        """Returns the list of clients of the company

        Args:
            port        : port used by webconsole tomcat
            protocol    : http or https

        Raises:
                        Exception:
                            - if failed to update data in DB
        """
        clients = []
        company_id = self._company.organization_id
        query = f'''DECLARE @inClientId INT = 0/*GetAllClients*/;
                    DECLARE @inSCGId INT = 0/*SCGProcessing*/;
                    select name from app_client where id in ((
                     SELECT clientId FROM dbo.scgV2CompanyClientAssociations('=', {company_id}  , @inClientId, @inSCGId )
                    )  UNION  (
                     SELECT clientId FROM dbo.scgV2CompanyClientInstallAssociations('=', {company_id}  , @inClientId, @inSCGId )
                    ));'''

        records = self.options_selector.update_commserve_db_via_cre(sql=query, port=port, protocol=protocol)
        for client in records:
            clients.append(client[0])

        return clients

    def checkfor_company_secondplan(self, plan_name):
        """Verify Second plan associated with company or not"""
        plans_list = self._company.plans
        if not plan_name.lower() in plans_list:
            raise Exception(
                "Second plan [{0}] is not associated with Company [{1}].Please associate it ".format(
                    plan_name, self._company_name)
            )
        self.log.info("Second Plan [{0}] is associated to company [{1}]".format(plan_name, self._company_name))

    def delete_domain(self, domain_name):
        """ Deletes a domain from the commcell

            Args:

                domain_name (str)    -- Domain name

            Returns:

            Raises:
                Exception if :
                    - failed during execution of module
        """
        try:
            if self._commcell.domains.has_domain(domain_name):
                self.log.info("Deleting domain [{0}] from commcell".format(domain_name))
                self._commcell.domains.delete(domain_name)
            else:
                self.log.info("Domain [{0}] does not exist on commcell".format(domain_name))

            if self._commcell.domains.has_domain(domain_name):
                raise Exception("Failed to delete domain [{0}]".format(domain_name))

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def cleanup(self):
        """ Cleans up the environment modified on commcell by the helper class """

        self.log.info("***Cleaning up environmental changes for organization class***")

        # Remove the users added to blacklisted user groups as part of testcases.
        if bool(self.blacklist_user_map):
            for user_group in self.blacklist_user_map:
                users = self.blacklist_user_map[user_group]
                for _user in users:
                    self.remove_user_from_blacklisted_group(_user, user_group)

        if self.blacklist_user_groups:
            for user_group in set(self.blacklist_user_groups):
                self.delete_blacklisted_group(user_group)

    @property
    def commcell_default_plan(self):
        """ Read only property for commcell_default_plan """
        return self._commcell_default_plan

    @commcell_default_plan.setter
    def commcell_default_plan(self, plan_name):
        """
        Args:
            plan_name (str)    - Plan name

            Sets default plan at Commcell level
            This is independent of the Organization as this sets the default plan with
            organization id as 0
            AC->Administration->Commcell

        Returns:
            None
        """

        self.log.info("Setting default plan [%s] for Commcell, with organization id = 0", plan_name)
        self._commcell.set_default_plan(plan_name)
        self._commcell_default_plan = plan_name

    @property
    def default_plan(self):
        """Returns the Default Plan associated to this Organization."""
        return self._default_plan

    @default_plan.setter
    def default_plan(self, value):
        """Update the default plan associated with the Organization."""

        self.log.info("Company's [{0}] default plan:[{1}]".format(self._company_name, self._company.default_plan))

        default_plan = self._company.default_plan
        default_plan = default_plan[0] if isinstance(default_plan, list) else default_plan
        if default_plan == value:
            self.log.info("""Skipped setting company's default plan, as it is already set to this plan [{0}]"""
                          .format(value))
        else:
            self.log.info("Setting default plan [{0}] for Company [{1}]".format(value,
                                                                                self._company_name))

            self._company.default_plan = {'Laptop Plan': value}
            default_plan = self._company.default_plan
            default_plan = default_plan[0] if isinstance(default_plan, list) else default_plan
            assert default_plan == value, "Failed to set company's default plan."

            self.log.info("Successfully validated and assigned default plan [{0}] for company [{1}]"
                          "".format(value, self._company_name))


    @property
    def company_name(self):
        """Returns the company name"""
        return self._company_name

    @property
    def company(self):
        """Returns the company object"""
        return self._company

    @company.setter
    def company(self, value):
        """Creates company object based on given company name: (value)"""
        try:
            self._company = self._commcell.organizations.get(value)
            self._company_name = value

        except Exception as excp:
            raise Exception("\n Failed to get company object {0} {1}".format(inspect.stack()[0][3],
                                                                             str(excp)))

    @property
    def tenant_client_group(self):
        """ Returns the tenant_client_group for the given company """
        return self._tenant_client_group

    @tenant_client_group.setter
    def tenant_client_group(self, plan_name):
        """Sets the Company's tenant client group for the given plan_name"""
        self._tenant_client_group = plan_name + ' clients'

    @property
    def machine_count(self):
        """ Returns the client count associated for the given company """
        return self._machine_count

    @machine_count.setter
    def machine_count(self, value):
        """ Set's the Tenant company's machine count """
        self._machine_count = value

    @property
    def shared_laptop_usage(self):
        """ Shared Laptop mode for the given company """
        if not self._company:
            self.log.info("Enabling shared laptop at commcell")
            self._commcell.enable_shared_laptop()
            self.log.info("Shared Laptop Usage is enabled for commcell")
            return True
        else:
            if self._company.shared_laptop:
                self.log.info('Shared Laptop Usage is enabled for Organization [{0}]'.format(self.company))
            else:
                self.log.info('Shared Laptop Usage is NOT enabled for Organization [{0}]'.format(self.company))
            return self._company.shared_laptop

    @shared_laptop_usage.setter
    def shared_laptop_usage(self, value):
        """ Set's the shared laptop usage for the organization

        Args:

        value (bool): True/False
            False: Enable Shared Laptop usage
            True: Disable Shared Laptop usage

        """
        operation = "Disabling" if not value else "Enabling"
        self.log.info('{0} Shared Laptop Usage for Organization [{1}]'.format(operation, self.company))
        self._company.shared_laptop = value


class RoleHelper:
    """Helper class to perform Roles REST API operations"""

    def __init__(self, commcell, role=None):
        """Initializes RoleHelper object

            Args:
                commcell    (obj)   -- Commcell object

                role        (str)   -- Role name
        """
        self._role = None
        if role:
            self._role = role
        self.log = logger.get_log()
        self.commcell_obj = commcell
        self.roles_obj = Roles(self.commcell_obj)
        self._csdb = database_helper.CommServDatabase(self.commcell_obj)
        self._utility = options_selector.OptionsSelector(self.commcell_obj)

    def create_role(self, role_name, permission_list=None, category_list=None,
                    random_permission=False, validate=True):
        """creates new role

             Args:
                 role_name          (str)   --  Name of the role to be created

                 category_list      (list)  --  role will be created with all the permissions
                                                associated with this category

                    e.g.: category Name=Client :role will have all permisisons from
                                        this category.
                    e.g.: category Name=Client Group :role will have all permissions
                                        from this category
                    e.g.: category Name=commcell :role will have all permissions from
                                        this category

                 validate         (boolean) -- Specifies whether to validate the role permissions/categories

                 permission_list (list)     --  permission array which is to be updated
                     e.g.: permisison_list=["View", "Agent Management", "Browse"]

                 random_permission   (bool) --  generates random permissions and categories if value
                                                is set to True
             Returns:
                 Role Object
         """
        self.log.info("creating role %s" % role_name)
        if random_permission:
            self.log.info("User preferred to generate random capabilities ")
            permission_list, category_list = self.generate_permissions_categories()
            self.log.info("creating role with randomly generated permission list and categoryName "
                          "list")
        self._role = self.roles_obj.add(rolename=role_name, permission_list=permission_list,
                                        categoryname_list=category_list)
        if validate:
            self._validate_role_permissions(request_type='Update', permission_list=permission_list,
                                            category_list=category_list)
        self.log.info("created role successfully %s" % self._role)
        return self._role

    def random_permissions(self):
        """Generates 5 Random Permissions

             Returns:
                 list of 5 randomly selected permissions from DB
         """
        self.log.info("Generating random permissions")
        permission_list = []
        _query = ("select permissionName from UMPermissions where categoryId in "
                  "(select id from UMCategories where flags=0 and hierarchyLevel=2)")
        self._csdb.execute(_query)
        permission_names = self._csdb.fetch_all_rows()
        # fetching total count of permissions from UMPermissions
        count = len(permission_names)
        #generating random numbers to pick up 5 permissions from the permission list
        permission_ids = random.sample(range(1, count), 5)
        for permission_id in permission_ids:
            permission_list.extend(permission_names[permission_id])
        self.log.info("Generated Random List of permissions :%s" % permission_list)
        return permission_list

    def random_category(self):  # change the name of the function
        """Generates 3 Random Category

             Returns:
                 list of 3 randomly selected categories from DB
         """
        self.log.info("Generating random Category Names")
        category_list = []
        # storing all categories in the lists
        _query = "select categoryName from UMCategories where flags = 0 and hierarchyLevel =2"
        self._csdb.execute(_query)
        categorynames = self._csdb.fetch_all_rows()
        # fetching total count of category names from UMCatagories
        count = len(categorynames)
        # generating random numbers to pick up 3 category names from the category list
        category_ids = random.sample(range(1, count), 3)
        for category_id in category_ids:
            category_list.extend(categorynames[category_id])
        self.log.info("Generated Random List of Category Names :%s" % category_list)
        return category_list

    def generate_permissions_categories(self):
        """Generates 5 Random permissions and 3 Random Category

             Returns:
                 list of 5 randomly selected permissions from DB
                 list of 3 randomly selected categories from DB
         """
        _permissions = self.random_permissions()
        _categories = self.random_category()
        return _permissions, _categories

    def delete_role(self, role_name):
        """Deletes the role passed
        Args:
            role_name        (str)  -- object of role to be deleted

            Raises:
                Exception:
                    if role deletion is unsuccessful

        """
        self.log.info("performing Delete Operation on role: %s", role_name)
        role = self.roles_obj.has_role(role_name=role_name)
        if role:
            self.roles_obj.delete(role_name)
            self.log.info("role deletion is Successful")
        else:
            self.log.info("Specified role is not present on the CommCell %s", role_name)

    @property
    def role(self):
        """Returns the role object of this commcell role"""
        return self._role

    @role.setter
    def role(self, role_object):
        """initialize role object"""
        self._role = role_object

    def update_role_properties(self, modification_request, random_flag=None,
                               permissions_list=None, category_list=None, **kwargs):
        """Update, Overwrite, deletes capabilities of the passed role
        Args:
            modification_request    (str)   --  Update, Overwrite, Delete operation for roles

            random_flag             (bool)  --  no permission list or category is required when
                                                this flag is set to True

            permission_list         (list)  --  new set of permissions assigned to role

            category_list           (list)  --  new set of category permissions assigned on role

            kwargs:

                name                (str)   --  New name to assigned to role

                description         (str)   --  New description to be assigned to role

                status              (bool)  --  Status flag for role
        """
        for key, value in kwargs.items():
            getattr(self, '_update_role_{0}'.format(key))(value)

        if random_flag:  # club both and add new function and call it here
            self.log.info("User preferred to generate random capabilities")
            permissions_list, category_list = self.generate_permissions_categories()
            self.log.info("updating role with randomly generated permissions and categories")

        if permissions_list or category_list:
            self._role.modify_capability(
                request_type=modification_request, permission_list=permissions_list,
                categoryname_list=category_list)
            self._validate_role_permissions(request_type=modification_request,
                                            permission_list=permissions_list,
                                            category_list=category_list)

    def _validate_role_permissions(self, request_type, permission_list, category_list):
        """validates capabilities present on the role with db values
        Args:
            request_type        (str)   --  Update, Overwrite, Delete operation for roles

            permission_list     (list)  --  set of permissions needed to be verified

            category_list       (list)  --  set of category permissions needed to be validated

            returns:
                True    :   if role capability validation is successful
            raises:
                Exception:
                    if Capability validation fails

        """

        # Exceptional permissions

        permission_mappings = {
            "Data Protection Operations": "Data Protection/Management Operations",
            "Delete CVApp": "DBOnly",
            "DLP": "DBOnly",
            "Operations on Storage Policy\Copy": "Operations on Storage Policy \  Copy",
            "Edit Storage Policy\Copy": "Edit Storage Policy \ Copy",
            "EndUser Access": "End User Access",
            "Install client": "Install Client",
            "Install Package/Update": "Install Package / Update",
            "Data Cube View": "DBOnly",
            "Execute CVApp": "DBOnly",
            "Create CVApp": "DBOnly",
            "Full Machine Recovery": "In Place Full Machine Recovery",
            "Out of Place Recover": "Out - of - Place Recover",
            "Credential Policy Creator": "DBOnly",
            "Delete Storage Policy\Copy": "Delete Storage Policy \ Copy",
            "Data Cube Edit": "DBOnly",
            "Edit CVApp": "DBOnly",
            "Data Cube Execute": "DBOnly",
            "View Reports": "View Royalty Report",
            "Operators": "Management",
            "Admins": "Administration",
            "Delete Client Group": "Delete Server group"
        }

        category_mappings = {
            "Report": "Reports",
            "DataSource": "Datasource",
            "Data Cube": "Data Cube Source",
            "CVApp": "DBOnly",
            "Client Group": "Server group"
        }

        temp_permission_list = []
        temp_category_list = []
        self.log.info('validating permissions and categories')
        list_of_permissions = self._role._role_permissions
        permissions = list_of_permissions['permission_list']
        categories = list_of_permissions['category_list']
        permission_arr = []
        self.log.info('permission validation started')
        if permission_list is not None:
            permission_arr = list(set(permission_list) - set(permissions))
            if permission_arr:
                for each in permission_arr:
                    if each in permission_mappings.keys():
                        if permission_mappings[each] in permissions or 'DBOnly':
                            continue
                    else:
                        temp_permission_list.append(each)
        if temp_permission_list:
            self.log.info("%s: these permissions could be part of categories"
                          % temp_permission_list)
            self.log.info("Generating the category list for such permissions to "
                          "validate whether category is present on the role")
            permission_set = str(temp_permission_list)
            permission_set = str.replace(permission_set, r"\\", "\\")
            permission_set = permission_set.replace('[', '(')
            permission_set = permission_set.replace(']', ')')
            query_1 = ("select categoryName from UMCategories where id in "
                       "(select categoryId from UMPermissions where permissionName in %s)"
                       % permission_set)
            cat, cat1 = self._utility.exec_commserv_query(query_1)
            category_list.extend(list(set(cat) - set(categories)))
        if category_list:
            self.log.info("new set of categories for validation: %s " % category_list)
            self.log.info("categories list present on the role: %s" % categories)
            diff_categories = list(set(category_list) - set(categories))
            if diff_categories:
                for each in diff_categories:
                    if each in category_mappings.keys():
                        if category_mappings[each] in categories or 'DBOnly':
                            continue
                    temp_category_list.append(each)
                if request_type != 'Delete' and temp_category_list:
                    self.log.info("These categories are missing on role: %s" % temp_category_list)
                    raise Exception("Not all categories present on the role")
                else:
                    self.log.info(
                        "sucessfully deleted role permissions")
        self.log.info("Capability Validation is successful on the role")
        return True

    def _update_role_status(self, status):
        """updates the role status
        Args:
            status        (str)  -- True -Enable role, False -Disable role

            Raises:
                Exception:
                    if role status update fails
        """
        role_status = {
            0: False,
            1: True
        }
        self.log.info("setting up role status")
        self._role.status = status
        flag = self._fetch_role_property(dbvalue='disabled', table_name='UMRoles',
                                         search_value='name', comp_value=self._role.role_name)
        stat = role_status[int(flag[0][0])]
        if self._role.status is not stat:
            raise Exception("failed to modify role status")
        self.log.info("successfully modified the role status")

    def _update_role_description(self, description):
        """updates the role description
        Args:
            description        (str)  -- Description of the role

            Raises:
                Exception:
                    if role description update fails
        """
        self.log.info("setting up description for role")
        self._role.role_description = description
        self._role.description = description
        desc = self._fetch_role_property(dbvalue='description', table_name='UMRoles',
                                         search_value='name', comp_value=self._role.role_name)
        description1 = "".join(desc)
        self.log.info("role description from json: %s" % self._role.description)
        self.log.info("role description from db: %s" % description1)
        if self._role.description != description1:
            raise Exception("failed to modify role description")
        self.log.info("description for role is successfully updated")

    def _update_role_name(self, new_name):
        """updates the role name
        Args:
            new_name        (str)  -- Name of the role

            Raises:
                Exception:
                    if role name update fails
        """
        self.log.info("updating role with new name:%s" % new_name)
        self._role.role_name = new_name
        name1 = self._fetch_role_property(dbvalue='name', table_name='UMroles',
                                          search_value='id', comp_value=self._role.role_id)
        self.log.info("role name from json: %s" % self._role.role_name)
        self.log.info("role name from db: %s" % name1)
        if self._role.role_name != name1:
            raise Exception("failed to modify role name")
        self.log.info("role name modification is successful")

    def _fetch_role_property(self, dbvalue, table_name, search_value, comp_value):
        """Gets role proerties from db for validation
        Args:
            dbvalue         (str)   --  expected column value from db

            table_name      (str)   --  name of the table to query data

            search_value    (str)   --  column condition value

            comp_value      (str)   --  comparison value

            returns:
                DB result set
        """
        query_1 = "select {0} from {1} where {2}='{3}'".format(dbvalue, table_name,
                                                               search_value, comp_value)
        self._csdb.execute(query_1)
        result = self._csdb.fetch_one_row()
        result1 = "".join(result)
        return result1

    def select_random_role(self, commcell=False) -> str:
        """Helper class to perform Roles REST API operations
        Args:
            commcell    (bool, optional)  -- If True, returns a random role which belongs to the commcell, 
                                             Defaults to False

        Returns:
            Randomly selected role.
        """
        if commcell:
            query1 = ("SELECT NAME FROM UMROLES WHERE FLAGS&0X004 = 0 AND ID NOT IN (SELECT ENTITYID FROM "
                      "APP_COMPANYENTITIES WHERE ENTITYTYPE = 120)")
            self._csdb.execute(query1)
            role_names = {roles[0] for roles in self._csdb.fetch_all_rows() if roles[0] != ''}
        else:
            role_names = self.commcell_obj.roles.all_roles
        new_role = random.choice(list(role_names))
        self.log.info("Random role selected for association dictionary:%s", new_role)
        return new_role

    def cleanup_roles(self, marker):
        """
            Delete roles that has provided marker / string

            Args:
                marker      (str)   --  marker tagged to roles for deletion
        """
        self.roles_obj.refresh()
        for role in self.roles_obj.all_roles:
            if marker.lower() in role:
                try:
                    self.roles_obj.delete(role)
                    self.log.info("Deleted role - {0}".format(role))
                except Exception as exp:
                    self.log.error(
                        "Unable to delete role {0} due to {1}".format(
                            role,
                            str(exp)
                        )
                    )

    def validate_roles_cache_data(self) -> bool:
        """
        Validates the data returned from Mongo cache for roles collection.

        Returns:
            bool: True if validation passes, False otherwise
        """
        cache = self.roles_obj.get_roles_cache(enum=False)
        out_of_sync = []

        for role, cache_data in cache.items():
            self.log.info(f'Validating cache for roles: {role}')
            role_prop = self.roles_obj.get(role)
            validations = {
                'roleId': int(role_prop.role_id),
                'status': role_prop.status,
            }

            for key, expected_value in validations.items():
                self.log.info(f'Comparing key: {key} for role: {role}')
                if cache_data.get(key) != expected_value:
                    out_of_sync.append((role, key))
                    self.log.error(f'Cache not in sync for prop "{key}". Cache value: {cache_data.get(key)}; '
                                   f'csdb value: {expected_value}')

            if cache_data.get('company') == 'Commcell':
                company_in_cache = cache_data.get('company').lower()
            else:
                company_in_cache = self.commcell_obj.organizations.get(cache_data.get('company')).domain_name.lower()

            self.log.info(f'Comparing key: company for role: {role}')
            if company_in_cache != role_prop.company_name.lower():
                out_of_sync.append((role, 'company'))
                self.log.error(f'Cache not in sync for prop "company". Cache value: {cache_data.get("company")} '
                               f'; csdb value: {role_prop.company_name}')

        if out_of_sync:
            raise Exception(f'Validation Failed. Cache out of sync: {out_of_sync}')
        else:
            self.log.info('Validation successful. All the roles cache are in sync')
            return True

    def validate_sort_on_cached_data(self) -> bool:
        """
        Method to validate sort parameter on entity cache API call

        Returns:
            bool: True if validation passes, False otherwise
        """
        # setting locale for validating sort
        locale.setlocale(locale.LC_COLLATE, 'English_United States')

        columns = ['roleName', 'roleId', 'status', 'company']
        unsorted_col = []
        for col in columns:
            optype = random.choice([1, -1])
            # get sorted cache from Mongo
            cache_res = self.roles_obj.get_roles_cache(fl=[col], sort=[col, optype])
            # sort the sorted list
            if col == 'clientName':
                cache_res = list(cache_res.keys())
                res = sorted(cache_res, key=lambda x: locale.strxfrm(str(x)), reverse=optype == -1)
            else:
                cache_res = [[key, value.get(col)] for key, value in cache_res.items() if col in value]
                if all(isinstance(item[1], int) for item in cache_res):
                    res = sorted(cache_res, key=lambda x: x[1], reverse=optype == -1)
                else:
                    res = sorted(cache_res, key=lambda x: locale.strxfrm(str(x[1])), reverse=optype == -1)
            # check is sorted list got modified
            if res == cache_res:
                self.log.info(f'sort on column {col} working.')
            else:
                self.log.error(f'sort on column {col} not working')
                unsorted_col.append(col)
        if not unsorted_col:
            self.log.info("validation on sorting cache passed!")
            return True
        else:
            raise Exception(f"validation on sorting cache Failed! Column : {unsorted_col}")

    def validate_limit_on_cache(self) -> bool:
        """
        Method to validate limit parameter on entity cache API call

        Returns:
            bool: True if validation passes, False otherwise
        """
        cache = self.roles_obj.get_roles_cache()

        # generate random limit
        test_limit = random.randint(1, len(cache.keys()))
        limited_cache = self.roles_obj.get_roles_cache(limit=['0', str(test_limit)])
        # check the count of entities returned in cache
        if len(limited_cache) == test_limit:
            self.log.info('Validation for limit on cache passed!')
            return True
        else:
            self.log.error(f'limit returned in cache : {len(limited_cache)}; expected limit : {test_limit}')
            raise Exception(f"validation for limit on cache Failed!")

    def validate_search_on_cache(self) -> bool:
        """
        Method to validate search parameter on entity cache API call

        Returns:
            bool: True if validation passes, False otherwise
        """
        # creating a test role

        role_name = f"caching_automation_{random.randint(0, 100000)} - roles"
        role = self.create_role(role_name=role_name, random_permission=True, validate=False)

        if role:
            # calling the API with search param
            response = self.roles_obj.get_roles_cache(search=role.role_name)
            # checking if test group is present in response
            if len(response.keys()) == 1 and [True for key in response.keys() if key == role.role_name]:
                self.log.info('Validation for search on cache passed')
                return True
            else:
                self.log.error(f'{role.role_name} is not returned in the response')
                raise Exception("Validation for search on cache failed!")
        else:
            raise Exception('Failed to create role. Unable to proceed.')

    def validate_filter_on_cache(self, filters: list, expected_response: list) -> bool:
        """
        Method to validate fq param on entity cache API call

        Args:
            filters (list) -- contains the columnName, condition, and value
                e.g. filters = [['roleName','contains', test'],['status','eq', 'Enabled']]
            expected_response (list) -- expected list of roles to be returned in response

        Returns:
            bool: True if validation passes, False otherwise
        """
        if not filters or not expected_response:
            raise ValueError('Required parameters not received')

        try:
            res = self.roles_obj.get_roles_cache(fq=filters)
        except Exception as exp:
            self.log.error("Error fetching roles cache")
            raise Exception(exp)

        missing_roles = [role for role in expected_response if role not in res.keys()]

        if missing_roles:
            raise Exception(f'Validation failed. Missing roles: {missing_roles}')
        self.log.info("validation for filter on cache passed!")
        return True


class SecurityHelper(object):
    """Helper class to perform Roles REST API operations"""

    def __init__(self, commcell, role=None):
        """Initializes SecurityHelper object

            Args:
                commcell    (obj)   -- Commcell object

                role        (str)   -- Role name
        """
        self._role = None
        if role:
            self._role = role
        self.log = logger.get_log()
        self.commcell_obj = commcell
        self.role_helper = RoleHelper(self.commcell_obj)
        self._csdb = database_helper.CommServDatabase(self.commcell_obj)
        self._sqlite = database_helper.SQLite(database_file_path=os.path.join(os.path.dirname(
            os.path.realpath(__file__)), securityconstants.SQLiteDB))
        self._utility = options_selector.OptionsSelector(self.commcell_obj)
        self.user = None
        self.usergroup = None
        self.permissions = {
            'Administrative Management': 1,
            'Agent Management': 2,
            'Data Protection/Management Operations': 3,
            'In Place Recover': 4,
            'MediaAgent Management': 5,
            'Report Management': 6,
            'Agent Scheduling': 7,
            'Create Storage Policy': 8,
            'Job Management': 9,
            'Out-of-Place Recover': 10,
            'User Management': 11,
            'Create Client Group': 12,
            'Change Client Associations': 13,
            'Browse': 14,
            'Operations on Storage Policy \\  Copy': 15,
            'Add, delete and modify a user': 16,
            'Add, delete and modify a user group': 17,
            'Create Schedule Policy': 18
        }
        self.entity_types = {
            'commCellName': 1,
            'clientGroupName': 2,
            'clientName': 3,
            'mediaAgentName': 4,
            'storagePolicyName': 5,
            'userName': 6,
            'userGroupName': 7,
            'providerDomainName': 8
        }

    def gen_random_entity_types_dict(self, no_of_entity_types, no_of_assoc=1, commcell=False):
        """Generate dictionary consisting of randomly selected dictionary types and roles

        no_of_entity_types  (Int)   -   no entity types to be generated

        no_of_assoc         (Int)   -   no. of associations that you want to generate randomly
                                        Basically no. of roles

        commcell            (bool)  -   Select roles of only msp environment

        Returns:
            dictionary consisting of different roles and entity types

        """

        entity_dict = {}
        for value in range(0, no_of_assoc):
            assoc1 = {}
            for entity_type in range(0, no_of_entity_types):
                assoc = self.gen_entity_role_dict(no_of_entities=2)
                assoc1.update(assoc)
            role_name = self.role_helper.select_random_role(commcell=commcell)
            assoc1['role'] = [role_name]
            entity_dict["assoc" + str(value)] = assoc1
        return entity_dict

    def generate_random_entity_dict(self, entity_type=None, no_of_assoc=1, entities_count=1):
        """Generates and returns random entity and role

        entity_type         (Str)   -   entity name used in xml
                                        example: 'clientName', 'workflowName'.. etc

        no_of_assoc         (Int)   -   no. of associations that you want to generate randomly

        entities_count      (Int)   -   no. of entities you want to select for each association

        Returns:
            dictionary consisting of different roles and entity types and entities

        """
        entity_dict = {}
        for value in range(0, no_of_assoc):
            role = self.role_helper.select_random_role()
            assoc = self.gen_entity_role_dict(entity_type=entity_type,
                                              no_of_entities=entities_count,
                                              role_name=role)
            entity_dict["assoc" + str(value)] = assoc
        self.log.info('entity_dict: %s', entity_dict)
        self.log.info('Enity-Role-Dictionary')
        return entity_dict

    def gen_entity_role_dict(self, entity_type=None, entities=None, no_of_entities=1,
                             role_name=None):
        """Generates and returns entity and role association not association dictionary
        Args:
            entity_type     (str)   : entity name used in xml

            entities        (list)  : list of entities belonging to entity type

            no_of_entities  (int)   : No. of entities to be selected of same entity_type

            role_name       (str)   : role name for association

        Raises:
                Exception:
                    if entities for specified entity_type are not present on the commcell

        Returns:
            single association blob consisting of entities and role
            example:
            1) {'schedulePolicyName': ['system created for ddb subclients',
                'system created ddb verification schedule policy']} if role is not passed.
                This can be used to form multiple entities with single role with help of function
                gen_random_entity_types_dict()
                example:
                {'assoc0': {'workflowName': ['create collaborative shares', 'rdsmigration'],
                'schedulePolicyName': ['system created autocopy schedule', 'server plan'],
                'role': ['all users laptops']},
                'assoc1': {'clientName': ['aprabhu_serv', 'client-point1_2'],
                'storagePolicyName': ['test_pool1', 'commservedr'], 'role': ['client admins']}}

            2) if role is password:
                Single Association will be generated and returned with role
                {'schedulePolicyName': ['system created for ddb subclients',
                                        'system created ddb verification schedule policy'],
                'role': ['client group creator']}}

        """
        entity_type_dict1 = {'clientName': 'clients',
                             # 'mediaAgentName':self.commcell_obj.media_agents.all_media_agents,
                             'workflowName': 'workflows',
                             'alertName': 'alerts',
                             'libraryName': 'disk_libraries',
                             'storagePolicyName': 'storage_policies',
                             'schedulePolicyName': 'schedule_policies',
                             'userGroupName': 'user_groups',
                             'providerDomainName': 'domains',
                             'clientGroupName': 'clientgroups',
                             'userName': 'users',
                             'roleName': 'roles',
                             # 'policyName': self.commcell_obj.monitoring_policies.
                             # all_monitoring_policies,
                             'commCellName': 'commCellName'
                             }
        if not entity_type:
            self.log.info("*********Randomly selecting entity_type***********")
            entity_type = random.choice(list(entity_type_dict1.keys()))
            self.log.info('selected entity_type:%s', entity_type)
        else:
            self.log.info("User passed entity_type:%s", entity_type)

        if entities:
            random_entities = entities
        else:
            if entity_type == 'commCellName':
                random_entities = [self.commcell_obj.commserv_name]
                self.log.info("commcell name is selected:%s", random_entities)
            else:
                attribute = 'all_' + entity_type_dict1[entity_type]
                if entity_type == 'clientGroupName':
                    colletion = getattr(getattr(self.commcell_obj, 'client_groups'), attribute)
                else:
                    colletion = getattr(getattr(self.commcell_obj,
                                                entity_type_dict1[entity_type]), attribute)
                if not len(colletion) >= no_of_entities:
                    raise Exception("very less entities present on the commcell for {0} !!!"
                                    .format(entity_type))
                else:
                    random_entities = random.sample(list(colletion), no_of_entities)

        if random_entities:
            self.log.info("Selected entities for associations:%s", random_entities)
            assoc1 = {
                entity_type: random_entities,
            }
            if role_name:
                assoc1.setdefault('role', [role_name])
            self.log.info("designed entity-role association: %s", assoc1)
            return assoc1

    def validate_security_associations(self, entity_dict, name, isuser=1):
        """Validates security Associations on user and userggroup
        Args:
            entity_dict         (Dict)  :   entity-role association dict

            name                (Str)   :   could be user name or usergroup name

            isuser              (Bool)  :   1= if name is of user, 0= if name is of usergroup

        Raises:
                Exception:
                    if any of the association doesn't present on the user or usergroup.
        """
        valid_list1 = []
        keys = []
        dictionary = {}
        count = 0
        if isuser:
            self.user = self.commcell_obj.users.get(name)
            security_dict = self.user.user_security_associations
        else:
            self.usergroup = UserGroup(self.commcell_obj, name)
            security_dict = self.usergroup.associations
        if not security_dict:
            raise Exception("There is No Role-Entity-Association present on the {0}".format(name))

        for entity_type, entities in security_dict.items():
            entities.remove(entities[0])
            for each_value in entities:
                if 'invalid' in each_value:
                    keys.extend(str(entity_type))
                    break
        for key in keys:
            del security_dict[int(key)]

        formatted_dict = {}
        security_list = []
        list1 = []
        dict1 = {}

        for key, values in security_dict.items():
            if (key + 1) in security_dict.keys():
                if security_dict[key][1] == security_dict[key + 1][1]:
                    list1.append(values[0])
                else:
                    list1.extend(security_dict[key])
                    dict1.setdefault(count, list1)
                    count += 1
                    list1 = []
            else:
                count += 1
                list1.extend(security_dict[key])
                dict1.setdefault(count, list1)
                count = 0

        for key, values in security_dict.items():
            if values[1] not in security_list:
                security_list.extend(values)
            else:
                security_list.append(values[0])
        formatted_dict.setdefault(0, security_list)

        for entity_type, entity in entity_dict.items():
            for key, value in entity.items():
                entity_list = [item.lower() for item in value]
                valid_list1.extend(entity_list)
            valid_list1.sort()
            dictionary.setdefault(count, valid_list1)
            valid_list1 = []
            count += 1

        self.log.info("Association dictionary present on entity:%s", entity_dict)
        self.log.info("Formatted Associations fetched from entity properties:%s", security_dict)
        self.log.info("Formatted dictionary used for validation:%s", dictionary)

        self.log.info("Security Validation started!!")
        for entities1 in dictionary.values():
            for entity_type2, entities2 in dict1.items():
                if set(entities1).issubset(set(entities2)):
                    self.log.info("validated:%s is present in %s", set(entities1), set(entities2))
                    break
                elif entity_type2 == len(dict1) - 1:
                    raise Exception(
                        "Security Validation failed!!: {0} is not present on {1} {2}".format(
                            entities1, name, entities2))
                else:
                    pass

    def return_association_details(self, user):
        """Returns list of lists containing entityType, entityName and permissionName

            Args:
                user      (str)   -- user name

            Returns:
                list consisting of list of entityName, entityType, permissionName
            example:
                    [
                    ['clientName', 'ClientEntityName', 'Agent Management'],
                    ['clientName', 'ClientEntityName', 'Browse'],
                    ['clientName', 'ClientEntityName', 'In Place Recover'],
                    ['commCellName', 'CommCellEntityName', 'Administrative Management'],
                    ['commCellName', 'CommCellEntityName', 'Add, delete and modify a user'],
                    ['commCellName', 'CommCellEntityName', 'Add, delete and modify a user group']
                    ]



        """
        user1 = self.commcell_obj.users.get(user)
        user_associations = user1.user_security_associations
        associations = []

        for each_asso in user_associations:
            asso1 = list(user_associations[each_asso])
            role = self.commcell_obj.roles.get(user_associations[each_asso][2])
            capabilities = role.permissions['permission_list']
            for each_permission in capabilities:
                list1 = [asso1[0], asso1[1], each_permission]
                associations.append(list1)
        self.log.info("Entity-Permission list is fetched from user associations: %s", associations)
        return associations

    def calculate_capability_bitmask(self, entity_permission_list):
        """Returns list of lists containing entityType, entityName and permissionName

            Args:
                entity_permission_list      (str)   --  list consisting of entityType and
                                                        permissionName
                                                        example- ['clientName', 'Agent Management'],
                                                                ['clientName', 'In Place Recover']


            Returns:
                Integer value: CapabilityBitMask
        """
        # Code required to Generate Capability Bit Mask for each operations
        '''
        entity_permission_list = [[['commCellName', 'Administrative Management']],
                                  [['commCellName', 'Administrative Management']],
                                  [['clientGroupName','Administrative Management']],
                                  [['clientName','Agent Management']],
                                  [['clientName','Agent Management']],
                                  [['clientName','Data Protection/Management Operations'],
                                  ['storagePolicyName','Operations on Storage Policy \\  Copy']],
                                  [['clientName','In Place Recover'],['clientName','Browse'],['clientName','Out-of-Place Recover']],
                                  [['clientGroupName','Agent Management']],
                                  [['commCellName', 'Administrative Management']],
                                  [['commCellName', 'Administrative Management']],
                                  [['mediaAgentName','MediaAgent Management']],
                                  [['commCellName','Report Management']],
                                  [['clientName', 'Agent Scheduling'],['clientName',
                                  'Data Protection/Management Operations']],
                                  [['clientName', 'Agent Scheduling'],['clientName',
                                  'In Place Recover']],
                                  [['commCellName', 'Administrative Management']],
                                  [['clientName', 'Agent Scheduling'],['clientName',
                                  'Data Protection/Management Operations']],
                                  [['commCellName', 'Create Storage Policy']],
                                  [['clientName', 'Job Management']],
                                  [['commCellName', 'Add, delete and modify a user']],
                                  [['commCellName', 'Add, delete and modify a user group']],
                                  [['commCellName', 'Create Client Group']]
                                  ]
        entity_types = {
            'commCellName': 1,
            'clientGroupName': 2,
            'clientName': 3,
            'mediaAgentName': 4,
            'storagePolicyName': 5,
            'userName': 6,
            'userGroupName': 7,
            'providerDomainName': 8,
        }

        for each_entry in entity_permission_list:
            total = 0
            for row in each_entry:
                #print("row:", row[0], row[1])
                mask = ((entity_types[row[0]]-1)*len(permissions))+(permissions[row[1]])
                value = pow(2, mask-1)
                total = total+value
            print('operation and mask:', each_entry, total)
        '''
        mask = ((self.entity_types[entity_permission_list[0]] - 1) * len(self.permissions)) + (
            self.permissions[entity_permission_list[1]])  # set zeroes for other permissions
        # in other entityType (-1:
        # is to exclude current entityType and set zero for other entityTypes)
        value = pow(2, mask - 1)
        self.log.info("Calculated mask for %s is %s:", entity_permission_list, value)
        return value

    def valid_operations_for_user(self, user_name):
        """Generates Intended Operations for User

            Args:

                user_name      (str)   -- Name of the User
        """
        entities = []
        entity_mask_value = {}
        associations = self.return_association_details(user=user_name)

        for each_asso in associations:
            user_associations = [each_asso[0], each_asso[2]]  # entityType and permission
            if user_associations[0] not in entities:  # collecting unique entityTypes
                self.log.info('Adding "%s" to entities list', user_associations[0])
                entities.append(user_associations[0])  # collect all entity types
            else:
                self.log.info('entity "%s" already present in the list', entities)
                # Ignore entityType if it is already present in the list

            entity_mask = self.calculate_capability_bitmask(entity_permission_list=
                                                            user_associations)
            if user_associations[0] not in entity_mask_value.keys():
                # if 'Add, delete and modify a user' in user_associations[1]:
                #     entity_mask_value[user_associations[0]] = entity_mask
                #  this condition is to reduce redundant entries to table
                entity_mask_value[user_associations[0]] = entity_mask
                sql_cmd1 = "Insert into EntityCapabilityBitMask values('%s', '%s', '%s')" % (
                    each_asso[1], user_associations[0], entity_mask_value[user_associations[0]])
                self._sqlite.execute(sql_cmd1)
            else:
                #  if entry is already present then update the mask value
                entity_mask_value[user_associations[0]] = entity_mask_value[user_associations[0]] \
                                                          + entity_mask
                sql_cmd1 = "update EntityCapabilityBitMask set EntityBitMask = %s where" \
                           " entityType = '%s'" % (entity_mask_value[user_associations[0]],
                                                   user_associations[0])
                self._sqlite.execute(sql_cmd1)
        self.log.info("Total Entities collected from user associations: %s", entities)

        sql_cmd2 = "Select Operation, OperationBitMask, RequiredEntityType, AdditionalEntityType " \
                   "from OperationCapabilities where RequiredEntityType in("
        for item in entities:
            sql_cmd2 += "'" + item + "'"
            if entities.index(item) != len(entities) - 1:
                sql_cmd2 += ","
        sql_cmd2 += ")"

        res = self._sqlite.execute(sql_cmd2).rows
        self.log.info("Total operations collected from Operations capabilities table: %s", res)
        sql_cmd3 = "select * from EntityCapabilityBitMask"
        entity_res = self._sqlite.execute(sql_cmd3)
        self.log.info("EntityCapabilityBit Mask generated for each entity present on user"
                      " associations:%s", entity_res.rows)

        entity_dict2 = {}
        for each_entity in entity_res.rows:
            entity = list(each_entity)
            if 'entityAssociated' in entity[1]:
                for each_entity in entities:
                    if 'entityAssociated' not in each_entity:
                        entity_dict2[each_entity] = [entity[0], entity[2]]
            entity_dict2[entity[1]] = [entity[0], entity[2]]  # entityType as key and
            # entityName and mask as values

        self.log.info('converting EntityCapabilityBit Mask to dictionary with entityType as'
                      ' key and entityName and mask as values:%s', entity_dict2)

        for each_op in res:
            operation1 = list(each_op)
            self.can_perform_operations(operation1, entity_dict2, user_name)

    def can_perform_operations(self, operation, entity_dict, username):
        """Inserts valid and intended operations list to DB.

            Args:

                operation       (str)   --  Each Operation that is being checked

                entity_dict     (dict)  --  Dict containing entityType as key and entityName
                                            and mask as values
                username        (str)   --  Name of the User
        """
        if operation[2] in entity_dict.keys():
            required_entity_mask = int(entity_dict[operation[2]][1])
            additional_entity_mask = 0
            if operation[3] not in ['None', operation[2]] and operation[3] in entity_dict.keys():
                additional_entity_mask = int(entity_dict[operation[3]][1])
            total_entity_mask = required_entity_mask + additional_entity_mask
            if int(operation[1]) & total_entity_mask == int(operation[1]):
                self.log.info('Successful Operation:%s', operation[0])
                sql_cmd1 = "Insert into IntendedResulttable values('%s', '%s', '%s', 1, '%s')" % (
                    operation[0], operation[2], entity_dict[operation[2]][0], username)
                self._sqlite.execute(sql_cmd1)
            else:
                self.log.info('expected failure Operation:%s', operation[0])
                sql_cmd3 = "Insert into IntendedResulttable values('%s', '%s', '%s', 0, '%s')" % (
                    operation[0], operation[2], entity_dict[operation[2]][0], username)
                self._sqlite.execute(sql_cmd3)

    # def update_operaion_capabilities(self):
    #
    #     # Code required to Generate Capability Bit Mask for each operations
    #
    #     entity_permission_list = [[['commCellName', 'Administrative Management']],
    #                               [['commCellName', 'Administrative Management']],
    #                               [['clientGroupName','Administrative Management']],
    #                               [['clientName','Agent Management']],
    #                               [['clientName','Agent Management']],
    #                               [['clientName','Data Protection/Management Operations'],
    #                               ['storagePolicyName','Operations on Storage Policy \\  Copy']],
    #                               [['clientName','In Place Recover'],['clientName','Browse'],['clientName','Out-of-Place Recover']],
    #                               [['clientGroupName','Agent Management']],
    #                               [['commCellName', 'Administrative Management']],
    #                               [['commCellName', 'Administrative Management']],
    #                               [['mediaAgentName','MediaAgent Management']],
    #                               [['commCellName','Report Management']],
    #                               [['clientName', 'Agent Scheduling'],['clientName',
    #                               'Data Protection/Management Operations']],
    #                               [['clientName', 'Agent Scheduling'],['clientName',
    #                               'In Place Recover']],
    #                               [['commCellName', 'Administrative Management']],
    #                               [['clientName', 'Agent Scheduling'],['clientName',
    #                               'Data Protection/Management Operations']],
    #                               [['commCellName', 'Create Storage Policy']],
    #                               [['clientName', 'Job Management']],
    #                               [['entityAssociated1', 'Add, delete and modify a user']],
    #                               [['entityAssociated2', 'Add, delete and modify a user group']],
    #                               [['commCellName', 'Create Client Group']]
    #                               ]
    #     entity_types = {
    #         'commCellName': 1,
    #         'clientGroupName': 2,
    #         'clientName': 3,
    #         'mediaAgentName': 4,
    #         'storagePolicyName': 5,
    #         'userName': 6,
    #         'userGroupName': 7,
    #         'providerDomainName': 8
    #     }
    #
    #     for each_entry in entity_permission_list:
    #         total = 0
    #         for row in each_entry:
    #             # print("row:", row[0], row[1])
    #             mask = ((entity_types[row[0]]-1)*len(self.permissions))+(self.permissions[row[1]])
    #             value = pow(2, mask-1)
    #             total = total+value
    #         print('operation and mask:', each_entry, total)
