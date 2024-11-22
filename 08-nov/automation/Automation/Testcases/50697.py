# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""

import sys
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from Application.Exchange.ExchangeMailbox.constants import OpType
from Application.Exchange.ExchangeMailbox.constants import (
    ARCHIVE_POLICY_ATTACHMENTS,
    ARCHIVE_POLICY_DEFAULT
)
from Application.Exchange.exchangepowershell_helper import ExchangePowerShell


class TestCase(CVTestCase):
    """Class for EXMB - Restore to mailbox , to PST and To Disk Options"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name            (str)       --  name of this test case

                show_to_user    (bool)      --  test case flag to determine if the test case is
                                                    to be shown to user or not
                    Accept:
                        True    -   test case will be shown to user from commcell gui

                        False   -   test case will not be shown to user
                    default: False

                tcinputs    (dict)      --  dict of test case inputs with input name as dict key
                                                and value as input type
                        Ex: {
                             "MY_INPUT_NAME": None
                        }

                exmbclient_object      (object)    --  Object of ExchangeMailbox class
        """
        super(TestCase, self).__init__()
        self._subclient = None
        self._client = None
        self.name = "EXMB - Restore to mailbox , to PST and To Disk Options"
        self.show_to_user = True
        self.smtp_list = []
        self.mailboxes_list = []
        self.exmbclient_object = None
        self.tcinputs = {
            "DomainName": None,
            "PSTRestorePath": None,
            "DiskRestorePath": None
        }
        self.archive_policy_default = None
        self.archive_policy_attachments = None

    def setup(self):
        """Setup function of this test case"""
        self.exmbclient_object = ExchangeMailbox(self)
        self.log.info(
            "--------------------------TEST DATA-----------------------------------"
        )

        test_data = TestData(self.exmbclient_object)

        self.mailboxes_list = test_data.create_mailbox()
        self.smtp_list = test_data.import_pst()
        self.exmbclient_object.users = self.smtp_list

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self._subclient = self.exmbclient_object.cvoperations.subclient
        ewsURL = self.tcinputs.get("EWSServiceURL", None)
        if ewsURL:
            self.exmbclient_object.cvoperations.enableEWSSupport(service_url=ewsURL)
        archive_policy_default = ARCHIVE_POLICY_DEFAULT % self.id
        archive_policy_attachments = ARCHIVE_POLICY_ATTACHMENTS % self.id
        self.archive_policy_default = self.exmbclient_object.cvoperations.add_exchange_plan(
            plan_name=archive_policy_default)
        self.archive_policy_attachments = self.exmbclient_object.cvoperations.add_exchange_plan(
            plan_name=archive_policy_attachments, include_only_msgs_with_attachemts=True)

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info(
                "-----------------------CREATE USER ASSOCIATION-----------------------")
            subclient_content1 = {
                'mailboxNames': [self.mailboxes_list[0]],
                'plan_name': self.archive_policy_default.plan_name
            }
            subclient_content2 = {
                'mailboxNames': [self.mailboxes_list[1]],
                'plan_name': self.archive_policy_attachments.plan_name
            }
            active_directory = self.exmbclient_object.active_directory
            active_directory.set_user_assocaitions(subclient_content1, False)
            active_directory.set_user_assocaitions(subclient_content2, False)

            self.log.info(
                "--------------------------READING MAILBOX PROPERTIES BEFORE BACKUP"
                "-----------------------------------")

            before_backup_object = self.exmbclient_object.exchange_lib
            before_backup_object.get_mailbox_prop()

            self.log.info(
                "---------------------------RUNNING BACKUP-----------------------------")
            self.exmbclient_object.cvoperations.run_backup()
            self.log.info(
                "--------------------------RUNNING OOP RESTORE-------------------------")

            # ----------------- OOP Restore - Restore to another Mailbox --------------
            mailbox_restore_name = self.mailboxes_list[2]
            self.exmbclient_object.cvoperations.run_restore(
                oop=True,
                destination_mailbox=mailbox_restore_name
            )

            self.log.info(
                "-------------READING MAILBOX PROPERTIES AFTER OOP RESTORE-----------")
            mailbox_restore_name = f'{mailbox_restore_name}@{ self.tcinputs["DomainName"]}'
            after_restore_object = self.exmbclient_object.exchange_lib
            after_restore_object.mail_users = [mailbox_restore_name]
            after_restore_object.get_mailbox_prop()
            restore = self.exmbclient_object.restore
            self.log.info(
                "-----------------------COMPARING OOP RESTORE------------------------")
            restore.compare_mailbox_prop(OpType.OOPOVERWRITE, before_backup_object.mailbox_prop,
                                         after_restore_object.mailbox_prop,
                                         mailbox_restore_name)
            self.log.info(
                "------------------------OOP RESTORE VALIDATED------------------------")

            # ----------------- OOP Restore - Restore to disk --------------

            self.log.info(
                "-------------------------STARTING DISK RESTORE-----------------------")
            self.exmbclient_object.cvoperations.disk_restore(
                self.tcinputs["DiskRestorePath"],
                self.exmbclient_object.server_name)

            self.log.info(
                "----------------------COMPARING RESTORE TO DISK----------------------")
            self.exmbclient_object.restore.compare_restore_disk(before_backup_object.mailbox_prop,
                                                                self.exmbclient_object.server_name,
                                                                self.tcinputs["DiskRestorePath"])
            self.log.info(
                "---------------------RESTORE TO DISK VALIDATED----------------------")

            # ----------------- OOP Restore - Restore to PST --------------

            self.log.info(
                "-----------------------STARTING PST RESTORE-----------------------")
            self.exmbclient_object.cvoperations.pst_restore(
                self.tcinputs["PSTRestorePath"],
                self.exmbclient_object.server_name)

            exchange_power_shell_obj = ExchangePowerShell(
                self.exmbclient_object,
                self.exmbclient_object.exchange_cas_server,
                self.exmbclient_object.exchange_server[0],
                self.exmbclient_object.service_account_user,
                self.exmbclient_object.service_account_password,
                self.exmbclient_object.server_name
            )

            self.log.info(
                "----------IMPORTING RESTORED PST TO MAILBOX: %s----------",
                self.mailboxes_list[len(self.mailboxes_list) - 1])
            temp = self.exmbclient_object.pst_restore_path.split("\\")
            pst_unc_path = f'\\\\{self.exmbclient_object.server_name}\\{temp[-2]}\\{temp[-1]}'
            exchange_power_shell_obj.import_pst(self.mailboxes_list[len(self.mailboxes_list) - 1],
                                                pst_unc_path)
            pst_restore_obj = self.exmbclient_object.exchange_lib
            pst_restore_obj.mail_users = [f'{self.mailboxes_list[len(self.mailboxes_list) - 1]}@'
                                          f'{self.tcinputs["DomainName"]}']
            pst_restore_obj.get_mailbox_prop()
            self.log.info(
                "--------------------COMPARING RESTORE TO PST--------------------")
            pst_restore = self.exmbclient_object.restore
            pst_restore.compare_restore_pst(before_backup_object.mailbox_prop,
                                            pst_restore_obj.mailbox_prop,
                                            pst_restore_obj.mail_users[0])
            self.log.info(
                "--------------------------- RESTORE TO PST VALIDATED ---------------------------")

        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            self.result_string = str(ex)
            self.status = constants.FAILED
