# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright CommVault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
    Main file for Solr related operations for a Dynamics 365 client

D365SolrHelper:

    d365_object()                           -- Returns CVDynamics365 object

    index_details()                         -- Return details of the index server associated with client

    base_url()                              -- Returns base url for solr queries

    client_id()                             -- Returns the client id

    client_name()                           -- Returns the client name

    set_cvsolr_base_url()                   -- Method to set the base url of the cvsolr

    get_number_of_items_in_backup_job()     -- Gets number of items in the provided backup job

    create_solr_query()                     -- Creates solr search query based on inputs provided

    _is_job_played()                        -- Checks if job has started play back

    _check_all_items_played_successfully()  -- Checks if playback was successfully completed

    check_if_error_in_response              -- Method to check if response has error

    get_count_from_json()                   -- Gets the value of numFound in json response of solr

    create_url_and_get_response()           -- Gets response of url

    set_cvsolr_base_url()                   -- Set the base url for SOLR queries for a Dynamics 365 client
        Base URL for Dynamics 365 clients are of the form:
            <SOLR-URL>/D365Index_<Backup-Set-GUID>

    is_job_played()                         -- Check if job has started playing

    check_all_items_played_successfully()   -- Check if playback was successfully completed for
                                                    a Dynamics 365 backup job

"""

import time
import json
import requests
import datetime


class D365SolrHelper:
    """Base class to execute solr related operations for Dynamics 365"""

    def __init__(self, d365_object, search_url=None):
        """
            Initializes the D365SolrHelper object
            Args:
                d365_object         (object)--  instance of the CVDynamics365 object
                search_url          (str)--     Search URL for CV Solr
        """
        self._d365_object = d365_object
        self.log = self._d365_object.log
        self.log.info("Logger initialized for D365SolrHelper")
        self._index_details = None
        self._base_url = search_url
        self.default_attrib_list = None
        if search_url is None:
            self.set_cvsolr_base_url()
        else:
            self.base_url = search_url

    @property
    def d365_object(self):
        """Returns CVDynamics365 object"""
        return self._d365_object

    @property
    def index_details(self):
        """Returns list of details of index servers"""
        if self._index_details is None:
            index_server_object = self.d365_object.commcell.index_servers.get(
                self.d365_object.index_server)
            self._index_details = index_server_object.properties
        return self._index_details

    @property
    def base_url(self):
        """Return base url for solr queries"""
        return self._base_url

    @base_url.setter
    def base_url(self, value):
        """
            Set the base URL for Solr queries
            Base URL is usually of the form:
                https://<machine-FQDN/IP Address>/<SOLR-Port>/D365index_<BackupSetGUID>_multinode

            Argument:
                value       (str)--     Base URl to be set
        """
        self._base_url = value

    @property
    def client_id(self):
        """Returns id of client"""
        return int(self.d365_object.client.client_id)

    @property
    def client_name(self):
        """Returns Name of client"""
        return self.d365_object.client.client_name

    def set_cvsolr_base_url(self, operation: str = "select"):
        """
            Method to set the base url of the CV Solr for a Dynamics 365 CRM Client

            Arguments:
                operation           (str)--     Operation to be performed
                    Default Value:
                        select      for select operation
            Raises:
                Exception if error in parsing xml
        """
        try:
            self.log.info("Setting the base url for Dynamics 365 SOLR queries")
            base_url = f'{self.index_details["cIServerURL"][0]}/solr/'
            backupset_guid = self.d365_object.backupset.properties.get("backupSetEntity", {}).get(
                "backupsetGUID", "")
            self.base_url = f'{base_url}D365Index_{backupset_guid}_multinode/{operation}?'
            self.log.info("The base URL for SOLR queries is: %s" % self.base_url)
        except Exception as exception:
            self.log.exception("Exception occurred. Check if index server is down. %s", str(exception))
            raise exception

    def check_all_items_played_successfully(self, job_id, attr_list=None):
        """Method to check if all items in the Dynamics 365 backup job were successfully
            played on the index or not.
            Arguments:
                job_id(int)        -- Job id

                attr_list(set)     -- Attribute list to return, Will return the
                    Default Value:
                        (None)      default_attrib_list by default(Works as fl in Solr)

            Returns:
                Details about all the items in that job if playback was successful

            Raises:
                Exception if the job was not played after 10 mins
        """
        try:
            self.log.info("Checking if Job with Job ID: %s was played successfully" % job_id)
            self._check_all_items_played_successfully({"JobId": job_id}, job_id, attr_list)
        except Exception as exception:
            self.log.exception("Exception: %s", str(exception))
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
            self.log.info(
                "Getting number of items in job %s from database" %
                job_id)
            query_string = "select totalNumOfFiles from JMBkpStats Where jobId=%s" % job_id
            self.d365_object.csdb.execute(query_string)
            result = self.d365_object.csdb.fetch_one_row()
            self.log.info(
                "Number of items in job %s is: %s" %
                (job_id, result[0]))
            return int(result[0])
        except Exception as exception:
            self.log.exception(
                "Error in getting job details from database. %s" %
                str(exception))
            raise exception

    def create_solr_query(
            self,
            select_dict=None,
            attr_list=None,
            op_params=None):
        """
            Method to create a Dynamics 365 CV Solr query based on the parameters
            Arguments:
                select_dict(dictionary)     --  Dictionary containing search criteria and value
                                                Acts as 'q' field in solr query

                attr_list(set)            --  Column names to be returned in results.
                                                Acts as 'fl' in solr query

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

        except Exception as exception:
            self.log.exception(
                "Exception while creating solr query: %s" %
                str(exception))
            raise exception

    def _is_job_played(self, select_dict):
        """
            Method to check if the job has started playing or not.
            Args:
                select_dict(dict)  -- Dictionary of keyword and job_id

            Raises:
                Exception if job is not played after 300 seconds
        """
        try:
            solr_url = self.create_solr_query(
                select_dict=select_dict, op_params={"rows": 0})
            self.log.info("Dynamics 365 CV Solr URL formed from the details provided is: %s" % solr_url)
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

    def _check_all_items_played_successfully(
            self, select_dict, job_id, attr_list=None):
        """
            Method to check if all items in a job were played successfully.
            Args:
                select_dict(dict)   --  Dictionary of backup job keyword and datatype

                job_id(int)         --  Job id

                attr_list(set)     --   Attribute list to return, Will return the
                    Default Value:
                        (None)          default_attrib_list by default(Works as fl in Solr)

            Returns:
                Details about all the items in that job if true

            Raises:
                Exception if the job was not played after 600 seconds
        """
        try:
            solr_url = self.create_solr_query(
                select_dict=select_dict)
            self.log.info(
                "URL formed from the details provided is: %s" %
                solr_url)
            response = requests.get(url=solr_url)
            self.check_if_error_in_response(response)
            index_new_num_file_count = self.get_count_from_json(response.content)
            index_old_num_file_count = -1
            job_num_file_count = self.get_number_of_items_in_backup_job(job_id)
            tot_time = 0
            while job_num_file_count - index_new_num_file_count > 0 and tot_time < 10:
                tot_time += 1
                self.log.info(
                    "Total number of files played(%d) is not equal to total items in "
                    "job(%d). Waiting for 1 minute and retrying" %
                    (index_new_num_file_count, job_num_file_count))
                time.sleep(60)
                if index_new_num_file_count != index_old_num_file_count:
                    index_old_num_file_count = index_new_num_file_count
                    response = requests.get(url=solr_url)
                    self.check_if_error_in_response(response)
                    index_new_num_file_count = self.get_count_from_json(response.content)
                else:
                    time.sleep(60)
                    tot_time += 1
                    response = requests.get(url=solr_url)
                    self.check_if_error_in_response(response)
                    index_new_num_file_count = self.get_count_from_json(response.content)
                    if index_new_num_file_count == index_old_num_file_count:
                        raise Exception("Job is not played")
            self.log.info("Job %s was successfully played." % job_id)
        except Exception as exception:
            self.log.exception(
                "Exception while checking if job was successfully played. %s" %
                str(exception))
            raise exception

    def check_if_error_in_response(self, response):
        """
            Method to check if the SOLR response has an error
            Args:
                response(obj)         --  Response Object

            Raises:
                Exception if response has an error
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

                attr_list(set)                  --  Criteria to filter results. Acts as 'fl' in
                                                    solr query

                op_params(dictionary)           --  Other params and values for solr query. Do not
                                                    mention 'wt' param as it is always json
                                                    (Ex: start, rows)

                http_request (str)              --  Type of http request

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
            if http_request == "GET":
                return requests.get(url=solr_url)
            elif http_request == "POST":
                if request_json:
                    return requests.post(url=solr_url, json=request_json)
                else:
                    self.log.exception("Request json is not provided for post request")
                    raise Exception("Request json is not provided for post request")
        except Exception as exception:
            raise exception

    def is_job_played(self, job_id):
        """
            Method to check if job has started playing or not.
            Args:
                job_id(int)        -- Job id

            Raises:
                Exception if job is not played after 300 seconds
        """
        try:
            self.log.info("Checking if Job with Job ID: %s has started playing" % job_id)
            self._is_job_played({"JobId": job_id})
        except Exception as exception:
            self.log.exception("Exception: %s", str(exception))
            raise exception

    def validate_retention(self, table_dict):
        """Method to validate retention

            Args:

                table_dict (dict)       -- Dictionary of backed up items along with their retention period
                Sample Values
                    {
                        'Table Name 1' : 2,
                        'Table Name 2' : -1
                    }



            Raises:
                Exception if retention is not valid
        """
        try:
            self.log.info(f"Validating Retention for client : {self.client_name}")
            retention = sorted(table_dict.values())[-1]
            if retention != -1:
                self._validate_retention(table_dict, retention - 2, {'DateDeleted': f'[* TO *]'})
                self._validate_retention(table_dict, retention + 2, {'DateDeleted': f'[* TO *]'})
            else:
                self._validate_retention(table_dict, 1000, {'DateDeleted': f'[* TO *]'})

        except Exception as exception:
            self.log.exception("Exception while validating retention")
            raise exception

    def _validate_retention(self, table_dict, modified_retention, select_dict):
        """Helper method to validate retention
            Args:

                 table_dict (dict)           --     Dictionary of backed up items along with their retention period

                    Example:
                    For Dynamics 365:

                        {
                            'Table Name 1': 365,
                            'Table Name 2': -1
                        }

                select_dict(dictionary)      --     Dictionary containing search criteria and value

            Raises:
                Exception if retention is not validated
        """
        try:
            op_params = {"rows": 10000}
            response = self.create_url_and_get_response(
                select_dict, ["contentid", "DateDeleted", "IsVisible", "EntityName", "EntityId", "D365Name"], op_params)
            count = self.get_count_from_json(response.content)
            if count == 0:
                raise Exception(f"Solr query returned nothing to check retention")
            self.log.info(f"Total number of items eligible for retention: {count}")
            solr_items = json.loads(response.content).get("response", {}).get("docs", [])

            if solr_items:
                for item in solr_items:
                    new_date_deleted_as_int = self.subtract_retention_time(item["DateDeleted"], modified_retention)
                    self.update_field(content_id=item["contentid"],
                                      field_name="DateDeleted",
                                      field_value=new_date_deleted_as_int)
            self.d365_object.d365_operations.submit_client_index_retention(
                self.index_details.get('indexServerClientId'))
            self.set_cvsolr_base_url()
            response = self.create_url_and_get_response(
                select_dict, ["contentid", "DateDeleted", "IsVisible", "EntityId", "EntityName", "D365Name"], op_params)
            solr_items = json.loads(response.content).get("response", {}).get("docs", [])
            if solr_items:
                for item in solr_items:
                    not_validated = False
                    self.log.info(f"Validating Retention for: {item}")

                    entity_name = item.get("EntityName").title()
                    if entity_name in table_dict:
                        if table_dict.get(entity_name) == -1 or table_dict.get(entity_name) > modified_retention:
                            if not item["IsVisible"]:
                                not_validated = True
                        else:
                            if item["IsVisible"]:
                                not_validated = True
                    else:
                        self.log.info(f"Retention needs not to be validated for {item['D365Name']} "
                                      f"of Table: {item['EntityName']}")

                    if not_validated:
                        self.log.exception(
                            f"Retention is not validated for {item['D365Name']} of Table: {item['EntityName']}")
                        raise Exception(
                            f"Retention is not validated for {item['D365Name']} of Table: {item['EntityName']}")
                    else:
                        self.log.info(f"Retention is validated for {item['D365Name']}")

            json_num = self.get_count_from_json(response.content)
            self.log.info("Total number of items not retained: %d" % json_num)
            if count != json_num:
                raise Exception("Retention not satisfied")
            self.log.info("Retention Validated")
        except Exception as exception:
            self.log.exception("Exception while validating retention")
            raise exception

    def update_field(self, content_id: str, field_name: str, field_value):
        """
            Updates specified field having specified content id

            Args:

                content_id(str)                --  content id of the item
                    Example "c8d2d2ebab2a86290f37cd6ae2ecba91!0c6932ab50bf08fa68596dacb6259f8d

                field_name(str)                --  Name of the field to be updated

                field_value                    --  Value of the field to be updated

        """
        try:
            request_json = [{
                "contentid": content_id,
                field_name: {
                    "set": field_value
                }
            }]
            self.set_cvsolr_base_url(operation="update")
            response = self.create_url_and_get_response(op_params={"commit": "true"}, http_request="POST",
                                                        request_json=request_json)
            response_json = json.loads(response.content)
            if response_json['responseHeader']['status'] == 0:
                self.log.info(f"{field_name} field with value {field_value} is changed for content id {content_id}")
            else:
                self.log.exception(f"Error occurred while updating {field_name} field for content id {content_id}")
                raise Exception(f"Error occurred while updating {field_name} field for content id {content_id}")
        except Exception as exception:
            self.log.exception(f"An error occurred while updating {field_name}field ")
            raise exception

    def subtract_retention_time(self, date_deleted_formatted_time: str, num_of_days: int):
        """
            Subtracts the specified number of days from given date deleted time

            Args:

                date_deleted_formatted_time (str)    --  Value of 'DateDeleted' field

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

