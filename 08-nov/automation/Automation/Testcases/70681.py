# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

Basic login test case for secure ldap via proxy in AdminConsole

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic, and it is the one executed

"""
import time
from AutomationUtils.cvtestcase import CVTestCase
from Server.Security.userhelper import UserHelper
from Server.Security.userconstants import WebConstants
from Web.Common.page_object import handle_testcase_exception
from cvpysdk.client import Client


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object

            Testcase json example:

            "70681":
                {
            "netbios_name1": None,
            "domain_name1": None,
            "domain_username1": None,
            "domain_password1": None,
            "netbios_name2": None,
            "domain_name2": None,
            "domain_username2": None,
            "domain_password2": None,
            "external_user_group1": None,
            "login_username": None,
            "login_password": None,

                }

        """

        super(TestCase, self).__init__()
        self.name = "Cross Domain Login"
        self.result_string = "Successful"
        self.user_helper = None
        self.client_machine = None
        self.tcinputs = {
            "netbios_name1": None,
            "domain_name1": None,
            "domain_username1": None,
            "domain_password1": None,
            "netbios_name2": None,
            "domain_name2": None,
            "domain_username2": None,
            "domain_password2": None,
            "external_user_group1": None,
            "login_username": None,
            "login_password": None,
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self.client_machine = Client(self._commcell, self._commcell.commserv_client.client_hostname)
        self.user_helper = UserHelper(self.commcell)

    def run(self):
        try:
            self.log.info("*********Adding the domains*********")
            self.commcell.domains.add(domain_name=self.tcinputs['domain_name1'],
                                      netbios_name=self.tcinputs['netbios_name1'],
                                      user_name=self.tcinputs['domain_username1'],
                                      password=self.tcinputs['domain_password1'], company_id=0)

            self.commcell.domains.add(domain_name=self.tcinputs['domain_name2'],
                                      netbios_name=self.tcinputs['netbios_name2'],
                                      user_name=self.tcinputs['domain_username2'],
                                      password=self.tcinputs['domain_password2'], company_id=0)

            self.commcell.user_groups.add(usergroup_name=self.tcinputs['external_user_group1'],
                                          domain=self.tcinputs['netbios_name2'], local_usergroup=['master'])

            if "windows" in self.client_machine.os_info.lower():
                self.commcell.add_additional_setting(category="CommServe",
                                                     key_name="bDontTurnOnReferrals",
                                                     data_type="Integer",
                                                     value="0")
                self.log.info("Performing IISRESET")
                self.commcell.commserv_client.execute_command('iisreset')
            else:
                self.commcell.add_additional_setting(category="CommServe",
                                                     key_name="bIterativeUGLookUpOnDomain",
                                                     data_type="Integer",
                                                     value="1")
                self.commcell.add_additional_setting(category="CommServe",
                                                     key_name="bShouldReturnMemberGroupDN",
                                                     data_type="Integer",
                                                     value="1")
                self.log.info("Performing commvault restart")
                self.commcell.commserv_client.restart_services()
            time.sleep(120)

            self.log.info("*********Login from adminconsole and webconsole*********")
            self.user_helper.web_login(user_name=self.tcinputs['login_username'],
                                       password=self.tcinputs['login_password'],
                                       web=WebConstants(self.commcell.commserv_hostname))

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """To clean up the test case environment created"""
        self.log.info("Deleting additional key")
        if "windows" in self.client_machine.os_info.lower():
            self.commcell.delete_additional_setting(category="CommServe",
                                                    key_name="bDontTurnOnReferrals")
        else:
            self.commcell.delete_additional_setting(category="CommServe",
                                                    key_name="bIterativeUGLookUpOnDomain")
            self.commcell.delete_additional_setting(category="CommServe",
                                                    key_name="bShouldReturnMemberGroupDN")

        self.commcell.refresh()
        self.commcell.domains.delete(self.tcinputs['netbios_name1'])
        self.commcell.domains.delete(self.tcinputs['netbios_name2'])
        
