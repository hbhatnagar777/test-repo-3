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
from Application.Exchange.ExchangeMailbox.constants import ARCHIVE_POLICY_DEFAULT

from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.data_generation import TestData


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Exchange Online with
    OnPremise AD Backup and restore"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name            (str)       --  name of this test case

                applicable_os   (str)       --  applicable os for this test case
                    Ex: self.os_list.WINDOWS

                product         (str)       --  applicable product for this test case
                    Ex: self.products_list.FILESYSTEM

                features        (str)       --  qcconstants feature_list item
                    Ex: self.features_list.DATAPROTECTION

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
        self.name = "Basic acceptance test of Exchange Online with OnPremise AD Backup and restore"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.EXCHANGEMB
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.mailboxes_list = []
        self.smtp_list = []
        self.exmbclient_object = None
        self.configuration_policies = None
        self.tcinputs = {
            "MailboxList": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.log.info('Creating Exchange Mailbox client object.')
        self.exmbclient_object = ExchangeMailbox(self)
        self.mailboxes_list = [mbx.lower().replace("@" + self.exmbclient_object.domain_name.lower(),
                                                   "") for mbx in self.tcinputs["MailboxList"]]
        self.smtp_list = self.tcinputs["MailboxList"]
        self.log.info(
            "--------------------------TEST DATA-----------------------------------"
        )
        self.log.info("Mailbox List: %s" % self.mailboxes_list)
        self.log.info("SMTP List: %s" % self.smtp_list)

        self.testdata = TestData(self.exmbclient_object)
        self.mailboxes_list = self.testdata.create_online_mailbox()
        self.smtp_list = self.testdata.send_email_online_mailbox()

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self._subclient = self.exmbclient_object.cvoperations.subclient

        archive_policy_default = ARCHIVE_POLICY_DEFAULT % (self.id)

        self.archive_policy = self.exmbclient_object.cvoperations.add_exchange_policy(
            self.exmbclient_object.cvoperations.get_policy_object(
                archive_policy_default, "Archive"))

    def run(self):
        """Run function of this test case"""
        try:

            self.exmbclient_object.users = self.smtp_list
            subclient_content = {
                'mailboxNames': self.mailboxes_list,
                'archive_policy': self.archive_policy,
            }

            self.log.info(
                "--------------------CREATE USER ASSOCAITION---------------------------"
            )
            active_directory = self.exmbclient_object.active_directory
            active_directory.set_user_assocaitions(subclient_content)

            self.log.info(
                "----------------------RUNNING BACKUP--------------------------"
            )
            b_job = self.exmbclient_object.cvoperations.run_backup()
            before_backup_cnt = int(b_job.summary['totalNumOfFiles'])

            self.log.info(
                "--------------------------RUNNING RESTORE"
                "-----------------------------------"
            )

            r_job = self.exmbclient_object.cvoperations.run_restore()
            details = r_job.details
            after_restore_cnt = int(details['jobDetail']['detailInfo']['numOfObjects'])

            if after_restore_cnt != before_backup_cnt:
                self.log.info("Before Backup Count: %d, After restore count: %d" % (before_backup_cnt,
                                                                                    after_restore_cnt))
                raise Exception("Backup and restore count do not match")
            self.log.info(
                "--------------------------VERIFIED COUNT %d, %d"
                "-----------------------------------" % (before_backup_cnt, after_restore_cnt)
            )


        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            self.result_string = str(ex)
            self.status = constants.FAILED
