# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for Solr related operations

Solr:
    exch_obj()                              -- Return exchange mailbox object

    keyword_for_client_id()                 -- Return keyword for client id

    keyword_for_client_id                   -- Set the keyword ofr client id

    index_details()                         -- Return list of details of index servers

    base_url()                              -- Return base url for solr queries

    base_url                                -- Set the base url for Solr queries

    client_id()                             -- Returns the client id

    get_number_of_items_inbackup_job()      -- Get number of items in the provided job

    create_solr_query()                     -- Create solr search query based on inputs provided

    _is_job_played()                        -- Check if job has started playing

    _check_all_items_played_successfully()  -- Check if playback was successfully completed

    _is_content_indexed()                   -- Check if items for a client are content indexed

    get_result_of_custom_query()            -- Get the result of any query based on custom filters

    parse_json()                            -- Parse json output of a solr query

    get_count_from_json()                   -- Get the value of numFound in json response of solr

    get_all_field_names()                   -- Get all field names in solr

    create_url_and_get_response()           -- Get response of url

    _validate_retention()                   -- Helper method to validate retention

    call_retention_process()                -- Runs the CvExAutomatedtask Process on the proxy

    is_solr_standalone()                    -- check if instance of solr is standalone

    get_emails_from_index_server()          --  To query the number of emails from index server

    convert_to_bytes()                      --  Convert size to bytes based on the unit

    create_q_filed()                        --  Create solr query as per filter given in the json

SolrStandAlone:
    get_user_results_count()                -- Get count of all items in all usermbx cores

    get_user_sum_of_results_count()         -- Total Count of items in each user mailbox core

    get_journal_results_count()             -- Get count of all items in journal core

    set_standalone_base_url()               -- Set the base url for standalone solr queries

    is_job_played()                         -- Check if job has started playing

    check_all_items_played_successfully()   -- Check if playback was successfully completed

    is_content_indexed()                   -- Check if items for a client are content indexed

    get_items_for_users()                   -- Method to get documents for user guids

    validate_retention()                    -- Method to validate retention

SolrCloud:
    get_user_results_count()                -- Get count of all items in all backup set guid

    set_cloud_base_url()                    -- Set the base url for cloud solr queries

    is_job_played()                         -- Check if job has started playing

    check_all_items_played_successfully()   -- Check if playback was successfully completed

    is_content_indexed()                    -- Check if items for a client are content indexed

    get_items_for_users()                   -- Method to get documents for user guids

    validate_retention()                    -- Method to validate retention

CVSolr:

    set_cvsolr_base_url()                   -- Set the base url for cvsolr queries

    get_user_results_count()                -- Get count of all items in all backup set guid

    get_user_sum_of_results_count()         -- Total Count of items in each user mailbox core

    is_job_played()                         -- Check if job has started playing

    check_all_items_played_successfully()   -- Check if playback was successfully completed

	is_content_indexed()                    -- Check if items for a client are content indexed

	get_items_for_users()                   -- Method to get documents for user guids

    validate_retention()                    -- Method to validate retention


    Example of solr queries:
    To get all mailbox name where owner name is John Doe
    http://localhost:2000/solr/usermbx0/select?q=cvownerdisp:"John Doe"
    or
    http://localhost:2000/solr/usermbx0/select?q=cvownerdisp:"John Doe*" * works as LIKE in SQL

    To get only subject and ccsmtp fields where sender is "john@testexch.commvault.com" and tosmtp
    is "ritesh@testexch.commvault.com"
    http://localhost:2000/solr/usermbx0/select?q=fmsmtp:"john@testexch.commvault.com" AND
    tosmtp:"ritesh@testexch.commvault.com"&fl=conv,ccsmtp

    To get all jobs where job id is greater than 10000
    http://localhost:2000/solr/usermbx0/select?q=jid:[10000 TO *]

    To get all items where sender is not john
    http://localhost:2000/solr/usermbx0/select?q=-fmsmtp:"john@testexch.commvault.com"

    To get all items where subject is not empty
    http://localhost:2000/solr/usermbx0/select?q=conv:[* TO *]

    To get number of records where subject is empty
    http://localhost:2000/solr/usermbx0/select?q=-conv:[* TO *]&rows=0

    Example of methods:
    Create a solr_helper class object:
    solr = solr_helper(exchange_object)
    #Name of index server, client details are picked up from this.

    To check if a job has started playing:
    s.is_job_played(job_id)

    To check if playback of job was successful - This method will also return all the results
    based on attributes:
    s.check_all_items_played_successfully(job id, ['tosmtp','fmsmtp','contentid'])
    This would tell if playback was successful, and if it was, return the tosmtp, fmsmtp and
    contentid of each item.

    To get the top 100 rows with fields 'tosmtp', 'fmsmtp', 'contentid' where sender was
    john@testexch.commvault.com
    s.get_result_of_custom_query({'fmsmtp':'john@testexch.commvault.com'}, ['tosmtp','fmsmtp',
    'contentid'], {'start':0,'rows':100})
"""

import urllib.request
import time
import json
from datetime import datetime, timedelta, timezone
import requests
from AutomationUtils.machine import Machine
from Kubernetes.indexserver.constants import IS_COMMSERV_CLIENT_PROP
from .constants import SOLR_TYPE_DICT
from collections import defaultdict
import calendar
import re

class SolrHelper:
    """Base class to execute solr related operations """

    def __new__(cls, ex_object, searchURL=None, cvsolr=True):
        """Decides which instance object needs to be created
            Args:
                ex_object(obj)      -- Exchange Mailbox Object

                searchURL(str)      -- Search URL with collection names already added

                cvsolr (Bool)       -- To check if the index server is cvsolr
        """
        is_k8s = False
        try:
            ex_object.tc_object.log.info(
                "Getting Index Server details to determine type of Solr")
            query = (
                    "SELECT DISTINCT 'http://'+ CL.net_hostname + ':' + CAST (S.Portno "
                    "AS nvarchar(20)) as url, C.cloudType, S.ClientId, CL.name, cl2.name, "
                    "C.cloudId, CL.net_hostname, S.portNo, C.pseudoClientId, C.name FROM DM2Cloud"
                    " C (NOLOCK) JOIN DM2SearchServerCoreInfo S (NOLOCK) ON S.CloudId = C.cloudId"
                    " JOIN APP_Client CL (NOLOCK) ON S.ClientId = CL.id JOIN APP_Client CL2 "
                    "(NOLOCK) ON C.pseudoClientId = CL2.id WHERE S.CloudType IN (1,4,5) AND "
                    "CL2.name = '%s'" %
                    ex_object.index_server)
            ex_object.tc_object.log.info(f'query: {query}')
            ex_object.csdb.execute(query)
            results = ex_object.csdb.fetch_all_rows()

            # cluster check
            _cluster_query = f"select attrVal from APP_ClientProp (NOLOCK) where attrname like '{IS_COMMSERV_CLIENT_PROP}' and componentNameId = (select id from app_client (NOLOCK) where name = '{ex_object.index_server}')"
            ex_object.csdb.execute(_cluster_query)
            cluster_results = ex_object.csdb.fetch_all_rows()
            for cluster in cluster_results:
                if not cluster[0]:
                    break
                results[0][0] = cluster[0]
                ex_object.tc_object.log.info(
                    f'Cluster indexserver found. Replaced Url is : {results[0][0]}')
                is_k8s = True

            ind_details = []
            solr_instance = None
            for result in results:

                if not result:
                    raise Exception("No records found for the index server: %s"
                                    % ex_object.index_server)
                ind_detail = {
                    'server_url': result[0],
                    'server_type': int(
                        result[1]),
                    'index_client_id': int(
                        result[2]),
                    'index_client_name': result[3],
                    'engine_name': result[4],
                    'cloud_id': result[5],
                    'host_name': result[6],
                    'port': result[7],
                    'pseudo_id': result[8],
                    'pseudo_name': result[9],
                    'backupset_id': ex_object.cvoperations.backupset.backupset_id,
                    'backupset_guid': ex_object.cvoperations.backupset.guid,
                    'is_k8s': is_k8s}
                ind_details.append(ind_detail)
            if int(results[0][1]) == 1:
                if cvsolr:
                    ex_object.tc_object.log.info(
                        "Type is CVSolr. "
                        "Creating CVSolr instance")
                    solr_instance = super(SolrHelper, cls).__new__(CVSolr)
                else:
                    ex_object.tc_object.log.info(
                        "Type is SolrStandAlone. "
                        "Creating SolrStandalone instance")
                    solr_instance = super(SolrHelper, cls).__new__(SolrStandAlone)
            elif int(results[0][1]) == 5:
                ex_object.tc_object.log.info("Type is SolrCloud. "
                                             "Creating SolrCloud instance")
                solr_instance = super(SolrHelper, cls).__new__(SolrCloud)
            if not solr_instance:
                raise Exception("Index Server type couldn't be determined")
            solr_instance._index_details = ind_details
            return solr_instance
        except Exception as excp:
            raise Exception(
                "Exception while creating Solr Object. Reason: %s" %
                str(excp))

    def __init__(self, exchange_obj, searchURL=None, cvsolr=True):
        """Initializes the Solr object
            Args:
                exchange_obj(object)      -- instance of the exchange object
                searchURL(str)            -- Search URL with collection names already added
                cvsolr (Bool)       -- To check if the index server is cvsolr
        """
        self._exch_obj = exchange_obj
        self.log = self._exch_obj.tc_object.log
        self._base_url = searchURL
        self._keyword_for_client_id = None
        self.default_attrib_list = None
        self._cvsolr = cvsolr

    @property
    def exch_obj(self):
        """Return exchange mailbox object"""
        return self._exch_obj

    @property
    def keyword_for_client_id(self):
        """Return keyword for client id"""
        return self._keyword_for_client_id

    @keyword_for_client_id.setter
    def keyword_for_client_id(self, keyword_for_client_id):
        self._keyword_for_client_id = keyword_for_client_id

    @property
    def index_details(self):
        """Return list of details of index servers"""
        return self._index_details

    @property
    def base_url(self):
        """Return base url for solr queries"""
        return self._base_url

    @base_url.setter
    def base_url(self, base_url):
        """Set the base url for standalone or cloud"""
        self._base_url = base_url

    @property
    def client_id(self):
        """Returns id of client"""
        return int(self._exch_obj.cvoperations.client.client_id)

    def get_user_sum_of_results_count(self):
        """Method to get the total count of items in each core for user mailbox
            Returns:
                Total Count of items in each user mailbox core
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def check_all_items_played_successfully(self, job_id, attr_list=None):
        """Method to get the total count of items in each core for user mailbox
            Returns:
                Total Count of items in each user mailbox core
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_number_of_items_inbackup_job(self, job_id):
        """Method to set the solr search query
            Args:
                job_id(int)        -- Job id for which number of items is required

            Returns:
                Number of items in the provided job id
        """
        try:
            self.log.info(
                "Getting number of items in job %s from database" %
                job_id)
            query_string = "select totalNumOfFiles from JMBkpStats Where jobId=%s" % job_id
            self.exch_obj.csdb.execute(query_string)
            result = self.exch_obj.csdb.fetch_one_row()
            self.log.info(
                "Number of items in job %s is: %s" %
                (job_id, result[0]))
            return int(result[0])
        except Exception as excp:
            self.log.exception(
                "Error in getting job details from database. %s" %
                str(excp))
            raise excp

    def create_solr_query(
            self,
            select_dict=None,
            attr_list=None,
            op_params=None):
        """Method to create the solr query based on the params
            Args:
                select_dict(dictionary)     --  Dictionary containing search criteria and value
                                                Acts as 'q' field in solr query

                attr_list(set)            --  Column names to be returned in results.
                                                Acts as 'fl' in solr query

                op_params(dictionary)       --  Other params and values for solr query
                                                (Ex: start, rows)

            Returns:
                The solr url based on params
        """
        try:
            self.log.info("Creating solr URL")
            search_query = f'q='
            simple_search = 0
            if select_dict:
                for key, value in select_dict.items():
                    if isinstance(key, tuple):
                        if isinstance(value, list):
                            search_query += f'({key[0]}:{str(value[0])}'
                            for val in value[1:]:
                                search_query += f' OR {key[0]}:{str(val)}'
                        else:
                            search_query += f'({key[0]}:{value}'
                        for key_val in key[1:]:
                            if isinstance(value, list):
                                search_query += f' OR {key_val}:{str(value[0])}'
                                for val in value[1:]:
                                    search_query += f' OR {key_val}:{str(val)}'
                            else:
                                search_query += f' OR {key_val}:{value}'
                        search_query += ') AND '
                    elif isinstance(value, list):
                        search_query += f'({key}:{str(value[0])}'
                        for val in value[1:]:
                            search_query += f' OR {key}:{str(val)}'
                        search_query += ") AND "
                    elif key == "keyword":
                        search_query += "(" + value + ")"
                        simple_search = 1
                        break
                    else:
                        search_query = search_query + \
                                       f'{key}:{str(value)} AND '

            if simple_search == 0:
                search_query = search_query[:-5]
            self.log.info("Search query: %s" % search_query)
            field_query = ""
            if attr_list:
                field_query = "&fl="
                for item in attr_list:
                    field_query += f'{str(item)},'
                field_query = field_query[:-1]
                self.log.info("Field query formed: %s" % field_query)
            ex_query = ""
            if not op_params:
                op_params = {'wt': "json"}
            else:
                op_params['wt'] = "json"
            for key, value in op_params.items():
                if value is None:
                    ex_query += f'&{key}'
                else:
                    ex_query += f'&{key}={str(value)}'
            self.log.info("Optional parameters are: %s" % ex_query)

            final_url = f'{self.base_url}{search_query}{field_query}{ex_query}'
            return final_url

        except Exception as excp:
            self.log.exception(
                "Exception while creating solr query: %s" %
                str(excp))
            raise excp

    def _is_job_played(self, select_dict):
        """Method to check if job has started playing or not. Should be called from SolrCloud or
        SolrStandAlone class
            Args:
                select_dict(dict)  -- Dictionary of keyword and job_id

            Raises:
                Exception if job is not played after 5 mins
        """
        try:
            solr_url = self.create_solr_query(
                select_dict=select_dict, op_params={"rows": 0})
            self.log.info(
                "URL formed from the details provided is: %s" %
                solr_url)
            response = requests.get(url=solr_url)
            new_cnt = self.get_count_from_json(response.content)
            tot_time = 0
            old_cnt = -1
            while tot_time < 10:
                tot_time += 1
                if old_cnt == new_cnt and new_cnt > 0:
                    return
                self.log.info(
                    "Job has started playing. Waiting 30 secs to check again")
                old_cnt = new_cnt
                time.sleep(30)
                response = requests.get(url=solr_url)
                self.check_if_error_in_response(response)
                new_cnt = self.get_count_from_json(response.content)
            if new_cnt == 0:
                raise Exception("Job is not played")
            self.log.info("Job has started playing: %s" % solr_url)
        except Exception as excp:
            self.log.exception(
                "Exception while checking if job was played. %s" %
                str(excp))
            raise excp

    def _check_all_items_played_successfully(
            self, select_dict, job_id, attr_list=None):
        """Method to check if all items in a job were played successfully. Should be called via
        check_all_items_played_successfully method in SolrStandalone or SolrCloud
            Args:
                select_dict(dict)   -- Dictionary of backup job keyword and datatype

                job_id(int)         -- Job id

                attr_list(set)     -- Attribute list to return, Will return the
                    Default(None)      default_attrib_list by default(Works as fl in Solr)

            Returns:
                Details about all the items in that job if true

            Raises:
                Exception if the job was not played after 10 mins
        """
        try:

            start = 0
            num_rows = 100
            solr_url = self.create_solr_query(
                select_dict=select_dict, op_params={"rows": 0})
            self.log.info(
                "URL formed from the details provided is: %s" %
                solr_url)
            response = requests.get(url=solr_url)
            self.check_if_error_in_response(response)
            result = {}
            new_results = self.get_count_from_json(response.content)
            old_results = -1
            total_results = self.get_number_of_items_inbackup_job(job_id)
            tot_time = 0
            while total_results - new_results > 0 and tot_time < 10:
                tot_time += 1
                self.log.info(
                    "Total number of files played(%d) is not equal to total items in "
                    "job(%d). Waiting for 1 minute and retrying" %
                    (new_results, total_results))
                time.sleep(90)
                if new_results != old_results:
                    old_results = new_results
                    response = requests.get(url=solr_url)
                    self.check_if_error_in_response(response)
                    new_results = self.get_count_from_json(response.content)
                else:
                    time.sleep(90)
                    tot_time += 1
                    response = requests.get(url=solr_url)
                    self.check_if_error_in_response(response)
                    new_results = self.get_count_from_json(response.content)
                    if new_results == old_results:
                        raise Exception("Job is not played")
            self.log.info(
                "---Job %s was successfully played. Now generating results---" %
                job_id)
            while total_results - start > 0:
                response = self.create_url_and_get_response(
                    select_dict=select_dict, op_params={
                        "start": start, "rows": num_rows})
                self.check_if_error_in_response(response)
                result['total_records'] = total_results
                self.parse_json(response.content, result, attr_list=attr_list)
                start += num_rows
            self.log.info(
                "---------------Results for job %s generated succesfully-------------" %
                job_id)
            return result

        except Exception as excp:
            self.log.exception(
                "Exception while checking if job was successfully played. %s" %
                str(excp))
            raise excp

    def _is_content_indexed(
            self,
            select_dict,
            number_of_items,
            preview=False,
            preview_path=None):
        """Method to check if items for the client are content indexed. Should be called via
        is_content_indexed method in SolrStandalone or SolrCloud
             Args:
                select_dict(dict)      -- Dictionary to check if ci was successful

                number_of_items(int)   -- Number of items applicable for CI job

                preview(boolean)       -- If job was done with preview option selected

                preview_path(str)      -- The preview path

             Raises:
                Exception if the items are not content indexed
        """
        try:
            if preview_path:
                solr_url = self.create_solr_query(
                    select_dict, None, {'rows': number_of_items})
            else:
                solr_url = self.create_solr_query(
                    select_dict, None, {'rows': 0})
            self.log.info("Solr url formed: %s" % solr_url)
            response = requests.get(url=solr_url)
            self.check_if_error_in_response(response)
            items_in_solr = 0
            if preview and 'docs' in json.loads(response.content)['response']:
                response = json.loads(response.content)['response']
                for doc in response['docs']:
                    if 'previewpath' in doc or 'PreviewPath' in doc:
                        items_in_solr += 1
            else:
                items_in_solr = self.get_count_from_json(response.content)
            self.log.info("Total items Content Indexed: %d" % items_in_solr)
            return int(items_in_solr) == int(number_of_items)
        except Exception as excp:
            raise Exception(
                "Error in method _is_content_indexed. Reason: %s" %
                str(excp))

    def get_result_of_custom_query(
            self,
            select_dict=None,
            attr_list=None,
            op_params=None):
        """Method to get results of any query.
            Args:
                select_dict(dictionary)         --  Dictionary containing search criteria and
                                                    value. Acts as 'q' field in solr query

                attr_list(set)                  --  Criteria to filter results. Acts as 'fl' in
                                                    solr query

                op_params(dictionary)           --  Other params and values for solr query. Do not
                                                    mention 'wt' param as it is always json
                                                    (Ex: start, rows)
            Returns:
                result dictionary containing properties as read from solr
        """
        try:
            if not op_params:
                op_params = {}
            op_params['wt'] = "json"
            response = self.create_url_and_get_response(
                select_dict, attr_list, op_params)
            self.check_if_error_in_response(response)
            result = {}
            results = json.loads(response.content)
            tot_rec = int(results['response']['numFound'])
            rows = 100
            start = 0
            result['total_records'] = tot_rec
            if "start" in op_params:
                start = op_params['start']
                tot_rec -= start
            if "rows" in op_params:
                if op_params['rows'] > tot_rec:
                    op_params['rows'] = tot_rec
                tot_rec = op_params['rows']
            if "rows" not in op_params or op_params['rows'] > rows:
                op_params['rows'] = rows
            self.log.info("Generating Results for the above query")
            while tot_rec > 0:
                op_params['start'] = start
                if rows > tot_rec:
                    op_params['rows'] = tot_rec
                response = self.create_url_and_get_response(
                    select_dict, attr_list, op_params)
                self.check_if_error_in_response(response)
                self.parse_json(response.content, result, attr_list)
                tot_rec -= rows
                start += rows
            if 'facet_counts' in results:
                result['facet_counts'] = results['facet_counts']
            return result

        except Exception as excp:
            self.log.exception(
                "Exception while getting result of custom query. %s" %
                str(excp))
            raise excp

    def check_if_error_in_response(self, response):
        """Method to check if response has error
            Args:
                response(obj)         --  Response Object

            Raises:
                Exception if response was error
        """
        try:
            if response.status_code != 200:
                raise Exception(
                    "Error in calling solr URL. Reason %s" %
                    response.reason)
            response = json.loads(response.content)
            if "error" in response:
                raise Exception(
                    "Error in the solr URL. Reason %s " %
                    response["error"]["msg"])
        except Exception as excp:
            self.log.exception(excp)
            raise excp

    def parse_json(self, json_string, result_obj, attr_list=None):
        """Method to parse json output of a solr query
            Args:
                json_string(string)         -- json result of solr in the form of string

                result_obj(dictionary)      -- Dictionary to hold the result

                attr_list(set)              -- Attribute list to return(Works as fl in solr)
                    Default(None)

            Returns:
                Result dictionary

            Raises:
                Exception if error in parsing json
        """
        try:
            self.log.info("Started parsing the response json")
            key = "result"
            if not attr_list:
                attr_list = self.default_attrib_list
            results = json.loads(json_string)
            results = results['response']
            if key not in result_obj:
                result_obj[key] = {}
            ind = 0
            if 'docs' not in results:
                result_obj[key] = results
                return result_obj
            for doc in results['docs']:
                content_id = ind
                ind += 1
                if 'contentid' in doc:
                    content_id = doc['contentid']
                result_list = {}
                for k, value in doc.items():
                    if k in attr_list:
                        result_list[k] = value
                    if k in ('cvownerdisp', 'OwnerName'):
                        str_val = value.split(" (", 1)
                        result_list['cvownerDisplayName'] = str_val[0]
                        result_list['cvownerSMTP'] = str_val[1][:-1]
                for item in attr_list:
                    if item not in result_list:
                        result_list[item] = None
                result_obj[key][content_id] = result_list
            return result_obj
        except Exception as excp:
            self.log.exception(
                "Exception in method 'parse_json' while parsing json. %s" %
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

    def get_all_field_names(self):
        """Helper Method to get all the column names in solr

            Returns:
                Dictionary of column names as key and their schema as value
        """
        val = self.base_url.split("select?", 1)
        solr_url = f'{val[0]}admin/luke?numTerms=0'
        if not val[1]:
            solr_url = f'{solr_url}&{val[1][:-1]}'
        response = requests.get(url=solr_url)
        self.check_if_error_in_response(response)
        results = json.loads(response.content)
        results = results['fields']
        result = {}
        for key, value in results.items():
            result[key] = value
        return result

    def create_url_and_get_response(
            self,
            select_dict=None,
            attr_list=None,
            op_params=None):
        """Helper method to get results from a url
            Args:
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
            solr_url = self.create_solr_query(
                select_dict, attr_list, op_params)
            self.log.info(
                "URL formed from the details provided is: %s" %
                solr_url)
            return requests.get(url=solr_url)
        except Exception as excp:
            raise excp

    def _validate_retention(self, number_of_days, keyword, select_dict):
        """Helper method to validate retention
            Args:
                number_of_days(int)             --  Number of days in retention period

                keyword(list)                   --  ["mtm", "datatype"] or ["ReceivedTime",
                                                    "DocumentType"] based on Solr type

                select_dict(dictionary)         --  Dictionary containing search criteria and
                                                    value.

            Raises:
                Exception if retention is not validated
        """
        try:
            valid_time = datetime.now(
                tz=timezone.utc) - timedelta(days=number_of_days + 1)
            mtm_valid = (
                f'{valid_time.year}-{valid_time.month}-{valid_time.day}T{valid_time.hour}'
                f':{valid_time.minute}:{valid_time.second}Z')
            s_dict = {self.keyword_for_client_id: self.client_id,
                      keyword[0]: f'[* TO {mtm_valid}]', keyword[1]: 2}
            response = self.create_url_and_get_response(
                s_dict, None, {"rows": 0})
            count = self.get_count_from_json(response.content)
            self.log.info(
                "Total number of items not eligible for retention: %d" %
                count)
            self.call_retention_process()
            time.sleep(600)
            response = self.create_url_and_get_response(
                select_dict, None, {"rows": 0})
            json_num = self.get_count_from_json(response.content)
            self.log.info("Total number of items not retained: %d" % json_num)
            if count != json_num:
                raise Exception("Retention not satisfied")
            self.log.info("Retention Validated")

        except Exception as excp:
            self.log.exception("Exception while validating retention")
            raise excp

    def call_retention_process(self):
        """Runs the CvExAutomatedtask Process on the proxy"""
        try:
            machine = Machine(self.exch_obj.proxies[0], self.exch_obj.commcell)
            self.log.info(
                "Running CvExAutomatedtask process on %s" %
                self.exch_obj.proxies[0])
            command = (
                f'CvExAutomatedtask.exe -vm {machine.instance} -SubmitRet -IS '
                f'"{self.client_id}"')
            machine.execute_command(command)
            time.sleep(120)
        except Exception as excp:
            raise excp

    def is_solr_standalone(self):
        """Method to check if current instance is of SolrCloud or StandAlone
            Returns:
                True if instance of SolrStandAlone

        """
        return isinstance(self, SolrStandAlone)

    def get_emails_from_index_server(self,solr_query,mssql,client_id,search_obj):
        """To query the number of emails from index server

            Args:
                solr_query(dictionary)     --  Dictionary containing search criteria and value
                                                Acts as 'q' field in solr query
                mssql(obj)                 --   instance of mssql object
                client_id(int)             --   client id
                search_obj                 --   instance of solr search object
        """
        try:
            email_count = 0
            app_id_list = search_obj.get_exchange_app_id(client_id=client_id)
            app_id = '(' + ','.join(app_id_list) + ')'
            details_list, distinct_cloud_ids = search_obj.get_ci_server_url(
                mssql, app_id)
            cloud_name = dict()
            for cloud_id in distinct_cloud_ids:
                cloud_name[cloud_id] = search_obj.get_index_server_name(
                    cloud_id)
            for item in details_list:
                self._exch_obj.index_server = cloud_name[item['cloudId']]
                self._base_url = item['ciServer'] + '/select?'
                if (item['serverType'] == '1' and
                        (item['schemaVersion'] == '0' or item['schemaVersion'] == '1')):
                    solr_results = self.create_url_and_get_response(
                        solr_query)
                    email_count+= self.get_count_from_json(
                        solr_results.content)
                elif item['serverType'] == '5' or (item['serverType'] == '1' and item['schemaVersion'] == '2'):
                    solr_results = self.create_url_and_get_response(solr_query)
                    email_count += self.get_count_from_json(
                        solr_results.content)
            self.log.info("Solr Query returns %s items", email_count)
            return email_count
        except Exception as excp:
            self.log.exception("Error querying the index server")

    def __convert_to_bytes(self,size, unit):
        """
        Convert size to bytes based on the unit.
            Args:
                size (str): Size of the attachment in mail
                unit (str): Unit of the size (KB, MB, GB)
        """
        size=int(size)
        if unit == 'KB':
            return size * 1024
        elif unit == 'MB':
            return size * 1024 * 1024
        elif unit == 'GB':
            return size * 1024 * 1024 * 1024

    def create_solr_q_filed_parameter(self,filter_value):
        """
        Create solr query as per filter given in the json
            Args:
                filter_value(dictionary)     --  Dictionary containing search criteria and value
        """
        new_solr_query = defaultdict(str)
        for keys in filter_value:
            if keys in ['From','To']:
                new_solr_query[keys+'SMTP']=filter_value[keys]

            elif keys in ['Folder','Has Attachment']:
                keys_id = re.sub(r"\s", "", keys)
                new_solr_query[keys_id] = filter_value[keys]

            elif keys =='Subject':
                new_solr_query[keys]=f"/.*{filter_value[keys]}/"

            elif keys =="Mailbox":
                new_solr_query["DocumentType"]='2'
                user_names=filter_value[keys].split(";")
                new_solr_query["OwnerName"]=f"({' OR '.join([f'/{user}.*/' for user in user_names])})"

            elif keys =='Mail Size':
                size_in_bytes = self.__convert_to_bytes(size=filter_value[keys][1], unit=filter_value[keys][2])
                if filter_value[keys][0]=="Greater than":
                    size_in_bytes+=1
                    new_solr_query['Size'] = f"[{size_in_bytes} TO *]"
                if filter_value[keys][0] == "Less than":
                    size_in_bytes-=1
                    new_solr_query['Size'] = f"[* TO {size_in_bytes}]"

            elif keys =='Received Time':
                now = datetime.utcnow()
                keys_id = re.sub(r"\s", "", keys)
                if filter_value[keys][0]=="Today":
                    new_solr_query[keys_id]=f"[{now.strftime('%Y-%m-%d')}T00:00:00Z TO NOW]"

                elif filter_value[keys][0]=="Yesterday":
                    yesterday=(now-timedelta(days=1))
                    new_solr_query[keys_id]=f"[{yesterday.strftime('%Y-%m-%d')}T00:00:00Z TO {yesterday.strftime('%Y-%m-%d')}T24:00:00Z]"

                elif filter_value[keys][0]=="This Week":
                    this_week=now-timedelta(days=now.weekday())
                    new_solr_query[keys_id] = f"[{this_week.strftime('%Y-%m-%d')}T00:00:00Z TO NOW]"

                elif filter_value[keys][0]=="This Month":
                    this_month=now.replace(day=1)
                    new_solr_query[keys_id] = f"[{this_month.strftime('%Y-%m-%d')}T00:00:00Z TO NOW]"

                elif filter_value[keys][0]=="This Year":
                    this_year=now.replace(month=1, day=1)
                    new_solr_query[keys_id] = f"[{this_year.strftime('%Y-%m-%d')}T00:00:00Z TO NOW]"

                elif filter_value[keys][0]=="Last Week":
                    current_week_start=now-timedelta(days=now.weekday())
                    last_week_start=current_week_start-timedelta(days=7)
                    last_week_end=last_week_start+timedelta(days=6)
                    new_solr_query[keys_id]=f"[{last_week_start.strftime('%Y-%m-%d')}T00:00:00Z TO {last_week_end.strftime('%Y-%m-%d')}T24:00:00Z]"

                elif filter_value[keys][0]=="Last Month":
                    if now.month == 1:
                        last_month_start=datetime(now.year - 1, 12, 1)
                    else:
                        last_month_start=datetime(now.year, now.month - 1, 1)
                    next_month=last_month_start.replace(day=28)+timedelta(days=4)
                    last_month_end=next_month - timedelta(days=next_month.day)
                    new_solr_query[keys_id] = f"[{last_month_start.strftime('%Y-%m-%d')}T00:00:00Z TO {last_month_end.strftime('%Y-%m-%d')}T24:00:00Z]"

                elif filter_value[keys][0]=="Last Year":
                    last_year_start=datetime(now.year - 1, 1, 1)
                    last_year_end=datetime(now.year - 1, 12, 31)
                    new_solr_query[keys_id] = f"[{last_year_start.strftime('%Y-%m-%d')}T00:00:00Z TO {last_year_end.strftime('%Y-%m-%d')}T24:00:00Z]"

                elif filter_value[keys][0]=="Date Range":
                    start_date_year=filter_value[keys][1]["year"]
                    month_name=filter_value[keys][1]["month"].capitalize()
                    start_date_month=list(calendar.month_name).index(month_name)
                    start_date_day=int(filter_value[keys][1]["day"])

                    end_date_year=filter_value[keys][2]["year"]
                    month_name = filter_value[keys][2]["month"].capitalize()
                    end_date_month = list(calendar.month_name).index(month_name)
                    end_date_day=int(filter_value[keys][2]["day"])
                    new_solr_query[keys_id] = f"[{start_date_year}:{start_date_month:02}:{start_date_day:02}T00:00:00Z TO {end_date_year}:{end_date_month:02}:{end_date_day:02}T24:00:00Z]"

        if "Contains" in list(filter_value.keys()):
            new_solr_query["IsVisible"] = "True"
            new_solr_query["DocumentType"] = '2'
            new_solr_query["-AchiveFileId"] = "0"
            new_solr_query["keyword"] = filter_value["Contains"]

        return new_solr_query

class SolrStandAlone(SolrHelper):
    """Class to execute solr standalone related operations """

    def __init__(self, ex_object, searchURL=None, cvsolr=False):
        """Initializes the Solr StandAlone object
            Args:
                ex_object(object)      -- instance of the exchange object
         """
        super(SolrStandAlone, self).__init__(ex_object)
        self.log.info(
            "-------------- Solr Stand Alone Constructor -------------")
        self.default_attrib_list = {
            'msgclass',
            'ccsmtp',
            'fmsmtp',
            'tosmtp',
            'conv',
            'hasattach',
            'hasAnyAttach',
            'folder',
            'entity_ccn',
            'entity_ssn',
            'CAState',
            'cijid',
            'cistatus',
            'afid',
            'afof'}
        self.get_user_results_count()
        self.get_journal_result_count()
        if searchURL is None:
            self.set_standlone_base_url()
        else:
            self.base_url = searchURL
        self.keyword_for_client_id = "clid"
        self.type = SOLR_TYPE_DICT[self.index_details[0]['server_type']]
        self.log.info(
            "-------------- Solr Stand Alone Constructor Ends-------------")

    def get_user_results_count(self):
        """Method to get the count of items in each core for user mailbox
            Returns:
                Count of items in each user mailbox core
        """
        try:
            result = {}
            self.log.info("Getting count of all results in each core")
            self.base_url = f'{self.index_details[0]["server_url"]}/solr/'
            for i in range(8):
                url = f'{self.base_url}usermbx{i}/select?q=*:*&rows=0&wt=json'
                response = requests.get(url=url)
                self.check_if_error_in_response(response)
                result[f'core{str(i)}'] = self.get_count_from_json(
                    response.content)
            self.log.info(result)
            return result
        except Exception as excp:
            self.log.exception("Exception in method 'get_user_results_count'")
            raise excp

    def get_user_sum_of_results_count(self):
        """Method to get the total count of items in each core for user mailbox
            Returns:
                Total Count of items in each user mailbox core
        """
        try:
            total_count = 0
            cores_count = self.get_user_results_count()
            for i in range(len(cores_count)):
                total_count = total_count + cores_count['core' + str(i)]
            self.log.info("Total Number of items got archived: %s", total_count)
            return total_count

        except Exception as excp:
            self.log.exception("Exception in method 'get_user_sum_of_results_count'")
            raise excp

    def get_journal_result_count(self, result=None):
        """Method to get the count of items in each core for journal mailbox
            Returns:
                Count of items in journal mailbox core
        """
        try:
            if result is None:
                result = {}
            self.log.info("Getting count of all results in journalmbx core")
            url = f'{self.base_url}journalmbx/select?q=*:*&rows=0&wt=json'
            response = requests.get(url=url)
            result["journalmbx"] = self.get_count_from_json(response.content)
            self.log.info(result["journalmbx"])
            return result
        except Exception as excp:
            self.log.exception(
                "Exception in method 'get_journal_result_cnt'. %s",
                str(excp))
            raise excp

    def set_standlone_base_url(self):
        """Method to set the base url of the Solr standalone"""
        try:
            self.log.info("Setting the base url for solr queries")
            temp_base = self.base_url.split("http://")[1]
            if self.exch_obj.subclient_name == "usermailbox":
                self.base_url = f'{self.base_url}usermbx0/select?shards='
                for i in range(8):
                    self.base_url = f'{self.base_url}{temp_base}usermbx{i}'
                    if i < 7:
                        self.base_url = f'{self.base_url},'
                self.base_url = f'{self.base_url}&'
            else:
                self.base_url = f'{self.base_url}journalmbx/select?'
            self.log.info("Base url for solr queries is: %s" % self.base_url)

        except Exception as excp:
            self.log.exception(
                "Exception in method 'set_standlone_base_url'. %s",
                str(excp))
            raise excp

    def is_job_played(self, job_id):
        """Method to check if job has started playing or not.
            Args:
                job_id(int)        -- Job id

            Raises:
                Exception if job is not played after 5 mins
        """
        try:
            self.log.info(
                "----------Checking if job %s started playing------------" %
                job_id)
            self._is_job_played({"jid": job_id, "datatype": 2,
                                 self.keyword_for_client_id: self.client_id})
        except Exception as excp:
            self.log.exception("Exception: %s" % excp)
            raise excp

    def check_all_items_played_successfully(self, job_id, attr_list=None):
        """Method to check if all items in the job were successfully played or not.
            Args:
                job_id(int)        -- Job id

                attr_list(set)     -- Attribute list to return, Will return the
                    Default(None)     default_attrib_list by default(Works as fl in Solr)

            Returns:
                Details about all the items in that job if playback was successful

            Raises:
                Exception if the job was not played after 10 mins
        """
        try:
            self.log.info(
                "----------Checking if job %s was played successfully------------" %
                job_id)
            self._check_all_items_played_successfully({"jid": job_id, "datatype": 2,
                                                       self.keyword_for_client_id: self.client_id},
                                                      job_id, attr_list)
        except Exception as excp:
            self.log.exception("Exception: %s", str(excp))
            raise excp

    def is_content_indexed(
            self,
            number_of_items,
            preview=False,
            preview_path=None):
        """Method to check if items are content indexed.
            Args:
                number_of_items (int)   -- Number of items applicable for CI job

                preview(boolean)        -- If job was done with preview option selected

                preview_path(str)        -- The preview path

            Raises:
               Exception if the items are not content indexed
        """
        try:
            self.log.info("Validating Content index")
            return self._is_content_indexed({"cistatus": 1,
                                             "CAState": 0,
                                             "datatype": 2,
                                             self.keyword_for_client_id: self.client_id},
                                            number_of_items,
                                            preview,
                                            preview_path)
        except Exception as excp:
            self.log.exception("Exception occurred %s" % excp)

    def get_items_for_users(self, user_guid_lists):
        """Method to get documents for users guid
            Args:
                user_guid_lists(list)     -- List of user guids

            Returns:
                Details dictonary of user details
        """
        try:
            self.log.info(
                "----------Getting solr documents for users: ------------" %
                user_guid_lists)
            result = {}

            for user in user_guid_lists:
                result[user] = self.get_result_of_custom_query(
                    select_dict={'visible': 'true', 'datatype': 2, 'cvowner': user})
            return result
        except Exception as excp:
            self.log.exception("Exception: %s", str(excp))
            raise excp

    def validate_retention(self, number_of_days):
        """Method to validate retention
            Args:
                number_of_days(int)     -- Number of days in retention period

            Raises:
                Exception if retention is not valid
        """
        try:
            self.log.info(
                "Validating Retention for client id: %s" %
                self.client_id)
            self._validate_retention(number_of_days, ["mtm", "datatype"],
                                     {self.keyword_for_client_id: self.client_id,
                                      'visible': 'false', "datatype": 2})

        except Exception as excp:
            self.log.exception("Exception while validating retention")
            raise excp


