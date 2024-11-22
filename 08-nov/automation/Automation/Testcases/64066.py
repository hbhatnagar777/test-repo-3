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

    create_subclient()      --  Creates new backupset and subclient

    create_index_server()   --  creates index server on CS

    run_backup()            --  runs a file system subclient backup

    validate_playback_on_cluster()    --  Validates whether Playback ran on cluster or not

    cleanup()                   --  performs cleanup of test environment

    validate_browse()           --  Validates browse for playedback items

    validate_restore()          --  Validates restore of file from client pointing to index server cluster

"""
import time

from cvpysdk.datacube.constants import IndexServerConstants as index_constants

from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Kubernetes.indexserver.ClusterHelper import ClusterHelper, ClusterApiHelper
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.index_server_helper import IndexServerHelper
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.utils.activateutils import ActivateUtils

_CONFIG_DATA = get_config().DynamicIndex.IndexServerCluster


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
        self.name = "IndexServer K8s - Cluster Environment Setup | Acceptance test case for V2 FS playback to Index server & file browse/restore"
        self.tcinputs = {
            "AccessNode": None,
            "ClientName": None,
            "WebServer": None,
            "WebServerUserName": None,
            "WebServerPassword": None
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
        self.activate_utils = None
        self.cluster_ip = None
        self.controller = None
        self.client_machine_obj = None
        self.is_node_machine_obj = None
        self.file_policy_object = None
        self.index_directory = None
        self.index_server_helper = None
        self.backup_items = 0
        self.collection_docs = 0

    def cleanup(self, pre_cleanup=False):
        """Perform Cleanup Operation"""

        self.activate_utils.activate_cleanup(
            commcell_obj=self.commcell,
            storage_policy_name=self.storage_policy_name,
            ci_policy_name=self.file_policy_name,
            client_name=self.client_name,
            backupset_name=self.backupset_name
        )
        if pre_cleanup:
            if self.controller.check_file_exists(
                    file_path=self.cluster_helper.environment_file):
                self.controller.delete_file(
                    self.cluster_helper.environment_file)
                self.log.info("Cleared cluster setup file")

            if self.controller.check_file_exists(
                    file_path=self.cluster_helper.result_json_file):
                self.controller.delete_file(
                    self.cluster_helper.result_json_file)
                self.log.info("Cleared cluster results file")

            self.log.info(
                f"Checking if Index Server - {self.index_server_name} already exists")
            if self.commcell.index_servers.has(self.index_server_name):
                analytics_dir = self.is_node_machine_obj.get_registry_value(
                    commvault_key=dynamic_constants.ANALYTICS_REG_KEY,
                    value=dynamic_constants.ANALYTICS_DIR_REG_KEY)
                self.log.info(f"The Analytics Directory - {analytics_dir}")
                self.log.info(
                    f"Deleting Index Server - {self.index_server_name}")
                self.commcell.index_servers.delete(self.index_server_name)
                self.log.info("Remove the index dir of IS")
                self.is_node_machine_obj.remove_directory(analytics_dir)

    def create_subclient(self):
        """Creates new backupset and subclient on client"""

        self.log.info(f"Creating new CI policy {self.file_policy_name}")
        policy_object = self.commcell.policies.configuration_policies. \
            get_policy_object(
                dynamic_constants.CI_POLICY_TYPE,
                self.file_policy_name)
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
        self.subclient_obj.content = [self.subclient_content]
        self.log.info(f"Content added to subclient : {self.subclient_content}")
        self.subclient_obj.enable_content_indexing(
            self.file_policy_object.configuration_policy_id)
        self.log.info(
            f"Subclient marked for Content Indexing with policy {self.file_policy_name}")

    def run_backup(self):
        """Runs a backup job on subclient and then content indexing on the CI policy"""
        self.log.info("Going to start backup job on subclient")
        backup_job = self.subclient_obj.backup()
        if not CrawlJobHelper.monitor_job(self.commcell, backup_job):
            raise Exception("Backup job failed to complete")
        # waiting for job to complete
        self.log.info(
            "Backup job got completed successfully. Waiting 5mins for playback to finish")
        time.sleep(300)
        self.backup_items = backup_job.num_of_files_transferred

    def validate_playback_on_cluster(self):
        """validates whether playback happened on index server cluster or not"""
        cluster_ops = ClusterApiHelper(
            commcell_object=self.commcell,
            cluster_ip=self.cluster_ip)
        loaded_cores = cluster_ops.get_loaded_collection_stats(
            dump_in_log=True)
        if not loaded_cores:
            raise Exception(
                "No collection got loaded in cluster. Possibly playback failed")
        _pseudo_client_id = self.commcell.index_servers.get(
            self.index_server_name).index_server_client_id
        collection_name = dynamic_constants.FILE_SYSTEM_MULTINODE_CORE.format(
            IS=f"{self.index_server_name}{_pseudo_client_id}")
        if collection_name not in loaded_cores:
            raise Exception(
                f"Loaded collection stats doesn't contain expected collection name - {collection_name}")
        self.log.info("Playback validation finished")
        solr_resp = cluster_ops.search_collection(
            name=collection_name, select_dict=dynamic_constants.QUERY_FILE_CRITERIA)
        self.collection_docs = solr_resp[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM]
        self.log.info(
            f"Total files played back in collection is - {self.collection_docs}")
        self.result_string = f"{self.result_string} | Played back collection name : {collection_name} | Playedback collection items count : {self.collection_docs}"

    def validate_browse(self):
        """Validates browse on index server cluster"""
        self.log.info("Going to do browse at backupset level")
        backupset_obj = self.fs_agent_object.backupsets.get(
            self.backupset_name)
        playback_items = backupset_obj.backed_up_files_count()
        self.log.info(f"Browse file count - {playback_items}")
        self.log.info(f"Backup Source file count - {self.backup_items}")
        if playback_items != self.backup_items:
            raise Exception(
                f"Backed up file count[{self.backup_items}] & cluster played back items count[{playback_items}] mismatched")
        if playback_items != self.collection_docs:
            raise Exception(
                f"Items in browse & collection is not matching. Browse items :{playback_items} collection items: {self.collection_docs}")
        self.log.info(
            f"Backed up file count & cluster played back count matched - {playback_items}")
        self.result_string = f"{self.result_string} | Total Played back items : {playback_items}"

    def validate_restore(self):
        """Validates restore of file from client pointing to index server cluster"""
        self.log.info("Going to do restore out of place on subclient")
        destination_path = f"{self.subclient_content}_{int(time.time())}"
        job_obj = self.subclient_obj.restore_out_of_place(
            client=self.client_name, destination_path=destination_path, paths=[
                self.subclient_content])
        self.log.info(f"Monitoring Restore job - {job_obj.job_id}")
        job_obj.wait_for_completion(timeout=60)
        self.log.info(
            "Restore job completed. Validate checksum between restored data & source data")
        _result, _diffstr = self.client_machine_obj.compare_checksum(
            source_path=self.subclient_content, destination_path=destination_path)
        if not _result:
            raise Exception(
                f"Checksum comparison between source & destination failed - {_diffstr}")
        self.log.info(f"Restore validation finished with status - {_result}")
        self.log.info(f"Deleting the restored folder - {destination_path}")
        self.client_machine_obj.remove_directory(
            directory_name=destination_path)

    def create_cluster(self):
        """creates index server cluster on kubernetes"""
        self.cluster_ip = self.cluster_helper.create_cluster(
            yaml_file=_CONFIG_DATA.CommonInputs.YamlFile)
        self.log.info(
            f"Index server Kubernetes cluster Ip - {self.cluster_ip}")
        self.cluster_helper.set_cluster_ip_in_cs(
            index_server=self.index_server_name,
            cluster_ip=self.cluster_ip,
            webserver=self.tcinputs['WebServer'],
            user_name=self.tcinputs['WebServerUserName'],
            password=self.tcinputs['WebServerPassword'])
        self.result_string = f"Index Server Kubernetes Cluster IP :- {self.cluster_ip}"
        images = self.cluster_helper.extract_image_info(
            yaml_file=_CONFIG_DATA.CommonInputs.YamlFile)
        self.result_string = f"{self.result_string} | Image version Info : {images}"

    def create_index_server(self):
        """Creates index server on cs"""
        self.index_directory = IndexServerHelper.get_new_index_directory(
            commcell_object=self.commcell,
            index_node_name=_CONFIG_DATA.CommonInputs.IndexServerNode,
            custom_string=str(
                int(
                    time.time())))
        self.log.info(f"Index server Dir - {self.index_directory}")
        self.is_node_machine_obj.create_directory(
            self.index_directory, force_create=True)
        self.log.info(f"Creating index server - {self.index_server_name}")
        self.commcell.index_servers.create(
            index_server_name=self.index_server_name,
            index_server_node_names=[
                _CONFIG_DATA.CommonInputs.IndexServerNode],
            index_directory=self.index_directory,
            index_server_roles=[
                index_constants.ROLE_DATA_ANALYTICS,
                index_constants.ROLE_FILE_SYSTEM_INDEX])
        time.sleep(120)
        self.log.info("Index server created successfully")

    def setup(self):
        """Setup function of this test case"""
        self.controller = Machine()
        self.index_server_name = "IndexServerCluster%s" % self.id
        self.file_policy_name = "CI_policy%s" % self.id
        self.storage_policy_name = "StoragePolicy%s" % self.id
        self.subclient_name = "Subclient%s" % self.id
        self.backupset_name = "BackupSet%s" % self.id
        self.media_agent_name = _CONFIG_DATA.CommonInputs.MediaAgentName
        self.library_name = _CONFIG_DATA.CommonInputs.Library
        self.fs_agent_object = self.client.agents.get(
            dynamic_constants.FILE_SYSTEM_IDA)
        self.subclient_content = _CONFIG_DATA.CommonInputs.DataPath
        self.activate_utils = ActivateUtils()
        self.cluster_helper = ClusterHelper(self.commcell)
        self.client_name = self.tcinputs['ClientName']
        self.client_machine_obj = Machine(
            commcell_object=self.commcell,
            machine_name=self.client_name)
        self.is_node_machine_obj = Machine(
            commcell_object=self.commcell,
            machine_name=_CONFIG_DATA.CommonInputs.IndexServerNode)
        self.cleanup(pre_cleanup=True)

    def run(self):
        """Run function of this test case"""
        try:
            self.create_index_server()
            self.create_cluster()
            self.create_subclient()
            self.run_backup()
            self.validate_playback_on_cluster()
            self.validate_browse()
            self.validate_restore()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.cleanup()
            self.controller.create_file(
                file_path=self.cluster_helper.environment_file,
                content=f"{self.cluster_ip}_{self.index_server_name}")
        self.cluster_helper.update_test_status_json(
            test_id=self.id, status=self.status)
