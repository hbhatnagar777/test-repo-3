# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper class for Exchange Collection Pruning related operations

    ExchangePruningHelper:

        __init__()                          --  Initialize the Exchange Pruning Helper object

        initialize_exchange_onprem()        --  Initializes exchange mailbox object

        create_exchange_client()            --  Create a new exchange client

        configure_exchange_subclient()      --  Creates and configures the subclient for exchange client

        exchange_run_backup()               --  Runs backup for the exchange client

        exchange_delete_client()            --  Deletes the exchange client

"""

import time
from Application.Exchange.ExchangeMailbox.constants import ARCHIVE_PLAN_DEFAULT
from dynamicindex.CollectionPruning.collection_pruning_helper import CollectionPruningHelper
from dynamicindex.utils import constants as cs


class ExchangePruningHelper(CollectionPruningHelper):
    """ contains helper class for Exchange Collection Pruning related operations"""

    def __init__(self, commcell, ex_mb_object, email_id, mailbox_name):
        """
        Initialize the Exchange Pruning Helper object
            Args:
                commcell(object)        -- instance of commcell class
                ex_mb_object(object)    -- instance of exchange mailbox class
                email_id(str)           -- email id to be associated as subclient content
                mailbox_name(str)       -- name of the mailbox to be backed up
        """
        super().__init__(commcell)
        self.log.info('Initializing Exchange pruning helper object')
        self.ex_mb_object = ex_mb_object
        self.email_id = email_id
        self.mailbox_name = mailbox_name
        self.log.info('Exchange pruning helper object initialized')

    def initialize_exchange_onprem(self):
        """
        Initializes exchange mailbox object
        Returns:
            Object  -- An instance of exchange mailbox helper
        """
        self.log.info('Initializing Exchange Mailbox object')
        smtp_list = [self.email_id]
        self.ex_mb_object.users = smtp_list
        self.log.info('Exchange Mailbox object initialized')
        return self.ex_mb_object

    def create_exchange_client(self):
        """
        Create a new exchange client
        Returns:
            Object - Instance of exchange mailbox client
        """
        self.log.info('Creating new exchange client')
        client = self.ex_mb_object.cvoperations.add_exchange_client()
        self.log.info('Exchange client created successfully. Proceeding with basic configuration on the '
                      'exchange client')
        return client

    def configure_exchange_subclient(self, plan_name):
        """
        Creates and configures the subclient for exchange client
        Args:
            plan_name   --  Name of archiving plan to be created
        Returns:
            Object - Instance of exchange subclient
        """
        self.log.info('Configuring exchange subclient')
        subclient = self.ex_mb_object.cvoperations.subclient
        archive_plan_default = ARCHIVE_PLAN_DEFAULT % plan_name
        archive_plan = self.ex_mb_object.cvoperations.add_exchange_plan(archive_plan_default)
        subclient_content = {
            'mailboxNames': [self.mailbox_name],
            'plan_name': archive_plan.plan_name
        }
        subclient.set_user_assocaition(subclient_content, False)
        self.log.info('All associations and configurations on Exchange client successful')
        return subclient

    def exchange_run_backup(self):
        """
        Runs backup for the exchange client
        """
        self.log.info('Exchange client performing backup operation')
        self.ex_mb_object.cvoperations.run_backup()
        self.log.info(f'Backup job completed successfully')

    def exchange_delete_client(self, index_server):
        """
        Deletes the exchange client
        """
        self.log.info('Deleting exchange client')
        index_server_client = self.commcell.clients.get(index_server)
        self.log.info("Stopping index server service to avoid deletion of collections associated to the client")
        index_server_client.stop_service(cs.ANALYTICS_SERVICE_NAME)
        self.log.info("Index server services stopped. Proceeding with the deletion of client")
        self.ex_mb_object.cvoperations.delete_client()
        self.log.info("Client deleted successfully. Starting services")
        index_server_client.start_service(cs.ANALYTICS_SERVICE_NAME)
        time.sleep(self.wait_time)
        self.log.info("Data analytics service started")
