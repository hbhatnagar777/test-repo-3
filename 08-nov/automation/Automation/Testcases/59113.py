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
import time
import calendar
import os
import random
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.index_server_helper import IndexServerHelper
from dynamicindex.utils import constants as dynamic_constants


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
        self.name = "File System DataSource : verify crawl job for failed items in content push"
        self.tcinputs = {
            "IndexServer": None,
            "AccessNode": None
        }
        self.data_source_obj = None
        self.timestamp = None
        self.fs_data_source_name = "Dcube_crawl_Content_"
        self.ds_helper = None
        self.machine_obj = None
        self.data_path = None
        self.option_helper_obj = None
        self.index_server_helper = None
        self.file_count = 10
        self.lock_file_list = None
        self.lock_process_pid = None

    def create_data_source(self):
        """Creates the file system data source with metadata & incremental option checked"""
        self.log.info(f"Going to create file system data source : {self.fs_data_source_name}")
        access_node_client_obj = self.commcell.clients.get(
            self.tcinputs['AccessNode'])
        self.log.info(f"Access Node Client object Initialised")
        access_node_clientid = access_node_client_obj.client_id
        self.log.info(f"Access node Client id : {access_node_clientid}")
        fs_dynamic_property = {
            "includedirectoriespath": self.data_path,
            "accessnodeclientid": access_node_clientid,
            "pushonlymetadata": "false",
            "doincrementalscan": "true",
            "includefilters": dynamic_constants.FILE_DS_INCLUDE_FILE_TYPES
        }

        file_properties = self.ds_helper.form_file_data_source_properties(fs_dynamic_property)

        self.data_source_obj = self.ds_helper.create_file_data_source(data_source_name=self.fs_data_source_name,
                                                                      index_server_name=self.tcinputs[
                                                                          'IndexServer'],
                                                                      fs_properties=file_properties)

    def setup(self):
        """Setup function of this test case"""
        self.timestamp = calendar.timegm(time.gmtime())
        self.option_helper_obj = OptionsSelector(self.commcell)
        self.fs_data_source_name = f"{self.fs_data_source_name}{self.timestamp}"
        self.ds_helper = DataSourceHelper(self.commcell)
        self.index_server_helper = IndexServerHelper(self.commcell, self.tcinputs['IndexServer'])
        self.machine_obj = Machine(machine_name=self.commcell.clients.get(self.tcinputs['AccessNode']),
                                   commcell_object=self.commcell)
        self.data_path = os.path.join(
            self.option_helper_obj.get_drive(
                machine=self.machine_obj),
            self.option_helper_obj.get_custom_str())
        self.ds_helper.populate_test_data(machine_obj=self.machine_obj, test_data_path=self.data_path,
                                          folder_name="FULL", file_count=self.file_count, file_name="full.txt")
        self.log.info(f"Test data generated successfully.")
        additional_folders = self.data_path.split(os.path.sep)
        self.additional_folders_count = len(additional_folders)
        self.log.info(f"Additional folders count which needs to be added : {self.additional_folders_count}")
        self.create_data_source()

    def lock_files_in_client(self):
        """Randomly locks file on data generated in client"""
        file_list = self.machine_obj.get_files_in_path(folder_path=self.data_path)
        file_list = [x.lower() for x in file_list]
        self.log.info(f"File list from dataset : {file_list}")
        # use random.sample to get unique files from list
        self.lock_file_list = random.sample(file_list, k=int(self.file_count / 2))
        self.log.info(f"Lock files list : {self.lock_file_list}")
        self.lock_process_pid = self.machine_obj.lock_file(file_list=self.lock_file_list)
        self.log.info(f"Locked files successfully with process id : {self.lock_process_pid}")

    def start_job(self, job_state):
        """runs the crawl job on data source and make sure it completes with given job state"""
        self.log.info(f"Going to start crawl job on the data source : {self.fs_data_source_name}")
        full_job_id = self.data_source_obj.start_job()
        self.ds_helper.monitor_crawl_job(job_id=full_job_id, job_state=job_state)

    def run(self):
        """Run function of this test case"""
        try:
            # lock files
            self.lock_files_in_client()

            # FULL crawl job
            self.start_job(job_state=dynamic_constants.JOB_WITH_ERROR)

            # query content field from solr and make sure it is empty for locked files
            solr_resp = self.index_server_helper.index_server_obj.execute_solr_query(
                core_name=self.data_source_obj.computed_core_name,
                select_dict=dynamic_constants.QUERY_FILE_CRITERIA,
                attr_list={dynamic_constants.FIELD_CONTENT, dynamic_constants.FIELD_URL},
                op_params=dynamic_constants.QUERY_100_ROWS)

            self.ds_helper.check_content_for_solr_docs(solr_response=solr_resp, file_list=self.lock_file_list,
                                                       content_present=False, check_all=False)

            # Kill the lock process
            for process in self.lock_process_pid:
                self.machine_obj.kill_process(process_id=process)
                self.log.info(f"Lock process with Pid : {process} killed successfully")

            # populate more data and then run incr job
            self.ds_helper.populate_test_data(machine_obj=self.machine_obj, test_data_path=self.data_path,
                                              folder_name="INCR", file_count=self.file_count, file_name="incr.txt")
            self.log.info(f"Test data generated successfully.")
            self.start_job(job_state=dynamic_constants.JOB_COMPLETE)

            self.index_server_helper.validate_data_in_core(
                data_source_obj=self.data_source_obj, file_count=len(
                    self.machine_obj.get_files_in_path(folder_path=self.data_path)),
                folder_count=self.additional_folders_count +
                len(self.machine_obj.get_folders_in_path(folder_path=self.data_path)))

            # query content field from solr and make sure it is not empty
            solr_resp = self.index_server_helper.index_server_obj.execute_solr_query(
                core_name=self.data_source_obj.computed_core_name,
                select_dict=dynamic_constants.QUERY_FILE_CRITERIA,
                attr_list={dynamic_constants.FIELD_CONTENT, dynamic_constants.FIELD_URL},
                op_params=dynamic_constants.QUERY_100_ROWS)

            self.ds_helper.check_content_for_solr_docs(solr_response=solr_resp, file_list=self.lock_file_list,
                                                       content_present=True,check_all=True)
            self.log.info("Files which was locked got pushed in next crawl correctly.")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.log.exception(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info(f"Going to delete FS data source : {self.fs_data_source_name}")
            self.commcell.datacube.datasources.delete(self.fs_data_source_name)
            self.log.info(f"Deleted the FS data source : {self.fs_data_source_name}")
            self.log.info(f"Going to delete generated data on access node : {self.data_path}")
            self.machine_obj.remove_directory(directory_name=self.data_path)
            self.log.info("Deleted the test data files successfully")
