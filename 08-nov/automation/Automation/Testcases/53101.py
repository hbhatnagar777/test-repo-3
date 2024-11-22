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
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case
"""
import sys
import os
from AutomationUtils import constants as cv_constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Application.Exchange.exchangepowershell_helper import ExchangePowerShell
from Application.Exchange.exchangedatabase_helper import ExchangeDbHelper
from Application.Exchange.ExchangeMailbox import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance
        test of Exchange Database backup and OOP Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Exchange Database: Full backup and OOP restores with and without recovery"
        self.show_to_user = True
        self.exchangepowershell_object = None
        self.ex_object = None
        self.tcinputs = {
            "ExchangeServerName": None,
            "DomainName": None,
            "ExchangeAdminName": None,
            "ExchangeAdminPassword": None,
            "ExchangeDatabaseName": [],
            "PSTPath": None,
            "OOPPath": None,
            "OOPWRPath": None
        }

    def run(self):
        """Main function for test case execution"""
        try:
            self.exchange_server = self.tcinputs['ExchangeServerName']
            self.domain_name = self.tcinputs['DomainName']
            self.exchange_adminname = self.tcinputs['ExchangeAdminName']
            self.exchange_pwd = self.tcinputs['ExchangeAdminPassword']
            self.database_name = self.tcinputs['ExchangeDatabaseName']
            self.pst_path = self.tcinputs['PSTPath']
            self.oop_path = self.tcinputs['OOPPath']
            self.oopwr_path = self.tcinputs['OOPWRPath']
            self.host_machine = Machine(self.exchange_server)
            self.subclient_name = self.id

            self.ex_object = ExchangeDbHelper(self)
            self.exchangepowershell_object = ExchangePowerShell(self.ex_object,
                                                                self.exchange_server,
                                                                self.exchange_server,
                                                                self.exchange_adminname,
                                                                self.exchange_pwd,
                                                                self.exchange_server)
            self.log.info("Creating Database")
            self.exchangepowershell_object.create_database(self.database_name[0])
            self.log.info("Creating mailboxes")

            for i in range(1, constants.NUMBER_OF_MAILBOXES + 1):
                display_name = "AUTOMB_" + self.database_name[0] + "_" + str(i)
                self.exchangepowershell_object.create_mailboxes(display_name,
                                                                self.database_name[0],
                                                                self.domain_name,
                                                                constants.NUMBER_OF_MAILBOXES)
                self.exchangepowershell_object.import_pst(display_name, self.pst_path)
            self.ex_object.create_exchdbsubclient(self.subclient_name, self.database_name)
            self.log.info("Getting the size of edb file before backup")
            edb_path = os.path.join(
                constants.EXCHANGE_DATABASES,
                self.database_name[0],
                self.database_name[0] + ".edb")
            dbsize_beforebackup = os.path.getsize(edb_path)
            self.log.info("Getting the list of log files before backup")
            db_path = os.path.join(constants.EXCHANGE_DATABASES, self.database_name[0])
            file_beforebackup = self.ex_object.copy_exchange_filenames(
                db_path, "53101_BeforeBackup.txt")
            self.ex_object.run_backup("full")
            self.log.info("Running OOP restore with recovery")
            self.ex_object.run_restore_out_of_place("OOP", self.database_name[0], self.oop_path)
            self.log.info("Getting the size of edb file after restore")
            oop_edbpath = os.path.join(self.oop_path, self.database_name[0] + ".edb")
            dbsize_afterrestore = os.path.getsize(oop_edbpath)
            self.log.info("Comparing Edb file size before backup and after restore")
            if dbsize_beforebackup != dbsize_afterrestore:
                raise Exception(
                    "Size of the backedup database is not equal to database after restore")
            self.log.info("Running OOP restore without recovery")
            self.ex_object.run_restore_out_of_place(
                "OOPWR", self.database_name[0], self.oopwr_path)
            self.log.info("Getting the list of log files after restore")
            log_path = os.path.join(self.oopwr_path, "_restoredLogs")
            file_afterrestore = self.ex_object.copy_exchange_filenames(
                log_path, "53101_AfterRestore.txt")
            self.host_machine.compare_files(
                self.host_machine, file_beforebackup, file_afterrestore)
            self.host_machine.remove_directory(self.oop_path)
            self.host_machine.remove_directory(self.oopwr_path)

        except Exception as ex:
            self.log.error(
                'Error %s on line %s. Error %s', type(ex).__name__,
                sys.exc_info()[-1].tb_lineno, ex
            )
            self.result_string = str(ex)
            self.status = cv_constants.FAILED
