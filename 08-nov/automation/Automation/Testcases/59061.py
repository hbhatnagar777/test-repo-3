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
        self.name = "File System Datasource : Verify incremental in content crawls"
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
        self.additional_folders_count = 0

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
        self.create_data_source()

    def full_job(self):
        """runs the full crawl job on data source"""
        self.log.info(f"Going to start FULL crawl job on the data source : {self.fs_data_source_name}")
        full_job_id = self.data_source_obj.start_job()
        self.ds_helper.monitor_crawl_job(job_id=full_job_id)
        additional_folders = self.data_path.split(os.path.sep)
        self.additional_folders_count = len(additional_folders)
        self.log.info(f"Additional folders count which needs to be added : {self.additional_folders_count}")
        self.index_server_helper.validate_data_in_core(
            data_source_obj=self.data_source_obj,
            file_count=len(self.machine_obj.get_files_in_path(folder_path=self.data_path)),
            folder_count=self.additional_folders_count + len(
                self.machine_obj.get_folders_in_path(folder_path=self.data_path)))

    def run(self):
        """Run function of this test case"""
        try:
            # FULL crawl job
            self.full_job()

            # Incrmental crawl job by adding new files in existing folder & new folders with new files
            self.ds_helper.file_crawl_after_random_folder_add(data_source_obj=self.data_source_obj,
                                                              machine_obj=self.machine_obj,
                                                              index_server_helper=self.index_server_helper,
                                                              test_data_path=self.data_path,
                                                              folder_name="INCR",
                                                              existing_folder="FULL",
                                                              file_count=self.file_count,
                                                              root_folder_count=self.additional_folders_count)

            # Incremental crawl job by modifying all files and deleting all files in folder
            self.ds_helper.file_crawl_after_folder_modify_delete(data_source_obj=self.data_source_obj,
                                                                 machine_obj=self.machine_obj,
                                                                 index_server_helper=self.index_server_helper,
                                                                 test_data_path=self.data_path,
                                                                 modify_folder_name="INCR_1",
                                                                 delete_folder_name="INCR_2",
                                                                 root_folder_count=self.additional_folders_count)

            # Incremental crawl job by modifying few file and deleting few file in folder
            self.ds_helper.file_crawl_after_random_file_modify_delete(data_source_obj=self.data_source_obj,
                                                                      machine_obj=self.machine_obj,
                                                                      index_server_helper=self.index_server_helper,
                                                                      test_data_path=self.data_path,
                                                                      file_count_to_alter=4,
                                                                      root_folder_count=self.additional_folders_count)

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
