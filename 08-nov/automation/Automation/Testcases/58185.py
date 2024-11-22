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

    index_server_setup()                        --  Setups the roles needed for index server

    create_data_source_import_data()            --  Creates the open & File system data source
                                                                        and imports some random data

    soft_delete_data()                          --  deletes the data from data sources

    run_backup()                                --  run solr backup

    index_server_restore_and_fetch_data()       --  do in-place restore of file system data source core and
                                                                            fetch data using data source handler

    validate_data()                             --  validate data before backup and after restore matches

    reverify_crawl()                            --  reruns crawl job on data sources

"""

import calendar
import time

from cvpysdk.datacube.constants import IndexServerConstants as index_constants
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
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
        self.name = "Validate IN-place restore of particular FS core of DS role from solr backup"
        self.tcinputs = {
            "IndexServerName": None,
            "StoragePolicyCopy": None,
            "StoragePolicy": None,
            "AccessNode": None,
            "IncludedirectoriesPath": None,
            "UserName": None,
            "Password": None,
            "PlainPassword": None
        }
        self.index_server_obj = None
        self.timestamp = None
        self.crawl_helper = None
        self.source_file_count = 0
        self.op_data_source_name = "Open_SolrBackup_"
        self.op_data_source_obj = None
        self.fs_data_source_name = "FS_SolrBackup_"
        self.fs_data_source_obj = None
        self.op_data_source_column = ['Id', 'Date', 'Name']
        self.op_data_source_column_type = ['int', 'date', 'string']
        self.index_server_roles = [index_constants.ROLE_DATA_ANALYTICS]
        self.op_total_crawlcount = 0
        self.ds_helper = None
        self.op_handler_name = None
        self.op_handler_obj = None
        self.op_data_before_backup = None
        self.op_data_after_restore = None
        self.fs_handler_name = None
        self.fs_handler_obj = None
        self.fs_data_before_backup = None
        self.fs_data_after_restore = None
        self.backup_job_id = None
        self.index_server_helper = None

    def index_server_setup(self):
        """Setups the roles needed for index server"""
        self.index_server_helper.update_roles(index_server_roles=self.index_server_roles)
        self.index_server_obj = self.index_server_helper.index_server_obj

    def create_data_source_import_data(self):
        """Creates the open & File system data source and imports some random data"""
        self.log.info("Going to create file system data source : %s", self.fs_data_source_name)

        access_node_client_obj = self.commcell.clients.get(
            self.tcinputs['AccessNode'])
        self.log.info("Client object Initialised")
        access_node_clientid = access_node_client_obj.client_id
        self.log.info("Accessnode Client id : %s", str(access_node_clientid))

        fs_dynamic_property = {
            "includedirectoriespath": self.tcinputs['IncludedirectoriesPath'],
            "username": self.tcinputs['UserName'],
            "password": self.tcinputs['Password'],
            "accessnodeclientid": access_node_clientid
        }
        file_properties = self.ds_helper.form_file_data_source_properties(fs_dynamic_property)

        self.fs_data_source_obj = self.ds_helper.create_file_data_source(data_source_name=self.fs_data_source_name,
                                                                         index_server_name=self.tcinputs[
                                                                             'IndexServerName'],
                                                                         fs_properties=file_properties)

        self.crawl_helper.monitor_crawl_job(self.fs_data_source_name)

        self.log.info("Going to create open data source : %s", self.op_data_source_name)
        self.op_data_source_obj = self.ds_helper.create_open_data_source(
            data_source_name=self.op_data_source_name,
            index_server_name=self.tcinputs['IndexServerName'])
        self.log.info("Going to do update schema on data source")
        self.ds_helper.update_data_source_schema(data_source_name=self.op_data_source_name,
                                                 field_name=self.op_data_source_column,
                                                 field_type=self.op_data_source_column_type,
                                                 schema_field=dynamic_constants.SCHEMA_FIELDS)
        self.log.info("Calling Import data on open data source")
        self.op_total_crawlcount = self.ds_helper.import_random_data(data_source_name=self.op_data_source_name,
                                                                     field_name=self.op_data_source_column,
                                                                     field_type=self.op_data_source_column_type, rows=5)
        self.log.info("Calling hard commit for this data source on index server")
        self.index_server_obj.hard_commit(core_name=self.op_data_source_obj.computed_core_name)

        self.log.info("Going to create new handler for file system: %s", self.fs_handler_name)
        self.fs_data_source_obj.ds_handlers.add(self.fs_handler_name, search_query=['*'])
        self.log.info("Get Handler object for the newly created handler for FS datasource")
        self.fs_handler_obj = self.fs_data_source_obj.ds_handlers.get(self.fs_handler_name)
        self.fs_data_before_backup = self.fs_handler_obj.get_handler_data(
            handler_filter=dynamic_constants.SOLR_FETCH_HUNDRED_ROW)
        self.log.info("Before Backup Handler Data for FS data source : %s", str(self.fs_data_before_backup))
        if self.source_file_count != self.fs_data_before_backup['numFound']:
            raise Exception("Crawl count & source count not matched for FS data source. Please check logs")

        self.log.info("Going to create new handler for open data source : %s", self.op_handler_name)
        self.op_data_source_obj.ds_handlers.add(self.op_handler_name, search_query=['*'])
        self.log.info("Get Handler object for the newly created handler from open datasource")
        self.op_handler_obj = self.op_data_source_obj.ds_handlers.get(self.op_handler_name)

    def soft_delete_data(self):
        """soft deletes the data from data sources"""
        self.log.info("Going to do soft delete on both data sources")
        self.op_data_source_obj.delete_content()
        self.fs_data_source_obj.delete_content()
        self.log.info("Soft data delete succeded")
        total_docs = self.fs_handler_obj.get_handler_data(
            handler_filter=dynamic_constants.SOLR_FETCH_HUNDRED_ROW)
        if total_docs['numFound'] != 0:
            raise Exception("Soft delete on File system data source is not success")
        total_docs = self.op_handler_obj.get_handler_data(
            handler_filter=dynamic_constants.SOLR_FETCH_HUNDRED_ROW)
        if total_docs['numFound'] != 0:
            raise Exception("Soft delete on Open data source is not success")
        self.op_data_before_backup = self.op_handler_obj.get_handler_data(
            handler_filter=dynamic_constants.SOLR_FETCH_HUNDRED_ROW)
        self.log.info("Before Restore Handler Data for open data source : %s", str(self.op_data_before_backup))

    def run_backup(self):
        """run solr backup"""
        self.log.info("Make sure default subclient has all roles in backup content")
        self.index_server_helper.subclient_obj.configure_backup(storage_policy=self.tcinputs['StoragePolicy'],
                                                                role_content=self.index_server_roles)
        self.backup_job_id = self.index_server_helper.run_full_backup()

    def index_server_restore_and_fetch_data(self):
        """do in-place restore of file system data source core and fetch data using data source handler"""
        core_to_restore = [f"{index_constants.ROLE_DATA_ANALYTICS}\\{self.fs_data_source_obj.computed_core_name}"]
        self.log.info("Going to do in-place restore of index server for core : %s", core_to_restore)
        job_obj = self.index_server_helper.subclient_obj.do_restore_in_place(core_name=core_to_restore)
        self.index_server_helper.monitor_restore_job(job_obj=job_obj)
        self.op_data_after_restore = self.op_handler_obj.get_handler_data(
            handler_filter=dynamic_constants.SOLR_FETCH_HUNDRED_ROW)
        self.log.info("After restore Handler Data for open data source  : %s", str(self.op_data_after_restore))
        total_docs = self.op_data_after_restore['numFound']
        self.log.info("Current index server doc count for open data source : %s", total_docs)

        self.fs_data_after_restore = self.fs_handler_obj.get_handler_data(
            handler_filter=dynamic_constants.SOLR_FETCH_HUNDRED_ROW)
        self.log.info("After restore Handler Data for FS data source  : %s", str(self.fs_data_after_restore))
        total_docs = self.fs_data_after_restore['numFound']
        self.log.info("Current index server doc count for FS data source : %s", total_docs)

    def validate_data(self):
        """validate data before backup and data after restore matches in index server via handlers"""
        self.log.info("Going to cross verify data before backup and after restore for FS data source")
        is_data_valid = self.ds_helper.validate_data_from_handler_response(source_data=self.fs_data_before_backup,
                                                                           dest_data=self.fs_data_after_restore)
        if not is_data_valid:
            raise Exception("Document not matched for FS data source after index server restore. Please check logs")

        total_docs = self.op_data_after_restore['numFound']
        self.log.info("Total docs in open data source after index server restore : %s", total_docs)
        if total_docs != 0:
            raise Exception("Open data source has some data after restore. Please check")
        self.log.info("Total docs in open data source is zero. consider core level index server restore worked")

    def reverify_crawl(self):
        """rerun crawl job for file system & open data source"""
        self.crawl_helper.monitor_crawl_job(self.fs_data_source_name)
        self.fs_data_after_restore = self.fs_handler_obj.get_handler_data(
            handler_filter=dynamic_constants.SOLR_FETCH_HUNDRED_ROW)
        self.log.info("After restore Handler Data for FS data source  : %s", str(self.fs_data_after_restore))
        total_docs = self.fs_data_after_restore['numFound']
        self.log.info("Current index server doc count for FS data source : %s", total_docs)
        if self.source_file_count != total_docs:
            raise Exception("FS Recrawl count & source count not matched. Please check logs")
        self.log.info("FS Recrawl count matched. consider as success : %s", total_docs)

        self.log.info("Calling Import data on open data source")
        self.op_total_crawlcount = self.ds_helper.import_random_data(data_source_name=self.op_data_source_name,
                                                                     field_name=self.op_data_source_column,
                                                                     field_type=self.op_data_source_column_type, rows=5)
        self.log.info("Calling hard commit for this data source on index server")
        self.index_server_obj.hard_commit(core_name=self.op_data_source_obj.computed_core_name)

        self.op_data_after_restore = self.op_handler_obj.get_handler_data(
            handler_filter=dynamic_constants.SOLR_FETCH_HUNDRED_ROW)
        self.log.info("After restore Handler Data for open data source  : %s", str(self.op_data_after_restore))
        total_docs = self.op_data_after_restore['numFound']
        self.log.info("Current index server doc count for open data source : %s", total_docs)

        if self.op_total_crawlcount != total_docs:
            raise Exception("Open data source Recrawl count & source count not matched. Please check logs")
        self.log.info("Open data source Recrawl count matched. consider as success : %s", total_docs)

    def setup(self):
        """Setup function of this test case"""
        self.timestamp = calendar.timegm(time.gmtime())
        self.crawl_helper = CrawlJobHelper(self)
        self.op_data_source_name = f"{self.op_data_source_name}{self.timestamp}"
        self.op_handler_name = f"Open_SolrBackup_Handler_{self.timestamp}"
        self.fs_data_source_name = f"{self.fs_data_source_name}{self.timestamp}"
        self.fs_handler_name = f"File_SolrBackup_Handler_{self.timestamp}"
        self.ds_helper = DataSourceHelper(self.commcell)
        self.source_file_count = self.crawl_helper.get_docs_count(folder_path=self.tcinputs['IncludedirectoriesPath'],
                                                                  machine_name=self.tcinputs['AccessNode'],
                                                                  username=self.tcinputs['UserName'],
                                                                  password=self.tcinputs['PlainPassword'],
                                                                  include_folders=True)
        self.log.info("File system source count on access node : %s", self.source_file_count)
        self.index_server_helper = IndexServerHelper(self.commcell, self.tcinputs['IndexServerName'])
        self.log.info("Index server helper initialized")
        self.index_server_setup()
        self.index_server_helper.init_subclient()
        self.create_data_source_import_data()

    def run(self):
        """Run function of this test case"""
        try:
            self.run_backup()
            self.soft_delete_data()
            self.index_server_restore_and_fetch_data()
            self.validate_data()
            self.reverify_crawl()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("Going to delete open data source : %s", self.op_data_source_name)
            self.commcell.datacube.datasources.delete(self.op_data_source_name)
            self.log.info("Deleted the open data source : %s", self.op_data_source_name)
            self.log.info("Going to delete FS data source : %s", self.fs_data_source_name)
            self.commcell.datacube.datasources.delete(self.fs_data_source_name)
            self.log.info("Deleted the FS data source : %s", self.fs_data_source_name)
            self.log.info("Going to delete the full backup job : %s", self.backup_job_id)
            storage_copy_obj = self.commcell.storage_policies.get(self.tcinputs['StoragePolicy']) \
                .get_copy(self.tcinputs['StoragePolicyCopy'])
            storage_copy_obj.delete_job(self.backup_job_id)
            self.log.info("Deleted the Full backup job")
