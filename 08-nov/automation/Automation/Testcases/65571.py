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
        self.dcube_helper = None
        self.dssync_regname = "nLastDCubeSyncTime"
        self.sync_helper = None
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
        self._before_metering = None
        self._after_metering = None
        self.name = "Validate Activate Metering Stored Procedure call by creating File system SDG Data Sources"
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
            crawl_path=self.path
        )
        self.log.info("SDG data source added successfully")
        self.all_ds_obj = sdg_proj_obj.data_sources
        self.sdk_helper = ActivateSDKHelper(commcell_object=self.commcell,
                                            app_entity=sdg_proj_obj,
                                            data_source=self.ds_name)
        job_id = self.sdk_helper.get_latest_job_id()
        self.ds_helper.monitor_crawl_job(job_id=job_id)
        self.log.info(f"Crawl job - {job_id} completed")

    def setup(self):
        """Setup function of this test case"""

        try:
            self.sync_helper = SyncHelper(self)
            self.dcube_helper = SolrHelper(self)
            self.ds_helper = DataSourceHelper(self.commcell)
            self.timestamp = calendar.timegm(time.gmtime())
            self.sdg_client = self.tcinputs['SDGClient']
            self.index_server = self.tcinputs['IndexServer']
            self.sdg_project_name = "DcubesyncCA_Project_%s" % self.id
            self.plan_name = "Dcubesync_TestPlan_%s" % self.id
            self.ds_name = "Dcubesync_DataSource_%s" % self.id
            self.inv_name = "Dcubesync_Inventory_%s" % self.id
            self.plans_obj = self.commcell.plans
            self.invs_obj = self.commcell.activate.inventory_manager()
            self.sdg_obj = self.commcell.activate.sensitive_data_governance()
            self.ca_helper = ContentAnalyzerHelper(self)
            self.crawl_helper = CrawlJobHelper(self)
            self.sdk_helper = ActivateSDKHelper(commcell_object=self.commcell)
            self.cleanup()

            # do clean up and then get meter stats
            self.log.info(f"Before Metering Data for SDG as follows")
            self._before_metering = self.sync_helper.execute_metering_sp(TargetApps.SDG)

            self.path = self.crawl_helper.create_files_with_content(
                client_names=[self.sdg_client], count=self.sensitive_files, content="Email is xhyhtyem@gmail.com")
            machine_obj = Machine(machine_name=self.sdg_client, commcell_object=self.commcell)
            self.crawl_helper.create_files_with_content(
                client_names=[
                    self.sdg_client],
                count=1000,
                content="Email is wrongemailgmail.com",
                folder=f"{self.path[0]}{machine_obj.os_sep}Non_Entity_files")
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

            current_time = datetime.datetime.now()
            self.sync_helper.set_dcube_sync_registry(current_time, 2, 24, True)
            statusxml = self.sync_helper.get_syncxml_by_csrestart(self.ds_obj.data_source_id, restart_required=True)
            self.log.info(f"Status xml got - {statusxml}")
            solr_core_name = self.ds_obj.computed_core_name
            self.log.info(f"Datasource computed core name is : {solr_core_name}")
            stats_response = self.sync_helper.get_core_stats(
                index_server=self.index_server, core_name=solr_core_name, is_fso=False)

            # validation starts for metering
            self.log.info(f"After Metering Data for SDG as follows")
            self._after_metering = self.sync_helper.execute_metering_sp(TargetApps.SDG)
            if len(self._after_metering.rows) != len(self._before_metering.rows) + 1:
                raise Exception("Got more rows from SP than expected count. Please check logs")
            self.sync_helper.validate_metering(
                metering_data=self._after_metering.rows,
                stats=stats_response,
                is_fso=False,
                client_id=self.commcell.clients.get(
                    self.tcinputs['SDGClient']).client_id,
                ds_id=self.ds_obj.data_source_id)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: ')
            self.result_string = str(exp)
            self.log.exception(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("Delete the activate entities created")
            ds_id = self.ds_obj.data_source_id
            self.cleanup()
            self.log.info(f"After cleanup - Metering Data for SDG as follows")
            self._after_metering = self.sync_helper.execute_metering_sp(TargetApps.SDG)
            for entry in self._after_metering.rows:
                if entry[dynamic_constants.ASSOCIATED_DS_PARAM] == ds_id:
                    raise Exception(f"Metering data still comes for data source which got deleted")
            self.log.info("Metering data is not available for deleted data source")
            self.log.info(f"Deleting the test data folder on client analyzed - {self.path[0]}")
            machine_obj = Machine(machine_name=self.sdg_client, commcell_object=self.commcell)
            machine_obj.remove_directory(directory_name=self.path[0])
