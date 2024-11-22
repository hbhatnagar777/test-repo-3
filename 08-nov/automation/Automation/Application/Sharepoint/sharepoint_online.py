# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
    Main Module for setting input variables and defining sharepoint specific functions
    This module is imported in any test case.
    You need to create an object of this module in the test case.

    SharePoint Online Pseudo Client: Class for defining sharepoint
    specific functions i.e., for making Graph and REST api calls
"""

from __future__ import unicode_literals
import random
import urllib.parse
import json
import requests
import re
import time
import subprocess
import os
from functools import wraps
from office365.sharepoint.client_context import ClientContext, ClientCredential
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.runtime.http.request_options import RequestOptions
from office365.runtime.http.http_method import HttpMethod
from O365 import Account
from O365.sharepoint import Sharepoint
from Application.Office365.solr_helper import SolrHelper
from ..Office365.operations import SharepointCvOperation
from . import sharepointconstants


class SPGraphAPIHelper(Sharepoint):
    """Class for defining SharePoint graph api functions
    """

    def __init__(self, parent, log, **kwargs):
        """Initializes the SPGraphAPIHelper object

            Args:

                parent  (Account object)        :   parent object

                log     (Logger object)         :   logger object
        """
        self.log = log
        self.parent = parent
        self.base_url = "https://graph.microsoft.com/v1.0"

        main_resource = kwargs.pop('main_resource', '')
        super().__init__(con=parent.con, protocol=parent.protocol, main_resource=main_resource)

    def search_sites(self, keyword):
        """Searches the SharePoint tenant for sites with the provided keyword

            Args:

                keyword (list[Site])        --   a keyword to search sites

        """
        if not keyword:
            raise ValueError('Must provide a valid keyword')

        self.log.info(f"Searching for site with keyword {keyword}")
        url = self.build_url(
            self._endpoints.get('search').format(keyword=keyword))

        response = self.con.get(url)
        if not response:
            return []

        data = response.json()
        next_link = data.get('@odata.nextLink')
        return_dict = {}
        if next_link:
            return_dict['nextLink'] = next_link

        return_dict['site_info'] = [
            self.site_constructor(parent=self, **{self._cloud_data_key: site})
            for site in data.get('value', [])]
        return return_dict

    def get_all_sites(self, tenant_name=None):
        """Gets all the active sites present in the SharePoint tenant

            Args:

                tenant_name (str)           --  name of the SharePoint tenant

        """

        url = "/".join([self.base_url, "sites", "getAllSites"])
        result = []

        self.log.info(f"Getting all sites from tenant {tenant_name}")
        while True:
            response = self.con.get(url)
            if not response:
                return result

            data = response.json()
            for site in data.get('value', []):
                if tenant_name and not site['webUrl'].startswith(f'https://{tenant_name}.sharepoint'):
                    continue
                result.append(
                    self.site_constructor(parent=self, **{self._cloud_data_key: site}))

            url = data.get('@odata.nextLink')
            if url is None:
                return result

    def get_teams_connected_sites(self, site_admin_url, username, password):
        """Searches the SharePoint tenant for sites connected to Teams"""
        self.log.info(f"Getting all teams connected sites from tenant {site_admin_url}")
        try:
            completed_process = subprocess.run(['powershell', '-File', sharepointconstants.GET_TEAMS_SITES,
                                                site_admin_url, username, password], text=True, timeout=300,
                                               check=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            file_name = completed_process.stdout.strip()
        except subprocess.CalledProcessError as cpe:
            raise Exception(cpe)

        if not file_name:
            return []

        with open(file_name, 'r', encoding='utf-8') as f:
            sites = [stripped for line in f.read().strip().split('\n') if (stripped := line.strip())]

        result = []
        for site_url in sites:
            host_name, path_to_site = site_url.removeprefix('https://').split('/', 1)
            result.append(self.parent.sharepoint().get_site(host_name, path_to_site))

        os.remove(file_name)
        return result

    def get_user(self, keyword):
        """Searches the SharePoint tenant for the user with the provided keyword

            Args:

                keyword (list[Site])        --   a keyword to search users

        """
        self.log.info(f"Searching for user with keyword {keyword}")
        if not keyword:
            raise ValueError('Must provide a valid keyword')
        self._endpoints['users'] = '/users/{keyword}'

        url = self.build_url(
            self._endpoints.get('users').format(keyword=keyword))

        response = self.con.get(url)
        if not response:
            return []

        data = response.json()
        if 'error' in data:
            error_code = response.json()['error']['code']

            if error_code != 0:
                error_string = response.json()['response']['errorString']
                raise Exception('Failed to get User Information\nError: "{0}"'.format(error_string))
        elif 'userPrincipalName' in data:
            return data

    def create_teams_connected_site(self, site_title):
        """Creates a teams connected site using Graph API

            Args:

                site_title  (str)       :   Site title
        """
        self.log.info(f"Creating teams connected site {site_title}")
        url = "/".join([self.base_url, "groups"])

        group_data = {
            "description": "It is a group",
            "displayName": site_title,
            "groupTypes": ["Unified"],  # Unified type means Microsoft 365 group
            "mailEnabled": True,
            "mailNickname": site_title,
            "securityEnabled": False
        }
        response = self.con.post(url, json=group_data)
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create teams connected site: {site_title}")

        self.log.info(f"Teams connected site {site_title} created successfully")


class SharePointOnline:
    """Class for defining SharePoint specific functions i.e., for making graph
    and REST api calls"""

    def __init__(self, tc_object):
        """creates object from other modules.

            Args:

                tc_object   --  instance of testcase class

            Returns:

                object      --  instance of SharePointOnline class

        """
        self.tc_object = tc_object
        self.log = self.tc_object.log
        self.log.info('logger initialized for SharePoint Client')
        self.app_name = self.__class__.__name__
        self.csdb = self.tc_object.csdb
        self.cvoperations = SharepointCvOperation(self)
        self.pseudo_client_name = None
        self.backupset_name = sharepointconstants.BACKUPSET_NAME
        self.subclient_name = sharepointconstants.SUBCLIENT_NAME
        self.server_plan = None
        self.index_server = None
        self.access_nodes_list = None
        self.machine_name = None
        self.is_modern_auth_enabled = None
        self.global_administrator = None
        self.global_administrator_password = None
        self.azure_app_id = None
        self.azure_app_secret = None
        self.azure_app_tenant_id = None
        self.job_results_directory = None
        self.azure_username = None
        self.azure_secret = None
        self.cert_string = None
        self.cert_password = None
        self.site_collection_list = []
        self._sp_api_object = None
        self.site_url_list = []
        self.site_url = None
        self.office_365_plan = None
        self.tenant_url = None
        self.user_username = None
        self.user_password = None
        self._ctx_auth = None
        self.v1 = False
        self.is_modern_auth_enabled = None
        self.environment = self.tc_object.tcinputs.get('Environment', 'commercial')
        self._client_cred = None

    @property
    def sp_api_object(self):
        """Returns an instance of SPGraphAPIHelper"""
        if self._sp_api_object is None:
            account = self.authenticate_microsoft_tenant()
            self._sp_api_object = SPGraphAPIHelper(account, self.log)
        return self._sp_api_object

    @property
    def ctx_auth(self):
        """Returns the context authentication object"""
        if self._ctx_auth is None:
            self._ctx_auth = AuthenticationContext(self.site_url)
            self.generate_token()
        return self._ctx_auth

    @property
    def client_cred(self):
        """Returns the client credential object"""
        if self._client_cred is None:
            self._client_cred = ClientCredential(self.azure_app_id, self.azure_app_secret)
        return self._client_cred

    def initialize_sp_v1_client_attributes(self):
        """Initializes SharePoint V1 client attributes to create client"""
        try:
            self.pseudo_client_name = self.tc_object.tcinputs['PseudoClientName']
            self.server_plan = self.tc_object.tcinputs['ServerPlanName']
            self.backupset_name = self.tc_object.tcinputs['BackupsetName']
            self.subclient_name = self.tc_object.tcinputs.get('SubclientName')
            self.user_username = self.tc_object.tcinputs['Username']
            self.user_password = self.tc_object.tcinputs['Password']
            self.is_modern_auth_enabled = self.tc_object.tcinputs.get('IsModernAuthEnabled', False)
            self.tenant_url = self.tc_object.tcinputs['TenantUrls']
            self.azure_app_id = self.tc_object.tcinputs['AzureAppId']
            self.azure_app_secret = self.tc_object.tcinputs['AzureAppKeyValue']
            self.azure_app_tenant_id = self.tc_object.tcinputs['AzureDirectoryId']
            self.cert_string = self.tc_object.tcinputs['CertString']
            self.cert_password = self.tc_object.tcinputs['CertPassword']
            self.azure_username = self.tc_object.tcinputs['AzureUsername']
            self.azure_secret = self.tc_object.tcinputs['AzureSecret']
            self.v1 = True
        except Exception as exception:
            self.log.exception("Required details are not given to create SharePoint v1 client: %s", str(exception))
            raise exception

    def initialize_sp_v2_client_attributes(self):
        """Initializes SharePoint V2 client attributes to create client"""
        try:
            self.pseudo_client_name = self.tc_object.tcinputs['PseudoClientName']
            self.server_plan = self.tc_object.tcinputs['ServerPlanName']
            self.index_server = self.tc_object.tcinputs['IndexServer']
            self.access_nodes_list = list(self.tc_object.tcinputs['AccessNodes'])
            self.machine_name = self.tc_object.tcinputs.get('MachineName', '')
            if len(self.access_nodes_list) > 1:
                self.job_results_directory = self.tc_object.tcinputs['SharedJRDirectoryDetails']
            self.is_modern_auth_enabled = self.tc_object.tcinputs.get('IsModernAuthEnabled', False)
            self.tenant_url = self.tc_object.tcinputs['TenantUrl']
            self.global_administrator = self.tc_object.tcinputs.get('GlobalAdministrator', '')
            if self.global_administrator:
                self.global_administrator_password = self.tc_object.tcinputs['GlobalAdministrator Password']
                self.azure_app_id = self.tc_object.tcinputs['AzureAppId']
                self.azure_app_secret = self.tc_object.tcinputs['AzureAppKeyValue']
                self.azure_app_tenant_id = self.tc_object.tcinputs['AzureDirectoryId']
            else:
                self.user_username = self.tc_object.tcinputs['Username']
                self.user_password = self.tc_object.tcinputs['Password']
                if self.is_modern_auth_enabled:
                    self.azure_app_id = self.tc_object.tcinputs['AzureAppId']
                    self.azure_app_secret = self.tc_object.tcinputs['AzureAppKeyValue']
                    self.azure_app_tenant_id = self.tc_object.tcinputs['AzureDirectoryId']
            self.cert_string = self.tc_object.tcinputs.get('CertString', '')
            self.cert_password = self.tc_object.tcinputs.get('CertPassword', '')
            self.azure_username = self.tc_object.tcinputs.get('AzureUserName', '')
            self.azure_secret = self.tc_object.tcinputs.get('AzureSecret', '')
        except Exception as exception:
            self.log.exception("Required details are not given to create SharePoint v2 client: %s", str(exception))
            raise exception

    def authenticate_microsoft_tenant(self):
        """This function authenticates the Microsoft tenant and
        creates an account object for running Microsoft graph APIs
        """
        try:
            credentials = (self.azure_app_id, self.azure_app_secret)
            account = Account(credentials, auth_flow_type='credentials',
                              tenant_id=self.azure_app_tenant_id)
            if account.authenticate():
                self.log.info('Client authenticated successfully for running graph API')
                return account
            self.log.error('Client authenticated failed for running graph API')
            raise Exception('Client authenticated failed for running graph API')
        except Exception as exception:
            self.log.exception("Exception while authenticating microsoft tenant: %s", str(exception))
            raise exception

    def get_sites_count(self, get_only_root_sites=True):
        """Returns total count of site collections present in the tenant

             Args:

                      get_only_root_sites (bool)   --  whether to return only root sites count
        """
        try:
            # Authorise microsoft tenant account to run graph API
            # Call graph API and get response and count number of site collections
            api_site_count = 0
            api_subsites_count = 0
            tenant_name = None
            if self.tenant_url:
                tenant_name = re.match(r'https://(.+)-admin\.sharepoint.*', self.tenant_url).group(1)
            elif self.site_url:
                tenant_name = re.match(r'https://(.+)\.sharepoint.*', self.site_url).group(1)

            team_sites = self.sp_api_object.get_teams_connected_sites(
                self.tenant_url, self.global_administrator, self.global_administrator_password)
            team_sites_count = len(team_sites)
            for site in team_sites:
                try:
                    team_sites_count += len(self.get_all_subsites(site))
                except Exception as teams_subsites_exp:
                    self.log.error(f'Error getting subsites for teams site {site.web_url}: {teams_subsites_exp}')

            site_data = self.sp_api_object.get_all_sites(tenant_name=tenant_name)
            for site in site_data:
                response = requests.get(site.web_url)
                if response.text == '404 FILE NOT FOUND':
                    continue
                if site.root and site.display_name != '':
                    self.site_collection_list.append(site)
                    api_site_count = api_site_count + 1
                if not get_only_root_sites:
                    try:
                        api_subsites_count += len(self.get_all_subsites(site))
                    except Exception as subsites_exp:
                        self.log.error(f"Error getting subsites for {site.web_url}: {subsites_exp}")

            if get_only_root_sites:
                return api_site_count, team_sites_count
            else:
                return api_site_count, api_subsites_count, team_sites_count
        except Exception as exception:
            self.log.exception("Exception while getting count of sites: %s", str(exception))
            raise exception

    def get_all_subsites(self, site):
        """Returns list of all subsites by scanning subsites recursively till all the subsites are scanned
             Args:

                  site (object)   --  object of Sharepoint Site class
        """
        try:
            subsites = site.get_subsites()
            sub_subsites = []
            for subsite in subsites:
                sub_subsites.extend(self.get_all_subsites(subsite))
            return subsites + sub_subsites
        except Exception as exception:
            self.log.exception("Exception while getting subsites: %s", str(exception))
            raise exception

    def is_onedrive_site(self):
        """Checks if the site is OneDrive site and returns True if it is"""
        return '-my.sharepoint.com/personal/' in self.site_url

    def get_group_based_sites_count(self):
        """Returns count of sites group wise including its subsites present in tenant
        """
        try:
            all_sites_count, team_site_count = self.get_sites_count()
            project_online_site_count = 0
            for site in self.site_collection_list:
                self.site_url = urllib.parse.unquote(site.web_url)
                if self.is_onedrive_site():
                    self.log.info(f'Skipping site: {self.site_url}')
                    continue

                site_properties = self.get_site_properties(root_site=True)
                if site_properties.get("WebTemplate") == "PWA":
                    project_online_site_count = project_online_site_count + 1
                sub_sites = self.get_all_subsites(site)
                if sub_sites:
                    for sub_site in sub_sites:
                        if sub_site:
                            if site_properties.get("WebTemplate") == "PWA":
                                project_online_site_count = project_online_site_count + 1
                            all_sites_count = all_sites_count + 1
            self.log.info(f"All Web Sites : {all_sites_count}")
            self.log.info(f"All Teams Sites : {team_site_count}")
            self.log.info(f"All Project Online Sites : {project_online_site_count}")
            return {
                "All Web Sites": all_sites_count,
                "All Teams Sites": team_site_count,
                "All Project Online Sites": project_online_site_count
            }
        except Exception as exception:
            self.log.exception("Exception while getting group based sites count: %s", str(exception))
            raise exception

    def validate_site_collections_count(self):
        """Validates site collections
            1. Count of site collections using Microsoft Graph API
            2. Count of site collections by querying CSDB
            Validates by comparing above two counts
        """
        try:
            api_site_count, _ = self.get_sites_count()
            # Query CSDB to get site collections count, ItemType = 2
            query_string = sharepointconstants.CSDB_QUERY['site collection count']
            query = query_string.format(self.cvoperations.subclient.subclient_id,
                                        sharepointconstants.ITEM_TYPE['site collections'])
            self.csdb.execute(query)
            csdb_count = self.csdb.fetch_one_row()

            """
            The following urls are present in graph api_response and not in csdb
            https://cvdevtenant.sharepoint.com/sites/contentTypeHub

            The following urls are present in  csdb and not in graph api_response
            https://cvdevtenant.sharepoint.com/search
            https://cvdevtenant-my.sharepoint.com/

            Search template sites are not getting fetched by Graph API

            For now assuming the site count difference shouldn't exceed 10
            """

            self.log.info("CSDB Site Count  : {0}, Graph API Site Count : {1} ".format(csdb_count[0], api_site_count))
            if abs(int(csdb_count[0]) - api_site_count) > 10:
                self.log.error("Site Collections are not equal")
                raise Exception("Site Collections are not equal")
        except Exception as exception:
            self.log.exception("Exception while validating site collections count: %s", str(exception))
            raise exception

    def validate_site_data(self):
        """Validates the following site properties
            1. Display name
            2. SMTP Address
            3. Validates all webs
        """
        try:
            no_of_sites = len(self.site_collection_list)
            sites_validated_count = 0
            no_of_sites_to_be_validated = no_of_sites // 10
            if no_of_sites_to_be_validated > 20:
                no_of_sites_to_be_validated = 20
            self.log.info("Validating Site Data for random {0} sites".format(no_of_sites_to_be_validated))
            for i in range(no_of_sites_to_be_validated):
                site_index = random.randrange(0, no_of_sites)
                site = self.site_collection_list[site_index]
                smtp_address = urllib.parse.unquote(site.web_url).replace("'", "''")
                query_string = sharepointconstants.CSDB_QUERY['site collection properties']
                query = query_string.format(self.cvoperations.subclient.subclient_id,
                                            sharepointconstants.ITEM_TYPE['site collections'],
                                            smtp_address)
                self.csdb.execute(query)
                csdb_site_data = self.csdb.fetch_one_row()
                self.log.info("Query Result : {0}".format(csdb_site_data))
                if len(csdb_site_data) > 0:
                    if csdb_site_data[0] != '' and csdb_site_data[0] == site.name:
                        sites_validated_count = sites_validated_count + 1
                        self.log.info("{0} site collection is present in csdb".format(smtp_address))
                        self.validate_webs_for_the_site(site)
                    else:
                        self.log.error("Unable to fetch site information for {0} from csdb".format(smtp_address))
                else:
                    """
                    Few site collections are not present in csdb
                    For now just displaying the url if it not present in csdb
                    """
                    self.log.error("{0} site collection is not present in csdb".format(smtp_address))
            self.log.info(("{0} sites and their web data are validated correctly out of {1} "
                           "sites").format(sites_validated_count, no_of_sites_to_be_validated))
            if no_of_sites_to_be_validated - sites_validated_count > 5:
                self.log.exception("Site Validation is not done properly")
                raise Exception("Site Validation is not done properly")
        except Exception as exception:
            self.log.exception("Exception while validating site data: %s", str(exception))
            raise exception

    def validate_site_collections(self):
        """Validates site collections by
            1. Validating site collections count
            2. Validating site data
        """
        self.validate_site_collections_count()
        self.log.info("Site Collections count is validated successfully")
        self.validate_site_data()
        self.log.info("Site Data is validated successfully")

    def validate_webs_for_the_site(self, site):
        """Validates webs i.e., all sub_sites  of a site collection in share point tenant
            1. Get sub_sites i.e, webs of the site collection
            2. Query csdb to validate sub_sites. The following properties are validated
                -> SMTP Address
                -> Display name
                -> ItemType = 1

            Args:

                site (Site)   --  object of site collection

        """
        try:
            sub_sites = site.get_subsites()
            if sub_sites:
                for sub_site in sub_sites:
                    if sub_site:
                        smtp_address = urllib.parse.unquote(sub_site.web_url).replace("'", "''")
                        query_string = sharepointconstants.CSDB_QUERY['web properties']
                        query = query_string.format(self.cvoperations.subclient.subclient_id,
                                                    sharepointconstants.ITEM_TYPE['site collections'], smtp_address)
                        self.csdb.execute(query)
                        csdb_web_data = self.csdb.fetch_one_row()
                        self.log.info("Query Result : {0}".format(csdb_web_data))
                        if len(csdb_web_data) > 0 and csdb_web_data[0] != '':
                            if csdb_web_data[1].split('/')[-1] == sub_site.name and int(csdb_web_data[2]) == 1:
                                self.log.info("{0} web is present in csdb".format(sub_site.web_url))
                            else:
                                self.log.error("{0} web properties are not correct".format(sub_site.web_url))
                        else:
                            self.log.error("{0} web is not present in csdb".format(sub_site.web_url))
                self.log.info("Validated webs successfully for the site {0}".format(site.web_url))
            else:
                self.log.info("No webs present for the site {0}".format(site.web_url))
        except Exception as exception:
            self.log.exception("Exception while validating subsites of the site: %s", str(exception))
            raise exception

    def validate_properties(self, property_list_1, property_list_2):
        """Validates whether properties in provided lists are equal or not

            Args:

               property_list_1 (list)   :   list of tuples of properties and their values
                                            Example -
                                                property_list_1 = [('property1', value1),('property2', value2)]

               property_list_2 (list)   :   list of values of properties
                                            Example -
                                                property_list_2 = [value1, value2]

           Raises:

                Exception:
                    if subsite properties are not equal


        """
        try:
            for i in range(len(property_list_1)):
                if property_list_1[i][1] == property_list_2[i]:
                    self.log.info(f"{property_list_1[i][0]} is validated")
                else:
                    self.log.error(f"Values for {property_list_1[i][0]} property are not equal")
                    raise Exception(f"values for {property_list_1[i][0]} property are not equal")
            else:
                self.log.info("All properties are validated")
        except Exception as exception:
            self.log.exception("Exception while validating property: %s", str(exception))
            raise exception

    def validate_subsite_properties(self, subsite_metadata):
        """Validates properties of subsite in CSDB

            Query csdb to validate sub_site. The following properties are validated
               -> SMTP Address
               -> Display name
               -> Type of Association
               -> flags value
               -> Status for deleted sites

           Args:

               subsite_metadata (dict)   --  metadata of subsite

           Raises:

                Exception:
                    if subsite properties are not correct

        """
        try:
            subsite_url = self.site_url + '/' + subsite_metadata.get('Url End', "")
            query_string = sharepointconstants.CSDB_QUERY['web properties']
            query = query_string.format(self.cvoperations.subclient.subclient_id, sharepointconstants.ITEM_TYPE['web'],
                                        subsite_url)
            self.csdb.execute(query)
            csdb_web_data = self.csdb.fetch_one_row()
            self.log.info("Query Result : {0}".format(csdb_web_data))
            if len(csdb_web_data) > 0 and csdb_web_data[0] != '':
                input_web_data = [("Title", subsite_metadata.get('Title', "")), ("URL", subsite_url),
                                  ("Item Type", '1'),
                                  ("Association Type", '1'), ("Associated Flags Value",
                                                              subsite_metadata.get('Associated Flags Value', "")),
                                  ('Office 365 Plan Id', str(subsite_metadata.get("Office 365 Plan Id", 0))),
                                  ('Status', '0')]
                if subsite_metadata.get('Operation') == 'DELETED':
                    input_web_data[-1] = ('Status', '1')
                self.log.info(f"Validating list : {input_web_data}")
                self.validate_properties(input_web_data, csdb_web_data)
                self.log.info(f"{subsite_url} site is validated in csdb")
            else:
                self.log.exception(f"{subsite_url} record is not present in csdb")
                raise Exception(f"{subsite_url} record is not present in csdb")
        except Exception as exception:
            self.log.exception("Exception while validating subsites: %s", str(exception))
            raise exception

    def generate_token(self):
        """Generates token for making SharePoint REST API calls

            Returns:

                True (boolean)         --  if token is generated

            Raises:

                Exception:
                    if token is not generated even after 5 attempts

        """
        try:
            if not self.site_url:
                if self.site_url_list:
                    self.site_url = self.site_url_list[0]
                else:
                    raise Exception("Site url is empty. Please provide site url or site url list")
            self.log.info("Generating token for making SharePoint REST API calls")
            count = 0
            while count < 5:
                try:
                    self.ctx_auth.with_credentials(self.client_cred, environment=self.environment)
                    self.log.info("Token is generated successfully")
                    return True
                except Exception as token_exp:
                    count = count + 1
                    self.log.info(f"Token is not generated successfully. Error: {token_exp}")
                    self.cvoperations.wait_time(120, "Sleeping for 120 seconds before retrying")
            if count > 5:
                raise Exception(f"Exception in generating token for making SharePoint REST API calls : "
                                f"{self.ctx_auth.provider.error}")
        except Exception as exception:
            self.log.exception("Exception while generating token: %s", str(exception))
            raise exception

    def make_patch_request(self, full_url, request_body=None):
        """Makes SharePoint PATCH request using Python

            Args:

                full_url (str)             --  URL to make patch request

                request_body (dict)        --  body of the request

            Returns:

                response (dict)            --  response of the patch request

        """
        try:
            options = RequestOptions(full_url)
            options.set_header('Accept', 'application/json; odata=verbose')
            options.set_header('Content-Type', 'application/json')
            options.set_header('If-Match', '*')
            options.method = "PATCH"
            self.ctx_auth.authenticate_request(options)
            if request_body is None:
                request_body = {}
            response = requests.patch(url=full_url, data=json.dumps(request_body), headers=options.headers)
            return response
        except Exception as exception:
            self.log.exception("Exception while making patch request: %s", str(exception))
            raise exception

    def make_post_request(self, full_url, request_body=None, headers=None):
        """Makes SharePoint POST request using Python

            Args:

                full_url (str)             --  URL to make post request

                headers(dict)              -- additional headers to make post request

                request_body (dict)        --  body of the request

            Returns:

                response (dict)            --  response of the post request

        """
        try:
            options = RequestOptions(full_url)
            if headers:
                for k, v in headers.items():
                    options.set_header(k, v)
            else:
                options.set_header('Accept', 'application/json; odata=verbose')
                options.set_header('Content-Type', 'application/json')
            options.method = HttpMethod.Post
            self.ctx_auth.authenticate_request(options)
            if request_body is None:
                request_body = {}
            response = requests.post(url=full_url, data=json.dumps(request_body), headers=options.headers)
            return response
        except Exception as exception:
            self.log.exception("Exception while making post request: %s", str(exception))
            raise exception

    def make_get_request(self, full_url):
        """Makes SharePoint GET request using Python

            Args:
                    full_url (str)             --  URL to make get request

            Returns:
                    response (dict)            --  response of the get request

        """
        try:
            options = RequestOptions(full_url)
            options.set_header('Accept', 'application/json; odata=verbose')
            options.set_header('Content-Type', 'application/json')
            options.method = HttpMethod.Get
            self.ctx_auth.authenticate_request(options)
            response = requests.get(url=full_url, headers=options.headers)
            return response
        except Exception as exception:
            self.log.exception("Exception while making get request: %s", str(exception))
            raise exception

    def make_delete_request(self, full_url):
        """Makes SharePoint DELETE request using Python

             Args:
                    full_url (str)             --  URL to make delete request

            Returns:
                    response (dict)            --  response of the delete request

        """
        try:
            options = RequestOptions(full_url)
            options.set_header('If-Match', '*')
            options.method = HttpMethod.Delete
            self.ctx_auth.authenticate_request(options)
            response = requests.delete(url=full_url, headers=options.headers)
            return response
        except Exception as exception:
            self.log.exception("Exception while making delete request: %s", str(exception))
            raise exception

    def api_retry(func):
        @wraps(func)
        def inner(self, *args, **kwargs):
            retry_count = 0
            while True:
                try:
                    result = func(self, *args, **kwargs)
                    return result
                except Exception as exception:
                    self.log.error(f"Exception in {func.__name__}: {exception}")
                    retry_count = retry_count + 1
                    if retry_count > 3:
                        break
                    self.cvoperations.wait_time(20 * (retry_count ** 2))
        return inner

    @api_retry
    def call_specific_end_uri(self, full_url):
        """Makes REST API GET call for specified URI

             Args:
                    full_url (str)             --   URL to make delete request

            Returns:
                    response (dict)            --   response of the get request

        """
        try:
            attempt = 1
            response = ""
            while True:
                response = self.make_get_request(full_url)
                attempt += 1
                if response.status_code == 200 or response.status_code == 201:
                    return response.json().get("d", {})
                elif response.status_code == 429:
                    # fix 429 ERROR TOO MANY REQUESTS
                    if attempt > 3:
                        break
                    time.sleep(30*attempt)
                elif response.status_code >= 400:
                    break
            self.log.info(f"Error while calling {full_url} uri with status code {response.status_code} "
                          f"and reason {response.text}")
            return {}
        except Exception as exception:
            self.log.exception("Exception while calling specific end uri", str(exception))
            raise exception

    @api_retry
    def get_request_to_create_subsite(self, title, url_end, web_template=None):
        """Attempts to create a subsite in SharePoint Site

             Args:

                 title (str)               --   title of the subsite

                 url_end (str)             --   url end of the subsite

                 web_template (str)        --   web template of the subsite

            Returns:

                 request_body (dict)       --  body of the request

                                               request_body : {
                                                        'parameters': {
                                                        '__metadata':  {'type': 'SP.WebInfoCreationInformation'},
                                                        'Url': 'RestSubWeb1',
                                                        'Title': 'RestSubWeb1',
                                                        'Description': 'REST created web',
                                                        'Language': 1033,
                                                        'WebTemplate': 'STS',
                                                        'UseUniquePermissions': False}
                                                    }

            Raises:
                    Exception:
                        if response is not success
        """
        try:
            if not web_template:
                web_template = 'STS'
            self.log.info("Creating a sub site")
            request_body = \
                {
                    'parameters':
                        {
                            '__metadata':
                                {
                                    'type': 'SP.WebInfoCreationInformation'
                                },
                            'Url': url_end,
                            'Title': title,
                            'Description': 'It is a subsite',
                            'Language': 1033,
                            'WebTemplate': web_template,
                            'UseUniquePermissions': False
                        }
                }
            return request_body
        except Exception as exception:
            self.log.exception("Exception while getting request to create subsite: %s", str(exception))
            raise exception

    @api_retry
    def create_subsite(self, title, url_end, web_template=None):
        """Attempts to create a subsite in SharePoint Site

             Args:

                 title (str)               --   title of the subsite

                 url_end (str)             --   url end of the subsite

                 web_template (str)        --   web template of the subsite

            Returns:

                response (dict)             --  metadata of site created

            Raises:

                Exception:
                    if response is not success

        """
        try:
            request_body = self.get_request_to_create_subsite(title, url_end, web_template)
            subsite_end_url = request_body.get('parameters').get('Url')
            if self.get_site_properties(subsite_end_url):
                self.delete_subsite(subsite_end_url)
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['CREATE_SUBSITE'].format(
                self.site_url)
            self.log.info(f"Request Body : {request_body}")
            subsite_url = self.site_url + '/' + request_body.get('parameters').get('Url')
            self.log.info(f"Subsite URL : {subsite_url}")

            headers = {
                'Accept': 'application/json; odata=verbose',
                'Content-Type': 'application/json; odata=verbose'
            }
            response = self.make_post_request(full_url, request_body, headers)
            if response.status_code == 200 or response.status_code == 201:
                self.log.info(f"{subsite_url} site created successfully")
                return response.json().get("d", {})
            else:
                raise Exception(f"Failed to create site with status code {response.status_code} "
                                f"and reason {response.text}")
        except Exception as exception:
            self.log.exception("Exception while creating a subsite: %s", str(exception))
            raise exception

    @api_retry
    def get_site_properties(self, subsite_end_url=None, root_site=None, additional_uri=None):
        """Returns the properties of the SharePoint subsite

               Args:
                      subsite_end_url (str)    --   end part of site url if it is a subsite
                                                    Example - 'subsite' in https:test.sharepoint.com/sites/site/subsite

                      root_site (boolean)      --   if it is root site or not

                      additional_uri(str)      --   additional uri in API endpoint
                                                    Example - Title

              Returns:

                      properties_dict (dict)   --   dictionary of site properties

              Raises:

                      Exception:
                          if response is not success

          """
        try:
            if root_site:
                site_url = self.site_url
            else:
                site_url = self.site_url + '/' + subsite_end_url
            if additional_uri:
                full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['WEB_SPECIFIC_METADATA'].format(
                    site_url, additional_uri)
            else:
                full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['WEB'].format(
                    site_url)
            response = self.make_get_request(full_url)
            if response.status_code == 200 or response.status_code == 201:
                return response.json().get("d", {})
            elif response.status_code == 404:
                self.log.info(f"{full_url} site is not present in the SharePoint tenant")
                return {}
            else:
                raise Exception(f"Failed to get site properties with status code {response.status_code} "
                                f"and reason {response.text}")
        except Exception as exception:
            self.log.exception("Exception while getting properties of subsite: %s", str(exception))
            raise exception

    @api_retry
    def update_subsite_level_properties(self, prop_dict, subsite_end_url):
        """Updates properties of a SharePoint subsite

            Args:

                prop_dict (dict)         --  dictionary of properties
                                                     Example - {
                                                                "ServerRelativeUrl": "subsite",
                                                                 "Title": "Subsite Title"
                                                              }

                subsite_end_url(str)    --  end url of subsite

           Raises:

               Exception:
                   if response is not success

           """
        try:
            request_body = {
                "__metadata": {
                    "type": "SP.Web"
                }
            }
            request_body.update(prop_dict)
            subsite_url = self.site_url + '/' + subsite_end_url
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['WEB'].format(subsite_url)
            self.log.info(f"API URL : {full_url}")
            headers = {
                'Accept': 'application/json; odata=verbose',
                'Content-Type': 'application/json; odata=verbose',
                'X-HTTP-Method': 'MERGE'
            }
            response = self.make_post_request(full_url, request_body, headers)
            if response.status_code == 200 or response.status_code == 204:
                self.log.info(f"Site level properties of site {subsite_url} are updated successfully")
            else:
                raise Exception(f"Failed to update site level properties with status code {response.status_code} "
                                f"and reason {response.text}")
        except Exception as exception:
            self.log.exception("Exception while updating subsite level properties: %s", str(exception))
            raise exception

    @api_retry
    def create_subsites(self, subsite_list):
        """Creates subsites and returns metadata of them

            Args:

                subsite_list (list)           --    list of sites dictionary to create subsites

        """
        try:
            subsites_metadata = {}
            for site in subsite_list:
                title = site.get("Title")
                url_end = site.get("Url End")
                response = self.create_subsite(title, url_end)
                subsites_metadata[response.get('ServerRelativeUrl')] = {
                    'Url End': response.get('ServerRelativeUrl').split("/")[-1],
                    'Title': response.get('Title', ""),
                    'Operation': "ADDED"
                }
            return subsites_metadata
        except Exception as exception:
            self.log.exception("Exception while creating subsites: %s", str(exception))
            raise exception

    @api_retry
    def delete_subsites(self, subsite_end_url_list, additional_uri=None):
        """Delete subsites specified in site list

            Args:

                subsite_end_url_list (list)           --    list of end urls of subsites

                additional_uri(str)                   --    additional uri in API endpoint
                                                            Example - Title

        """
        try:
            for subsite_end_url in subsite_end_url_list:
                if self.get_site_properties(subsite_end_url=subsite_end_url, additional_uri=additional_uri):
                    self.log.info("Site is present in SharePoint site")
                    self.delete_subsite(subsite_end_url)
        except Exception as exception:
            self.log.exception("Exception while deleting subsites: %s", str(exception))
            raise exception

    @api_retry
    def delete_subsite(self, subsite_end_url):
        """Deletes a SharePoint subsite

           Args:

              subsite_end_url      :    end part of subsite url
                                        Example - 'subsite' in https:test.sharepoint.com/sites/site/subsite

          Returns:

              boolean              --  if the site is deleted successfully

          Raises:

              Exception:
                  if response is not success

          """
        try:
            subsite_url = self.site_url + '/' + subsite_end_url
            self.log.info(f"Subsite URL : {subsite_url}")
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['WEB'].format(
                subsite_url)
            response = self.make_delete_request(full_url)
            if response.status_code == 200 or response.status_code == 201:
                self.log.info(f"{subsite_url}\nsite deleted successfully")
            else:
                raise Exception(f"Failed to delete site with status code {response.status_code} "
                                f"and reason {response.text}")
        except Exception as exception:
            self.log.exception("Exception while deleting subsite: %s", str(exception))
            raise exception

    @api_retry
    def upload_sp_list_attachment(self, list_title, item_id, file_name):
        """Attempts to upload a attachment to list item

             Args:

                list_title (str)           --  title of the list where item resides

                item_id (str)               --  id of the item for the attachment

                file_name (str)             --  name of the file

            Returns:

                response (dict)             --  metadata of file created

            Raises:

                Exception:
                    if response is not success

        """
        try:
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['LIST_ITEM_ATTACHMENT'].format(
                self.site_url, list_title, item_id, file_name)
            options = RequestOptions(full_url)
            options.set_header('Accept', 'application/json; odata=verbose')
            options.set_header('Content-Type', 'application/octet-stream')
            options.method = HttpMethod.Post
            with open(file_name, 'rb') as outfile:
                self.ctx_auth.authenticate_request(options)
                response = requests.post(url=full_url, data=outfile, headers=options.headers)
                if response.status_code == 200 or response.status_code == 201:
                    return response.json().get("d", {})
                raise Exception(
                    f"Response is not success with status code {response.status_code} and unable to create file")
        except Exception as exception:
            self.log.exception("Exception while uploading a file to SharePoint Site: %s", str(exception))
            raise exception

    @api_retry
    def upload_sp_binary_file(self, folder_path, file_name):
        """Attempts to upload a binary file in SharePoint Site

             Args:

                folder_path (str)           --  path of the folder where file has to be uploaded

                file_name (str)             --  name of the file

            Returns:

                response (dict)             --  metadata of file created

            Raises:

                Exception:
                    if response is not success

        """
        try:
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['CREATE_FILE'].format(
                self.site_url, self.encode_url(folder_path), self.encode_url(file_name))
            options = RequestOptions(full_url)
            options.set_header('Accept', 'application/json; odata=verbose')
            options.set_header('Content-Type', 'application/octet-stream')
            options.method = HttpMethod.Post
            with open(file_name, 'rb') as outfile:
                self.ctx_auth.authenticate_request(options)
                response = requests.post(url=full_url, data=outfile, headers=options.headers)
                if response.status_code == 200 or response.status_code == 201:
                    return response.json().get("d", {})
                raise Exception(
                    f"Response is not success with status code {response.status_code} "
                    f"and reason {response.text} and unable to create file")
        except Exception as exception:
            self.log.exception("Exception while uploading a file to SharePoint Site: %s", str(exception))
            raise exception

    @api_retry
    def create_sp_folder(self, request_body):
        """Attempts to create a folder in SharePoint Site

            Args:

               request_body(dict)       --  body of the request
                                                 request_body : {
                                                    "ServerRelativeUrl": folder_url
                                                 }

            Returns:

                response(dict)          --  metadata of folder created

            Raises:

                Exception:
                    if response is not success

        """
        try:
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['CREATE_FOLDER'].format(self.site_url)
            response = self.make_post_request(full_url, request_body)
            if response.status_code == 200 or response.status_code == 201:
                return response.json().get("d", {})
            raise Exception(
                f"Response is not success with status code {response.status_code} "
                f"and reason {response.text} and unable to create folder")
        except Exception as exception:
            self.log.exception("Exception while creating folder in SharePoint Site: %s", str(exception))
            raise exception

    @api_retry
    def rename_sp_folder(self, folder_url, new_name):
        """Attempts to rename a folder in SharePoint Site

            Args:

                folder_url  (str)       --  Server Relative URL of the folder
                new_name    (str)       --  New name for the folder

            Raises:

                Exception:
                    if response is not success
        """
        try:
            ctx = ClientContext(self.site_url, self.ctx_auth)

            folder = ctx.web.get_folder_by_server_relative_url(folder_url)
            ctx.load(folder)
            ctx.execute_query()

            folder_item = folder.list_item_all_fields
            ctx.load(folder_item)
            ctx.execute_query()

            folder_item.set_property('FileLeafRef', new_name)
            folder_item.update()
            ctx.execute_query()
        except Exception as exception:
            self.log.exception("Exception while renaming folder in SharePoint Site: %s", str(exception))
            raise exception

    @api_retry
    def edit_sp_library_description(self, library_name, description):
        """Edits description of a library in SharePoint Site

            Args:

                library_name    (str)   :       Server Relative URL of the library
                description     (str)   :       New description for the library

            Raises:
                Exception:
                    if response is not success
        """
        try:
            ctx = ClientContext(self.site_url, self.ctx_auth)

            library = ctx.web.lists.get_by_title(library_name)
            library.set_property('Description', description)
            library.update()
            ctx.execute_query()
        except Exception as exception:
            self.log.exception("Exception while changing library description in SharePoint Site: %s", str(exception))
            raise exception

    @api_retry
    def edit_site_description(self, description):
        """Edits site description of the SharePoint site

            Args:

                description (str)   :       New description for the site

            Raises:
                Exception:
                    if response is not success
        """
        try:
            ctx = ClientContext(self.site_url, self.ctx_auth)

            ctx.web.set_property("Description", description)
            ctx.web.update()
            ctx.execute_query()
        except Exception as exception:
            self.log.exception("Exception while changing description in SharePoint Site: %s", str(exception))
            raise exception

    @api_retry
    def rename_sp_file(self, folder_path, file_name, updated_file_name):
        """Renames file in SharePoint Site

            Args:

                folder_path (str)           --  path of folder in which the file is present

                file_name (str)             --  name of the file

                updated_file_name (str)     --  updated name of the file

            Raises:

                Exception:
                    if response is not success

        """
        try:
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['RENAME_FILE'].format(
                self.site_url, folder_path, file_name, updated_file_name)
            response = self.make_post_request(full_url)
            if not (response.status_code == 200 or response.status_code == 201):
                raise Exception(
                    f"Response is not success with status code {response.status_code} "
                    f"and reason {response.text} and unable to update file properties")
        except Exception as exception:
            self.log.exception("Exception while updating file metadata in SharePoint Site: %s", str(exception))
            raise exception

    @api_retry
    def create_sp_list(self, request_body):
        """Attempts to create a list in SharePoint site

             Args:

                request_body (dict)       --  body of the request
                                                 request_body : {
                                                    "AllowContentTypes": True,
                                                    "BaseTemplate": 100,
                                                    "ContentTypesEnabled": True,
                                                    "Description": "This is a list created for test automation",
                                                    "Title": list_title
                                                 }

            Returns:

                response (dict)          --  metadata of list created

            Raises:

                Exception:
                    if response is not success

        """
        try:
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['LISTS'].format(self.site_url)
            response = self.make_post_request(full_url, request_body)
            if response.status_code == 200 or response.status_code == 201:
                return response.json().get("d", {})
            raise Exception(
                f"Response is not success with status code {response.status_code} "
                f"and reason {response.text} and unable to create list")
        except Exception as exception:
            self.log.exception("Exception while creating a list in SharePoint Site: %s", str(exception))
            raise exception

    @api_retry
    def create_list_custom_column(self, list_guid, request_body):
        """Attempts to create a column in the list

             Args:

                list_guid (str)           --  guid of the list

                request_body (dict)       --  body of the request
                                                 request_body : {
                                                    "AllowContentTypes": True,
                                                    "BaseTemplate": 100,
                                                    "ContentTypesEnabled": True,
                                                    "Description": "This is a list created for test automation",
                                                    "Title": list_title
                                                 }

            Returns:

                response (dict)          --  metadata of list created

            Raises:

                Exception:
                    if response is not success

        """
        try:
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['LIST_FIELDS'].format(self.site_url,
                                                                                                    list_guid)
            headers = {
                'Accept': 'application/json; odata=verbose',
                'Content-Type': 'application/json; odata=verbose'
            }
            response = self.make_post_request(full_url, request_body, headers)
            if response.status_code == 200 or response.status_code == 201:
                return response.json().get("d", {})
            raise Exception(
                f"Response is not success with status code {response.status_code} "
                f"and reason {response.text} and unable to create column in list")
        except Exception as exception:
            self.log.exception("Exception while creating a column for the list: %s", str(exception))
            raise exception

    @api_retry
    def get_sp_list_items_metadata(self, list_title=None, list_id=None, full_url=None):
        """Returns metadata of  list items in a list

              Args:

                  list_title (str)          --  title of the list

              Raises:

                  Exception:
                      if response is not success

        """
        try:
            if not full_url:
                if list_title:
                    full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['LIST_ITEMS'].format(
                        self.site_url, list_title)
                elif list_id:
                    full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['LIST_ITEMS_BY_LIST_ID'].format(
                        self.site_url, list_id)
                else:
                    self.log.exception("Either provide list title or id or full url to fetch list items metadata")
            response = self.make_get_request(full_url)
            if response.status_code == 200 or response.status_code == 201:
                response_json = response.json().get("d", {})
                if response_json.get('__next', ""):
                    return self.get_sp_list_items_metadata(list_title=list_title,
                                                           full_url=response_json.get('__next', "")) + \
                           response.json().get("d", {}).get("results", [])
                else:
                    return response_json.get("results", [])
            else:
                raise Exception(f"Response is not success with status code {response.status_code} "
                                f"and reason {response.text} and "
                                f"unable to fetch list items metadata")
        except Exception as exception:
            self.log.exception("Exception while retrieving metadata of list items: %s",
                               str(exception))
            raise exception

    @api_retry
    def create_sp_list_item(self, list_title, request_body):
        """Creates a list item in the specified list

            Args:

                list_title (str)          --  title of the list

                request_body (dict)       --  body of the request
                                                 request_body : {
                                                        "Title": item_title
                                                    }

            Returns:

                response (dict)          --  metadata of list item created

            Raises:

                Exception:
                    if response is not success

        """
        try:
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['LIST_ITEMS'].format(self.site_url,
                                                                                                   list_title)
            response = self.make_post_request(full_url, request_body)
            if response.status_code == 200 or response.status_code == 201:
                return response.json().get("d", {})
            raise Exception(
                f"Response is not success with status code {response.status_code} "
                f"and reason {response.text} and unable to create list item")
        except Exception as exception:
            self.log.exception("Exception while creating a list item in SharePoint Site: %s", str(exception))
            raise exception

    @api_retry
    def update_sp_list_item(self, list_title, request_body, list_item_id=None):
        """Updates list item of the specified list in SharePoint Site

            Args:

                list_title (str)          --  title of the list

                request_body (dict)       --  body of the request
                                                 request_body : {
                                                        "Title": item_title
                                                    }

                list_item_id (str)        --  id of list item

            Raises:

                Exception:
                    if response is not success
        """
        try:
            if not list_item_id:
                list_item_id = "1"
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['LIST_ITEM'].format(
                self.site_url, list_title, list_item_id)
            response = self.make_patch_request(full_url, request_body)
            if not (response.status_code == 200 or response.status_code == 204):
                raise Exception(f"Response is not success with status code {response.status_code} "
                                f"and reason {response.text}"
                                f"and unable to update list_item properties")
        except Exception as exception:
            self.log.exception("Exception while updating a list in SharePoint Site: %s", str(exception))
            raise exception

    @api_retry
    def get_sp_list_metadata(self, list_title):
        """Returns metadata of  list in SharePoint Site

              Args:

                  list_title (str)          --  title of the list

              Raises:

                  Exception:
                      if response is not success

        """
        try:
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['LIST'].format(
                self.site_url, list_title)
            response = self.make_get_request(full_url)
            if response.status_code == 200 or response.status_code == 201:
                return response.json().get("d", {})
            elif response.status_code == 404:
                return False
            raise Exception(f"Response is not success with status code {response.status_code} "
                            f"and reason {response.text} and "
                            f"unable to fetch list metadata")
        except Exception as exception:
            self.log.exception("Exception while retrieving metadata of a list in SharePoint Site: %s",
                               str(exception))
            raise exception

    @api_retry
    def get_sp_file_metadata(self, file_name, folder_path, additional_uri=None):
        """Returns the metadata of specified file

            Args:

                file_name (str)             --  name of the file

                folder_path (str)           --  path of folder in which the file is present

                additional_uri (str)        --  additional uri in API endpoint
                                                Example - Versions


            Returns:

                response (dict)             --  metadata of specified file

            Raises:

                Exception:
                    if response is not success
        """
        try:
            if additional_uri:
                full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['GET_SPECIFIC_FILE_METADATA'].format(
                    self.site_url, self.encode_url(folder_path), self.encode_url(file_name), additional_uri)
            else:
                full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['GET_FILE_METADATA'].format(
                    self.site_url, self.encode_url(folder_path), self.encode_url(file_name))
            response = self.make_get_request(full_url)
            if response.status_code == 200 or response.status_code == 201:
                return response.json().get("d", {})
            elif response.status_code == 404:
                return False
            raise Exception(f"Response is not success with status code {response.status_code} "
                            f"and reason {response.text} and"
                            f" unable to fetch file metadata")
        except Exception as exception:
            self.log.exception("Exception while retrieving metadata of a file in SharePoint Site: %s", str(exception))
            raise exception

    @api_retry
    def get_sp_folder_metadata(self, folder_path):
        """Returns the metadata of specified folder

            Args:

                folder_path (str)           --  path of folder in which the file is present

            Returns:

                response (dict)             --  metadata of specified folder

            Raises:

                Exception:
                    if response is not success
        """
        try:
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['FOLDER'].format(
                self.site_url, self.encode_url(folder_path))
            response = self.make_get_request(full_url)
            if response.status_code == 200 or response.status_code == 201:
                return response.json().get("d", {})
            elif response.status_code == 404:
                return False
            raise Exception(f"Response is not success with status code {response.status_code} "
                            f"and reason {response.text} and "
                            f"unable to fetch folder metadata")
        except Exception as exception:
            self.log.exception("Exception while retrieving metadata of a folder in SharePoint Site: %s",
                               str(exception))
            raise exception

    @api_retry
    def get_sp_list_item_metadata(self, list_title, list_item_id=None, additional_uri=None):
        """Returns the metadata of first list item of specified list

            Args:

                list_title(str)             --  title of the list

                list_item_id (str)          --  id of list item

                additional_uri(str)         --  additional uri in API endpoint
                                                Example - Versions

            Returns:

                response (dict)             --  metadata of first list item of specified list

            Raises:

                Exception:
                    if response is not success

        """
        try:
            if not list_item_id:
                list_item_id = "1"
            if additional_uri:
                full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['LIST_ITEM_SPECIFIC_METADATA'].format(
                    self.site_url, list_title, list_item_id, additional_uri)
            else:
                full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['LIST_ITEM'].format(
                    self.site_url, list_title, list_item_id)
            response = self.make_get_request(full_url)
            if response.status_code == 200 or response.status_code == 201:
                return response.json().get("d", {})
            elif response.status_code == 404:
                return False
            raise Exception(f"Response is not success with status code {response.status_code} "
                            f"and reason {response.text} and"
                            f" unable to fetch list item metadata")
        except Exception as exception:
            self.log.exception("Exception while retrieving metadata of a list item in SharePoint Site: %s",
                               str(exception))
            raise exception

    @api_retry
    def get_sp_list_item_title(self, list_title, list_item_id=None):
        """Returns the title of first list item of specified list in SharePoint Site

            Args:

                list_title(str)             --  title of the list

            Returns:

                title (str)                 --  title of first list item of the list (for default case)
                                                title of specified list item of the list

            Raises:

                Exception:
                    if response is not success

        """
        try:
            if not list_item_id:
                list_item_id = "1"
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['LIST_ITEM_TITLE'].format(
                self.site_url, list_title, list_item_id)
            response = self.make_get_request(full_url)
            if response.status_code == 200 or response.status_code == 201:
                return response.json().get("d", {}).get("Title", "")
            raise Exception(f"Response is not success with status code {response.status_code} "
                            f"and reason {response.text} and"
                            f" unable to fetch list item title")
        except Exception as exception:
            self.log.exception("Exception while retrieving title of first list item of a list in SharePoint Site: %s",
                               str(exception))
            raise exception

    @api_retry
    def delete_sp_file_or_folder(self, path):
        """Deletes the file or folder present at specified path in SharePoint Site

            Args:

                path (str)                  --  path of file/folder to be deleted

            Raises:

                Exception:
                    if response is not success

        """
        try:
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['FOLDER'].format(
                self.site_url, self.encode_url(path))
            response = self.make_delete_request(full_url)
            if not response.status_code == 200:
                raise Exception(f"Response is not success with status code {response.status_code} "
                                f"and reason {response.text} and"
                                f" unable to delete file/folder")
        except Exception as exception:
            self.log.exception("Exception while deleting file/folder in SharePoint Site: %s", str(exception))
            raise exception

    @api_retry
    def delete_sp_list(self, list_title):
        """Deletes the specified list from SharePoint Site

            Args:

                list_title (str)            --  title of the list to be deleted

            Raises:

                Exception:
                    if response is not success

        """
        try:
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['LIST'].format(
                self.site_url, list_title)
            response = self.make_delete_request(full_url)
            if not response.status_code == 200:
                raise Exception(f"Response is not success with status code {response.status_code} "
                                f"and reason {response.text} and"
                                f" unable to delete list")
        except Exception as exception:
            self.log.exception("Exception while deleting list in SharePoint Site: %s", str(exception))
            raise exception

    @api_retry
    def delete_sp_list_item(self, list_title, list_item_id):
        """Deletes the specified list item from SharePoint list

            Args:

                list_title (str)            --  title of the list to be deleted

                list_item_id(str)           --  id of the list item

            Raises:

                Exception:
                    if response is not success

        """
        try:
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['LIST_ITEM'].format(
                self.site_url, list_title, list_item_id)
            response = self.make_delete_request(full_url)
            if not response.status_code == 200:
                raise Exception(f"Response is not success with status code {response.status_code} "
                                f"and reason {response.text} and"
                                f"unable to delete list item")
        except Exception as exception:
            self.log.exception("Exception while deleting list item from the list in SharePoint Site: %s",
                               str(exception))
            raise exception

    def get_folder_with_default_lists_metadata(self, folder_name):
        """Returns the metadata of folders of defaults lists

            Args:

                folder_name (str)         --    name of the folder

            Raises:

                Exception:
                    if unable to get metadata for folder with default lists

        """
        try:
            folder_path = "/" + "/".join(self.site_url.split("/")[3:]) + "/" + folder_name
            response = self.get_sp_folder_metadata(folder_path)
            response["Title"] = response["Name"]
            return response
        except Exception as exception:
            self.log.exception("Exception while getting metadata for folder with default lists: %s",
                               str(exception))
            raise exception

    def process_folder(self, folder_obj, path_dict):
        """Scans the folder and stores folder and files metadata in path_dict

              Args:

                  folder_obj (object)          --    SharePoint Rest API folder object

                  path_dict (dict)             --    dictionary of folder paths

              Raises:

                  Exception:
                        if unable to scan folder

        """
        try:
            folder_id = folder_obj.get('UniqueId')
            full_url = "{0}/_api/web/GetFolderById('{1}')/Files".format(self.site_url, folder_id)
            files = self.call_specific_end_uri(full_url)
            if files:
                files = files.get('results')
                for file in files:
                    if int(file.get('Length')):
                        path = "\\MB\\" + self.site_url + "\\Contents\\" + "\\".join(
                            file.get('ServerRelativeUrl').split("/")[3:])
                        path_dict[path] = {
                            'ServerRelativeUrl': file.get('ServerRelativeUrl'),
                            'VersionLabel': float(file.get('UIVersionLabel')),
                            'Size': int(file.get('Length'))
                        }
                        file_id = file.get('UniqueId')
                        full_url = "{0}/_api/web/GetFileById('{1}')/Versions".format(self.site_url, file_id)
                        versions = self.call_specific_end_uri(full_url).get("results")
                        if not versions:
                            versions = []
                        path_dict[path]['VersionCount'] = len(versions) + 1
                    else:
                        self.log.info(f"{file.get('ServerRelativeUrl')} is a 0kb file. So ignoring it")
                full_url = "{0}/_api/web/GetFolderById('{1}')/Folders".format(self.site_url, folder_id)
                folders = self.call_specific_end_uri(full_url).get("results")
                return folders
            else:
                return {}
        except Exception as exception:
            self.log.exception("Exception while processing folder: %s", str(exception))
            raise exception

    def process_deep_folder(self, folder_obj, path_dict):
        """Scans a folder and its subfolders till end recursively and stores metadata in path_dict

               Args:

                   folder_obj (object)          --    SharePoint Rest API folder object

                   path_dict (dict)             --    dictionary of folder paths

               Raises:

                  Exception:
                        if unable to scan folder recursively

        """
        try:
            folders = self.process_folder(folder_obj, path_dict)
            if folders is None or len(folders) == 0:
                return
            else:
                for folder in folders:
                    if not folder.get('ServerRelativeUrl').split("/")[-1] == "Forms":
                        path = "\\MB\\" + self.site_url + "\\Contents\\" + "\\".join(
                            folder.get('ServerRelativeUrl').split("/")[3:])
                        path_dict[path] = {
                            'ServerRelativeUrl': folder.get('ServerRelativeUrl'),
                            'VersionLabel': float(folder.get('UIVersionLabel', "0.0")),
                            'VersionCount': 1
                        }
                        self.process_deep_folder(folder, path_dict)
        except Exception as exception:
            self.log.exception("Exception while processing deep folder: %s", str(exception))
            raise exception

    def get_all_lists_metadata(self):
        """Returns metadata of all lists present in SharePoint site

            Returns:

                response (dict)          --  metadata of lists

            Raises:

                Exception:
                    if response is not success

        """
        try:
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['LISTS'].format(self.site_url)
            response = self.make_get_request(full_url)
            if response.status_code == 200 or response.status_code == 201:
                return response.json().get("d", {}).get("results", [])
            raise Exception(
                f"Response is not success with status code {response.status_code} "
                f"and reason {response.text} and unable to get lists metadata")
        except Exception as exception:
            self.log.exception("Exception while getting lists metadata: %s", str(exception))
            raise exception

    def get_all_files(self, folder_name=None):
        """Returns all the files present in given path

            Args:

                folder_name (str)        --  name of the folder

            Returns:

                response (dict)          --  metadata of files

            Raises:

                Exception:
                    if response is not success

        """
        try:
            folder_path = "/" + "/".join(self.site_url.split("/")[3:]) + "/" + folder_name
            full_url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['FILES'].format(
                self.site_url, folder_path)
            response = self.make_get_request(full_url)
            if response.status_code == 200 or response.status_code == 201:
                return response.json().get("d", {}).get("results", [])
            raise Exception(
                f"Response is not success with status code {response.status_code} "
                f"and reason {response.text} and unable to get files metadata")
        except Exception as exception:
            self.log.exception("Exception while getting files metadata: %s", str(exception))
            raise exception

    def get_site_all_items_metadata(self):
        """Returns all the items_dict present in a site

            Returns:

                lists (dict)        --  metadata of lists and all its items

            Raises:

                Exception:
                    if unable to get all items for the site
        """
        try:
            self.log.info(f"Getting items from SharePoint Site for {self.site_url}")
            lists_metadata = self.get_all_lists_metadata()
            lists_metadata.insert(0, self.get_site_properties(root_site=True))
            for folder_name in sharepointconstants.HIDDEN_FOLDERS:
                folder_metadata = self.get_folder_with_default_lists_metadata(folder_name)
                lists_metadata.append(folder_metadata)
            lists = {}
            for list in lists_metadata:
                list_title = list.get("Title", "")
                self.log.info(f"Getting items of {list_title}")
                if list_title not in sharepointconstants.HIDDEN_FOLDERS:
                    lists[list_title] = {
                        "Title": list_title,
                        "BaseType": list.get("BaseType", 1),
                        "RootFolder": list.get("RootFolder", "").get('__deferred').get('uri'),
                    }
                    folder_obj = self.call_specific_end_uri(lists[list_title]["RootFolder"])
                else:
                    lists[list_title] = {
                        "Title": list_title,
                        "BaseType": 1
                    }
                    folder_obj = list
                url = folder_obj.get('ServerRelativeUrl').split("/")
                if "Lists" in url:
                    url = "\\".join(folder_obj.get('ServerRelativeUrl').split("/")[4:])
                else:
                    url = "\\".join(folder_obj.get('ServerRelativeUrl').split("/")[3:])
                if url:
                    lists[list_title]["Url"] = "\\MB\\" + self.site_url + "\\Contents\\" + url
                else:
                    lists[list_title]["Url"] = "\\MB\\" + self.site_url
                lists[list_title]["VersionLabel"] = 0.0
                lists[list_title]["VersionCount"] = 1
                if lists[list_title]["BaseType"] == 0 or lists[list_title]["BaseType"] > 3 or \
                        list.get("BaseTemplate", -1) == 109:
                    # Base Type = 0, 4, 5 => lists
                    # Base Template = 109 => Picture Library App
                    # For Picture Library App, though it is a library, the items are retrieved directly from list type
                    # as it has hidden folders which need not be processed
                    list_id = list.get('Id')
                    list_items = self.get_sp_list_items_metadata(list_id=list_id)
                    items_dict = {}
                    for item in list_items:
                        if list.get("BaseTemplate", -1) == 109:
                            file_obj = self.call_specific_end_uri(item["File"].get('__deferred').get('uri'))
                            path = "\\MB\\" + self.site_url + "\\Contents\\" + url + "\\" + file_obj.get("Name")
                            items_dict[path] = {
                                "Title": file_obj.get("Name"),
                                'ServerRelativeUrl': file_obj.get('ServerRelativeUrl'),
                                'VersionLabel': float(file_obj.get('UIVersionLabel', 0.0))
                            }
                        elif item.get('FileSystemObjectType') == 1:
                            path = "\\MB\\" + self.site_url + "\\Contents\\" + url + "\\" + item.get("Title")
                            items_dict[path] = {
                                "Title": item.get("Title"),
                                'ServerRelativeUrl': folder_obj.get('ServerRelativeUrl') + "\\" + item.get("Title"),
                                'VersionLabel': 0.0  # float(item.get('OData__UIVersionString', 0.0))
                            }
                        elif item.get('FileSystemObjectType') == 0 and not item.get('ParentItemID', None):
                            path = "\\MB\\" + self.site_url + "\\Contents\\" + url + "\\" + str(
                                item.get("Id")) + "_.000"
                            items_dict[path] = {
                                "Id": item.get("Id"),
                                "Title": item.get("Title"),
                                'ServerRelativeUrl': folder_obj.get('ServerRelativeUrl'),
                                'VersionLabel': float(item.get('OData__UIVersionString'))
                            }
                            versions = self.call_specific_end_uri(
                                item.get('Versions', "").get('__deferred').get('uri')).get(
                                "results")
                            if not versions:
                                versions = [1.0]
                            items_dict[path]['VersionCount'] = len(versions)
                    lists[list_title]["Paths"] = items_dict
                elif lists[list_title]["BaseType"] == 1:
                    path_dict = {}
                    if list.get("Url", "") == self.site_url:
                        self.process_folder(folder_obj, path_dict)
                    else:
                        self.process_deep_folder(folder_obj, path_dict)
                    lists[list_title]["Paths"] = path_dict
            return lists
        except Exception as exception:
            self.log.exception("Exception while getting all the items_dict in SharePoint Site: %s",
                               str(exception))
            raise exception

    def process_source_paths(self, lists_dict):
        """Processes items into the format of items required for validating items with index

               Args:

                   lists_dict (dict)         --      dict of lists with all its items

               Returns:

                   source_paths (dict)        --      dictionary of items with its metadata
                   Example:
                       {
                         "\\MB\\https://test.sharepoint.com/sites/TestAutomation3\\Contents\\Test Automation List": {
                               'VersionLabel': 0.0,
                               'VersionCount' : 1
                           },
                         "\\MB\\https://test.sharepoint.com/sites/TestAutomation3\\Contents\\Automation List\\1_.000":{
                               'VersionLabel': 3.0,
                               'VersionCount' : 3
                           }
                       }

               Raises:
                   Exception if the items are not processed properly

        """
        try:
            paths = {}
            for list, items in lists_dict.items():
                paths[items.get('Url')] = {
                    'VersionLabel': items.get('VersionLabel', 0.0),
                    'VersionCount': items.get('VersionCount', 1)
                }
                for item, item_dict in items.get('Paths').items():
                    paths[item] = {
                        'VersionLabel': item_dict.get('VersionLabel', 1.0),
                        'VersionCount': item_dict.get('VersionCount', 1)
                    }
            site_path = "\\MB\\" + self.site_url
            additional_paths = {}
            for additional_path in sharepointconstants.ALL_ITEMS_ADDITIONAL_PATHS:
                additional_paths[site_path + additional_path] = {
                    'VersionLabel': 0.0,
                    'VersionCount': 1
                }
            return {**paths, **additional_paths}
        except Exception as exception:
            self.log.exception("Exception while processing items from SharePoint Site: %s",
                               str(exception))
            raise exception

    def associate_multiple_sites(self):
        """Associates multiple sites in content
        """

        try:
            for site_url in self.site_url_list:
                self.site_url = site_url
                self.cvoperations.browse_for_sp_sites()
                self.cvoperations.associate_content_for_backup(self.office_365_plan[0][1])

        except Exception as e:
            self.log.error(f'Failed to associate multiple sites due to {str(e)}')

    @api_retry
    def get_file_count_in_sp_library(self, library_title):
        """Gets the count all the files in the document library from the site

            Args:

                library_title   (str)   :       Title of the library

            Returns:

                int                     :       Number of files in the library
        """
        ctx = ClientContext(self.site_url, self.ctx_auth)
        self.log.info(f"Getting count of all files in {library_title} library")
        try:
            list_obj = ctx.web.lists.get_by_title(library_title)
            ctx.load(list_obj)
            ctx.execute_query()
        except Exception as ie:
            self.log.error(f"Library {library_title} was probably deleted. Error: {ie}")
            return 0

        try:
            items = list_obj.root_folder.files
            ctx.load(items)
            ctx.execute_query()

            item_count = len(items)
            self.log.info(f"Number of files in {library_title} library: {item_count}")
            return item_count
        except Exception as e:
            self.log.error(f"Error while getting count of all files from library {library_title}: {e}")
            raise e

    def wait_for_library_to_populate(self, library_title, target_files_count, poll_interval=15, wait_time=600):
        """Waits for library to populate with the target files count

            Args:

                library_title       (str)   :       Title of the library

                target_files_count  (int)   :       Number of files to be expected in the library

                poll_interval       (int)   :       Number of seconds to wait before polling

                wait_time           (int)   :       Max wait time before timing out

        """
        start_time = int(time.time())
        while (int(time.time()) - start_time) < wait_time:
            self.log.info(f'Waiting for library to populate')
            self.cvoperations.wait_time(poll_interval)
            file_count = self.get_file_count_in_sp_library(library_title)
            if file_count >= target_files_count:
                return
        else:
            raise Exception(f'Timed out while waiting for {target_files_count} files to populate')

    def delete_files_in_sp_library(self, library_title):
        """Deletes all the files in the document library from the site

            Args:

                library_title   (str)   :       Title of the library

            Returns:

                int                     :       Number of files in the library before they were deleted
        """
        ctx = ClientContext(self.site_url, self.ctx_auth)
        self.log.info(f"Deleting files in {library_title} library")
        try:
            list_obj = ctx.web.lists.get_by_title(library_title)
            ctx.load(list_obj)
            ctx.execute_query()
        except Exception as list_exp:
            self.log.error(f"Library {library_title} was probably deleted. Error: {list_exp}")
            return 0

        try:
            items = list_obj.root_folder.files
            ctx.load(items)
            ctx.execute_query()

            file_count = len(items)

            self.delete_sp_library(library_title)
            self.create_sp_library(library_title)
            self.log.info(f"{file_count} files deleted from the library '{library_title}'")
            return file_count
        except Exception as e:
            self.log.error(f"Error while deleting files from library {library_title}: {e}")
            raise e

    @api_retry
    def delete_sp_library(self, library_title):
        """Deletes the document library from the site

            Args:

                library_title   (str)   :       Title of the library

        """
        ctx = ClientContext(self.site_url, self.ctx_auth)
        self.log.info(f"Deleting {library_title} library")
        try:
            list_obj = ctx.web.lists.get_by_title(library_title)
            ctx.load(list_obj)
            ctx.execute_query()
        except Exception as ie:
            self.log.error(f"Library {library_title} was probably deleted. Error: {ie}")
            return

        try:
            list_obj.delete_object()
            ctx.execute_query()

            self.log.info(f"Library '{library_title}' has been deleted successfully")
        except Exception as e:
            self.log.error(f"Error while deleting library {library_title}: {e}")
            raise e

    @staticmethod
    def get_request_to_create_sp_library(library_title):
        """Gets request body to create a document library in SharePoint

            Args:

                library_title   (str)   :       Title of the library

        """
        request_body = {
            "__metadata": {
                "type": "SP.List"
            },
            "AllowContentTypes": True,
            "BaseTemplate": 101,
            "ContentTypesEnabled": True,
            "Description": "",
            "Title": library_title
        }
        return request_body

    @api_retry
    def create_sp_library(self, library_title):
        """Creates a document library in the site

            Args:

                library_title   (str)   :       Title of the library

        """
        self.log.info(f"Creating {library_title} library")
        body = self.get_request_to_create_sp_library(library_title)
        headers = {
            'Accept': 'application/json; odata=verbose',
            'Content-Type': 'application/json; odata=verbose'
        }
        url = sharepointconstants.SHAREPOINT_REST_APIS_DICT_TEMPLATE['LISTS'].format(
            self.site_url)

        try:
            response = self.make_post_request(url, body, headers)
            if response.status_code in [200, 201]:
                self.log.info(f"Library '{library_title}' has been created successfully")
            else:
                raise Exception(f"Failed to create {library_title} library [{response.status_code}]: {response.text}")
        except Exception as e:
            self.log.error(f"Error while creating library {library_title}: {e}")
            raise e

    def create_sp_site_collection(self, site_url=None, is_group=False):
        """Creates a SharePoint site collection

            Args:

                site_url    (str)       :   URL of the site collection

                is_group    (bool)      :   Whether the site is a group connected site
        """
        try:
            if not site_url:
                site_url = self.site_url
            site_title = site_url.split("/")[4]
            self.log.info(f"Creating site collection {site_title}")

            if is_group:
                self.sp_api_object.create_teams_connected_site(site_title)
                return

            completed_process = subprocess.run(['powershell', '-File', sharepointconstants.CREATE_SITE_COLLECTION,
                                                self.tenant_url, self.user_username, self.user_password, site_url,
                                                site_title], text=True, timeout=300, check=True,
                                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)

            output = completed_process.stdout.strip()
            try:
                err_code = int(output)
            except Exception as e:
                self.log.error(f"Output from PowerShell: {output}")
                raise e

            if err_code == 1:
                raise Exception(f"Failed to create site collection {site_title}")

            if err_code == 2:
                raise Exception(f"Site collection {site_title} already exists")

            self.log.info(f"Site collection {site_title} created successfully")
        except subprocess.CalledProcessError as cpe:
            raise Exception(cpe)

    def delete_connected_group(self, site_url=None):
        """Deletes the Microsoft 365 group connected to a group site

            Args:

                site_url    (str)       :   Site collection URL
        """
        try:
            if not site_url:
                site_url = self.site_url

            group_name = site_url.split("/")[4]  # Generally the site alias is the group name
            self.log.info(f"Deleting group {group_name}")

            completed_process = subprocess.run(['powershell', '-File', sharepointconstants.DELETE_CONNECTED_GROUP,
                                                self.user_username, self.user_password, group_name], text=True,
                                               timeout=300, check=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

            output = int(completed_process.stdout.strip())
            try:
                err_code = int(output)
            except Exception as e:
                self.log.error(f"Output from PowerShell: {output}")
                raise e

            if err_code == 1:
                raise Exception(f"Failed to delete group {group_name}")

            if err_code == 2:
                raise Exception(f"Group {group_name} does not exist")

            self.log.info(f"Connected group {group_name} deleted successfully")
        except subprocess.CalledProcessError as cpe:
            raise Exception(cpe)

    def delete_sp_site_collection(self, site_url=None, is_group=False, deletion_type=None):
        """Deletes a SharePoint site collection

            Args:

                site_url        (str)       :   Site collection URL

                is_group        (bool)      :   Whether the site is a group site, in this case the deletion_type
                                                parameter is ignored

                deletion_type   (site)      :   If deletion_type is set to "full", the site is sent to bin and deleted
                                                If it is set to "bin", the site is deleted from the bin
        """
        site_title = site_url.split("/")[4]
        self.log.info(f"Deleting site collection {site_title}")

        if not deletion_type:
            deletion_type = "full"
        try:
            if not site_url:
                site_url = self.site_url

            if is_group:
                self.delete_connected_group(site_url)
                deletion_type = "bin"

            completed_process = subprocess.run(['powershell', '-File', sharepointconstants.DELETE_SITE_COLLECTION,
                                                self.tenant_url, self.user_username, self.user_password, site_url,
                                                deletion_type], text=True, timeout=300, check=True,
                                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)

            output = completed_process.stdout.strip()
            try:
                err_code = int(output)
            except Exception as e:
                self.log.error(f"Output from PowerShell: {output}")
                raise e

            if err_code == 1:
                raise Exception(f"Failed to delete site collection {site_title}")

            if err_code == 2:
                raise Exception(f"Site collection {site_title} does not exist")

            self.log.info(f"Site collection {site_title} deleted successfully")
        except subprocess.CalledProcessError as cpe:
            raise Exception(cpe)

    @staticmethod
    def encode_url(text):
        """Encodes URL for Sharepoint REST API

        Args:

            text    (str)       :   Text to be encoded

        Returns:

            str                 :   Encoded text
        """
        return urllib.parse.quote(text.replace("'", "''"), safe="/!~*'()")
