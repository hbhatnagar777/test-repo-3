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
    ARCHIVE_POLICY_DELETED_ITEM_REETENTION_ENABLED,
    ARCHIVE_POLICY_DEFAULT
)


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of O365 deleted item retention"""

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
        self.name = "Office365 backups- Deleted item retention Basics (recoverable items)"
        self.show_to_user = True
        self.smtp_list = []
        self.mailboxes_list = []
        self.exmbclient_object = None
        self.tcinputs = {
            "SubclientName": None,
            "BackupsetName": None,
            "IndexServer": None,
            "StoragePolicyName": None,
            "DomainName": None,
            "ProxyServers": None,
            "azureAppKeyID": None,
            "azureAppKeySecret": None,
            "azureTenantName": None,
            "EnvironmentType": None,
            "ItemsInRecoverable": 0
        }

    def setup(self):
        """Setup function of this test case"""
        self.exmbclient_object = ExchangeMailbox(self)

        self.log.info(
            "--------------------------TEST DATA-----------------------------------"
        )

        """ Use this code once get_mailbox_properties start working"""
        testdata = TestData(self.exmbclient_object)
        self.mailboxes_list = testdata.create_online_mailbox()

        self.smtp_list = list()
        for mailbox in self.mailboxes_list:
            smtp = mailbox + "@" + self.tcinputs['DomainName']
            self.smtp_list.append(smtp)

        self.exmbclient_object.exchange_lib.send_email(
            mailbox_list=self.smtp_list)
        self.log.info("Populated mailboxes:{}".format(self.smtp_list))

        self.exmbclient_object.users = self.smtp_list

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self._subclient = self.exmbclient_object.cvoperations.subclient

        archive_policy_delete_items = ARCHIVE_POLICY_DELETED_ITEM_REETENTION_ENABLED % self.id
        archive_policy_delete_items_object = self.exmbclient_object.cvoperations.get_policy_object(
            archive_policy_delete_items, "Archive")
        archive_policy_delete_items_object.backup_deleted_item_retention = True
        archive_policy_delete_items_object.include_discovery_holds_folder = True
        archive_policy_delete_items_object.include_purges_folder = True
        archive_policy_delete_items_object.include_version_folder = True
        self.archive_policy_delete_items = self.exmbclient_object.cvoperations.add_exchange_policy(
            archive_policy_delete_items_object)

    def run(self):
        """Run function of this test case"""
        try:

            subclient_content = {
                'mailboxNames': self.mailboxes_list,
                'archive_policy': self.archive_policy_delete_items
            }

            self.log.info(
                "--------------------------CREATE USER ASSOCAITION"
                "-----------------------------------"
            )
            active_directory = self.exmbclient_object.active_directory
            active_directory.set_user_assocaitions(subclient_content)

            self.log.info(
                "--------------------------READING MAILBOX PROPERTIES BEFORE BACKUP"
                "-----------------------------------"
            )
            before_cleanup_object = self.exmbclient_object.exchange_lib
            before_cleanup_object.get_mailbox_prop()

            self.log.info(
                "--------------------------RUNNING BACKUP"
                "-----------------------------------"
            )
            b_job = self.exmbclient_object.cvoperations.run_backup()

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
            self.log.info(
                "--------------------------VALIDATING DELETED ITEM RETENTION"
                "-----------------------------------"
            )
            restore = self.exmbclient_object.restore
            restore.validate_delted_item_retention(before_cleanup_object.mailbox_prop,
                                                   after_restore_object.mailbox_prop)

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED