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
from Application.Exchange.ExchangeMailbox.contentstore_helper import ContentStore
from Application.Exchange.ExchangeMailbox.constants import (
    JOURNAL_POLICY_DEFAULT
)


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of ContentStore Backup,
    Cleanup and restore to Disk"""

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
        self._client = None
        self.mailboxes_list = None
        self.testdata = None
        self._subclient = None
        self.name = "Basic acceptance test of ContentStore backup, cleanup and restore"
        self.show_to_user = True
        self.exmbclient_object = None
        self.configuration_policies = None
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
            "ContentStoreServer": None,
            "RestorePath": None
        }

    def setup(self):
        """Setup function of this test case"""

        self.log.info('Creating Exchange Mailbox client object.')
        self.exmbclient_object = ExchangeMailbox(self)
        client = self.exmbclient_object.commcell.clients.get(self.exmbclient_object.server_name)
        client.start_service("GxImapServer(Instance001)")
        self.log.info(
            "--------------------------TEST DATA-----------------------------------"
        )
        self.testdata = TestData(self.exmbclient_object)

        self.mailboxes_list = self.testdata.import_data_contentstore_mailbox()
        display_names = []
        for mailbox in self.mailboxes_list:
            display_names.append(mailbox['displayName'])
        self.exmbclient_object.users = display_names

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self._subclient = self.exmbclient_object.cvoperations.subclient
        journal_policy_default = JOURNAL_POLICY_DEFAULT % self.id
        self.journal_policy = self.exmbclient_object.cvoperations.add_exchange_plan(
            journal_policy_default, 'ExchangeJournal')

    def run(self):
        """Run function of this test case"""
        try:
            subclient_content = {
                'mailboxNames': self.mailboxes_list,
                'contentStoreClients': [self.exmbclient_object.content_store_mail_server],
                'plan_name': self.journal_policy.plan_name,
                'plan_id':  self.journal_policy.plan_id
            }

            self.log.info(
                "--------------------------CREATE CONTENTSTORE MAILBOX---------------------"
            )
            self._subclient.set_contentstore_assocaition(subclient_content, False)

            self.log.info(
                "--------------------------READING MAILBOX PROPERTIES BEFORE BACKUP"
                "-----------------------------------"
            )

            before_backup_object = ContentStore(self.exmbclient_object)
            item_count = before_backup_object.get_mailbox_properties()  # Read properties of eml files in each folder
            before_backup_object.get_folder_status()      # Read backup status of each folder in master db
            expected_total_folders_to_archive = item_count[0]
            expected_total_messages_to_archive = item_count[1]

            self.log.info("Total messages count to be archived: %s", expected_total_messages_to_archive)

            self.log.info(
                "--------------------------RUNNING BACKUP-----------------------------------"
            )

            backup_job = self.exmbclient_object.cvoperations.run_backup(False)

            response = backup_job.advanced_job_details(backup_job.ADVANCED_JOB_DETAILS.BKUP_INFO)

            successful_messages_job_count = 0
            failed_messages_job_count = 0

            if 'bkpInfo' in response:
                if response['bkpInfo']:
                    advanced_details = response['bkpInfo']['exchMbInfo']
                    items_jobdetails = advanced_details['SourceMailboxStats']

                    for item in items_jobdetails:
                        successful_messages_job_count = successful_messages_job_count+item['SuccessfulMessages']
                        failed_messages_job_count = failed_messages_job_count + item['FailedMessages']
                else:
                    raise Exception('Job Details is empty')

            total_messages_job_details = successful_messages_job_count+failed_messages_job_count

            self.log.info("Job details- successful message count: %s", successful_messages_job_count)
            self.log.info("Job details- failed message count: %s", failed_messages_job_count)
            self.log.info("Job details- Total message count: %s", total_messages_job_details)

            if expected_total_messages_to_archive != total_messages_job_details:
                raise Exception("Not all messages are backedup. Mismatch with count in job details")

            # Verify messageinfo db in each folder after backup. each item which had archive status must have backup
            # status: true
            backedup_item_count = before_backup_object.verify_datfile()

            total_folders_archived = backedup_item_count[0]
            total_messages_archived = backedup_item_count[1]

            if expected_total_folders_to_archive != total_folders_archived:
                raise Exception("Not all folders are backedup")

            if expected_total_messages_to_archive!=total_messages_archived:
                raise Exception("Not all messages are backedup")

            before_cleanup_object = ContentStore(self.exmbclient_object)
            before_cleanup_object.get_folder_status()

            self.log.info(
                "--------------------------RUNNING CLEANUP-----------------------------------"
            )
            self.exmbclient_object.cvoperations.cleanup()
            folders_cleanedup = before_cleanup_object.verify_after_cleanup()
            if folders_cleanedup != total_folders_archived:
                raise Exception("Not all folders are cleaned up after archive")

            before_backup_object.delete_restore_data()

            self.log.info(
                "--------------------------RUNNING RESTORE-----------------------------------"
            )

            self.exmbclient_object.cvoperations.disk_restore(
                self.tcinputs['RestorePath'],
                self.exmbclient_object.content_store_mail_server
                )

            self.log.info(
                "--------------------------READING MAILBOX PROPERTIES AFTER RESTORE"
                "-----------------------------------"
            )

            after_restore_object = ContentStore(self.exmbclient_object)

            restore_item_count = after_restore_object.get_mailbox_properties(self.tcinputs['RestorePath'])

            self.log.info ("Total items restored is %s", restore_item_count[1])

            if restore_item_count[1] == total_messages_archived:
                self.log.info("All the messages are restored")
            elif restore_item_count[1]+failed_messages_job_count == total_messages_archived:
                # this case is for failed items. count doesn't match if there are failed items
                raise Exception("Not all messages are restored. "
                                "Count doesn't match even after including failed items count."
                                " Failing the test case")

            restore = self.exmbclient_object.restore
            restore.validate_contentstore_restore_to_disk(
                before_backup_object.mailbox_prop,
                after_restore_object.mailbox_prop)

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED
