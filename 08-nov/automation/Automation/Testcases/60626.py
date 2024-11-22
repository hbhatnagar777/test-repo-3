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
    __init__()                                   --  initialize TestCase class

    setup()                                      --  setup function of this test case

    configure_machine_inputs()                   --  Configure Inputs for machine according to machines configuration

    create_index_server()                        --  Create an Index Server

    delete_index_server()                        --  Delete an Index Server

    run()                                        --  run function of this test case

    tear_down()                                  --  tear down function of this test case

"""
import time
from Application.Exchange.ExchangeMailbox.constants import ARCHIVE_POLICY_DEFAULT
from Application.Exchange.ExchangeMailbox.constants import CLEANUP_POLICY_DEFAULT
from Application.Exchange.ExchangeMailbox.constants import RETENTION_POLICY_DEFAULT
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.AdminConsolePages.Index_Server import IndexServer
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from dynamicindex.index_server_helper import IndexServerHelper
from dynamicindex.utils.constants import USER_MAILBOX_BACKUPSET, FILE_STORAGE_OPTIMIZATION, USER_MAILBOX_SUBCLIENT, \
    LAST_INDEX_SERVER_STATS_SYNC_TIME, CVD_SERVICE_NAME

_CONFIG_DATA = get_config().DynamicIndex.ExchangeClientDetails


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Create a multi-node Index Server, backup some mailboxes, run Load Balancing operation"
        self.tcinputs = {
            "IndexServerNodeNames": None,
            "MediaAgentName": None,
            "MachineUsernames": None,
            "MachinePasswords": None
        }
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.IS_obj = None
        self.index_server_obj = None
        self.index_server_helper = None
        self.index_directory = []
        self.storage_policy = None
        self.archive_policy = None
        self.option_selector_obj = None
        self.retention_policy = None
        self.cleanup_policy = None
        self.exchange_mailbox_client = None
        self.node_machine_obj = None

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                 password=self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.index_server_obj = IndexServer(self.admin_console)
        media_agent_machine_obj = Machine(
            machine_name=self.tcinputs['MediaAgentName'],
            commcell_object=self.commcell
        )
        self.option_selector_obj = OptionsSelector(self.commcell)
        self.configure_machine_inputs(self.tcinputs['IndexServerNodeNames'])
        restore_directory_drive_letter = self.option_selector_obj.get_drive(media_agent_machine_obj)
        self.tcinputs['JobResultDirectory'] = _CONFIG_DATA.JobResultDirectory
        self.tcinputs['ExchangeServerName'] = _CONFIG_DATA.ExchangeServerName
        self.tcinputs['ProxyServers'] = _CONFIG_DATA.ProxyServers
        self.tcinputs['ServiceAccountDetails'] = [_CONFIG_DATA.ServiceAccountDetails._asdict()]
        self.tcinputs['UserMailBox'] = _CONFIG_DATA.UserMailBox
        self.tcinputs['DomainName'] = _CONFIG_DATA.DomainName
        self.tcinputs['DomainUserName'] = _CONFIG_DATA.DomainUserName
        self.tcinputs['DomainUserPassword'] = _CONFIG_DATA.DomainUserPassword
        # Selecting Exchange Client type as Exchange - OnPremise.
        self.tcinputs['EnvironmentType'] = 1
        self.tcinputs['MountPath'] = "%sLibrary_%s" % (restore_directory_drive_letter, self.id)
        self.tcinputs['IndexServer'] = "Index_server_%s" % self.id
        self.tcinputs['SubclientName'] = USER_MAILBOX_SUBCLIENT
        self.tcinputs['BackupsetName'] = USER_MAILBOX_BACKUPSET
        self.tcinputs['StoragePolicyName'] = "storagePolicy%s" % self.id
        self.tcinputs['LibraryName'] = "Library_%s" % self.id
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
        if not self.commcell.storage_policies.has_policy(self.tcinputs[
                'StoragePolicyName']):
            self.log.info("Creating storage policy")
            self.commcell.storage_policies.add(
                self.tcinputs['StoragePolicyName'],
                self.tcinputs['LibraryName'],
                self.tcinputs['MediaAgentName']
            )
            self.log.info("Storage policy added successfully")
        self.log.info('Creating a multi-node Index Server')
        self.create_index_server()
        self.commcell.clients.refresh()
        self.storage_policy = self.commcell.storage_policies.get(
            self.tcinputs['StoragePolicyName']
        )
        self.exchange_mailbox_client = ExchangeMailbox(self)
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

    def configure_machine_inputs(self, node_names):
        """
        Configure Inputs for machine according to machines configuration.

        Args:
             node_names (list):  name of the machine/node.
        """
        for node in node_names:
            self.log.info(f'Forming index directory on the node {node}')
            self.index_directory.append(IndexServerHelper.get_new_index_directory(
                                        self.commcell, node, int(time.time())))

    @test_step
    def create_index_server(self):
        """
            create an index server
        """
        self.navigator.navigate_to_index_servers()
        index_server_exist = self.index_server_obj.is_index_server_exists(self.tcinputs['IndexServer'])
        if index_server_exist:
            self.delete_index_server()
        self.index_server_obj.create_index_server(
            index_server_name=self.tcinputs['IndexServer'],
            index_directory=self.index_directory,
            index_server_node_names=self.tcinputs["IndexServerNodeNames"],
            solutions=[FILE_STORAGE_OPTIMIZATION],
            index_server_roles=['Exchange Index'],
            backup_plan="Server plan")

    @test_step
    def delete_index_server(self):
        """
            delete an Index server and remove index directories
        """
        self.navigator.navigate_to_index_servers()
        self.index_server_obj.delete_index_server(index_server_name=self.tcinputs['IndexServer'])
        index = 0
        for node in self.tcinputs['IndexServerNodeNames']:
            self.node_machine_obj = Machine(node, self.commcell)
            self.node_machine_obj.remove_directory(self.index_directory[index])
            index += 1

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
            self.exchange_mailbox_client.cvoperations.subclient.set_user_assocaition(subclient_content)
            self.exchange_mailbox_client.cvoperations.run_backup()
            self.log.info('Sleeping for 120 seconds')
            time.sleep(120)
            index_server_helper = IndexServerHelper(self.commcell, self.tcinputs['IndexServer'])
            self.index_server_obj.invoke_index_server_stats_sync(
                index_server_nodes=self.tcinputs['IndexServerNodeNames'],
                usernames=self.tcinputs['MachineUsernames'],
                passwords=self.tcinputs['MachinePasswords'])
            output = index_server_helper.get_cores_details_for_load_balancing_validation(
                index_size_limit_in_MB=0,
                index_item_counts=0,
                move_core_limit=25,
                repick_core_num_days=0,
                dst_free_disk_space_percent_limit=0)
            source, destination, cores_to_move, cores_details_before_operation = output
            self.log.info('Starting Load Balancing Operation')
            self.navigator.navigate_to_index_servers()
            self.index_server_obj.balance_load(self.tcinputs['IndexServer'], self.commcell)
            index_server_helper.verify_load_balancing(
                source, destination, cores_to_move, cores_details_before_operation)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.status == constants.PASSED:
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
                self.delete_index_server()
                self.log.info("Index server deleted")
                self.log.info("Deleting the library")
                self.commcell.disk_libraries.delete(self.tcinputs["LibraryName"])
                self.log.info("Library deleted")
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
