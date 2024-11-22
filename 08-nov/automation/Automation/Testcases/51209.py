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
import copy
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from Application.Exchange.ExchangeMailbox.constants import (
    CLEANUP_POLICY_DEFAULT_DELETE,
    CLEANUP_POLICY_DELETE_OLDER_THAN,
    CLEANUP_POLICY_DELETE_LARGER_THAN,
    CLEANUP_POLICY_DELETE_SKIP_UNREAD_MESSAGE,
    CLEANUP_POLICY_DELETE_HAS_ATTACHMENTS
)


class TestCase(CVTestCase):
    """Class for executing and verifying Exchange Cleanup using multiple
     Cleanup Policies with 'Delete Messages' option enabled"""

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

                log     (object)    --  Object of the logger module

        """
        super(TestCase, self).__init__()
        self.name = "Exchange Mailbox Agent : Cleanup (Delete Messages) Operation and Validation"
        self.show_to_user = True
        self.mailboxes_list = []
        self.cleanup_policies_list = []
        self.subclient_content_list = []
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
            "RecallService": None,
            "EnvironmentType": None
        }

    def setup(self):
        """Setup function of this test case"""

        self.log.info('Creating Exchange Mailbox client object.')
        self.exmbclient_object = ExchangeMailbox(self)

        self.log.info(
            "--------------------------TEST DATA CREATION-----------------------------------"
        )
        testdata = TestData(self.exmbclient_object)
        self.mailboxes_list = testdata.create_mailbox()
        self.smtp_list = testdata.import_pst()
        # List of mailboxes
        self.exmbclient_object.users = self.smtp_list

        # Creating Exchange Client
        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self._subclient = self.exmbclient_object.cvoperations.subclient
        ewsURL = self.tcinputs.get("EWSServiceURL", None)
        if ewsURL:
            self.exmbclient_object.cvoperations.enableEWSSupport(service_url=ewsURL)
        cleanup_policy_delete_default = CLEANUP_POLICY_DEFAULT_DELETE % self.id
        cleanup_policy_delete_older_than = CLEANUP_POLICY_DELETE_OLDER_THAN % self.id
        cleanup_policy_delete_larger_than = CLEANUP_POLICY_DELETE_LARGER_THAN % self.id
        cleanup_policy_delete_skip_unread_message = CLEANUP_POLICY_DELETE_SKIP_UNREAD_MESSAGE % self.id
        cleanup_policy_delete_has_attachments = CLEANUP_POLICY_DELETE_HAS_ATTACHMENTS % self.id

        cleanup_policy_delete_default_obj = self.exmbclient_object.cvoperations.add_exchange_plan(
            plan_name=cleanup_policy_delete_default, create_stubs=False)
        self.cleanup_policies_list.append(cleanup_policy_delete_default_obj)
        cleanup_policy_delete_older_than_obj = self.exmbclient_object.cvoperations.add_exchange_plan(
            plan_name=cleanup_policy_delete_older_than, cleanup_msg_older_than=30, create_stubs = False)
        self.cleanup_policies_list.append(cleanup_policy_delete_older_than_obj)
        cleanup_policy_delete_larger_than_obj = self.exmbclient_object.cvoperations.add_exchange_plan(
            plan_name=cleanup_policy_delete_larger_than, cleanup_msg_larger_than=10, create_stubs=False)
        self.cleanup_policies_list.append(cleanup_policy_delete_larger_than_obj)
        cleanup_policy_delete_skip_unread_message_obj = self.exmbclient_object.cvoperations.add_exchange_plan(
            plan_name=cleanup_policy_delete_skip_unread_message, create_stubs=False, skip_unread_msgs=True)
        self.cleanup_policies_list.append(cleanup_policy_delete_skip_unread_message_obj)
        cleanup_policy_delete_has_attachments_obj = self.exmbclient_object.cvoperations.add_exchange_plan(
            plan_name=cleanup_policy_delete_has_attachments, collect_msg_with_attach=True, create_stubs=False)
        self.cleanup_policies_list.append(cleanup_policy_delete_has_attachments_obj)

    def run(self):
        """Run function of this test case"""
        try:

            self.log.info("Creating subclient contents with mailbox names and its associated "
                          "Exchange Configuration Policies")

            for iterator in range(0, len(self.cleanup_policies_list)):
                subclient_content = {
                    'mailboxNames': [self.mailboxes_list[iterator]],
                    'is_auto_discover_user': True,
                    'plan_name': self.cleanup_policies_list[iterator].plan_name
                }
                self.subclient_content_list.append(subclient_content)

            self.log.info(
                "--------------------------CREATE USER ASSOCIATION"
                "-----------------------------------"
            )
            self.log.info("Creating active_directory object")
            active_directory = self.exmbclient_object.active_directory

            for iterator in range(0, len(self.cleanup_policies_list)):
                self.log.info("User association for Mailbox name: %s",
                              self.subclient_content_list[iterator]['mailboxNames'])
                active_directory.set_user_assocaitions(
                    self.subclient_content_list[iterator], False)

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
                "--------------------------RUNNING CLEANUP"
                "-----------------------------------"
            )

            self.exmbclient_object.cvoperations.cleanup()

            self.log.info(
                "--------------------------READING MAILBOX PROPERTIES AFTER CLEANUP"
                "-----------------------------------"
            )

            after_cleanup_object = self.exmbclient_object.exchange_lib
            after_cleanup_object.get_mailbox_prop()

            cleanup = self.exmbclient_object.cleanup
            cleanup.compare_mailbox_prop_cleanup(before_backup_object.mailbox_prop,
                                                 after_cleanup_object.mailbox_prop,
                                                 delete=True)
        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED
