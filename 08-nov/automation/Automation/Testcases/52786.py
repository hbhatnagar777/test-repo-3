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
    ARCHIVE_POLICY_DEFAULT,
    CLEANUP_POLICY_DEFAULT,
    RETENTION_POLICY_DEFAULT
)


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Exchange Hybrid Group and user discovery"""

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
        self.name = ("Exchange hybrid configuration with Exchange server configuration - "
                     "Disocvery operations")
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
            "EnvironmentType": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.exmbclient_object = ExchangeMailbox(self)

        self.log.info(
            "--------------------------TEST DATA-----------------------------------"
        )

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self._subclient = self.exmbclient_object.cvoperations.subclient
        archive_policy_default = ARCHIVE_POLICY_DEFAULT % self.id
        cleanup_policy_default = CLEANUP_POLICY_DEFAULT % self.id
        retention_policy_default = RETENTION_POLICY_DEFAULT % self.id

        archive_policy_object = self.exmbclient_object.cvoperations.get_policy_object(
            archive_policy_default, "Archive")
        self.archive_policy = self.exmbclient_object.cvoperations.add_exchange_policy(
            archive_policy_object)
        self.cleanup_policy = self.exmbclient_object.cvoperations.add_exchange_policy(
            self.exmbclient_object.cvoperations.get_policy_object(
                cleanup_policy_default, "Cleanup"))
        self.retention_policy = self.exmbclient_object.cvoperations.add_exchange_policy(
            self.exmbclient_object.cvoperations.get_policy_object(
                retention_policy_default, "Retention"))

    def run(self):
        """Run function of this test case"""
        try:

            o365_content = {
                'archive_policy': self.archive_policy,
                'cleanup_policy': self.cleanup_policy
            }
            self.log.info(
                "--------------------------VALIDATE USER DISCOVERY"
                "-----------------------------------"
            )
            active_directory = self.exmbclient_object.active_directory
            active_directory.validate_user_discovery()

            mailboxes_list = []
            for mailbox in self._subclient.discover_users:
                mailboxes_list.append(mailbox['aliasName'])
            subclient_content = {
                'mailboxNames': mailboxes_list,
                'archive_policy': self.archive_policy,
                'cleanup_policy': self.cleanup_policy,
                'retention_policy': self.retention_policy,
            }

            self.log.info(
                "--------------------------CREATE USER ASSOCAITION AND VALIDATE"
                "-----------------------------------"
            )

            active_directory.set_user_assocaitions(subclient_content)
            active_directory.validate_user_assocaition(subclient_content)

            self.log.info(
                "--------------------------DELETE USER ASSOCAITION"
                "-----------------------------------"
            )
            active_directory.delete_user_assocaitions(subclient_content)

            self.log.info(
                "--------------------------GET O365 GROUPS"
                "-----------------------------------"
            )

            testdata = TestData(self.exmbclient_object)
            group_details = testdata.get_o365_groups()

            self.log.info(
                "--------------------------CREATE GROUP ASSOCAITION AND VALIDATE"
                "-----------------------------------"
            )
            active_directory.set_o365group_asscoiations(o365_content)
            active_directory.validate_o365group_association(group_details, o365_content)

            self.log.info(
                "--------------------------DELETE GROUP ASSOCAITION"
                "-----------------------------------"
            )
            active_directory.delete_o365group_associations(o365_content)

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED