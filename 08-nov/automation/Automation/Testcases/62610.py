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
    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  tear down function of this test case

    cleanup()                   --  Cleans up SDG entities like Inventory/Plan/Projects created earlier

    create_plan_inventory()     --  Creates Plan & Inventory for SDG Project

    add_sdg_project()           --  Adds SDG project to commcell

    validate_sensitive_count()  --  Validates sentitive files count found on path

    get_job_id()                --  finds latest crawl job id in SDG Project

"""
import time

from cvpysdk.activateapps.constants import TargetApps
from cvpysdk.activateapps.constants import EdiscoveryConstants as edisconstant
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from dynamicindex.activate_sdk_helper import ActivateSDKHelper
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.content_analyzer_helper import ContentAnalyzerHelper
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper


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
        self.name = "Validate SDG local crawl job for multiple windows CA in plan"
        self.tcinputs = {
            "CAClouds": None,
            "SDGClient": None,
            "IndexServer": None
        }
        self.ca_list = []
        self.sdg_client = None
        self.path = None
        self.index_server = None
        self.plan_name = None
        self.ds_name = None
        self.inv_name = None
        self.plans_obj = None
        self.invs_obj = None
        self.sdg_obj = None
        self.ds_obj = None
        self.all_ds_obj = None
        self.ds_helper = None
        self.sdg_project_name = None
        self.ca_helper = None
        self.crawl_helper = None
        self.sdk_helper = None

    def cleanup(self):
        """Performs cleanup operations - Deletes SDG project, plan and inventory if they already exist"""
        self.sdk_helper.do_sdg_cleanup(plan_name=self.plan_name,
                                       project_name=self.sdg_project_name,
                                       inventory_name=self.inv_name)

    def create_plan_inventory(self):
        """Creates plan and inventory for SDG"""
        self.log.info(f"Going to create SDG Plan - {self.plan_name}")
        self.plans_obj.add_data_classification_plan(
            plan_name=self.plan_name,
            index_server=self.index_server,
            target_app=TargetApps.SDG,
            content_analyzer=self.tcinputs['CAClouds'],
            entity_list=[dynamic_constants.ENTITY_EMAIL])
        self.log.info("Plan got created")
        self.log.info(f"Going to create Inventory - {self.inv_name}")
        self.invs_obj.add(self.inv_name, self.index_server)
        self.log.info("Inventory got created. Waiting 4 Mins for crawl job on inventory to finish")
        time.sleep(240)
        self.log.info("Inventory crawl job got completed")

    def add_sdg_project(self):
        """Adds SDG project to commcell"""
        self.log.info("Going to create a SDG project")
        sdg_proj_obj = self.sdg_obj.add(
            project_name=self.sdg_project_name,
            inventory_name=self.inv_name,
            plan_name=self.plan_name,
        )
        self.log.info("Going to add SDG data source")
        sdg_proj_obj.add_fs_data_source(
            server_name=self.sdg_client,
            data_source_name=self.ds_name,
            source_type=edisconstant.SourceType.SOURCE,
            crawl_path=self.path
        )
        self.log.info("SDG data source added successfully")
        self.all_ds_obj = sdg_proj_obj.data_sources
        self.sdk_helper = ActivateSDKHelper(commcell_object=self.commcell,
                                            app_entity=sdg_proj_obj,
                                            data_source=self.ds_name)

    def get_job_id(self):
        """finds job id of latest crawl job in SDG Project and returns it"""
        return self.sdk_helper.get_latest_job_id()

    def validate_sensitive_count(self):
        """Validates total sensitive count files found with total files in source local path"""
        self.sdk_helper.validate_sensitive_count(client_name=self.sdg_client,
                                                 path=self.path)

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Initializing all SDG Entities class objects")
        self.sdg_client = self.tcinputs['SDGClient']
        self.index_server = self.tcinputs['IndexServer']
        self.sdg_project_name = "MultipleCA_Project_%s" % self.id
        self.plan_name = "MultipleCA_TestPlan_%s" % self.id
        self.ds_name = "MultipleCA_DataSource_%s" % self.id
        self.inv_name = "MultipleCA_Inventory_%s" % self.id
        self.plans_obj = self.commcell.plans
        self.invs_obj = self.commcell.activate.inventory_manager()
        self.sdg_obj = self.commcell.activate.sensitive_data_governance()
        ca_nodes = self.tcinputs['CAClouds']
        for node in ca_nodes:
            ca_obj = self.commcell.content_analyzers.get(node)
            client_name = self.commcell.clients.get(ca_obj.client_id).client_name
            self.ca_list.append(client_name)
            self.log.info(f"CA cloud mapping to client : [{node}] - [{client_name}]")
        self.ca_helper = ContentAnalyzerHelper(self)
        self.crawl_helper = CrawlJobHelper(self)
        self.sdk_helper = ActivateSDKHelper(commcell_object=self.commcell)

    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.path = self.crawl_helper.create_files_with_content(
                client_names=[self.sdg_client], count=2000, content="Email is xhyhtyem@gmail.com")
            self.create_plan_inventory()
            self.ca_helper.set_ca_debug_level(ca_nodes=self.ca_list, level=3)
            self.add_sdg_project()
            job_id = self.get_job_id()
            self.ca_helper.validate_multiple_ca_node_request(job_id=job_id,
                                                             ca_nodes=self.ca_list)
            self.validate_sensitive_count()

        except Exception as exp:
            self.log.exception('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.cleanup()
            machine_obj = Machine(machine_name=self.sdg_client, commcell_object=self.commcell)
            for folder_path in self.path:
                machine_obj.remove_directory(directory_name=folder_path)
                self.log.info(f"Deleted directory - {folder_path} on client - {self.sdg_client}")
