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
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.constants import ARCHIVE_POLICY_DEFAULT, DELETE_RETENTION_POLICY_DEFAULT, \
    OpType
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from Application.Exchange.ExchangeMailbox.trueup_helper import TrueUp


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Exchange online Backup and restore

            Example for test case inputs:
        "59076":
        {

        "AgentName": "Exchange Mailbox",
        "InstanceName": "defaultInstanceName",
        "BackupsetName": "User Mailbox",
        "ProxyServers": [
          <proxy server name>
        ],
        "EnvironmentType":4,
        "StoragePolicyName":"Exchange Plan",
        "IndexServer":"<index-server name>",
        "GroupName":"<name-of-group-to-be-discovered>",
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

                archive_policy         (object)    --  Object of Configuration policy to be used to associate the group
                retention_policy       (object)    --  Object of Configuration policy to be used to associate the group

                testdata               (object)    --  Object of Test Data class

                smtp_list               (list)     --   SMTP list of users
                mailboxes_list          (list)     --   List of Alias Name
        """
        super(TestCase, self).__init__()
        self.name = "Exchange Online Point in Time Recovery Test"
        self.show_to_user = True
        self.archive_policy = None
        self.mailboxes_list = list()
        self.smtp_list = list()
        self.exmbclient_object = None
        self.testdata = None
        self.retention_policy = None
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

        self._client = self.exmbclient_object.cvoperations.add_exchange_client(
        )
        self.log.info("Client creation successful")
        self._subclient = self.exmbclient_object.cvoperations.subclient
        self.log.info('Associated the SubClient')

        self.exmbclient_object.exchange_lib.send_email(mailbox_list=self.smtp_list)
        self.log.info('Populated the mailbox')

        archive_policy_default = ARCHIVE_POLICY_DEFAULT % self.id

        self.archive_policy = self.exmbclient_object.cvoperations.add_exchange_policy(
            self.exmbclient_object.cvoperations.get_policy_object(
                archive_policy_default, "Archive"))

        delete_retention_policy_default = DELETE_RETENTION_POLICY_DEFAULT % self.id
        delete_retention_policy_object = self.exmbclient_object.cvoperations.get_policy_object(
            delete_retention_policy_default, "Retention")
        delete_retention_policy_object.retention_type = 1
        delete_retention_policy_object.days_for_media_pruning = 1
        self.retention_policy = (
            self.exmbclient_object.cvoperations.add_exchange_policy(
                delete_retention_policy_object))

    def run(self):
        """Run function of this test case"""
        try:

            self.exmbclient_object.users = self.smtp_list

            self.log.info(
                "-----------------------CREATE USER ASSOCIATION-----------------------")
            subclient_content = {
                'mailboxNames': [self.mailboxes_list[0]],
                'archive_policy': self.archive_policy,
                'retention_policy': self.retention_policy
            }
            active_directory = self.exmbclient_object.active_directory
            active_directory.set_user_assocaitions(subclient_content)

            self.log.info(
                "--------------------------READING MAILBOX PROPERTIES BEFORE BACKUP"
                "-----------------------------------")

            initial_mailbox_object = self.exmbclient_object.exchange_lib
            initial_mailbox_object.get_mailbox_prop()

            self.log.info(
                "---------------------------RUNNING BACKUP-----------------------------")
            first_backup_job = self.exmbclient_object.cvoperations.run_backup()

            self.log.info(
                "------------------MODIFYING THE SUBJECT OF THE MAILS-------------------")
            mailbox_object_second = self.exmbclient_object.exchange_lib
            mailbox_object_second.modify_subject(mailbox_name=self.smtp_list[0])
            mailbox_object_second.get_mailbox_prop()

            self.log.info(
                "---------------------------RUNNING ANOTHER BACKUP-----------------------------")
            second_backup_job = self.exmbclient_object.cvoperations.run_backup()

            self.log.info(
                "---------------------------RUNNING ANOTHER BACKUP-----------------------------")
            third_backup_job = self.exmbclient_object.cvoperations.run_backup()

            self.log.info(
                "---------------------------RUNNING INCREMENTAL BACKUP CHECK-----------------------------")
            _job_items = self.exmbclient_object.csdb_helper.get_number_of_items_for_backup_job(third_backup_job.job_id)

            if _job_items != 0:
                self.log.info("Incremental backup job check failed, "
                              "as expected item count for the third backup job is 0")
                self.log.info("Backup job Item Count: {}".format(_job_items))
                raise Exception("Incremental backup job  check failed.")

            self.log.info(
                "------------------------DELETING SOME ITEMS FROM THE FOLDER-----------------------")
            self.exmbclient_object.exchange_lib.delete_mailbox_content(
                mailbox_name=self.smtp_list[0])

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

            self.log.info(
                "-------------TrueUp Completed- Proceeding with PIT Restore"
                "-----------------------------------"
            )

            self.log.info('Performing restore pre- requisites')

            mailbox_guid_dict = self.exmbclient_object.csdb_helper.get_mailbox_guid(
                mailbox_list=self.mailboxes_list)
            mailbox_guid = mailbox_guid_dict[self.mailboxes_list[0].lower()]

            self.log.info('Mailbox GUID found in DB: {}'.format(mailbox_guid))
            restore_path = "\\MB\\{" + mailbox_guid + "}"
            self.log.info('Restore path for mailbox: {}'.format(restore_path))

            self.log.info('Starting with Recovery Point creation')

            recovery_point_second = self.exmbclient_object.cvoperations.create_restore_point(
                mailbox_alias=self.mailboxes_list[0], b_job=second_backup_job)
            self.exmbclient_object.cvoperations.run_restore(
                paths=[restore_path], recovery_point_id=recovery_point_second)

            self.log.info('Restore Job Completed')
            self.log.info("Proceeding to read the mailbox properties")

            after_first_restore_prop = self.exmbclient_object.exchange_lib
            after_first_restore_prop.get_mailbox_prop()

            self.log.info('Fetched the mailbox properties')
            self.log.info(
                'These must match with the mailbox state between the first and second backup job')

            first_restore = self.exmbclient_object.restore

            first_restore.compare_mailbox_prop(op_type=OpType.OVERWRITE,
                                               before_backup=mailbox_object_second.mailbox_prop,
                                               after_restore=after_first_restore_prop.mailbox_prop)

            self.log.info('Restore Point creation validated')
            self.log.info('Successfully undone the changes made by the delete and true up job')

            self.log.info('Creating the Second Recovery Point')
            # self.testdata.clean_online_mailbox_contents()

            recovery_point_first = self.exmbclient_object.cvoperations.create_restore_point(
                mailbox_alias=self.mailboxes_list[0], b_job=first_backup_job)
            self.log.info('Recovery Point created with ID: {}'.format(recovery_point_first))

            self.exmbclient_object.cvoperations.run_restore(
                paths=[restore_path], recovery_point_id=recovery_point_first)

            self.log.info('Restore job completed')
            self.log.info('Getting the mailbox properties again')

            after_second_restore_prop = self.exmbclient_object.exchange_lib
            after_second_restore_prop.get_mailbox_prop()

            self.log.info('Comparing the mailbox properties now')

            second_restore = self.exmbclient_object.restore

            second_restore.compare_mailbox_prop(
                op_type=OpType.OVERWRITE,
                before_backup=initial_mailbox_object.mailbox_prop,
                after_restore=after_second_restore_prop.mailbox_prop)

            self.log.info('Mailbox has been restored to the initial state')

            self.log.info('TC Run completed!!!')

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s',
                           type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED

    def tear_down(self):
        """
            Tear down function for the Test Case
        """
        try:
            if self.status == constants.PASSED:
                self.commcell.clients.delete(self.client.client_name)
                self.log.info("Client Deleted")
        finally:
            self.log.info("Test Case Completed")
