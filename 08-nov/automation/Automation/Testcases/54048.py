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
import os
from AutomationUtils import constants as cv_constants
from AutomationUtils.machine import Machine
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
        self.name = "Exchange DAG: block level backup, manual selection, oop restore with recovery"
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
            "OOPPath": None,
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
        self.oop_path = self.tcinputs['OOPPath']
        self.subclient_name = self.id
        self.host_machine = Machine()
        self.ex_object = ExchangeDbHelper(self)
        self.member_servers = self.client.get_dag_member_servers()

    def run(self):
        """Main function for test case execution"""
        try:
            os_sep = self.host_machine.os_sep
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
                database_name = f"AUTODB3_{member_server}"
                self.database_names[database_name] = member_server
                self.exchange_powershell_objects[member_server].create_database(database_name)
                self.log.info("Creating mailboxes")
                for i in range(0, constants.NUMBER_OF_MAILBOXES):
                    display_name = "AUTOMB3_" + database_name + "_" + str(i)
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
            as_server = self.member_servers[0].upper()
            for database, server in self.database_names.items():
                if server != as_server:
                    self.exchange_server = as_server
                    self.exchange_powershell_objects[server].exdbcopy_operations(
                        database,
                        self.exchange_server,
                        "PASSIVE"
                    )
            self.ex_object.create_exchdbsubclient(
                self.subclient_name,
                list(self.database_names.keys())
            )
            self.log.info('Adding property to optimize for message level recovery')
            self.subclient.set_exchangedb_subclient_prop(
                'optimizeForMessageLevelRecovery',
                True
            )
            self.log.info('Adding property for manual selection of servers')
            self.subclient.set_exchangedb_subclient_prop(
                'serverType',
                0
            )
            self.subclient.refresh()

            self.log.info('Adding property to associate server operation type')
            self.subclient.set_exchangedb_subclient_prop(
                'associatedServerOperationType',
                2
            )
            self.log.info(f"Setting {as_server} manually to backup from")
            associated_servers = []
            for database in self.database_names:
                t_dict = {
                    'server': as_server,
                    'databaseName': database
                }
                associated_servers.append(t_dict)
                del t_dict


            self.subclient.set_exchangedb_subclient_prop(
                'exchDBAssociatedServer',
                associated_servers
            )

            self.subclient.refresh()

            edb_paths, oop_edbpaths, dbsize_before, dbsize_after = {}, {}, {}, {}
            for database in self.database_names:
                edb_paths[database] = os.path.join(
                    constants.EXCHANGE_DATABASES,
                    database,
                    database + ".edb"
                )
                self.log.info(database)
                self.log.info(edb_paths)
                self.log.info(self.database_names[database])
                self.log.info("Getting the size of edb files before backup:")
                server = self.database_names[database].split(".", 1)[0].lower()
                temp_m = Machine(server, self.commcell)
                dbsize_before[database] = int(temp_m.get_file_size(
                    edb_paths[database]
                ))
                del temp_m
                self.log.info(f'For {database}, before backup size: {dbsize_before[database]}')

            job = self.ex_object.run_backup("full")
            backup_details = self.ex_object.get_db_server_backup_dict(job)
            for database in self.database_names:
                if backup_details[database].lower() != as_server.split(".", 1)[0].lower():
                    raise Exception('Not backed up from intended server')
            self.log.info('Back up initiated from intended server for the databases')

            for database in self.database_names:
                member_server = self.database_names[database]
                self.log.info("Running an outplace database restore")
                path = f'{self.oop_path}{os_sep}{member_server.split(".", 1)[0].lower()}'
                oop_edbpaths[database] = os.path.join(
                    path,
                    database + ".edb"
                )
                self.ex_object.run_restore_out_of_place(
                    "OOP",
                    database,
                    path,
                    self.host_machine.machine_name
                )
                self.log.info("Getting the size of edb files after restore:")
                dbsize_after[database] = int(self.host_machine.get_file_size(
                    oop_edbpaths[database]
                ))
                self.log.info(f'For {database}, before backup size: {dbsize_after[database]}')

            self.log.info("Comparing EDB file sizes")
            for database in self.database_names:
                if dbsize_before[database] != dbsize_after[database]:
                    raise Exception(f'Size of {database} is not equal. '
                                    f'Before: {dbsize_before[database]} '
                                    f'After: {dbsize_after[database]}')
                self.log.info(f'Size of {database} is equal')

        except Exception as excp:
            self.log.error(
                'Error %s on line %s. Error %s', type(excp).__name__,
                sys.exc_info()[-1].tb_lineno, excp
            )
            self.result_string = str(excp)
            self.status = cv_constants.FAILED

    def tear_down(self):
        """Teardown function for this testcase"""
        self.host_machine.remove_directory(self.oop_path)
