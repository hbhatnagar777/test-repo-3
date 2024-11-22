# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This Test Case performs the Sanity Checks MultiCommcell Login.

1.Local Users, Domain Users and Company Users will be created on Service commcell within testcase
2.Registration
3.Sync Validation
4.Login for every User created in step 1 on Identity Provider Commcell
5.SAML Token generation for a user on Identity Provider
6.SAML Token generated in step 5 will be used to Login into Service Commcell

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Server.routercommcell import RouterCommcell
from Server.Security.userhelper import UserHelper
from AutomationUtils.options_selector import OptionsSelector
import datetime
from AutomationUtils.config import get_config
from Server.Security.usergrouphelper import UsergroupHelper
from Server.Security.securityhelper import SecurityHelper

_CONFIG = get_config()

class TestCase(CVTestCase):
    """Class for executing Multicommcell Login"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "MultiCommcell Login for Local Users, Domain Users and Company Users"
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
            new_user1 = 'Test_588691' + " " + str(datetime.datetime.today())
            new_ug = 'Testug58869'
            user_dict = {}
            company_name = 'TC'+str(datetime.datetime.today())
            user_password = _CONFIG.MultiCommcell.Local_users_password
            domain_name = _CONFIG.MultiCommcell.domains.domain1.domain1_name
            domain_password = _CONFIG.MultiCommcell.domains.domain1.domain1_pwd
            domain_smtp = _CONFIG.MultiCommcell.domains.domain1.domain1_smtp
            domain_uname = _CONFIG.MultiCommcell.domains.domain1.domain1_uname
            domain_u1 = _CONFIG.MultiCommcell.domains.domain1.domain1_user1
            domain_u2 = _CONFIG.MultiCommcell.domains.domain1.domain1_user2
            self.router_commcell.get_service_commcell(self.tcinputs["ServiceCommcellName"],
                                                      self.tcinputs["ServiceCommcellAdminUserName"],
                                                      self.tcinputs["ServiceCommcellAdminUserPassword"])
            self.service_commcell_object = self.router_commcell.service_commcell
            self._user_helper = UserHelper(self.service_commcell_object)
            self._user_helper.create_user(user_name=new_user,
                                          email='a@b.c',
                                          password=user_password)
            user_dict[new_user] = user_password
            self._user_helper.create_user(user_name=new_user1,
                                          email='test@b.c',
                                          password=user_password)
            user_dict[new_user1] = user_password
            if not self.service_commcell_object.domains.has_domain(domain_name):
                self.service_commcell_object.domains.add(domain_name=domain_smtp,
                                                         netbios_name=domain_name,
                                                         user_name='{0}\\{1}'.format(domain_name, domain_uname),
                                                         password=domain_password,
                                                         company_id=0)
            self._user_group_helper = UsergroupHelper(self.service_commcell_object)
            self._security_helper = SecurityHelper(self.service_commcell_object)
            new_dict = self._security_helper.gen_random_entity_types_dict(no_of_entity_types=1)
            if self.service_commcell_object.user_groups.has_user_group(new_ug):
                self._user_group_helper.delete_usergroup(group_name=new_ug, new_group='master')
            user_grp_object = self._user_group_helper.create_usergroup(group_name=new_ug, entity_dict=new_dict)
            if not self.service_commcell_object.user_groups.has_user_group('{0}\\Domain Users'.format(domain_name)):
                self._user_group_helper.create_usergroup(group_name='Domain Users',
                                                         domain=domain_name,
                                                         entity_dict=new_dict,
                                                         local_groups=[user_grp_object.name])
            if not self.service_commcell_object.users.has_user('{0}\\{1}'.format(domain_name, domain_u1)):
                self._user_helper.create_user(user_name=domain_u1,
                                              email='{0}@{1}'.format(domain_u1, domain_smtp),
                                              domain=domain_name)
            user_dict['{0}\\{1}'.format(domain_name, domain_u1)] = \
                _CONFIG.MultiCommcell.domains.domain1.domain1_user1_pwd
            if not self.service_commcell_object.users.has_user('{0}\\{1}'.format(domain_name, domain_u1)):
                self._user_helper.create_user(user_name=domain_u2,
                                              email='{0}@{1}'.format(domain_u2, domain_smtp),
                                              domain=domain_name)
            user_dict['{0}\\{1}'.format(domain_name, domain_u2)] = \
                _CONFIG.MultiCommcell.domains.domain1.domain1_user2_pwd
            self.comp_obj = self.service_commcell_object.organizations.add(name=company_name,
                                                                           email='{0}@{1}.com'.format(company_name,
                                                                                                      company_name),
                                                                           contact_name=company_name,
                                                                           company_alias=company_name)
            self._user_helper.create_user(user_name='{0}\\newuser'.format(company_name),
                                          email='newuser@{0}.com'.format(company_name),
                                          password=user_password)
            user_dict['{0}\\newuser'.format(company_name)] = user_password
            self._user_helper.create_user(user_name='{0}\\newuser1'.format(company_name),
                                          email='newuser1@{0}.com'.format(company_name),
                                          password=user_password)
            user_dict['{0}\\newuser1'.format(company_name)] = user_password
            self.router_commcell.register_service_commcell(service_commcell_host_name=
                                                           self.tcinputs["ServiceCommcellName"],
                                                           service_user_name=
                                                           self.tcinputs["ServiceCommcellAdminUserName"],
                                                           service_password=
                                                           self.tcinputs["ServiceCommcellAdminUserPassword"],
                                                           registered_for_idp="True")
            self.utility.sleep_time(10)
            self.router_commcell.check_registration()
            self.router_commcell.validate_sync()
            self.router_commcell.validate_commcells_idp(self.commcell)
            for user in user_dict:
                self.cc_object = self.router_commcell.get_commcell_object(user_name=user,
                                                                          password=user_dict[user])
                self.router_commcell.validate_commcells_idp(self.cc_object)
                self.sc_object = self.router_commcell.get_commcell_object(authtoken=self.cc_object.get_saml_token())
                self.sc_object.logout()
                self.cc_object.logout()
            self.router_commcell.unregister_service_commcell()

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
