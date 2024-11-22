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
    __init__()              --  initialize TestCase class

    setup()                 --  setup function of this test case

    create_plan_inventory() --  Create plan and inventory for FSO

    add_fso_server()        --  Adds FSO server data source

    Monitor_job()           --  Monitors crawl job

    validate_fso_metering() --  Validates metering for FSO data source

    cleanup()               --  Deletes the activate entities created in this testcase

    run()                   --  run function of this test case

    tear_down()             --  tear down function of this test case

"""
import calendar
import time
import datetime

from cvpysdk.activateapps.constants import TargetApps
from cvpysdk.activateapps.constants import EdiscoveryConstants as edisconstant

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.Datacube.dcube_sync_helper import SyncHelper
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
        self.datasource_id = None
        self.total_crawlcount = 0
        self.sync_helper = None
        self.ds_name = None
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
        self.machine_obj = None
        self._before_metering = None
        self._after_metering = None
        self.name = "Validate Activate Metering Stored Procedure call by creating File system FSO Data Sources"
        self.tcinputs = {
            "FSOClient": None,
            "LocalPath": None,
            "IndexServer": None
        }

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

    def add_fso_server(self):
        """Adds FSO server to commcell"""
        self.log.info("Going to add FSO data source")
        self.fso_client_obj = self.fso_obj.add_file_server(
            server_name=self.fso_client,
            data_source_name=self.ds_name,
            inventory_name=self.inv_name,
            plan_name=self.plan_name,
            source_type=edisconstant.SourceType.SOURCE,
            crawl_path=[self.path])
        self.log.info("FSO data source added successfully")
        self.all_ds_obj = self.fso_client_obj.data_sources
        self.ds_obj = self.all_ds_obj.get(self.ds_name)
        self.datasource_id = self.ds_obj.data_source_id
        self.monitor_job()
        self.total_crawlcount = self.ds_obj.total_documents

    def monitor_job(self):
        """Monitor crawl job invoked on data source"""
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

    def setup(self):
        """Setup function of this test case"""
        try:
            self.machine_obj = Machine(machine_name=self.commcell.clients.get(self.tcinputs['FSOClient']),
                                       commcell_object=self.commcell)
            self.sync_helper = SyncHelper(self)
            self.ds_name = f'dcubesync_fso_{str(calendar.timegm(time.gmtime()))}'
            self.fso_client = self.tcinputs['FSOClient']
            self.path = self.tcinputs['LocalPath']
            self.index_server = self.tcinputs['IndexServer']
            self.plan_name = "DsSync_fso_TestPlan_%s" % self.id
            self.ds_name = "DsSync_fso__DataSource_%s" % self.id
            self.inv_name = "DsSync_fso__Inventory_%s" % self.id
            self.plans_obj = self.commcell.plans
            self.invs_obj = self.commcell.activate.inventory_manager()
            self.fso_obj = self.commcell.activate.file_storage_optimization()
            self.ds_helper = DataSourceHelper(self.commcell)
            self.cleanup()
            # do clean up and then get meter stats
            self.log.info(f"Before Metering Data for FSO as follows")
            self._before_metering = self.sync_helper.execute_metering_sp(TargetApps.FSO)

            # generate test data
            self.ds_helper.populate_test_data(machine_obj=self.machine_obj, test_data_path=self.path,
                                              folder_name="INCR", file_count=500, file_name="incr.txt")
            self.log.info(f"Test data generated successfully.")

        except Exception as ee:
            self.log.error('Setup for the test case failed. Error:')
            self.log.exception(ee)
            self.result_string = str(ee)
            self.status = constants.FAILED
            raise Exception("Test case setup(Creation of Datasource failed). Please check")

    def validate_fso_metering(self):
        """validates fso metering data"""
        solr_core_name = self.ds_obj.computed_core_name
        current_time = datetime.datetime.now()
        self.sync_helper.set_dcube_sync_registry(current_time, 2, 24, True)
        statusxml = self.sync_helper.get_syncxml_by_csrestart(self.datasource_id, restart_required=True)
        self.log.info(f"Sync xml - {statusxml}")
        self.log.info(f"Datasource computed core name is : {solr_core_name}")
        stats_response = self.sync_helper.get_core_stats(index_server=self.index_server, core_name=solr_core_name)
        self.log.info(f"After Metering Data for FSO as follows")
        self._after_metering = self.sync_helper.execute_metering_sp(TargetApps.FSO)
        if len(self._after_metering.rows) != len(self._before_metering.rows) + 1:
            raise Exception("Got more rows from SP than expected count. Please check logs")
        self.sync_helper.validate_metering(metering_data=self._after_metering.rows,
                                           stats=stats_response, is_fso=True, client_id=self.ds_obj.client_id,
                                           ds_id=self.ds_obj.data_source_id)

    def run(self):
        """Run function of this test case"""
        try:
            self.create_plan_inventory()
            self.add_fso_server()
            self.validate_fso_metering()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: ')
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def cleanup(self):
        """Deletes the activate entites"""
        self.log.info("Deleting DataSource")
        if self.fso_obj.has_server(self.fso_client):
            self.fso_client_obj = self.fso_obj.get(self.fso_client)
            self.all_ds_obj = self.fso_client_obj.data_sources
            if self.all_ds_obj.has_data_source(self.ds_name):
                self.all_ds_obj.delete(self.ds_name)
        self.log.info("Deleting inventory")
        if self.invs_obj.has_inventory(self.inv_name):
            self.invs_obj.delete(self.inv_name)
        self.log.info("Deleting DC Plan")
        if self.plans_obj.has_plan(self.plan_name):
            self.plans_obj.delete(self.plan_name)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("Cleaning up Environment")
            ds_id = self.ds_obj.data_source_id
            self.cleanup()
            self.log.info(f"After cleanup - Metering Data for FSO as follows")
            self._after_metering = self.sync_helper.execute_metering_sp(TargetApps.FSO)
            for entry in self._after_metering.rows:
                if entry[dynamic_constants.ASSOCIATED_DS_PARAM] == ds_id:
                    raise Exception(f"Metering data still comes for data source which got deleted")
            self.log.info("Metering data is not available for deleted data source")
