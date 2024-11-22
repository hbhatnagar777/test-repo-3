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

    create_plan_inventory()     --  created inventory and plan for SDG

    add_sdg_project()           --  Adds SDG project

    cleanup()                   --  Cleans up the activate entities like plan, inventory & Project

    tear_down()                 --  tear down function of this test case

"""
import calendar
import os
import time
import datetime

from cvpysdk.activateapps.constants import TargetApps
from cvpysdk.activateapps.constants import EdiscoveryConstants as edisconstant

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.Datacube.data_source_helper import DataSourceHelper

from dynamicindex.Datacube.dcube_sync_helper import SyncHelper
from dynamicindex.Datacube.dcube_solr_helper import SolrHelper
from dynamicindex.activate_sdk_helper import ActivateSDKHelper
from dynamicindex.content_analyzer_helper import ContentAnalyzerHelper
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.utils.activateutils import ActivateUtils


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs    (dict)          --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.sensitive_files = 1000
        self.timestamp = None
        self.total_crawlcount = 0        
        self.dssync_regname = "nLastDCubeSyncTime"
        self.sync_helper = None
        self.sdg_client = None
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
        self.machine_obj = None
        self.name = "Validate sync disable and SDG FileSystem datasource Sync Status with failed items to CS DataBase"
        self.tcinputs = {
            "IndexServer": None,
            "SDGClient": None,
            "CAClouds": None
        }

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
        self.ds_obj = sdg_proj_obj.add_fs_data_source(
            server_name=self.sdg_client,
            data_source_name=self.ds_name,
            source_type=edisconstant.SourceType.SOURCE,
            crawl_path=[self.tcinputs['FileServerLocalDirectoryPath']]
        )
        self.log.info("SDG data source added successfully")
        self.all_ds_obj = sdg_proj_obj.data_sources
        self.sdk_helper = ActivateSDKHelper(commcell_object=self.commcell,
                                            app_entity=sdg_proj_obj,
                                            data_source=self.ds_name)
        job_id = self.sdk_helper.get_latest_job_id()
        self.ds_helper.monitor_crawl_job(job_id=job_id, raise_exception=False)
        self.log.info(f"Crawl job - {job_id} completed")

    def setup(self):
        """Setup function of this test case"""

        try:
            self.sync_helper = SyncHelper(self)            
            self.ds_helper = DataSourceHelper(self.commcell)
            self.timestamp = calendar.timegm(time.gmtime())
            self.sdg_client = self.tcinputs['SDGClient']
            self.index_server = self.tcinputs['IndexServer']
            self.sdg_project_name = "DcubesyncCA_Project_%s" % self.id
            self.plan_name = "Dcubesync_TestPlan_%s" % self.id
            self.ds_name = "Dcubesync_DataSource_%s" % self.id
            self.inv_name = "Dcubesync_Inventory_%s" % self.id
            self.ca_helper = ContentAnalyzerHelper(self)
            self.crawl_helper = CrawlJobHelper(self)
            self.sdk_helper = ActivateSDKHelper(commcell_object=self.commcell)
            self.plans_obj = self.commcell.plans
            self.invs_obj = self.commcell.activate.inventory_manager()
            self.sdg_obj = self.commcell.activate.sensitive_data_governance()
            activate_utils = ActivateUtils()
            self.machine_obj = Machine(machine_name=self.sdg_client, commcell_object=self.commcell)
            self.tcinputs['FileServerLocalDirectoryPath'] = f"{self.tcinputs['FileServerLocalDirectoryPath']}{self.machine_obj.os_sep}{self.timestamp}"
            self.cleanup()
            # encrypt file generation
            if not self.machine_obj.check_directory_exists(
                    directory_path=self.tcinputs['FileServerLocalDirectoryPath']):
                self.machine_obj.create_directory(
                    directory_name=self.tcinputs['FileServerLocalDirectoryPath'],
                    force_create=True)
            partial_path = os.path.splitdrive(
                self.tcinputs['FileServerLocalDirectoryPath'])[1]
            partial_path = partial_path.removeprefix(os.path.sep)
            partial_path = self.machine_obj.get_unc_path(partial_path)
            self.log.info(f"Encrypt/Corrupt Sensitive file generation path : {partial_path}")
            activate_utils.sensitive_data_generation(partial_path, number_files=600, encrypt=False,
                                                     corrupt=True)
            # test data generation

            self.crawl_helper.create_files_with_content(
                client_names=[
                    self.sdg_client],
                count=self.sensitive_files,
                content="Email is xhyhtyem@gmail.com",
                folder=f"{self.tcinputs['FileServerLocalDirectoryPath']}{self.machine_obj.os_sep}Entity_files")
            self.crawl_helper.create_files_with_content(
                client_names=[
                    self.sdg_client],
                count=1000,
                content="Email is wrongemailgmail.com",
                folder=f"{self.tcinputs['FileServerLocalDirectoryPath']}{self.machine_obj.os_sep}Non_Entity_files")

            self.create_plan_inventory()
            self.add_sdg_project()

        except Exception as ee:
            self.log.error('Setup for the test case failed.')
            self.log.exception(ee)
            self.result_string = str(ee)
            self.status = constants.FAILED
            raise Exception("Test case setup(Creation of Datasource failed). Please check")

    def cleanup(self):
        """Performs cleanup operations - Deletes SDG project, plan and inventory if they already exist"""
        self.sdk_helper.do_sdg_cleanup(plan_name=self.plan_name,
                                       project_name=self.sdg_project_name,
                                       inventory_name=self.inv_name)

    def run(self):
        """Run function of this test case"""
        try:
            # sync disable validation
            current_time = datetime.datetime.now()
            self.sync_helper.set_dcube_sync_registry(current_time, 2, 24, False)
            statusxml = self.sync_helper.get_syncxml_by_csrestart(self.ds_obj.data_source_id, restart_required=True)
            if not statusxml:
                self.log.info("Verified Datacube sync didn't happen")
            else:
                self.log.info("Datacube sync happened after setting disable key")
                raise Exception("Datacube sync happened after setting disable key")

            current_time = datetime.datetime.now()
            self.sync_helper.set_dcube_sync_registry(current_time, 2, 24, True)
            statusxml = self.sync_helper.get_syncxml_by_csrestart(self.ds_obj.data_source_id, restart_required=True)
            solr_core_name = self.ds_obj.computed_core_name
            self.log.info(f"Datasource computed core name is : {solr_core_name}")
            stats_response = self.sync_helper.get_core_stats(
                index_server=self.index_server, core_name=solr_core_name, is_fso=False)

            # validation starts
            testresult = self.sync_helper.verify_sync_xml(
                sync_xml=statusxml, core_stats=stats_response, is_fso=False)
            if testresult:
                self.log.info("Sync xml validation passed")
            else:
                raise Exception("Sync xml validation failed")

            # delete all sensitive files in folder and rerun crawl
            self.machine_obj.remove_directory(
                directory_name=f"{self.tcinputs['FileServerLocalDirectoryPath']}{self.machine_obj.os_sep}Entity_files")
            self.log.info("Removed the Entity files folder from test data generated")
            self.log.info("Started Incremental crawl on data source")
            self.ds_obj.start_collection()
            job_id = self.sdk_helper.get_latest_job_id()
            self.ds_helper.monitor_crawl_job(job_id=job_id)
            self.log.info(f"Incremental Crawl job - {job_id} completed")

            old_stats_sensitive_count = stats_response[dynamic_constants.SYNC_SUCCESS_STATE_PARAM][dynamic_constants.SENSITIVE_DOCS_PARAM]
            self.log.info(f"Success state sensitive files count : {old_stats_sensitive_count}")

            # revalidate the sync xml for deleted files
            current_time = datetime.datetime.now()
            self.sync_helper.set_dcube_sync_registry(current_time, 2, 24, True)
            statusxml = self.sync_helper.get_syncxml_by_csrestart(self.ds_obj.data_source_id, restart_required=True)
            solr_core_name = self.ds_obj.computed_core_name
            self.log.info(f"Datasource computed core name is : {solr_core_name}")
            stats_response = self.sync_helper.get_core_stats(
                index_server=self.index_server, core_name=solr_core_name, is_fso=False)

            new_stats_sensitive_count = stats_response[dynamic_constants.SYNC_SUCCESS_STATE_PARAM][
                dynamic_constants.SENSITIVE_DOCS_PARAM]
            self.log.info(f"Success state sensitive files count : {new_stats_sensitive_count}")

            if new_stats_sensitive_count != old_stats_sensitive_count - self.sensitive_files:
                raise Exception(
                    f"Sync xml not populated properly for sensitive doc count. Expected<{old_stats_sensitive_count - self.sensitive_files}> Actual<{new_stats_sensitive_count}>")
            self.log.info("Success state - Sensitive docs count matched")

            # validation starts
            testresult = self.sync_helper.verify_sync_xml(
                sync_xml=statusxml, core_stats=stats_response, is_fso=False)
            if testresult:
                self.log.info("Sync xml validation passed")
            else:
                raise Exception("Sync xml validation failed")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: ')
            self.result_string = str(exp)
            self.log.exception(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("Delete the activate entities created")
            self.cleanup()
            self.log.info(
                f"Deleting the test data folder on client analyzed - {self.tcinputs['FileServerLocalDirectoryPath']}")
            machine_obj = Machine(machine_name=self.sdg_client, commcell_object=self.commcell)
            machine_obj.remove_directory(directory_name=self.tcinputs['FileServerLocalDirectoryPath'])
