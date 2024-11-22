# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for solr related queries """
from datetime import date, timedelta, datetime
import re
import xml.etree.ElementTree as ET
import xmltodict
import requests
from dateutil.parser import parse
from cvpysdk.exception import SDKException
from dynamicindex.Datacube.dcube_solr_helper import SolrHelper


class SolrSearchHelper():
    """
     This class contains all the methods for IndexServer Solr search
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

    def _is_date(self, string, fuzzy=False):
        """
        Return whether the string can be interpreted as a date.

        Args: string: str, string to check for date
        Args: fuzzy: bool, ignore unknown tokens in string if True
        """
        try:
            parse(string, fuzzy=fuzzy)
            return True
        except ValueError:
            return False

    def get_date_range(self, dates_list):
        """
        Compute date range and return the range to fire Indexserver query
        Args: dates_list: list of date ranges to be converted
        Returns: daterange (str)
        """
        received_time_list = []
        for date_range in dates_list:
            if date_range == "Past month":
                today = date.today()
                lastmonth_date = today - timedelta(29)
                received_time = "[" + str(lastmonth_date) + \
                    "T00:00:00Z TO " + str(today) + "T23:59:59Z]"

            elif date_range == "Past year":
                today = date.today()
                lastyear_date = today - timedelta(364)
                received_time = "[" + str(lastyear_date) + \
                    "T00:00:00Z TO " + str(today) + "T23:59:59Z]"

            elif self._is_date(date_range):
                given_date = date_range
                date_time_obj = datetime.strptime(given_date, '%d/%m/%Y')
                given_last_date = date_time_obj - timedelta(1)
                time_now = datetime.now().time().replace(second=0, microsecond=0)
                yesterday = (datetime.now() - timedelta(1)).date()
                received_time = "[" + str(given_last_date.date()) + "T" + str(
                    time_now) + "Z TO " + str(yesterday) + "T23:59:59Z]"

            elif date_range == "More than a year":
                today = date.today()
                lastyear_date = today - timedelta(365)
                received_time = "[1970-01-01T00:00:00Z TO " + \
                    str(lastyear_date) + "T23:59:59Z]"
            else:
                received_time = ""

            received_time_list.append(received_time)

        return received_time_list

    def get_size_range(self, sizes_list):
        """
        Compute date range and return the range to fire Indexserver query
        Args: sizes_list: list of size ranges to be converted
        Returns: sizerange (str)
        """
        size_range_list = []
        for size_range in sizes_list:
            if size_range == "Below 1 MB":
                one_mb = 1024 * 1024
                size = "[0 TO " + str(one_mb) + "]"

            elif size_range == "1 - 5 MB":
                one_mb = 1024 * 1024
                five_mb = 5 * one_mb
                size = "[" + str(one_mb) + " TO " + str(five_mb) + "]"

            elif size_range == "5 - 10 MB":
                one_mb = 1024 * 1024
                five_mb = 5 * one_mb
                ten_mb = 10 * one_mb
                size = "[" + str(five_mb) + " TO " + str(ten_mb) + "]"

            elif "SizeKB" in size_range:
                values = re.findall(r'\d+', size_range)

                min_size_kb = int(values[0]) * 1024
                max_size_kb = int(values[1]) * 1024
                size = "[" + str(min_size_kb) + " TO " + str(max_size_kb) + "]"

            else:
                size = ""

            size_range_list.append(size)

        return size_range_list

    def construct_payload(
            self,
            search_keyword,
            indexservercloud,
            username,
            interfilter_op,
            filters,
            ci_server_info,
            search_view):
        """constructs the payload for doWebSearch API request

        Args:
            search_keyword             -- Search Keyword to be fired
            indexservercloud(str)      --  Indexserver cloud name
            username (str)             --  Login username
            interfilter_op (str)       -- Interfilter operator to be applied
            filters (list)             -- List of filters with format interoperator;values
                                          EX: Email_From : OR;email_add1;email_add2
                                          EX: Subject : AND;test_subj1;test_subj2
                                          Interoperator = None in case of single value
                                          EX: Folder: NONE;Inbox
            ci_server_info (str)        --  json encoded content with CIServer list
            search_view (str)           -- Search View to be applied (Email, File, etc.)

        Returns

            str - payload
        """

        interfilter_operators = {
            "OR": 0,
            "AND": 2,
            "NOT": 4,
            "NONE": 1,
            "RANGE": 1}
        inter_op = interfilter_operators[interfilter_op]

        user_guid_query = "select userGuid from UMUsers where login='%s'" % (
            username)
        self.csdb.execute(user_guid_query)
        _user_guid_results = self.csdb.fetch_one_row()
        user_guid = _user_guid_results[0]

        CIServerInfo = None
        ci_server_list = ''

        if search_view != "Email, File":
            cloud_id = self.get_cloudid(indexservercloud)
            for dict_info in ci_server_info:
                if dict_info['cloudID'] == int(cloud_id):
                    CIServerInfo = dict_info
                    break
            ci_server_list = fr"""<listOfCIServer cloudID="{CIServerInfo['cloudID']}"
                cIServerURL="{CIServerInfo['cIServerURL']}"
                clientId="{CIServerInfo['clientId']}" clientName="{CIServerInfo['clientName']}"
                basePort="{CIServerInfo['basePort']}" hostName="{CIServerInfo['hostName']}"
                version="{CIServerInfo['version']}" type="{CIServerInfo['type']}"
                engineName="{CIServerInfo['engineName']}" serverType="{CIServerInfo['serverType']}"
                indexServerClientId="{CIServerInfo['indexServerClientId']}"/>"""
        else:
            cloud_id_file = self.get_cloudid(indexservercloud)
            cloud_id_email = self.get_cloudid("Mailbox Index")
            for dict_info in ci_server_info:
                if dict_info['cloudID'] == int(cloud_id_file) or dict_info['cloudID'] == int(cloud_id_email):
                    ci_server_list = ci_server_list + fr"""<listOfCIServer cloudID="{dict_info['cloudID']}"
                                    cIServerURL="{dict_info['cIServerURL']}"
                                    clientId="{dict_info['clientId']}" clientName="{dict_info['clientName']}"
                                    basePort="{dict_info['basePort']}" hostName="{dict_info['hostName']}"
                                    version="{dict_info['version']}" type="{dict_info['type']}"
                                    engineName="{dict_info['engineName']}" serverType="{dict_info['serverType']}"
                                    indexServerClientId="{dict_info['indexServerClientId']}"/>"""

        if search_view == "Email":
            inter_filters = fr"""<emailFilter interGroupOP="{inter_op}">
                            <filter interFilterOP="{inter_op}">
                            </filter>
                        </emailFilter>"""

            is_user_mb = filters["usermailbox"]
            is_journal_mb = filters["journalmailbox"]
            is_smtp_mb = filters["smtpmailbox"]
            email_filter = fr"""<emailView usermailbox="{is_user_mb}" journalmailbox="{is_journal_mb}"
                       smtpmailbox="{is_smtp_mb}"/>"""
            galaxy_app_type = 3
        elif search_view == "File":
            inter_filters = fr"""<fileFilter interGroupOP="{inter_op}">
                            <filter interFilterOP="{inter_op}">
                            </filter>
                        </fileFilter>"""
            email_filter = ''
            galaxy_app_type = 4
        else:
            inter_filters = email_filter = ''
            galaxy_app_type = 0

        common_filters = fr"""<filter>
                                <filters field="CISTATE" intraFieldOp="0">
                                    <fieldValues>
                                        <values val="0"/>
                                        <values val="1"/>
                                        <values val="12"/>
                                        <values val="13"/>
                                        <values val="14"/>
                                        <values val="15"/>
                                        <values val="1014"/>
                                        <values val="3333"/>
                                        <values val="3334"/>
                                        <values val="3335"/>
                                    </fieldValues>
                                </filters>
                                <filters field="DATA_TYPE">
                                    <fieldValues>
                                         <values val="2"/>
                                    </fieldValues>
                                </filters>
                            </filter>"""

        # OR : 0, AND : 2

        payload_xml = fr"""
            <DM2ContentIndexing_CVSearchReq mode="2">
                <searchProcessingInfo pageSize="50" resultOffset="0">
                        <queryParams param="SORT_STYLE" value="DESCENDING"/>
                        <queryParams param="SORTFIELD" value="SIZEINKB"/>
                        <queryParams param="ENABLE_NEW_COMPLIANCE_SEARCH"
                         value="true"/>
                        <queryParams param="ENABLE_DEFAULT_VISIBLE_QUERY"
                         value="true"/>
                </searchProcessingInfo>
                <advSearchGrp>
                        <cvSearchKeyword keyword="{search_keyword}"
                        keywordIntraOperator="1" isExactWordsOptionSelected="0"/>
                        {inter_filters}
                        <commonFilter>
                            {common_filters if search_view == "Email" else ''}
                        </commonFilter>
                        <galaxyFilter applicationType="{galaxy_app_type}"/>
                        {email_filter}
                </advSearchGrp>
                {ci_server_list}
                <userInformation userGuid="{user_guid}"/>
            </DM2ContentIndexing_CVSearchReq>
        """
        root = ET.fromstring(payload_xml)
        # To convert to an ElementTree
        if search_view == "Email":
            filter_element = root.findall(".advSearchGrp/emailFilter/filter")[0]

        if search_view == "File":
            filter_element = root.findall(".advSearchGrp/fileFilter/filter")[0]
        indx = 0
        for item in filters:
            if isinstance(filters[item], str):
                if item in {"LANGUAGE", "Sampling Rate"}:
                    filters_element = root.findall(".searchProcessingInfo")[0]
                    attrib = {"param": item,
                              "value": filters[item]}
                    ET.SubElement(filters_element, 'queryParams', attrib)
                elif item == "raw_query":
                    filters_element = root.find(".advSearchGrp")
                    filters_element.set('modeOfQuerying', "2")
                    filters_element.set('rawQuery', filters[item])
                else:
                    all_values = filters[item].split(';')
                    attrib = {"field": item,
                              "intraFieldOp": str(interfilter_operators
                                                  [all_values[0]])}
                    ET.SubElement(filter_element, 'filters', attrib)
                    if search_view == "Email":
                        filters_element = root.findall(".advSearchGrp/emailFilter"
                                                       "/filter/filters")[indx]
                    else:
                        filters_element = root.findall(".advSearchGrp/fileFilter"
                                                       "/filter/filters")[indx]
                    if all_values[0] == "RANGE":
                        att = {"isRange": "1"}
                    else:
                        att = {}
                    ET.SubElement(filters_element, 'fieldValues', att)
                    if search_view == "Email":
                        field_values_element = root.findall(
                            ".advSearchGrp/emailFilter"
                            "/filter/filters/fieldValues")[indx]
                    else:
                        field_values_element = root.findall(
                            ".advSearchGrp/fileFilter"
                            "/filter/filters/fieldValues")[indx]
                    for value_item in all_values[1:]:
                        attrib_val = {"val": value_item}
                        ET.SubElement(field_values_element, 'values', attrib_val)
                    indx = indx + 1

        xml_string = ET.tostring(root)
        return xml_string.decode("utf-8")

    def construct_virtual_index_query(self,
                                      indexserver,
                                      username,
                                      mssql,
                                      indexservercloud=None,
                                      isadvancedsearch=None,
                                      datatypes_search=None):
        """Returns the Solr query to be fired against IndexServer- journal index/ mailbox index
                Args:
                    indexserver(str)      --  Indexserver cloud name (Journal Index/ Mailbox Index)
                                                  usermailbox/journalmailbox/smtpmailbox
                    username (str) -- loggedin user with compliance search capability
                    mssql   -- mssql object
                Returns
                    str - Solr Query
                Raises
                    Exception on failure to construct query
                """
        if indexserver == "Journal Index":
            mailboxtype = 2
        else:
            mailboxtype = 1
        subclient_id_list = self.get_subclient_id(mailboxtype)

        app_id_list = self.get_appid_compliancesearch(username, mssql)

        subclient_assoc_id = []
        for subclient_id in subclient_id_list:
            if int(subclient_id[0]) in app_id_list:
                subclient_assoc_id.append([subclient_id[0]])

        server_urls = self.getAnalyticsServer(subclient_assoc_id, mssql)

        if indexserver =="Mailbox Index":
            app_field_name = "ApplicationId"
        else:
            app_field_name = "apid"

        fq_query = "fq=("

        for appid in app_id_list:
            fq_query = fq_query + app_field_name+ ":" + str(appid) + " OR "

        fq_query = fq_query[:-4] + ")"

        base_url = server_urls[0]
        server_urls = server_urls[1:]

        url_query = base_url + "/select?" + fq_query + "&"

        if len(server_urls) > 0:
            shard_query = "shards="
            for url in server_urls:
                shard_query += url[7:-9] + "shard_0,"
            shard_query = shard_query[:-1]
            url_query = url_query + shard_query + "&"

            if isadvancedsearch:
                # get cloudID
                cloud_id = self.get_cloudid(indexservercloud)

                # get all collection names for the given cloud
                collection_names = self.get_collections_for_cloud(cloud_id)

                corename_prefix = []
                for datatype in datatypes_search:
                    if datatype == "usermailbox":
                        corename_prefix.append("UM")
                    elif datatype == "journalmailbox":
                        corename_prefix.append("JM")
                    elif datatype == "smtpmailbox":
                        corename_prefix.append("CM")

                datatype_collections = []

                for core_name in collection_names:
                    for prefix in corename_prefix:
                        if prefix in core_name:
                            datatype_collections.append(core_name)

                collection_names = datatype_collections

                # construct the query
                url_query =  url_query + "collection="

                for collection in collection_names:
                    url_query = url_query + collection + ","
                url_query = url_query[:-1] + "&"

        return url_query

    def getAnalyticsServer(self, subclient_id_list, mssql):
        """
        Get the Analytics Server associated for the given subclient
        Args:
            subclient_id_list: list of subclient id
            mssql: mssql object

        Returns: CI Server URL
        """
        details = []
        self.log.info('Querying CSDB to get Mailboxes Server URL')
        for subclient_id in subclient_id_list:
            parameter = "@i_SubClientId = "+subclient_id[0]+",@i_RoleName = NULL," \
                        "@i_CorePrefix = NULL,@i_CloudId = NULL," \
                        "@i_ciServerXML = NULL,@i_includeSearchEngine = NULL"
            procedure = 'SET NOCOUNT ON \n exec AppGetAnalyticsServerByRole ' + parameter
            self.log.info(f'Query: {procedure}')
            xml_response = mssql.execute(procedure)
            response = xmltodict.parse(xml_response.rows[0][0])
            resp_list = \
                response['DM2ContentIndexing_CIServers']['listOfCIServer']
            ciServer = []
            if isinstance(resp_list, list):
                for item in resp_list:
                    if item['@cIServerURL'] not in ciServer:
                        if item['@serverType'] == "1" or item['@serverType'] == "5":
                            if item['@cIServerURL'] not in details:
                                details.append(item['@cIServerURL'])
            else:
                if resp_list['@cIServerURL'] not in ciServer:
                    if resp_list['@serverType'] == "1" or resp_list['@serverType'] == "5":
                        if resp_list['@cIServerURL'] not in details:
                            details.append(resp_list['@cIServerURL'])

        self.log.info(f'List of CI details is {details}')
        return details

    def construct_solr_query_for_compliancesearch(
            self,
            username,
            mssql,
            indexservercloud,
            isadvancedsearch=None,
            datatypes_search=None):
        """Returns the Solr query to be fired against IndexServer

        Args:
            username (str) -- loggedin user with compliance search capability
            mssql   -- mssql object
            indexservercloud(str)      --  Indexserver cloud name
            isadvancedsearch(boolean)  -- true/ false or None
            datatypes_search (list)    -- list of datatypes included in advanced search-
                                          usermailbox/journalmailbox/smtpmailbox
        Returns

            str - Solr Query

        Raises
            Exception on failure to construct query
        """

        try:
            # get indexserver client names
            clientnames = self.get_index_server_client_names(indexservercloud)

            # get base URL
            solr_helper_obj = SolrHelper(self)
            base_client = str(clientnames[0][0])
            baseurl = solr_helper_obj.get_solr_baseurl(base_client, 5)

            # get cloudID
            cloud_id = self.get_cloudid(indexservercloud)

            # get all collection names for the given cloud

            collection_names = self.get_collections_for_cloud(cloud_id)
            if isadvancedsearch:
                corename_prefix = []
                for datatype in datatypes_search:
                    if datatype == "usermailbox":
                        corename_prefix.append("UM")
                    elif datatype == "journalmailbox":
                        corename_prefix.append("JM")
                    elif datatype == "smtpmailbox":
                        corename_prefix.append("CM")

                datatype_collections = []

                for core_name in collection_names:
                    for prefix in corename_prefix:
                        if prefix in core_name:
                            datatype_collections.append(core_name)

                collection_names = datatype_collections

            # construct the query

            search_base_url = baseurl + "/" + \
                collection_names[0] + "/" + "select/?collection="

            for collection in collection_names:
                search_base_url = search_base_url + collection + ","

            search_base_url = search_base_url[:-1] + "&"

            # append appids
            app_id_list = self.get_appid_compliancesearch(username, mssql)
            app_ids = ""
            for appid in app_id_list:
                app_ids = app_ids + str(appid) + ","
            appid_query = "fq={!terms f=ApplicationId}" + app_ids[:-1]
            search_base_url = search_base_url + appid_query + "&"
            return search_base_url

        except Exception as exp:
            self.log.info("Unable to construct solr query")
            raise Exception(exp)

    def get_index_server_client_names(self, cloudname):
        """Returns the list of client names for given cloud

        Args:
            cloudname(str)      --  Indexserver cloud name

        Returns

            list - client names list

        Raises
            Exception on failure to find details
        """

        try:
            cloudname = cloudname.replace("_", "")
            _query = "select name from app_client where id in " \
                "(select ClientId from dm2searchservercoreinfo where CloudId in" \
                "(select cloudId from DM2Cloud where name = '{0}'))".format(cloudname)

            self.log.info(
                "Querying CS DB to get indexserver %s client names",
                cloudname)
            self.csdb.execute(_query)
            rows = self.csdb.fetch_all_rows()
            clientnames = []

            for row in rows:
                clientnames.append(row)

            return clientnames

        except Exception as exp:
            self.log.info("Unable to find clientnames of indexserver")
            raise Exception(exp)

    def get_cloudid(self, cloudname):
        """Returns the cloudid for given cloud

        Args:
            cloudname (str)      --  Indexserver cloudname

        Returns

            str - cloudid

        Raises
            Exception on failure to find details
        """
        cloudname = cloudname.replace("_","")
        _query = "(select cloudId from DM2Cloud where displayName = '{0}')".format(
            cloudname)
        self.log.info("Querying CS DB : " + _query)
        self.csdb.execute(_query)
        cloud_id = self.csdb.fetch_one_row()
        if cloud_id is None:
            raise Exception("Unable to find cloud ID in CS db")
        return str(cloud_id[0])

    def get_subclient_id(self, mailboxtype):
        """Returns the subclient id for given mailbox type

        Args:
            mailboxtype (str)      --  mailboxtype
        Returns

            list(str) - subclientid list
        Raises
            Exception on failure to find details
        """
        _query = "(select distinct(subClientId) from APP_EmailConfigPolicyAssoc " \
                 "where mailBoxType = '{0}')".format(
            mailboxtype)
        self.log.info("Querying CS DB : " + _query)
        self.csdb.execute(_query)
        app_ids = self.csdb.fetch_all_rows()
        if app_ids is None:
            raise Exception("Unable to find subclient ID in CS db")
        return app_ids

    def get_appid_compliancesearch(self, username, mssql):
        """
        Args:
            username: Logged in user with compliancesearch rights
            mssql: sql object
        Returns: list of app_ids with Compliance search Capability
        """
        proc = "exec sec_ADUserLogin '{0}',NULL,NULL,25,0,NULL,NULL,1,0,NULL,0," \
               "NULL,NULL,NULL,NULL".format(username)
        self.log.info("Querying CS DB : " + proc)
        response_rows = mssql.execute(proc)
        values_list = response_rows.rows
        appid = []
        for val in values_list:
            appid.append(val[3])

        return appid

    def get_case_manager_clients(self):
        """
        Gets the list of Case Manager Client Ids and their Names

        Returns:
            list of client ids for Case Manager clients
        """
        _query = ("select id, name from APP_Client where id in ("
                  "select componentNameId from APP_ClientProp "
                  "where attrName='Case Manager Pseudo Client')")
        self.log.info("Querying CS DB : " + _query)
        self.csdb.execute(_query)
        clients = self.csdb.fetch_all_rows()
        if clients is None:
            raise Exception("Unable to find subclient ID in CS db")
        client_id_list = list()
        client_name_list = list()
        for client in clients:
            client_id_list.append(client[0])
            client_name_list.append(client[1])
        return client_id_list, client_name_list

    def get_client_id(self, clientname):
        """Returns the clientid for given client

        Args:
            clientname (str)      --  name of the client

        Returns

            str - clientid

        Raises
            Exception on failure to find details
        """
        _query = "(select id from App_client where name = '{0}')".format(
            clientname)
        self.log.info("Querying CS DB : " + _query)
        self.csdb.execute(_query)
        client_id = self.csdb.fetch_one_row()
        if client_id is None:
            raise Exception("Unable to find client ID in CS db")
        return str(client_id[0])


    def get_collections_for_cloud(self, cloudid):
        """Returns the list of collection names for given cloud

        Args:
            cloudid(str)      -- Cloudid

        Returns

            list - collection names list

        Raises
            Exception on failure to find details
        """

        try:
            _query = "select corename from SECollectionInfo where corename " \
                     "not like \'%meta%\' and SchemaType not like \'%sharepoint%\' and CloudID = {0}".format(cloudid)

            self.log.info(
                "Querying CS DB to get"
                " indexserver collection names of cloudid %s",
                cloudid)
            self.csdb.execute(_query)
            rows = self.csdb.fetch_all_rows()
            collectionnames = []

            # Checking if the collection is valid by cross checking
            # with backupset GUID in App_IndexDBInfo table

            for row in rows:
                collection_name = row[0]
                if 'onedriveindex' in collection_name:
                    continue
                data = collection_name.split("_")
                backupset_guid = data[len(data)-1]

                _query = "select count(*) from APP_IndexDBInfo " \
                         "where dbName = '{0}'".format(backupset_guid)
                #self.log.info("Querying CS DB to get IndexDBInfo for backupset %s", backupset_GUID)

                self.csdb.execute(_query)
                count = self.csdb.fetch_one_row()[0]
                if int(count) != 0:
                    # Valid
                    collectionnames.append(collection_name)
            return collectionnames

        except Exception as exp:
            self.log.info("Unable to find clientnames of indexserver")
            raise Exception(exp)

    def create_url_with_debug_query_and_get_response(
            self, helper_obj, select_dict=None, attr_list=None, op_params=None):
        """Helper method to get results from a url with debug query
            Args:
                helper_obj (object)             -- SolrHelper class object

                select_dict(dictionary)         --  Dictionary containing search criteria and
                                                    value. Acts as 'q' field in solr query

                attr_list(set)                  --  Criteria to filter results. Acts as 'fl' in
                                                    solr query

                op_params(dictionary)           --  Other params and values for solr query. Do not
                                                    mention 'wt' param as it is always json
                                                    (Ex: start, rows)

            Returns:
                content of the response
        """
        try:
            solr_url = helper_obj.create_solr_query(
                select_dict, attr_list, op_params)
            solr_url = solr_url + "&debugQuery=false"
            self.log.info(
                "URL formed from the details provided is: %s" %
                solr_url)
            return requests.get(url=solr_url)
        except Exception as excp:
            raise excp

    def submit_advanced_search_api_request(
            self,
            baseurl,
            username,
            password,
            indexserver,
            search_keyword,
            interfilter_op,
            filters,
            search_view="Email"
    ):
        """
        Helper method to submit advanced search REST API request

        Args:
        baseurl (str) - URL corresponding to Webservice base URL
        username (str) - Commserve username
        password (str) - Commserve user password- bas64 encoded
        indexserver(str) - Indexserver cloudname
        search_keyword (str)    - search keyword
        interfilter_op (str) - Interfilter operator to be applied
        filters (str) - List of filters with format interoperator;values
                                          EX: Email_From : OR;email_add1;email_add2
                                          EX: Subject : AND;test_subj1;test_subj2
                                          Interoperator = None in case of single value
                                          EX: Folder: NONE;Inbox
        search_view - Type of search view (Email, File, etc.) used in testcase
        Returns: totalSearchResults(str) - response json value for 'totalHits'
        """
        # Login to get authtoken
        url = baseurl + "/Login"
        login_payload = {
            "username": username,
            "password": password
        }
        cvpysdk = self.commcell._cvpysdk_object
        flag, response = cvpysdk.make_request(
            'POST', url=url, payload=login_payload)

        if flag:
            if response.json() and 'token' in response.json():
                authtoken = response.json()['token']
            else:
                raise SDKException('Response', '102')
        else:
            raise SDKException(
                'Response',
                '101',
                cvpysdk._update_response_(
                    response.text))

        # Get CI Server details
        url = baseurl + "/getCIServerList?mode=2"
        payload = {}
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/xml',
            'Authtoken': authtoken
        }

        cvpysdk = self.commcell._cvpysdk_object
        flag, response = cvpysdk.make_request(
            'GET', url=url, headers=headers, payload=payload)

        if flag:
            if response.json() and 'listOfCIServer' in response.json():
                ci_server_info = response.json()['listOfCIServer']
            else:
                raise SDKException('Response', '102')
        else:
            raise SDKException(
                'Response',
                '101',
                cvpysdk._update_response_(
                    response.text))

        url = baseurl + "/doWebSearch"
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/xml',
            'Authtoken': authtoken
        }

        payload = self.construct_payload(
            search_keyword,
            indexserver,
            username,
            interfilter_op,
            filters,
            ci_server_info,
            search_view
        )
        self.log.info(f'payload: {payload}')
        flag, response = cvpysdk.make_request(
            'POST', url=url, headers=headers, payload=payload)

        if flag:
            self.log.info(f'response.json(): {response.json()}')
            if response.json() and 'proccessingInfo' in response.json():
                total_search_results = response.json(
                )['proccessingInfo']['totalHits']
            else:
                raise SDKException('Response', '102')
        else:
            raise SDKException(
                'Response',
                '101',
                cvpysdk._update_response_(
                    response.text))

        return total_search_results

    def get_index_server_name(self, cloud_id):
        """
        To get the index server name from the CSDB
        Args: cloud_id:            Cloud Id number
        Returns:                    String containing the Index Server name
        """
        query = (
            "select name from app_client where id="
            "(select pseudoClientId from dm2cloud where cloudId=" + cloud_id + ")")
        self.log.info('Querying CSDB to get the Index Server name')
        self.csdb.execute(query)
        index_server = self.csdb.fetch_one_row()
        if index_server is None:
            raise Exception("Unable to find Index Server Name in CSDB")
        self.log.info(
            f'The Index Server Name retrieved from DB is {index_server[0]}')
        return index_server[0]

    def get_app_id(self, case_name, location, username, mssql, skip_user_check=False):
        """
        To query the app_id from the CSDB
        Args: case_name:           Name of the case
        Args: location:            Whether source / destination
        Returns:                    Integer containing the App Id
        """
        app_id_list = []
        if location.lower() == 'source':
            location = 'srcAppId'
        elif location.lower() == 'destination':
            location = 'destAppId'
        query = (
            "select " + location + " from CMReference where definitionId="
            "(select id from cmdefinition where name ='" + case_name + "')")
        self.log.info(f'Querying CSDB to get AppId: {query}')
        self.csdb.execute(query)
        app_id = self.csdb.fetch_all_rows()
        if app_id is None:
            raise Exception("Unable to find App ID in CSDB")
        for value in app_id:
            app_id_list.append(value[0])
        self.log.info(f'The App IDs retrieved from DB is %s', app_id_list)

        if not skip_user_check:
            user_app_id_list = self.get_appid_compliancesearch(username, mssql)
            user_app_ids = list()
            for app_id in app_id_list:
                if int(app_id) in user_app_id_list:
                    user_app_ids.append(app_id)
            return user_app_ids
        return app_id_list

    def get_ci_server_url(self, mssql, app_id, get_backupset_guid=False):
        """
        To get the URL of the Content Indexing Server
        Args: mssql:               MSSQL Object
        Args: app_id:              The App Id of the case
        Returns:                    List containing the URL(s) of the CI Server
        """
        query = (
            "select GUID from APP_BackupSetName where id in "
            "(select backupSet from App_Application where id in " + app_id + ")")
        self.log.info('Querying CSDB to get BackupSet GUIDs')
        self.log.info(f'query: {query}')
        self.csdb.execute(query)
        guid_list = []
        backupset_guid = self.csdb.fetch_all_rows()
        if backupset_guid is None:
            raise Exception('Unable to find BackupSet GUID in CSDB')
        for value in backupset_guid:
            guid_list.append(value[0])
        self.log.info(f'The backupSet GUID retrieved from DB is {guid_list}')
        if get_backupset_guid:
            return guid_list

        details_list = []
        distinct_cloud_ids = []
        ciServer = []
        for guid in guid_list:
            parameter = ("'<Indexing_GetCloudServerReq backupsetGUID=\""
                         + guid + "\" corePrefix=\"\"/>'")
            self.log.info('Querying CSDB to get CI Server URLs')
            query = 'SET NOCOUNT ON \n EXEC AppGetCloudServerInfo @inputXml=' + parameter
            self.log.info('query: %s', query)
            xml_response = mssql.execute(query)
            response = xmltodict.parse(xml_response.rows[0][0])
            resp_list = \
                response['DM2ContentIndexing_GetCloudServerResp']['ciServers']['listOfCIServer']
            if isinstance(resp_list, list):
                for item in resp_list:
                    if item['@cIServerURL'] not in ciServer:
                        if item['@serverType'] == "1" or item['@serverType'] == "5":
                            details = dict()
                            details['ciServer'] = item['@cIServerURL']
                            ciServer.append(item['@cIServerURL'])
                            details['cloudId'] = item['@cloudID']
                            details['serverType'] = item['@serverType']
                            details['schemaVersion'] = item['@schemaVersion']
                            if item['@cloudID'] not in distinct_cloud_ids:
                                distinct_cloud_ids.append(item['@cloudID'])
                            details_list.append(details)
            else:
                if resp_list['@cIServerURL'] not in ciServer:
                    if resp_list['@serverType'] == "1" or resp_list['@serverType'] == "5":
                        details = dict()
                        details['ciServer'] = resp_list['@cIServerURL']
                        ciServer.append(resp_list['@cIServerURL'])
                        details['cloudId'] = resp_list['@cloudID']
                        details['serverType'] = resp_list['@serverType']
                        details['schemaVersion'] = resp_list['@schemaVersion']
                        if resp_list['@cloudID'] not in distinct_cloud_ids:
                            distinct_cloud_ids.append(resp_list['@cloudID'])
                        details_list.append(details)
        self.log.info(f'List of CI details is {details_list}')
        return details_list, distinct_cloud_ids

    def get_archfile_id(self, job_id):
        """
        To get the Archive File Id given the Job Id
        Args: job_id:              Job Id
        Returns:                    Archive File Id
        """
        query = "select id from archFile where jobId='" + str(job_id) + "'"
        self.log.info('Querying CSDB to get Archive File Id')
        self.log.info(f'Query: {query}')
        self.csdb.execute(query)
        afile_id = self.csdb.fetch_all_rows()
        afile_list = []
        if afile_id is None:
            raise Exception("Unable to find Archive File ID in CSDB")
        for file_id in afile_id:
            afile_list.append(file_id[0])
        self.log.info(
            f'The Archive File IDs retrieved from DB are %s',
            afile_list)
        return afile_list

    def get_exchange_app_id(self,client_id):
        """
        To query the app_id from the CSDB
        Args: client_id:           client id
        Returns:                    Integer containing the App Id
        """
        app_id_list = []
        query = ("select id from App_Application where appTypeId=137 and clientId="+str(client_id))
        self.log.info(f'Querying CSDB to get AppId: {query}')
        self.csdb.execute(query)
        app_id = self.csdb.fetch_all_rows()
        if app_id is None:
            raise Exception("Unable to find App ID in CSDB")
        for value in app_id:
            app_id_list.append(value[0])
        self.log.info(f'The App IDs retrieved from DB is %s', app_id_list)
        return app_id_list
