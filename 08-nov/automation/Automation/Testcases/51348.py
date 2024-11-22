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
import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Application.Exchange.ExchangeMailbox.constants import OpType
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.constants import ARCHIVE_POLICY_DEFAULT
from Application.Exchange.ExchangeMailbox.data_generation import TestData


class TestCase(CVTestCase):
    """
        Class for executing Basic acceptance test of Exchange online Backup and restore
        "51348":
        {
        "AgentName": "Exchange Mailbox",
        "InstanceName": "defaultInstanceName",
        "BackupsetName": "User Mailbox",
        "ProxyServers": [
          <proxy server name>
        ],
        "EnvironmentType":4,
        "RecallService":"",
        "StoragePolicyName":"Exchange Plan",
        "IndexServer":"<index-server name>",
        "DomainName": <exchange-online-domain-name>
        "azureAppKeySecret": "<azure-app-key-secret-from-Azure-portal>",
        "azureAppKeyID":"<App-Key-ID-from-Azure-portal>",
        "azureTenantName": "<Tenant-Name-from-Azure-portal>",
        "SubClientName":"usermailbox",
        "PlanName": "<Plan-name>>",
        "ServiceAccountDetails": [
          {
            "ServiceType": 2,
            "Username": "<username>",
            "Password": "<password>>"
          }
        ]
      }
    """
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
        self.name = "Basic acceptance test of Exchange Online backup and restore"
        self.show_to_user = True
        self.mailboxes_list = []
        self.smtp_list = []
        self.exmbclient_object = None
        self.configuration_policies = None
        self.testdata = None
        self.archive_policy = None
        self.tcinputs = {
            "SubclientName": None,
            "BackupsetName": None,
            "IndexServer": None,
            "ServerPlanName": None,
            "DomainName": None,
            "ProxyServers": None,
            "azureAppKeyID": None,
            "azureAppKeySecret": None,
            "azureTenantName": None,
            "EnvironmentType": None,
        }

    def setup(self):
        """Setup function of this test case"""
        self.log.info('Creating Exchange Mailbox client object.')
        self.exmbclient_object = ExchangeMailbox(self)
        # self.mailboxes_list = [mbx.lower().replace("@" + self.exmbclient_object.domain_name.lower(),
        #                                            "") for mbx in self.tcinputs["MailboxList"]]
        # self.smtp_list = self.tcinputs["MailboxList"]
        self.log.info(
            "--------------------------TEST DATA-----------------------------------"
        )
        # self.log.info("Mailbox List: %s" % self.mailboxes_list )
        # self.log.info("SMTP List: %s" % self.smtp_list)

        self.testdata = TestData(self.exmbclient_object)

        self.mailboxes_list = self.testdata.create_online_mailbox()

        self.smtp_list = list()
        for mailbox in self.mailboxes_list:
            smtp = mailbox + "@" + self.tcinputs['DomainName']
            self.smtp_list.append(smtp)

        self.exmbclient_object.exchange_lib.send_email(
            mailbox_list=self.smtp_list)

        self.log.info("Mailbox List: %s" % self.mailboxes_list)
        self.log.info("SMTP List: %s" % self.smtp_list)

        self._client = self.exmbclient_object.cvoperations.add_exchange_client(
        )
        self.log.info("Client creation successful")
        self._subclient = self.exmbclient_object.cvoperations.subclient
        self.o365_plan = self.tcinputs["Office365Plan"]

    def run(self):
        """Run function of this test case"""
        try:

            self.exmbclient_object.users = self.smtp_list
            subclient_content = {
                'mailboxNames': self.mailboxes_list,
                'plan_name': self.o365_plan
            }

            self.log.info("--------------------------CREATE USER ASSOCAITION"
                          "-----------------------------------")
            active_directory = self.exmbclient_object.active_directory
            active_directory.set_user_assocaitions(subclient_content, use_policies=False)

            self.log.info(""" SUCCESSFULLY ASSOCIATED THE SUBCLIENT """)

            self.log.info(
                "--------------------------READING MAILBOX PROPERTIES BEFORE BACKUP"
                "-----------------------------------")

            before_backup_object = self.exmbclient_object.exchange_lib
            before_backup_object.get_mailbox_prop()

            self.log.info("--------------------------RUNNING BACKUP"
                          "-----------------------------------")

            self.exmbclient_object.cvoperations.run_backup()

            self.log.info("-----------------GETTING BACKUPSET SIZE"
                          "------------------------------------------")
            self.backupset = self.exmbclient_object.cvoperations.backupset
            # backupset_prop = self.exmbclient_object.csdb_helper.get_backup_time_size_from_csdb(
            # )
            # self.log.info(backupset_prop)
            #
            # if not int(backupset_prop["applicationSize"]) > 0:
            #     self.log.error('Backupset Size is 0')
            #     raise Exception('Backup size should be greater than 0')

            self.log.info("-----------------CLEANING MAILBOX CONTENTS"
                          "------------------------------------------")

            self.exmbclient_object.exchange_lib.cleanup_mailboxes(mailbox_list=self.smtp_list)

            self.log.info("--------------------------RUNNING RESTORE"
                          "-----------------------------------")

            self.exmbclient_object.cvoperations.run_restore()

            self.log.info(
                "--------------------------READING MAILBOX PROPERTIES AFTER RESTORE"
                "-----------------------------------")

            after_restore_object = self.exmbclient_object.exchange_lib
            after_restore_object.get_mailbox_prop()

            self.log.info("--------------------------VALIDATING RESTORE"
                          "-----------------------------------")

            restore = self.exmbclient_object.restore

            restore.compare_mailbox_prop(OpType.OVERWRITE,
                                         before_backup_object.mailbox_prop,
                                         after_restore_object.mailbox_prop)

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s',
                           type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function for the Test Case"""
        # Cleanup Operation: Cleaning Up the mailboxes created
        self.testdata.delete_online_mailboxes(mailboxes_list=self.smtp_list)
        self.commcell.clients.delete(self.client.client_name)
        self.log.info('Deleted the Client')
