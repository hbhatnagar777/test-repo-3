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
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.activedirectory_helper import DiscoveryOptions
from Application.Exchange.exchangepowershell_helper import ExchangePowerShell
from Application.Exchange.ExchangeMailbox.constants import (
    ARCHIVE_POLICY_DEFAULT,
    CLEANUP_POLICY_DEFAULT,
    RETENTION_POLICY_DEFAULT,
    Office365GroupType,
    AD_MAILBOX_MONITORING_EXE
)


class TestCase(CVTestCase):
    """Class for executing test case of discovery, association
    and disassociation of Exchange Online Mailbox Groups

        Example for test case inputs:
        "52784":
        {

        "AgentName": "Exchange Mailbox",
        "InstanceName": "defaultInstanceName",
        "BackupsetName": "User Mailbox",
        "ProxyServers": [
          <proxy server name>
        ],
        "EnvironmentType":4,
        "JobResultDirectory":"",
        "RecallService":"",
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
                cleanup_policy         (object)    --  Object of Configuration policy to be used to associate the group
                retention_policy       (object)    --  Object of Configuration policy to be used to associate the group

                machine                (object)    --  Object of Machine class for the iDA machine
                powershell             (object)    --  Object of Exchange PowerShell class

        """
        super(TestCase, self).__init__()
        self.name = "Basic Group Discovery, Association and Disassociation test case for Exchange Online"
        self.show_to_user = True
        self.active_directory = None
        self.product = self.products_list.EXCHANGEMB
        self.exmbclient_object = None
        self.archive_policy = None
        self.cleanup_policy = None
        self.retention_policy = None
        self.powershell = None
        self.tcinputs = {
        }
        self.machine = None
        self.o365_plan = None

    def setup(self):
        self.exmbclient_object = ExchangeMailbox(self)

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self.log.info('Created Exchange Online Client')
        self._subclient = self.exmbclient_object.cvoperations.subclient
        self.log.info('Associated Exchange Online Sub Client')

        self.o365_plan = self.tcinputs["Office365Plan"]

        self.machine = machine.Machine(machine_name=self.tcinputs["ProxyServerDetails"]["IpAddress"],
                                       commcell_object=self.exmbclient_object.commcell,
                                       username=self.tcinputs["ProxyServerDetails"]["Username"],
                                       password=self.tcinputs["ProxyServerDetails"]["Password"])

        self.log.info('Created and Instantiated Machine Class Object')

        self.powershell = ExchangePowerShell(ex_object=self.exmbclient_object, cas_server_name=None,
                                             exchange_server=None,
                                             exchange_adminname=self.exmbclient_object.exchange_online_user,
                                             exchange_adminpwd=self.exmbclient_object.exchange_online_password,
                                             server_name=self.exmbclient_object.server_name)

    def run(self):
        """ Run function of this test case"""
        try:
            self.machine.wait_for_process_to_exit(process_name=AD_MAILBOX_MONITORING_EXE)
            self.log.info('AdMailBoxMonitor has finished executing')

            self.log.info('AD Mailbox Discovery process completed successfully')

            groups = self.subclient.discover_adgroups
            self.log.info("Discovered groups: %s", groups)

            group_name = self.tcinputs['GroupName']
            self.log.info('Group to be Associated is: %s', group_name)

            self.active_directory = self.exmbclient_object.active_directory
            assoc_status = self.active_directory.validate_adgroup_discovery(
                discovered_groups=self.active_directory.groups.keys(),
                groups=[group_name]
            )
            if not assoc_status:
                self.log.info('Group not discovered. Check if the group exists in the AD')
                raise Exception('Group not in the list of discovered groups')

            self.log.info('Starting Group Association')
            group_dict = {
                'adGroupNames': [group_name],
                'is_auto_discover_user': True,
                'plan_name': self.o365_plan
            }
            self.subclient.set_adgroup_associations(subclient_content=group_dict, use_policies=False)
            self.log.info('Associated the Group')

            self.log.info('Getting the User count from the Exchange Online')

            mailbox_count = self.powershell.exch_online_o365_group_operations(
                op_type="MemberCount", group_name=group_name)
            self.log.info('User count from PowerShell is: %s', mailbox_count)

            user_count_sql_server = self.exmbclient_object.csdb_helper.get_assoc_mailbox_count()
            self.log.info('User count from the SQL Server is: {}'.format(user_count_sql_server))

            if user_count_sql_server != mailbox_count:
                self.log.info('User count doesnt match')
                raise Exception(
                    'User count does not match'
                )

            self.log.info('Starting Group Disassociation')
            self.subclient.delete_adgroup_assocaition(subclient_content=group_dict, use_policies=False)
            self.log.info('Group Disassociated')

            self.log.info('Checking if the group has been disassociated or not')
            adgroups = self.subclient.adgroups

            for group in adgroups:
                if group['adGroupName'] == group_name:
                    self.log.info('Group is there in the list of discovered groups\
                     \n Group disassociation unsuccessful')
                    raise Exception('Disassociation unsuccessful')

            self.log.info("Group successfully disassociated")

            self.commcell.clients.delete(self.client.client_name)
            self.log.info('Deleted the Client')

            self.log.info('Test Case executed successfully!!!')

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED
