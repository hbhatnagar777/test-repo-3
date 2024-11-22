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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
import calendar
import time

from cvpysdk.activateapps.constants import TargetApps
from cvpysdk.activateapps.constants import EdiscoveryConstants as edisconstant


from AutomationUtils import constants
from AutomationUtils.Performance.Utils.constants import GeneralConstants
from AutomationUtils.Performance.Utils.constants import JobTypes
from AutomationUtils.Performance.Utils.performance_helper import PerformanceHelper
from AutomationUtils.Performance.performance_monitor import PerformanceMonitor
from AutomationUtils.Performance.reportbuilder import ReportBuilder
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.Datacube.data_source_helper import DataSourceHelper


_CONFIG_DATA = get_config().DynamicIndex.PerformanceStats


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
        self.name = "Activate Performance Automation - FSO quick crawl job for backup data"
        self.tcinputs = {
            "IndexServerName": None,
            "FsoClientName": None

        }
        self.fso_client = None
        self.index_server = None
        self.plan_name = None
        self.ds_name = None
        self.inv_name = None
        self.plan_obj = None
        self.plans_obj = None
        self.inv_obj = None
        self.invs_obj = None
        self.fso_obj = None
        self.ds_obj = None
        self.all_ds_obj = None
        self.ds_helper = None
        self.job_id = None
        self.build_id = str(calendar.timegm(time.gmtime()))
        self.perf_monitor = None
        self.perf_helper = None
        self.monitor_config = None
        self.data_source_name = None

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
        self.log.info("Inventory got created. Waiting 5Mins for crawl job on inventory to finish")
        time.sleep(420)
        self.log.info("Inventory crawl job got completed")

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Initializing all FSO Entities class objects")
        self.fso_client = self.tcinputs['FsoClientName']
        self.index_server = self.tcinputs['IndexServerName']
        self.plan_name = "PerformanceFSO_quick_TestPlan_%s" % self.id
        self.ds_name = "PerformanceFSO_quick_DataSource_%s" % self.id
        self.inv_name = "PerformanceFSO_quick_Inventory_%s" % self.id
        self.plans_obj = self.commcell.plans
        self.invs_obj = self.commcell.activate.inventory_manager()
        self.fso_obj = self.commcell.activate.file_storage_optimization()
        self.ds_helper = DataSourceHelper(self.commcell)
        self.perf_monitor = PerformanceMonitor(commcell_object=self.commcell, build_id=self.build_id)
        self.perf_helper = PerformanceHelper(commcell_object=self.commcell)
        self.monitor_config = self.perf_helper.form_fso_monitor_param(index_server=self.tcinputs['IndexServerName'],
                                                                      job_type=JobTypes.FSO_BACKUP_QUICK_SCAN
                                                                      )
        self.perf_monitor.push_configurations(config_data=self.monitor_config)

    def add_fso_server(self):
        """Adds FSO server to commcell"""

        self.log.info("Going to add FSO data source")
        fso_client_obj = self.fso_obj.add_file_server(
            server_name=self.fso_client,
            data_source_name=self.ds_name,
            inventory_name=self.inv_name,
            plan_name=self.plan_name,
            source_type=edisconstant.SourceType.BACKUP
        )
        self.log.info("FSO data source added successfully")
        self.all_ds_obj = fso_client_obj.data_sources
        self.ds_obj = self.all_ds_obj.get(self.ds_name)
        self.log.info("Going to get job id for the created data source")
        ds_helper = DataSourceHelper(self.commcell)
        self.data_source_name = ds_helper.get_data_source_starting_with_string(
            start_string=self.ds_name)
        self.log.info("DataSource name : %s", self.data_source_name)
        jobs = self.ds_obj.get_active_jobs()
        if not jobs:
            self.log.info("Active job list returns zero list. so checking for job history")
            jobs = self.ds_obj.get_job_history()
            if not jobs:
                raise Exception("Online crawl job didn't get invoked for FSO server added")
        self.log.info(f"Job History details got - {jobs}")
        job_id = list(jobs.keys())
        job_id = [int(i) for i in job_id]
        job_id.sort(reverse=True)
        self.job_id = job_id[0]
        self.log.info(f"Online crawl job invoked with id - {self.job_id}")

    def delete_validate_fso_entities(self):
        """Deletes FSO entities and validates whether it got deleted or not"""

        self.log.info("Deleting DataSource")
        self.all_ds_obj.delete(self.ds_name)
        self.log.info("Deleting inventory")
        self.invs_obj.delete(self.inv_name)
        self.log.info("Deleting DC Plan")
        self.plans_obj.delete(self.plan_name)

    def run(self):
        """Run function of this test case"""
        try:
            self.create_plan_inventory()
            self.add_fso_server()

            # Monitor the job performance
            self.perf_monitor.start_monitor(job_id=self.job_id,
                                            job_type=JobTypes.FSO_BACKUP_QUICK_SCAN,
                                            config=self.monitor_config,
                                            push_to_data_source=True,
                                            **{GeneralConstants.DATA_SOURCE_NAME_PARAM: self.data_source_name,
                                               GeneralConstants.DYNAMIC_COLUMN_SOURCE_NAME: "QuickScan_Backup_Scale_Data",
                                               GeneralConstants.DYNAMIC_COLUMN_SOURCE_SIZE: "20Million"})

            # Generate performance report for this job
            report_helper = ReportBuilder(commcell_object=self.commcell,
                                          job_id=self.job_id,
                                          job_type=JobTypes.FSO_BACKUP_QUICK_SCAN,
                                          build_id=self.build_id,
                                          use_data_source=True)
            report_helper.generate_report(
                send_mail=True,
                receivers=self.inputJSONnode[GeneralConstants.EMAIL_NODE_NAME][GeneralConstants.RECEIVER_NODE_VALUE])

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("Going to delete FSO Environment entities")
            self.delete_validate_fso_entities()
