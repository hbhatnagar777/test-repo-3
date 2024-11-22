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
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.Datacube.dcube_solr_helper import SolrHelper
from dynamicindex.utils.constants import FILE_SYSTEM_DSTYPE


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
        self.name = "Standalone index server: Solr jvm memory validation"
        self.tcinputs = {
            "IndexServerNodeName": None,
            "IncludedirectoriesPath": None,
            "UserName": None,
            "Password": None,
            "AccessNodeClientName": None
        }
        self.index_location = None
        self.crawl_job_helper = None
        self.index_node_machine_obj = None
        self.index_server_obj = None
        self.index_server_name = None
        self.update_solr_jvm_memory = 100
        self.index_server_role = ["Data Analytics"]
        self.option_selector_obj = None
        self.solr_helper = None
        self.initial_memory = None
        self.updated_memory = None
        self.solr_base_url = None
        self.data_source_name = None
        self.data_source_obj = None
        self.initial_registry_memory = None
        self.updated_registry_memory = None
        self.jvm_memory_reg_key_path = "HKLM:\\SOFTWARE\\Wow6432Node\\Apache Software Foundation\\Procrun 2.0\\" \
                                       "CVAnalytics(Instance001)\\Parameters\\Java"
        self.jvm_memory_reg_value = "JvmMx"

    def setup(self):
        """Setup function of this test case"""
        self.index_node_machine_obj = Machine(self.tcinputs['IndexServerNodeName'], self.commcell)
        self.option_selector_obj = OptionsSelector(self.commcell)
        self.crawl_job_helper = CrawlJobHelper(self)
        self.solr_helper = SolrHelper(self)
        self.index_server_name = "IndexServer%s" % self.id
        self.data_source_name = self.option_selector_obj.get_custom_str("data_source").replace("-", "_")
        drive_letter = self.option_selector_obj.get_drive(self.index_node_machine_obj)
        self.index_location = "%sIndexDirectory%s" % (drive_letter, self.id)
        if self.commcell.index_servers.has(self.index_server_name):
            self.log.info("Deleting index server : %s", self.index_server_name)
            self.commcell.index_servers.delete(self.index_server_name)
        self.log.info("Creating index server : %s", self.index_server_name)
        self.commcell.index_servers.create(self.index_server_name, [self.tcinputs['IndexServerNodeName']],
                                           self.index_location, self.index_server_role)
        self.index_server_obj = self.commcell.index_servers.get(self.index_server_name)

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Getting solr base url for node: %s" % self.tcinputs['IndexServerNodeName'])
            self.solr_base_url = self.solr_helper.get_solr_baseurl(self.tcinputs['IndexServerNodeName'], 1)
            self.log.info("Solr base url : %s" % self.solr_base_url)
            self.initial_registry_memory = int(self.index_node_machine_obj.get_registry_value(
                win_key=self.jvm_memory_reg_key_path, value=self.jvm_memory_reg_value))
            self.log.info("Registry entry for JVM max memory: %s", self.initial_registry_memory)
            self.initial_memory = self.solr_helper.get_solr_jvm_memory(self.solr_base_url)
            self.log.info("Initial jvm max memory is : %s" % self.initial_memory)
            self.update_solr_jvm_memory = self.update_solr_jvm_memory + self.initial_registry_memory
            self.log.info("Modifying jvm max memory to %s" % self.update_solr_jvm_memory)
            self.index_server_obj.modify(self.index_location, self.tcinputs['IndexServerNodeName'],
                                         [
                                             {
                                                 "name": "JVMMAXMEMORY",
                                                 "value": str(self.update_solr_jvm_memory)
                                             },
                                             {
                                                 "name": "PORTNO",
                                                 "value": str(self.index_server_obj.base_port[0])
                                             }
                                         ])
            self.log.info("Index server modified : %s" % self.index_server_name)
            self.log.info("Cross verifying solr jvm memory")
            self.updated_memory = self.solr_helper.get_solr_jvm_memory(self.solr_base_url)
            self.log.info("Updated jvm memory: %s" % self.updated_memory)
            self.updated_registry_memory = int(self.index_node_machine_obj.get_registry_value(
                win_key=self.jvm_memory_reg_key_path, value=self.jvm_memory_reg_value))
            self.log.info("Registry entry for JVM max memory: %s" % self.updated_registry_memory)
            if not (self.updated_registry_memory == self.update_solr_jvm_memory
                    and self.updated_memory != self.initial_memory):
                self.log.error("Failed to update JVM memory")
                raise Exception("Failed to update JVM memory")
            self.log.info("JVM memory updated")
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
                FILE_SYSTEM_DSTYPE,
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

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("Deleting the data source now")
        self.commcell.datacube.datasources.delete(self.data_source_name)
        self.log.info("Data source deleted successfully.")
        self.log.info("Deleting index server: %s" % self.index_server_name)
        self.commcell.index_servers.delete(self.index_server_name)
        self.log.info("Index server deleted")
        self.log.info("Deleting the index directory: %s" % self.index_location)
        self.index_node_machine_obj.remove_directory(self.index_location, 0)
        self.log.info("Index directory deleted")
