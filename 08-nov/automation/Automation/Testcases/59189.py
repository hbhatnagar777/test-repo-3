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
    __init__()                                          --  initialize TestCase class

    setup()                                             --  setup function of this test case

    run()                                               --  run function of this test case

    tear_down()                                         --  tear down function of this test case

    install_content_analyzer_create_fs_data_source()    --  Installs CA package on new client and creates FS datasource

    validate_entity_extraction()                        --  validates entity extraction happened or not in
                                                                                    given data source

    validate_tppm_run_fs_crawl()                        --  Validates tppm and then runs crawl job for FS dataSource

    create_open_data_source()                           --  Creates open data sources with Entity extraction enabled

    import_data_open_data_source()                      --  Imports data into open data source

"""


import calendar
import time
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.content_analyzer_helper import ContentAnalyzerHelper
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.vm_manager import VmManager


_CONFIG_DATA = get_config().DynamicIndex.LinuxHyperV


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
        self.name = "Verify TPPM working for Linux content extractor service via data cube data sources " \
                    "with CvSolr as Index Server"
        self.tcinputs = {
            "EntitiestoExtractRER": None,
            "IndexServer": None,
            "IncludedirectoriesPath": None,
            "UserName": None,
            "Password": None,
            "Accessnodeclient": None,
            "EntityTestData": None
        }
        self.vm_name = None
        self.ca_cloud_name = None
        self.ca_helper_obj = None
        self.datasource_name = None
        self.open_datasource_name = None
        self.data_source_obj = None
        self.open_data_source_obj = None
        self.crawl_job_obj = None
        self.timestamp = None
        self.handler_name = None
        self.vm_helper = None
        self.ds_helper = None
        self.ca_cloud_obj = None
        self.open_column = ['id', 'comment']
        self.open_column_type = ['int', 'string']
        self.test_data_comment = None
        self.query_param = None

    def install_content_analyzer_create_fs_data_source(self):
        """Installs CA package on new client and creates FS datasource"""
        self.log.info("*************** Install content Analyzer client starts ****************")
        self.ca_helper_obj.install_content_analyzer(
            machine_name=self.vm_name,
            user_name=_CONFIG_DATA.VmUsername,
            password=_CONFIG_DATA.VmPassword,
            platform="Unix")
        self.log.info(f"Check whether python process is up and running on CA machine : {self.vm_name}")
        self.log.info("Refreshing client list as we installed new client with CA package")
        self.commcell.clients.refresh()
        client_obj = self.commcell.clients.get(self.vm_name)
        self.ca_helper_obj.check_all_python_process(client_obj=client_obj)
        self.log.info("*************** Install content Analyzer client ends *****************")
        self.log.info(f"Going to get CA cloud details for : {self.ca_cloud_name}")
        self.ca_cloud_obj = self.commcell.content_analyzers.get(self.ca_cloud_name)
        self.log.info(f"CA cloud URL : {self.ca_cloud_obj.cloud_url}")
        self.log.info("*************** Data source creation starts *****************")
        self.log.info(f"Going to create file system datasource : {self.datasource_name}")
        access_node_client_obj = self.commcell.clients.get(
            self.tcinputs['Accessnodeclient'])
        self.log.info("Access node client object Initialised")
        access_node_clientid = access_node_client_obj.client_id
        self.log.info(f"Access node Client id : {str(access_node_clientid)}")
        entities_to_extract = {
            "RER": self.tcinputs['EntitiestoExtractRER']
        }
        ca_config = self.ds_helper.form_entity_extraction_config(entities=entities_to_extract,
                                                                 entity_fields=dynamic_constants.FILE_DS_EE_COLUMN)
        fs_dynamic_property = {
            "includedirectoriespath": self.tcinputs['IncludedirectoriesPath'],
            "username": self.tcinputs['UserName'],
            "password": self.tcinputs['Password'],
            "accessnodeclientid": access_node_clientid,
            "iscaenabled": "true",
            "pushonlymetadata": "false",
            "caconfig": ca_config,
            "caclientid": str(self.ca_cloud_obj.client_id)
        }

        file_properties = self.ds_helper.form_file_data_source_properties(fs_dynamic_property)

        self.data_source_obj = self.ds_helper.create_file_data_source(data_source_name=self.datasource_name,
                                                                      index_server_name=self.tcinputs[
                                                                          'IndexServer'],
                                                                      fs_properties=file_properties)

    def validate_entity_extraction(self, data_source_obj):
        """validates entity extraction happened or not in given data source

                Args:

                    data_source_obj     (obj)   --  DataSource class object

                Returns:

                    None

                Raises:

                    Exception:

                            if failed to verify entity extracted
        """

        self.log.info("********** Entity extraction verification starts **********")
        self.log.info("Cross verify whether entity got extracted for data set and pushed to solr")
        self.log.info(f"Going to create Handler : {self.handler_name}")
        data_source_obj.ds_handlers.add(
            self.handler_name,
            search_query=[self.query_param])
        self.log.info("Handler created. Going to cross verify it by executing")
        handler_obj = data_source_obj.ds_handlers.get(self.handler_name)
        response_out = handler_obj.get_handler_data(handler_filter=dynamic_constants.SOLR_FETCH_ONE_ROW)
        self.log.info(f"Handler Data  : {response_out}")
        total_docs = response_out['numFound']
        if total_docs == 0:
            self.log.info("Entity extraction didn't happen on CA machine. Please check")
            raise Exception("No document found with entity extracted")
        self.log.info(f"Documents found with entity extracted data : {total_docs}")
        self.log.info("********** Entity extraction verification ends ************")

    def validate_tppm_run_fs_crawl(self):
        """Validates tppm and then runs crawl job for FS dataSource"""
        self.ca_helper_obj.validate_tppm_setup(content_analyzer=self.ca_cloud_name)
        self.crawl_job_obj.monitor_crawl_job(self.datasource_name)
        self.validate_entity_extraction(data_source_obj=self.data_source_obj)

    def create_open_data_source(self):
        """Creates open data sources with Entity extraction enabled"""
        self.log.info(f"Going to create Open datasource : {self.open_datasource_name}")
        entities_to_extract = {
            "RER": self.tcinputs['EntitiestoExtractRER']
        }
        ca_config = self.ds_helper.form_entity_extraction_config(entities=entities_to_extract,
                                                                 entity_fields=self.open_column)
        self.log.info(f"CA config Json formed : {ca_config}")
        datasource_prop_name = dynamic_constants.ENTITY_EXTRACTION_PROPERTY
        datasource_prop_value = ["true", ca_config, str(self.ca_cloud_obj.client_id)]
        datasource_properties = self.ds_helper.form_data_source_properties(datasource_prop_name,
                                                                           datasource_prop_value)
        self.open_data_source_obj = self.ds_helper.create_open_data_source(self.open_datasource_name,
                                                                           self.tcinputs['IndexServer'],
                                                                           datasource_properties)
        self.ca_helper_obj.validate_tppm_setup(content_analyzer=self.ca_cloud_name)
        self.ds_helper.update_data_source_schema(data_source_name=self.open_datasource_name,
                                                 field_name=self.open_column,
                                                 field_type=self.open_column_type,
                                                 schema_field=dynamic_constants.SCHEMA_FIELDS)

    def import_data_open_data_source(self):
        """Imports data into open data source"""
        total_rows = len(self.test_data_comment)
        total_crawlcount = 0
        input_data = []
        self.log.info(f"Total Entity Test Data rows : {total_rows}")
        self.log.info("Calling import data on this datasource")
        for data_row in range(total_rows):
            data_list = {
                self.open_column[0]: str(data_row),
                self.open_column[1]: self.test_data_comment[data_row]
            }
            total_crawlcount = total_crawlcount + 1
            input_data.append((data_list))
        self.log.info(f"Import Data formed : {input_data}")
        self.open_data_source_obj.import_data(input_data)
        self.log.info(f"Import Data done successfully. Total Docs : {total_crawlcount}")
        self.log.info("Sleep for 2mins to make sure EE happened")
        time.sleep(120)

    def setup(self):
        """Setup function of this test case"""
        try:
            self.vm_helper = VmManager(self)
            self.ds_helper = DataSourceHelper(self.commcell)
            self.ca_helper_obj = ContentAnalyzerHelper(self)
            self.crawl_job_obj = CrawlJobHelper(self)
            self.timestamp = calendar.timegm(time.gmtime())
            self.datasource_name = "FreshCAClient_59189_" + str(self.timestamp)
            self.open_datasource_name = "FreshCAClient_59189_Open_" + str(self.timestamp)
            self.vm_name = _CONFIG_DATA.VmName
            self.ca_cloud_name = self.vm_name
            self.handler_name = "FreshCA_H1_" + str(self.timestamp)
            self.test_data_comment = self.tcinputs['EntityTestData'].split(",")
            self.vm_helper.check_client_revert_snap(
                hyperv_name=_CONFIG_DATA.HyperVName,
                hyperv_user_name=_CONFIG_DATA.HyperVUsername,
                hyperv_user_password=_CONFIG_DATA.HyperVPassword,
                snap_name="PlainOS",
                vm_name=self.vm_name)
            self.log.info("Revert snap is successful")
            index_server_obj = self.commcell.index_servers.get(self.tcinputs['IndexServer'])
            client_list = index_server_obj.client_name
            client_list.append(self.tcinputs['Accessnodeclient'])
            client_list.append(self.commcell.commserv_name)
            client_list.append(self.inputJSONnode['commcell']['webconsoleHostname'])
            self.vm_helper.populate_vm_ips_on_client(config_data=_CONFIG_DATA, clients=client_list)
            entities_to_extract_rer = self.tcinputs['EntitiestoExtractRER'].split(',')
            self.log.info(f"Going to get entity id details for : {entities_to_extract_rer}")
            entity_keys = self.commcell.activate.entity_manager().get_entity_keys(entities_to_extract_rer)
            self.log.info(f"Entity key's got : {entity_keys}")
            self.query_param = "("
            for entity_key in entity_keys:
                self.query_param = self.query_param + "entity_" + entity_key + ":* OR "
            self.query_param = self.query_param.rstrip(" OR ")
            self.query_param = self.query_param + ") AND CAState:1"
            self.log.info(f"Query param formed : {self.query_param}")
        except Exception as except_setup:
            self.log.exception(except_setup)
            self.result_string = str(except_setup)
            self.status = constants.FAILED
            raise Exception("Test case setup(Reverting snap to Plain OS failed). Please check")

    def run(self):
        """Run function of this test case"""
        try:
            # Install new CA client and create datasources
            self.install_content_analyzer_create_fs_data_source()
            # Validate File system datasources and tppm entry for CA client
            self.validate_tppm_run_fs_crawl()
            # Create open data source
            self.create_open_data_source()
            # Delete the File System dataSource
            self.commcell.datacube.datasources.delete(self.datasource_name)
            self.log.info(f"FS Data source deleted successfully : {self.datasource_name}")

            # Import data into open data source
            self.import_data_open_data_source()
            # Validate enity extraction happened on open datasource
            self.validate_entity_extraction(data_source_obj=self.open_data_source_obj)
            # Delete the open data source
            self.commcell.datacube.datasources.delete(self.open_datasource_name)
            self.log.info(f"Open Data source deleted successfully : {self.open_datasource_name}")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.log.exception(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            # Get client id before deleting client so that we can validate it in tppm table
            client_id = int(self.commcell.clients.get(self.vm_name).client_id)
            self.log.info("Going to delete CA client")
            self.commcell.clients.delete(self.vm_name)
            self.log.info(f"CA client deleted successfully : {self.vm_name}")
            self.log.info("Verify tppm entry got deleted after CA client deletion")
            self.ca_helper_obj.validate_tppm_setup(content_analyzer=client_id, exists=False)
            self.log.info(f"Going to Shutdown the vm : {self.vm_name}")
            self.vm_helper.vm_shutdown(hyperv_name=_CONFIG_DATA.HyperVName,
                                       hyperv_user_name=_CONFIG_DATA.HyperVUsername,
                                       hyperv_user_password=_CONFIG_DATA.HyperVPassword,
                                       vm_name=self.vm_name)
            self.log.info("Power off vm successfull")
