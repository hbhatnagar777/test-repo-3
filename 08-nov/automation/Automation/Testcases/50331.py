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
    CLEANUP_POLICY_PRUNING_MESSAGES,
    CLEANUP_POLICY_PRUNING_STUBS
)


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Exchange
    User Mailbox Onpremise Cleanup with Souce Prunning combinations"""

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
        self.cleanup_policy_message_plan = None
        self.cleanup_policy_stubs_plan = None
        self._subclient = None
        self._client = None
        self.name = "Basic acceptance test of Clean up with Source Pruning combinations"
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
        self.cleanup_policy_message_plan = None
        self.cleanup_policy_stubs_plan = None

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

        self.cleanup_policy_message_plan = self.exmbclient_object.cvoperations.add_exchange_plan(
            CLEANUP_POLICY_PRUNING_MESSAGES % self.id, prune_msgs=True
        )
        self.cleanup_policy_stubs_plan = self.exmbclient_object.cvoperations.add_exchange_plan(
            CLEANUP_POLICY_PRUNING_STUBS % self.id, prune_stubs=True)

    def run(self):
        """Run function of this test case"""
        try:

            subclient_content_1 = {
                'mailboxNames': [self.mailboxes_list[0]],
                'plan_name': self.cleanup_policy_message_plan.plan_name
            }

            subclient_content_2 = {
                'mailboxNames': [self.mailboxes_list[1]],
                'plan_name': self.cleanup_policy_stubs_plan.plan_name
            }

            self.log.info(
                "--------------------------CREATE USER ASSOCAITION"
                "-----------------------------------"
            )
            active_directory = self.exmbclient_object.active_directory

            active_directory.set_user_assocaitions(subclient_content_1, False)

            active_directory.set_user_assocaitions(subclient_content_2, False)

            self.log.info(
                "--------------------------READING MAILBOX PROPERTIES BEFORE CLEANUP"
                "-----------------------------------"
            )

            before_cleanup_object = self.exmbclient_object.exchange_lib
            before_cleanup_object.get_mailbox_prop()

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

            self.log.info(
                "------------------VALIDATING SOURCE PRUNING"
                "-----------------------------------"
            )

            cleanup = self.exmbclient_object.cleanup
            cleanup.validate_source_pruning(before_cleanup_object.mailbox_prop,
                                            after_cleanup_object.mailbox_prop)

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED
