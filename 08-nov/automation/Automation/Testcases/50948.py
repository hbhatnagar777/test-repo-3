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
    ARCHIVE_POLICY_LARGER_THAN,
    ARCHIVE_POLICY_OLDER_THAN,
    ARCHIVE_POLICY_DEFAULT
)


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Exchange
    User Mailbox Onpremise backup and restore"""

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
        self.name = "Basic acceptance test of Exchange Onpremise backup and restore"
        self.show_to_user = True
        self.smtp_list = []
        self.mailboxes_list = []
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
            "EnvironmentType": None
        }
        self.archive_policy_attachments = None
        self.archive_policy_default = None
        self.archive_policy_msg_older_than = None
        self.archive_policy_msg_larger_than = None

    def setup(self):
        """Setup function of this test case"""
        self.exmbclient_object = ExchangeMailbox(self)
        self.log.info(
            "--------------------------TEST DATA-----------------------------------"
        )

        testdata = TestData(self.exmbclient_object)

        self.mailboxes_list = testdata.create_mailbox()
        self.smtp_list = testdata.import_pst()
        self.exmbclient_object.users = self.smtp_list

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self._subclient = self.exmbclient_object.cvoperations.subclient
        ewsURL = self.tcinputs.get("EWSServiceURL", None)
        if ewsURL:
            self.exmbclient_object.cvoperations.enableEWSSupport(service_url=ewsURL)
        archive_policy_default = ARCHIVE_POLICY_DEFAULT % self.id
        archive_policy_attachments = ARCHIVE_POLICY_ATTACHMENTS % self.id
        archive_policy_msg_larger_than = ARCHIVE_POLICY_LARGER_THAN % self.id
        archive_policy_msg_older_than = ARCHIVE_POLICY_OLDER_THAN % self.id
        self.archive_policy_default = self.exmbclient_object.cvoperations.add_exchange_plan(
            plan_name=archive_policy_default)
        self.archive_policy_attachments = self.exmbclient_object.cvoperations.add_exchange_plan(
            plan_name=archive_policy_attachments, include_only_msgs_with_attachemts=True)
        self.archive_policy_msg_older_than = self.exmbclient_object.cvoperations.add_exchange_plan(
            plan_name=archive_policy_msg_older_than, include_msgs_older_than=30)
        self.archive_policy_msg_larger_than = self.exmbclient_object.cvoperations.add_exchange_plan(
            plan_name=archive_policy_msg_larger_than, include_msgs_larger_than=10)

    def run(self):
        """Run function of this test case"""
        try:

            subclient_content_1 = {
                'mailboxNames': [self.mailboxes_list[0], self.mailboxes_list[1]],
                'plan_name': self.archive_policy_default.plan_name
            }
            subclient_content_2 = {
                'mailboxNames': [self.mailboxes_list[2], self.mailboxes_list[3]],
                'plan_name': self.archive_policy_attachments.plan_name
            }
            subclient_content_3 = {
                'mailboxNames': [self.mailboxes_list[4], self.mailboxes_list[5]],
                'plan_name': self.archive_policy_msg_larger_than.plan_name
            }
            subclient_content_4 = {
                'mailboxNames': [self.mailboxes_list[6], self.mailboxes_list[7]],
                'plan_name': self.archive_policy_msg_older_than.plan_name
            }

            self.log.info(
                "--------------------------CREATE USER ASSOCAITION"
                "-----------------------------------"
            )
            active_directory = self.exmbclient_object.active_directory

            active_directory.set_user_assocaitions(subclient_content_1, False)

            active_directory.set_user_assocaitions(subclient_content_2, False)

            active_directory.set_user_assocaitions(subclient_content_3, False)

            active_directory.set_user_assocaitions(subclient_content_4, False)

            self.log.info(
                "--------------------------READING MAILBOX PROPERTIES BEFORE BACKUP"
                "-----------------------------------"
            )

            before_backup_object = self.exmbclient_object.exchange_lib
            before_backup_object.get_mailbox_prop()

            self.log.info(
                "--------------------------RUNNING BACKUP"
                "-----------------------------------"
            )
            self.exmbclient_object.cvoperations.run_backup()

            self.log.info(
                "--------------------------RUNNING RESTORE"
                "-----------------------------------"
            )

            self.exmbclient_object.cvoperations.run_restore()
            self.log.info(
                "--------------------------READING MAILBOX PROPERTIES AFTER RESTORE"
                "-----------------------------------"
            )

            after_restore_object = self.exmbclient_object.exchange_lib
            after_restore_object.get_mailbox_prop()

            restore = self.exmbclient_object.restore
            restore.compare_mailbox_prop(OpType.OVERWRITE,
                                         before_backup_object.mailbox_prop,
                                         after_restore_object.mailbox_prop)

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED
