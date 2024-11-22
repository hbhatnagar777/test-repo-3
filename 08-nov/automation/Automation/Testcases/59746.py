# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

bAllowSingleSessionPerUser[single session per user].

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    second_session()            --  Login verification for admin console

    restart_webservice()        --  Restart Webserver Service

    run()                       --  Contains the core testcase logic, and it is the one executed

    tear_down()                 --  Clean up entities

"""

import time
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Server.Security.userhelper import UserHelper
from Server.mongodb_helper import MongoDBHelper
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "bAllowSingleSessionPerUser[single session per user]"
        self.browser = None
        self.client_obj = None
        self.webserver_name = None
        self.local_user_name = None
        self.local_user_email = None
        self.result_string = "Successful"
        self.user_helper = None

    def setup(self):
        """Initializes pre-requisites for test case"""
        self.user_helper = UserHelper(self.commcell)
        self.webserver_name = MongoDBHelper.get_default_webserver(self.csdb)[0]
        self.client_obj = self.commcell.clients.get(self.webserver_name)
        self.local_user_name = 'local_user' + str(datetime.today().microsecond)
        self.local_user_email = self.local_user_name + "@commvault.com"

    @test_step
    def second_session(self, username, password):
        """*********Command Center Login for second session to verify active sessions*********"""
        browser = BrowserFactory().create_browser_object()
        browser.open()
        try:
            session = AdminConsole(browser, self.commcell.webconsole_hostname)
            rtable = Rtable(session, id='UserSessions')
            session.login(username, password)
            session.check_error_message()
            session.account_activity()
            if rtable.get_total_rows_count() > 1:
                raise Exception("Multiple active sessions detected.")
            AdminConsole.logout(session)
        except CVWebAutomationException as exp:
            handle_testcase_exception(self, exp)
        finally:
            Browser.close_silently(browser)

    @test_step
    def restart_webservice(self):
        """*********Restart Webserver Service*********"""
        if 'unix' in self.client_obj.os_info.lower():
            self.client_obj.execute_command("commvault restart -s WebServerCore")
        else:
            self.client_obj.execute_command("iisreset")
        time.sleep(30)

    def run(self):
        self.log.info("*********Creating local user*********")
        password = self.user_helper.password_generator(3, 12)
        self.user_helper.create_user(user_name=self.local_user_name, email=self.local_user_email,
                                     full_name='local_user', password=password)

        self.log.info("*********Adding additional setting - bAllowSingleSessionPerUser*********")
        self.commcell.add_additional_setting("CommServDB.Console", "bAllowSingleSessionPerUser", "BOOLEAN", "true")
        self.restart_webservice()
        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        try:
            first_session = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            first_session.login(self.local_user_name, password)
            self.second_session(self.local_user_name, password)
            first_session.refresh_page()
            if first_session._is_logout_page():
                self.log.info("First session is ended after second session login.")
            else:
                first_session.logout()
                raise Exception("First session is still active.")
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """To clean up the test case environment created"""
        Browser.close(self.browser)
        self.user_helper.cleanup_users(self.local_user_name)
        self.commcell.delete_additional_setting("CommServDB.Console", "bAllowSingleSessionPerUser")
        self.restart_webservice()
