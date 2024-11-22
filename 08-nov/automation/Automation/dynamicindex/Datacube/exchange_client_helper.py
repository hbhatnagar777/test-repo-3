# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for exchange usermailbox client operations like
    backup/restore

    ExchangeClientHelper:

        __init__()                                  --  initialize the ExchangeClientHelper class

        create_exchange_mailbox_client()            --  creates a new exchange mailbox client

        create_exchange_policy()                    --  creates a exchange configuration policy

        create_exchange_configuration_policies()    --  creates all 3 exchange policies

        restore_exchange_mailbox_client()           --  perform a disk restore job on the exchange
                                                        mailbox client

        add_user_mailbox()                          --  Adds an usermailbox to the exchange subclient

        clear_exchange_environment()                --  Removes exchange client and configurations policies

"""
import datetime
import json
from AutomationUtils.config import get_config
from AutomationUtils import logger
from AutomationUtils.machine import Machine
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper
from Application.Exchange.ExchangeMailbox.constants import \
    CLEANUP_POLICY_DEFAULT, RETENTION_POLICY_DEFAULT, ARCHIVE_POLICY_DEFAULT, ARCHIVE, RETENTION, CLEANUP

EXCHANGE_CONFIG_DATA = get_config().DynamicIndex.ExchangeClientDetails


class ExchangeClientHelper():
    """Helper class for Exchange client operations like create/backup/restore"""

    def __init__(self, commcell_object=None, exchange_client=None, exchange_policies=None):
        """Initialize the class with commcell object"""
        self.log = logger.get_log()
        self.commcell = commcell_object
        self.exchange_client = exchange_client
        self.exchange_policies = exchange_policies
        if exchange_client:
            self.commcell = exchange_client.commcell
            self.tc_object = exchange_client.tc_object

    def create_exchange_mailbox_client(self, tc_object, storage_policy=None, index_server_name=None,
                                       add_from_config=True):
        """Creates a new exchange pseudoclient to the commcell

        Args:
            tc_object           (object)    --  testcase object

            storage_policy      (str)       --  storage policy name for exchange
                                                pseudo client

            index_server_name   (str)       --  index server name where the exchange
                                                pseudoclient will be pointing

            add_from_config     (bool)      --  True if exchange server details to be taken from config
                                                or False if exchange server details are already added to the tc_object

        Returns:
            object      (ExchangeMailbox)   --  Exchange mailbox client instance

        """
        if add_from_config:
            tc_object.tcinputs['ExchangeServerName'] = EXCHANGE_CONFIG_DATA.ExchangeServerName
            tc_object.tcinputs['UserMailBox'] = EXCHANGE_CONFIG_DATA.UserMailBox
            service_account = {
                "ServiceType": EXCHANGE_CONFIG_DATA.ServiceAccountDetails.ServiceType,
                "Username": EXCHANGE_CONFIG_DATA.ServiceAccountDetails.Username,
                "Password": EXCHANGE_CONFIG_DATA.ServiceAccountDetails.Password
            }
            tc_object.tcinputs['ServiceAccountDetails'] = [service_account]
            tc_object.tcinputs['ProxyServers'] = EXCHANGE_CONFIG_DATA.ProxyServers
            tc_object.tcinputs['JobResultDirectory'] = EXCHANGE_CONFIG_DATA.JobResultDirectory
            tc_object.tcinputs['DomainName'] = EXCHANGE_CONFIG_DATA.DomainName
            tc_object.tcinputs['DomainUserName'] = EXCHANGE_CONFIG_DATA.DomainUserName
            tc_object.tcinputs['DomainUserPassword'] = EXCHANGE_CONFIG_DATA.DomainUserPassword
            tc_object.tcinputs['ServerPlanName'] = EXCHANGE_CONFIG_DATA.StoragePolicyName
            tc_object.tcinputs['ExchangePlan'] = EXCHANGE_CONFIG_DATA.ExchangePlan
        tc_object.tcinputs['EnvironmentType'] = 1
        tc_object.tcinputs['IndexServer'] = index_server_name
        tc_object.tcinputs['SubclientName'] = "usermailbox"
        tc_object.tcinputs['BackupsetName'] = "User Mailbox"
        tc_object.tcinputs['RecallService'] = f'http://{self.commcell.webconsole_hostname}/webconsole'
        exchange_client = ExchangeMailbox(tc_object)
        self.log.info('Creating a exchange client')
        exchange_client.tc_object.client = exchange_client.cvoperations.add_exchange_client()
        self.log.info('Exchange client created with id: %s', exchange_client.tc_object.client.client_id)
        self.log.info("Creating an instance of subclient")
        exchange_client.tc_object.subclient = exchange_client.cvoperations.subclient
        self.log.info("Subclient instance created.")
        self.exchange_client = exchange_client
        self.tc_object = tc_object
        return exchange_client

    def create_exchange_policy(self, policy_name, policy_type, content_indexing=False):
        """Create an exchange configuration policy

        Args:
            policy_name         (str)       --  Config policy name

            policy_type         (str)       --  Policy type to be created
                  Valid values:
                        1.  "Cleanup"
                        2.  "Retention"
                        3.  "Archive"

            content_indexing    (bool)      --  True if content indexing to be enabled on the mailbox else False

        Returns:
            Configuration policy class instance

        """
        configuration_policies = self.commcell.policies.configuration_policies
        policy_object = configuration_policies.get_policy_object(
            policy_type, policy_name)
        self.log.info('Creating Exchange Policy %s ', policy_name)
        if configuration_policies.has_policy(policy_name):
            self.log.info('Policy exists. Deleting it and creating')
            configuration_policies.delete(policy_name)
        if policy_type == ARCHIVE:
            policy_object.enable_content_index = content_indexing
        policy = configuration_policies.add_policy(policy_object)
        return policy

    def create_exchange_configuration_policies(self, custom_str=None, content_indexing=False):
        """Creates all 3 default types of configuration policies

        Args:
            custom_str          (str)   --  prefix string for the policy names
            content_indexing    (bool)  --  True if content indexing to be enabled on the mailbox else False

        Returns:
            None

        """
        if custom_str is None:
            custom_str = str(int(datetime.datetime.today().timestamp()))
        policy_names = [ARCHIVE_POLICY_DEFAULT % custom_str,
                        CLEANUP_POLICY_DEFAULT % custom_str,
                        RETENTION_POLICY_DEFAULT % custom_str]
        policy_types = [ARCHIVE, CLEANUP, RETENTION]
        for index in range(len(policy_names)):
            self.create_exchange_policy(policy_names[index], policy_types[index], content_indexing)
        self.exchange_policies = policy_names
        return policy_names

    def restore_exchange_mailbox_client(self, exchange_mailbox_client, restore_machine, restore_path):
        """
        Invokes disk restore job for a given exchange client and verifies

        Args:
            exchange_mailbox_client     (object)    -   ExchangeMailbox object

            restore_machine             (str)       -   Restore client name where backed-up mails
                                                        will be restored

            restore_path                (str)       -   Restore path present on restore client
                                                        where backed-up mails will be restored

        Returns:
            None

        Raises:

            if input data is not valid

            if restored mails count was not same as expected

            if restored mail file size is invalid

        """
        if not (isinstance(exchange_mailbox_client, ExchangeMailbox) and
                isinstance(restore_machine, str) and isinstance(restore_path, str)):
            raise Exception("Input data is not of valid datatype")
        tc_object = exchange_mailbox_client.tc_object
        restore_client_machine = Machine(restore_machine, self.commcell)
        restore_client_machine.remove_directory(restore_path, 0)
        crawl_job_helper = CrawlJobHelper(tc_object)
        self.log.info("Now starting the restore process")
        job = exchange_mailbox_client.cvoperations.subclient. \
            disk_restore(paths=[r"\MB"],
                         destination_client=restore_machine,
                         destination_path=restore_path,
                         overwrite=True,
                         journal_report=False)
        exchange_mailbox_client.cvoperations.check_job_status(job)
        restore_mails_count = crawl_job_helper.get_docs_count(
            folder_path=restore_path,
            machine_name=restore_machine,
            include_folders=False
        )
        solr_helper = SolrHelper(exchange_mailbox_client)
        select_dict = {
            "DocumentType": 2,
            "ApplicationId": tc_object.subclient.subclient_id,
            "IsStub": 0
        }
        solr_resp = solr_helper.create_url_and_get_response(
            select_dict=select_dict
        )
        total_count = solr_helper.get_count_from_json(solr_resp.content)
        self.log.info("Expected restore mails count : %s", total_count)
        if not restore_mails_count == total_count:
            self.log.error("Restored files count doesn't match with expected value")
            self.log.error("Expected value: %s", total_count)
            self.log.error("Actual value: %s", restore_mails_count)
            raise Exception("Restored mails count doesn't match with expected value")
        self.log.info("All mails Restored successfully")

    def add_user_mailbox(self, exchange_client=None, mailbox_name=None, policy_names=None, use_policies=False):
        """Adds a user mailbox to the exchange client

            Args:
                exchange_client (ExchangeMailbox)   :   Exchange client where to add the mailbox
                mailbox_name    (str)               :   User mailbox mail id
                policy_names    (list)              :   List of the exchange configurations policies
                use_policies    (bool)              :   True if exchange policies to be used or Exchange Plan

            Returns:
                None
        """
        if not mailbox_name:
            mailbox_name = self.tc_object.tcinputs['UserMailBox']
        if not policy_names:
            policy_names = self.exchange_policies
        if not exchange_client:
            exchange_client = self.exchange_client
        sub_client_content = {
            "mailboxNames": mailbox_name,
            "plan_name": exchange_client.exchangeplan
        }
        if use_policies:
            sub_client_content = {
                "mailboxNames": mailbox_name,
                "archive_policy": policy_names[0],
                "retention_policy": policy_names[1],
                "cleanup_policy": policy_names[2]
            }
        self.log.info("Now setting up the user email.")
        exchange_client.cvoperations.subclient.set_user_assocaition(sub_client_content, use_policies=use_policies)
        self.log.info("User mailbox added to the sub client successfully")

    def clear_exchange_environment(self, exchange_client=None, policy_names=None):
        """Removes exchange client and index server from the environment

            Args:
                exchange_client (ExchangeMailbox)   :   Exchange client to be deleted
                policy_names    (list)              :   Policy names of the policies to be removed

            Returns:
                None
        """
        if not exchange_client:
            exchange_client: ExchangeMailbox = self.exchange_client
        if not policy_names:
            policy_names = self.exchange_policies
        self.log.info("Deleting exchange pseudo client")
        self.commcell.clients.delete(exchange_client.cvoperations.client.name)
        self.log.info("Exchange client deleted")
        configuration_policies = self.commcell.policies.configuration_policies
        if policy_names:
            for policy in policy_names:
                self.log.info(f"Deleting exchange policy {policy}")
                configuration_policies.delete(policy)
                self.log.info("Policy deleted successfully")
        self.log.info("Environment cleaned up")
