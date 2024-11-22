# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Companies - Create entities in a company

"""
import string
import random
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils import config
from Server.Security.userhelper import UserHelper
from Server.Security.usergrouphelper import UsergroupHelper
from Server.Security.securityhelper import OrganizationHelper
from Server.SmartClientGroups.smartclient_helper import SmartClientHelper
from Server.Plans.planshelper import PlansHelper
from cvpysdk.commcell import Commcell
from cvpysdk.policies.storage_policies import StoragePolicies
from cvpysdk.storage import DiskLibraries
from cvpysdk.security.role import Roles
from Install.install_helper import InstallHelper


class TestCase(CVTestCase):
    """Class for executing verification of tagging of entities to a company"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Companies - Create entities in a company"
        self.retval = 0
        self.tcinputs = {
            "ClientHostName": None,
            "ClientUserName": None,
            "ClientPassword": None,
        }
        self.server = None
        self.organization_helper = None
        self.user_helper = None
        self.smartclient_helper = None
        self.plans_helper = None
        self.storage_obj = None
        self.disk_library_obj = None
        self.options_selector = None
        self.company_obj = None
        self.company_creator_password = None
        self.company_user_obj = None
        self.company_user_commcell_obj  = None
        self.random_string = None
        self.company_id = None
        self.role_obj = None
        self.new_library_obj = None
        self.storage_policies_obj = None
        self.user_group_helper = None
        self.config_json = None
        self.company_name = ""
        self.company_username = ""
        self.company_email = "59749_user@cv.com"
        self.company_user_password = ""
        self.permission_list = ['Create Storage Policy Copy']

    def setup(self):
        """ Setup function of this test case """
        self.log.info("Executing testcase")
        self.organization_helper = OrganizationHelper(self.commcell)
        self.config_json = config.get_config()
        self.random_string = "".join(random.choice(string.ascii_uppercase) for i in range(8))
        self.company_name = "59749_company_"+self.random_string
        self.company_username = self.company_name + "\\" + self.company_email.split("@")[0]
        inputs = { "password": self.inputJSONnode['commcell']['commcellPassword'] }
        self.company_creator_password = inputs["password"]
        self.company_user_password = self.config_json.Organizations.company_user_password
        self.log.info("Creating company: %s", self.company_name)
        self.company_obj = self.organization_helper.create(name=self.company_name,
                                        email=self.company_email,
                                        contact_name="59749_contact_name",
                                        company_alias=self.company_name
                                        )
        self.company_id = str(self.company_obj.organization_id)
        self.company_user_obj = self.commcell.users.get(self.company_username)
        self.company_user_obj.update_user_password(new_password=self.company_user_password,
                                              logged_in_user_password=self.company_creator_password)
        self.company_user_commcell_obj = Commcell(self.commcell.webconsole_hostname,
                                                  self.company_username,
                                                  self.company_user_password)

    def run(self):
        """Main function for test case execution"""
        try:

            # Install client
            client_name = "59749_Client_" + self.random_string
            service_pack = f"SP{int(self.commcell.commserv_version)}"
            self.log.info("Installing Client [%s] for the company", client_name)
            machine_obj = Machine(self.tcinputs["ClientHostName"],
                                  self.commcell,
                                  self.tcinputs["ClientUserName"],
                                  self.tcinputs["ClientPassword"])
            install_helper = InstallHelper(self.commcell, machine_obj)
            install_helper.silent_install(client_name=client_name,
                                          tcinputs={
                                          "csClientName": self.commcell.commserv_name,
                                          "csHostname": self.commcell.commserv_hostname,
                                          "commserveUsername": self.company_username,
                                          "commservePassword":
                                          self.config_json.Organizations.company_user_encrypted_password},
                                          feature_release=service_pack,
                                          packages=['FILE_SYSTEM', 'MEDIA_AGENT'])
            self.log.info("Successfully finished Installing Client [%s]", client_name)

            # Create User
            new_user_name = self.company_name+"\\"+"59749_newUser_" + self.random_string
            self.log.info("Creating User [%s] for the company", new_user_name)
            self.user_helper = UserHelper(self.commcell, self.company_user_obj)
            self.user_helper.create_user(user_name=new_user_name,
                                          email='newuser@cv.com',
                                          password=self.company_user_password)

            # Create User Group
            user_group_name = "59749_UserGroup_" + self.random_string
            self.log.info("Creating User Group [%s] for the company", user_group_name)
            self.user_group_helper = UsergroupHelper(self.commcell)
            self.user_group_helper.create_usergroup(group_name=user_group_name,
                                                    domain=self.company_name)

            # Create Role
            role_name = "59749_Role_" + self.random_string
            self.log.info("Creating Role [%s] for the company", role_name)
            self.role_obj = Roles(self.company_user_commcell_obj)
            self.role_obj.add(role_name, self.permission_list)

            # Create Smart Client Group
            scg_name = "59749_ClientGroup_" + self.random_string
            self.log.info("Creating Smart Client Group [%s] for the company", scg_name)
            self.smartclient_helper = SmartClientHelper(
                                                commcell_object=self.company_user_commcell_obj,
                                                group_name=scg_name,
                                                description='Created by TC 59749',
                                                client_scope='Clients of Companies',
                                                value=self.company_name)
            rule_list = []
            rule1 = self.smartclient_helper.create_smart_rule(filter_rule='Client',
                                                         filter_condition='equal to',
                                                         filter_value='Installed')
            rule_list.append(rule1)
            self.smartclient_helper.create_smart_client(smart_rule_list=rule_list)

            self.log.info("Waiting 180 sec for MA to be ready..")
            time.sleep(180)

            # Create Storage Pool
            storage_pool_name = "59749_StoragePool_" + self.random_string
            self.log.info("Creating Storage Pool [%s] for the company", storage_pool_name)
            self.company_user_commcell_obj.storage_pools.add(storage_pool_name,
                                                            "c:\\59749\\"+storage_pool_name+"_path",
                                                            client_name,
                                                            client_name,
                                                            "c:\\59749\\"+storage_pool_name+"_path\\DDB")

            # Create Plan
            plan_name = "59749_Plan_" + self.random_string
            self.log.info("Creating Plan [%s] for the company", plan_name)
            self.plans_helper = PlansHelper(self.commcell.webconsole_hostname,
                                            self.company_username,
                                            self.company_user_password)
            self.plans_helper.create_base_plan(plan_name, "Server", storage_pool_name)

            # Create Library
            library_name = "59749_Library_" + self.random_string
            self.log.info("Creating Library [%s] for the company", library_name)
            self.disk_library_obj = DiskLibraries(self.company_user_commcell_obj)
            self.new_library_obj = self.disk_library_obj.add(library_name,
                                                             client_name,
                                                             "c:\\59749\\"+library_name+"_path")

            # Create Storage Policy
            storage_policy_name = "59749_SP_" + self.random_string
            self.log.info("Creating Storage Policy [%s] for the company", storage_policy_name)
            self.storage_policies_obj = StoragePolicies(self.company_user_commcell_obj)
            self.storage_policies_obj.add(storage_policy_name,
                                          library_name,
                                          client_name)

            self.options_selector = OptionsSelector(self._commcell)
            self.log.info("Verifying the tagging of all entities to companyid [%s]..",
                          self.company_id)

            # Verify Client
            dbquery = "SELECT companyid FROM App_CompanyEntities WHERE entityType = 3 " \
                      "AND entityID =(SELECT ID FROM APP_CLIENT WHERE NAME ='" + client_name + "')"
            companyid = self.options_selector.exec_commserv_query(dbquery)
            if self.company_id != str(companyid[0][0]):
                raise Exception("Client NOT tagged to company ID: %s" % self.company_id)

            # Verify Media Agent
            dbquery = "SELECT companyid FROM App_CompanyEntities WHERE entityType = 11 " \
                      "AND entityID =(SELECT ID FROM APP_CLIENT WHERE NAME ='" + client_name + "')"
            companyid = self.options_selector.exec_commserv_query(dbquery)
            if self.company_id != str(companyid[0][0]):
                raise Exception("Media Agent NOT tagged to company ID: %s" % self.company_id)

            # Verify User
            dbquery = "SELECT companyid FROM App_CompanyEntities WHERE entityType = 13 " \
                      "AND entityID =(SELECT ID FROM UMUsers WHERE login ='"+new_user_name+"')"
            companyid = self.options_selector.exec_commserv_query(dbquery)
            if self.company_id != str(companyid[0][0]):
                raise Exception("User NOT tagged to company ID: %s" % self.company_id)

            # Verify User Group
            dbquery = "SELECT companyid FROM App_CompanyEntities WHERE entityType = 15 " \
                      "AND entityID =(SELECT ID FROM UMGroups WHERE name ='"+user_group_name+"')"
            companyid = self.options_selector.exec_commserv_query(dbquery)
            if self.company_id != str(companyid[0][0]):
                raise Exception("User Group NOT tagged to company ID: %s" % self.company_id)

            # Verify Role
            dbquery = "SELECT companyid FROM App_CompanyEntities WHERE entityType = 120 " \
                      "AND entityID =(SELECT ID FROM UMRoles WHERE name ='"+role_name+"')"
            companyid = self.options_selector.exec_commserv_query(dbquery)
            if self.company_id != str(companyid[0][0]):
                raise Exception("Role NOT tagged to company ID: %s" % self.company_id)

            # Verify Smart Client Group
            dbquery = "SELECT companyid FROM App_CompanyEntities WHERE entityType = 28 " \
                      "AND entityID =(SELECT ID FROM APP_ClientGroup WHERE name ='"+scg_name+"')"
            companyid = self.options_selector.exec_commserv_query(dbquery)
            if self.company_id != str(companyid[0][0]):
                raise Exception("Smart Client Group NOT tagged to company ID: %s" % self.company_id)

            # Verify Storage Pool
            dbquery = "SELECT companyid FROM App_CompanyEntities WHERE entityType = 9 "\
            "AND entityID =(SELECT LibraryId FROM MMLibrary WHERE AliasName ='"+storage_pool_name+\
            "') UNION SELECT companyid FROM App_CompanyEntities WHERE entityType = 17 "\
            "AND entityID =(SELECT ID FROM archGroup WHERE NAME ='"+storage_pool_name+"')"
            companyid = self.options_selector.exec_commserv_query(dbquery)
            if len(companyid[0])!= 1 and self.company_id != str(companyid[0][0]):
                raise Exception("Storage Pool NOT tagged to company ID: %s" % self.company_id)

            # Verify Plan
            dbquery = "SELECT companyid FROM App_CompanyEntities WHERE entityType = 158 " \
                      "AND entityID =(SELECT ID FROM App_Plan WHERE name ='"+plan_name+"')"
            companyid = self.options_selector.exec_commserv_query(dbquery)
            if self.company_id != str(companyid[0][0]):
                raise Exception("Plan NOT tagged to company ID: %s" % self.company_id)

            # Verify Library
            dbquery = "SELECT companyid FROM App_CompanyEntities WHERE entityType = 9 " \
            "AND entityID =(SELECT LibraryId FROM MMLibrary WHERE AliasName ='"+library_name+"')"
            companyid = self.options_selector.exec_commserv_query(dbquery)
            if self.company_id != str(companyid[0][0]):
                raise Exception("Library NOT tagged to company ID: %s" % self.company_id)

            # Verify Storage Policy
            dbquery = "SELECT companyid FROM App_CompanyEntities WHERE entityType = 17 " \
            "AND entityID =(SELECT ID FROM archGroup WHERE name ='"+storage_policy_name+"')"
            companyid = self.options_selector.exec_commserv_query(dbquery)
            if self.company_id != str(companyid[0][0]):
                raise Exception("Storage Policy NOT tagged to company ID: %s" % self.company_id)

            self.log.info("All entities are tagged to the company. Deleting the company: %s",
                          self.company_name)
            self._commcell.organizations.delete(self.company_name)

            self.log.info("Testcase PASSED")

        except Exception as exp:
            self.log.error("Failed with error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
