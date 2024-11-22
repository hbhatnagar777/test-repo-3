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
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.Datacube.dcube_solr_helper import SolrHelper
from dynamicindex.index_server_helper import IndexServerHelper
from dynamicindex.utils.constants import SOLR_JVM_MEMORY_REG_KEY, SOLR_JVM_MEMORY_REG_KEY_PATH
from cvpysdk.datacube.constants import IndexServerConstants


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
        self.name = "CvSolr index server: Solr jvm memory validation"
        self.tcinputs = {
            "IndexServerNodeNames": None,
            "IncludedirectoriesPath": None,
            "UserName": None,
            "Password": None,
            "AccessNodeClientName": None,
            "IndexLocations": None
        }
        self.index_location = None
        self.crawl_job_helper = None
        self.data_source_helper = None
        self.index_node_machine_obj = None
        self.index_server_name = None
        self.update_solr_jvm_memory = 100
        self.option_selector_obj = None
        self.solr_helper = None
        self.initial_memory = None
        self.updated_memory = None
        self.solr_base_url = None
        self.data_source_name = None
        self.initial_registry_memory = None
        self.updated_registry_memory = None

    def setup(self):
        """Setup function of this test case"""
        try:
            self.index_server_name = "IndexServer%s" % self.id
            self.crawl_job_helper = CrawlJobHelper(self)
            self.data_source_helper = DataSourceHelper(self.commcell)
            self.solr_helper = SolrHelper(self)
            if isinstance(self.tcinputs['IndexServerNodeNames'], str):
                self.tcinputs['IndexServerNodeNames'] = self.tcinputs['IndexServerNodeNames'].split(",")
            if isinstance(self.tcinputs['IndexLocations'], str):
                self.tcinputs['IndexLocations'] = self.tcinputs['IndexLocations'].split(",")
            self.index_node_machine_obj = Machine(self.tcinputs['IndexServerNodeNames'][0],
                                                  self.commcell)
            self.option_selector_obj = OptionsSelector(self.commcell)
            self.data_source_name = self.option_selector_obj.get_custom_str("data_source").replace("-", "_")
            if self.commcell.index_servers.has(self.index_server_name):
                self.log.info("Deleting index server : %s", self.index_server_name)
                self.commcell.index_servers.delete(self.index_server_name)
            self.log.info("Creating CvSolr Index Server : %s", self.index_server_name)
            self.commcell.index_servers.create(
                self.index_server_name,
                self.tcinputs['IndexServerNodeNames'],
                self.tcinputs['IndexLocations'],
                [IndexServerConstants.ROLE_DATA_ANALYTICS]
            )
            self.log.info("CvSolr Index Server created")

        except Exception as err:
            self.log.error('Setup for the test case failed.')
            self.log.exception(err)
            self.result_string = str(err)
            self.status = constants.FAILED
            raise Exception("Test case setup failed.")

    def run(self):
        """Run function of this test case"""
        try:
            data_source_properties = {
                "includedirectoriespath": self.tcinputs['IncludedirectoriesPath'],
                "username": self.tcinputs['UserName'],
                "password": self.tcinputs['Password'],
                "accessnodeclientid": self.commcell.clients.get(
                    self.tcinputs['AccessNodeClientName']).client_id
            }
            data_source_properties = self.data_source_helper. \
                form_file_data_source_properties(data_source_properties)
            self.data_source_helper.create_file_data_source(
                self.data_source_name, self.index_server_name,
                data_source_properties)
            self.log.info("Getting solr base url for node: %s" % self.tcinputs['IndexServerNodeNames'][0])
            self.solr_base_url = self.solr_helper.get_solr_baseurl(self.tcinputs['IndexServerNodeNames'][0], 1)
            self.log.info("Solr base url : %s" % self.solr_base_url)
            self.initial_registry_memory = int(self.index_node_machine_obj.get_registry_value(
                win_key=SOLR_JVM_MEMORY_REG_KEY_PATH, value=SOLR_JVM_MEMORY_REG_KEY))
            self.log.info("Registry entry for JVM max memory: %s", self.initial_registry_memory)
            self.initial_memory = self.solr_helper.get_solr_jvm_memory(self.solr_base_url)
            self.log.info("Initial jvm max memory is : %s" % self.initial_memory)
            self.update_solr_jvm_memory = self.update_solr_jvm_memory + self.initial_registry_memory
            self.log.info("Modifying jvm max memory to %s" % self.update_solr_jvm_memory)
            index_server_obj = self.commcell.index_servers.get(self.index_server_name)
            index_node_obj = index_server_obj.get_index_node(
                self.tcinputs['IndexServerNodeNames'][0])
            index_node_obj.jvm_memory = self.update_solr_jvm_memory
            self.log.info("Modified index server successfully")
            self.log.info("Cross verifying solr jvm memory")
            self.updated_memory = self.solr_helper.get_solr_jvm_memory(self.solr_base_url)
            self.log.info("Updated jvm memory: %s" % self.updated_memory)
            self.updated_registry_memory = int(self.index_node_machine_obj.get_registry_value(
                win_key=SOLR_JVM_MEMORY_REG_KEY_PATH, value=SOLR_JVM_MEMORY_REG_KEY))
            self.log.info("Registry entry for JVM max memory: %s" % self.updated_registry_memory)
            if not (self.updated_registry_memory == self.update_solr_jvm_memory
                    and self.updated_memory != self.initial_memory):
                self.log.error("Failed to update JVM memory")
                raise Exception("Failed to update JVM memory")
            self.log.info("JVM memory updated")
            self.crawl_job_helper.monitor_crawl_job(self.data_source_name)
            self.crawl_job_helper.validate_crawl_files_count(
                self.data_source_name, self.tcinputs['IncludedirectoriesPath'],
                self.tcinputs['AccessNodeClientName'], self.index_server_name
            )

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("Deleting the data source now")
        self.commcell.datacube.datasources.delete(self.data_source_name)
        self.log.info("Data source deleted successfully.")
        index_server_helper = IndexServerHelper(self.commcell, self.index_server_name)
        index_server_helper.delete_index_server()
