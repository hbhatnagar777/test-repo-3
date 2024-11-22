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


_CONFIG_DATA = get_config().DynamicIndex.WindowsHyperV


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
        self.name = "Verify Fresh installation of CA package on windows machine and validate FS datasource " \
                    "crawl with Entity extraction"
        self.tcinputs = {
            "EntitiestoExtractRER": None,
            "IndexServer": None,
            "IncludedirectoriesPath": None,
            "DoincrementalScan": None,
            "UserName": None,
            "Password": None,
            "PushonlyMetadata": None,
            "Accessnodeclient": None
        }
        self.vm_name = None
        self.ca_cloud_name = None
        self.ca_helper_obj = None
        self.datasource_name = None
        self.datasource_obj = None
        self.datasource_id = None
        self.crawl_job_obj = None
        self.timestamp = None
        self.handler_name = None
        self.handler_obj = None
        self.vm_helper = None
        self.ds_helper = None

    def setup(self):
        """Setup function of this test case"""
        try:
            self.vm_helper = VmManager(self)
            self.ds_helper = DataSourceHelper(self.commcell)
            self.ca_helper_obj = ContentAnalyzerHelper(self)
            self.crawl_job_obj = CrawlJobHelper(self)
            self.timestamp = calendar.timegm(time.gmtime())
            self.datasource_name = "FreshCAClient_51288_" + str(self.timestamp)
            self.vm_name = _CONFIG_DATA.VmName
            self.ca_cloud_name = self.vm_name
            self.handler_name = "FreshCA_H1_" + str(self.timestamp)
            self.vm_helper.check_client_revert_snap(
                hyperv_name=_CONFIG_DATA.HyperVName,
                hyperv_user_name=_CONFIG_DATA.HyperVUsername,
                hyperv_user_password=_CONFIG_DATA.HyperVPassword,
                snap_name="PlainOS",
                vm_name=self.vm_name)
            self.log.info("Revert snap is successful")
            index_server_obj = self.commcell.index_servers.get(self.tcinputs['IndexServer'])
            client_list = index_server_obj.client_name
            client_list.append(self.tcinputs['AccessNode'])
            client_list.append(self.commcell.commserv_name)
            client_list.append(self.inputJSONnode['commcell']['webconsoleHostname'])
            self.vm_helper.populate_vm_ips_on_client(config_data=_CONFIG_DATA, clients=client_list)
        except Exception as except_setup:
            self.log.exception(except_setup)
            self.result_string = str(except_setup)
            self.status = constants.FAILED
            raise Exception("Test case setup(Reverting snap to Plain OS failed). Please check")

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("*************** Install content Analyzer client starts ****************")
            self.ca_helper_obj.install_content_analyzer(
                machine_name=self.vm_name,
                user_name=_CONFIG_DATA.VmUsername,
                password=_CONFIG_DATA.VmPassword,
                platform="Windows")
            self.log.info("Check whether python process is up and running on CA machine : %s", self.vm_name)
            self.log.info("Refreshing client list as we installed new client with CA package")
            self.commcell.clients.refresh()
            client_obj = self.commcell.clients.get(self.vm_name)
            self.ca_helper_obj.check_all_python_process(client_obj=client_obj)
            self.log.info("*************** Install content Analyzer client ends *****************")
            self.log.info("Going to get CA cloud details for : %s", self.ca_cloud_name)
            ca_cloud_obj = self.commcell.content_analyzers.get(self.ca_cloud_name)
            self.log.info("CA cloud URL : %s", ca_cloud_obj.cloud_url)
            self.ca_helper_obj.validate_tppm_setup(content_analyzer=self.ca_cloud_name)
            self.log.info("*************** Data source creation starts *****************")
            self.log.info("Going to create file system datasource : %s", self.datasource_name)
            access_node_client_obj = self.commcell.clients.get(
                self.tcinputs['Accessnodeclient'])
            self.log.info("Access node client object Initialised")
            access_node_clientid = access_node_client_obj.client_id
            self.log.info("Access node Client id : %s", str(access_node_clientid))
            entities_to_extract = {
                "RER": self.tcinputs['EntitiestoExtractRER']
            }
            ca_config = self.ds_helper.form_entity_extraction_config(entities=entities_to_extract,
                                                                     entity_fields=["content"])
            fs_dynamic_property = {
                "includedirectoriespath": self.tcinputs['IncludedirectoriesPath'],
                "username": self.tcinputs['UserName'],
                "password": self.tcinputs['Password'],
                "accessnodeclientid": access_node_clientid,
                "iscaenabled": "true",
                "caconfig": ca_config,
                "caclientid": str(ca_cloud_obj.client_id)
            }

            file_properties = self.ds_helper.form_file_data_source_properties(fs_dynamic_property)

            self.datasource_obj = self.ds_helper.create_file_data_source(data_source_name=self.datasource_name,
                                                                         index_server_name=self.tcinputs[
                                                                             'IndexServer'],
                                                                         fs_properties=file_properties)
            entities_to_extract_rer = self.tcinputs['EntitiestoExtractRER'].split(',')
            self.log.info("Going to get entity id details for : %s", entities_to_extract_rer)
            self.log.info("Entity input is of type : %s", type(entities_to_extract_rer))
            entity_keys = self.commcell.activate.entity_manager().get_entity_keys(entities_to_extract_rer)
            self.log.info("Entity key's got : %s", entity_keys)
            query_param = "("
            for entity_key in entity_keys:
                query_param = query_param + "entity_" + entity_key + ":* OR "
            query_param = query_param.rstrip(" OR ")
            query_param = query_param + ") AND CAState:1"
            self.log.info("Query param formed : %s", query_param)
            self.log.info("File system datasource created successfully")
            self.datasource_obj = self.commcell.datacube.datasources.get(
                self.datasource_name)
            self.datasource_id = self.datasource_obj.datasource_id
            self.log.info("Created DataSource id : %s", str(self.datasource_id))

            self.crawl_job_obj.monitor_crawl_job(self.datasource_name)
            self.log.info("*************** Data source creation ends *****************")
            self.log.info("********** Entity extraction verification starts **********")
            self.log.info("Cross verify whether entity got extracted for data set and pushed to solr")
            self.log.info("Going to create Handler :%s", self.handler_name)
            self.datasource_obj.ds_handlers.add(
                self.handler_name,
                search_query=[query_param])
            self.log.info("Handler created. Going to cross verify it by executing")
            self.handler_obj = self.datasource_obj.ds_handlers.get(self.handler_name)
            response_out = self.handler_obj.get_handler_data(handler_filter=dynamic_constants.SOLR_FETCH_ONE_ROW)
            self.log.info("Handler Data  : %s", str(response_out))
            total_docs = response_out['numFound']
            if total_docs == 0:
                self.log.info("Entity extraction didn't happen on CA machine. Please check")
                raise Exception("No document found with entity extracted")
            self.log.info("Documents found with entity extracted data : %s", total_docs)
            self.log.info("********** Entity extraction verification ends ************")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.log.exception(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.log.info("Going to delete datasource")
            self.commcell.datacube.datasources.delete(self.datasource_name)
            self.log.info("Datasource deleted successfully : %s", self.datasource_name)
            self.log.info("Going to delete CA client")
            self.commcell.clients.delete(self.vm_name)
            self.log.info("CA client deleted successfully : %s", self.vm_name)
            self.log.info("Going to Shutdown the vm : %s", self.vm_name)
            self.vm_helper.vm_shutdown(hyperv_name=_CONFIG_DATA.HyperVName,
                                       hyperv_user_name=_CONFIG_DATA.HyperVUsername,
                                       hyperv_user_password=_CONFIG_DATA.HyperVPassword,
                                       vm_name=self.vm_name)
            self.log.info("Power off vm successfull")
