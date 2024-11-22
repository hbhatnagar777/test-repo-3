# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for Solr related operations for Teams

SolrHelper:

    index_details()                         -- Return details of the index server associated with client

    base_url()                              -- Returns base url for solr queries

    set_cvsolr_base_url()                   -- Method to set the base url of the cvsolr

    create_solr_query()                     -- Creates solr search query based on inputs provided

    check_if_job_started_playing()          -- Checks if job has started play back

    check_if_error_in_response()            -- Method to check if response has error

    get_count_from_json()                   -- Gets the value of numFound in json response of solr

    create_url_and_get_response()           -- Gets response of url

    get_number_of_items_in_backup_job()     -- Gets number of items in the provided backup job

    _check_all_items_played_successfully()  -- Checks if playback was successfully completed

"""

import time
import json
import datetime

import requests
from AutomationUtils.machine import Machine
from Database.dbhelper import DbHelper


class SolrHelper:
    """Base class to execute solr related operations for Teams"""

    def __init__(self, teams_helper_obj, search_url=None):
        """Initializes the Solr object
            Args:
                teams_helper_obj  (object)      -- Instance of the teams_helper object
        """
        self._teams_helper_obj = teams_helper_obj
        self._tc_object = self._teams_helper_obj._tc_obj
        self.log = self._tc_object.log
        self._index_details = None
        self._base_url = search_url
        self.default_attrib_list = None
        self._csdb = DbHelper(self._tc_object.commcell)._csdb
        if self._base_url is None:
            self.set_cvsolr_base_url()
    @property
    def index_details(self):
        """Returns list of details of index servers"""
        if self._index_details is None:
            index_server_object = self._tc_object.commcell.index_servers.get(
                self._tc_object.tcinputs.get("IndexServer"))
            self._index_details = index_server_object.properties
        return self._index_details

    @property
    def base_url(self):
        """Return base url for solr queries"""
        return self._base_url

    @base_url.setter
    def base_url(self, value):
        self._base_url = value

    def set_cvsolr_base_url(self, operation="select"):
        """Method to set the base url of the cvsolr
            Raises:
                Exception if error in parsing xml
        """
        try:
            self.log.info("Setting the base url for solr queries")
            base_url = f'{self.index_details["cIServerURL"][0]}/solr/'
            backupset_guid = self._teams_helper_obj._backupset.properties.get("backupSetEntity", {}).get(
                "backupsetGUID", "")
            self.base_url = f'{base_url}TeamsIndex_{backupset_guid}_multinode/{operation}?'
            self.log.info("Base url for solr queries is: %s" % self.base_url)
        except Exception as exception:
            self.log.exception("Exception occurred. Check if index server is down. %s", str(exception))
            raise exception


    def create_solr_query(
            self,
            select_dict=None,
            attr_list=None,
            op_params={}):
        """Method to create the solr query based on the params
            Args:
                select_dict(dictionary)     --  Dictionary containing search criteria and value
                                                Acts as 'q' field in solr query
                                                (Ex:JobId:18888,TeamsItemType:15)

                attr_list(set)            --  Column names to be returned in results.
                                                Acts as 'fl' in solr query
                                                (Ex:TeamName,TeamsItemType,TeamsItemName)

                op_params(dictionary)       --  Other params and values for solr query
                                                (Ex: start, no. of rows)

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
            op_params['wt'] = "json"
            for key, value in op_params.items():
                if value is None:
                    ex_query += f'&{key}'
                else:
                    ex_query += f'&{key}={str(value)}'
            self.log.info("Optional parameters are: %s" % ex_query)

            final_url = f'{self.base_url}{search_query}{field_query}{ex_query}'
            return final_url

        except Exception as exception:
            self.log.exception(
                "Exception while creating solr query: %s" %
                str(exception))
            raise exception

    def check_if_job_started_playing(self, select_dict):
        """Method to check if job has started playing or not. Should be called from CVSolr class
            Args:
                select_dict(dict)  -- Dictionary of keyword and job_id

            Raises:
                Exception if job is not played after 5 mins
        """
        try:
            solr_url = self.create_solr_query(
                select_dict=select_dict, op_params={"rows": 0})
            self.log.info("URL formed from the details provided is: %s" % solr_url)
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
        except Exception as exception:
            self.log.exception(
                "Exception while checking if job was played. %s" %
                str(exception))
            raise exception

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
        except Exception as exception:
            self.log.exception(exception)
            raise exception

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
        except Exception as exception:
            self.log.exception(
                "Exception in method 'get_count_from_json' while parsing json to "
                "get result count")
            raise exception

    def create_url_and_get_response(
            self,
            select_dict=None,
            attr_list=None,
            op_params=None,
            http_request="GET",
            request_json=None):
        """Helper method to get results from a url
            Args:
                select_dict(dictionary)         --  Dictionary containing search criteria and
                                                    value. Acts as 'q' field in solr query
                                                    (Ex:JobId:18888,TeamsItemType:15)

                attr_list(set)                  --  Criteria to filter results. Acts as 'fl' in
                                                    solr query
                                                    (Ex:TeamName,TeamsItemType,TeamsItemName)

                op_params(dictionary)           --  Other params and values for solr query. Do not
                                                    mention 'wt' param as it is always json
                                                    (Ex: start, rows)

                http_request (str)              --  Type of http requests GET and POST

                request_json (dict)             --  Request json if it is post request

            Returns:
                content of the response
        """
        try:
            solr_url = self.create_solr_query(
                select_dict, attr_list, op_params)
            self.log.info(
                "URL formed from the details provided is: %s" %
                solr_url)
            if http_request.upper() == "GET":
                return requests.get(url=solr_url)
            elif http_request.upper() == "POST":
                if request_json:
                    return requests.post(url=solr_url, json=request_json)
                else:
                    self.log.exception("Request json is not provided for post request")
                    raise Exception("Request json is not provided for post request")
            else:
                self.log.exception(f"It does not support {http_request.upper()} method")
                raise Exception(f"It does not support {http_request.upper()} method")
        except Exception as exception:
            raise exception

    def get_number_of_items_in_backup_job(self, job_id: int):
        """
            Method to get the number of items in the backup job
            Arguments:
                job_id(int)        -- Job id for which number of items is required

            Returns:
                Number of items in the provided job id
        """
        try:
            if job_id is None:
                raise Exception("job_id should be valid one")
            self.log.info(
                "Getting number of items in job %s from database" %
                job_id)
            query_string = "select totalNumOfFiles from JMBkpStats Where jobId=%s" % job_id
            self._csdb.execute(query_string)
            result = self._csdb.fetch_one_row()
            self.log.info(
                "Number of items in job %s is: %s" %
                (job_id, result[0]))
            return int(result[0])
        except Exception as exception:
            self.log.exception(
                "Error in getting job details from database. %s" %
                str(exception))
            raise exception

    def _check_all_items_played_successfully(
            self, job_id):
        """
            Method to check if all items in a job were played successfully.
            Args:
                job_id  (int)  --  job id to be check
            Returns:
                Return True if

            Raises:
                Exception if the job was not played after 600 seconds
        """
        try:
            select_dict = {"keyword": f"JobId:{job_id}"}
            solr_url = self.create_solr_query(
                select_dict=select_dict)
            self.log.info(
                "URL formed from the details provided is: %s" %
                solr_url)
            response = requests.get(url=solr_url)
            self.check_if_error_in_response(response)
            index_new_num_file_count = self.get_count_from_json(response.content)
            job_num_file_count = self.get_number_of_items_in_backup_job(job_id)
            return (index_new_num_file_count - job_num_file_count - self._tc_object.no_of_objects) == 0

        except Exception as exception:
            self.log.exception(
                "Exception while checking if job was successfully played. %s" %
                str(exception))
            raise exception

    def update_document(self, content_id, document_key_values):
        update_values = {}
        for key in document_key_values:
            update_values[key] = {"set": document_key_values[key]}
        self.set_cvsolr_base_url(operation='update')
        try:
            update_url = self._base_url+'?&commit=true&wt=json'
            request_json = [{
                "contentid": content_id,
                **update_values
            }]
            response = requests.post(url=update_url, json=request_json)
            self.set_cvsolr_base_url()
        except Exception as ex:
            self.set_cvsolr_base_url()
            raise Exception(ex)

    def subtract_retention_time(self, date_deleted_formatted_time, num_of_days):
        """Subtracts the specified number of days from given date deleted time

            Args:

                date_deleted_formatted_time (str)    --  Vaule of 'DateDeleted' field
                                                         Example: 1608610925

                num_of_days(int)                     --  Number of days to be subtracted from 'DateDeleted' field

        """
        try:
            self.log.info(f"Date deleted formatted time: {date_deleted_formatted_time}")
            date_deleted_time = datetime.datetime.strptime(date_deleted_formatted_time, '%Y-%m-%dT%H:%M:%SZ')
            self.log.info(f"Date deleted time: {date_deleted_time}")
            subtracted_data_deleted_time = date_deleted_time - datetime.timedelta(num_of_days)
            self.log.info(
                f"Subtracted date deleted time: {subtracted_data_deleted_time} after subtracting {num_of_days} from "
                f"date deleted time")
            subtracted_data_deleted_formatted_time = subtracted_data_deleted_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            self.log.info(f"Subtracted date deleted formatted time: {subtracted_data_deleted_formatted_time}")
            return subtracted_data_deleted_formatted_time
        except Exception as exception:
            self.log.exception(f"An error occurred subtracting retention time from date deleted time ")
            raise exception


