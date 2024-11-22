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
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.Exchange.ExchangeMailbox.constants import OpType
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.utils import verify_mailbox_guids_association
from Application.Exchange.exchangepowershell_helper import ExchangePowerShell


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Exchange online Backup and restore

            Example for test case inputs:
        "60205":
        {
        "ClientName":<name of client>
        "AgentName": "Exchange Mailbox",
        "InstanceName": "defaultInstanceName",
        "BackupsetName": "User Mailbox",
        "ProxyServers": [
          <proxy server name>
        ],
        "EnvironmentType":3,
        "OnlineDomainName":<domain-for-online>,
        "DomainName":<on-prem-domain-name>
        "MigratedUsers":<list>,
        "OnlineCreatedUsers":<list>,
        "StoragePolicyName":"Exchange Plan",
        "IndexServer":"<index-server name>",
        "SubClientName":"usermailbox",
        "PlanName": "<Plan-name>>",

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

                archive_policy         (object)    --  Object of Configuration policy to be used to associate the group
                retention_policy       (object)    --  Object of Configuration policy to be used to associate the group

                mailboxes_list          (list)     --   List of Alias Name
        """
        super(TestCase, self).__init__()
        self.name = "EXMB Type 3: Mailbox Backup, Clean-up and Restore Verification"
        self.show_to_user = True
        self.archive_policy = None
        self.mailboxes_list = list()
        self.smtp_list = list()
        self.exmbclient_object = None
        self.testdata = None
        self.retention_policy = None
        self.online_exmblclient = None
        self.tcinputs = {
            "SubclientName": None,
            "BackupsetName": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.log.info('Creating Exchange Mailbox client object.')
        self.exmbclient_object = ExchangeMailbox(self)

        self.online_exmblclient = ExchangeMailbox(self)
        self.online_exmblclient.environment_type = 4
        self.online_exmblclient.domain_name = self.tcinputs["OnlineDomainName"]

        self.log.info(
            "--------------------------TEST DATA-----------------------------------"
        )


        self.migrated_users = self.tcinputs["MigratedUsers"]
        self.online_users = self.tcinputs["OnlineUsers"]
        self.mailboxes_list = list()

        self.mailboxes_list.extend(self.migrated_users)
        self.mailboxes_list.extend(self.online_users)
        self.log.info("Mailboxes List: {}".format(self.mailboxes_list))

        self.online_smtp = list()
        for mailbox in self.migrated_users:
            self.online_smtp.append(mailbox + "@" + self.exmbclient_object.domain_name)
        for mailbox in self.online_users:
            self.online_smtp.append(mailbox + "@" + self.online_exmblclient.domain_name)

        self.log.info("Online Mailboxes: {}".format(self.online_smtp))

        self.online_exmblclient.users = self.online_smtp

        self.exmbclient_object.client_name = self.client.client_name
        self.exmbclient_object.cvoperations.client_name = self.client.client_name

        self.online_exmblclient.client_name = self.client.client_name
        self.online_exmblclient.cvoperations.client_name = self.client.client_name

    def run(self):
        """Run function of this test case"""
        try:

            self.log.info(
                "-----------------------CREATE USER ASSOCIATION-----------------------")
            subclient_content = {
                'mailboxNames': self.mailboxes_list,
                'plan_name': self.tcinputs["ExchangePlan"]
            }

            self.subclient.set_user_assocaition(subclient_content, use_policies=False)

            self.log.info("Fetching mailbox properties")

            online_exchangelib_before_re = self.online_exmblclient.exchange_lib

            online_exchangelib_before_re.send_email(mailbox_list = self.online_smtp)

            online_exchangelib_before_re.get_mailbox_prop()

            self.log.info("Fetched Mailbox properties for on-prem and online users")

            self.log.info("Starting Backup Now")
            self.exmbclient_object.cvoperations.run_backup()
            self.log.info("Backup Completed Successfully")

            self.log.info("Performing a cleanup")

            online_exchangelib_before_re.cleanup_mailboxes(mailbox_list=self.online_smtp)

            self.log.info("Cleanup Completed")

            self.log.info("Starting Restore")
            self.exmbclient_object.cvoperations.run_restore()
            self.log.info("Restore completed")

            self.log.info("Fetching Mailbox properties again")

            online_exchangelib_after_re = self.online_exmblclient.exchange_lib

            online_exchangelib_after_re.get_mailbox_prop()

            self.log.info("Successfully Fetched Mailbox Properties")

            self.log.info("Comparing the Mailbox Properties now")

            online_restore = self.online_exmblclient.restore
            online_restore.compare_mailbox_prop(OpType.OVERWRITE,
                                                online_exchangelib_before_re.mailbox_prop,
                                                online_exchangelib_after_re.mailbox_prop)

            self.log.info("Performing Cleanup")

            self.log.info("Cleaning up mailbox content")
            online_exchangelib_before_re.cleanup_mailboxes(mailbox_list=self.online_smtp)

            self.log.info("Removing the association")
            self.subclient.delete_user_assocaition(subclient_content, use_policies=False)

            self.subclient.refresh()
            # Discovery for next run

            self.log.info('Test Case completed!!!')

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s',
                           type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED

