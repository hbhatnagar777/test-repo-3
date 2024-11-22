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
import os
import time
import calendar
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.index_server_helper import IndexServerHelper
from FileSystem.FSUtils.onepasshelper import cvonepas_helper


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
        self.name = "File System DataSource : verify crawl job for cvstub items"
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None,
            "IndexServer": None
        }
        self.machine_obj = None
        self.option_helper_obj = None
        self.OPHelper = None
        self.data_source_obj = None
        self.timestamp = None
        self.fs_data_source_name = "Dcube_crawl_Meta_"
        self.ds_helper = None
        self.index_server_helper = None
        self.stub_size = 8  # in KB
        self.non_stub_size = 4  # in KB

    def validate_stub(self, meta_data=True):
        """validates stubbed documents pushed to index server with Isstub=1 or not

                Args:

                    meta_data   (bool)  --   specifies whether to validate content field or not
                                                        default=True

                Returns:

                    None
        """
        file_list = self.machine_obj.get_files_in_path(folder_path=self.tcinputs['TestPath'])
        self.log.info(f"File list from test data : {file_list}")
        total_file_stubbed = 0
        total_file_not_stubbed = 0
        for stub_file in file_list:
            if self.machine_obj.is_stub(file_name=stub_file):
                total_file_stubbed = total_file_stubbed + 1
                self.log.info(f"Stub file : {stub_file}")
            else:
                self.log.info(f"Non-Stub file : {stub_file}")
                total_file_not_stubbed = total_file_not_stubbed + 1
        self.log.info(f"Total stub files in test data : {total_file_stubbed}")
        resp = self.index_server_helper.index_server_obj.execute_solr_query(
            core_name=self.data_source_obj.computed_core_name,
            select_dict=dynamic_constants.QUERY_CVSTUB_CRITERIA,
            attr_list={
                dynamic_constants.FIELD_CONTENT,
                dynamic_constants.FIELD_URL})
        if total_file_stubbed == 0:
            raise Exception("None of the generated data got stub. Please check archiving rules")
        if resp['response']['numFound'] != total_file_stubbed:
            raise Exception(f"Stub file mismatched. Expected : {total_file_stubbed} "
                            f"Actual : {resp['response']['numFound']}")
        self.log.info(f"Stubbed file count matched : {total_file_stubbed}")
        self.ds_helper.check_content_for_solr_docs(solr_response=resp, check_all=True, content_present=False)
        self.log.info("CVstub validation finished")

        if meta_data is False:
            self.log.info("Verify content field exists for non-stubbed files")
            resp = self.index_server_helper.index_server_obj.execute_solr_query(
                core_name=self.data_source_obj.computed_core_name,
                select_dict=dynamic_constants.QUERY_NON_STUB_FILE_CRITERIA,
                attr_list={
                    dynamic_constants.FIELD_CONTENT,
                    dynamic_constants.FIELD_URL})
            if resp['response']['numFound'] != total_file_not_stubbed:
                raise Exception(f"Non Stubbed file mismatched. Expected : {total_file_not_stubbed} "
                                f"Actual : {resp['response']['numFound']}")
            self.log.info(f"Non Stub file count matched : {total_file_not_stubbed}")
            self.ds_helper.check_content_for_solr_docs(solr_response=resp, check_all=True, content_present=True)
            self.log.info("Non-Stub Data documents validation finished")

    def create_data_source(self, meta_data=True):
        """Creates the file system data source with metadata option checked

                Args:

                    meta_data   (bool)  --   specifies whether to create FS datasource with metadata or content option
                                                                    default=True

                Returns:
                    None
        """
        self.log.info(f"Going to create file system data source : {self.fs_data_source_name}")
        self.log.info(f"Access node Client id : {self.client.client_id}")
        fs_dynamic_property = {
            "includedirectoriespath": self.tcinputs['TestPath'],
            "accessnodeclientid": self.client.client_id,
            "pushonlymetadata": "true" if meta_data else "false",
            "doincrementalscan": "false"
        }
        file_properties = self.ds_helper.form_file_data_source_properties(fs_dynamic_property)
        self.data_source_obj = self.ds_helper.create_file_data_source(data_source_name=self.fs_data_source_name,
                                                                      index_server_name=self.tcinputs[
                                                                          'IndexServer'],
                                                                      fs_properties=file_properties)
        self.log.info("Going to start crawl job on this data source")
        job_id = self.data_source_obj.start_job()
        self.ds_helper.monitor_crawl_job(job_id=job_id)

    def create_stub_data(self):
        """create test data and run archive job to stub the items"""

        self.ds_helper.populate_test_data(
            machine_obj=self.machine_obj,
            test_data_path=self.tcinputs['TestPath'],
            folder_name="StubFolder",
            file_name="NonStub.txt",
            file_size=self.non_stub_size,
            file_count=5)
        self.ds_helper.populate_test_data(machine_obj=self.machine_obj, test_data_path=self.tcinputs['TestPath'],
                                          folder_name="StubFolder", file_name="Stub.txt", file_size=self.stub_size + 2,
                                          file_count=8)
        self.log.info("Test data populated successfully.")
        self.OPHelper.create_archiveset(delete=True, is_nas_turbo_backupset=False)
        self.OPHelper.create_subclient(delete=True, content=[self.tcinputs['TestPath']])
        _disk_cleanup_rules = {
            "useNativeSnapshotToPreserveFileAccessTime": False,
            "fileModifiedTimeOlderThan": 0,
            "fileSizeGreaterThan": self.stub_size,
            "stubPruningOptions": 0,
            "afterArchivingRule": 1,
            "stubRetentionDaysOld": 365,
            "fileCreatedTimeOlderThan": 0,
            "maximumFileSize": 0,
            "fileAccessTimeOlderThan": 0,
            "startCleaningIfLessThan": 100,
            "enableRedundancyForDataBackedup": False,
            "patternMatch": "",
            "stopCleaningIfupto": 100,
            "rulesToSatisfy": 1,
            "enableArchivingWithRules": True
        }
        self.OPHelper.testcase.subclient.archiver_retention = True
        self.OPHelper.testcase.subclient.archiver_retention_days = 1
        self.OPHelper.testcase.subclient.backup_retention = False
        self.OPHelper.testcase.subclient.disk_cleanup = True
        self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules
        self.OPHelper.testcase.subclient.backup_only_archiving_candidate = True
        self.OPHelper.run_archive(repeats=1)

    def setup(self):
        """Setup function of this test case"""
        self.timestamp = calendar.timegm(time.gmtime())
        self.fs_data_source_name = f"{self.fs_data_source_name}{self.timestamp}"
        self.ds_helper = DataSourceHelper(self.commcell)
        self.index_server_helper = IndexServerHelper(self.commcell, self.tcinputs['IndexServer'])
        self.option_helper_obj = OptionsSelector(self.commcell)
        self.log.info(f"Going to populate test data on client : {self.client.name}")
        self.machine_obj = Machine(machine_name=self.client,
                                   commcell_object=self.commcell)
        self.tcinputs['TestPath'] = os.path.join(
            self.option_helper_obj.get_drive(machine=self.machine_obj),
            self.tcinputs['TestPath'],
            self.option_helper_obj.get_custom_str())
        self.log.info(f"Folder path : {self.tcinputs['TestPath']}")
        self.OPHelper = cvonepas_helper(self)
        self.OPHelper.populate_inputs()
        self.log.info("Test inputs populated successfully.")
        self.create_stub_data()

    def delete_data_source(self):
        """Deletes the file system data source"""
        self.log.info(f"Going to delete FS data source : {self.fs_data_source_name}")
        self.commcell.datacube.datasources.delete(self.fs_data_source_name)
        self.log.info(f"Deleted the FS data source : {self.fs_data_source_name}")

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Stub data created !!! Proceed with creating file system data sources")
            self.create_data_source(meta_data=True)
            self.validate_stub()
            self.delete_data_source()
            self.timestamp = calendar.timegm(time.gmtime())
            self.fs_data_source_name = f"{self.fs_data_source_name}{self.timestamp}"
            self.log.info(f"Going to create FS data source with content option enabled : {self.fs_data_source_name}")
            self.create_data_source(meta_data=False)
            self.validate_stub(meta_data=False)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.log.exception(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info(f"Going to delete FS data source : {self.fs_data_source_name}")
            self.commcell.datacube.datasources.delete(self.fs_data_source_name)
            self.log.info(f"Deleted the FS data source : {self.fs_data_source_name}")
            self.log.info(f"Going to delete generated data on access node : {self.tcinputs['TestPath']}")
            self.machine_obj.remove_directory(directory_name=self.tcinputs['TestPath'])
            self.log.info("Deleted the test data files successfully")
