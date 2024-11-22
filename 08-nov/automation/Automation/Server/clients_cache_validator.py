# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Main file for performing clients cache validation.

ClientsCacheValidator: Class for validations on SERVER cache operations

ClientsCacheValidator:

    __init__()                      --      Initialize instance of the ClientsCacheValidator class

    _get_idalist_for_server()       --      gets ida List for a server from CSDB

    _get_sp_version_info()          --      gets SP version info for a client id from CSDB

    validate_clients_cache_data()   --      validates the data returned from Mongo cache for clients collection

    validate_sort_on_cached_data()  --      validates sort parameter on entity cache API call

    validate_limit_on_cache()       --      validates limit parameter on entity cache API call

    validate_search_on_cache()      --      validates search parameter on entity cache API call

    validate_filter_on_cache()      --      validates fq param on entity cache API call

"""

from cvpysdk.commcell import Commcell
from AutomationUtils import logger, database_helper
import random
import locale


class ClientsCacheValidator(object):
    """Validator class to perform cache validations on SERVER cache """

    def __init__(self, commcell: Commcell, client: str = None) -> None:
        """Method to initialize clients cache validator object"""
        self._commcell_obj = commcell
        self._clients_obj = commcell.clients
        self._client = None
        if client is not None:
            self._client_name = client
            self._client = self._clients_obj.get(client)
        self.log = logger.get_log()
        self._csdb = database_helper.CommServDatabase(commcell)

    def _get_idalist_for_server(self, client_id: str) -> list:
        """
        Method to get ida List for a server from CSDB
        """
        self._csdb.execute('SELECT AIT.name FROM app_client '
                           'CL INNER JOIN dbo.APP_IDAName AIN ON AIN.clientId=CL.id '
                           f'INNER JOIN dbo.APP_iDAType AIT ON AIT.type=AIN.appTypeId  where CL.id = {client_id}')
        return sum(self._csdb.rows, [])

    def _get_sp_version_info(self, client_id: str) -> str:
        """
        Method to get SP version info for a client id from CSDB
        """
        self._csdb.execute("select attrVal from app_clientProp where attrName like '%SP Version Info%' "
                           f"and componentNameId = {client_id}")
        sp_info = self._csdb.rows[0][0].replace(' SP', '.')
        return sp_info

    def validate_clients_cache_data(self) -> bool:
        """
        Validates the data returned from Mongo cache for clients collection.

        Returns:
            bool: True if validation passes, False otherwise
        """
        self.log.info("Starting validation for clients cache...")
        cache = self._clients_obj.get_clients_cache(enum=False)
        out_of_sync = []

        for client, cache_data in cache.items():
            self.log.info(f'Validating cache for client: {client}')
            client_obj = self._clients_obj.get(client)

            validations = {
                'clientId': int(client_obj.client_id),
                'hostName': client_obj.client_hostname,
                'displayName': client_obj.display_name,
                'clientGUID': client_obj.client_guid,
                'companyName': client_obj.company_name,
                'agents': self._get_idalist_for_server(str(client_obj.client_id)) if 'agents' in cache_data else None,
                'isDeletedClient': client_obj.is_deleted_client if 'isDeletedClient' in cache_data else None,
                'version': self._get_sp_version_info(str(client_obj.client_id)) if 'version' in cache_data else None,
                'updateStatus': client_obj.update_status,
                'OSName': client_obj.os_info.split('  --  ')[1],
                'isInfrastructure': client_obj.is_infrastructure,
                'networkStatus': client_obj.network_status
            }

            for key, expected_value in validations.items():
                self.log.info(f'Comparing key: {key} for client: {client}')
                if expected_value is not None and cache_data.get(key) != expected_value:
                    out_of_sync.append((client, key))
                    self.log.error(f'Cache not in sync for prop "{key}". Cache value: {cache_data.get(key)}; '
                                   f'csdb value: {expected_value}')

        if out_of_sync:
            raise Exception(f'Validation Failed. Cache out of sync: {out_of_sync}')
        else:
            self.log.info('Validation successful. All the clients cache are in sync')
            return True

    def validate_sort_on_cached_data(self) -> bool:
        """
        Method to validate sort parameter on entity cache API call

        Returns:
            bool: True if validation passes, False otherwise
        """
        # setting locale for validating sort
        locale.setlocale(locale.LC_COLLATE, 'English_United States')

        self.log.info("starting Validation for sorting on clients cache...")
        columns = ['clientName', 'hostName', 'displayName', 'clientGUID', 'companyName', 'isDeletedClient', 'version',
                   'OSName', 'isInfrastructure', 'networkStatus', 'tags', 'updateStatus']
        # to do: clientRoles and idaList columns validation
        unsorted_col = []
        for col in columns:
            optype = random.choice([1, -1])
            # get sorted cache from Mongo
            cache_res = self._clients_obj.get_clients_cache(fl=[col], sort=[col, optype])
            # sort the sorted list
            if col == 'clientName':
                cache_res = list(cache_res.keys())
                res = sorted(cache_res, key=lambda x: locale.strxfrm(str(x)), reverse=optype == -1)
            else:
                cache_res = [[key, value.get(col)] for key, value in cache_res.items() if col in value]
                if all(isinstance(item[1], int) for item in cache_res) or col == 'version':
                    res = sorted(cache_res, key=lambda x: x[1], reverse=optype == -1)
                else:
                    res = sorted(cache_res, key=lambda x: locale.strxfrm(str(x[1])), reverse=optype == -1)

            # check if sorted list got modified
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
        self.log.info("starting Validation for limit on clients cache...")

        cache = self._clients_obj.get_clients_cache()

        # generate random limit
        test_limit = random.randint(1, len(cache.keys()))
        limited_cache = self._clients_obj.get_clients_cache(limit=['0', str(test_limit)])
        # check the count of entities returned in cache
        if len(limited_cache) == test_limit:
            self.log.info('Validation for limit on cache passed!')
            return True
        else:
            self.log.error(f'limit returned in cache : {len(limited_cache)}; expected limit : {test_limit}')
            raise Exception(f"validation for limit on cache Failed!")

    def select_random_server(self) -> str:
        """
        Helper class to return random server name

        Returns:
            Randomly selected server.
        """
        servers = self._clients_obj.get_clients_cache().keys()
        server = random.choice(list(servers))
        self.log.info(f"Random server selected :{server}")
        return server

    def validate_search_on_cache(self) -> bool:
        """
        Method to validate search parameter on entity cache API call

        Returns:
            bool: True if validation passes, False otherwise
        """
        self.log.info("starting Validation for search on clients cache...")
        client = self.select_random_server()
        response = self._clients_obj.get_clients_cache(search=client)
        # checking if client is present in response
        if [True for key in response.keys() if key.upper() == client.upper()]:
            self.log.info('Validation for search on cache passed')
            return True
        else:
            self.log.error(f'{client} is not returned in the response')
            raise Exception("Validation for search on cache failed!")

    def validate_filters_on_cache(self, filters: list, expected_response: list) -> bool:
        """
        Method to validate fq param on entity cache API call

        Args:
            filters (list) -- contains the columnName, condition, and value
                e.g. fq = [['displayName','contains', 'test'],['clientRoles','contains', 'Command Center']]
            expected_response (list) -- expected list of clients to be returned in response

        Returns:
            bool: True if validation passes, False otherwise
        """
        self.log.info("starting Validation for filter on clients cache...")
        if not filters or not expected_response:
            raise ValueError('Required parameters not received')

        try:
            res = self._clients_obj.get_clients_cache(fq=filters)
        except Exception as exp:
            self.log.error("Error fetching clients cache")
            raise Exception(exp)

        missing_clients = [client for client in expected_response if client not in res.keys()]

        if missing_clients:
            raise Exception(f'Validation failed. Missing clients: {missing_clients}')
        self.log.info("validation for filter on cache passed!")
        return True
