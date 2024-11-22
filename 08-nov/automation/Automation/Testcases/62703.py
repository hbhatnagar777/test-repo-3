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
    __init__()                   --  initialize TestCase class

    setup()                      --  setup function of this test case

    run()                        --  run function of this test case

    tear_down()                  --  tear down function of this test case

    cleanup()                    --  Cleans up SDG entities like Inventory/Plan/Projects created earlier

    create_plan_inventory()      --  Creates Plan & Inventory for SDG Project

    add_sdg_project()            --  Adds SDG project to commcell

    get_job_id()                 --  finds latest crawl job id in SDG Project

    validate_sensitive_files()   --  Validates sensitive files count in data source for RER/NER entities

    validate_ci_on_cluster()     --  Validates whether CI used cluster or not

"""
import re
import time

from cvpysdk.activateapps.constants import TargetApps
from cvpysdk.activateapps.constants import EdiscoveryConstants as edisconstant

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.extractor_helper import ExtractingClusterHelper
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.activate_sdk_helper import ActivateSDKHelper


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
        self.name = "CE Kubernetes Cluster - Acceptance test case for creating AKS cluster and " \
                    "validating RER/NER happening via SDG crawl job"
        self.tcinputs = {
            # Please make sure client passed here has backup data with
            # Email/Person names
            "SDGClient": None,
            "IndexServer": None,
            "CACloud": None,
            "IndexGatewayClient": None,
            "IGUserName": None,
            "IGPassword": None,
            "YamlFile": None
        }
        self.ca_client_name = None
        self.sdg_client = None
        self.index_server = None
        self.plan_name = None
        self.ds_name = None
        self.inv_name = None
        self.sdg_obj = None
        self.ds_obj = None
        self.sdg_project_name = None
        self.sdk_helper = None
        self.cluster_helper = None

    def get_job_id(self):
        """finds job id of latest crawl job in SDG Project and returns it"""
        return self.sdk_helper.get_latest_job_id()

    def cleanup(self):
        """Performs cleanup operations - Deletes SDG project, plan and inventory if they already exist"""
        self.sdk_helper.do_sdg_cleanup(plan_name=self.plan_name,
                                       project_name=self.sdg_project_name,
                                       inventory_name=self.inv_name)

    def create_plan_inventory(self):
        """Creates plan and inventory for SDG"""
        self.log.info(f"Going to create SDG Plan - {self.plan_name}")
        plans_obj = self.commcell.plans
        plans_obj.add_data_classification_plan(
            plan_name=self.plan_name,
            index_server=self.index_server,
            target_app=TargetApps.SDG,
            content_analyzer=[
                self.tcinputs['CACloud']],
            entity_list=[
                dynamic_constants.ENTITY_EMAIL,
                dynamic_constants.ENTITY_PERSON])
        self.log.info("Plan got created")
        self.log.info(f"Going to create Inventory - {self.inv_name}")
        invs_obj = self.commcell.activate.inventory_manager()
        try:
            invs_obj.add(self.inv_name, self.index_server)
        except Exception:
            time.sleep(60)
            if not invs_obj.has_inventory(self.inv_name):
                invs_obj.add(self.inv_name, self.index_server)
        self.log.info(
            "Inventory got created. Waiting 4 Mins for crawl job on inventory to finish")
        time.sleep(240)
        self.log.info("Inventory crawl job got completed")

    def add_sdg_project(self):
        """Adds SDG project to commcell"""
        self.log.info(
            f"Going to create a SDG project - {self.sdg_project_name}")
        sdg_proj_obj = self.sdg_obj.add(
            project_name=self.sdg_project_name,
            inventory_name=self.inv_name,
            plan_name=self.plan_name,
        )
        self.log.info("Going to add SDG data source")
        self.ds_obj = sdg_proj_obj.add_fs_data_source(
            server_name=self.sdg_client,
            data_source_name=self.ds_name,
            source_type=edisconstant.SourceType.BACKUP
        )
        self.log.info(f"SDG data source{self.ds_name} added successfully")
        self.sdk_helper = ActivateSDKHelper(commcell_object=self.commcell,
                                            app_entity=sdg_proj_obj,
                                            data_source=self.ds_name)

    def validate_ci_on_cluster(self):
        """Validates whether CI job ran on cluster or not"""
        self.log.info(
            f"Waiting for 10mins to stats to get populated in POD logs")
        time.sleep(600)
        req_count = 0
        stats = self.cluster_helper.get_pod_logs_for_pattern(
            file_name="_stdout",
            pattern=dynamic_constants.CE_STAT_LOG_PATTERN)
        for stat in stats:
            if dynamic_constants.CE_STAT_SEARCH_TEXT_PATTERN in stat:
                self.log.info(
                    "[SEARCHTEXT] extraction stats found to extract request count")
                req_count = req_count + \
                    int(re.findall(r"Total Request\[(\d+)\]", stat)[0])
                self.log.info(f"Total request found so for - {req_count}")
        if not req_count:
            raise Exception(
                "No searchtext extraction stats found in POD logs. Please check whether CI job used cluster or not")
        self.result_string = f"{self.result_string} | Total request found in POD logs for stats [SEARCHTEXT] = {req_count}"

    def validate_sensitive_files(self):
        """Validates whether sensitive files got tagged wiht RER/NER"""
        self.log.info(
            f"Refreshing Data Source object before fetching sensitive count")
        self.ds_obj.refresh()
        if self.ds_obj.sensitive_files_count == 0:
            raise Exception(
                "Sensitive files is zero.Extraction didnt happen properly in cluster. Please check logs")
        self.log.info(
            f"Total sensitive files found : {self.ds_obj.sensitive_files_count}")
        rer_count, _, _ = self.ds_obj.search(criteria=f"{dynamic_constants.ENTITY_KEY_EMAIL}:*",
                                             params=dynamic_constants.QUERY_ZERO_ROWS)
        ner_count, _, _ = self.ds_obj.search(criteria=f"{dynamic_constants.ENTITY_KEY_PERSON}:*",
                                             params=dynamic_constants.QUERY_ZERO_ROWS)
        if rer_count == 0:
            raise Exception(f"RER entity extraction didn't happen")
        if ner_count == 0:
            raise Exception(f"NER entity extraction didn't happen")
        self.log.info(
            f"RER/NER validation passed with RER count[{rer_count}] NER count[{ner_count}]")
        self.result_string = f"Total Documents in Datasource - {self.ds_obj.total_documents} and " \
                             f"Total Sensitive files count - {self.ds_obj.sensitive_files_count} " \
                             f"No of RER - Email docs : {rer_count} " \
                             f"No of NER - Person docs : {ner_count}   |  " \
                             f"Extracting Version Image used : " \
                             f"{self.cluster_helper.get_image_info_from_yaml(yaml_file=self.tcinputs['YamlFile'],container_name=dynamic_constants.EXTRACTING_CONTAINER_NAME)}"

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Initializing all SDG Entities class objects")
        self.sdg_client = self.tcinputs['SDGClient']
        self.index_server = self.tcinputs['IndexServer']
        self.sdg_project_name = "CECluster_Project_%s" % self.id
        self.plan_name = "CECluster_TestPlan_%s" % self.id
        self.ds_name = "CECluster_DataSource_%s" % self.id
        self.inv_name = "CECluster_Inventory_%s" % self.id
        self.sdg_obj = self.commcell.activate.sensitive_data_governance()
        self.sdk_helper = ActivateSDKHelper(commcell_object=self.commcell)
        self.cluster_helper = ExtractingClusterHelper(self.commcell)
        ca_obj = self.commcell.content_analyzers.get(self.tcinputs['CACloud'])
        self.ca_client_name = self.commcell.clients.get(
            ca_obj.client_id).client_name
        self.log.info(
            f"CA cloud mapping to client : [{self.tcinputs['CACloud']}] - [{self.ca_client_name}]")
        self.cleanup()
        self.sdk_helper.set_client_wrkload_region(
            client_name=self.tcinputs['IndexGatewayClient'],
            region_name=dynamic_constants.REGION_EASTUS2)

    def run(self):
        """Run function of this test case"""
        try:
            external_ip = self.cluster_helper.create_extracting_cluster(
                name=dynamic_constants.DEFAULT_CLUSTER_NAME,
                resource_group=dynamic_constants.DEFAULT_RESOURCE_GROUP,
                location=dynamic_constants.DEFAULT_AZURE_LOCATION,
                yaml_file=self.tcinputs['YamlFile'],
                vm_size=dynamic_constants.NER_VM_SIZE)
            self.cluster_helper.set_cluster_settings_on_cs(
                extracting_ip=external_ip,
                index_gateway=self.tcinputs['IndexGatewayClient'],
                user_name=self.tcinputs['IGUserName'],
                password=self.tcinputs['IGPassword'],
                feature_type=dynamic_constants.FEATURE_TYPE_SDG)
            self.create_plan_inventory()
            # bring down CA services on client
            self.log.info("Stopping Content extractor service on CA client")
            ca_client_obj = self.commcell.clients.get(self.ca_client_name)
            ca_client_obj.stop_service(
                service_name=dynamic_constants.CE_SERVICE_NAME)
            self.log.info(
                "Stopped CE service. Proceeding with project creation")
            self.add_sdg_project()
            job_id = self.get_job_id()
            self.sdk_helper.wait_for_playback_for_cijob(
                job_id=job_id, analyze_client_id=self.commcell.clients.get(
                    self.sdg_client).client_id)
            ds_helper = DataSourceHelper(self.commcell)
            # Network errors are expected when pushing from in-lab machine to
            # cluster. So handle job status accordingly
            ds_helper.monitor_crawl_job(
                job_id=job_id,
                job_state=[
                    dynamic_constants.JOB_COMPLETE,
                    dynamic_constants.JOB_WITH_ERROR], time_limit=200)
            self.validate_sensitive_files()
            self.validate_ci_on_cluster()

        except Exception as exp:
            self.log.exception(
                'Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.cleanup()
            self.log.info("Starting Content extractor service on CA client")
            ca_client_obj = self.commcell.clients.get(self.ca_client_name)
            ca_client_obj.start_service(
                service_name=dynamic_constants.CE_SERVICE_NAME)
            self.log.info(
                f"Started CE service on CA client  - {self.ca_client_name}")
            self.log.info("Deleting cluster resource group on azure")
            self.cluster_helper.delete_resource_group(
                resource_group=dynamic_constants.DEFAULT_RESOURCE_GROUP)
            self.cluster_helper.remove_cluster_settings_on_cs(
                index_gateway=self.tcinputs['IndexGatewayClient'],
                user_name=self.tcinputs['IGUserName'],
                password=self.tcinputs['IGPassword'])
