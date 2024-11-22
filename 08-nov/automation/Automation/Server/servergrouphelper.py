# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing Server group related operations on Commcell

ServerGroupHelper:

    __init__()                              --  initializing the server group helper class

    get_all_server_groups()                 --  method to get all server groups from DB

    get_server_groups_for_company()         --  method to get all server groups from DB for a company

    cleanup_server_groups()                 --  Delete server groups that has provided marker / string

    _get_group_assoc_type()                 --  calculates group assoc type

    validate_server_groups_cache_data()     --  validates the data returned from Mongo cache for server group collection

    validate_sort_on_cached_data()          --  validates sort parameter on entity cache API call

    validate_limit_on_cache()               --  validates limit parameter on entity cache API call

    validate_search_on_cache()              --  validates search parameter on entity cache API call

    validate_filter_on_cache()              --  validates fq param on entity cache API call

"""
from cvpysdk.commcell import Commcell
from AutomationUtils import database_helper
from AutomationUtils import logger
import random
import locale


class ServerGroupHelper(object):
    """Helper class to perform Server group related operations"""

    def __init__(self, commcell: Commcell, server_group_name: str = None) -> None:
        """Method to initialize server group helper object"""

        self.commcell_obj = commcell
        self.server_group_name = server_group_name
        self.log = logger.get_log()
        self._csdb = database_helper.CommServDatabase(commcell)
        self.server_group_obj = self.commcell_obj.client_groups
   
    def get_all_server_groups(self) -> list:
        """Method to get all the server group from DB"""
        query = "select name from APP_ClientGroup where flag <> 1073745920 and name <> 'Index Servers'"
        self._csdb.execute(query)
        temp_servergroup_list_db = self._csdb.fetch_all_rows()
        servergroup_list_db = []
        for item in temp_servergroup_list_db:
            if item[0]:
                servergroup_list_db.append(item[0])
    
        return sorted(servergroup_list_db, key=str.casefold)

    def get_server_groups_for_company(self, company_name: str) -> list:
        """Method to get all the server group from DB for a company"""
        company_id = self.commcell_obj.organizations.get(company_name).organization_id
        query = f"select name from APP_ClientGroup where flag <> 1073745920 and name <> 'Index Servers' and id in (select entityId from App_CompanyEntities where companyId = {company_id} and entityType=28)"
        self._csdb.execute(query)
        temp_servergroup_list_db = self._csdb.fetch_all_rows()
        servergroup_list_db = []
        for item in temp_servergroup_list_db:
            if item[0]:
                servergroup_list_db.append(item[0])
    
        return sorted(servergroup_list_db, key=str.casefold)

    def cleanup_server_groups(self, marker: str):
        """
            Delete server groups that has provided marker / string

            Args:
                marker      (str)   --  marker tagged to server groups for deletion
        """
        self.server_group_obj.refresh()
        for server_group in self.server_group_obj.all_clientgroups:
            if server_group.startswith(marker.lower()):
                try:
                    self.server_group_obj.delete(server_group)
                    self.log.info("Deleted server group - {0}".format(server_group))
                except Exception as exp:
                    self.log.error(
                        "Unable to delete server group {0} due to {1}".format(
                            server_group,
                            str(exp)
                        )
                    )

    def _get_group_assoc_type(self, group_id: str) -> int:
        """
        Method to calculate group assoc type
            Args:
                group_id   (str)   -- client group id
        """
        self._csdb.execute(f'select flag from APP_ClientGroup where id = {group_id}')
        flags = int(self._csdb.rows[0][0])
        if flags & 0x1000 != 0:
            return 1
        elif flags & 0x4000000 != 0:
            return 2
        else:
            return 3

    def validate_server_groups_cache_data(self) -> bool:
        """
        Validates the data returned from Mongo cache for server group collection.

        Returns:
            bool: True if validation passes, False otherwise
        """
        cache = self.server_group_obj.get_client_groups_cache(enum=False)
        out_of_sync = []

        for group, cache_data in cache.items():
            if group == 'Automatic TPPM Clients':
                continue
            self.log.info(f'Validating cache for server group: {group}')
            group_prop = self.server_group_obj.get(group)
            validations = {
                'id': int(group_prop.clientgroup_id),
                'association': self._get_group_assoc_type(group_prop.clientgroup_id),
            }

            for key, expected_value in validations.items():
                self.log.info(f'Comparing key: {key} for server group: {group}')
                if cache_data.get(key) != expected_value:
                    out_of_sync.append((group, key))
                    self.log.error(f'Cache not in sync for prop "{key}". Cache value: {cache_data.get(key)}; '
                                   f'csdb value: {expected_value}')

            if cache_data.get('company') == 'Commcell':
                company_in_cache = cache_data.get('company').lower()
            else:
                company_in_cache = self.commcell_obj.organizations.get(cache_data.get('company')).domain_name.lower()

            self.log.info(f'Comparing key: company for Server group: {group}')
            if company_in_cache !=group_prop.company_name.lower():
                out_of_sync.append((group, 'company'))
                self.log.error(f'Cache not in sync for prop "company". Cache value: {cache_data.get("company")} '
                               f'; csdb value: {group_prop.company_name.user_company_name}')

        if out_of_sync:
            raise Exception(f'Validation Failed. Cache out of sync: {out_of_sync}')
        else:
            self.log.info('Validation successful. All the server group cache are in sync')
            return True

    def validate_sort_on_cached_data(self) ->bool:
        """
        Method to validate sort parameter on entity cache API call

        Returns:
            bool: True if validation passes, False otherwise
        """
        # setting locale for validating sort
        locale.setlocale(locale.LC_COLLATE, 'English_United States')

        columns = ['name', 'id', 'association', 'company', 'tags']
        unsorted_col = []
        for col in columns:
            optype = random.choice([1, -1])
            # get sorted cache from Mongo
            cache_res = self.server_group_obj.get_client_groups_cache(fl=[col], sort=[col, optype])
            # sort the sorted list
            if col == 'name':
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

        cache = self.server_group_obj.get_client_groups_cache()

        # generate random limit
        test_limit = random.randint(1, len(cache.keys()))
        limited_cache = self.server_group_obj.get_client_groups_cache(limit=['0', str(test_limit)])
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
        group = self.server_group_obj.add(f"caching_automation_{random.randint(0, 100000)} - server_group")

        if group:
            # calling the API with search param
            response = self.server_group_obj.get_client_groups_cache(search=group.name)
            # checking if test group is present in response
            if len(response.keys()) == 1 and [True for key in response.keys() if key == group.name]:
                self.log.info('Validation for search on cache passed')
                return True
            else:
                self.log.error(f'{group.name} is not returned in the response')
                raise Exception("Validation for search on cache failed!")
        else:
            raise Exception('Failed to create server group. Unable to proceed.')

    def validate_filter_on_cache(self, filters: list, expected_response: list) -> bool:
        """
        Method to validate fq param on entity cache API call

        Args:
            filters (list) -- contains the columnName, condition, and value
                e.g. filters = [['name','contains', 'test'],['association','eq', 'Manual']]
            expected_response (list) -- expected list of server groups to be returned in response

        Returns:
            bool: True if validation passes, False otherwise
        """
        if not filters or not expected_response:
            raise ValueError('Required parameters not received')

        try:
            res = self.server_group_obj.get_client_groups_cache(fq=filters)
        except Exception as exp:
            self.log.error("Error fetching server groups cache")
            raise Exception(exp)

        missing_groups = [group for group in expected_response if group not in res.keys()]

        if missing_groups:
            raise Exception(f'Validation failed. Missing server groups: {missing_groups}')
        self.log.info("validation for filter on cache passed!")
        return True
