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
        self.name = "Different Types of Groups Discovery"
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
        self._subclient = self.exchangeMailObject.cvoperations.subclient
        self.log.info("Associated Subclient")
        archive_policy = ARCHIVE_POLICY_DEFAULT % (self.id)
        cleanup_policy = CLEANUP_POLICY_DEFAULT % (self.id)
        retention_policy = RETENTION_POLICY_DEFAULT % (self.id)
        self.archive_policy_object = self.exchangeMailObject.cvoperations.add_exchange_policy(
            policy_object=self.exchangeMailObject.cvoperations.get_policy_object(policy_name=archive_policy,
                                                                                 policy_type="Archive"))
        self.cleanup_policy_object = self.exchangeMailObject.cvoperations.add_exchange_policy(
            policy_object=self.exchangeMailObject.cvoperations.get_policy_object(policy_name=cleanup_policy,
                                                                                 policy_type="Cleanup"))
        self.retention_policy_object = self.exchangeMailObject.cvoperations.add_exchange_policy(
            policy_object=self.exchangeMailObject.cvoperations.get_policy_object(policy_name=retention_policy,
                                                                                 policy_type="Retention"))
        self.machine_object = Machine(
            machine_name=self.tcinputs["ProxyServerDetails"]["IpAddress"],
            commcell_object=self.exchangeMailObject.commcell,
            username=self.tcinputs["ProxyServerDetails"]["Username"],
            password=self.tcinputs["ProxyServerDetails"]["Password"]
        )
        self.activedirectoryobject = self.exchangeMailObject.active_directory
        self.powershell_object = ExchangePowerShell(
            ex_object=self.exchangeMailObject,
            exchange_server=None,
            cas_server_name=None,
            exchange_adminname=self.exchangeMailObject.exchange_online_user,
            exchange_adminpwd=self.exchangeMailObject.exchange_online_password,
            server_name=self.exchangeMailObject.server_name
        )
        self.DistributionGroups = self.powershell_object.get_online_groups(group_type="Distribution List")
        self.MailEnabledSecurityGroups = self.powershell_object.get_online_groups(group_type="Mail Enabled Security Group")
        self.Microsoft365Groups = self.powershell_object.get_online_groups(group_type="Microsoft 365")

    def run(self):
        """Run function of this test case"""
        try:
            distributiongroupcontent = {
                "adGroupNames": self.DistributionGroups,
                "is_auto_discover_user": True,
                "archive_policy": self.archive_policy_object,
                "cleanup_policy": self.cleanup_policy_object,
                "retention_policy": self.retention_policy_object,
            }
            mailenabledsecuritygroupcontent = {
                "adGroupNames": self.MailEnabledSecurityGroups,
                "is_auto_discover_user": True,
                "archive_policy": self.archive_policy_object,
                "cleanup_policy": self.cleanup_policy_object,
                "retention_policy": self.retention_policy_object,
            }
            o365groupcontent = {
                "adGroupNames": self.Microsoft365Groups,
                "is_auto_discover_user": True,
                "archive_policy": self.archive_policy_object,
                "cleanup_policy": self.cleanup_policy_object,
                "retention_policy": self.retention_policy_object,
            }
            self.log.info("Refreshing the subclient")
            self._subclient.refresh()
            self.log.info("----------------------------------------"
                          "Starting the discovery of the groups"
                          "----------------------------------------")
            groups=self._subclient.discover_adgroups
            for group in groups:
                self.log.info("Group discovered {0}".format(group["adGroupName"]))
            self.log.info("-----------------------------------------"
                          "Discovery of the groups ended"
                          "-----------------------------------------")
            self.log.info("-----------------------------------------"
                          "Validating the groups discovery"
                          "-----------------------------------------")
            self.activedirectoryobject.validate_ad_discovery()
            self.log.info("-----------------------------------------"
                          "Validated the groups discovery"
                          "-----------------------------------------")
            self.log.info("-----------------------------------------"
                          "Distribution List Groups Alias Names"
                          "-----------------------------------------")
            for distributiongroup in self.DistributionGroups:
                self.log.info("{0}".format(distributiongroup))
                
            self.log.info("-----------------------------------------"
                          "Mail Enabled Security Groups Alias Names"
                          "-----------------------------------------")
            for mailenabledgroup in self.MailEnabledSecurityGroups:
                self.log.info("{0}".format(mailenabledgroup))
                
            self.log.info("-----------------------------------------"
                          "Office 365 Groups Alias Names"
                          "-----------------------------------------")
            for office365group in self.Microsoft365Groups:
                self.log.info("{0}".format(office365group))

            self.log.info("-----------------------------------------"
                          "Associating mail enabled security group"
                          "-----------------------------------------")
            self._subclient.set_adgroup_associations(distributiongroupcontent)
            self.log.info("-----------------------------------------"
                          "Groups association Over"
                          "-----------------------------------------")
            self.log.info("------------------------------------------"
                          "Validating associations"
                          "------------------------------------------")
            self.activedirectoryobject.validate_adgroup_assocaition(distributiongroupcontent)
            self.log.info("------------------------------------------"
                          "Validated associations"
                          "------------------------------------------")
            self.log.info("------------------------------------------"
                          "Deassociation of the group starting"
                          "------------------------------------------")
            self._subclient.delete_adgroup_assocaition(distributiongroupcontent)
            self.log.info("------------------------------------------"
                          "Deassociation of the group ended"
                          "------------------------------------------")
            self.log.info("-------------------------------------------"
                          "Associating mailenabled security groups"
                          "-------------------------------------------")
            self._subclient.set_adgroup_associations(mailenabledsecuritygroupcontent)
            self.log.info("---------------------------------------------"
                          "Associated the mailenabled security group"
                          "---------------------------------------------")
            self.log.info("---------------------------------------------"
                          "Validating the mailenabledsecuriy association"
                          "---------------------------------------------")
            self.activedirectoryobject.validate_adgroup_assocaition(mailenabledsecuritygroupcontent)
            self.log.info("------------------------------------------"
                          "  Validated the mailenabledsecurity mailboxes  "
                          "------------------------------------------")
            self.log.info("------------------------------------------"
                          "Deleting association"
                          "------------------------------------------")
            self._subclient.delete_adgroup_assocaition(mailenabledsecuritygroupcontent)
            self.log.info("------------------------------------------"
                          "Done Deleting association"
                          "------------------------------------------")
            self.log.info("------------------------------------------"
                          "Associating O365 group"
                          "------------------------------------------")
            self._subclient.set_adgroup_associations(o365groupcontent)
            self.log.info("-------------------------------------------"
                          "Associated O365 group"
                          "-------------------------------------------")
            self.log.info("---------------------------------------------"
                          "Validating the association"
                          "---------------------------------------------")
            self.activedirectoryobject.validate_adgroup_assocaition(o365groupcontent)
            self.log.info("---------------------------------------------"
                          "Validated the association"
                          "---------------------------------------------")
            self.log.info("------------------------------------------"
                          "Deleting association"
                          "------------------------------------------")
            self._subclient.delete_adgroup_assocaition(o365groupcontent)
            self.log.info("------------------------------------------"
                          "Done Deleting association"
                          "------------------------------------------")

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