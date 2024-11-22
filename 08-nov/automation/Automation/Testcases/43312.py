# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test cases to validate basic functionality of a smart client group.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                           --  initialize TestCase class

    cleanup()                            --  To cleanup created roles and user

    run()                                --  run function of this test case

    _create_smart_client_group           -- Private module to perform common steps

# To do: Make sure the non- admin user is also the owner of that client
"""

from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from AutomationUtils.options_selector import OptionsSelector, CVEntities
from Server import serverconstants


class TestCase(CVTestCase):
    """Class for executing this test case"""
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Acceptance]:Validate basic functionality of a smart client group"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.CLIENTGROUP
        self.show_to_user = True
        self.user = None
        self.non_admin = None
        self.client_group = None
        self.role = None
        self.user_name = None
        self.role_name1 = None
        self.role_name2 = None
        self.entities = None
        self.db_obj = None

    def cleanup(self):
        """clean up the created roles and users"""
        if self.role.has_role(self.role_name1):
            self.role.delete(self.role_name1)
        if self.role.has_role(self.role_name2):
            self.role.delete(self.role_name2)
        if self.user.has_user(self.user_name):
            self.user.delete(self.user_name, new_user='Admin')

    def _create_smart_client_group(self,
                                   rule_list,
                                   rules_filter,
                                   string,
                                   query_type=None,
                                   entity=None,
                                   id_value=None):
        """common module to perform common tasks"""

        scg_rule = self.client_group.merge_smart_rules(rule_list, rules_filter)
        clientgroup = self.entities.create({'clientgroup': {'scg_rule': scg_rule}})
        group_id = clientgroup['clientgroup']['id']
        automatic_client_groupids = self.db_obj.get_client_ids('GROUP_ID', 'client', group_id)
        ida_specific_clients = self.db_obj.get_client_ids(query_type, entity, id_value)
        if set(automatic_client_groupids) ^ set(ida_specific_clients):
            raise Exception("Failed! Mismatch with number of clients in Client group and {0}"
                            .format(string))
        self.log.info("validation of Client Group with {0} is completed"
                      .format(string))

    def run(self):
        """Run function of this test case"""
        try:
            self.entities = CVEntities(self)
            self._log.info("Started executing {0} testcase".format(self.id))
            server_tc = ServerTestCases(self)
            self.db_obj = OptionsSelector(self.commcell)
            self.client_group = self.commcell.client_groups
            self.user = self.commcell.users
            self.role = self.commcell.roles
            self.user_name = OptionsSelector.get_custom_str('user', '43312')
            user_email = self.user_name + '@cvtest.com'
            self.role_name1 = OptionsSelector.get_custom_str('Role1', '43312')
            self.role_name2 = OptionsSelector.get_custom_str('Role2', '43312')
            foreign_name = self.client.client_name[-2:]

            rule_list = []
            self.log.info("""
                ====================================================
                Step1:
                Creating Automatic Client Group with agent installed (ex: WinFS, Linux FS)
                ====================================================
                """)

            rs_rule_1 = self.client_group.create_smart_rule('Agents Installed',
                                                            'any in selection',
                                                            'Windows File System',
                                                            serverconstants.APPGROUPXML)
            rule_list.append(rs_rule_1)
            string = 'Windows FS IDA installed clients'
            self._create_smart_client_group(rule_list, 'all', string, 'APP_TYPEID', 'client', '33')
            self.log.info("""
                ====================================================
                Step2:
                Creating Automatic Client Group with Media Agents installed clients
                ====================================================
                """)
            rs_rule_1 = self.client_group.create_smart_rule('Associated Client Group',
                                                            'equal to',
                                                            'Media Agents',
                                                            '3')
            rule_list.clear()
            rule_list.append(rs_rule_1)
            string = 'Media Agents installed clients'
            self._create_smart_client_group(rule_list,
                                            'all',
                                            string,
                                            'SIM_ID',
                                            'client',
                                            serverconstants.MAPACKAGEID)
            self.log.info("""
                ====================================================
                Step3:
                Creating Automatic Client Group with ClientName Contains foreign language
                ====================================================
                """)
            rs_rule_1 = self.client_group.create_smart_rule('Name',
                                                            'contains',
                                                            value=foreign_name)
            rule_list.clear()
            rule_list.append(rs_rule_1)
            string = 'ClientName Contains foreign language'
            self._create_smart_client_group(rule_list,
                                            'all',
                                            string,
                                            'NAME_ID',
                                            'client',
                                            foreign_name)
            self.log.info("""
                ====================================================
                Step4:
                Creating Automatic Client Group with TIME zone india or pacific
                ====================================================
                """)
            sec_value = '(UTC+05:30) Chennai, Kolkata, Mumbai, New Delhi'
            rs_rule_1 = self.client_group.create_smart_rule('Timezone',
                                                            'equal to',
                                                            sec_value,
                                                            value='42')
            sec_value = '(UTC-08:00) Pacific Time (US & Canada)'
            rs_rule_2 = self.client_group.create_smart_rule('Timezone',
                                                            'equal to',
                                                            sec_value,
                                                            value='64')
            rule_list.clear()
            rule_list.append(rs_rule_1)
            rule_list.append(rs_rule_2)
            string = 'TIME zone india or pacific'
            self._create_smart_client_group(rule_list, 'any', string, 'TIMEZONE_ID', 'client')
            self.log.info("""
                ====================================================
                Step5:
                Creating Automatic Client Group with OSTYPE as Windows
                ====================================================
                """)
            rs_rule_1 = self.client_group.create_smart_rule('OS Type', 'equal to', 'Windows', '1')
            rule_list.clear()
            rule_list.append(rs_rule_1)
            string = 'OSTYPE as Windows'
            self._create_smart_client_group(rule_list,
                                            'all',
                                            string,
                                            'OSTYPE_ID',
                                            'client',
                                            'Windows')
            self.log.info("""
                ====================================================
                Step6:
                Creating Automatic Client Group with  OSTYPE as Windows And
                Installed agent as Media agent
                ====================================================
                """)

            rs_rule_1 = self.client_group.create_smart_rule('OS Type', 'equal to', 'Windows', '1')
            rs_rule_2 = self.client_group.create_smart_rule('Package Installed',
                                                            'any in selection',
                                                            'MediaAgent',
                                                            serverconstants.APPADVANCEPKG)
            rule_list.clear()
            rule_list.append(rs_rule_1)
            rule_list.append(rs_rule_2)
            string = 'OSTYPE as Windows And Installed agent as Media agent'
            self._create_smart_client_group(rule_list, 'all', string, 'PACKAGE_ID', 'client')
            self.log.info("""
                ====================================================
                Step7:
                Login as a non-admin user with administrative management
                agent management capability on some clients and
                create a smart client group with Installed agent as Media agent
                ====================================================
                """)
            self.role.add(self.role_name1, ["Agent Management", "Administrative Management"])
            self.role.add(self.role_name2, ["Create Client Group"])
            entity_dictionary = {
                # Agent Management & Administrative Management permissions on client level
                'assoc1': {'clientName': [self.client.client_name], 'role': [self.role_name1]},
                # Create Client Group permission on any client
                'assoc2': {
                    'commCellName': [self.commcell.commserv_name],
                    'role': [self.role_name2]
                },
                # View permission on @commcell level
                'assoc3': {'commCellName': [self.commcell.commserv_name], 'role': ['View']}
                }
            # To do: Make sure the non- admin user is also the owner of that client
            self.user.add(self.user_name,
                          self.user_name,
                          user_email,
                          password=serverconstants.PASSWORD,
                          entity_dictionary=entity_dictionary)
            self._log.info("NonAdmin user created successfully with name: {0}"
                           .format(self.user_name))
            self.non_admin = Commcell(self.commcell.webconsole_hostname,
                                      self.user_name,
                                      serverconstants.PASSWORD)
            self._log.info("Successfully! Login to commcell with NonAdmin user: {0}"
                           .format(self.user_name))

            self.client_group = self.non_admin.client_groups
            rs_rule_1 = self.client_group.create_smart_rule('Name',
                                                            'contains',
                                                            value=self.client.client_name)
            rule_list.clear()
            rule_list.append(rs_rule_1)
            string = self.client.client_name
            self._create_smart_client_group(rule_list,
                                            'all',
                                            string,
                                            'NAME_ID',
                                            'client',
                                            self.client.client_name)
        except Exception as exp:
            server_tc.fail(exp)
        finally:
            self.entities.cleanup()
            self.cleanup()
