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

    add_sdg_project()                    --  Adds SDG project to commcell

    wait_for_job()                      --  Waits for crawl job to finish

    validate_sdg_project()               --  Validates SDG project added to commcell

    setup_new_user()                    --  Creates new commcell user for sharing SDG project

    validate_sharing()                  --  Shares project with user and validate it

    setup_data()                        --  create new data and run backup job on default subclient

    validate_schedule()                 --  Creates schedule & Validates schedule invoked job or not

    tear_down()                         --  tear down function of this test case

    delete_validate_sdg_entities()      --  Deletes plan/inventory/data source and validates it

"""

import time
import datetime

from cvpysdk.activateapps.constants import TargetApps
from cvpysdk.activateapps.constants import EdiscoveryConstants as edisconstant
from cvpysdk.commcell import Commcell
from cvpysdk.exception import SDKException
from cvpysdk.schedules import SchedulePattern

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Server.Security.userhelper import UserHelper
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
        self.name = "CvPySDK Integration Test cases for SDG (Backed Up Data) - Validate plan create/delete , " \
                    "Inventory create/Delete , SDG Project (Backed Up Data) create/Delete, sharing & scheduling  "
        self.tcinputs = {
            "SDGClient": None,
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
        self.sdg_proj_obj = None
        self.user_commcell = None
        self.user = None
        self.password = None
        self.client_obj = None
        self.agent_obj = None
        self.user_helper = None

    def pre_cleanup(self):
        """Performs cleanup operations - Deleted SDG project, plan and inventory if they already exist"""
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
        self.sdg_proj_obj = self.sdg_obj.add(
            project_name=self.sdg_project_name,
            inventory_name=self.inv_name,
            plan_name=self.plan_name,
        )
        self.log.info("Going to add SDG data source")
        sdg_proj_ds = self.sdg_proj_obj.add_fs_data_source(
            server_name=self.sdg_client,
            data_source_name=self.ds_name,
            source_type=edisconstant.SourceType.BACKUP
        )
        self.log.info("SDG data source added successfully")
        self.all_ds_obj = self.sdg_proj_obj.data_sources
        self.ds_obj = self.all_ds_obj.get(self.ds_name)

    def wait_for_job(self):
        """Waits for crawl job to complete on data source"""
        jobs = self.ds_obj.get_active_jobs()
        if not jobs:
            self.log.info("Active job list returns zero list. so checking for job history")
            jobs = self.ds_obj.get_job_history()
            if not jobs:
                raise Exception("Online crawl job didn't get invoked for SDG project added")
        self.log.info(f"Job History details got - {jobs}")
        job_id = list(jobs.keys())
        job_id = [int(i) for i in job_id]
        job_id.sort(reverse=True)
        job_id = job_id[0]
        self.log.info(f"Online crawl job invoked with id - {job_id}. Going to wait till it completes")
        self.ds_helper.monitor_crawl_job(job_id=job_id)
        self.log.info(f"Crawl job - {job_id} completed")

    def setup_new_user(self):
        """Creates new user in commcell"""

        self.user_helper.create_user(
            user_name=self.user,
            email=f"test{self.id}_{int(time.time())}@test.com",
            full_name="Test User Created by Dm2 Automation",
            password=self.password)

    def validate_sharing(self):
        """Shares SDG project with new user and validates whether shared user is able to see this project"""

        self.user_commcell = Commcell(self.inputJSONnode['commcell']['webconsoleHostname'], self.user,
                                      self.password)
        try:
            sdg_obj = self.user_commcell.activate.sensitive_data_governance()
            if sdg_obj.has_project(self.sdg_project_name):
                raise Exception(f"New user is able to see SDG project {self.sdg_project_name} without sharing")

        except SDKException:
            dummy = 0

        self.log.info(f"New user [{self.user}] is not able to see SDG Project")
        self.log.info(f"Going to share SDG Project with user - {self.user}")
        self.sdg_proj_obj.share(user_or_group_name=self.user, allow_edit_permission=False)
        self.log.info("Sharing completed. Creating new commcell object for new user")
        self.user_commcell = Commcell(self.inputJSONnode['commcell']['webconsoleHostname'], self.user, self.password)
        sdg_obj = self.user_commcell.activate.sensitive_data_governance()
        if not sdg_obj.has_project(self.sdg_project_name):
            raise Exception(f"New user is not able to see SDG Project {self.sdg_project_name} even after sharing")
        self.log.info(f"New user is able to see shared SDG Project")

    def setup_data(self):
        """Generate data and run backup job on the default subclient"""
        machine_obj = Machine(self.tcinputs['SDGClient'], self.commcell)
        backup_set_obj = self.agent_obj.backupsets.get("defaultbackupset")
        subclient_obj = backup_set_obj.subclients.get("default")
        content = subclient_obj.content[0]
        self.log.info(f"Going to create test data on path which exists on default subclient")
        new_data_count = 5
        self.log.info(f"Going to generate Test data on path - {content}")
        machine_obj.generate_test_data(
            file_path=f"{content}{machine_obj.os_sep}Folder_{int(time.time())}",
            ascii_data_file=True,
            dirs=1,
            files=new_data_count, custom_file_name=f"Integration_File({int(time.time())}).txt")
        job_obj = subclient_obj.backup("Full")
        self.log.info("Invoked the FS backup job with id : %s", job_obj.job_id)
        self.log.info("Going to Monitor this backup job for completion")
        if not job_obj.wait_for_completion(timeout=90):
            self.log.info("Backup job failed on storage policy. Please check logs")
            raise Exception("Backup job failed on storage policy")
        self.log.info("Backup job is finished")

    def validate_schedule(self):
        """Create schedule & validates schedule invoked job or not on SDG Project"""

        self.sdg_proj_obj = self.sdg_obj.get(self.sdg_project_name)
        self.all_ds_obj = self.sdg_proj_obj.data_sources
        self.ds_obj = self.all_ds_obj.get(self.ds_name)
        schedule_time_in_min = 2
        custom_time = datetime.datetime.now()
        custom_time += datetime.timedelta(minutes=schedule_time_in_min)
        self.log.info(f"Going to do scheduling with start time as - {custom_time}")
        pattern = SchedulePattern().create_schedule_pattern(
            {'freq_type': 'One_Time', 'active_start_time': custom_time.strftime('%H:%M')})
        self.log.info(f"Pattern JSON formed - {pattern}")
        self.sdg_proj_obj.add_schedule(pattern_json=pattern,
                                       schedule_name=f"IntegrationTest_Schedule_{int(time.time())}")
        self.log.info(f"Schedule created successfully")
        self.log.info(f"Going to wait for [{schedule_time_in_min}]Min")
        time.sleep(schedule_time_in_min * 60)
        self.wait_for_job()
        self.log.info("Validate whether schedule invoked job or not")
        jobs = self.ds_obj.get_job_history()
        if len(jobs) != 2:
            raise Exception(f"Job history shows only one job or more jobs")
        self.log.info("Schedule invoked the crawl job correctly. Schedule Validation - Passed")

    def validate_sdg_project(self):
        """Validates the SDG project added to commcell"""
        if not self.all_ds_obj.has_data_source(self.ds_name):
            raise Exception(f"DataSource ({self.ds_name}) doesn't exists in SDG project")
        if not self.ds_obj.crawl_type != edisconstant.CrawlType.BACKUP.value:
            raise Exception(f"Crawl type is not of BACKUP")
        total_doc_in_src = 0
        all_sets = self.agent_obj.backupsets.all_backupsets
        for backup_set, _ in all_sets.items():
            self.log.info(f"Analyzing backupset - [{backup_set}] for backup files count")
            backupset_obj = self.agent_obj.backupsets.get(backup_set)
            current_set_count = backupset_obj.backed_up_files_count()
            self.log.info(f"Backup Set ({backup_set}) has [{current_set_count}] files")
            total_doc_in_src = total_doc_in_src + current_set_count
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
        self.index_server = self.tcinputs['IndexServer']
        self.sdg_project_name = "Integration_Project_%s" % self.id
        self.plan_name = "Integration_TestPlan_%s" % self.id
        self.ds_name = "Integration_DataSource_%s" % self.id
        self.inv_name = "Integration_Inventory_%s" % self.id
        self.user = f"TestUser_{self.id}"
        self.password = f"TestUser_{self.id}!12"
        # Delete user if it exists already
        self.user_helper = UserHelper(self.commcell)
        self.user_helper.delete_user(self.user, new_user=self.inputJSONnode['commcell']['commcellUsername'])
        self.plans_obj = self.commcell.plans
        self.invs_obj = self.commcell.activate.inventory_manager()
        self.sdg_obj = self.commcell.activate.sensitive_data_governance()
        self.ds_helper = DataSourceHelper(self.commcell)
        self.client_obj = self.commcell.clients.get(self.tcinputs["SDGClient"])
        self.agent_obj = self.client_obj.agents.get("File System")

    def run(self):
        """Run function of this test case"""
        try:
            self.pre_cleanup()
            self.create_plan_inventory()
            self.validate_plan_inventory()
            self.add_sdg_project()
            self.setup_new_user()
            self.validate_sharing()
            self.setup_data()
            self.validate_schedule()
            self.validate_sdg_project()

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
