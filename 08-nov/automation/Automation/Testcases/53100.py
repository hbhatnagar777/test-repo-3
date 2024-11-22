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

from Application.Exchange.exchangepowershell_helper import ExchangePowerShell
from Application.Exchange.ExchangeMailbox import constants
from Application.Exchange.exchangedatabase_helper import ExchangeDbHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance
        test of Exchange Database backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Exchange Database: Full backup and inplace restore "
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
            "PSTPath": None
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
            self.subclient_name = self.id

            self.ex_object = ExchangeDbHelper(self)
            self.exchangepowershell_object = ExchangePowerShell(self.ex_object,
                                                                self.exchange_server,
                                                                self.exchange_server,
                                                                self.exchange_adminname,
                                                                self.exchange_pwd,
                                                                self.exchange_server)
            self.host_machine = Machine(self.exchange_server)

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
            path1 = self.exchangepowershell_object.get_mailbox_name(
                self.database_name[0], "MBname1_53100.txt")

            self.ex_object.create_exchdbsubclient(self.subclient_name, self.database_name)
            self.ex_object.run_backup("full")
            self.exchangepowershell_object.mountordismount_database(
                self.database_name[0], "DISMOUNT")
            self.exchangepowershell_object.overwrite_exdb(self.database_name[0])

            self.ex_object.run_restore_inplace(self.database_name[0])
            self.exchangepowershell_object.mountordismount_database(
                self.database_name[0], "MOUNT")
            path2 = self.exchangepowershell_object.get_mailbox_name(
                self.database_name[0], "MBname2_53100.txt")
            self.log.info("Comparing files")
            self.host_machine.compare_files(self.host_machine, path1, path2)

        except Exception as ex:
            self.log.error(
                'Error %s on line %s. Error %s', type(ex).__name__,
                sys.exc_info()[-1].tb_lineno, ex
            )
            self.result_string = str(ex)
            self.status = cv_constants.FAILED
