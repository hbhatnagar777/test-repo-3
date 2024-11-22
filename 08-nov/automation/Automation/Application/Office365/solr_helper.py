# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for Solr related operations

Solr:

    o365_object()                           -- Returns SharePoint/CloudConnector object

    index_details()                         -- Return details of the index server associated with client

    base_url()                              -- Returns base url for solr queries

    client_id()                             -- Returns the client id

    client_name()                           -- Returns the client name

    set_cvsolr_base_url()                   -- Method to set the base url of the cvsolr

    check_cvods_running()                   -- Checks if CVODS is running on the index server

    get_number_of_items_in_backup_job()     -- Gets number of items in the provided backup job

    create_solr_query()                     -- Creates solr search query based on inputs provided

    _is_job_played()                        -- Checks if job has started play back

    _check_all_items_played_successfully()  -- Checks if playback was successfully completed

    check_if_error_in_response              -- Method to check if response has error

    get_count_from_json()                   -- Gets the value of numFound in json response of solr

    create_url_and_get_response()           -- Gets response of url

    update_field()                          -- Updates specified field having specified content id

    subtract_retention_time()               -- Subtracts the specified number of days from given date deleted time

    _validate_retention()                   -- Helper method to validate retention

    _get_all_items_metadata()               -- Helper method to get metadata of all items from solr

CVSolr:

    set_cvsolr_base_url()                   -- Set the base url for cvsolr queries

    is_job_played()                         -- Check if job has started playing

    check_all_items_played_successfully()   -- Check if playback was successfully completed

    validate_retention()                    -- Method to validate retention

    get_all_items_metadata()                -- Method to return metadata of all items in index for the given sites

    process_index_items()                   -- Processes items returned from index into the format of items received
                                               from test case to validate

    validate_all_items()                    -- Validates items from SharePoint site and items present on index

    Example of solr queries:

    To get all the items present in a collection
    http://localhost:20000/solr/sharepointindex_backupset_GUID_multinode/select?q=*:*

    To get items count where job id is 123
    http://localhost:20000/solr/sharepointindex_backupset_GUID_multinode/select?q=JobId:7538

    To update a field in Solr
    http://localhost:20000/solr/sharepointindex_backupset_GUID_multinode/update?&commit=true&wt=json

"""

import time
import json
import datetime
from xml.etree import ElementTree

import requests
from AutomationUtils.machine import Machine
from Application.CloudApps import constants

class SolrHelper:
    """Base class to execute solr related operations """

    def __init__(self, o365_object, search_url=None):
        """Initializes the Solr object
            Args:
                o365_object(object)      -- instance of the SharePoint/CloudConnector object
        """
        self._o365_object = o365_object
        self.log = self._o365_object.tc_object.log
        self._index_details = None
        self._base_url = search_url
        self.default_attrib_list = None

    @property
    def o365_object(self):
        """Returns SharePoint/CloudConnector object"""
        return self._o365_object

    @property
    def index_details(self):
        """Returns list of details of index servers"""
        if self._index_details is None:
            index_server_object = self.o365_object.cvoperations.commcell.index_servers.get(
                self.o365_object.index_server)
            self._index_details = index_server_object.properties
        return self._index_details

    @property
    def base_url(self):
        """Return base url for solr queries"""
        return self._base_url

    @base_url.setter
    def base_url(self, value):
        self._base_url = value

    @property
    def client_id(self):
        """Returns id of client"""
        return int(self.o365_object.cvoperations.client.client_id)

    @property
    def client_name(self):
        """Returns id of client"""
        return self.o365_object.cvoperations.client.client_name

    def set_cvsolr_base_url(self, operation="select"):
        """Method to set the base url of the cvsolr
            Raises:
                Exception if error in parsing xml
        """
        try:
            self.log.info("Setting the base url for solr queries")
            base_url = f'{self.index_details["cIServerURL"][0]}/solr/'
            backupset_guid = self.o365_object.cvoperations.backupset.properties.get("backupSetEntity", {}).get(
                "backupsetGUID", "")
            if hasattr(self.o365_object.cvoperations, "instance") \
                    and hasattr(self.o365_object.cvoperations.instance, "ca_instance_type")\
                    and self.o365_object.cvoperations.instance.ca_instance_type.lower() == constants.ONEDRIVE_INSTANCE.lower():
                self.base_url = f'{base_url}onedriveindex_{backupset_guid}_multinode/{operation}?'
            else:
                self.base_url = f'{base_url}sharepointindex_{backupset_guid}_multinode/{operation}?'
            self.log.info("Base url for solr queries is: %s" % self.base_url)
        except Exception as exception:
            self.log.exception("Exception occurred. Check if index server is down. %s", str(exception))
            raise exception

    def check_cvods_running(self):
        """Method to check if CVODS is running on the index server
            Returns:
                True if CVODS is running
        """
        try:
            cnt = 0
            self.log.info("Checking if CVODS is launched")
            machine_name = self.base_url.split(":")
            machine_name = machine_name[1].split("//")[1]
            commcell = self.o365_object.cvoperations.commcell
            remote_machine = Machine(machine_name, commcell)
            while cnt < 5:
                res = remote_machine.is_process_running("CVODS")
                if res:
                    self.log.info("CVODS is running")
                    return True
                self.log.info(
                    "CVODS is not launched. Will check again after 1 min")
                time.sleep(60)
                cnt += 1
            return False
        except Exception as exception:
            self.log.exception("Exception while checking cvods status: %s", str(exception))
            raise exception

    def check_all_items_played_successfully(self, job_id, attr_list=None):
        """Method to get the total count of items in SharePoint/CloudConnector Collection
            Returns:
                Total Count of items in SharePoint/CloudConnector Collection
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_number_of_items_in_backup_job(self, job_id):
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
            self.o365_object.csdb.execute(query_string)
            result = self.o365_object.csdb.fetch_one_row()
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
        """Method to create the solr query based on the params
            Args:
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

    def _check_all_items_played_successfully(
            self, select_dict, job_id, deleted_objects_count=0, attr_list=None):
        """Method to check if all items in a job were played successfully. Should be called via
        check_all_items_played_successfully method in SolrStandalone or SolrCloud
            Args:
                select_dict(dict)   -- Dictionary of backup job keyword and datatype

                job_id(int)         -- Job id

                deleted_objects_count   -- Total objects deleted just before this job

                attr_list(set)     -- Attribute list to return, Will return the
                    Default(None)      default_attrib_list by default(Works as fl in Solr)

            Returns:
                Details about all the items in that job if true

            Raises:
                Exception if the job was not played after 10 mins
        """
        try:
            solr_url = self.create_solr_query(
                select_dict=select_dict, op_params={"rows": 0})
            self.log.info(
                "URL formed from the details provided is: %s" %
                solr_url)
            response = requests.get(url=solr_url)
            self.check_if_error_in_response(response)
            index_new_num_file_count = self.get_count_from_json(response.content) + deleted_objects_count
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
            self.log.info("Total number of items played back : %d.\nTotal number of items in the job : %d" %
                          (index_new_num_file_count, job_num_file_count))
            self.log.info("Job %s was successfully played." % job_id)
        except Exception as exception:
            self.log.exception(
                "Exception while checking if job was successfully played. %s" %
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

    def update_field(self, content_id, field_name, field_value):
        """Updates specified field having specified content id

            Args:

                content_id(str)                --  content id of the item
                Example: "c8d2d2ebab2a86290f37cd6ae2ecba91!0c6932ab50bf08fa68596dacb6259f8d

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
                self.log.exception(f"Error occured while updating {field_name} field for content id {content_id}")
                raise Exception(f"Error occured while updating {field_name} field for content id {content_id}")
        except Exception as exception:
            self.log.exception(f"An error occurred while updating {field_name}field ")
            raise exception

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

    def _validate_retention(self, items_dict, select_dict):
        """Helper method to validate retention
            Args:

                 items_dict (dict)           --     Dictionary of backed up items along with their retention period

                    Example:
                    For SharePoint:

                        {
                            'https://cvidc365.sharepoint.com/sites/TestSite1': 365,
                            'https://cvidc365.sharepoint.com/sites/TestSite2': -1
                        }

                select_dict(dictionary)      --     Dictionary containing search criteria and value

            Raises:
                Exception if retention is not validated
        """
        try:
            op_params = {"rows": 50}
            response = self.create_url_and_get_response(
                select_dict, ["contentid", "DateDeleted", "IsVisible", "Url"], op_params)
            count = self.get_count_from_json(response.content)
            if count == 0:
                raise Exception(f"Solr query returned nothing to check retention")
            self.log.info(f"Total number of items eligible for retention: {count}")
            solr_items = json.loads(response.content).get("response", {}).get("docs", [])
            retention_period = sorted(items_dict.values())[-1] + 2
            if solr_items:
                for item in solr_items:
                    new_date_deleted_as_int = self.subtract_retention_time(item["DateDeleted"], retention_period)
                    self.update_field(content_id=item["contentid"],
                                      field_name="DateDeleted",
                                      field_value=new_date_deleted_as_int)
            self.o365_object.cvoperations.process_index_retention_rules(self.index_details.get('indexServerClientId'))
            self.set_cvsolr_base_url()
            response = self.create_url_and_get_response(
                select_dict, ["contentid", "DateDeleted", "IsVisible", "Url"], op_params)
            solr_items = json.loads(response.content).get("response", {}).get("docs", [])
            if solr_items:
                for item in solr_items:
                    item_url = item['Url'].split("\\")[2]
                    if 0 < items_dict[item_url] <= retention_period:
                        if not item["IsVisible"]:
                            self.log.info(f"Retention is validated for {item['Url']}")
                        else:
                            self.log.exception(f"Retention is not validated for {item['Url']}")
                            raise Exception(f"Retention is not validated for {item['Url']}")
                    elif items_dict[item_url] == -1 or items_dict[item_url] > retention_period:
                        if item["IsVisible"]:
                            self.log.info(f"Retention is validated for {item['Url']}")
                        else:
                            self.log.exception(f"Retention is not validated for {item['Url']}")
                            raise Exception(f"Retention is not validated for {item['Url']}")
            json_num = self.get_count_from_json(response.content)
            self.log.info("Total number of items not retained: %d" % json_num)
            if count != json_num:
                raise Exception("Retention not satisfied")
            self.log.info("Retention Validated")
        except Exception as exception:
            self.log.exception("Exception while validating retention")
            raise exception

    def _get_all_items_metadata(self, filters, select_dict=None):
        """Helper method to get metadata of all items from solr

            Args:

                filters (list)      --  filters to get metadata

                select_dict (dict)  --  dictionary containing search criteria and value
                                        acts as 'q' field in solr query

            Raises:

                Exception if unable to get all items metadata

        """
        try:
            op_params = {"rows": 0}
            if select_dict is None:
                select_dict = {"*": "*"}
            response = self.create_url_and_get_response(
                select_dict, filters, op_params)
            count = self.get_count_from_json(response.content)
            op_params["rows"] = count
            response = self.create_url_and_get_response(
                select_dict, filters, op_params)
            self.log.info(f"Total number of items on index: {count}")
            solr_items = json.loads(response.content).get("response", {}).get("docs", [])
            return solr_items
        except Exception as exception:
            self.log.exception("Exception while validating retention")
            raise exception


