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
import Application.Exchange.ExchangeMailbox.utils as exmb_utils
from Application.Exchange.exchangepowershell_helper import ExchangePowerShell
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Exchange online Backup and restore

            Example for test case inputs:
        "59218":
        {
        "ClientName":<name of client>
        "AgentName": "Exchange Mailbox",
        "InstanceName": "defaultInstanceName",
        "BackupsetName": "User Mailbox",
        "ProxyServers": [
          <proxy server name>
        ],
        "EnvironmentType":4,
        "StoragePolicyName":"Exchange Plan",
        "SubClientName":"usermailbox",
        "PlanName": "<Plan-name>>",
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

                mailboxes_list          (list)     --   List of Alias Name
        """
        super(TestCase, self).__init__()
        self.name = "Exchange Hybrid Type 3 GUID Verification"
        self.show_to_user = True
        self.archive_policy = None
        self.mailboxes_list = list()
        self.smtp_list = list()
        self.exmbclient_object = None
        self.powershell = None
        self.migrated_users = list()
        self.online_users = list()
        self.on_prem_powershell = None
        self.proxy_machine = None
        self.tcinputs = {
            "SubclientName": None,
            "BackupsetName": None,
            "IndexServer": None,
        }

    def setup(self):
        """Setup function of this test case"""
        self.log.info('Creating Exchange Mailbox client object.')
        self.exmbclient_object = ExchangeMailbox(self)
        self.log.info(
            "--------------------------TEST DATA-----------------------------------"
        )

        self.migrated_users = self.tcinputs["MigratedUsers"]
        self.online_users = self.tcinputs["OnlineUsers"]
        self.mailboxes_list = list()

        self.mailboxes_list.extend(self.migrated_users)
        self.mailboxes_list.extend(self.online_users)
        self.log.info("Mailboxes List: {}".format(self.mailboxes_list))

        self.exmbclient_object.client_name = self.client.client_name

        self.powershell = ExchangePowerShell(ex_object=self.exmbclient_object, cas_server_name=None,
                                             exchange_server=None,
                                             exchange_adminname=self.exmbclient_object.exchange_online_user,
                                             exchange_adminpwd=self.exmbclient_object.exchange_online_password,
                                             server_name=self.exmbclient_object.server_name,
                                             domain_name=self.tcinputs["OnlineDomainName"])

        self.on_prem_powershell = ExchangePowerShell(ex_object=self.exmbclient_object, cas_server_name=None,
                                                     exchange_server=None,
                                                     exchange_adminname=self.exmbclient_object.service_account_user,
                                                     exchange_adminpwd=self.exmbclient_object.service_account_password,
                                                     server_name=self.exmbclient_object.server_name,
                                                     domain_name=self.exmbclient_object.domain_name)

    def run(self):
        """Run function of this test case"""
        try:

            if not exmb_utils.is_mailbox_cache_valid(self.exmbclient_object):
                self.log.info("Mailbox cache is not latest one")
                raise Exception("Mailbox cache is outdated, check if any error in discovery")

            self.log.info(
                "-----------------------CREATE USER ASSOCIATION-----------------------")
            subclient_content = {
                'mailboxNames': self.mailboxes_list,
                'plan_name': self.tcinputs["ExchangePlan"]
            }

            self.subclient.set_user_assocaition(subclient_content, use_policies=False)

            self.log.info(
                "-----------------------VERIFYING GUID for MIGRATED USERS"
                "-------------------------------")
            migrated_users_guid = self.exmbclient_object.csdb_helper.get_mailbox_guid(mailbox_list=self.migrated_users)
            self.log.info("GUID from CSDB: {}".format(migrated_users_guid))

            migrates_users_ad_guid = self.on_prem_powershell.get_mailbox_guid(mailbox_list=self.migrated_users,
                                                                              environment="OnPrem")
            self.log.info("GUID from AD: {}".format(migrates_users_ad_guid))

            _discv_status = exmb_utils.verify_mailbox_guids_association(migrates_users_ad_guid.values(),
                                                                        migrated_users_guid.values())
            self.log.info("GUID verification for Migrated users: {}".format(_discv_status))

            if not _discv_status:
                self.log.error("Migrated Users GUID did not match")
                raise Exception("Migrated Users GUIDs did not match")

            self.log.info(
                "-----------------------VERIFYING GUID for ONLINE CREATED USERS"
                "-------------------------------")
            online_users_guid = self.exmbclient_object.csdb_helper.get_mailbox_guid(mailbox_list=self.online_users)
            self.log.info("GUID from CSDB: {}".format(online_users_guid))

            online_users_ad_guid = self.powershell.get_mailbox_guid(mailbox_list=self.online_users,
                                                                    environment="AzureAD")
            self.log.info("GUID from AD: {}".format(online_users_ad_guid))

            _discv_status = exmb_utils.verify_mailbox_guids_association(online_users_guid.values(),
                                                                        online_users_ad_guid.values())
            self.log.info("GUID verification for Online created users: {}".format(_discv_status))

            if not _discv_status:
                self.log.error("Online Created Users GUID did not match")
                raise Exception("Online Created Users GUIDs did not match")

            self.log.info("Removing Mailbox Association")
            self.subclient.delete_user_assocaition(subclient_content)

            self.subclient.refresh()
            # Discovery for next run

            self.log.info('Test Case completed!!!')

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s',
                           type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED
