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
from Application.Exchange.ExchangeMailbox.constants import OFFICE_365_PLAN_ATTACHMENTS, OpType
from Application.Exchange.ExchangeMailbox.constants import OFFICE_365_PLAN_DEFAULT
from Application.Exchange.ExchangeMailbox.constants import OFFICE_365_PLAN_LARGER_THAN
from Application.Exchange.ExchangeMailbox.constants import OFFICE_365_PLAN_OLDER_THAN
from Application.Exchange.ExchangeMailbox.data_generation import TestData


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Exchange online archive job with
    archive rules

    Example for test case inputs:
        "53113":
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
        self.office_365_plan_msg_larger_than = None
        self.office_365_plan_msg_older_than = None
        self.office_365_plan_attachments = None
        self.office_365_plan_default = None
        self.plan_helper = None
        self.name = "Basic acceptance test of Exchange Online archive job with archive rules"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.EXCHANGEMB
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.mailboxes_list = []
        self.smtp_list = []
        self.exmbclient_object = None
        self.configuration_policies = None
        self.tcinputs = {
            "DomainName": "example.com"
        }

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

        self.log.info("Mailbox List: %s" % self.mailboxes_list)
        self.log.info("SMTP List: %s" % self.smtp_list)

        self.exmbclient_object.users = self.smtp_list

        self.log.info("Populating mailboxes:{} with emails".format(self.smtp_list))
        self.exmbclient_object.exchange_lib.send_email(
            mailbox_list=self.smtp_list)
        self.log.info("Populated the mailboxes with emails")

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self._subclient = self.exmbclient_object.cvoperations.subclient

        office_365_plan_default = OFFICE_365_PLAN_DEFAULT % (self.id)
        office_365_plan_attachments = OFFICE_365_PLAN_ATTACHMENTS % (self.id)
        office_365_plan_msg_larger_than = OFFICE_365_PLAN_LARGER_THAN % (self.id)
        office_365_plan_msg_older_than = OFFICE_365_PLAN_OLDER_THAN % (self.id)

        self.log.info("Creating office 365 plan")
        self.office_365_plan_default = Office365Plan(self.commcell, office_365_plan_default)
        self.log.info("Done creating office 365 plan")

        self.log.info("Creating office 365 plan with attachments enabled")
        self.office_365_plan_attachments = Office365Plan(self.commcell, office_365_plan_attachments)
        self.office_365_plan_attachments.enable_backup_attachments()
        self.log.info("Done creating Office 365 Plan with attachments enabled")

        self.log.info("Creating office 365 plan with including messages older than 30 days")
        self.office_365_plan_msg_older_than = Office365Plan(self.commcell,office_365_plan_msg_older_than)
        self.office_365_plan_msg_older_than.include_messages_older_than(30)
        self.log.info("Done creating Office 365 Plan with including messages older than 30 days")

        self.log.info("Creating office 365 plan with including messages larger than 10 KB")
        self.office_365_plan_msg_larger_than = Office365Plan(self.commcell, office_365_plan_msg_larger_than)
        self.office_365_plan_msg_larger_than.include_messages_larger_than(10)
        self.log.info("Done creating Office 365 Plan with including messages larger than 10 KB")
        
    def run(self):
        """Run function of this test case"""
        try:
            subclient_content_1 = {
                'mailboxNames': [self.mailboxes_list[0], self.mailboxes_list[1]],
                'plan_name': self.office_365_plan_default.plan_name,
            }
            subclient_content_2 = {
                'mailboxNames': [self.mailboxes_list[2], self.mailboxes_list[3]],
                'plan_name': self.office_365_plan_attachments.plan_name,
            }
            subclient_content_3 = {
                'mailboxNames': [self.mailboxes_list[4], self.mailboxes_list[5]],
                'plan_name': self.office_365_plan_msg_larger_than.plan_name,
            }
            subclient_content_4 = {
                'mailboxNames': [self.mailboxes_list[6], self.mailboxes_list[7]],
                'plan_name': self.office_365_plan_msg_older_than.plan_name,
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
                "--------------------------CREATED USER ASSOCAITION"
                "-----------------------------------"
            )

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
            b_job = self.exmbclient_object.cvoperations.run_backup()
            before_backup_cnt = int(b_job.summary['totalNumOfFiles'])

            self.log.info(
                "--------------------------RUNNING CLEANUP"
                "-----------------------------------"
            )

            self.exmbclient_object.exchange_lib.cleanup_mailboxes(mailbox_list=self.smtp_list)

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
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            self.result_string = str(ex)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function for the Test Case"""
        self.testdata.delete_online_mailboxes(mailboxes_list=self.smtp_list)
        # Cleaning Up the mailboxes created: to not see Azure sync issue in next run
