# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for datacube solr related queries

    SolrHelper:
        __init__(testcase)          --  Initialize the DcubesolrHelper object

        get_coreid_datasource(datasourceid)   --  get coreid for given datasource id

        get_solr_baseurl(clientname,cloudtype) --  Returns the base solr url for
                                                given clientname and cloudtype

        get_corestats(baseurl,corename)      --  Get core stats for given corename in solr

        get_fs_sync_facets(baseurl,corename)  --  Get sync facets for given
                                                FS data source core


        do_hard_commit(self,baseurl)          -- to do hard commit for given solr core

"""
from dynamicindex.utils import constants as dynamic_constants


class SolrHelper():
    """ contains helper class for datacube solr related queries
    """

    def __init__(self, tc_object):
        self.commcell = tc_object.commcell
        self.csdb = tc_object.csdb
        self.log = tc_object.log

    def get_coreid_datasource(self, datasourceid):
        """Returns the coreid of the given datasource id

        Args:
            datasourceid(str)      --  id of the datasource

        Returns

            str - core id of datasource

        Raises

            Exception on failure to find details


        """
        _query = "select coreid from sedatasource where datasourceid=" + \
                 datasourceid
        self.log.info("Querying CS DB to get coreid for datasource id %s", str(datasourceid))
        self.csdb.execute(_query)
        dbresults = self.csdb.fetch_one_row()
        if dbresults:
            return dbresults[0]
        raise Exception("Unable to find coreid for given datasource id")

    def get_solr_baseurl(self, clientname, cloudtype):
        """Returns the base solr url for given clientname and cloudtype

        Args:
            clientname(str)      --  Name of the client
            Cloudtype(int)      --  Type of cloud.
                valid values are
                    1-Analytics,
                    2-Search engine
                    3-CA cloud

        Returns

            str - solr base url on success

        Raises

            Exception on failure to find details


        """
        clientobj = self.commcell.clients.get(clientname)
        client_id = clientobj.client_id
        client_hostname = clientobj.client_hostname
        _query = "select portno from DM2SearchServerCoreInfo " \
                 "where ClientId={0} and CloudType={1}".format(client_id, cloudtype)
        self.log.info("Querying CS DB : " + _query)
        self.csdb.execute(_query)
        client_portno = self.csdb.fetch_one_row()
        if client_portno is None:
            raise Exception("Unable to find cloud details in CS db")
        baseurl = f"http://{client_hostname}:{str(client_portno[0])}"
        if cloudtype in [1, 2, 5]:
            baseurl += '/solr'
        return str(baseurl)

    def get_corestats(self, baseurl, corename):
        """Returns solr stats info for given corename

               Args:
                   baseurl(str)       -- solr base url
                        Example : http://#####:20000/solr
                   corename(str)      --  Name of the solr Core

               Returns

                   dict     -- Core stats

               Raises

                   Exception on failure to find details


               """
        baseurl = baseurl + "/admin/cores?wt=json"
        self.log.info("Querying solr : " + baseurl)
        flag, response = self.commcell._cvpysdk_object.make_request("GET", baseurl)
        if flag:
            if 'status' in response.json():
                return response.json()['status'][corename]
            raise Exception("Unable to find status object in response")
        raise Exception("Unable to get core stats for given corename : " + response.text)

    def get_fs_sync_facets(self, baseurl, corename):
        """Returns solr facets (source,users,size) info for given FS corename

                       Args:
                           corename(str)      --  Name of the solr Core
                           baseurl(str)       -- solr base url
                                Example : http://#####:20000/solr

                       Returns

                           dict     -- facets response

                       Raises

                           Exception on failure to find details


                       """
        stats = {}
        call_url = baseurl + "/" + corename + \
            "/select?q=NOT(ItemState:3334 OR cistate:3334)&wt=json&rows=0&json.facet=" \
            "{\"Users\":\"unique(OwnerSID)\"," \
            "\"Size\":\"sum(Size)\"," \
            "\"Source\": \"unique(Source)\", " \
            "\"EntitiesCount\": {query:\"entities_extracted:*\"}," \
            " \"FilesCount\": {query:\"DocumentType:1\"}}"
        self.log.info("Querying Solr : " + call_url)
        flag, response = self.commcell._cvpysdk_object.make_request("GET", call_url)
        if flag:
            if 'facets' in response.json():
                stats.update({
                    dynamic_constants.SYNC_TOTAL_PARAM: response.json()['facets']
                })
            else:
                raise Exception("Unable to find facets object in response")
        else:
            raise Exception("Unable to get FS solr core stats for given corename : " + response.text)

        call_url = baseurl + "/" + corename + \
            "/select?q=(cistate:1 OR ItemState:1)&wt=json&rows=0&json.facet=" \
            "{\"Users\":\"unique(OwnerSID)\"," \
            "\"Size\":\"sum(Size)\"," \
            "\"Source\": \"unique(Source)\", " \
            "\"EntitiesCount\": {query:\"entities_extracted:*\"}," \
            " \"FilesCount\": {query:\"DocumentType:1\"}}"
        self.log.info("Querying Solr : " + baseurl)
        flag, response = self.commcell._cvpysdk_object.make_request("GET", call_url)
        if flag:
            if 'facets' in response.json():
                stats.update({
                    dynamic_constants.SYNC_SUCCESS_STATE_PARAM: response.json()['facets']
                })
            else:
                raise Exception("Unable to find facets object in response")
        else:
            raise Exception("Unable to get FS solr core stats for given corename : " + response.text)
        return stats

    def do_hard_commit(self, baseurl):
        """do hard commit for the given solr core url

                Args:
                    baseurl(str)      --  solr core url
                        Example : http://#####:20000/solr

                Raises

                    Exception on failure to commit solr core
        """
        baseurl = baseurl + "/update?commit=true"
        self.log.info("Sending Commit to  Solr : " + baseurl)
        flag, response = self.commcell._cvpysdk_object.make_request("GET", baseurl)
        if flag and response.json():
            if 'error' in response.json():
                self.log.info(str(response))
                raise Exception("Hard commit returned error")
            if 'responseHeader' in response.json():
                commitstatus = str(response.json()['responseHeader']['status'])
                self.log.info(
                    "commit response : " + commitstatus)
                if(int(commitstatus) != 0):
                    raise Exception("Hard commit returned bad status")

        else:
            self.log.info(str(response.text))
            raise Exception("Something went wrong with hard commit")

    def get_solr_jvm_memory(self, baseurl, in_bytes=False):
        """Returns the Solr JVM max memory

        Args:
            baseurl     (str)   -   Solr base URL
            in_bytes    (bool)  -   if true then returns memory in Bytes else returns in MB
                default- False

        Returns:
            int     -   Solr jvm memory

        """
        baseurl = baseurl + "/admin/metrics?group=jvm&wt=json"
        self.log.info("Querying Solr : " + baseurl)
        flag, response = self.commcell._cvpysdk_object.make_request("GET", baseurl)
        if flag:
            if response.json() and "metrics" in response.json():
                if 'solr.jvm' in response.json()['metrics']:
                    metrics_data = response.json()['metrics']['solr.jvm']
                    if "memory.heap.init" in metrics_data:
                        jvm_mem = int(metrics_data['memory.total.max'])
                        if in_bytes:
                            return jvm_mem
                        return jvm_mem // 1048576
                    raise Exception("Unable to find the max heap object in response")
                raise Exception("Unable to get solr jvm object in response")
            raise Exception("Unable to find metrics object in response")
        raise Exception("Unable to get java memory details for given solr")
