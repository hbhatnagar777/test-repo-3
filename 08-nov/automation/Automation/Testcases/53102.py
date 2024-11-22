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
from Application.Exchange.exchangepowershell_helper import ExchangePowerShell
from Application.Exchange.exchangedatabase_helper import ExchangeDbHelper
from Application.Exchange.ExchangeMailbox import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance
        test of Exchange Database backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Exchange Database: Full , incremental backup and OOP restore "
        self.show_to_user = True
        self.exchangepowershell_object = None
        self.ex_object = None
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
            self.ex_object.run_backup("full")

            inc_display_name = "Inc1_" + self.exchange_server + "_" + self.database_name[0]
            self.exchangepowershell_object.create_mailboxes(
                inc_display_name, self.database_name[0], self.domain_name)
            self.exchangepowershell_object.import_pst(inc_display_name, self.pst_path)
            self.ex_object.run_backup()
            self.exchangepowershell_object.mountordismount_database(
                self.database_name[0], "DISMOUNT")

            dest_path = os.path.join(constants.EXCHANGE_DATABASES, self.database_name[0])
            self.ex_object.delete_dbfile(dest_path)
            self.ex_object.run_restore_out_of_place("OOP", self.database_name[0], dest_path)
            self.exchangepowershell_object.mountordismount_database(
                self.database_name[0], "MOUNT")
            self.exchangepowershell_object.check_mailbox(inc_display_name)

        except Exception as ex:
            self.log.error(
                'Error %s on line %s. Error %s', type(ex).__name__,
                sys.exc_info()[-1].tb_lineno, ex
            )
            self.result_string = str(ex)
            self.status = cv_constants.FAILED
