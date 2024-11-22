# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for solr fileview related queries in Compliance Search

SolrFiletypeHelper:
    get_indexserver_info()            -- Returns the list of Index Servers and associated info

    get_fastserver_list()             -- Returns the list of fast servers (Ex. search engines)

    get_internal_cloud_name()         -- Return the internal cloud name of the provided index server

    get_cloud_id_and_base_url()       -- Returns cloud id and base url for provided index server

    get_collection_name()             -- Queries the CS DB and returns the collection name

    get_index_server_shards()         -- Queries CSDB and returns a list of shards associated to an Index Server

    create_solr_url()                 -- Creates the Solr base url with collection name

    create_query_and_get_response()   -- Creates the Solr query based on parameters provided and gets the response

    get_count_from_json()             -- Returns the numFound value in any json_string

    clear_filters()                   -- Clears the selected filters in Compliance Search UI

"""

import json
import requests

from Application.Exchange.SolrSearchHelper import SolrSearchHelper


class SolrFiletypeHelper:
    """
     This class contains methods for File System IndexServer Solr search
    """

    def __init__(self, tc_object):
        """
        Helper for IndexServer Solr search related files

        Args:
            tc_object   (object)    --  Testcase class object
        """

        self.commcell = tc_object.commcell
        self.csdb = tc_object.csdb
        self.log = tc_object.log
        self.mssql = tc_object.mssql
        self.index_server = tc_object.indexservercloud
        self.solr_search_obj = SolrSearchHelper(self)
        self.is_fs_server = False

    def get_indexserver_info(self):
        """
        Returns the list of index servers and associated info

        Returns:
            index servers and associated info as a list
        """

        _query = (f'SET NOCOUNT ON \n CREATE TABLE ISList \n '
                  f'(Cloudid INT, CloudName VARCHAR(150), CloudServerType INT, '
                  f'IndexServerClientId INT, InternalCloudName VARCHAR(150) ,\n '
                  f'BaseUrl VARCHAR(150), NodeClientId INT, NodeClientName VARCHAR(150), '
                  f'NodeHostName VARCHAR(150), NodeBasePort INT, \n IndexServerPoolClientId INT, '
                  f'RolesInfo VARCHAR(150), NodeStatus INT, CloudStatus INT, NodeManagledName VARCHAR(150))'
                  f' \n INSERT INTO ISList \n EXEC AppAnalyticsGetFlatNodeInfos 1 \n'
                  f'SELECT * FROM ISList \n WHERE CloudName = \'{self.index_server}\'\n DROP TABLE ISList')

        self.log.info(f'Obtaining information about provided index server')
        self.log.info(f'Query: {_query}')
        _response = self.mssql.execute(_query)

        if not _response:
            raise Exception("Unable to obtain Index Server info for provided Index Server")

        rows = _response.rows

        return rows

    def get_fastserver_list(self):
        """
        Returns the list of fast servers (Ex. search engines, mailbox index, etc.)

        Returns:
            fast servers and associated info as a list
        """
        query = 'SET NOCOUNT ON \n exec appgetfastserverlist 1'
        self.log.info(f'Obtaining fast server list')
        self.log.info(f'Query: {query}')
        _response = self.mssql.execute(query)

        if not _response:
            raise Exception("Unable to obtain Fast Server list")

        rows = _response.rows

        return rows

    def get_internal_cloud_name(self):
        """
        Returns the internal cloud name for given index server

        Returns:
            internal cloud name as a string
        """
        try:
            index_server_info = self.get_indexserver_info()
            return index_server_info[0][4]

        except Exception as exp:
            self.log.info("Unable to obtain internal cloud name for given Index Server")
            raise Exception(exp)

    def get_cloud_id_and_base_url(self):
        """
        Returns the cloud id for the provided index server

        Returns:
            cloudid (int)
            base_url (string)
        """
        try:
            cloud_id = None
            base_url = ""
            fs_list = self.get_fastserver_list()
            for row in fs_list:
                if self.index_server == row[7]:
                    cloud_id = row[3]
                    base_url = row[0]
                    self.is_fs_server = True
                    break

            if not self.is_fs_server:
                is_name = self.get_indexserver_info()
                cloud_id = is_name[0][0]
                base_url = is_name[0][5]

            self.log.info(
                f'Cloud id obtained for {self.index_server} is {cloud_id}')

            return cloud_id, base_url

        except Exception as exp:
            self.log.info("Unable to obtain cloud id for given Index Server")
            raise Exception(exp)

    def get_collection_name(self, cloudid, source_type=None, username=None, mssql=None):
        """
        Queries the CS DB and returns the collection name

        Args:
            cloudid     (int)           --   cloud id of index server to get collection name
            source_type  (string)       --   source type of data (default: fsindex),
                                             other source types cloud be sharepoint, exchange, etc.
            mssql (object)              --   MSSQL object
            username (string)           --   user that is logged in to Command Center

        Returns:
              collection name (string)
        """
        try:
            if source_type == 'fsindex':
                query = (f"select ActualCoreName from SECollectionInfo where corename not "
                         f"like '%meta%' and SchemaType like '%fsindex%' and CloudID={cloudid}")
            else:
                query = (f"select ActualCoreName from SECollectionInfo where corename "
                         f"not like '%meta%' and ("
                         f"SchemaType like '%usermbx%' or SchemaType like '%fsindex%'"
                         f") and CloudID={cloudid}")

            self.log.info("Querying CS DB to get indexserver collection names")
            self.log.info(f"query: {query}")
            self.csdb.execute(query)
            rows = self.csdb.fetch_all_rows()
            collectionnames = []
            invalid_list = set()
            valid_list = set()

            # Getting the list of Case Manager Clients since they have to be excluded
            _, cm_client_names = self.solr_search_obj.get_case_manager_clients()
            cm_definition_names = [f'{names}-definition' for names in cm_client_names]
            cm_dest_app_ids = set()
            for case in cm_definition_names:
                app_ids = self.solr_search_obj.get_app_id(
                    case, 'destination', username, mssql, skip_user_check=True)
                cm_dest_app_ids.update(app_ids)
            cm_dest_app_ids = filter(lambda x: (x != ""), cm_dest_app_ids)
            for dest_app_id in cm_dest_app_ids:
                invalid_list.update(self.solr_search_obj.get_ci_server_url(
                    mssql, f'({dest_app_id})', get_backupset_guid=True))

            # Checking if the collection is valid by cross checking
            # with backupset GUID in App_IndexDBInfo table
            for row in rows:
                collection_name = row[0]
                if 'fsindex' in collection_name or 'usermbx' in collection_name:
                    collectionnames.append(collection_name)
                    continue
                data = collection_name.split("_")
                backupset_guid = data[1]
                if backupset_guid in invalid_list:
                    continue
                elif backupset_guid in valid_list:
                    collectionnames.append(collection_name)
                    continue

                _query = (f"select count(*) from APP_IndexDBInfo "
                          f"where dbName = '{backupset_guid}'")

                self.csdb.execute(_query)
                count = self.csdb.fetch_one_row()[0]
                if int(count) != 0:
                    valid_list.add(backupset_guid)
                    collectionnames.append(collection_name)
                else:
                    invalid_list.add(backupset_guid)

            collections = [collection for collection in collectionnames if not collection.endswith('multinode')]
            self.log.info(f'collections: {collections}')
            return collections

        except Exception as exp:
            self.log.info(
                "Unable to obtain collection name for provided cloud id")
            raise Exception(exp)

    def create_solr_url(
            self,
            username,
            search_view,
            mssql,
            sourcetype=None):
        """
        Creates the Solr base url with collection name

        Args:
            username     (string)       --      login Username
            search_view  (string)       --      search view in Compliance search
            mssql        (object)       --      mssql object
            sourcetype   (string)       --      source type of data (default: fsindex)

        Returns:
            base url along with collection name

        """
        cloud_id, search_base_url = self.get_cloud_id_and_base_url()
        shards = ""

        if self.is_fs_server:
            base_url = search_base_url + "/solr/"
        else:
            if search_view == "File":
                collection_list = self.get_collection_name(cloud_id, 'fsindex', username, mssql)
            else:
                collection_list = self.get_collection_name(cloud_id, sourcetype, username, mssql)

            base_url = search_base_url + "/solr/" + collection_list[0]
            shards = "&shards="

            for collection in collection_list:
                shards = shards + search_base_url[7:] + "/solr/" + collection + ","
            shards = shards[:-1]

        cm_client_ids, _ = self.solr_search_obj.get_case_manager_clients()
        app_id_list = self.solr_search_obj.get_appid_compliancesearch(
            username, self.mssql)
        app_field_name = "ApplicationId" if not self.is_fs_server else "apid"

        fq_query = "fq=("

        non_case_manager_clients = [client_id for client_id in app_id_list
                                    if client_id not in cm_client_ids]

        for appid in non_case_manager_clients:
            fq_query = fq_query + app_field_name + ":" + str(appid) + " OR "

        fq_query = fq_query[:-4] + ")"

        url_query = base_url + "/select/?" + fq_query

        if (search_view == "Email, File" or search_view == "File") and not self.is_fs_server:
            url_query = url_query + shards

        self.log.info(f'Base url created is {url_query}')
        return url_query

    def create_query_and_get_response(
            self,
            solr_url,
            op_params=None
    ):
        """
        Creates the Solr query based on parameters provided and gets the response
        Args:
            solr_url    (string)           --   the base url with collection name
            op_params   (dictionary)       --   Other params and values for solr query
                                                    (Ex: start, rows)

        Returns:
            response (json) of created solr query
        """
        try:
            self.log.info("Creating solr URL")

            doctype_absent = True
            ex_query = ""
            search_query = '&q='
            if not op_params:
                op_params = {'wt': "json"}
            else:
                op_params['wt'] = "json"
            for key, value in op_params.items():
                if key == 'q':
                    search_query = search_query + str(value) + " AND "
                elif value is None:
                    ex_query += f'&{key}'
                else:
                    ex_query += f'&{key}={str(value)}'

                if isinstance(value, str) and "DocumentType" in value:
                    doctype_absent = False

            self.log.info("Optional parameters are: %s" % ex_query)

            if doctype_absent:
                ex_query = ex_query + f'&fq=(DocumentType:1) OR (DocumentType:2)'

            search_query = (f'{search_query}((((ItemState:0) OR (cistate:0)) OR ((ItemState:1) OR (cistate:1))'
                            f' OR ((ItemState:12) OR (cistate:12)) OR ((ItemState:13) OR (cistate:13))'
                            f' OR ((ItemState:14) OR (cistate:14)) OR ((ItemState:15) OR (cistate:15))'
                            f' OR ((ItemState:1014) OR (cistate:1014))))')

            final_url = f'{solr_url}{search_query}{ex_query}'
            self.log.info("Final url is: %s" % final_url)

            return requests.get(url=final_url)

        except Exception as excp:
            self.log.exception(
                "Exception while creating solr query: %s" %
                str(excp))
            raise excp

    def get_count_from_json(self, json_string):
        """Method to return the numFound in any json_string
            Args:
                json_string(string)  -- String representation of output solr json

            Returns:
                count of numFound
        """
        try:
            results = json.loads(json_string)
            return results['response']['numFound']
        except Exception as excp:
            self.log.exception(
                "Exception in method 'get_count_from_json' while parsing json to "
                "get result count")
            raise excp

    def clear_filters(self, custom_filter):
        """
        Method to clear all selected filters in Compliance Search
        Args:
            custom_filter(obj) -- object of class CustomFilter
        """
        try:
            while custom_filter.clear_custodian_filter():
                continue
        except Exception as excp:
            self.log.exception(
                "Exception while clearing filters: %s" %
                str(excp))
            raise excp
