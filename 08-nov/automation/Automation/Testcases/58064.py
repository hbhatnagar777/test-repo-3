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

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.index_server_helper import IndexServerHelper
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
        self.name = "Validation of DA role on CvSolr Index server"
        self.index_server_name = None
        self.data_source_name = OptionsSelector.get_custom_str('data_source')
        self.crawl_job_helper = None
        self.data_source_helper = None
        self.tcinputs = {
            "IndexServerNodeNames": None,
            "IndexLocations": None,
            "UserName": None,
            "Password": None,
            "IncludedirectoriesPath": None,
            "AccessNodeClientName": None
        }

    def setup(self):
        """Setup function of this test case"""
        try:
            self.index_server_name = "IndexServer_%s" % self.id
            self.crawl_job_helper = CrawlJobHelper(self)
            self.data_source_helper = DataSourceHelper(self.commcell)
            if self.commcell.index_servers.has(
                    self.index_server_name):
                self.log.info("Index server already exist.")
                self.log.info("Deleting and creating index server.")
                self.commcell.index_servers.delete(
                    self.index_server_name)
                self.log.info("Index server deleted successfully.")
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
            self.crawl_job_helper.monitor_crawl_job(self.data_source_name)
            self.crawl_job_helper.validate_crawl_files_count(
                self.data_source_name, self.tcinputs['IncludedirectoriesPath'],
                self.tcinputs['AccessNodeClientName'], self.index_server_name
            )
            index_server_obj = self.commcell.index_servers.get(self.index_server_name)
            index_node_obj = index_server_obj.get_index_node(
                self.tcinputs['IndexServerNodeNames'][0])
            update_port_no = int(index_node_obj.solr_port) + 1
            self.log.info(
                "Modifying %s solr port to %s" % (index_node_obj.node_name, update_port_no))
            index_node_obj.solr_port = update_port_no
            self.log.info("Modified index server successfully")
            self.crawl_job_helper.monitor_crawl_job(self.data_source_name)
            self.crawl_job_helper.validate_crawl_files_count(
                self.data_source_name, self.tcinputs['IncludedirectoriesPath'],
                self.tcinputs['AccessNodeClientName'], self.index_server_name
            )

        except Exception as err:
            self.log.error('Run for the test case failed.')
            self.log.exception(err)
            self.result_string = str(err)
            self.status = constants.FAILED
            raise Exception("Test case run failed.")

    def tear_down(self):
        if self.status != constants.FAILED:
            self.log.info("Deleting the data source now")
            self.commcell.datacube.datasources.delete(self.data_source_name)
            self.log.info("Data source deleted successfully.")
            index_server_helper = IndexServerHelper(self.commcell, self.index_server_name)
            index_server_helper.delete_index_server()
