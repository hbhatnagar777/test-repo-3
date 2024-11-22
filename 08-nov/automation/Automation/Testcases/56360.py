# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.Datacube.dcube_solr_helper import SolrHelper
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
        self.name = "Standalone Index server - Validation of data " \
                    "analytics role by creating FS datasource"
        self.index_server_name = None
        self.data_source_name = OptionsSelector.get_custom_str('data_source')
        self.index_server_roles = ['Data Analytics']
        self.data_source_obj = None
        self.index_server_obj = None
        self.index_location = None
        self.data_source_type = dynamic_constants.FILE_SYSTEM_DSTYPE
        self.file_ds_prefix = dynamic_constants.FILE_DS_PREFIX
        self.crawl_job_helper = None
        self.tcinputs = {
            "IndexServerNodeName": None,
            "UserName": None,
            "Password": None,
            "IncludedirectoriesPath": None,
            "AccessNodeClientName": None
        }

    def setup(self):
        """Setup function of this test case"""
        try:
            self.index_location = IndexServerHelper.get_new_index_directory(self.commcell,
                                                                            self.tcinputs['IndexServerNodeName'],
                                                                            self.id)
            self.index_server_name = "IndexServer_%s" % self.id
            self.crawl_job_helper = CrawlJobHelper(self)
            if self.commcell.index_servers.has(
                    self.index_server_name):
                self.log.info("Index server already exist.")
                self.log.info("Deleting and creating index server.")
                self.commcell.index_servers.delete(
                    self.index_server_name)
                self.log.info("Index server deleted successfully.")
            self.log.info("Creating Index Server : %s", self.index_server_name)
            self.commcell.index_servers.create(
                self.index_server_name,
                [self.tcinputs['IndexServerNodeName']],
                self.index_location,
                self.index_server_roles
            )
            self.index_server_obj = self.commcell.index_servers.get(
                self.index_server_name
            )
            self.log.info("Using Index Server with "
                          "cloud id %s", self.index_server_obj.cloud_id)

        except Exception as err:
            self.log.error('Setup for the test case failed.')
            self.log.exception(err)
            self.result_string = str(err)
            self.status = constants.FAILED
            raise Exception(
                "Test case setup(Creation of Index server) failed.")

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Creating a file system data source : %s",
                          self.data_source_name)
            property_name = [
                'includedirectoriespath',
                'doincrementalscan',
                'username',
                'password',
                'pushonlymetadata',
                'accessnodeclientid',
                'createclient',
                'candelete',
                'appname',
                'excludefilters',
                'minumumdocumentsize',
                'maximumdocumentsize']
            property_value = [
                self.tcinputs['IncludedirectoriesPath'],
                "false",
                self.tcinputs['UserName'],
                self.tcinputs['Password'],
                "false",
                self.commcell.clients.get(
                    self.tcinputs['AccessNodeClientName']).client_id,
                "archiverClient",
                "true",
                "DATACUBE",
                "",
                "0",
                "52428800"]
            data_source_properties = [
                {
                    "propertyName": property_name[i],
                    "propertyValue": property_value[i]
                } for i in range(len(property_name))
            ]
            self.commcell.datacube.datasources.add(
                self.data_source_name,
                self.tcinputs['IndexServerNodeName'],
                self.data_source_type,
                data_source_properties
            )
            self.data_source_obj = self.commcell.datacube.datasources.get(
                self.data_source_name
            )
            self.log.info("Created file system data source successfully : %s",
                          self.data_source_obj.datasource_id)
            dcube_core_stats = self.crawl_job_helper.get_data_source_stats(
                data_source_name=self.data_source_name,
                client_name=self.tcinputs['IndexServerNodeName']
            )
            data_source_data_dir = dcube_core_stats.get('dataDir', '')
            if not data_source_data_dir.startswith(
                    self.index_location):
                self.log.error("Invalid data directory path.")
                raise Exception(
                    "Index server is not pointed to expected index dir location.")
            crawl_dir_paths = self.tcinputs['IncludedirectoriesPath'].split(
                ',')
            total_files_count = 0
            for i in crawl_dir_paths:
                total_files_count += self.crawl_job_helper.get_docs_count(
                    folder_path=i,
                    machine_name=self.tcinputs['AccessNodeClientName'],
                    include_folders=True
                )
            self.log.info(
                "Number of files present in crawl directories : %s",
                total_files_count)
            self.crawl_job_helper.monitor_crawl_job(
                self.data_source_obj.datasource_name
            )
            crawled_files_count = self.crawl_job_helper.get_crawl_docs_count(
                data_source_name=self.data_source_name,
                client_name=self.tcinputs['IndexServerNodeName']
            )
            self.log.info(
                "Number of documents crawled : %s",
                crawled_files_count)
            if int(crawled_files_count) != int(total_files_count):
                self.log.error(
                    "Number of crawled documents are invalid\nExpected: %s\tActual: %s",
                    total_files_count,
                    crawled_files_count)
                raise Exception("Number of documents crawled were incorrect")
            self.log.info("All the documents were crawled successfully")
            self.log.info(
                "Modifying index server base port to %s and testing again", int(
                    self.index_server_obj.base_port[0]) + 1)
            cloud_params = [
                {
                    "name": "PORTNO",
                    "value": str(int(self.index_server_obj.base_port[0]) + 1)
                }
            ]
            self.index_server_obj.modify(self.index_location,
                                         self.tcinputs['IndexServerNodeName'],
                                         cloud_params)
            self.log.info("Modified index server successfully")
            self.index_server_obj = self.commcell.index_servers.\
                get(self.index_server_name)
            self.data_source_obj = self.commcell.datacube.datasources.\
                get(self.data_source_name)
            self.crawl_job_helper.monitor_crawl_job(
                self.data_source_obj.datasource_name
            )
            crawled_files_count = self.crawl_job_helper.get_crawl_docs_count(
                data_source_name=self.data_source_name,
                client_name=self.tcinputs['IndexServerNodeName']
            )
            self.log.info(
                "Number of documents crawled : %s",
                crawled_files_count)
            if int(crawled_files_count) != int(total_files_count):
                self.log.error(
                    "Number of crawled documents are invalid\nExpected: %s\tActual: %s",
                    total_files_count,
                    crawled_files_count)
                raise Exception("Number of documents crawled were incorrect")
            self.log.info("All the documents were crawled successfully")
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.data_source_obj:
            self.log.info("Deleting the data source now")
            self.commcell.datacube.datasources.delete(
                self.data_source_obj.datasource_name)
            self.log.info("Data source deleted successfully.")
        if self.index_server_obj:
            self.log.info("Deleting the index server now")
            self.commcell.index_servers.delete(
                self.index_server_obj.engine_name
            )
            self.log.info("Index server deleted successfully.")
