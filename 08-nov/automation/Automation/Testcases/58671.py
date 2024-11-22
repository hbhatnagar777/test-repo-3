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

import time
from Application.Office365.Office365Plan import Office365Plan
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.exchangepowershell_helper import ExchangePowerShell
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from Application.Exchange.ExchangeMailbox.constants import (
    OFFICE_365_PLAN_DEFAULT,
    AD_MAILBOX_MONITORING_EXE)
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing test case of discovery, association
    and disassociation of Exchange Online Mailbox Mailboxes

        Example for test case inputs:
        "58761":
        {

        "AgentName": "Exchange Mailbox",
        "InstanceName": "defaultInstanceName",
        "BackupsetName": "User Mailbox",
        "ProxyServers": [
          <proxy server name>
        ],
        "EnvironmentType":4,
        "RecallService":"",
        "StoragePolicyName":"Exchange Plan",
        "IndexServer":"<index-server name>",
        "DomainName": <exchange-online-domain-name>
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
        ],
        "IDADetails":
          {
            "Name": "<Name-of-exchange-IDA-Machine>",
            "IpAddress": "<IP Address-of-Exchange-IDA-Machine>",
            "Username": "<Username-Of-Exchange-IDA>",
            "Password": "<Password-Of-Exchange-IDA>"
          }

      }
      """
    test_step = TestStep()

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

                exmbclient_object      (object)     --  Object of ExchangeMailbox class

                archive_policy         (object)     --  Object of Configuration policy to be used to associate the group
                cleanup_policy         (object)     --  Object of Configuration policy to be used to associate the group

                lower_retention_policy  (object)    --  Object of Configuration policy with lower retention to
                                                            be used to associate the group
                higher_retention_policy (object)    --  Object of Configuration policy with higher retention to
                                                            be used to associate the AD Group

                machine                (object)     --  Object of Machine class for the iDA machine

                smtp_list              (list)       --   List of mailbox SMTPs
                mailboxes_list          (list)      -- List of mailboxes
                group_list              (list)      --  List of Office 365 Groups

                testdata                (Object)    --  Object of Test Data class

        """
        super(TestCase, self).__init__()
        self.name = "Basic Mailbox Discovery, Association and Disassociation test case for Exchange Online"
        self.show_to_user = True
        self.product = self.products_list.EXCHANGEMB
        self.exmbclient_object = None
        self.archive_policy = None
        self.cleanup_policy = None
        self.higher_retention_policy = None
        self.lower_retention_policy = None
        self.query = None
        self.tcinputs = {}
        self.machine = None
        self.testdata = None
        self.ex_powershell = None
        self.plan_helper = None
        self.office365_plan = None
        self.office365_low_retention_plan = None
        self.office365_high_retention_plan = None
        self.smtp_list = list()
        self.mailboxes_list = list()
        self.group_list = list()

    @test_step
    def verify_display_name_update(self):
        """
            Verify that display name update is being reflected by discpvery
            Modifying Display Name for a User and checking discovery
        """
        _new_name = self.exmbclient_object.graph_helper.update_user(user_upn=self.smtp_list[1],
                                                                    properrty="DISPLAY-NAME")
        self.log.info(f"Updated Display name for user: {self.smtp_list[1]} to: {_new_name}")

        self.exmbclient_object.cvoperations.run_admailbox_monitor()
        self.machine.wait_for_process_to_exit(
            process_name=AD_MAILBOX_MONITORING_EXE)
        self.log.info('AD Mailbox Discovery process completed successfully')
        self.subclient.refresh()

        _db_display_name = self.exmbclient_object.csdb_helper.get_attr_for_mailbox(property_name='displayName',
                                                                                   mailbox_smtp_address=self.smtp_list[
                                                                                       1])
        self.log.info("DisplayName from the CSDB: {}".format(_db_display_name))
        assert _db_display_name == _new_name

    @test_step
    def verify_manual_user_deletion(self):
        """
            Deleting Manually Associated Mailbox and Verifying its Removal from Content
        """
        self.log.info('Deleting the mailbox {} on Exchange'.format(
            self.smtp_list[5]))
        self.exmbclient_object.graph_helper.delete_azure_ad_user(user_upn=self.smtp_list[5])
        self.log.info('Deleted Mailbox')
        time.sleep(30)  # For the changes to reflect on the Exchange/ Azure AD

        self.exmbclient_object.cvoperations.run_admailbox_monitor()
        self.machine.wait_for_process_to_exit(
            process_name=AD_MAILBOX_MONITORING_EXE)
        self.log.info('AD Mailbox Discovery process completed successfully')
        self.subclient.refresh()

        mailbox_deleted_flag = self.exmbclient_object.csdb_helper.check_deleted_flag_set(
            mailbox_smtp_address=self.smtp_list[5])
        if not mailbox_deleted_flag:
            self.log.error('Mailbox is in the list of associated mailboxes')
            self.log.error(
                'Mailbox: {} should not be in the list of associated mailboxes'
                .format(self.smtp_list[5]))
            raise Exception('Mailbox Deletion unsuccessful')

        self.log.info('Mailbox is not in the list of discovered mailboxes')
        self.log.info(
            'Manually associated mailbox, deleted from Azure is removed by ad mailbox monitor from subclient')

    def setup(self):
        """Setup Function for the Test Case"""
        self.exmbclient_object = ExchangeMailbox(self)

        self.log.info('Creating TestData using PowerShell')
        self.testdata = TestData(self.exmbclient_object)

        self.mailboxes_list = self.testdata.create_online_mailbox()

        self.manual_assoc_mailboxes = self.testdata.create_online_mailbox(count=2, use_json=False)

        for mailbox in self.mailboxes_list:
            smtp = mailbox + "@" + self.tcinputs['DomainName']
            self.smtp_list.append(smtp)

        for mailbox in self.manual_assoc_mailboxes:
            smtp = mailbox + "@" + self.tcinputs['DomainName']
            self.smtp_list.append(smtp)

        self.log.info("Mailbox List: %s" % self.mailboxes_list)
        self.log.info("SMTP List: %s" % self.smtp_list)

        self.log.info("Manual Association Mailboxes: {}".format(self.manual_assoc_mailboxes))

        self.log.info('Created Mailboxes for Test Case')

        self.log.info('Creating Office 365 Groups')
        self.group_list = self.testdata.create_o365_group()
        self.log.info('Groups Created: {}'.format(self.group_list))

        self.log.info('Initializing Exchange PowerShell and Machine objects')
        self.ex_powershell = ExchangePowerShell(
            ex_object=self.exmbclient_object,
            cas_server_name=None,
            exchange_server=None,
            exchange_adminname=self.exmbclient_object.exchange_online_user,
            exchange_adminpwd=self.exmbclient_object.exchange_online_password,
            server_name=self.exmbclient_object.server_name)

        self.machine = machine.Machine(
            machine_name=self.tcinputs["ProxyServerDetails"]["IpAddress"],
            commcell_object=self.exmbclient_object.commcell,
            username=self.tcinputs["ProxyServerDetails"]["Username"],
            password=self.tcinputs["ProxyServerDetails"]["Password"])
        self.log.info('Initialized Exchange PowerShell and Machine objects')

        time.sleep(
            30
        )  # For the changes made by PowerShell to reflect on the Azure AD/ Exchange Online

        self._client = self.exmbclient_object.cvoperations.add_exchange_client(
        )
        self.log.info('Created Exchange Online Client')
        self._subclient = self.exmbclient_object.cvoperations.subclient
        self.log.info('Associated Exchange Online Sub Client')
        office365_plan = OFFICE_365_PLAN_DEFAULT % self.id
        office365_low_retention_plan = OFFICE_365_PLAN_DEFAULT % ("Lower_Retention"+self.id)
        office365_high_retention_plan = OFFICE_365_PLAN_DEFAULT % ("Higher_Retention"+self.id)
        self.log.info("Creating Office 365 plan {}".format(office365_plan))
        self.office365_plan = Office365Plan(self.commcell, office365_plan)
        self.log.info("Created Office 365 plan successfully")

        self.log.info("Creating Office 365 plan {}".format(office365_low_retention_plan))
        self.office365_low_retention_plan = Office365Plan(self.commcell, office365_low_retention_plan)
        self.log.info("Created Office 365 plan successfully")
        self.log.info("Setting a lower retention on plan {}".format(office365_low_retention_plan))
        self.office365_low_retention_plan.update_retention_days(numOfDaysForMediaPruning=1)
        self.log.info("Initialized a retention of {} day on plan {}".format(1, office365_low_retention_plan))

        self.log.info("Creating Office 365 plan {}".format(office365_high_retention_plan))
        self.office365_high_retention_plan = Office365Plan(self.commcell, office365_high_retention_plan)
        self.log.info("Created Office 365 plan successfully")
        self.log.info("Setting a higher retention on plan {}".format(office365_high_retention_plan))
        self.office365_high_retention_plan.update_retention_days(numOfDaysForMediaPruning=10)
        self.log.info("Initialized a retention of {} days on plan {}".format(10, office365_high_retention_plan))

    def run(self):
        """Run Function for the Test Case"""
        o365_content = {
            'adGroupNames': [self.group_list[0]],
            'is_auto_discover_user': True,
            'plan_name': self.office365_low_retention_plan.plan_name,
            'plan_object': self.office365_low_retention_plan
        }
        self.machine.wait_for_process_to_exit(
            process_name=AD_MAILBOX_MONITORING_EXE)

        self.log.info(
            "--------------------------CREATE GROUP ASSOCIATION WITH LOWER RETENTION"
            "-----------------------------------")

        active_directory = self.exmbclient_object.active_directory
        active_directory.set_adgroup_associations(subclient_content=o365_content, use_policies=False)
        active_directory.validate_adgroup_assocaition(
            subclient_content=o365_content)

        self.log.info("--------------------------"
                      "ASSOCIATING O365 GROUP AND VALIDATING "
                      "AUTODISCOVER USER ASSOCIATION WITH HIGHER RETENTION"
                      "-----------------------------------")
        o365_content = {
            'adGroupNames': [self.group_list[1]],
            'is_auto_discover_user': True,
            'plan_name': self.office365_high_retention_plan.plan_name,
            'plan_object': self.office365_high_retention_plan
        }

        active_directory.set_adgroup_associations(subclient_content=o365_content,use_policies=False)

        self.log.info('Group Associated')

        subclient_content = {
            'mailboxNames': self.manual_assoc_mailboxes,
            'plan_name': self.office365_plan.plan_name
        }

        active_directory.set_user_assocaitions(subclient_content, False)
        self.subclient.refresh(
        )  # Refresh the subclient content with the latest association details

        self.log.info('Validating Association of Users in the Group')
        active_directory.validate_users_in_group(
            subclient_content=o365_content)

        self.log.info("----------------"
                      "AD Group and Auto Discover User Association Validated"
                      "-----------------")

        self.log.info("----------------"
                      "Updating Mailbox SMTP and validating policy association"
                      "-----------------")

        policy_before_modify = self.exmbclient_object.csdb_helper.get_mailbox_assoc_policy(
            mailbox_smtp_address=self.smtp_list[2])
        self.log.info('Policy Dictionary before SMTP Update: {}'.format(
            policy_before_modify))

        new_smtp = f"modified{self.smtp_list[2]}"
        self.exmbclient_object.graph_helper.update_user_smtp(user_upn=self.smtp_list[2], new_mail_address=new_smtp)

        active_directory.wait_mailbox_smtp_update_complete(
            original_smtp_address=self.smtp_list[2], new_smtp_address=new_smtp, mailbox_upn=new_smtp)
        self.smtp_list[2] = new_smtp
        self.log.info('Updated Mailbox SMTP is reflected on Graph API')

        self.exmbclient_object.cvoperations.run_admailbox_monitor()
        self.machine.wait_for_process_to_exit(
            process_name=AD_MAILBOX_MONITORING_EXE)
        self.log.info('AD Mailbox Discovery process completed successfully')
        self.subclient.refresh()  # Refresh the Subclient object with the latest modifications

        self.log.info('Getting the Policy Dictionary after update')
        policy_after_modify = self.exmbclient_object.csdb_helper.get_mailbox_assoc_policy(
            mailbox_smtp_address=self.smtp_list[2])
        self.log.info('Policy Dictionary after modification: {}'.format(
            policy_after_modify))

        if not (policy_before_modify['archive_policy']
                == policy_before_modify['archive_policy']
                and policy_before_modify['cleanup_policy']
                == policy_after_modify['cleanup_policy']
                and policy_before_modify['retention_policy']
                == policy_after_modify['retention_policy']):
            self.log.error(' Policy values mismatch')
            raise Exception(
                'Policies values before and after SMTP update do not match')

        self.log.info("----------------"
                      "Deleting Mailbox and Verifying its Removal from Content"
                      "-----------------")

        self.log.info('Deleting the mailbox {} on Exchange'.format(
            self.smtp_list[3]))
        self.exmbclient_object.graph_helper.delete_azure_ad_user(user_upn=self.smtp_list[3])
        self.log.info('Deleted Mailbox')
        time.sleep(30)  # For the changes to reflect on the Exchange/ Azure AD

        self.exmbclient_object.cvoperations.run_admailbox_monitor()
        self.machine.wait_for_process_to_exit(
            process_name=AD_MAILBOX_MONITORING_EXE)
        self.log.info('AD Mailbox Discovery process completed successfully')
        self.subclient.refresh()

        mailbox_deleted_flag = self.exmbclient_object.csdb_helper.check_deleted_flag_set(
            mailbox_smtp_address=self.smtp_list[3])
        if not mailbox_deleted_flag:
            self.log.error('Mailbox is in the list of associated mailboxes')
            self.log.error(
                'Mailbox: {} should not be in the list of associated mailboxes'
                .format(self.mailboxes_list[3]))
            raise Exception('Mailbox Deletion unsuccessful')

        self.log.info('Mailbox is not in the list of discovered mailboxes')
        self.log.info(
            'Auto discovered mailbox, deleted from Azure is removed by subclient')

        # self.verify_manual_user_deletion()
        self.verify_display_name_update()

        self.log.info('Test Case Completed')

    def tear_down(self):
        """Tear Down Function for the Test Case"""
        self.smtp_list.remove(self.smtp_list[3])
        self.smtp_list.remove(self.smtp_list[5])
        # Removing this, because that mailbox has already been deleted in the testcase run
        for mailbox in self.smtp_list:
            self.ex_powershell.exch_online_operations(
                op_type="DELETE",
                smtp_address=mailbox)
        # Cleanup Operation: Cleaning Up the mailboxes created
