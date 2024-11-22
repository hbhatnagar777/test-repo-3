# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper class for Exchange SDG related operations

    ExchangeSDGHelper:

        __init__()                          --  Initialize the Exchange Pruning Helper object

        initialize_exchange_onprem()        --  Initializes exchange mailbox object

        create_exchange_client()            --  Create a new exchange client

        configure_exchange_subclient()      --  Creates and configures the subclient for exchange client

        exchange_run_backup()               --  Runs backup for the exchange client

        exchange_delete_client()            --  Deletes the exchange client

"""
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper
from AutomationUtils import logger


class ExchangeSDGHelper:
    """ contains helper class for Exchange SDG related operations"""

    def __init__(self, commcell, ex_mb_object):
        """
        Initialize the Exchange SDG Helper object
            Args:
                commcell(object)        -- instance of commcell class
                ex_mb_object(object)    -- instance of exchange mailbox class
        """
        self.commcell = commcell
        self.log = logger.get_log()
        self.log.info('Initializing Exchange pruning helper object')
        self.ex_mb_object = ex_mb_object
        self.ex_mb_object.cvoperations.commcell = self.commcell
        self.log.info('Exchange pruning helper object initialized')

    def create_exchange_online_client(self, client_name, server_plan, **kwargs):
        """
        Adds a new Exchange Online Client to the Commcell.
        Args:
            client_name(str)                --  name of the new Exchange Mailbox Client
            server_plan(str)                --  server_plan to associate with the client
        **kwargs(dict)                      --  Dictionary of inputs
            index_server(str)               --  index server for virtual client
            clients_list(list)              --  list containing client names / client objects,
                                                to associate with the Virtual Client
            azure_app_key_secret(str)       --  app secret for the Exchange online
            azure_tenant_name(str)          --  tenant for exchange online
            azure_app_key_id(str)           --  app key for exchange online

        Returns:
            Object                          --  Exchange Online Client Type Object

        """
        self.log.info(f"Creating Exchange online client - [{client_name}]")
        client = self.commcell.clients.add_exchange_client(client_name=client_name,
                                                           server_plan=server_plan,
                                                           azure_tenant_name=kwargs.get('azure_directory_id'),
                                                           azure_app_key_id=kwargs.get('azure_app_id'),
                                                           azure_app_key_secret=kwargs.get('azure_app_key_id'),
                                                           index_server=kwargs.get('index_server'),
                                                           clients_list=kwargs.get('access_nodes_list'),
                                                           backupset_type_to_create=1,
                                                           environment_type=4, recall_service_url='',
                                                           job_result_dir='', exchange_servers=[], service_accounts={})
        self.log.info(f"Client [{client_name}] created successfully")
        return client

    def configure_exchange_subclient(self, plan_name, mailboxes):
        """
        Creates and configures the subclient for exchange client
        Args:
            plan_name   --  Name of archiving plan to be created
        Returns:
            Object - Instance of exchange subclient
        """
        self.log.info('Configuring exchange subclient')
        subclient = self.ex_mb_object.cvoperations.subclient
        subclient_content = {
            'mailboxNames': mailboxes,
            'plan_name': plan_name
        }
        subclient.set_user_assocaition(subclient_content, False)
        self.log.info('All associations and configurations on Exchange client successful')
        return subclient

    def exchange_run_backup(self, admin_commcell=None):
        """
        Runs backup for the exchange client and checks for playback completion
        Args:
            admin_commcell(object)  --  Admin commcell object to ensure playback completion
        """
        job = self.exchange_run_backup_only()
        self.log.info("Checking for playback completion")
        if admin_commcell is not None:
            self.ex_mb_object.cvoperations.commcell = admin_commcell
        solr = SolrHelper(self.ex_mb_object)
        solr.check_all_items_played_successfully(job.job_id)
        if admin_commcell is not None:
            self.ex_mb_object.cvoperations.commcell = self.commcell
        self.log.info("Playback completed successfully")

    def exchange_run_backup_only(self):
        """
        Runs backup for the exchange client and waits for completion
        Raises:
            Exception - When job fails to complete
        """
        self.log.info('Exchange client performing backup operation')
        subclient = self.ex_mb_object.cvoperations.subclient
        job = subclient.backup()
        self.log.info('Backup job started; job ID: %s', job.job_id)
        if not job.wait_for_completion():
            self.log.exception("Pending Reason %s", job.pending_reason)
            raise Exception('%s job not completed successfully.', job.job_type)
        self.log.info('%s job completed successfully.', job.job_type)
        self.log.info('Backup job completed successfully')
        return job

    def delete_client(self, client_name):
        """
        Deletes the given Exchange client
        Args:
            client_name(str)        --  Name of the client
        """
        self.log.info(f'Request received to remove client - [{client_name}]')
        if self.commcell.clients.has_client(client_name):
            self.commcell.clients.delete(client_name)
        self.log.info(f"Successfully deleted client - [{client_name}]")