class SolrCloud(SolrHelper):
    """Class to execute solr cloud related operations """

    def __init__(self, ex_object, searchURL=None, cvsolr=False):
        """Initializes the Solr Cloud object
            Args:
                ex_object(object)      -- instance of the exchange object
        """
        super().__init__(ex_object)
        self.log.info("-------------- Solr Cloud Constructor -------------")
        self.default_attrib_list = {
            'MessageClass',
            'CCSMTP',
            'FromSMTP',
            'ToSMTP',
            'Subject',
            'HasAttachment',
            'HasAnyAttachment',
            'Folder',
            'entity_ccn',
            'entity_ssn',
            'CAState',
            'CIJobId',
            'ContentIndexingStatus',
            'AchiveFileId',
            'ArchiveFileOffset'}
        if searchURL is None:
            self.set_cloud_base_url()
            self.get_user_results_count()
        else:
            self.base_url = searchURL
        self.keyword_for_client_id = "ClientId"
        self.type = SOLR_TYPE_DICT[self.index_details[0]['server_type']]
        self.log.info(
            "-------------- Solr Cloud Constructor Ends -------------")

    def set_cloud_base_url(self):
        """Method to set the base url of the Solr cloud
            Raises:
                Exception if error in parsing xml
        """
        try:
            self.log.info("Setting the base url for solr queries")
            base_url = f'{self.index_details[0]["server_url"]}/solr/'
            valid = True
            if self.exch_obj.subclient_name == "usermailbox":
                for i in range(len(self.index_details)):
                    response = urllib.request.urlopen(
                        f'{base_url}#/').getcode()
                    if response == 200:
                        self.base_url = (
                            f'{base_url}UM_{self.index_details[i]["engine_name"]}_'
                            f'{self.index_details[i]["backupset_guid"]}/select?')
                        valid = False
                        break
            else:
                mb_type = 'CM_'
                if self.exch_obj.subclient_name == "journalmailbox":
                    mb_type = 'JM_'
                for i in range(len(self.index_details)):
                    response = requests.get(url=f'{base_url}#/').status_code
                    if response == 200:
                        self.base_url = (
                            f'{base_url}{mb_type}'
                            f'{self.index_details[i]["engine_name"]}_'
                            f'{self.index_details[i]["backupset_guid"]}/select?')
                        valid = False
                        break
            if valid:
                raise Exception
            self.log.info("Base url for solr queries is: %s" % self.base_url)

        except Exception as excp:
            self.log.exception(
                "Exception occurred. Check if index server is down. %s",
                str(excp))
            raise excp

    def get_user_results_count(self):
        """Method to get the count of items in each core for user mailbox
            Returns:
                Count of items in the collection
        """
        try:
            result = {}
            url = f'{self.base_url}q=*:*&rows=0&wt=json'
            self.log.info(
                "Getting the count of all items for the solr cloud. URL = %s" %
                url)
            response = requests.get(url=url)
            self.check_if_error_in_response(response)
            result[self.index_details[0]["engine_name"]] = (
                self.get_count_from_json(response.content))
            self.log.info(result)
            return result
        except Exception as excp:
            self.log.info(
                "Exception occurred while getting total count. %s" %
                str(excp))
            raise excp

    def is_job_played(self, job_id):
        """Method to check if job has started playing or not.
            Args:
                job_id(int)        -- Job id

            Raises:
                Exception if job is not played after 5 mins
        """
        try:
            self.log.info(
                "----------Checking if job %s started playing------------" %
                job_id)
            self._is_job_played({"BackupJobId": job_id, "DocumentType": 2,
                                 self.keyword_for_client_id: self.client_id})
        except Exception as excp:
            self.log.exception("Exception: %s", str(excp))
            raise excp

    def check_all_items_played_successfully(self, job_id, attr_list=None):
        """Method to check if all items in the job were successfully played or not.
            Args:
                job_id(int)        -- Job id

                attr_list(set)     -- Attribute list to return, Will return the
                    Default(None)      default_attrib_list by default(Works as fl in Solr)

            Returns:
                Details about all the items in that job if playback was successful

            Raises:
                Exception if the job was not played after 10 mins
        """
        try:
            self.log.info(
                "----------Checking if job %s was played successfully------------" %
                job_id)
            self._check_all_items_played_successfully(
                {
                    "BackupJobId": job_id,
                    "DocumentType": 2,
                    self.keyword_for_client_id: self.client_id},
                job_id,
                attr_list)
        except Exception as excp:
            self.log.exception("Exception: %s", str(excp))
            raise excp

    def is_content_indexed(
            self,
            number_of_items,
            preview=False,
            preview_path=None):
        """Method to check if items for the client are content indexed.
            Args:
                number_of_items (int)   -- Number of items applicable for CI job

                preview(boolean)        -- If job was done with preview option selected

                preview_path(str)        -- The preview path

            Raises:
               Exception if the items are not content indexed
        """
        try:
            self.log.info("Validating Content Indexing")
            return self._is_content_indexed(
                {
                    "ContentIndexingStatus": 1,
                    "DocumentType": 2,
                    self.keyword_for_client_id: self.client_id},
                number_of_items,
                preview,
                preview_path)
        except Exception as excp:
            self.log.exception("Exception occurred %s" % excp)

    def get_items_for_users(self, user_guid_lists):
        """Method to get documents for users guid
            Args:
                user_guid_lists(list)     -- List of user guids

            Returns:
                Details dictonary of user details
        """
        try:
            self.log.info(
                "----------Getting solr documents for users: ------------" %
                user_guid_lists)
            reuslt = {}
            for user in user_guid_lists:
                reuslt[user] = self.get_result_of_custom_query(
                    select_dict={'IsVisible': 'true', 'DocumentType': 2, 'OwnerId_sort': user})
            return reuslt
        except Exception as excp:
            self.log.exception("Exception: %s", str(excp))
            raise excp

    def validate_retention(self, number_of_days):
        """Method to validate retention
            Args:
                number_of_days(int)     -- Number of days in retention period

            Raises:
                Exception if retention is not validated
        """
        try:
            self.log.info(
                "Validating Retention for client id: %s" %
                self.client_id)
            self._validate_retention(number_of_days, ["ReceivedTime", "DocumentType"],
                                     {self.keyword_for_client_id: self.client_id,
                                      'IsVisible': 'false', "DocumentType": 2})
        except Exception as excp:
            self.log.exception("Exception while validating retention")
            raise excp


