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
from Application.Exchange.ExchangeMailbox.constants import ARCHIVE_POLICY_DEFAULT
from Application.Exchange.ExchangeMailbox.constants import CLEANUP_POLICY_DEFAULT
from Application.Exchange.ExchangeMailbox.constants import RETENTION_POLICY_DEFAULT


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Exchange online with local AD
    Discovery validation"""

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
        self.name = ("Class for executing Basic acceptance test of Exchange online with "
                     "lcoal Ad Discovery validation")
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.EXCHANGEMB
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.exmbclient_object = None

    def setup(self):
        """Setup function of this test case"""

        self.log.info('Creating Exchange Mailbox client object.')
        self.exmbclient_object = ExchangeMailbox(self)

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self._subclient = self.exmbclient_object.cvoperations.subclient

        archive_policy_default = ARCHIVE_POLICY_DEFAULT % (self.id)
        cleanup_policy_default = CLEANUP_POLICY_DEFAULT % (self.id)
        retention_policy_default = RETENTION_POLICY_DEFAULT % (self.id)

        self.archive_policy = self.exmbclient_object.cvoperations.add_exchange_policy(
            self.exmbclient_object.cvoperations.get_policy_object(
                archive_policy_default, "Archive"))
        self.cleanup_policy = self.exmbclient_object.cvoperations.add_exchange_policy(
            self.exmbclient_object.cvoperations.get_policy_object(
                cleanup_policy_default, "Cleanup"))
        self.retention_policy = self.exmbclient_object.cvoperations.add_exchange_policy(
            self.exmbclient_object.cvoperations.get_policy_object(
                retention_policy_default, "Retention"))

    def run(self):
        """Run function of this test case"""
        try:

            self.log.info(
                "--------------------------VALIDATE USER DISCOVERY"
                "-----------------------------------"
            )
            active_directory = self.exmbclient_object.active_directory
            active_directory.validate_user_discovery()

            self.log.info(
                "--------------------------VALIDATE AD DISCOVERY"
                "-----------------------------------"
            )
            active_directory.validate_ad_discovery()

            mailboxes_list = []
            for mailbox in self._subclient.discover_users:
                mailboxes_list.append(mailbox['aliasName'])
            adgroup_list = []
            for group in self._subclient.discover_adgroups:
                adgroup_list.append(group['adGroupName'])

            subclient_content = {
                'mailboxNames': mailboxes_list,
                'archive_policy': self.archive_policy,
                'cleanup_policy': self.cleanup_policy,
                'retention_policy': self.retention_policy,
            }
            adgroup_content = {
                'adGroupNames': adgroup_list,
                'is_auto_discover_user': True,
                'archive_policy': self.archive_policy,
                'cleanup_policy': self.cleanup_policy,
                'retention_policy': self.retention_policy,
            }
            allusers_content = {
                'is_auto_discover_user': True,
                'archive_policy': self.archive_policy,
                'cleanup_policy': self.cleanup_policy,
                'retention_policy': self.retention_policy,
            }

            self.log.info(
                "--------------------------ENABLE ALL USER ASSOCAITION AND VALIDATE"
                "-----------------------------------"
            )

            self._subclient.enable_allusers_associations(allusers_content)
            active_directory.validate_allusers_assocaition(allusers_content)


            self.log.info(
                "--------------------------DISABLE ALL USER ASSOCAITION AND VALIDATE"
                "-----------------------------------"
            )

            self._subclient.disable_allusers_associations()

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
                "--------------------------DELETE DATABASE AND USERs ASSOCAITION"
                "-----------------------------------"
            )

            active_directory.delete_user_assocaitions(subclient_content)

            self.log.info(
                "--------------------------CREATE AD ASSOCAITION AND VALIDATE"
                "-----------------------------------"
            )

            active_directory.set_adgroup_associations(adgroup_content)
            active_directory.validate_adgroup_assocaition(adgroup_content)
            active_directory.validate_users_in_group(adgroup_content)

        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            self.result_string = str(ex)
            self.status = constants.FAILED
