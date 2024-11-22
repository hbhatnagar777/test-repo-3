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
        self.name = "Exchange DAG: backup from active copy if passive unavailable and OOP restore without recovery"
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
                database_name = f"AUTODB5_{member_server}"
                self.database_names[database_name] = member_server
                self.exchange_powershell_objects[member_server].create_database(database_name)
                self.log.info("Creating mailboxes")
                for i in range(0, constants.NUMBER_OF_MAILBOXES):
                    display_name = "AUTOMB5_" + database_name + "_" + str(i)
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
            self.log.info("Will not create passive copies")
            self.ex_object.create_exchdbsubclient(
                self.subclient_name,
                list(self.database_names.keys())
            )

            self.log.info('Adding property to backup from active copy if passive is unavailable')
            self.subclient.set_exchangedb_subclient_prop(
                'backupFromPassiveCopy',
                True
            )
            self.subclient.set_exchangedb_subclient_prop(
                'backupFromActiveCopy',
                True
            )

            database_paths = {}
            self.log.info('Getting db paths before backup')
            for database, server in self.database_names.items():
                db_path = os.path.join(constants.EXCHANGE_DATABASES, database)
                database_paths[database] = db_path
            self.log.info(f'Database Paths: {database_paths}')

            job = self.ex_object.run_backup("full")

            backup_details = self.ex_object.get_db_server_backup_dict(job)
            for database, server in self.database_names.items():
                if backup_details[database].lower() != server.split(".", 1)[0].lower():
                    raise Exception('Not backed up from active copy')
            self.log.info('Back up initiated from active copies for the databases')

            for database, server in self.database_names.items():
                self.log.info("Running an out place database restore")
                path = f'{self.oop_path}{os_sep}{server.split(".", 1)[0].lower()}'
                self.ex_object.run_restore_out_of_place(
                    "OOPWR",
                    database,
                    path,
                    self.host_machine.machine_name
                )
                log_path = os.path.join(path, "_restoredLogs")
                self.log.info(f'Coping files from _restoredLogs folder to restored folder')
                files = self.host_machine.get_files_in_path(log_path)
                for f in files:
                    Machine().copy_folder(f, path)
                self.log.info('Removing _restoredLogs folder')
                self.host_machine.remove_directory(log_path)
                files = self.host_machine.get_files_in_path(path)
                self.log.info(f"Dismounting the database{database} on {member_server}")
                self.exchange_powershell_objects[server].mountordismount_database(
                    database,
                    "DISMOUNT"
                )
                machine = Machine(server.split(".", 1)[0], self.commcell)

                self.ex_object.replace_database_objects(
                    machine,
                    database_paths[database],
                    database,
                    files
                )
                self.log.info("Mounting the databases to check the consistency")
                self.exchange_powershell_objects[server].mountordismount_database(
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

    def tear_down(self):
        """"Teardown function for this testcase
        """
        self.host_machine.remove_directory(self.oop_path)
