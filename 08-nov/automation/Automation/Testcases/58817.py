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

    index_server_setup()                        --  Setups the roles needed for index server

    create_data_source_start_crawl              --  Creates file system datasource and starts the crawl job

    run_backup()                                --  run solr backup

    validate_crawl()                            --  validates the crawl status of the data source

    do_restore()                                --  do in-place restore of data analytics role

    validate_data()                             --  validates document count of the data source after restore

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    tear_down()                                 --  tear down function of this test case

"""

import calendar
import time

from cvpysdk.datacube.constants import IndexServerConstants as index_constants
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.utils.constants import ENTITY_EXTRACTION_CLOUDID
from dynamicindex.index_server_helper import IndexServerHelper
from Server.JobManager.jobmanager_helper import JobManager


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
        self.name = "Validate solr backup during live crawl of FS Datasource"
        self.datasource_obj = None
        self.timestamp = None
        self.total_crawlcount = 0
        self.fs_data_source_name = "SolrBackup_"
        self.ds_helper = None
        self.crawl_helper = None
        self.index_server_helper = None
        self.index_server_obj = None
        self.backup_job_id = None
        self.crawl_job_id = None
        self.doc_count_before_backup = 0
        self.index_server_roles = [index_constants.ROLE_DATA_ANALYTICS]
        self.entities_to_extract = {
            "RER": 'Email,Credit Card Number'
        }
        self.job_helper = None
        self.tcinputs = {
            "IndexServerName": None,
            "IncludedirectoriesPath": None,
            "AccessNode": None,
            "CANode": None,
            "StoragePolicyCopy": None,
            "StoragePolicy": None
        }

    def validate_data(self):
        """validates document count of the data source after restore"""
        self.log.info("Querying solr core to get document count : %s", self.datasource_obj.computed_core_name)
        resp = self.index_server_obj.execute_solr_query(core_name=self.datasource_obj.computed_core_name)
        current_count = resp['response']['numFound']
        self.log.info("Current document count in solr after doing restore : %s", current_count)
        if current_count < self.doc_count_before_backup:
            raise Exception("Solr backup on core missed few documents. Please check logs")
        if current_count >= self.total_crawlcount:
            raise Exception("Solr backup didnt happen properly during live crawl. Please check logs")
        self.log.info("Current document count matched the criteria. Consider as pass")

    def do_restore(self):
        """do in-place restore of data analytics role"""
        role_to_restore = [index_constants.ROLE_DATA_ANALYTICS]
        self.log.info("Going to do in-place restore of index server for role : %s", role_to_restore)
        job_obj = self.index_server_helper.subclient_obj.do_restore_in_place(roles=role_to_restore)
        self.index_server_helper.monitor_restore_job(job_obj=job_obj)

    def index_server_setup(self):
        """Setups the roles needed for index server"""
        self.index_server_helper.update_roles(index_server_roles=self.index_server_roles)
        self.index_server_obj = self.index_server_helper.index_server_obj

    def run_backup(self):
        """run solr backup"""
        self.log.info("Make sure default subclient has all roles in backup content")
        self.index_server_helper.init_subclient()
        self.index_server_helper.subclient_obj.configure_backup(storage_policy=self.tcinputs['StoragePolicy'],
                                                                role_content=self.index_server_roles)
        self.backup_job_id = self.index_server_helper.run_full_backup()
        self.log.info("Backup job completed")

    def validate_crawl(self):
        """Validates the crawl status of the data source"""
        self.log.info("Going to monitor the data source crawl job : %s", self.crawl_job_id)
        job_obj = self.commcell.job_controller.get(self.crawl_job_id)
        if not job_obj.wait_for_completion(timeout=60):
            raise Exception("Crawl job went to pending or Failed")
        self.log.info("Crawl job finished successfully")
        self.log.info("Going to find total files & folders in source location & DataSource")
        additional_folders = self.tcinputs['IncludedirectoriesPath'].split("\\")
        additional_folders_count = len(additional_folders)
        self.log.info("Additional folders which needs to be added : %s", additional_folders_count)
        expected_count = self.crawl_helper.get_docs_count(folder_path=self.tcinputs['IncludedirectoriesPath'],
                                                          machine_name=self.tcinputs['AccessNode'])
        expected_count = expected_count + additional_folders_count
        self.log.info("Source path count : %s", expected_count)
        resp = self.index_server_obj.execute_solr_query(core_name=self.datasource_obj.computed_core_name)
        self.total_crawlcount = int(resp['response']['numFound'])
        self.log.info("Total crawl count from data source : %s", self.total_crawlcount)
        if self.total_crawlcount != expected_count:
            msg = f"File count mismatched. Expected <{expected_count}> Actual <{self.total_crawlcount}>"
            raise Exception(msg)
        self.log.info("Consider backup as success as Total file & folder count matched - %s", expected_count)

    def create_data_source_start_crawl(self):
        """ Creates file system datasource and starts the crawl job"""
        self.log.info("Going to create file system data source : %s", self.fs_data_source_name)
        access_node_client_obj = self.commcell.clients.get(
            self.tcinputs['AccessNode'])
        self.log.info("Client object Initialised")
        access_node_clientid = access_node_client_obj.client_id
        self.log.info("Accessnode Client id : %s", str(access_node_clientid))
        ca_config = self.ds_helper.form_entity_extraction_config(entities=self.entities_to_extract,
                                                                 entity_fields=["content"])
        self.log.info("Going to get CA cloud details for : %s", self.tcinputs['CANode'])
        ca_cloud_obj = self.commcell.content_analyzers.get(self.tcinputs['CANode'])
        self.log.info("CA cloud URL : %s", ca_cloud_obj.cloud_url)
        fs_dynamic_property = {
            "includedirectoriespath": self.tcinputs['IncludedirectoriesPath'],
            "accessnodeclientid": access_node_clientid,
            "iscaenabled": "true",
            "caconfig": ca_config,
            ENTITY_EXTRACTION_CLOUDID: str(ca_cloud_obj.client_id)
        }

        file_properties = self.ds_helper.form_file_data_source_properties(fs_dynamic_property)

        self.datasource_obj = self.ds_helper.create_file_data_source(data_source_name=self.fs_data_source_name,
                                                                     index_server_name=self.tcinputs[
                                                                         'IndexServerName'],
                                                                     fs_properties=file_properties)
        self.log.info("Going to start crawl job on this data source")
        self.crawl_job_id = self.datasource_obj.start_job()
        self.log.info("Job id of crawl job : %s", self.crawl_job_id)
        self.log.info("Going to wait till job reaches content push phase")
        job_obj = self.commcell.job_controller.get(self.crawl_job_id)
        self.job_helper = JobManager(job_obj, self.commcell)
        self.job_helper.wait_for_phase(phase="Content Push", total_attempts=120, check_frequency=30)
        self.log.info("Content Push phase started.")
        doc_found = False
        threshold = 30  # in Mins
        core_name = self.datasource_obj.computed_core_name
        time_limit = time.time() + threshold * 60
        while(not doc_found and time.time() <= time_limit):
            self.log.info("Querying solr core to get document count : %s", core_name)
            resp = self.index_server_obj.execute_solr_query(core_name=core_name)
            if 'response' in resp:
                doc_count = int(f"{resp['response']['numFound']}")
                self.log.info("Current Document count : %s", doc_count)
                if doc_count > 0:
                    self.log.info("Document found in solr core. Assume job has started pushing data")
                    doc_found = True
                    self.doc_count_before_backup = doc_count
                else:
                    self.log.info("Sleeping for 5 Seconds before retrying again")
                    time.sleep(5)
        if not doc_found:
            raise Exception("Document not pushed into solr core yet during live crawl")

    def setup(self):
        """Setup function of this test case"""
        self.crawl_helper = CrawlJobHelper(self)
        self.ds_helper = DataSourceHelper(self.commcell)
        self.timestamp = calendar.timegm(time.gmtime())
        self.fs_data_source_name = f"{self.fs_data_source_name}{self.timestamp}"
        self.index_server_helper = IndexServerHelper(self.commcell, self.tcinputs['IndexServerName'])
        self.index_server_setup()
        self.create_data_source_start_crawl()

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Going to start solr backup job")
            self.run_backup()
            self.validate_crawl()
            self.do_restore()
            self.validate_data()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("Going to delete FS data source : %s", self.fs_data_source_name)
            self.commcell.datacube.datasources.delete(self.fs_data_source_name)
            self.log.info("Deleted the FS data source : %s", self.fs_data_source_name)
            self.log.info("Going to delete the full backup job : %s", self.backup_job_id)
            storage_copy_obj = self.commcell.storage_policies.get(self.tcinputs['StoragePolicy']) \
                .get_copy(self.tcinputs['StoragePolicyCopy'])
            storage_copy_obj.delete_job(self.backup_job_id)
            self.log.info("Deleted the Full backup job")
