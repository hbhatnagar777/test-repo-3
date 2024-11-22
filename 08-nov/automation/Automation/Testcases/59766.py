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

from cvpysdk.datacube.constants import IndexServerConstants
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.utils.constants import FILE_SYSTEM_DSTYPE, FILE_DS_PREFIX
from dynamicindex.utils.activateutils import ActivateUtils
from dynamicindex.index_server_helper import IndexServerHelper
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.Datacube.data_source_helper import DataSourceHelper


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
        self.name = "Negative : Folder Stats should not get pushed to Solr for Content Crawl"
        self.tcinputs = {
            "IndexServerNodeName": None,
            "UserName": None,
            "Password": None,
            "IncludedirectoriesPath": None,
            "AccessNodeClientName": None,
            "FilesCount": None
        }
        self.index_server_name = None
        self.index_node_name = None
        self.access_node_name = None
        self.crawl_dir = None
        self.index_server_helper = None
        self.crawl_job_helper = None
        self.activate_utils = None
        self.data_source_helper = None
        self.index_location = None
        self.index_server_roles = [IndexServerConstants.ROLE_DATA_ANALYTICS]
        self.data_source_type = FILE_SYSTEM_DSTYPE
        self.file_ds_prefix = FILE_DS_PREFIX
        self.data_source_name = OptionsSelector.get_custom_str('data_source').replace('-', '_')

    def setup(self):
        """Setup function of this test case"""
        self.index_node_name = self.tcinputs['IndexServerNodeName']
        self.access_node_name = self.tcinputs['AccessNodeClientName']
        self.crawl_dir = self.tcinputs['IncludedirectoriesPath']
        self.activate_utils = ActivateUtils()
        self.crawl_job_helper = CrawlJobHelper(self)
        self.data_source_helper = DataSourceHelper(self.commcell)
        self.index_server_name = f"IndexServer{self.id}"
        self.index_location = IndexServerHelper.get_new_index_directory(self.commcell, self.index_node_name, self.id)
        self.activate_utils.sensitive_data_generation(self.crawl_dir, self.tcinputs['FilesCount'])

    def run(self):
        """Run function of this test case"""
        try:
            IndexServerHelper.create_index_server(self.commcell, self.index_server_name,
                                                  [self.index_node_name], [self.index_location],
                                                  self.index_server_roles)
            IndexServerHelper.set_compute_folder_stats_key(self.commcell, self.index_node_name)
            self.index_server_helper = IndexServerHelper(self.commcell, self.index_server_name)
            data_source_properties = {
                "includedirectoriespath": self.tcinputs['IncludedirectoriesPath'],
                "username": self.tcinputs['UserName'],
                "password": self.tcinputs['Password'], "pushonlymetadata": "false",
                "accessnodeclientid": self.commcell.clients.get(
                    self.tcinputs['AccessNodeClientName']).client_id
            }
            data_source_properties = self.data_source_helper. \
                form_file_data_source_properties(data_source_properties)
            self.data_source_helper.create_file_data_source(
                self.data_source_name, self.index_server_name,
                data_source_properties)
            self.crawl_job_helper.monitor_crawl_job(self.data_source_name, job_time_limit=180)
            validation = self.crawl_job_helper.validate_folder_stats(self.commcell, constants.ACTIVATE_UTIL_DB_PATH,
                                                                     self.data_source_name, self.index_server_name)
            if validation:
                raise Exception("Folder stats were pushed to Solr for Content Crawl")
            self.log.info("Folder stats were not pushed to Solr as expected")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.commcell.datacube.datasources.delete(self.data_source_name)
            self.index_server_helper.delete_index_server()
