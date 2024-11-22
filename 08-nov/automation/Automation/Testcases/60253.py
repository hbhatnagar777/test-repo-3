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
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.constants import (CLEANUP_POLICY_DEFAULT,
                                                            ARCHIVE_POLICY_DEFAULT,
                                                            RETENTION_POLICY_DEFAULT,
                                                            AD_MAILBOX_MONITORING_EXE)
from Application.Exchange.exchangepowershell_helper import ExchangePowerShell
from Application.Exchange.ExchangeMailbox.activedirectory_helper import *
from cvpysdk.subclients.exchange.usermailbox_subclient import UsermailboxSubclient
from Application.Exchange.ExchangeMailbox.exchangecsdb_helper import *


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Association and De-association validation for O365 group mailboxes, AD group and All Users in Exchange Online"
        self.archive_policy_object = None
        self.cleanup_policy_object = None
        self.retention_policy_object = None
        self.machine_object = None
        self.tcinputs = {
        }


    def setup(self):
        """Setup function of this test case"""
        self.exchangeMailObject = ExchangeMailbox(self)
        self._client = self.exchangeMailObject.cvoperations.add_exchange_client()
        self.log.info("Added the exchange client")
        
        self._backupset = self.exchangeMailObject.cvoperations.backupset
        self._subclient = UsermailboxSubclient(backupset_object=self.backupset,
                                               subclient_name=self.tcinputs["SubclientName"])
        self.log.info("Subclient association completed")

        archive_policy = ARCHIVE_POLICY_DEFAULT % (self.id)
        cleanup_policy = CLEANUP_POLICY_DEFAULT % (self.id)
        retention_policy = RETENTION_POLICY_DEFAULT % (self.id)

        self.archive_policy_object = self.exchangeMailObject.cvoperations.add_exchange_policy(
            policy_object=self.exchangeMailObject.cvoperations.get_policy_object(policy_name=archive_policy,policy_type="Archive"))
        self.cleanup_policy_object = self.exchangeMailObject.cvoperations.add_exchange_policy(
            policy_object=self.exchangeMailObject.cvoperations.get_policy_object(policy_name=cleanup_policy,policy_type="Cleanup"))
        self.retention_policy_object = self.exchangeMailObject.cvoperations.add_exchange_policy(
            policy_object=self.exchangeMailObject.cvoperations.get_policy_object(policy_name=retention_policy,policy_type="Retention"))

        self.machine_object = Machine(
            machine_name=self.tcinputs["ProxyServerDetails"]["IpAddress"],
            commcell_object=self.exchangeMailObject.commcell,
            username=self.tcinputs["ProxyServerDetails"]["Username"],
            password=self.tcinputs["ProxyServerDetails"]["Password"]
        )
        
        self.activedirectory = self.exchangeMailObject.active_directory
        self.log.info("Defined the active directory constructor")
        self.powershell_object = ExchangePowerShell(
            ex_object=self.exchangeMailObject,
            exchange_server=None,
            cas_server_name=None,
            exchange_adminname=self.exchangeMailObject.exchange_online_user,
            exchange_adminpwd=self.exchangeMailObject.exchange_online_password,
            server_name=self.exchangeMailObject.server_name
        )
        self.log.info("Created a powershell object")

    def run(self):
        """Run function of this test case"""
        try:
            adgroupcontent = {
                "adGroupNames": [self.tcinputs["GroupName"]],
                "is_auto_discover_user": True,
                "archive_policy": self.archive_policy_object,
                "cleanup_policy": self.cleanup_policy_object,
                "retention_policy": self.retention_policy_object,
            }
            alluserscontent = {
                "is_auto_discover_user": True,
                "archive_policy": self.archive_policy_object,
                "cleanup_policy": self.cleanup_policy_object,
                "retention_policy": self.retention_policy_object,
            }
            o365groupcontent = {
                "archive_policy": self.archive_policy_object,
                "cleanup_policy": self.cleanup_policy_object,
                "retention_policy": self.retention_policy_object,
            }
            self.log.info("Refreshing the subclient")
            self._subclient.refresh()
            self.log.info("------------------------------------------"
                          "Starting the all O365 group mailbox associations"
                          "------------------------------------------")
            o365groups = self._subclient.discover_adgroups
            o365list = []
            self.log.info("Discovered groups {0}".format(o365groups))
            for o365group in o365groups:
                self.log.info("Group mailbox discovered {0}".format(o365group))
                o365list.append(o365group["adGroupName"].lower())
            self.log.info("------------------------------------------"
                          "Discovery over"
                          "------------------------------------------")
            self.log.info("------------------------------------------"
                          "Associating O365 group"
                          "------------------------------------------")
            self._subclient.set_o365group_asscoiations(subclient_content=o365groupcontent)
            self.log.info("-------------------------------------------"
                          "Associated O365 group"
                          "-------------------------------------------")
            smtpaddresses = []
            for x in self._subclient.o365groups:
                self.log.info("O365 group associated {0}".format(x["display_name"]))
                smtpaddresses.append(x["smtp_address"])
            self.log.info("---------------------------------------------"
                          "Validating the association"
                          "---------------------------------------------")

            self.activedirectory.validate_o365group_association(o365group_dict=o365list,
                                                                subclient_content=o365groupcontent)
            self.log.info("---------------------------------------------"
                          "Validated the association"
                          "---------------------------------------------")
            self.log.info("------------------------------------------"
                          "Deleting the o365 group mailbox association"
                          "------------------------------------------")
            self._subclient.delete_auto_discover_association(association_name="All O365 group mailboxes",
                                                             subclient_content=o365groupcontent)
            self.log.info("------------------------------------------"
                          "Deleted the o365 group mailbox association"
                          "------------------------------------------")
            self.log.info("------------------------------------------"
                          "Validating the deletion by using Commserve CSdb"
                          "------------------------------------------")

            for smtpadress in smtpaddresses:
                check = self.exchangeMailObject.csdb_helper.check_deleted_flag_set(mailbox_smtp_address=smtpadress)
                if check:
                    self.log.info("Mailbox {0} is deleted".format(smtpadress))
                else:
                    self.log.info("Mailbox {0} is not deleted".format(smtpadress))
                    raise Exception("Mailbox not yet deleted")
            smtpaddresses.clear()
            self.log.info("-----------------------------------------"
                          "Validation over of deletion"
                          "-----------------------------------------")
            self.log.info("-----------------------------------------"
                          "Refreshing the Subclient"
                          "-----------------------------------------")
            self._subclient.refresh()
            self.log.info("-----------------------------------------"
                          "Refreshed the Subclient"
                          "-----------------------------------------")

            self.log.info("------------------------------------------"
                          "Starting the adgroup association"
                          "------------------------------------------")

            self.log.info("----------------------------------------"
                          "Starting the discovery of the groups"
                          "----------------------------------------")

            groups = self._subclient.discover_adgroups
            for group in groups:
                self.log.info("Groups discovered %s", group)

            self.log.info("-----------------------------------------"
                          "Discovery of the groups ended"
                          "-----------------------------------------")

            self.log.info("Group to be associated is %s", self.tcinputs["GroupName"])

            self.log.info("-----------------------------------------"
                          "Associating the group"
                          "-----------------------------------------")
            self._subclient.set_adgroup_associations(subclient_content=adgroupcontent)

            group = self._subclient.adgroups

            self.log.info("Group associated {0}".format(group[0]["adgroup_name"]))

            users = self.subclient.users
            for user in users:
                self.log.info("User associated {0} {1}".format(user["display_name"], user["smtp_address"]))
                smtpaddresses.append(user["smtp_address"])

            self.log.info("-----------------------------------------"
                          "Groups association Over"
                          "-----------------------------------------")

            self.log.info("------------------------------------------"
                          "Validating the users in the group"
                          "------------------------------------------")

            self.activedirectory.validate_users_in_group(subclient_content=adgroupcontent)

            self.log.info("------------------------------------------"
                          "Validated the users in the group"
                          "------------------------------------------")

            self.log.info("------------------------------------------"
                          "De-associating the group"
                          "------------------------------------------")

            self._subclient.delete_adgroup_assocaition(subclient_content=adgroupcontent)

            self.log.info("------------------------------------------"
                          "De-associated the group"
                          "------------------------------------------")

            self.log.info("------------------------------------------"
                          "Validating the deletion by using CSdb"
                          "------------------------------------------")

            for smtpadress in smtpaddresses:
                check = self.exchangeMailObject.csdb_helper.check_deleted_flag_set(mailbox_smtp_address=smtpadress)
                if check:
                    self.log.info("Mailbox {0} is deleted".format(smtpadress))
                else:
                    self.log.info("Mailbox {0} is not deleted".format(smtpadress))
                    raise Exception("Mailbox not yet deleted")
            smtpaddresses.clear()

            self.log.info("-----------------------------------------"
                          "Validation over of deletion"
                          "-----------------------------------------")

            self.log.info("------------------------------------------"
                          "Starting the all user mailbox associations"
                          "------------------------------------------")

            self.log.info("---------------------------------------------"
                          "Associating all user and group mailboxes"
                          "---------------------------------------------")

            self._subclient.enable_allusers_associations(subclient_content=alluserscontent)
            users = self._subclient.users
            o365list = []
            for user in users:
                self.log.info("User Mailbox associated {0},{1}".format(user["display_name"], user["smtp_address"]))
                smtpaddresses.append(user["smtp_address"])

            groupmailboxes = self._subclient.o365groups
            for groupmailbox in groupmailboxes:
                self.log.info("Group Mailbox associated {0}".format(groupmailbox))
                o365list.append(groupmailbox["alias_name"].lower())
                smtpaddresses.append(groupmailbox["smtp_address"])

            self.log.info("---------------------------------------------"
                          "Associated all the users"
                          "---------------------------------------------")

            self.log.info("---------------------------------------------"
                          "          Validating the association         "
                          "---------------------------------------------")
            self.activedirectory.validate_allusers_assocaition(subclient_content=alluserscontent)
            self.activedirectory.validate_o365group_association(o365group_dict=o365list,
                                                                subclient_content=alluserscontent)
            self.log.info("------------------------------------------"
                          "  Validated all user and group mailboxes  "
                          "------------------------------------------")

            self.log.info("------------------------------------------"
                          "Deleting the user association"
                          "------------------------------------------")

            self._subclient.delete_auto_discover_association(association_name="All Users",
                                                             subclient_content=alluserscontent)

            self.log.info("------------------------------------------"
                          "Done Deleting the user association"
                          "------------------------------------------")

            self.log.info("------------------------------------------"
                          "Validating the deletion by using Commserve CSdb"
                          "------------------------------------------")

            for smtpadress in smtpaddresses:
                check = self.exchangeMailObject.csdb_helper.check_deleted_flag_set(mailbox_smtp_address=smtpadress)
                if check:
                    self.log.info("Mailbox {0} is deleted".format(smtpadress))
                else:
                    self.log.info("Mailbox {0} is not deleted".format(smtpadress))
                    raise Exception("Mailbox not yet deleted")

            self.log.info("-----------------------------------------"
                          "Validation over of deletion"
                          "-----------------------------------------")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("-----------------------------------------"
                      "Deleting the Client"
                      "-----------------------------------------")
        self.commcell.clients.delete(self.client.client_name)
        self.log.info("-----------------------------------------"
                      "Deleted the Client"
                      "-----------------------------------------")