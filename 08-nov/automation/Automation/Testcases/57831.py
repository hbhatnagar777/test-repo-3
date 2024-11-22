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

import json
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.constants import RETENTION_POLICY_DEFAULT
from Application.Exchange.ExchangeMailbox.constants import ARCHIVE_POLICY_DEFAULT
from Application.Exchange.ExchangeMailbox.constants import CLEANUP_POLICY_DEFAULT


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
        self.name = "Validation of modify operation on HAC cluster for cloud index server with exchange role"
        self.tcinputs = {
            "IndexServerNodeNames": [],
            "JobResultDirectory": None,
            "ProxyServers": None,
            "MediaAgentName": None,
            "ServiceAccountDetails": None,
            "ExchangeServerName": None,
            "UserMailBox": None
        }
        self.archive_policy = None
        self.retention_policy = None
        self.cleanup_policy = None
        self.exchange_mailbox_client = None
        self.solr_helper = None
        self.crawl_job_helper = None
        self.total_count = None
        self.hac_cluster_name = None
        self.index_pool_name = None
        self.node_machine_obj_list = []
        self.media_agent_machine_obj = None
        self.index_server_name = None
        self.index_location = None
        self.hac_cluster_obj = None
        self.index_server_roles = ['Exchange Index']

    def setup(self):
        """Setup function of this test case"""
        self.media_agent_machine_obj = Machine(self.tcinputs['MediaAgentName'],
                                               self.commcell)
        for node_name in self.tcinputs['IndexServerNodeNames']:
            self.node_machine_obj_list.append(Machine(node_name, self.commcell))
        option_selector = OptionsSelector(self.commcell)
        drive_letter_ma = option_selector.get_drive(self.media_agent_machine_obj)
        drive_letter_node = option_selector.get_drive(self.node_machine_obj_list[0])
        self.tcinputs['IndexServer'] = "IndexServer%s" % self.id
        self.tcinputs['SubclientName'] = "usermailbox"
        self.tcinputs['BackupsetName'] = "User Mailbox"
        self.tcinputs['StoragePolicyName'] = "storagePolicy%s" % self.id
        self.tcinputs['LibraryName'] = "Library%s" % self.id
        self.tcinputs['MountPath'] = "%sLibrary%s" % (drive_letter_ma, self.id)
        self.hac_cluster_name = "HAC%s" % self.id
        self.index_pool_name = "Pool%s" % self.id
        self.tcinputs['IndexLocation'] = '%sindexDirectory%s' % (drive_letter_node, self.id)
        self.tcinputs['DiskRestorePath'] = '%srestoreMail%s' % (drive_letter_ma, self.id)
        self.tcinputs['DiskRestoreClient'] = self.tcinputs['MediaAgentName']
        if not self.commcell.hac_clusters.has_cluster(self.hac_cluster_name):
            self.log.info("Creating HAC cluster with nodes %s" % ",".join(self.tcinputs['IndexServerNodeNames']))
            self.commcell.hac_clusters.add(self.hac_cluster_name, self.tcinputs['IndexServerNodeNames'])
            self.log.info("HAC cluster created")
        self.hac_cluster_obj = self.commcell.hac_clusters.get(self.hac_cluster_name)
        if not self.commcell.index_pools.has_pool(self.index_pool_name):
            self.log.info("Creating index pool with nodes %s" % ",".join(self.tcinputs['IndexServerNodeNames']))
            self.commcell.index_pools.add(self.index_pool_name,
                                          self.tcinputs['IndexServerNodeNames'],
                                          self.hac_cluster_name)
            self.log.info("Index pool created")
        if not self.commcell.index_servers.has(self.tcinputs['IndexServer']):
            for machine_obj in self.node_machine_obj_list:
                machine_obj.remove_directory(self.tcinputs['IndexLocation'], 0)
            self.log.info("Creating index server")
            self.commcell.index_servers.create(
                self.tcinputs['IndexServer'],
                self.tcinputs['IndexServerNodeNames'],
                self.tcinputs['IndexLocation'],
                self.index_server_roles,
                index_pool_name=self.index_pool_name,
                is_cloud=True
            )
            self.log.info("Index server created")
            self.commcell.clients.refresh()
        if not self.commcell.disk_libraries.has_library(self.tcinputs['LibraryName']):
            self.log.info("Creating %s on mount path %s" % (self.tcinputs['LibraryName'],
                                                            self.tcinputs['MountPath']))
            self.commcell.disk_libraries.add(self.tcinputs['LibraryName'],
                                             self.tcinputs['MediaAgentName'],
                                             self.tcinputs['MountPath'])
            self.log.info("Library created")
        archive_policy_default = ARCHIVE_POLICY_DEFAULT % self.id
        retention_policy_default = RETENTION_POLICY_DEFAULT % self.id
        cleanup_policy_default = CLEANUP_POLICY_DEFAULT % self.id
        if not self.commcell.storage_policies.has_policy(self.tcinputs['StoragePolicyName']):
            self.log.info("Creating storage policy")
            self.commcell.storage_policies.add(
                self.tcinputs['StoragePolicyName'],
                self.tcinputs['LibraryName'],
                self.tcinputs['MediaAgentName']
            )
            self.log.info("Storage policy added successfully")
        self.exchange_mailbox_client = ExchangeMailbox(self)
        self.crawl_job_helper = CrawlJobHelper(self)
        self.log.info('Creating a exchange client')
        self._client = self.exchange_mailbox_client.cvoperations.add_exchange_client()
        self.log.info('Exchange client created with id: %s',
                      self._client.client_id)
        self.log.info("Creating an instance of subclient")
        self._subclient = self.exchange_mailbox_client.cvoperations.subclient
        self.log.info("Subclient instance created.")
        self.log.info("Creating policies.")
        self.cleanup_policy = self.exchange_mailbox_client.cvoperations.add_exchange_policy(
            self.exchange_mailbox_client.cvoperations.get_policy_object(
                cleanup_policy_default, "Cleanup"
            )
        )
        self.archive_policy = self.exchange_mailbox_client.cvoperations.add_exchange_policy(
            self.exchange_mailbox_client.cvoperations.get_policy_object(
                archive_policy_default, "Archive"
            )
        )
        self.retention_policy = self.exchange_mailbox_client.cvoperations.add_exchange_policy(
            self.exchange_mailbox_client.cvoperations.get_policy_object(
                retention_policy_default, "Retention"
            )
        )
        self.log.info("Policy generation completed.")

    def run(self):
        """Run function of this test case"""
        try:
            subclient_content = {
                "mailboxNames": self.tcinputs['UserMailBox'],
                "archive_policy": self.archive_policy,
                "retention_policy": self.retention_policy,
                "cleanup_policy": self.cleanup_policy
            }
            self.log.info("Now setting up the user email.")
            self.exchange_mailbox_client.cvoperations.subclient. \
                set_user_assocaition(subclient_content)
            self.log.info("User email association done")
            self.log.info("Now changing the zoo keeper data port for node: %s" %
                          self.tcinputs['IndexServerNodeNames'][0])
            hac_node_info = self.hac_cluster_obj.node_info(self.tcinputs['IndexServerNodeNames'][0])
            port_info = {}
            for node_info in hac_node_info['nodeMetaInfos']:
                port_info[node_info['name']] = node_info['value']
            listener_port = int(port_info["ZKDATAPORT"])
            self.hac_cluster_obj.modify_node(self.tcinputs['IndexServerNodeNames'][0], data_port=str(listener_port + 1))
            self.log.info("Zoo keeper port modified successfully")
            self.exchange_mailbox_client.cvoperations.run_backup()
            self.media_agent_machine_obj.remove_directory(self.tcinputs['DiskRestorePath'], 0)
            self.log.info("Now starting the restore process")
            job = self.exchange_mailbox_client.cvoperations.subclient. \
                disk_restore(paths=[r"\MB"],
                             destination_client=self.tcinputs['DiskRestoreClient'],
                             destination_path=self.tcinputs['DiskRestorePath'],
                             overwrite=True,
                             journal_report=False)
            self.exchange_mailbox_client.cvoperations.check_job_status(job)
            restore_mails_count = self.crawl_job_helper.get_docs_count(
                folder_path=self.tcinputs['DiskRestorePath'],
                machine_name=self.tcinputs['DiskRestoreClient'],
                include_folders=False
            )
            self.solr_helper = SolrHelper(self.exchange_mailbox_client)
            select_dict = {
                "DocumentType": 2,
                "ApplicationId": self._subclient.subclient_id
            }
            solr_resp = self.solr_helper.create_url_and_get_response(
                select_dict=select_dict
            )
            self.total_count = self.solr_helper.get_count_from_json(solr_resp.content)
            self.log.info("Expected restore mails count : %s", self.total_count)
            if not restore_mails_count == self.total_count:
                self.log.error("Restored files count doesn't match with expected value")
                self.log.error("Expected value: %s", self.total_count)
                self.log.error("Actual value: %s", restore_mails_count)
                raise Exception("Restored mails count doesn't match with expected value")
            self.log.info("All mails Restored successfully")
            files_list = self.media_agent_machine_obj.get_files_in_path(self.tcinputs['DiskRestorePath'])
            file_name_map = {}
            for file in files_list:
                file_name_map["_".join((file.split('\\')[-1]).split('_')[:-3])] = file
            attr_params = {'Size', 'Subject'}
            op_params = {
                "rows": restore_mails_count
            }
            solr_resp = json.loads(self.solr_helper.create_url_and_get_response(
                select_dict=select_dict,
                attr_list=attr_params,
                op_params=op_params
            ).content)
            for doc in solr_resp['response']['docs']:
                illegal_entries = '\t\"*/:<>?\\|'
                for illegal_entry in illegal_entries:
                    doc['Subject'] = str(doc['Subject']).replace(illegal_entry, '_')
                disk_size = self.media_agent_machine_obj.get_file_size(file_name_map[doc['Subject']], True)
                if int(disk_size) < int(doc['Size']):
                    self.log.error("Invalid file size found for %s.msg" % doc['Subject'])
                    self.log.error("Expected file size >=%s" % doc['Size'])
                    raise Exception("Invalid file size found")
            self.log.info("No invalid file size found for any email")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.log.info("Deleting exchange pseudo client")
            self.commcell.clients.delete(self.exchange_mailbox_client.cvoperations.client.name)
            self.log.info("Exchange client deleted")
            self.log.info("Deleting exchange configuration policies")
            self.commcell.policies.configuration_policies.delete(
                ARCHIVE_POLICY_DEFAULT % self.id
            )
            self.commcell.policies.configuration_policies.delete(
                CLEANUP_POLICY_DEFAULT % self.id
            )
            self.commcell.policies.configuration_policies.delete(
                RETENTION_POLICY_DEFAULT % self.id
            )
            self.log.info("Exchange configuration policies deleted")
            self.log.info("Deleting storage policy")
            self.commcell.storage_policies.delete(self.tcinputs['StoragePolicyName'])
            self.log.info("Storage policy deleted")
            self.log.info("Deleting the index server")
            self.commcell.index_servers.delete(self.tcinputs['IndexServer'])
            self.log.info("Index server deleted")
            self.log.info("Deleting the index pool")
            self.commcell.index_pools.delete(self.index_pool_name)
            self.log.info("Index pool deleted")
            self.log.info("Deleting the HAC cluster")
            self.commcell.hac_clusters.delete(self.hac_cluster_name)
            self.log.info("HAC cluster deleted")
            self.log.info("Removing index directory")
            for machine_obj in self.node_machine_obj_list:
                machine_obj.remove_directory(self.tcinputs['IndexLocation'], 0)
            self.log.info("Index directory removed")
            self.log.info("Removing restored mails directory")
            self.media_agent_machine_obj.remove_directory(self.tcinputs['DiskRestorePath'], 0)
            self.log.info("Restored mails directory removed")
            self.log.info("Deleting the library")
            self.commcell.disk_libraries.delete(self.tcinputs["LibraryName"])
            self.log.info("Library deleted")
