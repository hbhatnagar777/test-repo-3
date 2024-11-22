# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This Test Case performs the Sanity Checks MultiCommcell Operations.

1.Create a user on service commcell
2.Create a user on service commcell which already exists on IdP
3.Create a user on service commcell with user group that already exists on IdP
4.create a user on service commcell by associating it with user group that doesnt exists on IdP
5.create a user group on service commcell
6.create a user group on service which already exists on IdP

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


_CONFIG = get_config()

class TestCase(CVTestCase):
    """Class for executing Multicommcell local add and associate operations"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Muticommcell - Local User and Usergroup Create Operations on Service Commcell"
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
            new_user = 'Test_58960' + " " + str(datetime.datetime.today())
            new_user1 = 'Test_589601' + " " + str(datetime.datetime.today())
            new_user2 = 'Test_589602' + " " + str(datetime.datetime.today())
            new_user3 = 'Test_589603' + " " + str(datetime.datetime.today())
            new_ug = 'Testug' + " " + str(datetime.datetime.today())
            new_ug1 = 'Testug1' + " " + str(datetime.datetime.today())
            new_ug2 = 'Testug2' + " " + str(datetime.datetime.today())
            user_password = _CONFIG.MultiCommcell.Local_users_password
            self.log.info("Step 1:Creating a Service commcell object")
            self.router_commcell.get_service_commcell(self.tcinputs["ServiceCommcellName"],
                                                      self.tcinputs["ServiceCommcellAdminUserName"],
                                                      self.tcinputs["ServiceCommcellAdminUserPassword"])
            self.service_commcell_object = self.router_commcell.service_commcell
            self.log.info("Step 2: Creating a UserHelper object directly using service creds")
            self._user_helper = UserHelper(self.service_commcell_object)
            self.log.info("Step 3: Creating a UsergroupHelper object directly using service creds")
            self._user_group_helper = UsergroupHelper(self.service_commcell_object)
            user_grp_object = self._user_group_helper.create_usergroup(group_name=new_ug)
            self.log.info("Step 4: Registering a service commcell for Identity Provider")
            self.router_commcell.register_service_commcell(service_commcell_host_name=self.tcinputs["ServiceCommcellName"],
                                                           service_user_name=self.tcinputs["ServiceCommcellAdminUserName"],
                                                           service_password=self.tcinputs["ServiceCommcellAdminUserPassword"],
                                                           registered_for_idp="True")
            self.utility.sleep_time(10)
            self.log.info("Step 5: Checking the Registration")
            self.router_commcell.check_registration()
            self.log.info("Step 6: Validating the Sync")
            # self.router_commcell.validate_sync()
            self.log.info("Step 7: Login into the service commcell using master's SAML Token")
            self.sc_object = self.router_commcell.get_commcell_object(authtoken=self.commcell.get_saml_token(),
                                                                      service_commcell="True")
            self.log.info("Step 8: Creating a UserHelper object using sc object created using SAML token")
            self._user_helper1 = UserHelper(self.sc_object)
            self.log.info("Step 9: Creating a user on service commcell")
            self._user_helper1.create_user(user_name=new_user, email='a@b.c', password=user_password)
            self.log.info("Step 10: Creating a UserHelper object for master")
            self._user_helper2 = UserHelper(self.commcell)
            self.log.info("Step 11: Creating a user on IdP commcell")
            self._user_helper1.create_user(user_name=new_user1, email='aa@ba.ca', password=user_password)
            try:
                self.log.info("Step 12: Creating the same user on service which is created on IdP commcell")
                self._user_helper1.create_user(user_name=new_user1, email='aa@ba.ca', password=user_password)
            except SDKException as excp:
                if excp.exception_id == '103':
                    self.log.info('User already exists on IdP')
                else:
                    raise excp
            self.log.info("Step 13: Creating a user on Service commcell with usergroup which is already on IdP")
            self._user_helper1.create_user(user_name=new_user2, email='aa@ba.ca', password=user_password,
                                           local_usergroups=[user_grp_object.name])
            self.log.info("Step 14: Creating a UsergroupHelper object using sc object created using SAML token")
            self._ug_helper = UsergroupHelper(self.sc_object)
            self.log.info("Step 15: Creating a Usergroup on service commcell")
            user_grp_object1 = self._ug_helper.create_usergroup(group_name=new_ug1)
            self.log.info("Step 16: Creating a User on service commcell using the group created in step 15")
            self._user_helper1.create_user(user_name=new_user3, email='aaa@baa.caa', password=user_password,
                                           local_usergroups=[user_grp_object1.name])
            self.log.info("Step 17: Creating the usergroup object for master commcell")
            self._ug_helper_master = UsergroupHelper(self.commcell)
            self.log.info("Step 18: Creating the usergroup on master commcell")
            user_grp_object2 = self._ug_helper_master.create_usergroup(group_name=new_ug2)
            self.log.info("Step 19: Creating the same usergroup on service which is created on IdP commcell")
            self._ug_helper.create_usergroup(group_name=user_grp_object2.name)


        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
