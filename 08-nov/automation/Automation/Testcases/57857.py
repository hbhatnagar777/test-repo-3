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
from AutomationUtils.constants import FAILED
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.constants import RETENTION_POLICY_DEFAULT
from Application.Exchange.ExchangeMailbox.constants import ARCHIVE_POLICY_DEFAULT
from Application.Exchange.ExchangeMailbox.constants import CLEANUP_POLICY_DEFAULT
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Cloud index server: DC plan creation"
        self.tcinputs = {
            "IndexServerNodeName": None,
            "ContentAnalyserCloudName": None,
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
        self.index_server_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.plan_name = None
        self.index_directory = None
        self.index_server_node_machine = None
        self.media_agent_machine = None
        self.commcell_password = None
        self.hac_cluster_name = None
        self.index_pool_name = None

    def setup(self):
        """Setup function of this test case"""
        self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
        self.plan_name = "TestPlan_%s" % self.id
        self.index_server_name = "%s_AnalyticsServer" % self.tcinputs['IndexServerNodeName']
        self.hac_cluster_name = "%s_HACCluster" % self.tcinputs['IndexServerNodeName']
        self.index_pool_name = "%s_IndexServerPool" % self.tcinputs['IndexServerNodeName']
        self.index_server_node_machine = Machine(self.tcinputs['IndexServerNodeName'], self.commcell)
        self.media_agent_machine = Machine(self.tcinputs['MediaAgentName'], self.commcell)
        drive_letter = OptionsSelector.get_drive(self.index_server_node_machine)
        self.index_directory = "%sIndexDirectory_%s" % (drive_letter, self.id)
        self.tcinputs['IndexServer'] = self.index_server_name
        self.tcinputs['SubclientName'] = "usermailbox"
        self.tcinputs['BackupsetName'] = "User Mailbox"
        self.tcinputs['StoragePolicyName'] = "storagePolicy%s" % self.id
        self.tcinputs['LibraryName'] = "Library%s" % self.id
        drive_letter = OptionsSelector.get_drive(self.media_agent_machine)
        self.tcinputs['MountPath'] = "%sLibrary%s" % (drive_letter, self.id)
        self.tcinputs['DiskRestorePath'] = '%srestoreMail%s' % (drive_letter, self.id)
        self.tcinputs['DiskRestoreClient'] = self.tcinputs['MediaAgentName']
        self.cleanup()

    def init_tc(self):
        """ Initial configuration for the test case. """
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                          username=self.commcell.commcell_username,
                                          password=self.commcell_password)
        self.admin_console.login(username=self.commcell.commcell_username,
                                 password=self.commcell_password)
        self.log.info('Logged in through web automation')
        self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)

    def cleanup(self):
        if self.commcell.plans.has_plan(self.plan_name):
            self.log.info("Deleting DC plan")
            self.commcell.plans.delete(self.plan_name)
        if self.commcell.clients.has_client("ExchangeClient_%s" % self.id):
            self.log.info("Deleting exchange client")
            self.commcell.clients.delete("ExchangeClient_%s" % self.id)
        if self.commcell.index_servers.has(self.index_server_name):
            self.log.info("Deleting index server")
            self.commcell.index_servers.delete(self.index_server_name)
        if self.commcell.index_pools.has_pool(self.index_pool_name):
            self.log.info("Deleting index pool")
            self.commcell.index_pools.delete(self.index_pool_name)
        if self.commcell.hac_clusters.has_cluster(self.hac_cluster_name):
            self.log.info("Deleting HAC cluster")
            self.commcell.hac_clusters.delete(self.hac_cluster_name)
        if self.commcell.storage_policies.has_policy(self.tcinputs['StoragePolicyName']):
            self.log.info("Deleting Storage policy")
            self.commcell.storage_policies.delete(self.tcinputs['StoragePolicyName'])
        if self.commcell.disk_libraries.has_library(self.tcinputs['LibraryName']):
            self.log.info("Deleting Library")
            self.commcell.disk_libraries.delete(self.tcinputs['LibraryName'])
        self.media_agent_machine.remove_directory(self.tcinputs['MountPath'], 0)
        self.index_server_node_machine.remove_directory(self.index_directory, 0)

    @test_step
    def create_plan(self):
        """creates a data classification plan"""
        self.admin_console.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            self.plan_name, self.index_server_name,
            self.tcinputs['ContentAnalyserCloudName'], ["Email"],
            target_app="casemanager",
            create_index_server=True, node_name=self.tcinputs['IndexServerNodeName'],
            index_directory=self.index_directory)

    def run(self):
        """Run function of this test case"""
        try:
            self.init_tc()
            self.create_plan()
            self.commcell.clients.refresh()
            self.commcell.index_servers.refresh()
            self.commcell.plans.refresh()
            self.commcell.hac_clusters.refresh()
            self.commcell.index_pools.refresh()
            self.log.info("Checking if index server is created or not")
            if not self.commcell.index_servers.has(self.index_server_name):
                self.log.error("Index server not created")
                raise Exception("Index server not created")
            self.log.info("Cloud index server is created: %s" % self.index_server_name)
            self.log.info("Checking if DC plan is created or not")
            if not self.commcell.plans.has_plan(self.plan_name):
                self.log.error("DC not created")
                raise Exception("DC not created")
            self.log.info("DC is created: %s" % self.plan_name)
            self.log.info("Creating %s on mount path %s" % (self.tcinputs['LibraryName'],
                                                            self.tcinputs['MountPath']))
            self.commcell.disk_libraries.add(self.tcinputs['LibraryName'],
                                             self.tcinputs['MediaAgentName'],
                                             self.tcinputs['MountPath'])
            self.log.info("Library created")
            archive_policy_default = ARCHIVE_POLICY_DEFAULT % self.id
            retention_policy_default = RETENTION_POLICY_DEFAULT % self.id
            cleanup_policy_default = CLEANUP_POLICY_DEFAULT % self.id
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
            self.exchange_mailbox_client.cvoperations.run_backup()
            self.media_agent_machine.remove_directory(self.tcinputs['DiskRestorePath'], 0)
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
            total_count = self.solr_helper.get_count_from_json(solr_resp.content)
            self.log.info("Expected restore mails count : %s", total_count)
            if not restore_mails_count == total_count:
                self.log.error("Restored files count doesn't match with expected value")
                self.log.error("Expected value: %s", total_count)
                self.log.error("Actual value: %s", restore_mails_count)
                raise Exception("Restored mails count doesn't match with expected value")
            self.log.info("All mails Restored successfully")
            files_list = self.media_agent_machine.get_files_in_path(self.tcinputs['DiskRestorePath'])
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
                disk_size = self.media_agent_machine.get_file_size(file_name_map[doc['Subject']], True)
                if int(disk_size) < int(doc['Size']):
                    self.log.error("Invalid file size found for %s.msg" % doc['Subject'])
                    self.log.error("Expected file size >=%s" % doc['Size'])
                    raise Exception("Invalid file size found")
            self.log.info("No invalid file size found for any email")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != FAILED:
            self.cleanup()
