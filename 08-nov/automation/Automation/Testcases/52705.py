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
from Application.Exchange.ExchangeMailbox.constants import (
    JOURNAL_POLICY_DEFAULT,
    RETENTION_POLICY_DEFAULT
)


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of of Journal Mailbox Cleanup"""

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
        self.testdata = None
        self.journal_policy = None
        self.name = "Basic acceptance test of Journal Mailbox Cleanup"
        self.show_to_user = True
        self.mailboxes_list = []
        self.smtp_list = []
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
            "ExchangeCASServer": None,
            "RecallService": None
        }
        self.journal_policy = None

    def setup(self):
        """Setup function of this test case"""
        self.log.info('Creating Exchange Mailbox client object.')
        self.exmbclient_object = ExchangeMailbox(self)
        self.log.info(
            "--------------------------TEST DATA-----------------------------------"
        )
        self.testdata = TestData(self.exmbclient_object)
        self.mailboxes_list = self.testdata.create_journal_mailbox()
        self.smtp_list = self.testdata.import_pst()

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self._subclient = self.exmbclient_object.cvoperations.subclient

        journal_policy_default = JOURNAL_POLICY_DEFAULT % self.id
        self.journal_policy = self.exmbclient_object.cvoperations.add_exchange_plan(
            journal_policy_default, 'ExchangeJournal')

    def run(self):
        """Run function of this test case"""
        try:

            self.exmbclient_object.users = self.smtp_list
            subclient_content = {
                'mailboxNames': self.mailboxes_list,
                'is_auto_discover_user': True,
                'plan_name': self.journal_policy.plan_name,
                'plan_id': self.journal_policy.plan_id
            }

            self.log.info(
                "-----------------CREATE JOURNAL ASSOCIATION----------------"
            )
            active_directory = self.exmbclient_object.active_directory

            active_directory.set_journal_assocaition(subclient_content, False)

            self.log.info(
                "----------------READING MAILBOX PROPERTIES BEFORE BACKUP----------------------"
            )

            before_backup_object = self.exmbclient_object.exchange_lib
            before_backup_object.get_mailbox_prop()

            self.log.info(
                "------------------RUNNING BACKUP---------------------------------"
            )
            self.exmbclient_object.cvoperations.run_backup(False)

            self.log.info(
                "------------------RUNNING CLEANUP--------------------------"
            )

            self.exmbclient_object.cvoperations.cleanup()
            self.log.info(
                "--------------------------READING MAILBOX PROPERTIES AFTER RESTORE"
                "----------------------------------"
            )

            after_restore_object = self.exmbclient_object.exchange_lib
            after_restore_object.get_mailbox_prop()

            self.log.info(
                "--------------------------VALIDATING CLEANUP"
                "-----------------------------------"
            )

            cleanup = self.exmbclient_object.cleanup
            cleanup.validate_journal_delete(before_backup_object.mailbox_prop,
                                            after_restore_object.mailbox_prop)

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED
