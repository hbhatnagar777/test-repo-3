# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for CSDB queries queries """
import xmltodict


class CSDBHelper:
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

    def get_index_server_url(self, mssql, job_id=None, client_name=None):
        """
        Get the onedrive index core name for the respective job id

        Args:
            mssql       :       MSSQL Object
            job_id (str):       Job Id
            client_name (str):  Name of client

        Returns:
            url (str):    The Index Server URL

        """
        if client_name:
            query = (f"select GUID from APP_BackupSetName where id=("
                     f"select backupSet from APP_Application where clientId=("
                     f"select id from APP_Client where name='{client_name}'))")
        else:
            query = (f"select GUID from APP_BackupSetName where id=("
                     f"select backupSet from APP_Application where id=("
                     f"select top 1 appId from JMBkpStats where jobId='{job_id}'))")
        self.log.info('Querying CSDB to get BackupSet GUID')
        self.log.info(f'query: {query}')
        self.csdb.execute(query)
        backupset_guid = self.csdb.fetch_all_rows()[0][0]
        if backupset_guid is None:
            raise Exception('Unable to find BackupSet GUID in CSDB')
        self.log.info(f'The backupSet GUID retrieved from DB is {backupset_guid}')

        parameter = ("'<Indexing_GetCloudServerReq backupsetGUID=\""
                     + backupset_guid + "\" corePrefix=\"\"/>'")
        query = 'SET NOCOUNT ON \n EXEC AppGetCloudServerInfo @inputXml=' + parameter
        self.log.info('Querying CSDB to get CI Server URLs')
        self.log.info(f'query: {query}')
        xml_response = mssql.execute(query)
        response = xmltodict.parse(xml_response.rows[0][0])
        url = response['DM2ContentIndexing_GetCloudServerResp']['ciServers']['listOfCIServer']['@cIServerURL']
        if url is None:
            raise Exception('Unable to find Index Server URL in CSDB')
        self.log.info(f'The Index Server URL retrieved from DB is {url}')
        return url

    def get_subclient_id(self, app_name):
        """
        Gets the subclient id for a given OneDrive client

        Args:
            app_name (str): Name of the OneDrive client

        Returns:
            subclient_id (str): The subclient id

        """
        query = f"select id from APP_Client where name='{app_name}'"
        self.log.info('Querying CSDB to get Client Id')
        self.log.info(f'query: {query}')
        self.csdb.execute(query)
        client_id = self.csdb.fetch_all_rows()[0][0]
        if client_id is None:
            raise Exception('Unable to find Client Id in CSDB')
        self.log.info(f'The subclient id retrieved from DB is {client_id}')

        query = f"select id from APP_Application where clientId={client_id}"
        self.log.info('Querying CSDB to get Subclient Id')
        self.log.info(f'query: {query}')
        self.csdb.execute(query)
        subclient_id = self.csdb.fetch_all_rows()[0][0]
        if subclient_id is None:
            raise Exception('Unable to find Subclient Id in CSDB')
        self.log.info(f'The subclient id retrieved from DB is {subclient_id}')
        return client_id, subclient_id

    def get_access_node_details(self, app_name):
        """
        Gets the access node details for a given OneDrive client

        Args:
            app_name (str): Name of the OneDrive client

        Returns:
            machine_name and client_name

        """
        query = (f"select attrVal from APP_InstanceProp where componentNameId=("
                 f"select instance from APP_Application where clientId=("
                 f"select id from APP_Client where name='{app_name}')) "
                 f"and attrName='Proxy Clients'")
        self.log.info('Querying CSDB to get Access Node client id')
        self.log.info(f'query: {query}')
        self.csdb.execute(query)
        xml_response = self.csdb.fetch_all_rows()[0][0]
        if xml_response is None:
            raise Exception('Unable to find Access Node client id in CSDB')
        self.log.info(f'The xml response retrieved from DB is {xml_response}')
        response = xmltodict.parse(xml_response)
        client_id = response['App_GeneralCloudProperties']['memberServers']['client']['@clientId']

        query = f"select name, net_hostname from APP_Client where id={client_id}"
        self.log.info('Querying CSDB to get Access Node details')
        self.log.info(f'query: {query}')
        self.csdb.execute(query)
        details = self.csdb.fetch_all_rows()[0]
        client_name = details[0]
        machine_name = details[1]
        return client_name, machine_name

    def get_user_guid(self, client_name, user_name):
        """
        Returns the userGUID for a particular user in a particular client

        Args:
            client_name (str):  Office365 Client Name
            user_name (str):    Email address of user

        Returns:
            user_guid (str):    GUID of the user

            select userGUID from APP_CloudAppUserDetails
            where subClientId = (
                select id from APP_Application where clientId=(
                    select id from APP_Client
                    where name='Nandini_Automation_FiltersTest'
                )
            ) and smtpAddress = 'onedrive_automation_include_filter_test_user@commvault365.onmicrosoft.com'
        """
        query = (f"select userGUID from APP_CloudAppUserDetails where subClientId=("
                 f"select id from APP_Application where clientId=("
                 f"select id from APP_Client where name='{client_name}')) "
                 f"and smtpAddress='{user_name}'")
        self.log.info('Querying CSDB to get userGUID')
        self.log.info(f'query: {query}')
        self.csdb.execute(query)
        user_guid = self.csdb.fetch_one_row()[0]
        if user_guid is None:
            raise Exception('Unable to find userGUID in CSDB')
        self.log.info(f'The userGUID retrieved from DB is {user_guid}')
        return user_guid

    def get_cloudappuser_detail(self, subclient_id):
        """
        Returns the list of users from the App_CloudAppUserDetails table

        Args:
            subclient_id(int)             : subclient id of the subclient


        Retruns:

            license_user                : List of the users

        """

        query = (f"select smtpAddress from App_CloudAppUserDetails where licensingStatus =1 "
                 f"and modified = 0and flags=1 and subclientid ={subclient_id}")

        self.log.info("Executing the query to get the license user from the CSDB")
        self.log.info(f"query {query}")
        self.csdb.execute(query)
        license_users = self.csdb.fetch_all_rows()
        return license_users

    def get_cloudappslicensing_user(self, backupset_id):
        """
        Returns the list of users from the CloudAppLicensingInfo Table

        Args:
            backupset_id(int)             : backupset id of the client


        Retruns:
            license_user(list)                : List of the users

        """
        query = f"select email from CloudAppsLicensingInfo with (NOLOCK) where backupsetId = {backupset_id}"
        self.log.info("Executing the query to get the license user from the CSDB")
        self.log.info(f"query {query}")
        self.csdb.execute(query)
        license_users = self.csdb.fetch_all_rows()
        return license_users

    def get_lic_currentusage_user(self, client_id):
        """
        Returns the list of users from the Lic_CurrentUsage table

        Args:
            client_id(int)             : client id of the client


        Retruns:

            license_user(list)                : List of the users

        """
        query = f"select ObjectName from Lic_CurrentUsage with (NOLOCK) where ClientId={client_id} and UsageType = 18"
        self.log.info("Executing the query to get the license user from the CSDB")
        self.log.info(f"query {query}")
        self.csdb.execute(query)
        license_users = self.csdb.fetch_all_rows()
        return license_users

    def get_commcell_number(self):
        """
        Returns the commcell No. of the current setup

        Retruns:

            commcell_number(int)               : returns the commcell number
        """
        query = f"SELECT number from APP_CommCell where id = 2"
        self.log.info("Executing the query to get the license user from the CSDB")
        self.log.info(f"query {query}")
        self.csdb.execute(query)
        commcell_number = self.csdb.fetch_all_rows()
        return commcell_number[0][0]

    def get_authcode_setclientproperty(self, client_id,commcell_number):
        """
        Returns the authcode required to run the qscript for setting client level property

        Args:
            client_id(int)             : client id of the client
            commcell_number(int)       : commcell number of the commcell

        Retruns:

            authcode(int)              : returns the authcode
        """
        query = f"SELECT (CHECKSUM(HASHBYTES('SHA1', '<' + N'QS_SetClientProperty' + '><' + N'{client_id}' + '><' + N'{commcell_number}' + '><COMMVAULT>')) & 2147483646)"
        self.log.info("Executing the query to get the license user from the CSDB")
        self.log.info(f"query {query}")
        self.csdb.execute(query)
        authcode = self.csdb.fetch_all_rows()
        return authcode[0][0]
