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

import AutomationUtils.machine
from Application.Exchange.ExchangeMailbox.constants import (CLEANUP_POLICY_DEFAULT,
                                                            ARCHIVE_POLICY_DEFAULT,
                                                            RETENTION_POLICY_DEFAULT, OpType)
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.exchangepowershell_helper import ExchangePowerShell
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.Exchange.ExchangeMailbox.data_generation import TestData


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "OOP Browse and Restore Validation"
        self.archive_policy_object = None
        self.cleanup_policy_object = None
        self.retention_policy_object = None
        self.machine_object = None
        self.tcinputs = {
        }

    def setup(self):
        """Setup function of this test case"""
        self.exchangeMailObject = ExchangeMailbox(self)
        self.log.info(
            "--------------------------TEST DATA-----------------------------------"
        )

        self.testdata = TestData(self.exchangeMailObject)

        self.mailbox_list = self.testdata.create_online_mailbox()

        self.smtp_list = list()
        for mailbox in self.mailbox_list:
            smtp = mailbox + "@" + self.tcinputs['DomainName']
            self.smtp_list.append(smtp)

        self.log.info("Mailbox List: %s" % self.mailbox_list)
        self.log.info("SMTP List: %s" % self.smtp_list)

        self.exchangeMailObject.users = self.smtp_list

        self.log.info("Populating mailboxes:{} with emails".format(self.smtp_list[0:4]))
        self.exchangeMailObject.exchange_lib.send_email(
            mailbox_list=self.smtp_list[0:4])
        self.log.info("Populated the mailboxes with emails")
        self._client = self.exchangeMailObject.cvoperations.add_exchange_client()
        self.log.info("Added the exchange client")
        self._backupset = self.exchangeMailObject.cvoperations.backupset
        self._subclient = self.exchangeMailObject.cvoperations.subclient
        self.log.info("Subclient association completed")
        archive_policy = ARCHIVE_POLICY_DEFAULT % self.id
        cleanup_policy = CLEANUP_POLICY_DEFAULT % (self.id)
        retention_policy = RETENTION_POLICY_DEFAULT % (self.id)
        self.archive_policy_object = self.exchangeMailObject.cvoperations.add_exchange_policy(
            policy_object=self.exchangeMailObject.cvoperations.get_policy_object(policy_name=archive_policy,
                                                                                 policy_type="Archive"))
        self.cleanup_policy_object = self.exchangeMailObject.cvoperations.add_exchange_policy(
            policy_object=self.exchangeMailObject.cvoperations.get_policy_object(policy_name=cleanup_policy,
                                                                                 policy_type="Cleanup"))
        self.retention_policy_object = self.exchangeMailObject.cvoperations.add_exchange_policy(
            policy_object=self.exchangeMailObject.cvoperations.get_policy_object(policy_name=retention_policy,
                                                                                 policy_type="Retention"))
        self.machine_object = AutomationUtils.machine.Machine(
            machine_name=self.tcinputs["ProxyServerDetails"]["IpAddress"],
            commcell_object=self.exchangeMailObject.commcell,
            username=self.tcinputs["ProxyServerDetails"]["Username"],
            password=self.tcinputs["ProxyServerDetails"]["Password"]
        )
        self.activedirectory = self.exchangeMailObject.active_directory
        self.powershell_object = ExchangePowerShell(
            ex_object=self.exchangeMailObject,
            exchange_server=None,
            cas_server_name=None,
            exchange_adminname=self.exchangeMailObject.exchange_online_user,
            exchange_adminpwd=self.exchangeMailObject.exchange_online_password,
            server_name=self.exchangeMailObject.server_name
        )

    def run(self):
        """Run function of this test case"""
        global mailboxprop
        try:
            self._subclient.refresh()
            userscontent = {
                "mailboxNames": self.mailbox_list[0:4],
                "archive_policy": self.archive_policy_object,
                "cleanup_policy": self.cleanup_policy_object,
                "retention_policy": self.retention_policy_object,
            }
            self._subclient.set_user_assocaition(subclient_content=userscontent)
            self.log.info("Associated the users")
            self.activedirectory.validate_user_assocaition(subclient_content=userscontent)
            self.log.info("Validated the association")
            self.log.info("--------------------------------------------------"
                          "Fetching the backup mailbox details"
                          "--------------------------------------------------")
            before_backup_prop = self.exchangeMailObject.exchange_lib
            before_backup_prop.mail_users = self.smtp_list[0:4]
            before_backup_prop.get_mailbox_prop()
            self.log.info("--------------------------------------------------"
                          "Backup Job running"
                          "--------------------------------------------------")
            backup_job = self._subclient.backup_mailboxes(mailbox_alias_names=self.mailbox_list[0:4])
            backup_job.wait_for_completion()
            isCompleted=backup_job.is_finished
            if isCompleted:
                self.log.info("---------------------------------------------"
                              "Backup Job Completed"
                              "---------------------------------------------")
            destination_mailbox = self.mailbox_list[-1]
            destination_mailbox_smtp = self.smtp_list[-1]
            self.log.info("--------------------------------------------------"
                          "Running OOP restore"
                          "--------------------------------------------------")
            mailboxes = self.exchangeMailObject.cvoperations.browse_mailboxes()
            self.activedirectory.validate_user_discovery()
            restore_job = self.exchangeMailObject.cvoperations.run_restore(oop=True, destination_mailbox=destination_mailbox)
            isCompleted = restore_job.is_finished
            if isCompleted:
                self.log.info("----------------------------------------------"
                              "OOP Restore Job Completed"
                              "----------------------------------------------")
            self.log.info("--------------------------------------------------"
                          "Fetching the restore mailbox details"
                          "--------------------------------------------------")
            after_restore_object=self.exchangeMailObject.exchange_lib
            after_restore_object.mail_users=[self.smtp_list[-1]]
            after_restore_object.get_mailbox_prop()
            restore_option = self.exchangeMailObject.restore
            restore_option.compare_mailbox_prop(OpType.OOPOVERWRITE,
                                                before_backup_prop.mailbox_prop,
                                                after_restore_object.mailbox_prop,
                                                destination_mailbox_smtp)
            # OOP restore to the mailbox Folder
            self.log.info("----------------------------------------------------"
                          "Running OOP restore to another mailbox folder"
                          "---------------------------------------------------")
            self.log.info("Creating new folder in the mailbox")
            exchange_lib=self.exchangeMailObject.exchange_lib
            destination_folder=exchange_lib.create_mailbox_folder(mailbox_smtp=destination_mailbox_smtp, folder_name="Personal")
            mailboxes = self.exchangeMailObject.cvoperations.browse_mailboxes()
            self.activedirectory.validate_user_discovery()
            restore_job=self.exchangeMailObject.cvoperations.run_restore(
                restore_selected_mailboxes=True,
                source_mailboxes=self.mailbox_list[0:4],
                oop=True,
                destination_mailbox=destination_mailbox,
                destination_mailbox_folder=destination_folder
            )
            isCompleted = restore_job.is_finished
            if isCompleted:
                self.log.info("----------------------------------------------"
                              "OOP Restore Job Completed"
                              "----------------------------------------------")
            self.log.info("--------------------------------------------------"
                          "Fetching the restore mailbox details"
                          "--------------------------------------------------")
            after_restore_object = self.exchangeMailObject.exchange_lib
            after_restore_object.mail_users = [self.smtp_list[-1]]
            after_restore_object.get_mailbox_prop()
            restore_option = self.exchangeMailObject.restore
            restore_option.compare_mailbox_prop(op_type=OpType.OOPOVERWRITE,
                                                before_backup=before_backup_prop.mailbox_prop,
                                                after_restore=after_restore_object.mailbox_prop,
                                                destination_mailbox_name=destination_mailbox_smtp,
                                                destination_mailbox_folder=destination_folder)
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("-----------------------------------------"
                      "Deleting the Client"
                      "-----------------------------------------")
        self.commcell.clients.delete(self.client.client_name)
        self.log.info("-----------------------------------------"
                      "Deleted the Client"
                      "-----------------------------------------")