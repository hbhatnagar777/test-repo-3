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
from AutomationUtils import constants as cv_constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Application.Exchange.ExchangeMailbox import constants
from Application.Exchange.exchangepowershell_helper import ExchangePowerShell
from Application.Exchange.exchangedatabase_helper import ExchangeDbHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Exchange
     Database backup and Restore test case when edb and log file are different"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Exchange Database full backup and inplace restore" \
                    " when edb path and log file path are different "
        self.show_to_user = True
        self.exchangepowershell_object = None
        self.ex_object = None
        self.domain_name = None
        self.exchange_server = None
        self.tcinputs = {
            "ExchangeServerName": None,
            "DomainName": None,
            "ExchangeAdminName": None,
            "ExchangeAdminPassword": None,
            "ExchangeDatabaseName": [],
            "PSTPath": None,
            "EDBpath": None,
            "Logpath": None
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
            self.edb_path = self.tcinputs['EDBpath']
            self.log_path = self.tcinputs['Logpath']
            self.subclient_name = self.id

            self.ex_object = ExchangeDbHelper(self)
            self.exchangepowershell_object = ExchangePowerShell(self.ex_object,
                                                                self.exchange_server,
                                                                self.exchange_server,
                                                                self.exchange_adminname,
                                                                self.exchange_pwd,
                                                                self.exchange_server)
            self.host_machine = Machine(self.exchange_server)

            self.log.info("Creating Database with the given name")
            self.exchangepowershell_object.create_database\
                        (self.database_name[0], self.edb_path, self.log_path)
            self.log.info("Creating mailboxes and importing pst to the mailboxes")

            for i in range(1, constants.NUMBER_OF_MAILBOXES + 1):
                display_name = "AUTOMB_" + self.database_name[0] + "_" + str(i)
                self.exchangepowershell_object.create_mailboxes(display_name,
                                                                self.database_name[0],
                                                                self.domain_name,
                                                                constants.NUMBER_OF_MAILBOXES)
                self.exchangepowershell_object.import_pst(display_name, self.pst_path)

            self.log.info("Getting the mailbox names from exchange powershell")
            path1 = self.exchangepowershell_object.get_mailbox_name(
                self.database_name[0], "MBname1_48474.txt")

            self.log.info("Creating subclient and assigning content")
            self.ex_object.create_exchdbsubclient(self.subclient_name, self.database_name)
            self.log.info("Running full backup")
            self.ex_object.run_backup("full")
            self.log.info("Dismounting the database")
            self.exchangepowershell_object.mountordismount_database(self.database_name[0],
                                                                    "DISMOUNT")
            self.log.info("overwriting the database")
            self.exchangepowershell_object.overwrite_exdb(self.database_name[0])
            self.log.info("Running an inplace database restore")
            self.ex_object.run_restore_inplace(self.database_name[0])
            self.log.info("Mounting the database to check the consistency")
            self.exchangepowershell_object.mountordismount_database(self.database_name[0], "MOUNT")
            self.log.info("getting the mailbox names after restore")
            path2 = self.exchangepowershell_object.get_mailbox_name(
                self.database_name[0], "MBname2_48474.txt")
            self.log.info("Comparing files before backup and after restore")
            self.host_machine.compare_files(self.host_machine, path1, path2)
            self.exchangepowershell_object.remove_database(self.database_name[0], self.edb_path, self.log_path)


        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = cv_constants.FAILED
