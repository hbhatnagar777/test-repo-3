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

    add_fso_server()                    --  Adds FSO server to commcell

    wait_for_job()                      --  Waits for crawl job to complete

    validate_fso_server()               --  Validates FSO server added to commcell

    validate_export()                   --  Validates export to CSV

    validate_crawl()                    --  Validates start collection job

    invoke_review_actions()             --  Invokes review actions Delete/Move

    validate_review_actions()           --  Validates review actions Delete/Move

    tear_down()                         --  tear down function of this test case

    delete_validate_fso_entities()      --  Deletes plan/inventory/data source and validates



"""
import base64
import os
import time
import zipfile

from cvpysdk.activateapps.constants import TargetApps
from cvpysdk.activateapps.constants import EdiscoveryConstants as edisconstant
from cvpysdk.activateapps.constants import InventoryConstants
from cvpysdk.activateapps.constants import RequestConstants


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
        self.name = "CvPySDK Integration Test cases for FSO - Validate inventory with name server " \
                    ", FSO UNC live crawl job , Review Actions(Delete/Move), Export to CSV & Start collection"
        self.tcinputs = {
            "FSOClient": None,
            "UNCPath": None,
            "IndexServer": None,
            "AccessNode": None,
            "UserName": None,
            "Password": None,
            "NameServer": None,
            "UNCClient": None,
            "UNCClientPath": None
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
        self.all_ds_obj = None
        self.ds_helper = None
        self.del_doc_id = []
        self.move_doc_id = []
        self.search_resp = None
        self.del_review_name = None
        self.mov_review_name = None
        self.req_mgr = None
        self.mov_folder = None
        self.filer_machine_obj = None
        self.encoded_pwd = None

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

    def validate_export(self):
        """Validates export operation on data source"""
        self.log.info("Going to export data to csv. Criteria is : All files")
        export_token = self.ds_obj.export(criteria=edisconstant.FIELD_IS_FILE, params={"rows": "10000"})
        self.log.info(f"Waiting for export to complete. Token - {export_token}")
        zip_path = self.ds_obj.wait_for_export(token=export_token)
        self.log.info(f"Export completed. Downloaded ZIP path - {zip_path}")
        csv_name = None
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            self.log.info("Extracting all files inside zip")
            zip_ref.extractall(os.getcwd())
            csv_name = zip_ref.namelist()[0]
        if export_token not in csv_name:
            raise Exception(f"Export file name doesn't match with token GUID - {csv_name}")
        csv_path = f"{os.getcwd()}{os.sep}{csv_name}"
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
        del_review_obj.review_document(comment="Automation Approved")
        mov_review_obj.review_document(comment="Automation Approved")
        stats = del_review_obj.review_stats()
        self.log.info(f"Delete Review action Current Stats : {stats}")
        if stats[dynamic_constants.REVIEW_ACTION_REVIEWED_DOC_PARAM] != len(self.del_doc_id):
            raise Exception(
                f"Mismatch between document selected({len(self.del_doc_id)}) for review and "
                f"reviewed documents({stats[dynamic_constants.REVIEW_ACTION_REVIEWED_DOC_PARAM]})")
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

    def delete_validate_fso_entities(self):
        """Deletes FSO entities and validates whether it got deleted or not"""
        self.log.info("Deleting Delete request")
        self.req_mgr.delete(self.del_review_name)
        self.log.info("Deleting Move request")
        self.req_mgr.delete(self.mov_review_name)
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
        if self.req_mgr.has_request(self.del_review_name):
            raise Exception(f"Delete Review Request({self.del_review_name}) didn't get deleted properly. Please check")
        if self.req_mgr.has_request(self.mov_review_name):
            raise Exception(f"Move Review Request({self.mov_review_name}) didn't get deleted properly. Please check")

    def validate_fso_server(self):
        """Validates the FSO server added to commcell"""
        if not self.all_ds_obj.has_data_source(self.ds_name):
            raise Exception(f"DataSource ({self.ds_name}) doesn't exists in FSO server")
        total_doc_in_src = 0
        files = len(self.filer_machine_obj.get_files_in_path(folder_path=self.tcinputs['UNCClientPath']))
        self.log.info(f"File count for path ({self.tcinputs['UNCClientPath']}) is {files}")
        total_doc_in_src = total_doc_in_src + files
        self.log.info(f"Total document at source client  - {total_doc_in_src}")
        self.all_ds_obj.refresh()
        doc_in_dst = self.all_ds_obj.get_datasource_document_count(data_source=self.ds_name)
        if doc_in_dst != total_doc_in_src:
            raise Exception(f"Document count mismatched. Expected - {total_doc_in_src} but Actual : {doc_in_dst}")
        self.log.info("Document count validation - Success")

    def add_fso_server(self):
        """Adds FSO server to commcell"""

        self.log.info("Going to add FSO data source")
        self.fso_client_obj = self.fso_obj.add_file_server(
            server_name=self.fso_client,
            data_source_name=self.ds_name,
            inventory_name=self.inv_name,
            plan_name=self.plan_name,
            source_type=edisconstant.SourceType.SOURCE,
            crawl_path=[self.path],
            access_node=self.tcinputs['AccessNode'],
            user_name=self.tcinputs['UserName'],
            password=self.encoded_pwd)
        self.log.info("FSO data source added successfully")
        self.all_ds_obj = self.fso_client_obj.data_sources
        self.ds_obj = self.all_ds_obj.get(self.ds_name)
        self.wait_for_job()

    def wait_for_job(self):
        """Waits for crawl job to complete on data source"""
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
                self.fso_obj.refresh()  # As it is new client, refreshing it again
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
        self.log.info("Inventory got created")
        # Add asset to inventory
        assets_obj = self.inv_obj.get_assets()
        asset_obj = assets_obj.add(
            asset_name=self.tcinputs['NameServer'],
            asset_type=InventoryConstants.AssetType.IDENTITY_SERVER)
        self.log.info("Waiting 10mins on job for inventory asset")
        time.sleep(600)
        self.log.info("Inventory asset collection job finished")

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Initializing all FSO Entities class objects")
        self.fso_client = self.tcinputs['FSOClient']
        self.path = self.tcinputs['UNCPath']
        self.index_server = self.tcinputs['IndexServer']
        self.plan_name = "Integration_TestPlan_%s" % self.id
        self.ds_name = "Integration_DataSource_%s" % self.id
        self.inv_name = "Integration_Inventory_%s" % self.id
        self.del_review_name = "Integration_RA_Delete_%s" % self.id
        self.mov_review_name = "Integration_RA_Move_%s" % self.id
        self.mov_folder = "Integration_Move_ops_%s" % int(time.time())
        self.plans_obj = self.commcell.plans
        self.invs_obj = self.commcell.activate.inventory_manager()
        self.fso_obj = self.commcell.activate.file_storage_optimization()
        self.ds_helper = DataSourceHelper(self.commcell)
        self.req_mgr = self.commcell.activate.request_manager()
        self.filer_machine_obj = Machine(machine_name=self.tcinputs['UNCClient'], username=self.tcinputs['UserName'],
                                         password=self.tcinputs['Password'])
        self.filer_machine_obj.set_encoding_type('utf-8')
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

            self.create_plan_inventory()
            self.add_fso_server()
            self.validate_fso_server()
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
            self.log.info("Going to delete FSO Environment entities")
            self.delete_validate_fso_entities()
