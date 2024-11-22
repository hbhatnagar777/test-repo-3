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
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this test case

    run()                           --  run function of this test case

    tear_down()                     --  tear down function of this test case

    create_data_source()            --  creates the file system data source

"""
import calendar
import time
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.utils import constants as dynamic_constants
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
        self.name = "File System DataSource : validate extractor timeout handling"
        self.tcinputs = {
            "IndexServer": None,
            "AccessNode": None,
            "IncludedirectoriesPath": None
        }
        self.data_source_obj = None
        self.fs_data_source_name = "Dcube_crawl_Content_"
        self.ds_helper = None
        self.machine_obj = None
        self.client_obj = None
        self.index_server_helper = None

    def create_data_source(self):
        """Creates the file system data source"""
        self.log.info(f"Going to create file system data source : {self.fs_data_source_name}")
        access_node_client_obj = self.commcell.clients.get(
            self.tcinputs['AccessNode'])
        self.log.info(f"Access Node Client object Initialised")
        access_node_clientid = access_node_client_obj.client_id
        self.log.info(f"Access node Client id : {access_node_clientid}")
        fs_dynamic_property = {
            "includedirectoriespath": self.tcinputs['IncludedirectoriesPath'],
            "accessnodeclientid": access_node_clientid,
            "pushonlymetadata": "false",
            "includefilters": dynamic_constants.FILE_DS_INCLUDE_FILE_TYPES,
            "maximumdocumentsize":"104857600"
        }

        file_properties = self.ds_helper.form_file_data_source_properties(fs_dynamic_property)

        self.data_source_obj = self.ds_helper.create_file_data_source(data_source_name=self.fs_data_source_name,
                                                                      index_server_name=self.tcinputs[
                                                                          'IndexServer'],
                                                                      fs_properties=file_properties)

    def setup(self):
        """Setup function of this test case"""
        timestamp = calendar.timegm(time.gmtime())
        self.fs_data_source_name = f"{self.fs_data_source_name}{timestamp}"
        self.ds_helper = DataSourceHelper(self.commcell)
        self.index_server_helper = IndexServerHelper(self.commcell, self.tcinputs['IndexServer'])
        self.log.info(f"Going to create machine object for index server client - "
                      f"{self.index_server_helper.index_server_obj.client_name[0]}")
        self.client_obj = self.commcell.clients.get(self.index_server_helper.index_server_obj.client_name[0])
        self.machine_obj = Machine(machine_name=self.client_obj,
                                   commcell_object=self.commcell)
        self.log.info(
            f"Going to set extractor thread timeout & excel max size on Index server - {self.tcinputs['IndexServer']}")
        self.machine_obj.create_registry(key=dynamic_constants.CA_REGISTRY,
                                         value=dynamic_constants.EXTRACTOR_THREAD_TIME_OUT,
                                         data="1",
                                         reg_type=dynamic_constants.REG_DWORD)
        self.machine_obj.create_registry(key=dynamic_constants.CA_REGISTRY,
                                         value=dynamic_constants.EXCEL_MAX_SIZE_IN_MB,
                                         data="100",
                                         reg_type=dynamic_constants.REG_DWORD)
        self.log.info(f"Going to restart Content Extractor service on index server machine")
        self.client_obj.restart_service(service_name=dynamic_constants.CE_SERVICE_NAME)
        self.log.info("Service Restart finished")
        self.create_data_source()

    def run(self):
        """Run function of this test case"""
        try:
            job_id = self.data_source_obj.start_job()
            self.ds_helper.monitor_crawl_job(job_id=job_id, job_state=dynamic_constants.JOB_WITH_ERROR)

            # delete the registry now
            self.log.info(f"Going to remove extractor thread timeout on Index server - {self.tcinputs['IndexServer']}")
            self.machine_obj.remove_registry(key=dynamic_constants.CA_REGISTRY,
                                             value=dynamic_constants.EXTRACTOR_THREAD_TIME_OUT)
            self.machine_obj.remove_registry(key=dynamic_constants.CA_REGISTRY,
                                             value=dynamic_constants.EXCEL_MAX_SIZE_IN_MB)
            self.log.info(f"Going to restart Content Extractor service on index server machine")
            self.client_obj.restart_service(service_name=dynamic_constants.CE_SERVICE_NAME)
            self.log.info("Service Restart finished")
            time.sleep(60)
            try:
                resp = self.index_server_helper.index_server_obj.execute_solr_query(
                    core_name=self.data_source_obj.computed_core_name,
                    select_dict=dynamic_constants.QUERY_EXTRACTOR_TIME_OUT_DOCS)
            except Exception as ep:
                self.log.info("Something wrong in querying solr. Retrying once more")
                time.sleep(60)
                resp = self.index_server_helper.index_server_obj.execute_solr_query(
                    core_name=self.data_source_obj.computed_core_name,
                    select_dict=dynamic_constants.QUERY_EXTRACTOR_TIME_OUT_DOCS)
            self.index_server_helper.check_solr_doc_count(solr_response=resp, doc_count=-1)
            self.log.info("Extractor thread timeout validated successfully.")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.log.exception(exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info(f"Going to delete FS data source : {self.fs_data_source_name}")
            self.commcell.datacube.datasources.delete(self.fs_data_source_name)
            self.log.info(f"Deleted the FS data source : {self.fs_data_source_name}")
