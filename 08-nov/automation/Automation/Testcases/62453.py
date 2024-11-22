import time

from cvpysdk.activateapps.constants import TargetApps
from cvpysdk.activateapps.constants import EdiscoveryConstants as edisconstant
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
        self.name = "CvPySDK Integration Test cases for SDG - Validate plan create/delete , " \
                    "Inventory create/Delete , SDG local live crawl job"
        self.tcinputs = {
            "SDGClient": None,
            "LocalPath": None,
            "IndexServer": None,
            "ContentAnalyzer": None
        }
        self.sdg_client = None
        self.path = None
        self.index_server = None
        self.plan_name = None
        self.ds_name = None
        self.inv_name = None
        self.plan_obj = None
        self.plans_obj = None
        self.inv_obj = None
        self.invs_obj = None
        self.sdg_obj = None
        self.ds_obj = None
        self.all_ds_obj = None
        self.ds_helper = None
        self.sdg_project_name = None

    def pre_cleanup(self):
        """Performs cleanup operations - Deletes SDG project, plan and inventory if they already exist"""
        project_exists = self.sdg_obj.has_project(self.sdg_project_name)
        if project_exists:
            self.sdg_obj.delete(self.sdg_project_name)
            self.log.info(f"Deleted the SDG Project - {self.sdg_project_name}")
        if self.plans_obj.has_plan(self.plan_name):
            self.log.info(f"Deleting plan as it exists early - {self.plan_name}")
            self.plans_obj.delete(self.plan_name)
        if self.invs_obj.has_inventory(self.inv_name):
            self.log.info(f"Deleting inventory as it exists early - {self.inv_name}")
            self.invs_obj.delete(self.inv_name)

    def create_plan_inventory(self):
        """Creates plan and inventory for SDG"""
        self.log.info(f"Going to create SDG Plan - {self.plan_name}")
        self.plan_obj = self.plans_obj.add_data_classification_plan(
            plan_name=self.plan_name,
            index_server=self.index_server,
            target_app=TargetApps.SDG,
            content_analyzer=[self.tcinputs['ContentAnalyzer']],
            entity_list=[dynamic_constants.ENTITY_EMAIL, dynamic_constants.ENTITY_IP])
        self.log.info("Plan got created")
        self.log.info(f"Going to create Inventory - {self.inv_name}")
        self.inv_obj = self.invs_obj.add(self.inv_name, self.index_server)
        self.log.info("Inventory got created. Waiting 4 Mins for crawl job on inventory to finish")
        time.sleep(240)
        self.log.info("Inventory crawl job got completed")

    def validate_plan_inventory(self):
        """Validates plan and inventory for SDG"""
        if not self.plans_obj.has_plan(self.plan_name):
            raise Exception(f"DC Plan({self.plan_name}) didn't get created properly. Please check")
        if not self.plan_obj.content_indexing_props:
            raise Exception("Content indexing properties missing in plan attributes")
        if not self.invs_obj.has_inventory(self.inv_name):
            raise Exception(f"Inventory({self.inv_name}) doesn't exists in commcell")
        if not self.inv_obj.get_inventory_data():
            raise Exception(f"Inventory doesn't return any items")
        self.log.info("Plan & Inventory validation is success")

    def add_sdg_project(self):
        """Adds SDG project to commcell"""
        self.log.info("Going to create a SDG project")
        sdg_proj_obj = self.sdg_obj.add(
            project_name=self.sdg_project_name,
            inventory_name=self.inv_name,
            plan_name=self.plan_name,
            )
        self.log.info("Going to add SDG data source")
        sdg_proj_ds = sdg_proj_obj.add_fs_data_source(
            server_name=self.sdg_client,
            data_source_name=self.ds_name,
            source_type=edisconstant.SourceType.SOURCE,
            crawl_path=self.path
        )
        self.log.info("SDG data source added successfully")
        self.all_ds_obj = sdg_proj_obj.data_sources
        self.ds_obj = self.all_ds_obj.get(self.ds_name)
        jobs = self.ds_obj.get_active_jobs()
        if not jobs:
            self.log.info("Active job list returns zero list. so checking for job history")
            jobs = self.ds_obj.get_job_history()
            if not jobs:
                raise Exception("Online crawl job didn't get invoked for SDG server added")
        job_id = list(jobs.keys())[0]
        self.log.info(f"Online crawl job invoked with id - {job_id}. Going to wait till it completes")
        self.ds_helper.monitor_crawl_job(job_id=job_id)
        self.log.info(f"Crawl job - {job_id} completed")

    def validate_sdg_server(self):
        """Validates the SDG server added to commcell"""
        if not self.all_ds_obj.has_data_source(self.ds_name):
            raise Exception(f"DataSource ({self.ds_name}) doesn't exists in SDG Project")
        total_doc_in_src = 0
        machine_obj = Machine(machine_name=self.sdg_client, commcell_object=self.commcell)
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

    def delete_validate_sdg_entities(self):
        """Deletes SDG entities and validates whether it got deleted or not"""
        self.log.info("Deleting SDG Project")
        self.sdg_obj.delete(self.sdg_project_name)
        self.log.info("Deleting Inventory")
        self.invs_obj.delete(self.inv_name)
        self.log.info("Deleting DC Plan")
        self.plans_obj.delete(self.plan_name)
        if self.plans_obj.has_plan(self.plan_name):
            raise Exception(f"DC Plan({self.plan_name}) didn't get deleted properly. Please check")
        if self.invs_obj.has_inventory(self.inv_name):
            raise Exception(f"Inventory({self.inv_name}) didn't get deleted properly. Please check")
        if self.sdg_obj.has_project(self.sdg_project_name):
            raise Exception(f"Project({self.sdg_project_name}) didn't get deleted properly. Please check")

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Initializing all SDG Entities class objects")
        self.sdg_client = self.tcinputs['SDGClient']
        self.path = self.tcinputs['LocalPath']
        self.index_server = self.tcinputs['IndexServer']
        self.sdg_project_name = "Integration_Project_%s" % self.id
        self.plan_name = "Integration_TestPlan_%s" % self.id
        self.ds_name = "Integration_DataSource_%s" % self.id
        self.inv_name = "Integration_Inventory_%s" % self.id
        self.plans_obj = self.commcell.plans
        self.invs_obj = self.commcell.activate.inventory_manager()
        self.sdg_obj = self.commcell.activate.sensitive_data_governance()
        self.ds_helper = DataSourceHelper(self.commcell)

    def run(self):
        """Run function of this test case"""
        try:
            self.pre_cleanup()
            self.create_plan_inventory()
            self.validate_plan_inventory()
            self.add_sdg_project()
            self.validate_sdg_server()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("Going to delete SDG Environment entities")
            self.delete_validate_sdg_entities()
