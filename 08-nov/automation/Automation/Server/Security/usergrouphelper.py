# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing User Group related operations on Commcell

UsergroupHelper:
    __init__()                      --  Initialize Usergroup Helper object

    delete_usergroup()              --  Deletes the usergroup passed

    create_usergroup()              --  Adds local/external user group on this commcell based
                                        domain parameter provided

    modify_security_associations()  --  Validates security Associations on user and usergroup

    cleanup_user_groups()           --  Delete user groups that has provided marker / string

    validate_user_groups_cache_data()   --  validates the data returned from Mongo cache for user groups collection

    validate_sort_on_cached_data()      --  validates sort parameter on entity cache API call

    validate_limit_on_cache()           --  validates limit parameter on entity cache API call

    validate_search_on_cache()          --  validates search parameter on entity cache API call

    validate_filter_on_cache()          --  validates fq param on entity cache API call
"""

import os
from AutomationUtils import database_helper
from AutomationUtils import logger, options_selector
import random
import locale


class UsergroupHelper(object):
    """Helper class to perform User related operations"""

    def __init__(self, commcell, usergroup=None):
        """Initializes Usergroup Helper object

        Args:
            commcell    (obj)   --  Commcell object

            usergroup   (obj)   --  usergroup object
        """
        if usergroup:
            self._usergroup = usergroup
        self.log = logger.get_log()
        self.commcell_obj = commcell
        self._csdb = database_helper.CommServDatabase(commcell)
        self._utility = options_selector.OptionsSelector(self.commcell_obj)
        self.cl_obj = self.commcell_obj.commserv_client
        self.user_groups_obj = self.commcell_obj.user_groups

    def delete_usergroup(self, group_name, new_user=None, new_group=None):
        """Deletes the usergroup passed
        Args:
            group_name       (str)   -- object of usergroup to be deleted

            new_user        (str)   -- user to whom ownership of entities will be transferred

            new_group       (str)   -- user group to whom ownership will be transferred

        """
        self.log.info("performing Delete Operation on user group: %s", group_name)

        user = self.commcell_obj.user_groups.has_user_group(user_group_name=group_name)
        if user:
            self.commcell_obj.user_groups.delete(user_group=group_name, new_user=new_user,
                                                 new_usergroup=new_group)
            self.log.info("usergroup deletion is Successful")
        else:
            self.log.info("Specified usergroup is not present on the CommCell %s", group_name)

    def create_usergroup(self, group_name, domain=None, users=None, entity_dict=None,
                         external_groups=None, local_groups=None):
        """Adds local/external user group on this commcell based domain parameter provided

            Args:
                group_name          (str)   --  name of the user group

                domain              (str)   --  name of the domain to which user group
                                                belongs to

                users               (list)  --  list which contains users who will be
                                                members of this group

                entity_dict         (dict)  --  combination of entity_type, entity
                                                names and role
                e.g.: entity_dict={
                                'assoc1':
                                    {
                                        'entity_type':['entity_name'],
                                        'entity_type':['entity_name', 'entity_name'],
                                        'role': ['role1']
                                    },
                                'assoc2':
                                    {
                                        'mediaAgentName': ['networktestcs', 'standbycs'],
                                        'clientName': ['Linux1'],
                                        'role': ['New1']
                                        }
                                    }
                entity_type         --      key for the entity present in dictionary
                                            on which user will have access
                entity_name         --      Value of the key
                role                --      key for role name you specify
                e.g:   e.g.: {"clientName":"Linux1"}
                Entity Types are:   clientName, mediaAgentName, libraryName, userName,
                                    userGroupName, storagePolicyName, clientGroupName,
                                    schedulePolicyName, locationName, providerDomainName,
                                    alertName, workflowName, policyName, roleName

                entity_name = "Linux1", "ClientMachine1"

                external_groups     (list)  --  list of domain user group which could
                                                be added as members to this group

                local_groups        (list)  --  list of commcell usergroup which could
                                                be added as members to this group
        """
        args = [group_name, domain, users, entity_dict, external_groups, local_groups]
        self.log.info("Creating usergroup with name = {0}, domain = {1}, users_list = {2}, entity_dict = {3},"
                      "external_group = {4}, local_usergroups = {5}".format(*args))
        user_group_object = self.commcell_obj.user_groups.add(*args)
        self.log.info("UserGroup {0} creation is Successful!!".format(group_name))
        return user_group_object

    def modify_security_associations(self, entity_dict, group_name, request='UPDATE'):
        """Validates security Associations on user and userggroup
        Args:
            entity_dict         (Dict)  :   entity-role association dict

            group_name          (Str)   :   Name of the usergroup

            request             (Str)   :   decides whether to UPDATE, DELETE or
                                            OVERWRITE user security association

        Raises:
                Exception:
                    if request type is not valid

        """

        if request not in ['UPDATE', 'ADD', 'OVERWRITE', 'DELETE']:
            raise Exception("Invalid Request type is sent to the  function!!")
        else:
            self._usergroup = self.commcell_obj.user_groups.get(user_group_name=group_name)
            self._usergroup.update_security_associations(entity_dictionary=entity_dict,
                                                         request_type=request)
            self.log.info("""Sucessfully modified security association for entity [{0}], group [{1}], request: [{2}]"""
                          .format(entity_dict, group_name, request))

    def get_usergroup_clients(self):
        """Returns the list of clients for the user group
        """
        clients = []
        usergroup_id = self._usergroup.user_group_id
        # Now we read in the stored procedure query for getting clients of a user group
        # usergroup_stored_proc.txt must be present in SmartClientGroups Folder
        script_dir = os.path.dirname(__file__)
        rel_path = '../SmartClientGroups/usergroup_stored_proc.txt'
        abs_file_path = os.path.join(script_dir, rel_path)
        filename = os.path.abspath(os.path.realpath(abs_file_path))
        file = open(filename, 'r')
        stored_proc = file.read()
        # Execute create stored_procedure query
        try:
            self._utility.update_commserve_db(stored_proc)
        except Exception as excp:
            self.log.info(excp)
        file.close()
        # Execute query to get usergroup clients
        query = f"""CREATE TABLE #getIdaObjects 
                    (clientId INT, apptypeId INT, instanceID INT, backupsetId INT, subclientID INT,primary key(clientId,appTypeId,instanceId,backupsetId,subclientId))
                    EXEC sec_getIdaObjectsForUser {usergroup_id}, 3, 0,0, '#getIdaObjects', 0, '2'
                    select name from app_client where id in (select clientId from #getIdaObjects);"""
        db_response = self._utility.update_commserve_db(query)
        drop_stored_proc = """DROP PROCEDURE sec_getIdaObjectsForUserGroup;"""
        # Execute drop stored procedure query
        try:
            self._utility.update_commserve_db(drop_stored_proc)
        except Exception as drop_proc_excp:
            self.log.info(drop_proc_excp)
        for client in db_response.rows:
            clients.append(client['name'])

        return clients

    def get_all_usergroup(self, company_name = None, local_groups= False, external_groups= False):
        """Method to get all the user groups from the DB

        Returns:
            List: a list of all the usergroups present in DB that are visible in UI
        """
        query = f"select domainName, id from UMDSProviders"
        self._csdb.execute(query)
        temp_company_id_list = self._csdb.fetch_all_rows(True)
        company_id_map = {}
        for records in temp_company_id_list:
            company_id_map[records["id"]] = records["domainName"]
        
        if company_name: # if company is specified, filter usergroups which are mapped with company indentity servers 
            if company_name.lower() != 'commcell':
                company_domain = self.commcell_obj.organizations.get(company_name).domain_name
            else:
                company_domain = 'Commcell'
            company_id = list(company_id_map.keys())[list(company_id_map.values()).index(company_domain)]
            self._csdb.execute(f"select id from UMDSProviders where serviceType not in (0,1,5,11) and ownerCompany = {company_id}")
            # getting indentity servers of particular company to get usergroups out of it
            company_indentity_servers = '(' + ','.join([i[0] for i in self._csdb.fetch_all_rows() if i[0] != '']) + ')'
            
        query = "select * from UMGroups where groupFlags&0x0010=0 and name not like 'CV_Restricted_Visibility'"
        
        if local_groups: 
            query += " and umdsProviderId not in (select id from UMDSProviders where serviceType in (2,8,9,10,12,14))"
            if company_name: # if local group of a particular company is needed
                query += f" and umdsProviderId = {company_id}"
        elif external_groups:
            query = "select * from umgroups where umdsProviderId in (select id from UMDSProviders where serviceType in (2,8,9,10,12,14))"
            if company_name: # if external group of a particular company is needed
                query += (f" and umdsProviderId in {company_indentity_servers}" if company_indentity_servers != '()' else "")
        elif company_name:
            query += f" and umdsProviderId = {company_id}" + (f" or umdsProviderId in {company_indentity_servers}" if company_indentity_servers != '()' else "")
        
        self.log.info(f'Executing query: {query}')
        self._csdb.execute(query)
        temp_userg_list_db = self._csdb.fetch_all_rows(True)
        temp_user_group_details = []
        for records in temp_userg_list_db:
            if isinstance(records, dict):
                temp_user_group_details.append({records["name"]: company_id_map[records["umdsProviderId"]]})

        user_group_list = []
        for item in temp_user_group_details:
            key = list(item.keys())[0]
            user_group = key
            value = item[user_group]
            if value and value != "Commcell":
                user_group = str(value) + '\\' + str(key)

            user_group_list.append(user_group)

        return sorted(user_group_list, key=str.casefold)

    def cleanup_user_groups(self, marker):
        """
            Delete user groups that has provided marker / string

            Args:
                marker      (str)   --  marker tagged to user groups for deletion
        """
        self.user_groups_obj.refresh()
        for user_group in self.user_groups_obj.all_user_groups:
            if marker.lower() in user_group:
                try:
                    self.user_groups_obj.delete(user_group, new_usergroup="master")
                    self.log.info("Deleted user group - {0}".format(user_group))
                except Exception as exp:
                    self.log.error(
                        "Unable to delete user group {0} due to {1}".format(
                            user_group,
                            str(exp)
                        )
                    )

    def validate_user_groups_cache_data(self) -> bool:
        """
        Validates the data returned from Mongo cache for user groups collection.

        Returns:
            bool: True if validation passes, False otherwise
        """
        cache = self.user_groups_obj.get_user_groups_cache(enum=False)
        out_of_sync = []

        for group, cache_data in cache.items():
            self.log.info(f'Validating cache for user group: {group}')
            user_group_prop = self.user_groups_obj.get(group)
            validations = {
                'groupId': int(user_group_prop.user_group_id),
                'description': user_group_prop.description,
                'status': user_group_prop.status,
            }

            for key, expected_value in validations.items():
                self.log.info(f'Comparing key: {key} for user group: {group}')
                if cache_data.get(key) != expected_value:
                    out_of_sync.append((group, key))
                    self.log.error(f'Cache not in sync for prop "{key}". Cache value: {cache_data.get(key)}; '
                                   f'csdb value: {expected_value}')

            if cache_data.get('company') == 'Commcell':
                company_in_cache = cache_data.get('company').lower()
            else:
                company_in_cache = self.commcell_obj.organizations.get(cache_data.get('company')).domain_name.lower()

            self.log.info(f'Comparing key: company for user group: {group}')
            if company_in_cache != user_group_prop.company_name.lower():
                out_of_sync.append((group, 'company'))
                self.log.error(f'Cache not in sync for prop "company". Cache value: {cache_data.get("company")} '
                               f'; csdb value: {user_group_prop.user_company_name}')

        if out_of_sync:
            raise Exception(f'Validation Failed. Cache out of sync: {out_of_sync}')
        else:
            self.log.info('Validation successful. All the user groups cache are in sync')
            return True

    def validate_sort_on_cached_data(self) -> bool:
        """
        Method to validate sort parameter on entity cache API call

        Returns:
            bool: True if validation passes, False otherwise
        """
        # setting locale for validating sort
        locale.setlocale(locale.LC_COLLATE, 'English_United States')

        columns = ['groupName', 'groupId', 'description', 'status', 'company']
        unsorted_col = []
        for col in columns:
            optype = random.choice([1, -1])
            # get sorted cache from Mongo
            cache_res = self.user_groups_obj.get_user_groups_cache(fl=[col], sort=[col, optype])
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
        cache = self.user_groups_obj.get_user_groups_cache()

        # generate random limit
        test_limit = random.randint(1, len(cache.keys()))
        limited_cache = self.user_groups_obj.get_user_groups_cache(limit=['0', str(test_limit)])
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
        # creating a test group
        group_name = f"caching_automation_{random.randint(0, 100000)} - user_group"
        group = self.create_usergroup(group_name=group_name)

        if group:
            # calling the API with search param
            response = self.user_groups_obj.get_user_groups_cache(search=group.name)
            # checking if test group is present in response
            if len(response.keys()) == 1 and [True for key in response.keys() if key == group.name]:
                self.log.info('Validation for search on cache passed')
                return True
            else:
                self.log.error(f'{group.name} is not returned in the response')
                raise Exception("Validation for search on cache failed!")
        else:
            raise Exception('Failed to create user group. Unable to proceed.')

    def validate_filter_on_cache(self, filters: list, expected_response: list) -> bool:
        """
        Method to validate fq param on entity cache API call

        Args:
            filters (list) -- contains the columnName, condition, and value
                e.g. filters = [['groupName','contains', test']['status','eq','Enabled']]
            expected_response (list) -- expected list of user groups to be returned in response

        Returns:
            bool: True if validation passes, False otherwise
        """
        if not filters or not expected_response:
            raise ValueError('Required parameters not received')

        try:
            res = self.user_groups_obj.get_user_groups_cache(fq=filters)
        except Exception as exp:
            self.log.error("Error fetching user groups cache")
            raise Exception(exp)

        missing_groups = [group for group in expected_response if group not in res.keys()]

        if missing_groups:
            raise Exception(f'Validation failed. Missing user groups : {missing_groups}')
        self.log.info("validation for filter on cache passed!")
        return True
