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

    validate_load_collection()  --  Validates metadata only collection load and benchmark metrics

    validate_search()           --  Validates searches on collection and benchmark metrics

    validate_push()             --  Validates push document on collection and benchmark metrics

    tear_down()     --  tear down function of this test case

"""
import calendar
import datetime
import os
import random
import time

from AutomationUtils import constants, commonutils
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.Performance.Utils.constants import GeneralConstants
from Kubernetes.indexserver.ClusterHelper import ClusterApiHelper
from Kubernetes.akscluster_helper import AksClientHelper
from Kubernetes.kubectl_helper import KubectlHelper
from Kubernetes.indexserver import constants as ctrl_const
from dynamicindex.utils import constants as dynamic_constants


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
        self.name = "Index Server k8s - Performance metrics for metadata collection load"
        self.tcinputs = {
            "ClusterName": None,
            "ResourceGroupName": None,
            "CollectionName": None
        }
        self.cluster_name = None
        self.rs_group = None
        self.collection = None
        self.cluster_api_obj = None
        self._wait_interval = 60
        self._search_count = 30
        self._push_thread = 10
        self._add_doc = 5000000
        self._br_tag = '<br>'
        self._option_selector = None
        self.build_id = int(calendar.timegm(time.gmtime()))

    def setup(self):
        """Setup function of this test case"""
        self._option_selector = OptionsSelector(self.commcell)
        self.cluster_name = self.tcinputs['ClusterName']
        self.rs_group = self.tcinputs['ResourceGroupName']
        self.collection = self.tcinputs['CollectionName']
        self.az_master = AksClientHelper(
            self._commcell,
            machine_name=_CONFIG_DATA.AZMachine.name,
            user_name=_CONFIG_DATA.AZMachine.username,
            password=_CONFIG_DATA.AZMachine.password,
            service_principal={
                dynamic_constants.FIELD_APPID: _CONFIG_DATA.AzureAdServicePrincipals.appId,
                dynamic_constants.FIELD_PASSWORD: _CONFIG_DATA.AzureAdServicePrincipals.password,
                dynamic_constants.FIELD_TENANT: _CONFIG_DATA.AzureAdServicePrincipals.tenant},
            subscription_id=_CONFIG_DATA.AzureSubscription)
        self.log.info("Initialized AksClientHelper object")
        self.kube_master = KubectlHelper(
            self._commcell,
            machine_name=_CONFIG_DATA.KubectlMachine.name,
            user_name=_CONFIG_DATA.KubectlMachine.username,
            password=_CONFIG_DATA.KubectlMachine.password)
        self.log.info("Initialized KubectlHelper object")
        self.az_master.get_credentials(cluster_name=self.cluster_name, resource_group=self.rs_group)
        # check status of cluster and start it
        self.az_master.cluster_ops(cluster_name=self.cluster_name, resource_group=self.rs_group, is_start=True)
        time.sleep(self._wait_interval * 20)
        # find the cluster ip
        ip = self.kube_master.get_service(
            service_name=ctrl_const.TRAEFIK_SERVICE_NAME,
            name_space=ctrl_const.IS_NAME_SPACE)
        ip = ip[dynamic_constants.FIELD_STATUS][dynamic_constants.FIELD_LOADBALANCER][
            dynamic_constants.FIELD_INGRESS][0][dynamic_constants.FIELD_EXTERNAL_IP]
        if not ip:
            raise Exception("Failed to get index server cluster IP")
        self.log.info(f"Initialising the cluster API helper class with IP : {ip}")
        self.cluster_api_obj = ClusterApiHelper(commcell_object=self.commcell, cluster_ip=ip)

    def validate_push(self):
        """Validates document add to collection and benchmark metrics"""
        _thread_obj, _push_stats_folder = self.kube_master.monitor_pod_metrics(name_space=ctrl_const.IS_NAME_SPACE)
        _start = datetime.datetime.now()
        self.cluster_api_obj.bulk_push_data(collection_name=self.collection,
                                            doc_count=self._add_doc,
                                            doc_type=dynamic_constants.FIELD_FILE,
                                            thread_count=self._push_thread,
                                            create_collection=False)
        _end = datetime.datetime.now()
        _total_time = round((_end - _start).total_seconds() / 60, 2)
        self.log.info("Push Validation done")
        time.sleep(self._wait_interval)
        self.kube_master.stop_monitor_threads = True
        _push_stats = self.kube_master.analyze_metrics(
            folder=_push_stats_folder, push_to_datasource=True, Build_Id=self.build_id, Export=True)
        self.result_string = f"{self.result_string}{self._br_tag}" \
                             f"{'*' * 50} Document Push Performance {'*' * 50}{self._br_tag}{self._br_tag}" \
                             f"Total Parallel Thread : {self._push_thread}{self._br_tag}" \
                             f"Total documents added : {self._add_doc}{self._br_tag}" \
                             f"Total time take to push document : {_total_time} Mins (i.e {self._option_selector.convert_no((self._add_doc/_total_time)*60)} docs/hr){self._br_tag}{self._br_tag}" \
                             f"POD metrics while pushing documents: {self._br_tag}{self._br_tag}{commonutils.convert_json_to_html(_push_stats)}"

    def validate_search(self):
        """runs random searches on collection and benchmark metrics"""
        _success_hits = 0
        _thread_obj, _search_stats_folder = self.kube_master.monitor_pod_metrics(name_space=ctrl_const.IS_NAME_SPACE)
        while _success_hits <= self._search_count:
            _resp = self.cluster_api_obj.search_collection(name=self.collection, select_dict={
                                                           dynamic_constants.CLIENT_ID_PARAM: random.randint(0, 2000)})
            if _resp[ctrl_const.FIELD_RESPONSE][ctrl_const.FIELD_NUMFOUND] > 0:
                _success_hits = _success_hits + 1
                self.log.info(f"Total Success hits count : {_success_hits}")
                if _success_hits > self._search_count:
                    break
            _resp = self.cluster_api_obj.search_collection(name=self.collection, select_dict={
                dynamic_constants.SIZE_ON_DISK_BYTES_PARAM: f"[0 TO {random.randint(100, 922337203685477580)}]"})
            if _resp[ctrl_const.FIELD_RESPONSE][ctrl_const.FIELD_NUMFOUND] > 0:
                _success_hits = _success_hits + 1
                self.log.info(f"Total Success hits count : {_success_hits}")
                if _success_hits > self._search_count:
                    break

            _resp = self.cluster_api_obj.search_collection(name=self.collection, select_dict={
                dynamic_constants.FILTER_EXTENSION: random.choice(dynamic_constants.FILE_TYPES_DATA_GEN)})
            if _resp[ctrl_const.FIELD_RESPONSE][ctrl_const.FIELD_NUMFOUND] > 0:
                _success_hits = _success_hits + 1
                self.log.info(f"Total Success hits count : {_success_hits}")
                if _success_hits > self._search_count:
                    break

            _resp = self.cluster_api_obj.search_collection(name=self.collection, select_dict={
                dynamic_constants.FIELD_CLIENT_NAME: f"dikube{random.randint(0,50)}"})
            if _resp[ctrl_const.FIELD_RESPONSE][ctrl_const.FIELD_NUMFOUND] > 0:
                _success_hits = _success_hits + 1
                self.log.info(f"Total Success hits count : {_success_hits}")
                if _success_hits > self._search_count:
                    break

            _resp = self.cluster_api_obj.search_collection(name=self.collection, select_dict={
                dynamic_constants.FIELD_JOB_ID: random.randint(0, 1000)})
            if _resp[ctrl_const.FIELD_RESPONSE][ctrl_const.FIELD_NUMFOUND] > 0:
                _success_hits = _success_hits + 1
                self.log.info(f"Total Success hits count : {_success_hits}")
                if _success_hits > self._search_count:
                    break
        self.log.info("Search Validation done")
        time.sleep(self._wait_interval)
        self.kube_master.stop_monitor_threads = True
        _search_stats = self.kube_master.analyze_metrics(
            folder=_search_stats_folder)
        self.result_string = f"{self.result_string}{self._br_tag}" \
                             f"{'*' * 50} Search Performance {'*' * 50}{self._br_tag}{self._br_tag}" \
                             f"Total Searches Performed : {self._search_count}{self._br_tag}{self._br_tag}" \
                             f"POD metrics while running searches: {self._br_tag}{self._br_tag}{commonutils.convert_json_to_html(_search_stats)}"

    def validate_load_collection(self):
        """Validates metadata collection load and benchmark metrics"""
        _thread_obj, _before_stats_folder = self.kube_master.monitor_pod_metrics(name_space=ctrl_const.IS_NAME_SPACE)
        time.sleep(self._wait_interval)
        self.kube_master.stop_monitor_threads = True
        _before_stats = self.kube_master.analyze_metrics(folder=_before_stats_folder)
        _thread_obj, _after_stats_folder = self.kube_master.monitor_pod_metrics(name_space=ctrl_const.IS_NAME_SPACE)
        self.log.info(f"Going to load collection - {self.collection}")
        self.cluster_api_obj.ping_collection(name=self.collection, do_search=True)
        time.sleep(self._wait_interval)
        self.kube_master.stop_monitor_threads = True
        _after_stats = self.kube_master.analyze_metrics(
            folder=_after_stats_folder)
        _collection_stats = self.cluster_api_obj.get_loaded_collection_stats(dump_in_log=True)[self.collection]
        self.result_string = f"{self.result_string}{'*' * 50} Collection Load Performance {'*' * 50}{self._br_tag}{self._br_tag}" \
                             f"Collection Type : Metadata only {self._br_tag} " \
                             f"Collection Name : {self.collection}{self._br_tag} " \
                             f"Total Docs : {_collection_stats[ctrl_const.FIELD_TOTAL_CORE_DOCS_STR]}{self._br_tag}" \
                             f"Index Size : {_collection_stats[ctrl_const.FIELD_TOTAL_CORE_SIZE_STR]}{self._br_tag}" \
                             f"Loaded DCube Server ID : {_collection_stats[ctrl_const.FIELD_ALL_CORE_SERVER_ID]}{self._br_tag}{self._br_tag}" \
                             f"Before collection load POD Stats: {self._br_tag}{self._br_tag}{commonutils.convert_json_to_html(_before_stats)}{self._br_tag} " \
                             f"After collection load POD Stats: {self._br_tag}{self._br_tag} {commonutils.convert_json_to_html(_after_stats)}"
        self.log.info("Load Validation done")

    def run(self):
        """Run function of this test case"""
        try:
            self.result_string = f"POD Image : {self.cluster_api_obj.get_image_info_from_deployment(yaml_dict=self.kube_master.get_deployments(name_space=ctrl_const.IS_NAME_SPACE),container_name=ctrl_const.IS_CONTROLLER_DEPLOYMENT)} {self._br_tag} {self._br_tag}"
            self.validate_load_collection()
            self.validate_search()
            self.validate_push()
            report_folder = os.path.join(GeneralConstants.CONTROLLER_FOLDER_PATH,
                                         str(self.build_id),
                                         GeneralConstants.CONTROLLER_REPORTS_FOLDER_NAME,
                                         GeneralConstants.CONTROLLER_EXPORT_HTML_FOLDER_NAME)
            report_share_folder = os.path.join(GeneralConstants.CONTROLLER_SHARE_FOLDER_PATH,
                                               str(self.build_id),
                                               GeneralConstants.CONTROLLER_REPORTS_FOLDER_NAME,
                                               GeneralConstants.CONTROLLER_EXPORT_HTML_FOLDER_NAME)
            report_files = []
            self.result_string = f"{self.result_string}{self._br_tag}{self._br_tag}{'*' * 50} Final Exported HTML Reports Location for Document push operation {'*' * 50}{self._br_tag}{self._br_tag}"
            self.result_string = f'{self.result_string}<a href="{report_share_folder}">Open Exported HTML Reports from controller</a>'
            try:
                for filename in os.listdir(report_folder):
                    _file = os.path.join(report_folder, filename)
                    # checking if it is a file
                    if os.path.isfile(_file):
                        self.log.info(f"Attaching report file {_file} to mailer")
                        report_files.append(_file)
                self.attachments = report_files
            except Exception as ep:
                self.log.info("Unable to attach reports to mailer")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("Shutting down the cluster")
            self.cluster_api_obj.unload_collection(collection_name=self.collection)
            self.az_master.cluster_ops(cluster_name=self.cluster_name, resource_group=self.rs_group, is_start=False)
