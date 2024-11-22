# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This Test Case performs the Sanity Checks MultiCommcell Operations.

1.Create Service commcell object
2.Check if Service commcell has idcprodcert domain in it , Delete if exists
2.Register a commcell for IdP
3.Validate Registration
4.Validate Sync
5.Create a local user ,local usergroupon IdP
6.Associate created user,usergroup on IdP to Service commcell
7.Associate idcprodcert domain to Service commcell
8.Create a user on idcprodcert domain
9.Create a company on IdP
10.Associate company to Service commcell
11.Create a user for the company created on IdP
12.Create a company on IdP by associating Service commcell
13.login into IdP using local/Domain/Company user that are associated to service commcell

"""


from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Server.routercommcell import RouterCommcell
from Server.Security.userhelper import UserHelper
from Server.Security.usergrouphelper import UsergroupHelper
from AutomationUtils.options_selector import OptionsSelector
import datetime
from AutomationUtils.config import get_config

_CONFIG = get_config()

class TestCase(CVTestCase):
    """Class for executing Multicommcell add and associate operations"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Multicommcell add and associate operations on IdP commcell"
        self.log = None
        self._user_helper = None
        self.show_to_user = False
        self.tcinputs = {
            "ServiceCommcellName": None,
            "ServiceCommcellAdminUserName": None,
            "ServiceCommcellAdminUserPassword": None
        }
    def setup(self):
        """Setup function of this test case"""
        self.router_commcell = RouterCommcell(self.commcell)
        self.utility = OptionsSelector(self.commcell)


    def run(self):
        """Main function for test case execution"""

        try:
            new_user = 'Test_58869' + " " + str(datetime.datetime.today())
            new_ug = 'Testug' + " " + str(datetime.datetime.today())
            user_dict = {}
            company_name = 'TC'+str(datetime.datetime.today())
            company_name1 = 'TC1'+str(datetime.datetime.today())
            user_password = _CONFIG.MultiCommcell.Local_users_password
            domain_name = _CONFIG.MultiCommcell.domains.domain2.domain2_name
            domain_password = _CONFIG.MultiCommcell.domains.domain2.domain2_pwd
            domain_smtp = _CONFIG.MultiCommcell.domains.domain2.domain2_smtp
            domain_uname = _CONFIG.MultiCommcell.domains.domain2.domain2_uname
            domain_u1 = _CONFIG.MultiCommcell.domains.domain2.domain2_user1
            self.log.info("Step 1:Creating a Service commcell object")
            self.router_commcell.get_service_commcell(self.tcinputs["ServiceCommcellName"],
                                                      self.tcinputs["ServiceCommcellAdminUserName"],
                                                      self.tcinputs["ServiceCommcellAdminUserPassword"])
            self.service_commcell_object = self.router_commcell.service_commcell
            self.log.info("Step 2: Creating a UserHelper object")
            self._user_helper = UserHelper(self.commcell)
            self.log.info("Step 3: Creating a UsergroupHelper object")
            self._user_group_helper = UsergroupHelper(self.commcell)
            self.log.info("Step 4: Checking if domain exists on service commcell")
            if self.service_commcell_object.domains.has_domain(domain_name):
                self.log.info("Step 5: Deleting the domain as domain exists")
                self.service_commcell_object.domains.delete(domain_name)
            self.log.info("Step 6: Registering a service commcell for Identity Provider")
            self.router_commcell.register_service_commcell(service_commcell_host_name=self.tcinputs["ServiceCommcellName"],
                                                           service_user_name=self.tcinputs["ServiceCommcellAdminUserName"],
                                                           service_password=self.tcinputs["ServiceCommcellAdminUserPassword"],
                                                           registered_for_idp="True")
            self.utility.sleep_time(10)
            self.log.info("Step 7: Checking the Registration")
            self.router_commcell.check_registration()
            self.log.info("Step 8: Validating the Sync")
            self.router_commcell.validate_sync()
            self.log.info("Step 9: Validating the list of commcells registered for IdP")
            self.router_commcell.validate_commcells_idp(self.commcell)
            self.log.info("Step 10: Creating user on IdP")
            user_obj = self._user_helper.create_user(user_name=new_user,
                                                     email='a@b.c',
                                                     password=user_password)
            user_dict[new_user] = user_password
            self.log.info("Step 11: Associating created user to service commcell")
            self.commcell.add_service_commcell_associations(user_obj, self.service_commcell_object.commserv_name)
            self.log.info("Step 12: Creating UserGroup on IdP")
            user_grp_object = self._user_group_helper.create_usergroup(group_name=new_ug)
            self.log.info("Step 13: Associating created usergroup to service commcell")
            self.commcell.add_service_commcell_associations(user_grp_object, self.service_commcell_object.commserv_name)
            self.log.info("Step 14: Checking if domain exists on IdP")
            if not self.commcell.domains.has_domain(domain_name):
                self.log.info("Step 15: Creating the domain on IdP as domain doesnt exists")
                self.commcell.domains.add(domain_name=domain_smtp,
                                          netbios_name=domain_name,
                                          user_name='{0}\\{1}'.format(domain_name, domain_uname),
                                          password=domain_password,
                                          company_id=0)
            self.log.info("Step 16: Associating created domain to service commcell")
            self.commcell.add_service_commcell_associations(self.commcell.domains.get(domain_name),
                                                            self.service_commcell_object.commserv_name)
            if not self.commcell.users.has_user('{0}\\{1}'.format(domain_name, domain_u1)):
                self._user_helper.create_user(user_name=domain_u1,
                                              email='{0}@{1}'.format(domain_u1, domain_smtp),
                                              domain=domain_name)
            user_dict['{0}\\{1}'.format(domain_name, domain_u1)] = \
                _CONFIG.MultiCommcell.domains.domain2.domain2_user1_pwd
            self.log.info("Step 17: Creating a new company on IdP")
            self.comp_obj = self.commcell.organizations.add(name=company_name,
                                                            email='{0}@{1}.com'.format(company_name,
                                                                                       company_name),
                                                            contact_name=company_name,
                                                            company_alias=company_name)
            self.log.info("Step 18: Associating the created company to Service commcell")
            self.commcell.add_service_commcell_associations(self.comp_obj, self.service_commcell_object.commserv_name)
            self._user_helper.create_user(user_name='{0}\\newuser'.format(company_name),
                                          email='newuser@{0}.com'.format(company_name),
                                          password=user_password)
            user_dict['{0}\\newuser'.format(company_name)] = user_password
            self.log.info("Step 19: Creating a company on IdP by associating to Service commcell")
            self.comp_obj1 = self.commcell.organizations.add(name=company_name1,
                                                             email='{0}@{1}.com'.format(company_name1,
                                                                                        company_name1),
                                                             contact_name=company_name1,
                                                             company_alias=company_name1,
                                                             service_commcells=[self.service_commcell_object.commserv_name])
            self._user_helper.create_user(user_name='{0}\\newuser'.format(company_name1),
                                          email='newuser@{0}.com'.format(company_name1),
                                          password=user_password)
            user_dict['{0}\\newuser'.format(company_name1)] = user_password
            self.log.info("Step 20: For all the users that got created and associated checking the login")
            for user in user_dict:
                self.cc_object = self.router_commcell.get_commcell_object(user_name=user,
                                                                          password=user_dict[user])
                self.router_commcell.validate_commcells_idp(self.cc_object)
                self.sc_object = self.router_commcell.get_commcell_object(authtoken=self.cc_object.get_saml_token(),
                                                                          service_commcell="True")
                self.sc_object.logout()
                self.cc_object.logout()
            self.router_commcell.unregister_service_commcell()

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