class CVSolr(SolrHelper):
    """Class to execute cvsolr related operations """

    def __init__(self, o365_object, search_url=None):
        """Initializes the cvsolr object
            Args:
                o365_object(object)      -- instance of the SharePoint/CloudConnector object
         """
        super(CVSolr, self).__init__(o365_object)
        if search_url is None:
            self.set_cvsolr_base_url()
        else:
            self.base_url = search_url

    def is_job_played(self, job_id):
        """Method to check if job has started playing or not.
            Args:
                job_id(int)        -- Job id

            Raises:
                Exception if job is not played after 5 mins
        """
        try:
            self.log.info("Checking if job %s started playing" % job_id)
            self._is_job_played({"JobId": job_id})
        except Exception as exception:
            self.log.exception("Exception: %s", str(exception))
            raise exception

    def check_all_items_played_successfully(self, job_id, deleted_objects_count=0, attr_list=None):
        """Method to check if all items in the job were successfully played or not.
            Args:
                job_id(int)        -- Job id

                deleted_objects_count   -- toala objects deleted just before this job

                attr_list(set)     -- Attribute list to return, Will return the
                    Default(None)      default_attrib_list by default(Works as fl in Solr)

            Returns:
                Details about all the items in that job if playback was successful

            Raises:
                Exception if the job was not played after 10 mins
        """
        try:
            self.log.info("Checking if job %s was played successfully" % job_id)
            self._check_all_items_played_successfully({"JobId": job_id}, job_id, deleted_objects_count, attr_list)
        except Exception as exception:
            self.log.exception("Exception: %s", str(exception))
            raise exception

    def validate_retention(self, items_dict):
        """Method to validate retention

            Args:

                items_dict (dict)       -- Dictionary of backed up items along with their retention period
                Example:
                For SharePoint:

                    {
                        'https://cvidc365.sharepoint.com/sites/TestSite1': 365,
                        'https://cvidc365.sharepoint.com/sites/TestSite2': -1
                    }



            Raises:
                Exception if retention is not valid
        """
        try:
            self.log.info(f"Validating Retention for client : {self.client_name}")
            self._validate_retention(items_dict, {'DateDeleted': f'[* TO *]'})
        except Exception as exception:
            self.log.exception("Exception while validating retention")
            raise exception

    def get_all_items_metadata(self, filters, sites_list):
        """Method to return metadata of all items in index for the given sites.
        It includes subsites metadata also if they are backed up

            Args:

                filters (list)      --  filters to get metadata
                Example : ["SPTitle", "Url", "Version"]

                sites_list (list)   --  list of site urls for which all items index metadata to be retrieved
                Example : [
                            "https://test.sharepoint.com/sites/testsite1",
                            "https://test.sharepoint.com/sites/testsite2"
                        ]

            Raises:
                Exception if unable to get all items metadata

        """
        try:
            self.log.info(f"Validating Items backed up for the client : {self.client_name}")
            sites_index_paths = {}
            for site_url in sites_list:
                site_name = "/".join(site_url.split("/")[4:])
                sites_query = '"' + requests.utils.quote(site_name) + '" '
                select_dict = {"slevel_Url_4": sites_query}
                index_all_items_metadata = self._get_all_items_metadata(filters, select_dict)
                processed_index_paths = self.process_index_items(index_all_items_metadata)
                self.log.info(f"Number of Unique Items: {len(processed_index_paths)}")
                all_items_count = 0
                for path, items in processed_index_paths.items():
                    all_items_count = all_items_count + items.get('VersionCount')
                self.log.info(f"Number of Items Including Versions: {all_items_count}")
                sites_index_paths[site_url] = processed_index_paths
            return sites_index_paths
        except Exception as exception:
            self.log.exception("Exception while validating retention")
            raise exception

    def process_index_items(self, items):
        """Processes items returned from index into the format of items received from test case to validate

            Args:

                items (dict)              --      sets of set of items

            Returns:

                index_paths (dict)        --      dictionary of items with its metadata
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
        index_paths = {}
        for item in items:
            if item['Url'] not in index_paths.keys():
                index_paths[item['Url']] = {
                    'Title': item['SPTitle']
                }
            if 'IdxMetaData' in item.keys():
                current_version = ElementTree.fromstring(item.get('IdxMetaData')).findall('*')[0].attrib.get('uiVersion')
                if current_version:
                    current_version = float(current_version)
                else:
                    current_version = 0.0
            else:
                current_version = 0.0
            index_version = index_paths[item['Url']].get('VersionLabel', 0.0)
            version_count = index_paths[item['Url']].get('VersionCount', 0)
            index_paths[item['Url']] = {
                'VersionLabel': max(index_version, current_version),
                'VersionCount': version_count + 1
            }
        self.log.info(f"Total number of unique items on index: {len(items)}")
        return index_paths

    def validate_all_items(self, source_paths, index_paths):
        """Validates items from SharePoint site and items present on index

            Args:

                source_paths (dict)        --      dictionary of items with its metadata from SharePoint site
                Example:
                    {
                      "\\MB\\https://test.sharepoint.com/sites/TestSPAutomation\\Contents\\Test Automation List": {
                            'VersionLabel': 0.0,
                            'VersionCount' : 1
                        },
                      "\\MB\\https://test.sharepoint.com/sites/TestSPAutomation\\Contents\\AutomationList\\1_.000": {
                            'VersionLabel': 3.0,
                            'VersionCount' : 3
                        }
                    }

                index_paths (dict)         --      dictionary of items with its metadata from index
                 Example:
                    {
                      "\\MB\\https://test.sharepoint.com/sites/TestSPAutomation\\Contents\\Test Automation List": {
                            'VersionLabel': 0.0,
                            'VersionCount' : 1
                        },
                      "\\MB\\https://test.sharepoint.com/sites/TestSPAutomation\\Contents\\AutomationList\\1_.000": {
                            'VersionLabel': 1.0,
                            'VersionCount' : 1
                        }
                    }

            Raises:
                Exception if any exception occurs while validating all items
        """
        try:
            failed_items = []
            present_items = []
            ignore_paths = [
                "Contents\\_cts\\Video\\videoplayerpage.aspx",
                "Contents\\_cts\\Video\\docsethomepage.aspx",
                "Contents\\_cts\\Document Set\\docsethomepage.aspx",
                "Contents\\_catalogs\\masterpage\\v4.master",
                "Contents\\_catalogs\\masterpage\\Display Templates\\Language Files\\hr-hr\\CustomStrings.js"
            ]
            ignore_users_path = "Contents\\_catalogs\\users"
            self.log.info("Comparing site items with items on index")
            for item, item_metadata in source_paths.items():
                if item.split("\\", 3)[-1] in ignore_paths:
                    continue
                # we no longer backup _catalogs\users folder
                if ignore_users_path in item.split("\\", 3)[-1]:
                    continue
                if item in index_paths:
                    if abs(source_paths[item]['VersionLabel'] - index_paths[item]['VersionLabel']) <= 1 and \
                            abs(source_paths[item]['VersionCount'] - index_paths[item]['VersionCount']) <= 1:
                        self.log.info(f"{item} is present in index with {source_paths[item]['VersionCount']} versions".
                                      encode())
                        present_items.append(item)
                    else:
                        self.log.exception(
                            f"{item} is present in index with {index_paths[item]['VersionCount']} versions"
                            f"instead of {source_paths[item]['VersionCount']} versions".encode())
                        failed_items.append([item, item_metadata, index_paths[item]])
                else:
                    self.log.exception(f"{item} is not present in index".encode())
                    failed_items.append([item, item_metadata, index_paths.get(item, {})])
            for item in present_items:
                del index_paths[item]
                del source_paths[item]
            additional_index_items = []
            self.log.info("Comparing items on index with site items")
            for item, item_metadata in index_paths.items():
                self.log.exception(f"{item} is present in index but not on SharePoint Site".encode())
                additional_index_items.append([item, item_metadata, source_paths.get(item, {})])
            if len(failed_items) > 0:
                self.log.exception(f"The number of failed items are {len(failed_items)}")
                self.log.exception(f"The failed objects in the backup: {failed_items}".encode())
            else:
                self.log.info("There are no failed items")
            if len(additional_index_items) > 0:
                self.log.exception(f"The number of additional items on index are : {len(additional_index_items)}")
                self.log.exception(f"The additional items on index are : {additional_index_items}")
            else:
                self.log.info("There are no additional items on index ")
            if len(failed_items) > 0 or len(additional_index_items) > 0:
                return False
            return True
        except Exception as exception:
            self.log.exception("Exception while validating all items")
            raise exception
