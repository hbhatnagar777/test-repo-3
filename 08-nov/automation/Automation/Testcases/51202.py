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
    ARCHIVE_POLICY_DEFAULT
)
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper


class TestCase(CVTestCase):
    """Exchange mailbox: Verify retention policy"""

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
        self._subclient = None
        self._client = None
        self.name = "Exchange mailbox: Verify retention policy"
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
        self.archive_policy_default = None
        self.number_of_days = 365

    def setup(self):
        """Setup function of this test case"""
        self.exmbclient_object = ExchangeMailbox(self)
        self.log.info(
            "--------------------------TEST DATA-----------------------------------"
        )

        test_data = TestData(self.exmbclient_object)
        self.mailboxes_list = test_data.create_mailbox()

        self.smtp_list = test_data.import_pst()
        self.exmbclient_object.users = self.smtp_list

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self._subclient = self.exmbclient_object.cvoperations.subclient
        ewsURL = self.tcinputs.get("EWSServiceURL", None)
        if ewsURL:
            self.exmbclient_object.cvoperations.enableEWSSupport(service_url=ewsURL)
        archive_policy_default = ARCHIVE_POLICY_DEFAULT % self.id
        self.archive_policy_default = self.exmbclient_object.cvoperations.add_exchange_plan(
            archive_policy_default, retain_msgs_deletion_time=self.number_of_days)

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info(
                "-----------------------CREATE USER ASSOCIATION-----------------------")
            subclient_content1 = {
                'mailboxNames': self.mailboxes_list,
                'plan_name': self.archive_policy_default.plan_name
            }
            active_directory = self.exmbclient_object.active_directory
            active_directory.set_user_assocaitions(subclient_content1, False)
            self.log.info(
                "---------------------------RUNNING BACKUP-----------------------------")
            self.exmbclient_object.cvoperations.run_backup()
            solr = SolrHelper(self.exmbclient_object)
            self.log.info(
                "-----------------------Validating Retention------------------------")

            solr._validate_retention(self.number_of_days)

        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            self.result_string = str(ex)
            self.status = constants.FAILED
