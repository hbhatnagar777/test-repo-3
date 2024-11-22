# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

Verify Stay Logged In and Additional Settings - Hide Stay Logged In, Session Timeout Minutes.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    adminconsole_login()        --  Login verification for admin console

    restart_tomcat_service()    --  Restart Tomcat Service

    run()                       --  Contains the core testcase logic, and it is the one executed

    tear_down()                 --  Clean up entities

"""

import time
from datetime import datetime
from cvpysdk.client import Clients, Client
from AutomationUtils.cvtestcase import CVTestCase
from Server.Security.userhelper import UserHelper
from Server.organizationhelper import OrganizationHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Testcase json example:

            "70805":
                {
                "domain_name": None,
                "netbios_name": None,
                "service_account_user_name": None,
                "service_account_password": None,
                "ad_username": None,
                "ad_email": None,
                "ad_password": None
                }

        """
        super(TestCase, self).__init__()
        self.name = "Verify Stay Logged In and Additional Settings - Hide Stay Logged In, Session Timeout Minutes."
        self.admin_console = None
        self.user_helper = None
        self.client_obj = None
        self.client_name = None
        self.organization_helper = None
        self.local_user_name = None
        self.local_user_email = None
        self.company_name = None
        self.tenant_admin_user = None
        self.additional_setting = True
        self.result_string = "Successful"
        self.tcinputs = {
            "domain_name": None,
            "netbios_name": None,
            "service_account_user_name": None,
            "service_account_password": None,
            "ad_username": None,
            "ad_email": None,
            "ad_password": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self.user_helper = UserHelper(self.commcell)
        self.client_name = Clients(self.commcell)._get_client_from_hostname(self.commcell.webconsole_hostname)
        self.client_obj = self.commcell.clients.get(self.client_name)
        self.client = Client(self.commcell, self.client_name)
        self.organization_helper = OrganizationHelper(self.commcell)
        self.local_user_name = 'local_user' + str(datetime.today().microsecond)
        self.local_user_email = self.local_user_name + "@commvault.com"
        self.company_name = 'company70805' + str(datetime.today().microsecond)
        self.tenant_admin_user = 'tenant_admin_user' + str(datetime.today().microsecond)

    @test_step
    def adminconsole_login(self, username, password, stay_logged_in=False, expected_timeout=None,
                           hide_stay_logged_in=False, check_session=False):
        """*********Command Center Login*********"""
        browser = BrowserFactory().create_browser_object()
        browser.open()
        try:
            console = AdminConsole(browser, self.commcell.webconsole_hostname)
            console.login(username, password, stay_logged_in=stay_logged_in, hide_stay_logged_in=hide_stay_logged_in)
            console.check_error_message()

            self.csdb.execute(f"SELECT timeout FROM UMQSDKSessions WHERE userName='{username}'")
            timeout_from_db = int(self.csdb.fetch_one_row()[0])
            self.log.info(f"Session Timeout value for {username} from DB: {timeout_from_db} minutes")

            cookies = browser.driver.get_cookie('acLogoutTimer')
            timeout_from_cookie = int(cookies['value']) // 60
            self.log.info(f"Session Timeout value for {username} from cookie: {timeout_from_cookie} minutes")

            if not timeout_from_db == expected_timeout == timeout_from_cookie:
                raise Exception(f"Unexpected session timeout value for user '{username}'. DB Timeout: {timeout_from_db}"
                                f" minutes, Cookie Timeout: {timeout_from_cookie} minutes."
                                f" Expected: {expected_timeout} minutes.")

            if check_session:
                self.log.info("*********Waiting for session to expire and verifying removal from DB*********")
                time.sleep((expected_timeout + 3) * 60)

                if not console._is_logout_page():
                    raise Exception(f"User session for '{username}' is still active")
                else:
                    self.log.info(f"User session for '{username}' ended in the UI after the specified timeout.")

                self.csdb.execute(f"SELECT COUNT(*) FROM UMQSDKSessions WHERE userName='{username}'")
                session_count = int(self.csdb.fetch_one_row()[0])
                if session_count != 0:
                    raise Exception(f"User session for '{username}' is still present in the database.")
                else:
                    self.log.info(f"User session for '{username}' has been removed the database.")
            else:
                AdminConsole.logout(console)

        except CVWebAutomationException as exp:
            handle_testcase_exception(self, exp)
        finally:
            Browser.close_silently(browser)

    @test_step
    def restart_tomcat_service(self):
        """*********Restart Tomcat Service*********"""
        if 'unix' in self.client_obj.os_info.lower():
            self.client_obj.restart_service('Tomcat')
        else:
            self.client_obj.restart_service('GxTomcatInstance001')
        time.sleep(120)

    def run(self):
        try:
            self.log.info("*********Creating local user*********")
            password = self.user_helper.password_generator(3, 12)
            self.user_helper.create_user(user_name=self.local_user_name, email=self.local_user_email,
                                         full_name='local_user', password=password)

            self.log.info("*********Creating company and user*********")
            self.organization_helper.create(name=self.company_name, company_alias=self.company_name)

            self.organization_helper = OrganizationHelper(self.commcell, company=self.company_name)
            self.organization_helper.add_new_company_user_and_make_tenant_admin(self.tenant_admin_user, password)

            self.log.info("*********Creating Active Directory and Ad User*********")
            self.commcell.domains.add(domain_name=self.tcinputs['domain_name'],
                                      netbios_name=self.tcinputs['netbios_name'],
                                      user_name=self.tcinputs['service_account_user_name'],
                                      password=self.tcinputs['service_account_password'],
                                      company_id=0)

            self.user_helper.create_user(user_name=self.tcinputs['ad_username'], email=self.tcinputs['ad_email'],
                                         domain=self.tcinputs['netbios_name'],
                                         local_usergroups=['master'])

            self.log.info("*********Adding additional setting - hideStayLoggedIn and Timeout is 30 minutes*********")
            self.client.add_additional_setting("WebConsole", "hideStayLoggedIn", "BOOLEAN", "true")
            time.sleep(120)
            self.adminconsole_login(self.local_user_name, password, expected_timeout=30, hide_stay_logged_in=True)
            self.client.delete_additional_setting("WebConsole", "hideStayLoggedIn")
            self.additional_setting = False

            self.log.info(
                "*********Adding additional setting - SessionTimeoutMinutes and Timeout is 2 minutes*********")
            self.client.add_additional_setting("WebConsole", "SessionTimeoutMinutes", "INTEGER", "2")
            self.restart_tomcat_service()
            self.adminconsole_login(self.local_user_name, password, expected_timeout=2, check_session=True)
            self.adminconsole_login(self.company_name + '\\' + self.tenant_admin_user, password,
                                    expected_timeout=2, check_session=True)
            self.adminconsole_login(self.tcinputs['netbios_name'] + '\\' + self.tcinputs['ad_username'],
                                    self.tcinputs['ad_password'], expected_timeout=2, check_session=True)

            self.log.info("*********Performing Stay Logged In functionality and Timeout is 20160 minutes*********")
            self.adminconsole_login(self.local_user_name, password, expected_timeout=20160, stay_logged_in=True)
            self.adminconsole_login(self.company_name + '\\' + self.tenant_admin_user, password,
                                    expected_timeout=20160, stay_logged_in=True)
            self.adminconsole_login(self.tcinputs['netbios_name'] + '\\' + self.tcinputs['ad_username'],
                                    self.tcinputs['ad_password'],
                                    expected_timeout=20160, stay_logged_in=True)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """To clean up the test case environment created"""
        self.user_helper.cleanup_users(self.local_user_name)
        self.organization_helper.cleanup_orgs(self.company_name)
        if self.additional_setting:
            self.client.delete_additional_setting("WebConsole", "hideStayLoggedIn")
        self.client.delete_additional_setting("WebConsole", "SessionTimeoutMinutes")
        if self.commcell.domains.has_domain(self.tcinputs['netbios_name']):
            self.commcell.domains.delete(self.tcinputs['netbios_name'])
        self.restart_tomcat_service()
