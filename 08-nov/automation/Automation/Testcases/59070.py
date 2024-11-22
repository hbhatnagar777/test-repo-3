# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This Test Case performs the Sanity Checks MultiCommcell Operations.

1.Create a Domain user on service commcell
2.Create a Domain user on service commcell which already exists on IdP
3.Create a domain user on service commcell with user group that already exists on IdP
4.create a domain user on service commcell by associating it with domain user group that doesnt exists on IdP
5.create a domain user group on service commcell
6.create a domain user group on service which already exists on IdP


"""


from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Server.routercommcell import RouterCommcell
from Server.Security.userhelper import UserHelper
from Server.Security.usergrouphelper import UsergroupHelper
from AutomationUtils.options_selector import OptionsSelector
import datetime
from AutomationUtils.config import get_config
from cvpysdk.exception import SDKException
from Server.Security.securityhelper import SecurityHelper

_CONFIG = get_config()

class TestCase(CVTestCase):
    """Class for executing Multicommcell domain add and associate operations"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Muticommcell - Domain User and Usergroup Create Operations on Service Commcell"
        self._user_helper = None
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
            new_ug = 'Testug59070' + " " + str(datetime.datetime.today())
            domain_name = _CONFIG.MultiCommcell.domains.domain2.domain2_name
            domain_password = _CONFIG.MultiCommcell.domains.domain2.domain2_pwd
            domain_smtp = _CONFIG.MultiCommcell.domains.domain2.domain2_smtp
            domain_uname = _CONFIG.MultiCommcell.domains.domain2.domain2_uname
            domain_u1 = _CONFIG.MultiCommcell.domains.domain2.domain2_user1
            domain_u2 = _CONFIG.MultiCommcell.domains.domain2.domain2_user2
            self.log.info("Step 1:Creating a Service commcell object")
            self.router_commcell.get_service_commcell(self.tcinputs["ServiceCommcellName"],
                                                      self.tcinputs["ServiceCommcellAdminUserName"],
                                                      self.tcinputs["ServiceCommcellAdminUserPassword"])
            self.service_commcell_object = self.router_commcell.service_commcell
            if self.service_commcell_object.domains.has_domain(domain_name):
                self.log.info("Step 2: Deleting the domain as domain exists")
                self.service_commcell_object.domains.delete(domain_name)
            self.log.info("Step 3: Registering a service commcell for Identity Provider")
            self.router_commcell.register_service_commcell(service_commcell_host_name=self.tcinputs["ServiceCommcellName"],
                                                           service_user_name=self.tcinputs["ServiceCommcellAdminUserName"],
                                                           service_password=self.tcinputs["ServiceCommcellAdminUserPassword"],
                                                           registered_for_idp="True")
            self.utility.sleep_time(10)
            self.log.info("Step 4: Checking the Registration")
            self.router_commcell.check_registration()
            self.log.info("Step 5: Validating the Sync")
            self.router_commcell.validate_sync()
            self.log.info("Step 6: Creating the UsergroupHelper for IdP commcell")
            self._user_group_helper = UsergroupHelper(self.commcell)
            self.log.info("Step 7: Creating the SecurityHelper for IdP commcell")
            self._security_helper = SecurityHelper(self.service_commcell_object)
            self.log.info("Step 8: Generating the Random entities to associate with Service commcell")
            new_dict = self._security_helper.gen_random_entity_types_dict(no_of_entity_types=1)
            self.log.info("Step 9: Creating a local user group on IdP commcell")
            user_grp_object = self._user_group_helper.create_usergroup(group_name=new_ug, entity_dict=new_dict)
            if self.commcell.domains.has_domain(domain_name):
                self.log.info("Step 10: Deleting the domain as domain exists")
                self.commcell.domains.delete(domain_name)
                self.log.info("Step 11: Adding the domain on IdP")
                self.commcell.domains.add(domain_name=domain_smtp,
                                          netbios_name=domain_name,
                                          user_name='{0}\\{1}'.format(domain_name, domain_uname),
                                          password=domain_password,
                                          company_id=0)
            self._user_group_helper.create_usergroup(group_name='Domain Users',
                                                     domain=domain_name,
                                                     entity_dict=new_dict,
                                                     local_groups=[user_grp_object.name])
            self.log.info("Step 12: Associating created domain to service commcell")
            self.commcell.add_service_commcell_associations(self.commcell.domains.get(domain_name),
                                                            self.service_commcell_object.commserv_name)
            self.log.info("Step 13: Login into IdP and service commcell as domain user")
            self.cc_object = self.router_commcell.get_commcell_object(user_name='{0}\{1}'.format(domain_name, domain_uname),
                                                                      password=domain_password)
            self.router_commcell.validate_commcells_idp(self.cc_object)
            self.sc_object1 = self.router_commcell.get_commcell_object(authtoken=self.cc_object.get_saml_token())
            self.log.info("Step 14: Logout from service commcell domain user")
            self.sc_object1.logout()
            self.log.info("Step 15: Logout from master commcell domain user")
            self.cc_object.logout()
            self.log.info("Step 16: Login into the service commcell using master's SAML Token")
            self.sc_object = self.router_commcell.get_commcell_object(authtoken=self.commcell.get_saml_token(),
                                                                      service_commcell="True")
            self.log.info("Step 17: Creating a user helper object for service commcell")
            self._user_helper = UserHelper(self.sc_object)
            self.log.info("Step 18: Create an AD user on service commcell")
            self._user_helper.create_user(user_name=domain_u1,
                                          email='{0}@{1}'.format(domain_u1, domain_smtp),
                                          domain=domain_name)
            self.log.info("Step 19: Creating a user helper object for IdP commcell")
            self._user_helper1 = UserHelper(self.commcell)
            self.log.info("Step 20: Create an AD user on IdP commcell")
            self._user_helper1.create_user(user_name=domain_u2,
                                           email='{0}@{1}'.format(domain_u2, domain_smtp),
                                           domain=domain_name)
            self.log.info("Step 21: Creating the same user on service commcell")
            try:
                self.log.info("Step 22: Creating the same domain user on service which is created on IdP commcell")
                self._user_helper1.create_user(user_name=domain_u2, email='{0}@{1}'.format(domain_u2, domain_smtp),
                                               domain=domain_name)
            except SDKException as excp:
                if excp.exception_id == '103':
                    self.log.info('User already exists on IdP')
                else:
                    raise excp
            self.log.info("Step 23: Creating the UsergroupHelper for Service commcell")
            self._user_group_helper1 = UsergroupHelper(self.sc_object)
            self.log.info("Step 24: Creating the Usergroup on Service commcell")
            self._user_group_helper1.create_usergroup(group_name='Domain Admins',
                                                      domain=domain_name)
            self.log.info("Step 25: Creating the Usergroup on IdP")
            user_grp_object = self._user_group_helper.create_usergroup(group_name='Domain Guests',
                                                                       domain=domain_name)
            self.log.info("Step 26: Creating the same usergroup on service which is created on IdP commcell")
            self._user_group_helper1.create_usergroup(group_name=user_grp_object.name)


        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
