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
from Application.Exchange.ExchangeMailbox.constants import (ARCHIVE_POLICY_DEFAULT,
                                                            ARCHIVE_POLICY_ATTACHMENTS)
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from Application.Exchange.ExchangeMailbox.constants import OpType
from Application.Exchange.exchangepowershell_helper import ExchangePowerShell


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Exchange online Backup and OOP restore"""

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
        self.name = "EXMB Exchange online only- restore cases"
        self.show_to_user = True
        self.mailboxes_list = []
        self.smtp_list = []
        self.exmbclient_object = None
        self.testdata = None
        self.configuration_policies = None
        self.archive_policy_default = None
        self.archive_policy_attachments = None

        self.tcinputs = {
            "DomainName": None,
            "MailboxList": None,
            "PSTRestorePath": None,
            "DiskRestorePath": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.log.info('Creating Exchange Mailbox client object.')
        self.exmbclient_object = ExchangeMailbox(self)

        # Remove below code when method starts to work. Need to change input json too
        self.mailboxes_list = [
            mbx.lower().replace("@" + self.exmbclient_object.domain_name.lower(), "")
            for mbx in self.tcinputs["MailboxList"]]
        self.smtp_list = self.tcinputs["MailboxList"]
        # --- Remove till here ---

        self.log.info(
            "--------------------------TEST DATA-----------------------------------"
        )

        # Uncomment this code once get_mailbox_properties start working
        """ 
        testdata = TestData(self.exmbclient_object)
        self.mailboxes_list = testdata.create_mailbox()
        self.smtp_list = testdata.import_pst()
        """
        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self.log.info("Client creation successful")
        self._subclient = self.exmbclient_object.cvoperations.subclient
        archive_policy_default = ARCHIVE_POLICY_DEFAULT % self.id
        archive_policy_attachments = ARCHIVE_POLICY_ATTACHMENTS % self.id

        self.archive_policy_default = self.exmbclient_object.cvoperations.add_exchange_policy(
            self.exmbclient_object.cvoperations.get_policy_object
            (archive_policy_default, "Archive"))

        archive_policy_object = self.exmbclient_object.cvoperations.get_policy_object(
            archive_policy_attachments, "Archive")
        archive_policy_object.include_messages_with_attachements = True
        self.archive_policy_attachments = (
            self.exmbclient_object.cvoperations.add_exchange_policy(archive_policy_object))

    def run(self):
        """Run function of this test case"""
        try:

            self.exmbclient_object.users = self.smtp_list
            subclient_content_arr = [
                {
                    'mailboxNames': [self.mailboxes_list[0]],
                    'archive_policy': self.archive_policy_default,
                },
                {
                    'mailboxNames': [self.mailboxes_list[1]],
                    'archive_policy': self.archive_policy_attachments,
                }
            ]
            self.log.info(
                "--------------------------CREATE USER ASSOCAITION"
                "-----------------------------------"
            )
            active_directory = self.exmbclient_object.active_directory
            for subclient_content in subclient_content_arr:
                active_directory.set_user_assocaitions(subclient_content)
            """
            Uncomment below code when get_mailbox_props start working 
            self.log.info(
                "--------------------------READING MAILBOX PROPERTIES BEFORE BACKUP"
                "-----------------------------------")

            before_backup_object = self.exmbclient_object.exchange_lib
            before_backup_object.get_mailbox_prop()
            """
            self.log.info(
                "--------------------------RUNNING BACKUP"
                "-----------------------------------"
            )
            b_job = self.exmbclient_object.cvoperations.run_backup()

            # Remove below line when method starts working
            before_backup_cnt = int(b_job.summary['totalNumOfFiles'])

            self.log.info(
                "--------------------------RUNNING RESTORE"
                "-----------------------------------"
            )
            mailbox_restore_name = self.mailboxes_list[2]
            r_job = self.exmbclient_object.cvoperations.run_restore(
                oop=True, destination_mailbox=mailbox_restore_name)
            """
            # Uncomment when methods starts working
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
            """
            # Remove below lines when method starts working
            details = r_job.details
            after_restore_cnt = int(details['jobDetail']['detailInfo']['numOfObjects'])
            if after_restore_cnt != before_backup_cnt:
                self.log.info(
                    "Before Backup Count: %d, After restore count: %d" % (
                        before_backup_cnt, after_restore_cnt))
                raise Exception("Backup and restore count do not match")
            self.log.info(
                "-------------------VERIFIED RESTORE TO OTHER MBX COUNT %d, %d"
                "-----------------------------------" % (before_backup_cnt, after_restore_cnt)
            )
            # ---- Remove till here ----

            r_job = self.exmbclient_object.cvoperations.pst_restore(
                self.tcinputs["PSTRestorePath"],
                self.exmbclient_object.server_name)
            """
            # Uncomment when method starts working
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
            """

            # Remove below lines when method starts working
            details = r_job.details
            after_restore_cnt = int(details['jobDetail']['detailInfo']['numOfObjects'])

            if after_restore_cnt != before_backup_cnt:
                self.log.info(
                    "Before Backup Count: %d, After restore count: %d" % (
                        before_backup_cnt, after_restore_cnt))
                raise Exception("Backup and restore count do not match")
            self.log.info(
                "-------------------VERIFIED RESTORE TO PST COUNT %d, %d"
                "-----------------------------------" % (before_backup_cnt, after_restore_cnt)
            )
            # ---- Remove till here ----

            self.log.info(
                "-------------------------STARTING DISK RESTORE-----------------------")
            r_job = self.exmbclient_object.cvoperations.disk_restore(
                self.tcinputs["DiskRestorePath"], self.exmbclient_object.server_name)
            """
            # Uncomment when method starts to work
            self.log.info(
                "----------------------COMPARING RESTORE TO DISK----------------------")
            self.exmbclient_object.restore.compare_restore_disk(before_backup_object.mailbox_prop,
                                                                self.exmbclient_object.server_name,
                                                                self.tcinputs["DiskRestorePath"])
            self.log.info(
                "---------------------RESTORE TO DISK VALIDATED----------------------")
            """
            # Remove below lines when method starts working
            details = r_job.details
            after_restore_cnt = int(details['jobDetail']['detailInfo']['numOfObjects'])

            if after_restore_cnt != before_backup_cnt:
                self.log.info(
                    "Before Backup Count: %d, After restore count: %d" % (
                        before_backup_cnt, after_restore_cnt))
                raise Exception("Backup and restore count do not match")
            self.log.info(
                "--------------------------VERIFIED RESTORE TO DISK COUNT %d, %d"
                "-----------------------------------" % (before_backup_cnt, after_restore_cnt)
            )
            # ---- Remove till here ----

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED
