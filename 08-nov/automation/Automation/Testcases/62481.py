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

    pre_cleanup()                       --  Performs clean up operations for previous run

    create_plan_inventory()             --  Create plan & Inventory

    add_sdg_project()                    --  Adds SDG Project to commcell

    wait_for_job()                      --  Waits for crawl job to complete

    validate_sdg_project()               --  Validates SDG project added to commcell

    validate_export()                   --  Validates export to CSV

    validate_crawl()                    --  Validates start collection job

    invoke_review_actions()             --  Invokes review actions Delete/Move

    validate_review_actions()           --  Validates review actions Delete/Move

    tear_down()                         --  tear down function of this test case

    delete_validate_sdg_entities()      --  Deletes plan/inventory/data source and validates



"""

import base64
import os
import time
import zipfile

from cvpysdk.activateapps.constants import TargetApps, InventoryConstants, RequestConstants
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
        self.name = "CvPySDK Integration Test cases for SDG - Validate inventory with a name server, " \
                    "SDG UNC live crawl job, Review Actions(Delete/Move), Export to CSV & Start collection"
        self.tcinputs = {
            "SDGClient": None,
            "IndexServer": None,
            "ContentAnalyzer": None,
            "UNCPath": None,
            "AccessNode": None,
            "UserName": None,
            "Password": None,
            "NameServer": None,
            "UNCClient": None,
            "UNCClientPath": None
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
        self.del_doc_id = []
        self.move_doc_id = []
        self.search_resp = None
        self.del_review_name = None
        self.mov_review_name = None
        self.req_mgr = None
        self.mov_folder = None
        self.filer_machine_obj = None
        self.encoded_pwd = None

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

        # Add asset to inventory
        assets_obj = self.inv_obj.get_assets()
        asset_obj = assets_obj.add(
            asset_name=self.tcinputs['NameServer'],
            asset_type=InventoryConstants.AssetType.NAME_SERVER)
        self.log.info("Starting job on inventory asset")
        asset_obj.start_collection(wait_for_job=True)
        self.log.info("Inventory asset collection job finished")

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
            crawl_path=[self.path],
            access_node=self.tcinputs['AccessNode'],
            user_name=self.tcinputs['UserName'],
            password=self.encoded_pwd
        )
        self.log.info("SDG data source added successfully")
        self.all_ds_obj = sdg_proj_obj.data_sources
        self.ds_obj = self.all_ds_obj.get(self.ds_name)
        self.wait_for_job()

    def wait_for_job(self):
        """Waits for crawl job to complete on data source"""
        jobs = self.ds_obj.get_active_jobs()
        if not jobs:
            self.log.info("Active job list returns zero list. so checking for job history")
            jobs = self.ds_obj.get_job_history()
            if not jobs:
                raise Exception("Online crawl job didn't get invoked for SDG project added")
        job_id = list(jobs.keys())[0]
        self.log.info(f"Online crawl job invoked with id - {job_id}. Going to wait till it completes")
        self.ds_helper.monitor_crawl_job(job_id=job_id)
        self.log.info(f"Crawl job - {job_id} completed")

    def validate_sdg_project(self):
        """Validates the SDG project added to commcell"""
        if not self.all_ds_obj.has_data_source(self.ds_name):
            raise Exception(f"DataSource ({self.ds_name}) doesn't exists in SDG Project")
        total_doc_in_src = 0
        files = len(self.filer_machine_obj.get_files_in_path(folder_path=self.path))
        self.log.info(f"File count for path ({self.path}) is {files}")
        total_doc_in_src = total_doc_in_src + files
        self.log.info(f"Total document at source client  - {total_doc_in_src}")
        self.all_ds_obj.refresh()
        doc_in_dst = self.all_ds_obj.get_datasource_document_count(data_source=self.ds_name)
        if doc_in_dst != total_doc_in_src:
            raise Exception(f"Document count mismatched. Expected - {total_doc_in_src} but Actual : {doc_in_dst}")
        self.log.info("Document count validation - Success")

    def validate_export(self):
        """Validates export operation on data source"""

        self.log.info("Going to export data to csv. Criteria is : All files")
        export_token = self.ds_obj.export(criteria=edisconstant.FIELD_IS_FILE, params={"rows": "10000"})
        self.log.info(f"Waiting for export to complete. Token - {export_token}")
        zip_path = self.ds_obj.wait_for_export(token=export_token)
        self.log.info(f"Export completed. Downloaded ZIP path - {zip_path}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            self.log.info("Extracting all files inside zip")
            zip_ref.extractall(os.getcwd())
        csv_path = f"{os.getcwd()}{os.sep}{export_token}.csv"
        rowcount = 0
        for _ in open(csv_path):
            rowcount += 1
        rowcount = rowcount - 1  # remove one line for header
        self.log.info(f"Total rows found in CSV File : {rowcount}")
        if rowcount != self.ds_obj.total_documents:
            raise Exception(
                f"File count mismatched. Datasource({self.ds_obj.total_documents}) but export csv({rowcount})")
        self.log.info("Export to CSV validation - Passed")
        os.unlink(zip_path)
        os.unlink(csv_path)

    def validate_crawl(self):
        """Validates start collection job on this data source"""

        new_data_count = 5
        self.log.info(f"Going to generate Test data on filer - {self.tcinputs['UNCClientPath']}")
        self.filer_machine_obj.generate_test_data(
            file_path=self.tcinputs['UNCClientPath'],
            ascii_data_file=True,
            dirs=1,
            files=new_data_count, custom_file_name=f"Integration_File({int(time.time())}).txt")
        before_crawl_count = self.ds_obj.total_documents
        self.log.info("Invoking start collection job on data source")
        self.ds_obj.start_collection(is_incr=False)
        self.wait_for_job()
        after_crawl_count = self.ds_obj.total_documents
        if before_crawl_count + new_data_count != after_crawl_count:
            raise Exception(
                f"Crawl didn't push generated data correctly. Generated Test data files - {new_data_count}"
                f" Old crawl files count - {before_crawl_count} New crawl files count - {after_crawl_count}")
        self.log.info("Start collection job Validation - Passed")

    def invoke_review_actions(self):
        """Invokes review actions for Delete & Move operation"""

        self.log.info("Trying Search on data source to pick document id")
        _, self.search_resp, _ = self.ds_obj.search(
            criteria=dynamic_constants.IS_FILE_PARAM, attr_list={
                dynamic_constants.CONTENT_ID_PARAM, dynamic_constants.URL_PARAM}, params={
                "rows": "6"})
        self.log.info(f"Random document got - {self.search_resp}")
        i = 0
        for doc in self.search_resp:
            doc_id = doc[dynamic_constants.CONTENT_ID_PARAM]
            if i % 2 == 0:
                self.del_doc_id.append(doc_id)
            else:
                self.move_doc_id.append(doc_id)
            i = i + 1
        self.log.info(f"Picked document content id for Delete - {self.del_doc_id}")
        self.log.info(f"Picked document content id for Move - {self.move_doc_id}")
        self.log.info("Invoking Review actions operation for documents")
        self.ds_obj.review_action(
            action_type=edisconstant.ReviewActions.DELETE, document_ids=self.del_doc_id, reviewers=[
                self.inputJSONnode['commcell']['commcellUsername']], approvers=[
                self.inputJSONnode['commcell']['commcellUsername']], req_name=self.del_review_name)
        self.ds_obj.review_action(
            action_type=edisconstant.ReviewActions.MOVE,
            document_ids=self.move_doc_id,
            reviewers=[
                self.inputJSONnode['commcell']['commcellUsername']],
            approvers=[
                self.inputJSONnode['commcell']['commcellUsername']],
            req_name=self.mov_review_name,
            destination=f"{self.path}{self.filer_machine_obj.os_sep}{self.mov_folder}",
            user_name=self.tcinputs['UserName'],
            password=self.encoded_pwd)
        self.log.info("Successfully invoked review request for delete/move actions")
        self.req_mgr.refresh()

    def validate_review_actions(self):
        """Validates review actions for Delete & Move operation"""
        self.log.info("Initializing review action objects for delete/move operations")
        del_review_obj = self.req_mgr.get(self.del_review_name)
        mov_review_obj = self.req_mgr.get(self.mov_review_name)
        self.log.info("Cross checking review document count for delete action")
        count, _ = del_review_obj.get_document_details()
        self.log.info(f"Delete review contains [{count}] documents")
        if count != len(self.del_doc_id):
            raise Exception(
                f"Review documents count mismatched. Selected({len(self.del_doc_id)}) "
                f"but in review, we have documents({count})")
        self.log.info("Going to mark as review complete for both delete/move operations")
        for doc in self.del_doc_id:
            del_review_obj.review_document(comment="Automation Approved", doc_id=doc, ds_id=self.ds_obj.data_source_id)

        for doc in self.move_doc_id:
            mov_review_obj.review_document(comment="Automation Approved", doc_id=doc, ds_id=self.ds_obj.data_source_id)

        stats_del = del_review_obj.review_stats()
        self.log.info(f"Delete Review action Current Stats : {stats_del}")
        stats_mov = mov_review_obj.review_stats()
        self.log.info(f"Move Review action Current Stats : {stats_mov}")
        if stats_del[dynamic_constants.REVIEW_ACTION_REVIEWED_DOC_PARAM] != len(self.del_doc_id):
            raise Exception(
                f"Mismatch between document selected({len(self.del_doc_id)}) for review and "
                f"reviewed documents({stats_del[dynamic_constants.REVIEW_ACTION_REVIEWED_DOC_PARAM]})")
        self.log.info("Going to set Review complete for both delete/move operations")
        del_review_obj.mark_review_complete()
        mov_review_obj.mark_review_complete()
        self.log.info("Cross checking review status for Move operation")
        if mov_review_obj.status != RequestConstants.RequestStatus.ReviewCompleted.name:
            raise Exception(
                f"Review status is not set correctly. Expected({RequestConstants.RequestStatus.ReviewCompleted.name}) "
                f"but Actual({mov_review_obj.status})")
        self.log.info("Going to request approval")
        del_wjob = del_review_obj.request_approval()
        mov_wjob = mov_review_obj.request_approval()
        self.log.info("Fetch document count detail in source before approving")
        total_doc_in_src_before = 0
        files = len(self.filer_machine_obj.get_files_in_path(folder_path=self.tcinputs['UNCClientPath']))
        self.log.info(f"File count for path ({self.tcinputs['UNCClientPath']}) is {files}")
        total_doc_in_src_before = total_doc_in_src_before + files
        self.log.info(f"Total document at source client  - {total_doc_in_src_before}")
        self.log.info("Going to provide approval")
        del_review_obj.give_approval(workflow_job_id=del_wjob)
        mov_review_obj.give_approval(workflow_job_id=mov_wjob)
        self.log.info(
            f"Approval Workflow job invoked. Delete Approval jobid[{del_wjob}] Move Approval jobid[{mov_wjob}]")
        self.log.info("Review Actions completed. Waiting on status to change to 'Task completed'")
        timeout = time.time() + 60 * 15  # 15mins
        while True:
            if time.time() > timeout:
                raise Exception("Review Actions Delete/Move job Timeout")
            del_review_obj.refresh()
            mov_review_obj.refresh()
            if del_review_obj.status == RequestConstants.RequestStatus.TaskCompleted.name and \
                    mov_review_obj.status == RequestConstants.RequestStatus.TaskCompleted.name:
                break
            self.log.info(
                f"Going to wait for 30seconds. Current status of reviews : Delete({del_review_obj.status}) "
                f"Move({mov_review_obj.status})")
            time.sleep(30)
        self.log.info("Validation on review action status - Passed")
        self.log.info("Going to check Deleted files on source")
        total_doc_in_src_after = 0
        files = len(self.filer_machine_obj.get_files_in_path(folder_path=self.tcinputs['UNCClientPath']))
        self.log.info(f"File count for path ({self.tcinputs['UNCClientPath']}) is {files}")
        total_doc_in_src_after = total_doc_in_src_after + files
        self.log.info(f"Total document at source client  - {total_doc_in_src_after}")
        if total_doc_in_src_before != total_doc_in_src_after + len(self.del_doc_id):
            raise Exception(
                f"Delete operation didn't remove files. Before review count:{total_doc_in_src_before} "
                f"After review count: {total_doc_in_src_after}")
        self.log.info("Delete operation Validation - Passed")
        self.log.info("Going to check move operation files on source")
        total_doc_in_mov_src_after = 0
        url = f"{self.tcinputs['UNCClientPath']}{self.filer_machine_obj.os_sep}{self.mov_folder}"
        files = len(self.filer_machine_obj.get_files_in_path(folder_path=url))
        self.log.info(f"File count for path ({url}) is {files}")
        total_doc_in_mov_src_after = total_doc_in_mov_src_after + files
        self.log.info(f"Total document at source client  - {total_doc_in_mov_src_after}")
        if total_doc_in_mov_src_after == 0:
            raise Exception("Move operation didn't move files properly")
        self.log.info("Move operation Validation - Passed")

    def delete_validate_sdg_entities(self):
        """Deletes SDG entities and validates whether it got deleted or not"""
        self.log.info("Deleting Delete request")
        self.req_mgr.delete(self.del_review_name)
        self.log.info("Deleting Move request")
        self.req_mgr.delete(self.mov_review_name)
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
        if self.req_mgr.has_request(self.del_review_name):
            raise Exception(f"Delete Review Request({self.del_review_name}) didn't get deleted properly. Please check")
        if self.req_mgr.has_request(self.mov_review_name):
            raise Exception(f"Move Review Request({self.mov_review_name}) didn't get deleted properly. Please check")

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Initializing all SDG Entities class objects")
        self.sdg_client = self.tcinputs['SDGClient']
        self.path = self.tcinputs['UNCPath']
        self.index_server = self.tcinputs['IndexServer']
        self.sdg_project_name = "Integration_Project_%s" % self.id
        self.plan_name = "Integration_TestPlan_%s" % self.id
        self.ds_name = "Integration_DataSource_%s" % self.id
        self.inv_name = "Integration_Inventory_%s" % self.id
        self.del_review_name = f"Integration_RA_Delete_{self.id}_{int(time.time())}"
        self.mov_review_name = f"Integration_RA_Move_{self.id}_{int(time.time())}"
        self.mov_folder = "Integration_Move_ops_%s" % int(time.time())
        self.plans_obj = self.commcell.plans
        self.invs_obj = self.commcell.activate.inventory_manager()
        self.sdg_obj = self.commcell.activate.sensitive_data_governance()
        self.ds_helper = DataSourceHelper(self.commcell)
        self.req_mgr = self.commcell.activate.request_manager()
        self.filer_machine_obj = Machine(machine_name=self.tcinputs['UNCClient'], username=self.tcinputs['UserName'],
                                         password=self.tcinputs['Password'])
        self.log.info(
            f"Move directory - {self.tcinputs['UNCClientPath']}{self.filer_machine_obj.os_sep}{self.mov_folder}")
        self.filer_machine_obj.create_directory(
            directory_name=f"{self.tcinputs['UNCClientPath']}{self.filer_machine_obj.os_sep}{self.mov_folder}",
            force_create=True)
        self.encoded_pwd = self.tcinputs['Password'].encode()
        self.encoded_pwd = base64.b64encode(self.encoded_pwd)
        self.encoded_pwd = self.encoded_pwd.decode()
        if self.req_mgr.has_request(self.del_review_name):
            self.log.info("Deleting older run Delete request")
            self.req_mgr.delete(self.del_review_name)
        if self.req_mgr.has_request(self.mov_review_name):
            self.log.info("Deleting older run Move request")
            self.req_mgr.delete(self.mov_review_name)

    def run(self):
        """Run function of this test case"""
        try:
            self.pre_cleanup()
            self.create_plan_inventory()
            self.validate_plan_inventory()
            self.add_sdg_project()
            self.validate_sdg_project()
            self.validate_export()
            self.validate_crawl()
            self.invoke_review_actions()
            self.validate_review_actions()

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
