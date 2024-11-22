# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    validate_collection()   --  Validates collection operations like create/update/search

    validate_servers()  --  Validates server api call

    validate_cores()    --  Validates the cores api call

    validate_routes()    --  Validates the routes api call

"""
import os
import time

from AutomationUtils import constants
from AutomationUtils.Performance.Utils.performance_helper import PerformanceHelper
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.utils import constants as dynamic_constants
from Kubernetes.indexserver.ClusterHelper import ClusterHelper, ClusterApiHelper
from Kubernetes.indexserver import constants as kube_constants


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Validate core status sync , Controller API[servers/cores/routes] & Delete Cluster Environment"
        self.cluster_helper = None
        self.cluster_api_helper = None
        self.cluster_ip = None
        self.index_server_name = None
        self.collection_name = None
        self.collection_doc_count = 5000

    def validate_collection(self):
        """Validates collection operations like create/update/search"""
        self.log.info(f"Collection API Validation Started")
        self.cluster_api_helper.bulk_push_data(
            collection_name=self.collection_name,
            doc_count=self.collection_doc_count,
            doc_type=kube_constants.DATA_TYPE_FILE,
            thread_count=2,
            create_collection=True,
            batch_size=100)
        _response = self.cluster_api_helper.search_collection(
            name=self.collection_name)
        if _response[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM] != self.collection_doc_count:
            raise Exception(
                f"Collection Validation failed. Document count Pushed : [{self.collection_doc_count}] but search yielded only : [{_response[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM]}] docs")
        self.log.info(
            f"Document count in solr - {_response[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM]}")
        self.log.info(f"Collection API Validation Passed")

    def validate_servers(self):
        """Validates servers api call from dkubectrlr"""
        self.log.info(f"Server API Validation Started")
        _servers = self.cluster_api_helper.get_servers(dump_in_log=True)
        total_cores = 0
        for _each_srv in _servers:
            loaded_cores = _each_srv[kube_constants.FIELD_CORES]
            for key, value in loaded_cores.items():
                if self.collection_name in key:
                    self.log.info(
                        f"Found Server POD hosting the collection core [{key}] in server - {_each_srv[kube_constants.FIELD_SERVER_ID]}")
                    total_cores = total_cores + 1

        if total_cores != 8:
            raise Exception(
                f"Found so many cores name matching the collection. Something wrong. Please check logs")
        self.log.info(
            f"Total cores in solr for this collection - {total_cores}")
        self.log.info(f"Server API Validation Passed")

    def validate_cores(self):
        """Validates the cores api call"""
        self.log.info("Cores API Validation Started")
        _cores = self.cluster_api_helper.get_cores(dump_in_log=True)
        total_docs = 0
        for _each_core in _cores:
            if self.collection_name == _each_core[kube_constants.FIELD_CV_COLLECTION]:
                self.log.info(
                    f"Core[{_each_core[kube_constants.FIELD_NAME]}] found with doc count [{_each_core[kube_constants.FIELD_CORE_DOCS]}]")
                total_docs = total_docs + \
                    _each_core[kube_constants.FIELD_CORE_DOCS]
        if total_docs != self.collection_doc_count:
            raise Exception(
                f"Cores API returns wrong doc count for collection. Expected[{self.collection_doc_count}] Actual[{total_docs}]")
        self.log.info(f"Total docs in solr - {total_docs}")
        self.log.info("Cores API Validation Passed")

    def validate_routes(self):
        """Validates the routes api call"""
        self.log.info("Routes API Validation Started")
        _stats = self.cluster_api_helper.get_loaded_collection_stats(
            dump_in_log=True)
        if self.collection_name not in _stats:
            raise Exception(
                f"Collection is not in loaded status. Please check logs")
        if _stats[self.collection_name][kube_constants.FIELD_TOTAL_CORE_DOCS] != self.collection_doc_count:
            raise Exception(
                "Document count mismatched in Routes API call. Please check logs")
        self.log.info("Routes API Validation Passed")

    def setup(self):
        """Setup function of this test case"""
        self.cluster_helper = ClusterHelper(self.commcell)
        self.collection_name = f"AutomationCollection_{self.id}"
        self.cluster_ip, self.index_server_name = self.cluster_helper.get_cluster_ip_from_setup()
        self.log.info(
            f"Index server cluster ip : {self.cluster_ip} & Index server is : {self.index_server_name}")
        self.cluster_api_helper = ClusterApiHelper(
            commcell_object=self.commcell, cluster_ip=self.cluster_ip)
        if not os.path.exists(self.cluster_helper.result_json_file):
            raise Exception(
                f"No results file exists - {self.cluster_helper.result_json_file}")

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Analyzing results file for final status")
            perf_helper = PerformanceHelper(commcell_object=self.commcell)
            _result_json = perf_helper.read_json_file(
                json_file=self.cluster_helper.result_json_file)
            for _each_result in _result_json:
                if _result_json[_each_result] == constants.FAILED:
                    raise Exception(
                        f"Results file contains failed status for Test case : [{_each_result}]")
            self.log.info("All cases are PASSED.")

            # Validate API calls
            self.validate_collection()
            self.validate_servers()
            self.log.info(
                "Waiting for 15mins for core sync status thread to populate core status")
            # wait for 15mins for core status sync to happen
            time.sleep(900)
            self.validate_cores()
            self.validate_routes()

            # delete the cluster

            self.cluster_helper.delete_resource_group(
                resource_group=kube_constants.DEFAULT_IS_RESOURCE_GROUP)
            on_error = False
            try:
                _servers = self.cluster_api_helper.get_servers(
                    dump_in_log=True)
            except Exception:
                self.log.info(f"Cluster Deleted")
                on_error = True
            if not on_error:
                raise Exception(
                    "Cluster IP accessible even after deletion. Please check")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
