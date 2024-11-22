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
from dynamicindex.vm_manager import VmManager
from dynamicindex.Datacube.data_source_helper import DataSourceHelper


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
        self.name = "Verify Fresh installation of CA package on Windows machine and validate RER, custom entity & NER" \
                    " on open datasource"
        self.tcinputs = {
            "EntitiestoExtractRER": None,
            "EntitiestoExtractNER": None,
            "IndexServer": None,
            "EntityTestData": None
        }
        self.vm_name = None
        self.ca_cloud_name = None
        self.ca_helper_obj = None
        self.datasource_name = None
        self.datasource_obj = None
        self.datasource_id = None
        self.timestamp = None
        self.handler_name = None
        self.handler_obj = None
        self.custom_entity = "AutomationFreshCADate"
        self.custom_regex = "(?:[0-9]{4}-[0-9]{2}-[0-9]{2})"
        self.custom_keywords = "date"
        self.open_column = ['id', 'comment']
        self.open_column_type = ['int', 'string']
        self.total_crawlcount = 0
        self.input_data = []
        self.test_data_comment = None
        self.datasource_properties = None
        self.hyperv_obj = None
        self.expected_entity = None
        self.entity_keys = []
        self.vm_helper = None
        self.ds_helper = None

    def setup(self):
        """Setup function of this test case"""
        try:
            self.vm_helper = VmManager(self)
            self.ds_helper = DataSourceHelper(self.commcell)
            self.ca_helper_obj = ContentAnalyzerHelper(self)
            self.timestamp = calendar.timegm(time.gmtime())
            self.datasource_name = "FreshCAClient_56579_" + str(self.timestamp)
            self.vm_name = _CONFIG_DATA.VmName
            self.ca_cloud_name = self.vm_name
            self.handler_name = "FreshCA_H1_" + str(self.timestamp)
            self.test_data_comment = self.tcinputs['EntityTestData'].split(",")
            self.expected_entity = self.tcinputs['ExpectedEntity']
            self.log.info("Expected Entity Json :%s", self.expected_entity)
            self.vm_helper.check_client_revert_snap(
                hyperv_name=_CONFIG_DATA.HyperVName,
                hyperv_user_name=_CONFIG_DATA.HyperVUsername,
                hyperv_user_password=_CONFIG_DATA.HyperVPassword,
                snap_name="PlainOS",
                vm_name=self.vm_name)
            self.log.info("Revert snap is successful")
            index_server_obj = self.commcell.index_servers.get(self.tcinputs['IndexServer'])
            client_list = index_server_obj.client_name
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
            self.log.info("*************** Data source creation starts *****************")
            entities_to_extract_rer = self.tcinputs['EntitiestoExtractRER'].split(',')
            entities_to_extract_ner = self.tcinputs['EntitiestoExtractNER'].split(',')
            self.log.info("Going to create custom entity : %s", self.custom_entity)
            if self.commcell.activate.entity_manager().has_entity(self.custom_entity):
                self.log.info("Custom entity found in commcell. Delete & recreate it")
                self.commcell.activate.entity_manager().delete(self.custom_entity)
            self.commcell.activate.entity_manager().add(entity_name=self.custom_entity, entity_regex=self.custom_regex,
                                                        entity_keywords=self.custom_keywords, entity_flag=5)
            self.log.info("Created custom entity successfully")
            entities_to_extract_rer.append(self.custom_entity)
            self.log.info("Going to get entity id details for RER : %s", entities_to_extract_rer)
            self.log.info("RER Entity input is of type : %s", type(entities_to_extract_rer))
            rer_entity_ids = self.commcell.activate.entity_manager().get_entity_ids(entities_to_extract_rer)
            self.log.info("RER Entity id's got : %s", rer_entity_ids)
            rer_entity_keys = self.commcell.activate.entity_manager().get_entity_keys(entities_to_extract_rer)
            self.log.info("RER Entity key's got : %s", rer_entity_keys)
            self.log.info("Going to get entity id details for NER : %s", entities_to_extract_ner)
            self.log.info("NER Entity input is of type : %s", type(entities_to_extract_ner))
            ner_entity_ids = self.commcell.activate.entity_manager().get_entity_ids(entities_to_extract_ner)
            self.log.info("NER Entity id's got : %s", ner_entity_ids)
            ner_entity_keys = self.commcell.activate.entity_manager().get_entity_keys(entities_to_extract_ner)
            self.log.info("NER Entity key's got : %s", ner_entity_keys)
            ca_config = self.ca_helper_obj.generate_entity_config(
                rer=rer_entity_ids, ner=ner_entity_ids, entity_fields=self.open_column)
            self.log.info("CA config Json formed : %s", ca_config)
            query_param = "("
            for entity_key in rer_entity_keys:
                self.entity_keys.append(entity_key.lower())
                query_param = query_param + "entity_" + entity_key + ":* AND "
            for entity_key in ner_entity_keys:
                self.entity_keys.append(entity_key.lower())
                query_param = query_param + "entity_" + entity_key + ":* AND "
            query_param = query_param.rstrip(" AND ")
            query_param = query_param + ") AND CAState:1"
            self.log.info("Query param formed : %s", query_param)
            self.log.info("Going to create Open datasource : %s", self.datasource_name)
            datasource_prop_name = dynamic_constants.ENTITY_EXTRACTION_PROPERTY
            datasource_prop_value = ["true", ca_config, str(ca_cloud_obj.client_id)]
            self.datasource_properties = self.ds_helper.form_data_source_properties(datasource_prop_name,
                                                                                    datasource_prop_value)
            self.ds_helper.create_open_data_source(self.datasource_name,
                                                   self.tcinputs['IndexServer'],
                                                   self.datasource_properties)
            self.datasource_obj = self.commcell.datacube.datasources.get(
                self.datasource_name)
            self.datasource_id = self.datasource_obj.datasource_id
            self.log.info("Created DataSource id : %s", str(self.datasource_id))
            self.ds_helper.update_data_source_schema(data_source_name=self.datasource_name,
                                                     field_name=self.open_column,
                                                     field_type=self.open_column_type,
                                                     schema_field=dynamic_constants.SCHEMA_FIELDS)
            total_rows = len(self.test_data_comment)
            self.log.info("Total Entity Test Data rows : %s", total_rows)
            self.log.info("Calling import data on this datasource")
            for data_row in range(total_rows):
                data_list = {
                    self.open_column[0]: str(data_row),
                    self.open_column[1]: self.test_data_comment[data_row]
                }
                self.total_crawlcount = self.total_crawlcount + 1
                self.input_data.append((data_list))
            self.log.info("Import Data formed : %s", str(self.input_data))
            self.datasource_obj.import_data(self.input_data)
            self.log.info("Import Data done successfully")
            self.log.info("Sleep for 2mins to make sure EE happened")
            time.sleep(120)
            self.log.info("Total document count : %s", str(self.total_crawlcount))
            self.log.info("*************** Data source creation ends *****************")
            self.log.info("********** Entity extraction verification starts **********")
            self.log.info("Cross verify whether entity got extracted for data set and pushed to solr")
            self.log.info("Going to create Handler :%s", self.handler_name)
            self.datasource_obj.ds_handlers.add(
                self.handler_name,
                search_query=[query_param])
            self.log.info("Handler created. Going to cross verify it by executing")
            self.handler_obj = self.datasource_obj.ds_handlers.get(self.handler_name)
            response_out = self.handler_obj.get_handler_data()
            self.log.info("Handler Data  : %s", str(response_out))
            total_docs = response_out['numFound']
            if total_docs == 0:
                self.log.info("Entity extraction didn't happen on CA machine. Please check")
                raise Exception("No document found with entity extracted")
            self.log.info("Documents found with entity extracted data : %s", total_docs)
            if total_docs != self.total_crawlcount:
                raise Exception("Few entities got missed in few documents. Please check")
            self.log.info("Entity extracted document count & crawl count matched - %s", self.total_crawlcount)
            self.log.info("Cross verify whether extracted entity really comes from source data")
            self.log.info("Final Entity keys for verification :%s", self.entity_keys)
            self.ca_helper_obj.check_extracted_entity_with_src(solr_response=response_out,
                                                               entity_keys=self.entity_keys,
                                                               source_data=self.tcinputs['EntityTestData'],
                                                               expected_entity=self.expected_entity)
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
            self.log.info("Going to delete custom entity : %s", self.custom_entity)
            self.commcell.activate.entity_manager().delete(self.custom_entity)
            self.log.info("Custom entity deleted successfully")
            self.log.info("Going to delete CA client")
            self.commcell.clients.delete(self.vm_name)
            self.log.info("CA client deleted successfully : %s", self.vm_name)
            self.log.info("Going to Shutdown the vm : %s", self.vm_name)
            self.vm_helper.vm_shutdown(hyperv_name=_CONFIG_DATA.HyperVName,
                                       hyperv_user_name=_CONFIG_DATA.HyperVUsername,
                                       hyperv_user_password=_CONFIG_DATA.HyperVPassword,
                                       vm_name=self.vm_name)
            self.log.info("Power off vm successfull")
