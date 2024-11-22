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
    __init__()              --  initialize TestCase class

    setup()                 --  setup function of this test case

    run()                   --  run function of this test case

    tear_down()             --  tear down function of this test case

    create_subclient()      --  Creates new backupset and subclient

    run_backup_and_ci()     --  runs a file system subclient backup and Content indexing job

    cleanup()                   --  performs cleanup of test environment

    validate_local_ca()         --  Validates connection error on index gateway log

    validate_search()           --  Validates content search on ciéd data

"""
import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Server.JobManager.jobmanager_helper import JobManager
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.activate_sdk_helper import ActivateSDKHelper
from dynamicindex.extractor_helper import ExtractingClusterHelper
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.utils.activateutils import ActivateUtils


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
        self.name = "CE Kubernetes Cluster - Validate V2 FS content indexing job uses correct region as per Access node workload region"
        self.tcinputs = {
            "IndexServer": None,
            "YamlFile": None,
            "IndexGatewayClient": None,
            "ClientName": None,
            "IGUserName": None,
            "IGPassword": None,
            "MediaAgentName": None,
            "DataPath": None,
            "Library": None,
            "AccessNode": None,
            "Searches": None,
            "WebServer": None,
            "WebUserName": None,
            "WebPassword": None,
        }
        self.index_server_name = None
        self.cluster_helper = None
        self.file_policy_name = None
        self.storage_policy_name = None
        self.subclient_name = None
        self.backupset_name = None
        self.media_agent_name = None
        self.subclient_content = None
        self.library_name = None
        self.client_name = None
        self.fs_agent_object = None
        self.ci_job = None
        self.external_ip = None

    def validate_local_ca(self):
        """Validates connection error on index gateway log for local CA"""
        pattern = f"status \\[ServiceUnavailable] for url \\[http://localhost:{dynamic_constants.DEFAULT_CA_PORT}"
        gateway_machine_obj = Machine(
            machine_name=self.tcinputs['IndexGatewayClient'],
            commcell_object=self.commcell)
        time_limit = time.time() + 30 * 60  # 30mins
        while True:
            log_lines = gateway_machine_obj.get_logs_for_job_from_file(
                log_file_name=dynamic_constants.INDEX_GATEWAY_LOG_NAME, search_term=pattern)
            if log_lines:
                break
            if time.time() >= time_limit:
                raise Exception(
                    f"No connection error logs for this pattern {pattern} found in index gateway.log for past 30mins")
            time.sleep(30)
        self.log.info(
            "Connection to localhost CA Error present in IndexGateway.log. No of entries - {}".format(len(log_lines.split('\r\n'))))

    def cleanup(self, post_cleanup=False):
        """Perform Cleanup Operation"""
        activate_utils = ActivateUtils(commcell=self.commcell)
        activate_utils.activate_cleanup(
            commcell_obj=self.commcell,
            storage_policy_name=self.storage_policy_name,
            ci_policy_name=self.file_policy_name,
            client_name=self.client_name,
            backupset_name=self.backupset_name
        )
        if post_cleanup:
            activate_utils.set_dm2_settings(
                webserver=self.tcinputs['WebServer'],
                setting_name=dynamic_constants.RECALL_BASED_PREVIEW_SETTING,
                setting_value='allowed')
        else:
            # Disable on-demand start of Content extractor
            activate_utils.set_dm2_settings(
                webserver=self.tcinputs['WebServer'],
                setting_name=dynamic_constants.RECALL_BASED_PREVIEW_SETTING,
                setting_value='False')
        web_machine_obj = Machine(
            machine_name=self.tcinputs['WebServer'],
            username=self.tcinputs['WebUserName'],
            password=self.tcinputs['WebPassword'])
        web_machine_obj.restart_iis()
        self.log.info(
            f"Restarted IIS on webserver. Waiting for 5mins to come up")
        time.sleep(300)

    def create_subclient(self):
        """Creates new backupset and subclient on client"""

        self.log.info(f"Creating new CI policy {self.file_policy_name}")
        policy_object = self.commcell.policies.configuration_policies. \
            get_policy_object(dynamic_constants.CI_POLICY_TYPE, self.file_policy_name)
        policy_object.index_server_name = self.index_server_name
        policy_object.data_access_node = self.tcinputs['AccessNode']
        self.file_policy_object = self.commcell.policies.configuration_policies.add_policy(
            policy_object)
        self.log.info(f"CI policy {self.file_policy_name} created")
        self.log.info(
            f"Creating new storage policy {self.storage_policy_name}")
        self.commcell.storage_policies.add(
            storage_policy_name=self.storage_policy_name,
            library=self.library_name,
            media_agent=self.media_agent_name)
        self.log.info(f"Storage policy {self.storage_policy_name} created")
        self.log.info(f"Creating new backupset {self.backupset_name}")
        self.fs_agent_object.backupsets.add(self.backupset_name)
        self.log.info(f"Backupset {self.backupset_name} created")
        self.log.info(
            f"Adding new subclient {self.subclient_name} to backupset {self.backupset_name}")
        self.subclient_obj = self.fs_agent_object.backupsets.get(
            self.backupset_name).subclients.add(
            self.subclient_name, self.storage_policy_name)
        self.log.info(f"Subclient {self.subclient_name} added")
        self.log.info("Adding content to subclient")
        self.subclient_obj.content = self.subclient_content
        self.log.info(f"Content added to subclient {self.subclient_content}")
        self.subclient_obj.enable_content_indexing(
            self.file_policy_object.configuration_policy_id)
        self.log.info(
            f"Subclient marked for Content Indexing with policy {self.file_policy_name}")

    def setup(self):
        """Setup function of this test case"""
        self.index_server_name = self.tcinputs['IndexServer']
        self.file_policy_name = "CI_policy%s" % self.id
        self.storage_policy_name = "StoragePolicy%s" % self.id
        self.subclient_name = "Subclient%s" % self.id
        self.backupset_name = "BackupSet%s" % self.id
        self.media_agent_name = self.tcinputs['MediaAgentName']
        self.library_name = self.tcinputs['Library']
        self.client_name = self.tcinputs['ClientName']
        self.fs_agent_object = self.client.agents.get(
            dynamic_constants.FILE_SYSTEM_IDA)
        self.subclient_content = self.tcinputs['DataPath'].split(',')
        self.cluster_helper = ExtractingClusterHelper(self.commcell)
        self.external_ip = self.cluster_helper.create_extracting_cluster(
            name=dynamic_constants.DEFAULT_CLUSTER_NAME,
            resource_group=dynamic_constants.DEFAULT_RESOURCE_GROUP,
            location=dynamic_constants.DEFAULT_AZURE_LOCATION,
            yaml_file=self.tcinputs['YamlFile'])
        self.cluster_helper.set_cluster_settings_on_cs(
            extracting_ip=self.external_ip,
            index_gateway=self.tcinputs['IndexGatewayClient'],
            user_name=self.tcinputs['IGUserName'],
            password=self.tcinputs['IGPassword'])
        self.cleanup()
        sdk_helper = ActivateSDKHelper(self.commcell)
        # set access node region as different
        sdk_helper.set_client_wrkload_region(
            client_name=self.tcinputs['AccessNode'],
            region_name=dynamic_constants.REGION_EASTUS)
        self.create_subclient()

    def run_backup_and_ci(self):
        """Runs a backup job on subclient and then content indexing on the CI policy"""
        backup_job = self.subclient_obj.backup()
        if not CrawlJobHelper.monitor_job(self.commcell, backup_job):
            raise Exception("Backup job failed to completed successfully")
        self.log.info("Backup job got completed successfully")
        self.log.info("Now running CI job")
        self.ci_job = self.commcell.policies.configuration_policies.run_content_indexing(
            self.file_policy_name)

    def validate_search(self):
        """Validates search are working for file content by querying index server"""
        index_server_obj = self.commcell.index_servers.get(
            self.index_server_name)
        core_name = dynamic_constants.FILE_SYSTEM_MULTINODE_CORE.format(
            IS=self.index_server_name)
        self.result_string = f"{self.result_string}  | Rerunning CI job after bring up local CA and performed Searches"
        for search_word in self.tcinputs['Searches'].split(","):
            self.log.info(f"Trigger search for keyword : {search_word}")
            solr_response = index_server_obj.execute_solr_query(
                core_name=core_name,
                select_dict={
                    dynamic_constants.APPLICATION_ID_PARAM: self.subclient_obj.subclient_id,
                    dynamic_constants.FIELD_KEYWORD_SEARCH: search_word},
                op_params=dynamic_constants.QUERY_ZERO_ROWS)
            solr_doc_count = int(
                solr_response[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM])
            self.log.info(f"Solr Response document count : {solr_doc_count}")
            if not solr_doc_count:
                raise Exception(
                    f"Search didn't yield any result from index server. Please check CI logs. Search Term : {search_word}")
            self.result_string = f"{self.result_string} | Search word : {search_word} - Result doc count : {solr_doc_count}"

    def run(self):
        """Run function of this test case"""
        try:
            # bring down CA services on client
            self.log.info("Stopping Content extractor service on CA client")
            ca_client_obj = self.commcell.clients.get(
                self.tcinputs['AccessNode'])
            ca_client_obj.stop_service(
                service_name=dynamic_constants.CE_SERVICE_NAME)
            self.log.info(
                "Stopped CE service on access node")
            self.log.info("Going to start V2 CI job")
            self.run_backup_and_ci()
            self.validate_local_ca()
            # make sure job is in failed state
            job_manager = JobManager(_job=self.ci_job, commcell=self.commcell)
            job_manager.wait_for_state(
                expected_state=dynamic_constants.JOB_FAILED)

            self.result_string = "Content indexing job reported with 'Connection to localhost CA' error in IndexGateway logs and Job marked with Failed Status"
            self.log.info(self.result_string)

            ca_client_obj.start_service(
                service_name=dynamic_constants.CE_SERVICE_NAME)
            self.log.info(
                "Started CE service on access node")
            time.sleep(120)

            # start new ci job and make sure it reprocessed all files again for
            # this
            self.ci_job = self.commcell.policies.configuration_policies.run_content_indexing(
                self.file_policy_name)
            if not CrawlJobHelper.monitor_job(self.commcell, self.ci_job):
                raise Exception(
                    "Content Indexing job completed with error")
            self.log.info("CI job completed successfully using local CA")
            self.validate_search()

        except Exception as exp:
            self.log.exception(
                'Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("Cleaning up environment")
            self.cleanup(post_cleanup=True)
            self.log.info("Deleting cluster resource group on azure")
            self.cluster_helper.delete_resource_group(
                resource_group=dynamic_constants.DEFAULT_RESOURCE_GROUP)
            self.cluster_helper.remove_cluster_settings_on_cs(
                index_gateway=self.tcinputs['IndexGatewayClient'],
                user_name=self.tcinputs['IGUserName'],
                password=self.tcinputs['IGPassword'])
