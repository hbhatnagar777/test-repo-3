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
    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  tear down function of this test case

    get_entity_list()           --  gets entity list from test data path folder

    create_fs_data_source()     --  Creates FS data source and runs crawl job

    validate_pii_entities()     --  Validates extracted PII entities are matching with test data

    read_entity_file()          --  Reads entities file and returns entities as list

"""
import calendar
import time
import os

from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
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
        self.name = "Integration Test case for validating PII entities of different countries"
        self.tcinputs = {
            "TestDataFolder": None,
            "IndexServer": None,
            "AccessNode": None,
            "ContentAnalyserCloudName": None

        }
        self.test_data_path = None
        self.entity_list = None
        self.access_machine_obj = None
        self.entity_keys = None
        self.datasource_name = None
        self.ds_helper = None
        self.crawl_job_obj = None
        self.remote_test_data_path = None
        self.index_server_helper = None
        self.machine_obj = None
        self.timestamp = calendar.timegm(time.gmtime())
        self.test_error = []
        self.data_source_obj = None

    def read_entity_file(self, file_name):
        """Reads entity file and returns entities

                Args:

                    file_name       (str)       --  File name

                Returns:

                    list    --  List containing entities read from file

        """
        entity_list = []
        entity_file = open(file_name, "r")
        entity_file.readline()  # read first line which will be proximity keyword
        while True:
            line = entity_file.readline()
            if not line:
                break
            line = line.strip()  # strip the new line character
            entity_list.append(line)
        entity_file.close()
        return entity_list

    def validate_pii_entities(self):
        """Validates extracted PII entities are matching with test data"""
        valid_text_file_prefix = "Valid.txt"
        invalid_text_file_prefix = "InValid.txt"
        self.log.info(f"Going to get entity id details for RER : {self.entity_list}")
        self.entity_keys = self.commcell.activate.entity_manager().get_entity_keys(self.entity_list)
        self.log.info("Entity keys's got for RER : %s", self.entity_keys)
        index = 0
        for entity in self.entity_list:
            self.log.info("*****" * 15)
            self.log.info(f"Going to verify entity : {entity}")
            solr_field = f"entity_{self.entity_keys[index]}"
            expected_valid_entity_list = []
            expected_invalid_entity_list = []
            modified_entity = f"\"{entity}\""
            entity_query = {dynamic_constants.FIELD_KEYWORD_SEARCH: modified_entity}
            entity_query.update(dynamic_constants.QUERY_FILE_CRITERIA)
            resp = self.index_server_helper.index_server_obj.execute_solr_query(
                core_name=self.data_source_obj.computed_core_name,
                select_dict=entity_query,
                attr_list={dynamic_constants.FIELD_URL,
                           dynamic_constants.FIELD_ALL_ENTITIES})
            valid_file_path = f"{self.test_data_path}{self.machine_obj.os_sep}{entity}" \
                              f"{self.machine_obj.os_sep}{valid_text_file_prefix}"
            invalid_file_path = f"{self.test_data_path}{self.machine_obj.os_sep}{entity}" \
                                f"{self.machine_obj.os_sep}{invalid_text_file_prefix}"
            self.log.info(f"Valid file path : {valid_file_path}")
            self.log.info(f"InValid file path : {invalid_file_path}")
            if os.path.exists(valid_file_path):
                expected_valid_entity_list = self.read_entity_file(file_name=valid_file_path)
            else:
                self.log.info("Valid file doesn't exists in Test data path")
            if os.path.exists(invalid_file_path):
                expected_invalid_entity_list = self.read_entity_file(file_name=invalid_file_path)
            else:
                self.log.info("InValid file doesn't exists in Test data path")
            self.log.info(f"Expected Valid entity list : {expected_valid_entity_list}")
            self.log.info(f"Expected InValid entity list : {expected_invalid_entity_list}")
            for doc in resp[dynamic_constants.RESPONSE_PARAM][dynamic_constants.DOCS_PARAM]:
                doc_url = doc[dynamic_constants.FIELD_URL]
                self.log.info(f"Analyzing solr document with url : {doc_url}")
                if invalid_text_file_prefix.lower() in doc_url.lower():
                    if solr_field in doc:
                        self.test_error.append(
                            f"[Validate - {entity} in doc - {doc_url} Failed] "
                            f"Entities contains invalid entries : {doc[solr_field]}")
                    else:
                        self.log.info("Invalid entities are not present in solr document")
                    continue
                if valid_text_file_prefix.lower() in doc_url.lower():
                    self.log.info(f"Valid entity checks started on doc : {doc_url}")
                    if solr_field not in doc:
                        self.test_error.append(
                            f"[Validate - {entity} in doc - {doc_url} Failed] "
                            f"Entities are not present")
                    else:
                        actual_valid_entity_list = doc[solr_field]
                        if len(actual_valid_entity_list) != len(expected_valid_entity_list):
                            self.test_error.append(
                                f"[Validate - {entity} in doc - {doc_url} Failed] "
                                f"Expected entity count is : {len(expected_valid_entity_list)} but "
                                f"actual entity count is : {len(actual_valid_entity_list)}")
                        for valid_entity in expected_valid_entity_list:
                            if valid_entity not in actual_valid_entity_list:
                                self.test_error.append(
                                    f"[Validate - {entity} in doc - {doc_url} Failed] "
                                    f"Expected entity : {valid_entity} is not present in document : {doc_url}")
                        self.log.info(f"Valid entities matched with count : {len(expected_valid_entity_list)}")
                    continue
            index = index + 1

    def create_fs_data_source(self):
        """Creates FS data source and runs crawl job"""
        self.log.info(
            f"Going to Copy Test data to access node : {self.tcinputs['AccessNode']} "
            f"on path : {self.remote_test_data_path}")
        self.access_machine_obj.copy_from_local(local_path=self.test_data_path, remote_path=self.remote_test_data_path,
                                                raise_exception=True)
        self.log.info(f"Going to create file system data source - {self.datasource_name}")
        access_node_client_obj = self.commcell.clients.get(
            self.tcinputs['AccessNode'])
        self.log.info("Access node client object Initialised")
        access_node_clientid = access_node_client_obj.client_id
        self.log.info(f"Access node Client id : {str(access_node_clientid)}")
        entities_to_extract = {
            "RER": ','.join([str(elem) for elem in self.entity_list])
        }
        ca_config = self.ds_helper.form_entity_extraction_config(entities=entities_to_extract,
                                                                 entity_fields=dynamic_constants.FILE_DS_EE_COLUMN)
        ca_cloud_obj = self.commcell.content_analyzers.get(self.tcinputs['ContentAnalyserCloudName'])
        fs_dynamic_property = {
            "includedirectoriespath": self.remote_test_data_path,
            "accessnodeclientid": access_node_clientid,
            "iscaenabled": "true",
            "pushonlymetadata": "false",
            "caconfig": ca_config,
            dynamic_constants.ENTITY_EXTRACTION_CLOUDID: str(ca_cloud_obj.client_id)
        }
        file_properties = self.ds_helper.form_file_data_source_properties(fs_dynamic_property)
        self.data_source_obj = self.ds_helper.create_file_data_source(data_source_name=self.datasource_name,
                                                                      index_server_name=self.tcinputs[
                                                                          'IndexServer'],
                                                                      fs_properties=file_properties)

    def get_entity_list(self):
        """gets the entity list from the given test data path"""
        self.entity_list = os.listdir(self.test_data_path)
        self.log.info(f"PII Entity to be validated - {self.entity_list}")

    def setup(self):
        """Setup function of this test case"""

        self.datasource_name = "FileAuto_PII_60633_" + str(self.timestamp)
        self.test_data_path = self.tcinputs['TestDataFolder']
        self.ds_helper = DataSourceHelper(self.commcell)
        self.crawl_job_obj = CrawlJobHelper(self)
        self.index_server_helper = IndexServerHelper(self.commcell, self.tcinputs['IndexServer'])
        self.machine_obj = Machine()
        self.log.info(f"Going to find list of entities from given Test data path : {self.test_data_path}")
        self.access_machine_obj = Machine(machine_name=self.tcinputs['AccessNode'], commcell_object=self.commcell)
        option_obj = OptionsSelector(self.commcell)
        self.remote_test_data_path = f"{option_obj.get_drive(machine=self.access_machine_obj)}" \
                                     f"PIITesting_{self.timestamp}"
        self.get_entity_list()
        self.create_fs_data_source()

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Going to start crawl job on this data source")
            self.crawl_job_obj.monitor_crawl_job(self.datasource_name)
            resp = self.index_server_helper.index_server_obj.execute_solr_query(
                core_name=self.data_source_obj.computed_core_name,
                select_dict=dynamic_constants.QUERY_FILE_CRITERIA)
            solr_doc_count = int(resp[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM])
            self.log.info(f"Solr document count : {solr_doc_count}")
            source_count = self.machine_obj.number_of_items_in_folder(folder_path=self.test_data_path,
                                                                      include_only="files",
                                                                      recursive=True,
                                                                      filter_name="*.txt")
            if int(source_count) != solr_doc_count:
                raise Exception(
                    f"Crawled document count Mismatched. Expected - {source_count}  Actual - {solr_doc_count} ")
            self.log.info(f"Crawled document count Matched. Count = {solr_doc_count}")
            self.log.info("Going to validate PII entities extracted during crawl job")
            self.validate_pii_entities()
            if len(self.test_error) > 0:
                self.log.info("*****" * 15)
                self.log.info("FAILED FILES DETAILS")
                for err_detail in self.test_error:
                    self.log.info(err_detail)
                self.log.info("*****" * 15)
                raise Exception(str(self.test_error))
            self.log.info("PII Entity validation - Passed")
            self.result_string = f" Validated {len(self.entity_list)} PII entities totally"

        except Exception as exp:
            self.log.exception('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.log.info(f"Going to delete the data source - {self.datasource_name}")
            self.commcell.datacube.datasources.delete(self.datasource_name)
            self.log.info(f"Deleted the FS data source : {self.datasource_name}")
            self.log.info("Going to delete PII test data on access node")
            self.access_machine_obj.remove_directory(directory_name=self.remote_test_data_path)
            self.log.info("Test data got deleted")