class CVSolr(SolrHelper):
    """Class to execute solr cvsolr related operations """

    def __init__(self, ex_object, searchURL=None):
        """Initializes the cvsolr object
            Args:
                ex_object(object)      -- instance of the exchange object
         """
        super(CVSolr, self).__init__(ex_object)
        self.log.info(
            "-------------- CVSolr Constructor -------------")
        self.default_attrib_list = {
            'msgclass',
            'ccsmtp',
            'fmsmtp',
            'tosmtp',
            'conv',
            'hasattach',
            'hasAnyAttach',
            'folder',
            'entity_ccn',
            'entity_ssn',
            'CAState',
            'cijid',
            'ContentIndexingStatus',
            'afid',
            'afof'}
        if searchURL is None:
            self.set_cvsolr_base_url()
            self.get_user_results_count()
        else:
            self.base_url = searchURL
        self.keyword_for_client_id = "ClientId"
        self.type = SOLR_TYPE_DICT[self.index_details[0]['server_type']]
        self.log.info(
            "-------------- Solr cvsolr Constructor Ends -------------")

    def set_cvsolr_base_url(self):
        """Method to set the base url of the cvsolr
            Raises:
                Exception if error in parsing xml
        """
        try:
            self.log.info("Setting the base url for solr queries")
            base_url = f'{self.index_details[0]["server_url"]}/solr/'
            if self.exch_obj.subclient_name == "usermailbox":
                if self.index_details[0]['is_k8s']:
                    self.log.info(
                        f'Kubernetes Index server cluster. Trying admin ping - {base_url}UM_{self.index_details[0]["backupset_guid"]}_multinode/admin/ping')
                    response = urllib.request.urlopen(
                        f'{base_url}UM_{self.index_details[0]["backupset_guid"]}_multinode/admin/ping').getcode()
                    if response == 200:
                        self.base_url = (
                            f'{base_url}UM_'
                            f'{self.index_details[0]["backupset_guid"]}_multinode/select?')
                else:
                    response = urllib.request.urlopen(
                        f'{base_url}#/').getcode()
                    if response == 200:
                        self.base_url = (
                            f'{base_url}UM_'
                            f'{self.index_details[0]["backupset_guid"]}_multinode/select?')
            self.log.info("Base url for solr queries is: %s" % self.base_url)

        except Exception as excp:
            self.log.exception(
                "Exception occurred. Check if index server is down. %s",
                str(excp))
            raise excp

    def get_user_results_count(self):
        """Method to get the count of items in each core for user mailbox
            Returns:
                Count of items in the collection
        """
        try:
            result = {}
            base_url = f'{self.index_details[0]["server_url"]}/solr/'
            if self.exch_obj.subclient_name == "usermailbox":
                self.base_url = (
                    f'{base_url}UM_'
                    f'{self.index_details[0]["backupset_guid"]}_multinode/select?')
            url = f'{self.base_url}q=*:*&rows=0&wt=json'
            self.log.info(
                "Getting the count of all items for the cvsolr URL = %s" %
                url)
            response = requests.get(url=url)
            self.check_if_error_in_response(response)
            result[self.index_details[0]["engine_name"]] = (
                self.get_count_from_json(response.content))
            self.log.info(result)
            return result
        except Exception as excp:
            self.log.info(
                "Exception occurred while getting total count. %s" %
                str(excp))
            raise excp

    def get_user_sum_of_results_count(self):
        """Method to get the total count of items in each core for user mailbox
            Returns:
                Total Count of items in each user mailbox core
        """
        try:
            result = {}
            base_url = f'{self.index_details[0]["server_url"]}/solr/'
            self.base_url = (
                f'{base_url}UM_'
                f'{self.index_details[0]["backupset_guid"]}_multinode/select?')
            url = f'{self.base_url}q=*:*&rows=0&wt=json'
            self.log.info(
                "Getting the count of all items for the cvsolr URL = %s" %
                url)
            response = requests.get(url=url)
            self.check_if_error_in_response(response)
            result[self.index_details[0]["engine_name"]] = (
                self.get_count_from_json(response.content))
            self.log.info(result)
            return result
        except Exception as excp:
            self.log.exception("Exception in method 'get_user_sum_of_results_count'")
            raise excp

    def is_job_played(self, job_id):
        """Method to check if job has started playing or not.
            Args:
                job_id(int)        -- Job id

            Raises:
                Exception if job is not played after 5 mins
        """
        try:
            self.log.info(
                "----------Checking if job %s started playing------------" %
                job_id)
            self._is_job_played({"BackupJobId": job_id, "DocumentType": 2,
                                 self.keyword_for_client_id: self.client_id})
        except Exception as excp:
            self.log.exception("Exception: %s", str(excp))
            raise excp

    def check_all_items_played_successfully(self, job_id, attr_list=None):
        """Method to check if all items in the job were successfully played or not.
            Args:
                job_id(int)        -- Job id

                attr_list(set)     -- Attribute list to return, Will return the
                    Default(None)      default_attrib_list by default(Works as fl in Solr)

            Returns:
                Details about all the items in that job if playback was successful

            Raises:
                Exception if the job was not played after 10 mins
        """
        try:
            self.log.info(
                "----------Checking if job %s was played successfully------------" %
                job_id)
            self._check_all_items_played_successfully(
                {
                    "BackupJobId": job_id,
                    "DocumentType": 2,
                    self.keyword_for_client_id: self.client_id},
                job_id,
                attr_list)
        except Exception as excp:
            self.log.exception("Exception: %s", str(excp))
            raise excp

    def is_content_indexed(
            self,
            number_of_items,
            preview=False,
            preview_path=None):
        """Method to check if items for the client are content indexed.
            Args:
                number_of_items (int)   -- Number of items applicable for CI job

                preview(boolean)        -- If job was done with preview option selected
					Default(False)

                preview_path(str)        -- The preview path
                    Default(None)

            Raises:
               Exception if the items are not content indexed
        """
        try:
            self.log.info("Validating Content Indexing")
            return self._is_content_indexed(
                {
                    "ContentIndexingStatus": 1,
                    "DocumentType": 2,
                    self.keyword_for_client_id: self.client_id},
                number_of_items,
                preview,
                preview_path)
        except Exception as excp:
            self.log.exception("Exception occurred %s" % excp)

    def get_items_for_users(self, user_guid_lists):
        """Method to get documents for users guid
            Args:
                user_guid_lists(list)     -- List of user guids

            Returns:
                Details dictonary of user details
        """
        try:
            self.log.info(
                "----------Getting solr documents for users: ------------" %
                user_guid_lists)
            reuslt = {}
            for user in user_guid_lists:
                reuslt[user] = self.get_result_of_custom_query(
                    select_dict={'IsVisible': 'true', 'DocumentType': 2, 'OwnerId_sort': user})
            return reuslt
        except Exception as excp:
            self.log.exception("Exception: %s", str(excp))
            raise excp

    def validate_retention(self, number_of_days):
        """Method to validate retention
            Args:
                number_of_days(int)     -- Number of days in retention period

            Raises:
                Exception if retention is not validated
        """
        try:
            self.log.info(
                "Validating Retention for client id: %s" %
                self.client_id)
            self._validate_retention(number_of_days, ["ReceivedTime", "DocumentType"],
                                     {self.keyword_for_client_id: self.client_id,
                                      'IsVisible': 'false', "DocumentType": 2})
        except Exception as excp:
            self.log.exception("Exception while validating retention")
            raise excp
