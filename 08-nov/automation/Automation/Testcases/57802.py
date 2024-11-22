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
import shutil

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.config import get_config
from dynamicindex.content_analyzer_helper import ContentAnalyzerHelper
from dynamicindex.vm_manager import VmManager
from dynamicindex.utils.activateutils import ActivateUtils
from dynamicindex.utils.search_engine_util import SearchEngineHelper
from dynamicindex.utils import constants as Entity_constant
from dynamicindex.entity_extraction_thread import EntityExtractionThread


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
        self.name = "Verify Fresh installation of CA package on Windows machine and validate RER & custom entity" \
                    " for Offline CI'ed docs"
        self.tcinputs = {
            "EntityTestData": None,
            "TestDataSQLiteDBPath": None,
            "SearchEngineClientName": None,
            "MediaAgent": None,
            "Library": None
        }
        self.vm_name = None
        self.ca_helper_obj = None
        self.expected_entity = None
        self.entity_keys = []
        self.vm_helper = None
        self.activate_util = None
        self.data_path = None
        self.search_engine = None
        self.storage_policy = None
        self.media_agent = None
        self.library = None
        self.search_engine_helper = None
        self.subclient = None
        self.entity_db_path = None
        self.db_query_field = "FilePath"
        self.solr_query_field = "url"
        self.ee_query = None
        self.entity_list = None
        self.entity_key_list = None
        self.solr_url = None
        self.storage_policy_obj = None
        self.subclient_obj = None
        self.delimiter = Entity_constant.DB_ENTITY_DELIMITER
        self.ner_data_path = None
        self.ner_file_name = "Ner_test_data.txt"
        self.custom_entity = Entity_constant.ENTITY_AUTOMATION
        self.custom_regex = Entity_constant.ENTITY_AUTOMATION_REGEX
        self.custom_keywords = Entity_constant.ENTITY_AUTOMATION_KEYWORDS
        self.ca_cloud_name = None
        self.machine_obj = None

    def generate_custom_file(self, file_path, data):
        """
            Generate sensitive single file with test data provided

                Args:
                    file_path (str)  -- Path of file
                    data      (str)  -- content which needs to be written to the file

                Returns:
                    None
        """
        file_ptr = open(file_path, "a")
        file_ptr.write(data)
        file_ptr.close()
        self.log.info("Successfully created the NER test data file")

    def generate_sensitive_files_copy_to_machine(self):
        """
            Generate sensitive files with PII entities and then copies to client machine
        """
        if os.path.exists(self.entity_db_path):
            self.log.info("old Entity db exists. Deleting it")
            os.remove(self.entity_db_path)
        if os.path.exists(self.data_path):
            self.log.info("old data exists. Deleting it")
            os.remove(self.data_path)
        self.log.info("Going to create random 25 files for entity extraction")
        self.activate_util.sensitive_data_generation(database_path=self.data_path, number_files=25)
        self.ner_data_path = f"{self.data_path}\\GENERATED_DATA\\{self.ner_file_name}"
        self.generate_custom_file(file_path=self.ner_data_path, data=self.tcinputs['EntityTestData'])
        self.log.info("Going to copy this data to Client machine to run backup : %s", self.client.name)
        if self.machine_obj.check_directory_exists(directory_path=self.data_path):
            self.machine_obj.remove_directory(directory_name=self.data_path)
            self.log.info("Directory exists on remote client. Deleting it")
        self.log.info("Started copying data . . . .")
        generated_data_path = rf"{self.data_path}\\GENERATED_DATA"
        self.machine_obj.copy_from_local(
            local_path=generated_data_path,
            remote_path=self.data_path,
            raise_exception=True)
        self.log.info("Successfully copied data to remote machine")

    def create_subclient_run_backup_ci(self):
        """
            Creates the storage policy , enables CI and then creates subclient pointing to it
        """
        self.log.info("Storage policy to be created : %s", self.storage_policy)
        self.commcell.storage_policies.add(storage_policy_name=self.storage_policy,
                                           library=self.library,
                                           media_agent=self.media_agent)
        self.log.info("Going to configure storage policy with CI enabled for search engine : %s", self.search_engine)
        cloud_id = self.search_engine_helper.get_cloud_id(self.search_engine)
        self.log.info("Cloud id for the search engine is : %s", cloud_id)
        self.storage_policy_obj = self.commcell.storage_policies.get(self.storage_policy)
        self.storage_policy_obj.enable_content_indexing(cloud_id=cloud_id)
        self.log.info("Successfully configured CI on storage policy")
        self.log.info("Going to create new subclient : %s", self.subclient)
        self.subclient_obj = self.backupset.subclients.add(subclient_name=self.subclient,
                                                           storage_policy=self.storage_policy)

        self.subclient_obj.content = [self.data_path]
        job_obj = self.subclient_obj.backup('Full')
        self.log.info("Invoked the FS backup job with id : %s", job_obj.job_id)
        self.log.info("Going to Monitor this backup job for completion")
        if not job_obj.wait_for_completion(timeout=90):
            self.log.info("Backup job failed on storage policy. Please check logs")
            raise Exception("Backup job failed on storage policy")
        self.log.info("Backup job is finished")

        self.log.info("Start the content indexing job for this storage policy")
        job_obj = self.storage_policy_obj.run_content_indexing()
        self.log.info("Invoked the content indexing job with id : %s", job_obj.job_id)
        self.log.info("Going to Monitor this CI job for completion")
        if not job_obj.wait_for_completion(timeout=90):
            self.log.info("Content indexing job failed on storage policy. Please check logs")
            raise Exception("Content indexing job failed on storage policy")
        self.log.info("Content indexing job is finished")

    def run_entity_extraction(self):
        """
            Enables entity extraction at storage policy level and monitors Entity extraction job for subclient
        """
        self.log.info("Going to enable entity extraction for this storage policy")
        subclient_list = [[self.client.name, 'File System', 'defaultBackupSet', self.subclient]]
        self.storage_policy_obj = self.commcell.storage_policies.get(self.storage_policy)
        self.storage_policy_obj.enable_entity_extraction(entity_details=subclient_list,
                                                         entity_names=self.entity_list,
                                                         ca_client_name=self.vm_name)
        self.log.info("Successfully configured Entity extraction for this storage policy")
        self.solr_url = self.search_engine_helper.get_cloud_url(self.search_engine)
        extracting_times = self.ca_helper_obj.get_latest_extractingat_solr(
            solr_url=self.solr_url, subclient_ids=[self.subclient_obj.subclient_id])
        self.log.info("Response json from search engine : %s", extracting_times)
        self.ca_helper_obj.monitor_offline_entity_extraction(subclient_ids=[self.subclient_obj.subclient_id],
                                                             extracting_times=extracting_times)
        self.ee_query = "(apid:{0} AND (cistate:1 OR cistate:16) AND (datatype:1 OR datatype:2) AND !url:*{1})".format(
            self.subclient_obj.subclient_id, self.ner_file_name)
        client_obj = self.commcell.clients.get(self.vm_name)
        self.log.info("Shutdown the content extractor service as it will create paging error on solr query due to atomic updates")
        client_obj.stop_service(service_name=Entity_constant.CE_SERVICE_NAME)
        self.log.info("Successfully killed the content extractor process on CA client :%s", self.vm_name)

    def verify_entity_extraction_results(self):
        """
            cross verifies the entity extraction results for the subclient documents against solr
        """
        threads = []
        i = 1
        for entity in self.entity_key_list:
            thread = EntityExtractionThread(i, entity, self.entity_db_path, self.db_query_field,
                                            self.solr_query_field, self.ee_query,
                                            self.solr_url, self.delimiter)
            thread.start()
            threads.append(thread)
            i = i + 1

        for invoke_thread in threads:
            invoke_thread.join()

        for invoke_thread in threads:
            if invoke_thread.failed != 0 and invoke_thread.failed != invoke_thread.partial_success:
                self.log.info("Thread went down with some failed docs ThreadID : %s", invoke_thread.thread_id)
                self.log.info("Failed Count : %s", invoke_thread.failed)
                self.log.info("Partial success : %s", invoke_thread.partial_success)
                raise Exception("Entity Verification failed")
            else:
                self.log.info("Thread went down with all success ThreadID : %s", invoke_thread.thread_id)
                self.log.info("Success Count : %s", invoke_thread.success)

    def verify_custom_entity_results(self):
        """
            cross verifies the entity extraction custom entity results for the subclient documents against solr
        """
        self.ee_query = "(apid:{0} AND (cistate:1 OR cistate:16) AND (datatype:1 OR datatype:2) AND url:*{1})".format(
            self.subclient_obj.subclient_id, self.ner_file_name)
        solr_response = self.search_engine_helper.query_solr(
            solr_url=self.solr_url, criteria=self.ee_query, start=0, rows=1, fields=[
                Entity_constant.ENTITY_KEY_EMAIL, Entity_constant.ENTITY_KEY_AUTOMATION, "url"])
        self.ca_helper_obj.check_extracted_entity_with_src(
            solr_response=solr_response,
            entity_keys=[Entity_constant.ENTITY_KEY_EMAIL, Entity_constant.ENTITY_KEY_AUTOMATION],
            source_data=self.tcinputs['EntityTestData'],
            expected_entity=self.expected_entity)

    def revert_install_package(self):
        """
            Reverts the vm to fresh snap and then installs CA package on client
        """
        self.vm_helper.check_client_revert_snap(
            hyperv_name=_CONFIG_DATA.HyperVName,
            hyperv_user_name=_CONFIG_DATA.HyperVUsername,
            hyperv_user_password=_CONFIG_DATA.HyperVPassword,
            snap_name=_CONFIG_DATA.SnapName,
            vm_name=self.vm_name)
        self.log.info("Revert snap is successful")
        client_list = []
        client_list.append(self.tcinputs['SearchEngineClientName'])
        client_list.append(self.tcinputs['ClientName'])
        client_list.append(self.tcinputs['MediaAgent'])
        client_list.append(self.commcell.commserv_name)
        self.vm_helper.populate_vm_ips_on_client(config_data=_CONFIG_DATA, clients=client_list)
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

    def create_custom_entity(self):
        """
             Creates custom activate regex entity on commcell
        """
        self.log.info("Going to create custom entity : %s", self.custom_entity)
        if self.commcell.activate.entity_manager().has_entity(self.custom_entity):
            self.log.info("Custom entity found in commcell. Delete & recreate it")
            self.commcell.activate.entity_manager().delete(self.custom_entity)
        self.commcell.activate.entity_manager().add(entity_name=self.custom_entity, entity_regex=self.custom_regex,
                                          entity_keywords=self.custom_keywords, entity_flag=5)
        self.log.info("Created custom entity successfully")

    def setup(self):
        """Setup function of this test case"""
        try:
            self.vm_helper = VmManager(self)
            option_helper_obj = OptionsSelector(self.commcell)
            self.search_engine_helper = SearchEngineHelper(self)
            self.storage_policy = f"57802_{option_helper_obj.get_custom_str()}"
            self.subclient = f"57802_{option_helper_obj.get_custom_str()}"
            self.machine_obj = Machine(self.client)
            self.activate_util = ActivateUtils()
            self.ca_helper_obj = ContentAnalyzerHelper(self)
            this_dir = os.path.dirname(os.path.realpath('__file__'))
            self.entity_db_path = os.path.join(this_dir, 'CompiledBins', 'entity.db')
            self.vm_name = _CONFIG_DATA.VmName
            self.media_agent = self.tcinputs['MediaAgent']
            self.library = self.tcinputs['Library']
            self.data_path = self.tcinputs['TestDataSQLiteDBPath']
            self.ca_cloud_name = self.vm_name + "_ContentAnalyzer"
            self.data_path = f"{self.data_path}{option_helper_obj.get_custom_str()}"
            self.search_engine = self.tcinputs['SearchEngineClientName']
            self.expected_entity = self.tcinputs['ExpectedEntity']
            self.log.info("Expected Entity Json :%s", self.expected_entity)
            self.entity_list = [
                Entity_constant.ENTITY_EMAIL,
                Entity_constant.ENTITY_IP,
                Entity_constant.ENTITY_AUTOMATION
            ]
            # No need to add custom RER here as it is done separately
            self.entity_key_list = [Entity_constant.ENTITY_KEY_EMAIL, Entity_constant.ENTITY_KEY_IP]

            self.create_custom_entity()
            self.generate_sensitive_files_copy_to_machine()
            self.create_subclient_run_backup_ci()

        except Exception as except_setup:
            self.log.exception(except_setup)
            self.result_string = str(except_setup)
            self.status = constants.FAILED
            raise Exception("Test case setup(Environment) failed. Please check")

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Config data : %s", _CONFIG_DATA)
            self.revert_install_package()
            self.run_entity_extraction()
            self.verify_entity_extraction_results()
            self.verify_custom_entity_results()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.log.exception(exp)
            self.status = constants.FAILED

    def cleanup(self):
        """
            cleans the test environment entity created by this test case
        """

        self.log.info("Going to delete subclient : %s", self.subclient)
        self.backupset.subclients.delete(self.subclient)
        self.log.info("Deleted subclient")
        self.log.info("Going to delete storage policy : %s", self.storage_policy)
        self.commcell.storage_policies.delete(self.storage_policy)
        self.log.info("Deleted the storage policy")
        self.log.info("Going to delete custom entity : %s", self.custom_entity)
        self.commcell.activate.entity_manager().delete(self.custom_entity)
        self.log.info("Custom entity deleted successfully")
        self.log.info("Going to delete CA cloud pseudoclient")
        self.commcell.clients.delete(self.ca_cloud_name)
        self.log.info("Refresh the content analyzer details in the commcell and recheck for CA cloud exists or not")
        self.commcell.content_analyzers.refresh()
        if self.commcell.content_analyzers.has_cloud(self.ca_cloud_name):
            raise Exception("Content analyzer cloud still exists")
        self.log.info("CA Cloud pseudoclient deleted successfully : %s", self.ca_cloud_name)
        self.log.info("Going to delete CA client")
        self.commcell.clients.delete(self.vm_name)
        self.log.info("CA client deleted successfully : %s", self.vm_name)
        self.log.info("Going to Shutdown the vm : %s", self.vm_name)
        self.vm_helper.vm_shutdown(hyperv_name=_CONFIG_DATA.HyperVName,
                                   hyperv_user_name=_CONFIG_DATA.HyperVUsername,
                                   hyperv_user_password=_CONFIG_DATA.HyperVPassword,
                                   vm_name=self.vm_name)
        self.log.info("Power off vm successfull")
        if os.path.exists(self.data_path):
            self.log.info("Deleting the generated file on controller")
            shutil.rmtree(self.data_path, ignore_errors=True)
        if self.machine_obj.check_directory_exists(directory_path=self.data_path):
            self.machine_obj.remove_directory(directory_name=self.data_path)
            self.log.info("Deleting the generated files on client where backup was done")

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.cleanup()
