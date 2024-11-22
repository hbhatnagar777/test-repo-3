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

    validate_max_cores()    --  Validates max number of cores per pod

    apply_yaml()            --  applies configuration change yaml to cluster

    validate_unload()       --  Validates unload collection happens

    validate_load()         --  Validates load collection happens for unloaded collection

    validate_delete()       --  validates collection deletion

"""
import time

from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Kubernetes.indexserver.ClusterHelper import ClusterHelper, ClusterApiHelper
from Kubernetes.indexserver import constants as kube_constants

_CONFIG_DATA = get_config().DynamicIndex.IndexServerCluster


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
        self.name = "Validate ServerPickCriteria - MaxNumCores and automatic unload collection"
        self.tcinputs = {
        }
        self.cluster_helper = None
        self.cluster_api_helper = None
        self.cluster_ip = None
        self.index_server_name = None
        self.collection_name = None
        self.collection_name_idle = None
        self.collection_doc_count = 500
        self.idle_collection_servers = []

    def validate_delete(self):
        """Validates delete collection on cluster"""
        self.log.info("Deleting the collection created")
        self.cluster_api_helper.delete_collection(
            name=self.collection_name)
        self.cluster_api_helper.delete_collection(
            name=self.collection_name_idle)
        _collections = self.cluster_api_helper.get_loaded_collection_stats(
            dump_in_log=True)
        if self.collection_name in _collections or self.collection_name_idle in _collections:
            raise Exception(
                "Deleted collections is still shown as Loaded. Please check")
        self.log.info("Delete collection validation Passed")
        self.result_string = f"{self.result_string} | Collection delete succeeded for both idle and working collections "

    def validate_load(self):
        """Validates load of collection happens or not"""
        self.cluster_api_helper.ping_collection(name=self.collection_name_idle)
        _response = self.cluster_api_helper.search_collection(
            name=self.collection_name_idle)
        _numfound = _response[kube_constants.FIELD_RESPONSE][kube_constants.FIELD_NUMFOUND]
        if self.collection_doc_count != _numfound:
            raise Exception(
                f"Loaded collection numfound[{_numfound}] is not matching with generated data[{self.collection_doc_count}]")
        self.log.info("Load collection validation Passed")
        self.result_string = f"{self.result_string} | Load collection req loaded the collection and search returned expected Document count - {_numfound}"

    def validate_unload(self):
        """Validates automatic unload of collection happens or not"""
        # core status thread timer is 5mins. Our idle timeout config
        # is 3mins and idle collection thread is 1.5 times of core status sync thread timer
        self.log.info(
            f"Waiting for 25mins for automatic unload collection to happen for "
            f"idle collection[{self.collection_name_idle}]. In Parallel querying "
            f"working collection - {self.collection_name}")
        cur_time = None
        wait_time = time.time() + 25 * 60
        while True:
            cur_time = time.time()
            if cur_time > wait_time:
                self.log.info("Wait time is over")
                break
            self.cluster_api_helper.search_collection(
                name=self.collection_name)
            time.sleep(120)
        _collections = self.cluster_api_helper.get_loaded_collection_stats(
            dump_in_log=True)
        if self.collection_name not in _collections or self.collection_name_idle in _collections:
            raise Exception(
                "Automatic unload of collection didnt happen properly. Please check logs")
        self.log.info(
            f"Idle collection[{self.collection_name_idle}] got unloaded successfully and Working collection[{self.collection_name}] retained in POD")
        self.log.info(
            f"Wait for 1.5 times of {kube_constants.CORE_STATUS_SYNC_IN_MINS}mins for server to go down")
        time.sleep((kube_constants.CORE_STATUS_SYNC_IN_MINS +
                   kube_constants.CORE_STATUS_SYNC_IN_MINS / 2) * 60)
        servers = self.cluster_api_helper.get_servers(dump_in_log=True)
        _server_down_detected = False
        running_servers = []
        for _server in servers:
            running_servers.append(_server[kube_constants.FIELD_SERVER_ID])

        for idle_server in self.idle_collection_servers:
            if idle_server not in running_servers:
                self.log.info(
                    f"Server[{idle_server}] which hosted Idle collection is not up and running")
                _server_down_detected = True
            else:
                self.log.info(
                    f"Server[{idle_server}] which hosted Idle collection is up and running")

        if not _server_down_detected:
            raise Exception(
                "Servers which hosted Idle collection is still up and running")

        self.log.info("Unload collection validation Passed")
        self.result_string = f"{self.result_string} | Idle collection[{self.collection_name_idle}] got unloaded successfully whereas querying working collection[{self.collection_name}] retained in POD"

    def apply_yaml(self, yaml_file):
        """applies configuration change yaml file to cluster"""
        self.cluster_helper.apply_yaml_do_rollout(yaml_file=yaml_file)

    def validate_max_cores(self):
        """validates max number of cores per pod got honoured or not"""
        self.cluster_api_helper.bulk_push_data(
            collection_name=self.collection_name,
            doc_count=self.collection_doc_count,
            doc_type=kube_constants.DATA_TYPE_FILE,
            thread_count=2,
            create_collection=True,
            batch_size=100, num_cores=8)
        self.cluster_api_helper.bulk_push_data(
            collection_name=self.collection_name_idle,
            doc_count=self.collection_doc_count,
            doc_type=kube_constants.DATA_TYPE_FILE,
            thread_count=2,
            create_collection=True,
            batch_size=100, num_cores=8)
        servers = self.cluster_api_helper.get_servers(dump_in_log=True)
        self.log.info(f"Created two collection with 8 core shards")

        for server in servers:
            loaded_cores = server[kube_constants.FIELD_CORES]
            for core_name in loaded_cores:
                if core_name.startswith(self.collection_name_idle):
                    if server[kube_constants.FIELD_SERVER_ID] not in self.idle_collection_servers:
                        self.idle_collection_servers.append(
                            server[kube_constants.FIELD_SERVER_ID])
                        self.log.info(
                            f"Idle collection found in Server id - {server[kube_constants.FIELD_SERVER_ID]}")
        if len(self.idle_collection_servers) != 2:
            raise Exception(
                "Max number of cores pick criteria failed. Please check logs")
        self.log.info(
            f"Idle collection got loaded in two different servers - {self.idle_collection_servers}")
        self.log.info("MaxNumCores per Pod validation Passed")
        self.result_string = f"Created two collection with 8 shards each. 2nd collection got loaded in {len(self.idle_collection_servers)}servers due to MaxNUmCore Limit (10)"

    def setup(self):
        """Setup function of this test case"""
        self.cluster_helper = ClusterHelper(self.commcell)
        self.collection_name = f"AutomationCollection_{int(time.time())}_{self.id}"
        self.collection_name_idle = f"AutomationCollection_idle_{int(time.time())}_{self.id}"
        self.cluster_ip, self.index_server_name = self.cluster_helper.get_cluster_ip_from_setup()
        self.log.info(
            f"Index server cluster ip : {self.cluster_ip} & Index server is : {self.index_server_name}")
        self.cluster_api_helper = ClusterApiHelper(
            commcell_object=self.commcell, cluster_ip=self.cluster_ip)

    def run(self):
        """Run function of this test case"""
        try:
            yaml_file = self.cluster_helper.update_config_map(
                yaml_file=_CONFIG_DATA.CommonInputs.YamlFile,
                update_dict=kube_constants.SERVER_PICK_CRITERIA_MAX_CORES_AND_UNLOAD_CORES)
            self.apply_yaml(yaml_file=yaml_file)
            self.validate_max_cores()
            self.validate_unload()
            self.validate_load()
            self.validate_delete()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.cluster_helper.update_test_status_json(
            test_id=self.id, status=self.status)
        if self.status == constants.PASSED:
            self.log.info(
                "Reverting the cluster to original cluster configuration")
            self.apply_yaml(
                yaml_file=_CONFIG_DATA.CommonInputs.YamlFile)
