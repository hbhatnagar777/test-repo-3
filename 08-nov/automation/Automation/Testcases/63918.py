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
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    tear_down()                                 --  tear down function of this test case

    validate_query()                            --  validates whether query api works for core

    validate_update()                           --  validates whether update api works for core

    create_data_source_import_data()            --  Creates the open data source and imports some random data

"""
import time
import calendar

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.index_server_helper import IndexServerHelper
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
        self.name = "Validate core load status in solr during query & update API calls"
        self.tcinputs = {
            "IndexServer": None
        }
        self.is_helper = None
        self.data_source_name = None
        self.ds_helper = None
        self.data_source_obj = None
        self.data_source_column = ['Id', 'Date', 'Name']
        self.data_source_column_type = ['int', 'date', 'string']
        self.total_crawlcount = None
        self.idle_timeout = 150
        # api interval based on above idle timeout
        self.api_interval = 90

    def validate_update(self):
        """validates whether update api works for core"""
        attempts = 5
        while attempts:
            time.sleep(self.api_interval)
            status = self.is_helper.is_core_loaded(core_name=self.data_source_obj.computed_core_name)
            if not status:
                raise Exception("Core got unloaded even in middle of updating")
            self.log.info(f"Try update core for attempt - {attempts}")
            attempts = attempts - 1
            self.ds_helper.import_random_data(data_source_name=self.data_source_name,
                                              field_name=self.data_source_column,
                                              field_type=self.data_source_column_type, rows=50)
            self.total_crawlcount = self.total_crawlcount + 50
            status = self.is_helper.is_core_loaded(core_name=self.data_source_obj.computed_core_name)
            if not status:
                raise Exception("Core got unloaded even in middle of updating")
        self.log.info("Core is in loaded status during entire update API call attempts")

    def validate_query(self):
        """validates whether query api works for core"""
        attempts = 5
        while attempts:
            time.sleep(self.api_interval)
            status = self.is_helper.is_core_loaded(core_name=self.data_source_obj.computed_core_name)
            if not status:
                raise Exception("Core got unloaded even in middle of querying")
            self.log.info(f"Try querying core for attempt - {attempts}")
            attempts = attempts - 1
            solr_response = self.is_helper.index_server_obj.execute_solr_query(
                core_name=self.data_source_obj.computed_core_name, op_params=dynamic_constants.QUERY_ZERO_ROWS)
            self.is_helper.check_solr_doc_count(solr_response=solr_response, doc_count=self.total_crawlcount)
            status = self.is_helper.is_core_loaded(core_name=self.data_source_obj.computed_core_name)
            if not status:
                raise Exception("Core got unloaded even in middle of querying")
        self.log.info("Core is in loaded status during entire query API call attempts")

    def create_data_source_import_data(self):
        """Creates the open data source, imports some random data"""
        self.log.info("Going to create open data source : %s", self.data_source_name)
        self.data_source_obj = self.ds_helper.create_open_data_source(
            data_source_name=self.data_source_name,
            index_server_name=self.tcinputs['IndexServer'])
        self.log.info("Going to do update schema on data source")
        self.ds_helper.update_data_source_schema(data_source_name=self.data_source_name,
                                                 field_name=self.data_source_column,
                                                 field_type=self.data_source_column_type,
                                                 schema_field=dynamic_constants.SCHEMA_FIELDS)
        self.log.info("Calling Import data")
        self.total_crawlcount = self.ds_helper.import_random_data(data_source_name=self.data_source_name,
                                                                  field_name=self.data_source_column,
                                                                  field_type=self.data_source_column_type, rows=50)
        self.log.info("Calling hard commit for this data source on index server")
        self.is_helper.index_server_obj.hard_commit(core_name=self.data_source_obj.computed_core_name)

    def setup(self):
        """Setup function of this test case"""
        self.data_source_name = "UnloadCoreTest_" + str(calendar.timegm(time.gmtime()))
        self.ds_helper = DataSourceHelper(self.commcell)
        self.is_helper = IndexServerHelper(commcell_object=self.commcell,
                                           index_server_name=self.tcinputs['IndexServer'])
        self.log.info("Setting unload core additional settings on index server")
        self.is_helper.set_unload_core_settings(max_core_loaded='1', idle_core_timeout=str(self.idle_timeout))
        self.is_helper.restart_svc_all_index_nodes()
        self.create_data_source_import_data()

    def run(self):
        """Run function of this test case"""
        try:
            start_time = time.time()
            self.validate_query()
            self.validate_update()
            end_time = time.time()
            elapsed = int(end_time - start_time) * 1000  # millisec conversion
            self.log.info(f"Total elapsed time - {elapsed}")
            core_stats = self.is_helper.get_core_stats(core_name=self.data_source_obj.computed_core_name)
            if dynamic_constants.FIELD_UPTIME in core_stats and core_stats[dynamic_constants.FIELD_UPTIME] > elapsed:
                self.log.info(
                    f"Core uptime [{core_stats[dynamic_constants.FIELD_UPTIME]}] is greater than elapsed time  [{elapsed}]. Consider it as success")
            else:
                raise Exception(
                    f"Core Uptime[{core_stats[dynamic_constants.FIELD_UPTIME]}] is less than elapsed time [{elapsed}]")

            self.log.info(f"Waiting for {self.idle_timeout * 3} seconds for unload to happen")
            time.sleep(self.idle_timeout * 3)
            status = self.is_helper.is_core_loaded(core_name=self.data_source_obj.computed_core_name)
            if status:
                raise Exception("Core is still in loaded status even after timeout interval")
            self.log.info("Unload core validation succeeded")

            # calling update should load the core.
            self.log.info("Core is in unload status. Try calling update API")
            self.ds_helper.import_random_data(data_source_name=self.data_source_name,
                                              field_name=self.data_source_column,
                                              field_type=self.data_source_column_type, rows=50)
            self.total_crawlcount = self.total_crawlcount + 50

            self.log.info("Calling hard commit for this data source on index server")
            self.is_helper.index_server_obj.hard_commit(core_name=self.data_source_obj.computed_core_name)

            solr_response = self.is_helper.index_server_obj.execute_solr_query(
                core_name=self.data_source_obj.computed_core_name, op_params=dynamic_constants.QUERY_ZERO_ROWS)

            self.is_helper.check_solr_doc_count(solr_response=solr_response, doc_count=self.total_crawlcount)
            self.log.info(f"Document count validation succeeded by querying  - Total docs - [{self.total_crawlcount}]")

            self.log.info(f"Waiting for {self.idle_timeout * 3} seconds for unload to happen")
            time.sleep(self.idle_timeout * 3)
            status = self.is_helper.is_core_loaded(core_name=self.data_source_obj.computed_core_name)
            if status:
                raise Exception("Core is still in loaded status even after timeout interval")
            self.log.info("Unload core validation succeeded")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("Going to delete open data source : %s", self.data_source_name)
            self.commcell.datacube.datasources.delete(self.data_source_name)
            self.log.info("Deleted the open data source : %s", self.data_source_name)
            self.log.info(f"Rolling back unload settings to default")
            self.is_helper.set_unload_core_settings()
            self.is_helper.restart_svc_all_index_nodes()
