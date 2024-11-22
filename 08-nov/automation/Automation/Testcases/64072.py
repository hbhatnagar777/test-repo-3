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

    tear_down()     --  tear down function of this test

    create_exchange_client()    --  creates exchange client on CS

    validate_playback_on_cluster()    --  Validates whether Playback ran on cluster or not

"""

from Application.Exchange.ExchangeMailbox.constants import ARCHIVE_POLICY_DEFAULT, RETENTION_POLICY_DEFAULT, \
    CLEANUP_POLICY_DEFAULT
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Kubernetes.indexserver.ClusterHelper import ClusterHelper, ClusterApiHelper
from dynamicindex.Datacube.exchange_client_helper import ExchangeClientHelper
from dynamicindex.utils import constants as dynamic_constants

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
        self.name = "IndexServer K8s - Acceptance test case for Exchange Mailbox playback & Restore"
        self.tcinputs = {

        }
        self.cluster_helper = None
        self.cluster_ip = None
        self.index_server_name = None
        self.storage_policy = None
        self.archive_policy = None
        self.retention_policy = None
        self.cleanup_policy = None
        self.exchange_client = None
        self.media_agent_machine_obj = None
        self.exchange_helper = None
        self.restore_path = None
        self.collection_docs = 0

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
        mailbox_guid = self.exchange_client.cvoperations.backupset.guid
        collection_name = dynamic_constants.USER_MAILBOX_MULTINODE_CORE.format(
            IS=mailbox_guid)
        self.log.info(f"Collection name formed : {collection_name}")
        if collection_name not in loaded_cores:
            raise Exception(
                f"Loaded collection stats doesn't contain expected collection name - {collection_name}")
        self.log.info("Playback validation finished")
        solr_resp = cluster_ops.search_collection(
            name=collection_name, select_dict={
                dynamic_constants.DOCUMENT_TYPE_PARAM: 2})
        self.collection_docs = solr_resp[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM]
        self.log.info(
            f"Total files played back in collection is - {self.collection_docs}")
        self.result_string = f"Cluster IP : {self.cluster_ip} | Played back collection name : {collection_name} | Played back collection items count : {self.collection_docs}"

    def create_exchange_client(self):
        """Creates exchange client on CS"""
        if not self.commcell.storage_policies.has_policy(self.tcinputs[
                'StoragePolicyName']):
            self.log.info("Creating storage policy")
            self.commcell.storage_policies.add(
                self.tcinputs['StoragePolicyName'],
                _CONFIG_DATA.CommonInputs.Library,
                _CONFIG_DATA.CommonInputs.MediaAgentName
            )
            self.log.info("Storage policy added successfully")

        self.storage_policy = self.commcell.storage_policies.get(
            self.tcinputs['StoragePolicyName']
        )
        self.log.info('Creating a exchange client')
        self.exchange_client = self.exchange_helper.create_exchange_mailbox_client(
            tc_object=self,
            storage_policy=self.tcinputs['StoragePolicyName'],
            index_server_name=self.index_server_name)
        self.log.info('Exchange client created')
        self.exchange_helper.create_exchange_configuration_policies(self.id)

    def setup(self):
        """Setup function of this test case"""
        self.cluster_helper = ClusterHelper(self.commcell)
        self.cluster_ip, self.index_server_name = self.cluster_helper.get_cluster_ip_from_setup()
        self.log.info(
            f"Index server cluster ip : {self.cluster_ip} & Index server is : {self.index_server_name}")
        self.media_agent_machine_obj = Machine(
            machine_name=_CONFIG_DATA.CommonInputs.MediaAgentName,
            commcell_object=self.commcell
        )
        option_selector_obj = OptionsSelector(self.commcell)
        restore_directory_drive_letter = option_selector_obj.get_drive(
            self.media_agent_machine_obj)
        self.archive_policy = ARCHIVE_POLICY_DEFAULT % self.id
        self.retention_policy = RETENTION_POLICY_DEFAULT % self.id
        self.cleanup_policy = CLEANUP_POLICY_DEFAULT % self.id
        self.exchange_helper = ExchangeClientHelper(self.commcell)
        self.restore_path = "%srestore_mail_%s" % (
            restore_directory_drive_letter, self.id)
        self.tcinputs['StoragePolicyName'] = "storagePolicy%s" % self.id

    def run(self):
        """Run function of this test case"""
        try:
            self.create_exchange_client()
            sub_client_content = {
                "mailboxNames": _CONFIG_DATA.CommonInputs.UserMailbox,
                "archive_policy": self.archive_policy,
                "retention_policy": self.retention_policy,
                "cleanup_policy": self.cleanup_policy
            }
            self.log.info("Now setting up the user email.")
            self.exchange_client.cvoperations.subclient.set_user_assocaition(
                sub_client_content)
            self.exchange_client.cvoperations.run_backup()

            # validate collection on cluster
            self.validate_playback_on_cluster()

            self.exchange_helper.restore_exchange_mailbox_client(
                exchange_mailbox_client=self.exchange_client,
                restore_machine=_CONFIG_DATA.CommonInputs.MediaAgentName,
                restore_path=self.restore_path)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("Deleting exchange pseudo client")
            self.commcell.clients.delete(
                self.exchange_client.cvoperations.client.name)
            self.log.info("Exchange client deleted")
            self.log.info("Deleting exchange configuration policies")
            self.commcell.policies.configuration_policies.delete(
                self.archive_policy)
            self.commcell.policies.configuration_policies.delete(
                self.cleanup_policy)
            self.commcell.policies.configuration_policies.delete(
                self.retention_policy)
            self.log.info("Exchange configuration policies deleted")
            self.log.info("Deleting storage policy")
            self.commcell.storage_policies.delete(
                self.tcinputs['StoragePolicyName'])
            self.log.info("Storage policy deleted")
        self.cluster_helper.update_test_status_json(
            test_id=self.id, status=self.status)
