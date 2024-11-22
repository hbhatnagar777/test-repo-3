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
from Application.Office365.Office365Plan import Office365Plan
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants

from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from Application.Exchange.ExchangeMailbox.constants import OFFICE_365_PLAN_DEFAULT
from Application.Exchange.ExchangeMailbox.constants import RETENTION_POLICY_DEFAULT
from Application.Exchange.ExchangeMailbox.constants import DELETE_RETENTION_POLICY_DEFAULT
from Application.Exchange.ExchangeMailbox.constants import DELETE_MESSAGE_COUNT
from Application.Exchange.ExchangeMailbox.trueup_helper import TrueUp


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Exchange online trueup job with
    deletion based retention policy"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name            (str)       --  name of this test case

                applicable_os   (str)       --  applicable os for this test case
                    Ex: self.os_list.WINDOWS

                product         (str)       --  applicable product for this test case
                    Ex: self.products_list.EXCHANGEMB

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
        self.name = ("Basic acceptance test of Exchange Online true up job with deletion based"
                     " retention policy")
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.EXCHANGEMB
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.mailboxes_list = []
        self.smtp_list = []
        self.exmbclient_object = None
        self.office_365_plan = None
        self.archive_policy_default = None
        self.retention_policy_default = None
        self.delete_retention_policy_default = None

    def setup(self):
        """Setup function of this test case"""

        self.log.info('Creating Exchange Mailbox client object.')
        self.exmbclient_object = ExchangeMailbox(self)
        self.log.info(
            "--------------------------TEST DATA-----------------------------------"
        )
        self.testdata = TestData(self.exmbclient_object)
        self.mailboxes_list = self.testdata.create_online_mailbox()

        self.smtp_list = list()
        for mailbox in self.mailboxes_list:
            smtp = mailbox + "@" + self.tcinputs['DomainName']
            self.smtp_list.append(smtp)

        self.exmbclient_object.exchange_lib.send_email(mailbox_list=self.smtp_list)
        self.exmbclient_object.users = self.smtp_list

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self._subclient = self.exmbclient_object.cvoperations.subclient
        office365_plan_default = OFFICE_365_PLAN_DEFAULT % self.id
        self.office_365_plan = Office365Plan(self.commcell, office365_plan_default)
        self.office_365_plan.enable_content_indexing()
        self.office_365_plan.enable_backup_deleted_item_retention()
        self.office_365_plan.update_retention_days(numOfDaysForMediaPruning=0)

    def run(self):
        """Run function of this test case"""
        try:

            subclient_content_1 = {
                'mailboxNames': [self.mailboxes_list[0], self.mailboxes_list[2]],
                'plan_name': self.office_365_plan.plan_name
            }
            subclient_content_2 = {
                'mailboxNames': [self.mailboxes_list[1], self.mailboxes_list[3]],
                'plan_name': self.office_365_plan.plan_name
            }

            self.log.info(
                "--------------------------CREATE USER ASSOCAITION"
                "-----------------------------------"
            )
            active_directory = self.exmbclient_object.active_directory
            active_directory.set_user_assocaitions(subclient_content_1,False)
            active_directory.set_user_assocaitions(subclient_content_2,False)

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
                "--------------------------DELETING MESSAGES"
                "-----------------------------------"
            )
            trueup_object = self.exmbclient_object.exchange_lib
            trueup_object = trueup_object.delete_items_from_cv_well_known_folders(
                self.exmbclient_object.users, DELETE_MESSAGE_COUNT)

            self.log.info(
                "--------------------------RUNNING AdMailboxMonitor"
                "-----------------------------------"
            )
            self.exmbclient_object.cvoperations.run_admailbox_monitor()

            self.log.info(
                "--------------------------RUNNING TrueUp"
                "-----------------------------------"
            )
            true_up = TrueUp(self.exmbclient_object)
            true_up.wait_for_sync_process_to_exit()
            self.log.info("Sync process exited")

            true_up.validate_true_up(trueup_object)
            self.log.info("True Up Validated")

            true_up.validate_deletion_time_based_retention(before_backup_object.mailbox_prop)

        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            self.result_string = str(ex)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function for the Test Case"""
        self.testdata.delete_online_mailboxes(mailboxes_list=self.smtp_list)
        # Cleaning Up the mailboxes created: to not see Azure sync issue in next run
