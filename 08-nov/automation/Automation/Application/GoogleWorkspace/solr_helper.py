""""Main file for Solr related operations"""

import time
import requests
import json
from . import constants


class SolrHelper:
    """Base class to execute solr related operations """

    def __init__(self, google_object, search_url=None):
        """Initializes the Solr object
            Args:
                google_object(object)      -- instance of the google object
                searchURL(str)            -- Search URL with collection names already added
        """
        self._google_object = google_object
        self.log = self._google_object.log
        self.default_attrib_list = None
        self._index_details = None
        self._base_url = search_url
        if self._base_url is None:
            self.set_cvsolr_base_url()

    @property
    def index_details(self):
        """Returns list of details of index servers"""
        if self._index_details is None:
            index_server_object = self._google_object.commcell.index_servers.get(
                self._google_object.client_properties.get("cloudAppsInstance", {})
                                                     .get("generalCloudProperties", {})
                                                     .get("indexServer", {})
                                                     .get('clientName', None))
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
            backupset_guid = self._google_object.backupset.properties.get("backupSetEntity", {}).get("backupsetGUID",
                                                                                                     "")
            if (self._google_object.client_properties.get("instance", {})
                    .get("instanceName") == constants.GDRIVE_INSTANCE_NAME):
                self.base_url = f'{base_url}googledrive_{backupset_guid}_multinode/{operation}?'
            else:
                self.base_url = f'{base_url}gmail_{backupset_guid}_multinode/{operation}?'
            self.log.info("Base url for solr queries is: %s" % self.base_url)
        except Exception as exception:
            self.log.exception("Exception occurred. Check if index server is down. %s", str(exception))
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
        except Exception as excp:
            self.log.exception(excp)
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
            self._google_object.csdb.execute(query_string)
            result = self._google_object.csdb.fetch_one_row()
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

    def check_all_items_played_successfully(
            self, select_dict, attr_list=None):
        """Method to check if all items in a job were played successfully. d
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
            solr_url = self.create_solr_query(
                select_dict=select_dict, op_params={"rows": 0})
            self.log.info(
                "URL formed from the details provided is: %s" %
                solr_url)
            response = requests.get(url=solr_url)
            self.check_if_error_in_response(response)
            result = self.get_count_from_json(response.content)
            if result != 0:
                self.log.info("Job Played back successfully")
            return result
        except Exception as excp:
            self.log.exception(
                "Exception while checking if job was successfully played. %s" %
                str(excp))
            raise excp
