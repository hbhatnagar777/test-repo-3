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
from Application.Exchange.ExchangeMailbox.constants import (
    JOURNAL_POLICY_DEFAULT
)


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Exchange Journal Mailbox
     Discovery validation"""

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
        self.journal_policy = None
        self._subclient = None
        self._client = None
        self.name = ("Basic acceptance test of Journal Mailbox Discovery and"
                     " Validation of Journal Mailbox association Validation.")
        self.show_to_user = True
        self.exmbclient_object = None
        self.tcinputs = {
            "SubclientName": None,
            "BackupsetName": None,
            "IndexServer": None,
            "StoragePolicyName": None,
            "JobResultDirectory": None,
            "DomainName": None,
            "ProxyServers": None,
            "ExchangeServerName": None,
            "ExchangeCASServer": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.log.info('Creating Exchange Mailbox client object.')
        self.exmbclient_object = ExchangeMailbox(self)

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self._subclient = self.exmbclient_object.cvoperations.subclient

        journal_policy_default = JOURNAL_POLICY_DEFAULT % self.id
        self.journal_policy = self.exmbclient_object.cvoperations.add_exchange_plan(
            journal_policy_default, 'ExchangeJournal')

    def run(self):
        """Run function of this test case"""
        try:

            self.log.info(
                "---------------VALIDATE JOURNAL MAILBOX DISCOVERY"
                "---------------"
            )
            active_directory = self.exmbclient_object.active_directory

            active_directory.validate_journal_discovery()

            mailboxes_list = []
            for mailbox in self._subclient.discover_journal_users:
                mailboxes_list.append(mailbox['aliasName'])

            subclient_content = {
                'mailboxNames': mailboxes_list,
                'is_auto_discover_user': True,
                'plan_name': self.journal_policy.plan_name,
                'plan_id': self.journal_policy.plan_id
            }

            self.log.info(
                "------------CREATE JOURNAL MAILBOX ASSOCAITION AND VALIDATE"
                "-------------"
            )

            active_directory.set_journal_assocaition(subclient_content, False)
            active_directory.validate_journal_assocaition(subclient_content, False)

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED
