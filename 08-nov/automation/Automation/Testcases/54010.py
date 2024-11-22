# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__() 		--  Initialize TestCase class

    setup()			-- 	setup function of this test case

    run() 			--  run function of this test case
"""
import sys
import random
from collections import defaultdict
from AutomationUtils import constants as cv_constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.Exchange.exchangepowershell_helper import ExchangePowerShell
from Application.Exchange.exchangedatabase_helper import ExchangeDbHelper
from Application.Exchange.ExchangeMailbox import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance
        test of Exchange Database backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Exchange DAG: incremental backup and restore to another database"
        self.show_to_user = True
        self.exchangepowershell_object = None
        self.ex_object = None
        self.tcinputs = {
            "ClientName": None,
            "CASServerName": None,
            "DomainName": None,
            "ExchangeAdminName": None,
            "ExchangeAdminPassword": None,
            "PSTPath": None,
            "StoragePolicyName": None
        }
        self.exchange_server = None
        self.exchange_powershell_objects = {}
        self.database_names = {}
        self.cas_server, self.domain_name, self.exchange_adminname = None, None, None
        self.exchange_pwd, self.pst_path, self.subclient_name = None, None, None
        self.member_servers = None

    def setup(self):
        """Setup function for this test case"""
        self.cas_server = self.tcinputs['CASServerName']
        self.domain_name = self.tcinputs['DomainName']
        self.exchange_adminname = self.tcinputs['ExchangeAdminName']
        self.exchange_pwd = self.tcinputs['ExchangeAdminPassword']
        self.pst_path = self.tcinputs['PSTPath']
        self.subclient_name = self.id
        self.ex_object = ExchangeDbHelper(self)
        self.member_servers = self.client.get_dag_member_servers()

    def run(self):
        """Main function for test case execution"""
        try:
            for member_server in self.member_servers:
                self.exchange_powershell_objects[member_server] = ExchangePowerShell(
                    self.ex_object,
                    self.cas_server,
                    member_server,
                    self.exchange_adminname,
                    self.exchange_pwd,
                    member_server
                )
                self.log.info("Creating Database")
                database_name = f"AUTODB1_{member_server}"
                self.database_names[database_name] = member_server
                self.exchange_powershell_objects[member_server].create_database(database_name)
                self.log.info("Creating mailboxes")
                for i in range(0, constants.NUMBER_OF_MAILBOXES):
                    display_name = "AUTOMB1_" + database_name + "_" + str(i)
                    self.exchange_powershell_objects[member_server].create_mailboxes(
                        display_name,
                        database_name,
                        self.domain_name,
                        constants.NUMBER_OF_MAILBOXES
                    )
                    self.exchange_powershell_objects[member_server].import_pst(
                        display_name,
                        self.pst_path
                    )
            self.log.info("Databases info:")
            self.log.info(self.database_names)
            self.log.info("Creating passive copies")
            for database, server in self.database_names.items():
                while True:
                    member_server = random.choice(self.member_servers)
                    if member_server != server:
                        break
                self.exchange_server = member_server
                self.exchange_powershell_objects[server].exdbcopy_operations(
                    database,
                    self.exchange_server,
                    "PASSIVE"
                )
            self.ex_object.create_exchdbsubclient(
                self.subclient_name,
                list(self.database_names.keys())
            )
            self.log.info('Adding property to backup from passive copy')
            self.subclient.set_exchangedb_subclient_prop(
                'backupFromPassiveCopy',
                True
            )

            self.ex_object.run_backup("full")
            inc_display_name = defaultdict(list)
            for database, member_server in self.database_names.items():
                for i in range(0, constants.NUMBER_OF_MAILBOXES):
                    t_display_name = f"Inc1_{member_server}_{str(i)}"
                    inc_display_name[database].append(t_display_name)
                    self.exchange_powershell_objects[member_server].create_mailboxes(
                        t_display_name,
                        database,
                        self.domain_name,
                        constants.NUMBER_OF_MAILBOXES
                    )
                    self.exchange_powershell_objects[member_server].import_pst(
                        t_display_name,
                        self.pst_path
                    )
            job = self.ex_object.run_backup()
            if  job.backup_level != 'Incremental':
                raise Exception(f'Job {job.job_id} was not an incremental job')
            self.log.info('Ran incremental job')
            for database in self.database_names:
                member_server = self.database_names[database]
                self.log.info(f"Dismounting the database{database} on {member_server}")
                self.exchange_powershell_objects[member_server].mountordismount_database(
                    database,
                    "DISMOUNT"
                )
                self.log.info(f"Overwriting the database{database}")
                self.exchange_powershell_objects[member_server].overwrite_exdb(database)
                client = self.commcell.clients.get(
                    member_server.split(".", 1)[0]
                )
                self.log.info("Running an inplace database restore")
                self.ex_object.run_restore_inplace(database, client)
            self.log.info("Mounting the databases to check the consistency")
            for database in self.database_names:
                member_server = self.database_names[database]
                self.exchange_powershell_objects[member_server].mountordismount_database(
                    database,
                    "MOUNT"
                )
            for database, member_server in self.database_names.items():
                for mailbox in inc_display_name[database]:
                    self.exchange_powershell_objects[member_server].check_mailbox(mailbox)

            new_databases = {}
            for database in self.database_names:
                member_server = self.database_names[database]
                new_database = f'COPY_{database}'
                self.log.info(f'Creating new database: {new_database}')

                self.exchange_powershell_objects[member_server].create_database(new_database)
                self.log.info(f"Dismounting the database{new_database} on {member_server}")
                self.exchange_powershell_objects[member_server].mountordismount_database(
                    new_database,
                    "DISMOUNT"
                )
                self.log.info(f"Overwriting the database{new_database}")
                self.exchange_powershell_objects[member_server].overwrite_exdb(new_database)
                client = self.commcell.clients.get(
                    member_server.split(".", 1)[0]
                )
                self.log.info("Running restore to another database")
                self.ex_object.run_restore_inplace(database, client, new_database)
                new_databases[new_database] = member_server

            self.log.info(f'New databases info: {new_databases}')

            self.log.info("Mounting the databases to check the consistency")
            for database, member_server in new_databases.items():
                self.exchange_powershell_objects[member_server].mountordismount_database(
                    database,
                    "MOUNT"
                )

        except Exception as excp:
            self.log.error(
                'Error %s on line %s. Error %s', type(excp).__name__,
                sys.exc_info()[-1].tb_lineno, excp
            )
            self.result_string = str(excp)
            self.status = cv_constants.FAILED
