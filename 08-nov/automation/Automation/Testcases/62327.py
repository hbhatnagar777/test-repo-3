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
    __init__()                          --  initialize TestCase class

    setup()                             --  setup function of this test case

    run()                               --  run function of this test case

    create_plan_inventory()             --  Create plan & Inventory

    validate_plan_inventory()           --  Validate plan & Inventory

    add_fso_server()                    --  Adds FSO server to commcell

    validate_fso_server()               --  Validates FSO server added to commcell

    tear_down()                         --  tear down function of this test case

    validate_tagging()                  --  Applies tagging and validate it

    delete_validate_fso_entities()      --  Deletes plan/inventory/data source and validates



"""
import time

from cvpysdk.activateapps.constants import TargetApps
from cvpysdk.activateapps.constants import EdiscoveryConstants as edisconstant
from cvpysdk.activateapps.entity_manager import EntityManagerTypes

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.utils import constants as dynamic_constants


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
        self.name = "CvPySDK Integration Test cases for FSO - Validate plan create/delete , " \
                    "Inventory create/Delete , FSO local live crawl job , Document Search & Document tagging"
        self.tcinputs = {
            "FSOClient": None,
            "LocalPath": None,
            "IndexServer": None
        }
        self.fso_client = None
        self.path = None
        self.index_server = None
        self.plan_name = None
        self.ds_name = None
        self.inv_name = None
        self.plan_obj = None
        self.plans_obj = None
        self.inv_obj = None
        self.invs_obj = None
        self.fso_client_obj = None
        self.fso_obj = None
        self.ds_obj = None
        self.tag_mgr = None
        self.all_ds_obj = None
        self.ds_helper = None

    def validate_tagging(self):
        """Applies tagging to document & validates it"""
        self.log.info(f"Going to create Tagset & Tag")
        tag_set_name = "Integration_Tagset_%s" % self.id
        tag_name = "Integration_Tag_%s" % self.id
        if self.tag_mgr.has_tag_set(tag_set_name=tag_set_name):
            self.log.info("Deleting Tagset as it exists already")
            self.tag_mgr.delete(tag_set_name=tag_set_name)
        tag_set_obj = self.tag_mgr.add(tag_set_name=tag_set_name)
        tag_obj = tag_set_obj.add_tag(tag_name=tag_name)
        self.log.info(f"Tagset({tag_set_name}) & Tag({tag_name}) got created")
        self.log.info("Trying Search on data source to pick document id")
        _, doc_resp, _ = self.ds_obj.search(criteria=dynamic_constants.IS_FILE_PARAM,
                                            attr_list={dynamic_constants.CONTENT_ID_PARAM},
                                            params={"rows": "1"})
        self.log.info(f"Random document got - {doc_resp}")
        doc_id = doc_resp[0][dynamic_constants.CONTENT_ID_PARAM]
        self.log.info(f"Picked document content id for tagging - {doc_id}")
        self.log.info("Document Search Validation - Success")
        job_id = self.ds_obj.tag_items(tags=[f"{tag_set_name}\\\\{tag_name}"], document_ids=[doc_id])
        self.log.info(f"Waiting for Tag job to finish - {job_id}")
        self.ds_helper.monitor_crawl_job(job_id=job_id)
        self.log.info("Going to validate tagged document")
        _, doc_resp, _ = self.ds_obj.search(
            criteria=f"{dynamic_constants.IS_FILE_PARAM} AND {dynamic_constants.CONTENT_ID_PARAM}:{doc_id}", attr_list={
                dynamic_constants.CONTENT_ID_PARAM, dynamic_constants.TAG_ID_PARAM}, params={
                "rows": "1"})
        doc_resp = doc_resp[0]
        self.log.info(f"Search Document response - {doc_resp}")
        if dynamic_constants.TAG_ID_PARAM not in doc_resp:
            raise Exception("Document is missing tag details")
        if tag_obj.guid not in doc_resp[dynamic_constants.TAG_ID_PARAM]:
            raise Exception(f"Tag guid({tag_obj.guid}) is not present correctly in document({doc_id})")
        self.log.info(f"Tagging Validation - Success")
        self.log.info(f"Deleting Tagset - {tag_set_name}")
        self.tag_mgr.delete(tag_set_name=tag_set_name)

    def delete_validate_fso_entities(self):
        """Deletes FSO entities and validates whether it got deleted or not"""
        self.log.info("Deleting DataSource")
        self.all_ds_obj.delete(self.ds_name)
        self.log.info("Deleting inventory")
        self.invs_obj.delete(self.inv_name)
        self.log.info("Deleting DC Plan")
        self.plans_obj.delete(self.plan_name)

        if self.plans_obj.has_plan(self.plan_name):
            raise Exception(f"DC Plan({self.plan_name}) didn't get deleted properly. Please check")
        if self.invs_obj.has_inventory(self.inv_name):
            raise Exception(f"Inventory({self.inv_name}) didn't get deleted properly. Please check")
        if self.all_ds_obj.has_data_source(self.ds_name):
            raise Exception(f"DataSource({self.ds_name}) didn't get deleted properly. Please check")

    def validate_fso_server(self):
        """Validates the FSO server added to commcell"""
        if not self.all_ds_obj.has_data_source(self.ds_name):
            raise Exception(f"DataSource ({self.ds_name}) doesn't exists in FSO server")
        total_doc_in_src = 0
        machine_obj = Machine(machine_name=self.fso_client, commcell_object=self.commcell)
        for src_path in self.path:
            files = len(machine_obj.get_files_in_path(folder_path=src_path))
            self.log.info(f"File count for path ({src_path}) is {files}")
            total_doc_in_src = total_doc_in_src + files
        self.log.info(f"Total document at source client  - {total_doc_in_src}")
        self.all_ds_obj.refresh()
        doc_in_dst = self.all_ds_obj.get_datasource_document_count(data_source=self.ds_name)
        if doc_in_dst != total_doc_in_src:
            raise Exception(f"Document count mismatched. Expected - {total_doc_in_src} but Actual : {doc_in_dst}")
        self.log.info("Document count validation - Success")

    def add_fso_server(self):
        """Adds FSO server to commcell"""
        server_exists = self.fso_obj.has_server(self.fso_client)
        if server_exists:
            self.log.info("FSO Server exists with data sources already. Rechecking for any older run entities exists")
            server_obj = self.fso_obj.get(self.fso_client)
            ds_obj = server_obj.data_sources
            if ds_obj.has_data_source(self.ds_name):
                self.log.info(f"Datasource({self.ds_name}) exists already. Deleting it")
                ds_obj.delete(self.ds_name)
        self.log.info("Going to add FSO data source")
        self.fso_client_obj = self.fso_obj.add_file_server(
            server_name=self.fso_client,
            data_source_name=self.ds_name,
            inventory_name=self.inv_name,
            plan_name=self.plan_name,
            source_type=edisconstant.SourceType.SOURCE,
            crawl_path=self.path)
        self.log.info("FSO data source added successfully")
        self.all_ds_obj = self.fso_client_obj.data_sources
        self.ds_obj = self.all_ds_obj.get(self.ds_name)
        jobs = self.ds_obj.get_active_jobs()
        if not jobs:
            self.log.info("Active job list returns zero list. so checking for job history")
            jobs = self.ds_obj.get_job_history()
            if not jobs:
                raise Exception("Online crawl job didn't get invoked for FSO server added")
        job_id = list(jobs.keys())[0]
        self.log.info(f"Online crawl job invoked with id - {job_id}. Going to wait till it completes")
        self.ds_helper.monitor_crawl_job(job_id=job_id)
        self.log.info(f"Crawl job - {job_id} completed")

    def validate_plan_inventory(self):
        """Validates plan and inventory for FSO"""
        if not self.plans_obj.has_plan(self.plan_name):
            raise Exception(f"DC Plan({self.plan_name}) didn't get created properly. Please check")
        if not self.plan_obj.content_indexing_props:
            raise Exception("Content indexing properties missing in plan attributes")
        if not self.invs_obj.has_inventory(self.inv_name):
            raise Exception(f"Inventory({self.inv_name}) doesn't exists in commcell")
        if not self.inv_obj.get_inventory_data():
            raise Exception(f"Inventory doesn't return any items")
        self.log.info("Plan & Inventory validation is success")

    def create_plan_inventory(self):
        """Creates plan and inventory for FSO"""
        server_exists = self.fso_obj.has_server(self.fso_client)
        if server_exists:
            self.log.info("FSO Server exists with data sources already. Rechecking for any older run entities exists")
            server_obj = self.fso_obj.get(self.fso_client)
            ds_obj = server_obj.data_sources
            if ds_obj.has_data_source(self.ds_name):
                self.log.info(f"Datasource({self.ds_name}) exists already. Deleting it")
                ds_obj.delete(self.ds_name)
        if self.plans_obj.has_plan(self.plan_name):
            self.log.info(f"Deleting plan as it exists early - {self.plan_name}")
            self.plans_obj.delete(self.plan_name)
        if self.invs_obj.has_inventory(self.inv_name):
            self.log.info(f"Deleting inventory as it exists early - {self.inv_name}")
            self.invs_obj.delete(self.inv_name)
        self.log.info(f"Going to create FSO Plan - {self.plan_name}")
        self.plan_obj = self.plans_obj.add_data_classification_plan(
            plan_name=self.plan_name,
            index_server=self.index_server,
            target_app=TargetApps.FSO)
        self.log.info("Plan got created")
        self.log.info(f"Going to create Inventory - {self.inv_name}")
        self.inv_obj = self.invs_obj.add(self.inv_name, self.index_server)
        self.log.info("Inventory got created. Waiting 5Mins for crawl job on inventory to finish")
        time.sleep(420)
        self.log.info("Inventory crawl job got completed")

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Initializing all FSO Entities class objects")
        self.fso_client = self.tcinputs['FSOClient']
        self.path = self.tcinputs['LocalPath']
        self.index_server = self.tcinputs['IndexServer']
        self.plan_name = "Integration_TestPlan_%s" % self.id
        self.ds_name = "Integration_DataSource_%s" % self.id
        self.inv_name = "Integration_Inventory_%s" % self.id
        self.plans_obj = self.commcell.plans
        self.invs_obj = self.commcell.activate.inventory_manager()
        self.fso_obj = self.commcell.activate.file_storage_optimization()
        self.ds_helper = DataSourceHelper(self.commcell)
        self.tag_mgr = self.commcell.activate.entity_manager(EntityManagerTypes.TAGS)

    def run(self):
        """Run function of this test case"""
        try:

            self.create_plan_inventory()
            self.validate_plan_inventory()
            self.add_fso_server()
            self.validate_fso_server()
            self.validate_tagging()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("Going to delete FSO Environment entities")
            self.delete_validate_fso_entities()
