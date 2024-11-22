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

"""
import time

from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.extractor_helper import ExtractingClusterHelper
from dynamicindex.utils import constants as dynamic_constants


_CONFIG_DATA = get_config().DynamicIndex.ExtractingCluster


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
        self.name = "CE Kubernetes Cluster - Validate POD restart by manually stopping CV services in POD"
        self.tcinputs = {
        }
        self.kube_master = None
        self.cluster_helper = None

    def setup(self):
        """Setup function of this test case"""
        self.cluster_helper = ExtractingClusterHelper(self.commcell)
        self.kube_master = self.cluster_helper.kube_master
        start_time = time.time()
        self.cluster_helper.create_extracting_cluster(
            name=dynamic_constants.DEFAULT_CLUSTER_NAME,
            resource_group=dynamic_constants.DEFAULT_RESOURCE_GROUP,
            location=dynamic_constants.DEFAULT_AZURE_LOCATION,
            yaml_file=self.tcinputs['YamlFile'])
        end_time = time.time()
        self.result_string = f"Cluster Creation & Kubernetes setup on client took [{int(end_time-start_time)}] seconds"

    def run(self):
        """Run function of this test case"""
        try:
            pods = None
            start_time = time.time()
            time_limit = start_time + 12 * 60  # 12mins as image needs to be downloaded for deployment
            while True:
                if time.time() >= time_limit:
                    raise Exception(f"Time limit reached while waiting for POD to be ready after cluster creation")
                pods = self.kube_master.get_pods(status="Running", ready_only=True)
                if len(pods) != 0:
                    end_time = time.time()
                    self.result_string = f"{self.result_string} | After cluster Creation module call, POD came to ready state in [{int(end_time-start_time)}] seconds | "
                    break
                time.sleep(5)
            self.log.info(f"Total running PODS - {len(pods)}")
            if len(pods) > 1:
                raise Exception("More PODS found in cluster in ready state than required minimum of 1")
            pod_name = pods[0]
            if not pod_name.startswith(dynamic_constants.EXTRACTING_SERVICE_NAME):
                raise Exception(f"POD name didn't start with cvextractor. Pod name is - {pod_name}")
            self.log.info("Pod name validation : success")
            self.log.info(f"Going to kill java process on POD [{pod_name}]")
            pid_list = self.kube_master.run_cmd_on_pod(
                pod_name=pod_name,
                command=f"ps -C java -o pid=", format=True)
            if not pid_list:
                raise Exception("Failed to find Java pid")
            self.log.info(f"java is running with Pid - {pid_list}")
            total_killed = 0
            for pid in pid_list:
                pid = pid.strip()
                self.log.info(f"Killing java with Pid - {pid}")
                try:
                    self.kube_master.run_cmd_on_pod(
                        pod_name=pod_name,
                        command=f"kill -9 {pid}")
                    total_killed = total_killed + 1
                except Exception:
                    continue
            if not total_killed:
                raise Exception(
                    "Failed to kill any of the java process in POD")
            self.log.info(
                f"Waiting for POD to come down as we stopped java processes")
            start_time = time.time()
            end_time = None
            # 3mins as we have retry in ping check for content extractor
            # service
            time_limit = start_time + 3 * 60
            while True:
                if time.time() >= time_limit:
                    raise Exception(
                        f"Time limit reached while waiting for POD to go down")
                new_pods = self.kube_master.get_pods(
                    status="Running", ready_only=True)
                self.log.info(
                    f"Count of new pod [{len(new_pods)}] old pod [{len(pods)}]")
                if pod_name not in new_pods:
                    self.log.info("POD came down as expected")
                    end_time = time.time()
                    self.result_string = f"{self.result_string} | After java service shutdown, " \
                                         f"POD came down in [{int(end_time-start_time)}] seconds"
                    self.log.info(self.result_string)
                    break

            self.log.info(
                f"Waiting for POD to come up after restart signal by load balancer cluster")
            start_time = time.time()
            time_limit = start_time + 5 * 60  # Machine POD restart
            while True:
                if time.time() >= time_limit:
                    raise Exception(
                        f"Time limit reached while waiting for POD to come up as running")
                new_pods = self.kube_master.get_pods(
                    status="Running", ready_only=True)
                self.log.info(
                    f"Count of new pod [{len(new_pods)}] old pod [{len(pods)}]")
                if pod_name in new_pods:
                    self.log.info("POD came up after restart as expected")
                    end_time = time.time()
                    self.result_string = f"{self.result_string}  | After restart signal, " \
                                         f"POD came to ready state in [{int(end_time-start_time)}] seconds"
                    self.log.info(self.result_string)
                    break

        except Exception as exp:
            self.log.exception('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("Deleting cluster resource group on azure")
            self.cluster_helper.delete_resource_group(resource_group=dynamic_constants.DEFAULT_RESOURCE_GROUP)
