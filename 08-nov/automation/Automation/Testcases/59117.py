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
        self.name = "File System DataSource : verify crawl job for failed items in metadata push"
        self.tcinputs = {
            "IndexServer": None,
            "AccessNode": None,
            "FileSharePath": None,  # Share path should be on Accessnode as we need to change file permissions.
            "FilePathUserName": None,
            "FilePathPassword": None,
            "LocalFilePathForSharedPath": None  # Local path for the corresponding shared path provided above
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
        self.lock_folder = None
        self.lock_file_count = 0
        self.source_file_count = 0
        self.deny_folder_name = "Deny_Full"

    def create_data_source(self):
        """Creates the file system data source with metadata & incremental option checked"""
        self.log.info(f"Going to create file system data source : {self.fs_data_source_name}")
        access_node_client_obj = self.commcell.clients.get(
            self.tcinputs['AccessNode'])
        self.log.info(f"Access Node Client object Initialised")
        access_node_clientid = access_node_client_obj.client_id
        self.log.info(f"Access node Client id : {access_node_clientid}")
        fs_dynamic_property = {
            "includedirectoriespath": self.tcinputs['FileSharePath'],
            "username": self.tcinputs['FilePathUserName'],
            "password": self.tcinputs['FilePathPassword'],
            "accessnodeclientid": access_node_clientid,
            "pushonlymetadata": "true",
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
        # delete all left over data if any from this path
        self.machine_obj.clear_folder_content(folder_path=self.tcinputs['LocalFilePathForSharedPath'])
        self.data_path = os.path.join(self.tcinputs['LocalFilePathForSharedPath'],
                                      self.option_helper_obj.get_custom_str())
        self.ds_helper.populate_test_data(
            machine_obj=self.machine_obj,
            test_data_path=self.data_path,
            folder_name="Normal_Full",
            file_count=self.file_count,
            file_name="NormalFiles.txt")
        self.ds_helper.populate_test_data(
            machine_obj=self.machine_obj,
            test_data_path=self.data_path,
            folder_name=self.deny_folder_name,
            file_count=self.file_count,
            file_name="DeniedFiles.txt")
        self.lock_folder = os.path.join(self.data_path, self.deny_folder_name)
        self.log.info(f"Test data generated successfully.")
        self.create_data_source()

    def set_permission_files_in_client(self):
        """Randomly sets deny permission for user on folder on data generated in client"""
        self.log.info(f"Going to lock folder : {self.lock_folder}")
        self.lock_file_count = len(self.machine_obj.get_files_in_path(folder_path=self.lock_folder))
        file_list = self.machine_obj.get_files_in_path(folder_path=self.data_path)
        self.source_file_count = len(file_list)
        self.log.info(f"Total files to be locked : {self.lock_file_count}")
        self.log.info(f"Total files before lock : {self.source_file_count}")
        self.machine_obj.windows_operation(user=self.tcinputs['FilePathUserName'], path=self.lock_folder,
                                           action=dynamic_constants.DENY, inheritance="0",
                                           permission=dynamic_constants.FULL_CONTROL, modify_acl=True, folder=True)
        self.log.info(f"Modified permission for folder : {self.lock_folder}")

    def start_job(self, job_state):
        """runs the crawl job on data source and make sure it completes with given job state"""
        self.log.info(f"Going to start crawl job on the data source : {self.fs_data_source_name}")
        full_job_id = self.data_source_obj.start_job()
        self.ds_helper.monitor_crawl_job(job_id=full_job_id, job_state=job_state)

    def run(self):
        """Run function of this test case"""
        try:
            # deny files by setting deny permission to folder
            self.set_permission_files_in_client()

            # FULL crawl job
            self.start_job(job_state=dynamic_constants.JOB_WITH_ERROR)

            # check file count
            resp = self.index_server_helper.index_server_obj.execute_solr_query(
                core_name=self.data_source_obj.computed_core_name, select_dict={
                    **dynamic_constants.QUERY_FILE_CRITERIA, **dynamic_constants.QUERY_CISTATE_SUCCESS})
            self.log.info(f"File count in source : {self.source_file_count}")
            self.log.info(f"Locked File count in source : {self.lock_file_count}")
            self.log.info(f"Solr file document count : {resp['response']['numFound']}")
            if self.source_file_count != int(resp['response']['numFound']) + self.lock_file_count:
                raise Exception(f"Locked files got pushed in crawl job. Please check logs")
            self.log.info("Crawl didn't push the locked files to solr.Going to reset permission and re-crawl again")

            # reset the permission using local folder path as network path will not be accesible for this user
            # for locked folder
            self.machine_obj.windows_operation(user=self.tcinputs['FilePathUserName'],
                                               path=self.lock_folder,
                                               action=dynamic_constants.DENY, inheritance="0",
                                               permission=dynamic_constants.FULL_CONTROL,
                                               remove=True, folder=True, modify_acl=True)
            self.log.info(f"Removed Deny permission for folder : {self.lock_folder}")

            # populate more data and then run incr job
            self.ds_helper.populate_test_data(machine_obj=self.machine_obj, test_data_path=self.data_path,
                                              folder_name="INCR", file_count=self.file_count, file_name="incr.txt")
            self.log.info(f"Test data generated successfully.")
            self.start_job(job_state=dynamic_constants.JOB_COMPLETE)

            # folder count is plus one as we push root folder of share path to solr
            self.index_server_helper.validate_data_in_core(file_criteria=dynamic_constants.QUERY_CISTATE_SUCCESS,
                data_source_obj=self.data_source_obj, file_count=len(
                    self.machine_obj.get_files_in_path(folder_path=self.data_path)),
                folder_count= len(self.machine_obj.get_folders_in_path(folder_path=self.data_path)))

            self.log.info("Source and Solr document count matched. Failed items got re-pushed successfully")

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
