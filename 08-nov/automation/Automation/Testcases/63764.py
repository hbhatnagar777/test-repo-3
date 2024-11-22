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

    validate_access_denied()    --  Validates access denied error on index gateway log

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
        self.name = "CE Kubernetes Cluster [Negative] - Validate Access denied scenario via V2 FS content indexing by corrupting cluster key url in credential manager"
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
            "AccessNode": None
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

    def validate_access_denied(self):
        """Validates access denied error on index gateway log"""
        pattern = f"Response \\[Access Denied] for url \\[http://{self.external_ip}"
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
                    f"No Access denied logs for this pattern {pattern} found in index gateway.log for past 30mins")
            time.sleep(30)
        self.log.info(
            "Access denied Error present in IndexGateway.log. No of entries - {}".format(len(log_lines.split('\r\n'))))

    def cleanup(self):
        """Perform Cleanup Operation"""
        activate_utils = ActivateUtils()
        activate_utils.activate_cleanup(
            commcell_obj=self.commcell,
            storage_policy_name=self.storage_policy_name,
            ci_policy_name=self.file_policy_name,
            client_name=self.client_name,
            backupset_name=self.backupset_name
        )

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
            password=self.tcinputs['IGPassword'],
            corrupt_cluster_key=True)
        self.cleanup()
        sdk_helper = ActivateSDKHelper(self.commcell)
        sdk_helper.set_client_wrkload_region(
            client_name=self.tcinputs['AccessNode'],
            region_name=dynamic_constants.REGION_EASTUS2)
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

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Going to start V2 CI job")
            self.run_backup_and_ci()
            self.validate_access_denied()
            # make sure job is in failed state
            job_manager = JobManager(_job=self.ci_job, commcell=self.commcell)
            job_manager.wait_for_state(
                expected_state=dynamic_constants.JOB_FAILED)

            self.result_string = "Content indexing job reported with 'Access Denied' error in IndexGateway logs and Job marked with Failed Status"
            self.log.info(self.result_string)

        except Exception as exp:
            self.log.exception(
                'Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("Cleaning up environment")
            self.cleanup()
            self.log.info("Deleting cluster resource group on azure")
            self.cluster_helper.delete_resource_group(
                resource_group=dynamic_constants.DEFAULT_RESOURCE_GROUP)
            self.cluster_helper.remove_cluster_settings_on_cs(
                index_gateway=self.tcinputs['IndexGatewayClient'],
                user_name=self.tcinputs['IGUserName'],
                password=self.tcinputs['IGPassword'])
