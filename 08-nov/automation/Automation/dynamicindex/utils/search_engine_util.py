# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module contains the various utility functions related to search engine.

These are the functions defined in this module:

SearchEngineHelper:

get_cloud_id()                --  Returns the search engine cloud id for the given client name

get_cloud_url()               --  Returns the search engine cloud url for the given client name

execute_search_engine_query() --  Executes the query on search engine and returns the json response

query_solr()                  --  creates the solr query for the given input and returns the solr json response


"""


class SearchEngineHelper():
    """Helper class for search engine"""

    def __init__(self, tc_object):
        """Initialize the class with testcase object"""
        self.commcell = tc_object.commcell
        self.log = tc_object.log
        self.csdb = tc_object.csdb

    def query_solr(self, solr_url, criteria, start=0, rows=0, fields=None):
        """Creates and then Executes the query and gets the response json from solr

                        Args:

                                solr_url             (str)    --  Solr base url

                                    Example : "http://<searchengine_machinename>:<port no>/solr"

                                criteria             (str)    --  q param for solr query

                                start                (int)    --  solr start param

                                rows                 (int)    --  solr rows params to fetch rows

                                fields              (list)   --  column to be fetched from solr

                        Return:
                                dics : Response json from solr

                        Exception:

                                if response is not success
        """
        solr_url = solr_url + "/select?q={0}&start={1}&rows={2}&wt=json".format(criteria, start, rows)
        if fields is not None:
            updated_fl = ""
            for field in fields:
                updated_fl = updated_fl + field + ","
            solr_url = solr_url + "&fl={0}".format(updated_fl[:-1])
        self.log.info("Querying solr : %s", solr_url)
        response = self.execute_search_engine_query(solr_url)
        if start == 0 and rows == 0:
            return int(response['numFound'])
        return response

    def execute_search_engine_query(self, query):
        """Executes the query and gets the response json from solr

                                       Args:

                                           query             (str)    --  Solr query url

                                       Return:
                                           dics : Response json from solr

                                       Exception:

                                           if response is not success
        """

        flag, response = self.commcell._cvpysdk_object.make_request("GET", query)
        if flag:
            if response.json():
                return response.json()['response']
            raise Exception("Unable to find response object in response")
        raise Exception("Unable to get response from solr : " + response.text)

    def get_cloud_id(self, client_name):
        """Method to get search engine cloud id for the given client name

                    Args:

                        client_name    (str)   --  Name of the client where search engine package is installed

                    Returns:

                        str  -- cloud id of the search engine

                    Raises:
                        Exception:

                            if fails to find cloud id from DB
        """
        clientobj = self.commcell.clients.get(client_name)
        client_id = clientobj.client_id
        _query = "select cloudid from DM2SearchServerCoreInfo " \
                 "where ClientId={0} and CloudType={1}".format(client_id, 3)
        self.log.info("Querying CS DB : " + _query)
        self.csdb.execute(_query)
        cloud_id = self.csdb.fetch_one_row()
        if cloud_id is None:
            raise Exception("Unable to find cloud details in CS db")
        return str(cloud_id[0])

    def get_cloud_url(self, client_name):
        """Method to get search engine cloud url for the given client name

                    Args:

                        client_name    (str)   --  Name of the client where search engine package is installed

                    Returns:

                        str  -- cloud url of the search engine

                    Raises:
                        Exception:

                            if fails to find cloud url from DB
        """
        clientobj = self.commcell.clients.get(client_name)
        client_id = clientobj.client_id
        client_hostname = clientobj.client_hostname
        _query = "select portno from DM2SearchServerCoreInfo " \
                 "where ClientId={0} and CloudType={1}".format(client_id, 3)
        self.log.info("Querying CS DB : " + _query)
        self.csdb.execute(_query)
        client_portno = self.csdb.fetch_one_row()
        if client_portno is None:
            raise Exception("Unable to find cloud details in CS db")
        baseurl = f"http://{client_hostname}:{str(client_portno[0])}/solr"
        return baseurl
