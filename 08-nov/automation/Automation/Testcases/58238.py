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

    recreate_index_server()                     --  deletes and recreates the index directory of data source core

    index_server_setup()                        --  Setups the roles needed for index server

    create_data_source_import_data()            --  Creates the open data source,imports some random data
                                                                                        and create handler

    run_backup_and_import_more_data()           --  run solr backup and import more data to the open data source

    index_server_restore_and_fetch_data()       --  do in-place restore of index server for open data source core
                                                                        and fetch data using data source handler

    validate_data()                             --  validate data before backup and after restore matches

"""

import calendar
import time

from cvpysdk.datacube.constants import IndexServerConstants as index_constants
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.index_server_helper import IndexServerHelper


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
        self.name = "Validate IN-place restore of particular solr core on new index server using Open Data Source"
        self.tcinputs = {
            "IndexServerName": None,
            "StoragePolicyCopy": None,
            "StoragePolicy": None
        }
        self.index_server_obj = None
        self.timestamp = None
        self.data_source_name = "SolrBackup_"
        self.data_source_obj = None
        self.data_source_column = ['Id', 'Date', 'Name']
        self.data_source_column_type = ['int', 'date', 'string']
        self.index_server_roles = [index_constants.ROLE_DATA_ANALYTICS, index_constants.ROLE_EXCHANGE_INDEX]
        self.total_crawlcount = 0
        self.ds_helper = None
        self.handler_name = None
        self.handler_obj = None
        self.data_before_backup = None
        self.data_after_restore = None
        self.backup_job_id = None
        self.index_server_helper = None

    def recreate_index_server(self):
        """deletes and recreates the index directory of data source core"""

        src_machine_obj = Machine(machine_name=self.index_server_obj.client_name[0],
                                  commcell_object=self.commcell)

        analytics_dir = src_machine_obj.get_registry_value(commvault_key=dynamic_constants.ANALYTICS_REG_KEY,
                                                           value=dynamic_constants.ANALYTICS_DIR_REG_KEY)
        self.log.info("Index server Index directory is : %s", analytics_dir)
        self.log.info("Stopping the index server process")
        dest_client_obj = self.commcell.clients.get(self.index_server_obj.client_name[0])
        dest_client_obj.stop_service(service_name=dynamic_constants.ANALYTICS_SERVICE_NAME)
        self.log.info("Wait two minute for solr to go down")
        time.sleep(120)
        # remove only the index directory. confhome cant be removed as it is not supported during restore
        dir_to_remove = f"{analytics_dir}\\{self.data_source_obj.computed_core_name}"
        self.log.info("Remove the index dir of open data source code : %s", dir_to_remove)
        src_machine_obj.remove_directory(directory_name=dir_to_remove)
        self.log.info("Starting the index server process")
        dest_client_obj.start_service(service_name=dynamic_constants.ANALYTICS_SERVICE_NAME)
        self.log.info("Wait two minute for solr to come up")
        time.sleep(120)

    def index_server_setup(self):
        """Setups the roles needed for index server"""
        self.index_server_helper.update_roles(index_server_roles=self.index_server_roles)
        self.index_server_obj = self.index_server_helper.index_server_obj

    def create_data_source_import_data(self):
        """Creates the open data source and imports some random data"""
        self.log.info("Going to create open data source : %s", self.data_source_name)
        self.data_source_obj = self.ds_helper.create_open_data_source(
            data_source_name=self.data_source_name,
            index_server_name=self.tcinputs['IndexServerName'])
        self.log.info("Going to do update schema on data source")
        self.ds_helper.update_data_source_schema(data_source_name=self.data_source_name,
                                                 field_name=self.data_source_column,
                                                 field_type=self.data_source_column_type,
                                                 schema_field=dynamic_constants.SCHEMA_FIELDS)
        self.log.info("Calling Import data")
        self.total_crawlcount = self.ds_helper.import_random_data(data_source_name=self.data_source_name,
                                                                  field_name=self.data_source_column,
                                                                  field_type=self.data_source_column_type, rows=5)
        self.log.info("Calling hard commit for this data source on index server")
        self.index_server_obj.hard_commit(core_name=self.data_source_obj.computed_core_name)
        self.log.info("Going to create new handler : %s", self.handler_name)
        self.data_source_obj.ds_handlers.add(self.handler_name, search_query=['*'])
        self.log.info("Get Handler object for the newly created handler from this datasource")
        self.handler_obj = self.data_source_obj.ds_handlers.get(self.handler_name)
        self.data_before_backup = self.handler_obj.get_handler_data(
            handler_filter=dynamic_constants.SOLR_FETCH_HUNDRED_ROW)
        self.log.info("Before Backup Handler Data  : %s", str(self.data_before_backup))

    def run_backup_and_import_more_data(self):
        """run solr backup and import more data to the data source"""
        self.log.info("Make sure default subclient has all roles in backup content")
        self.index_server_helper.subclient_obj.configure_backup(storage_policy=self.tcinputs['StoragePolicy'],
                                                                role_content=self.index_server_roles)
        self.backup_job_id = self.index_server_helper.run_full_backup()
        self.log.info("Going to import more data to data source : %s", self.data_source_name)
        self.ds_helper.import_random_data(data_source_name=self.data_source_name,
                                          field_name=self.data_source_column,
                                          field_type=self.data_source_column_type, rows=5)
        self.log.info("Calling hard commit for this data source on index server")
        self.index_server_obj.hard_commit(core_name=self.data_source_obj.computed_core_name)
        response_out = self.handler_obj.get_handler_data(handler_filter=dynamic_constants.SOLR_FETCH_HUNDRED_ROW)
        self.log.info("Handler Data  : %s", str(response_out))
        total_docs = response_out['numFound']
        if total_docs == self.total_crawlcount:
            msg = f"Import didnt happen properly. Expected count : 10 Actual count :  {total_docs}"
            raise Exception(msg)
        self.log.info("Import more data finished. Current index server doc count for this data source : %s", total_docs)

    def index_server_restore_and_fetch_data(self):
        """do in-place restore of index server for data analytics role and fetch data using data source handler"""
        role_to_restore = [index_constants.ROLE_DATA_ANALYTICS]
        self.log.info("Going to do in-place restore of index server for open data source core : %s", role_to_restore)
        job_obj = self.index_server_helper.subclient_obj.do_restore_in_place(
            core_name=[f"{index_constants.ROLE_DATA_ANALYTICS}\\{self.data_source_obj.computed_core_name}"])
        self.index_server_helper.monitor_restore_job(job_obj=job_obj)
        self.data_after_restore = self.handler_obj.get_handler_data(
            handler_filter=dynamic_constants.SOLR_FETCH_HUNDRED_ROW)
        self.log.info("After restore Handler Data  : %s", str(self.data_after_restore))
        total_docs = self.data_after_restore['numFound']
        self.log.info("Current index server doc count for this data source : %s", total_docs)

    def validate_data(self):
        """validate data before backup and data after restore matches in index server via handler"""
        self.log.info("Going to cross verify data before backup and after restore for this data source")
        is_data_valid = self.ds_helper.validate_data_from_handler_response(source_data=self.data_before_backup,
                                                                           dest_data=self.data_after_restore)
        if not is_data_valid:
            raise Exception("Document not matched after index server restore. Please check logs")

    def setup(self):
        """Setup function of this test case"""
        self.timestamp = calendar.timegm(time.gmtime())
        self.data_source_name = f"{self.data_source_name}{self.timestamp}"
        self.handler_name = f"SolrBackup_Handler_{self.timestamp}"
        self.ds_helper = DataSourceHelper(self.commcell)
        self.index_server_helper = IndexServerHelper(self.commcell, self.tcinputs['IndexServerName'])
        self.log.info("Index server helper intialized")
        self.index_server_setup()
        self.index_server_helper.init_subclient()
        self.index_server_obj = self.index_server_helper.index_server_obj
        self.create_data_source_import_data()

    def run(self):
        """Run function of this test case"""
        try:
            self.run_backup_and_import_more_data()
            self.recreate_index_server()
            self.index_server_restore_and_fetch_data()
            self.validate_data()

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
            self.log.info("Going to delete the full backup job : %s", self.backup_job_id)
            storage_copy_obj = self.commcell.storage_policies.get(self.tcinputs['StoragePolicy']) \
                .get_copy(self.tcinputs['StoragePolicyCopy'])
            storage_copy_obj.delete_job(self.backup_job_id)
            self.log.info("Deleted the Full backup job")
