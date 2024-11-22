# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Web Console - Forgot password"""

import random
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Laptop.laptoputils import LaptopUtils
from Web.WebConsole.Laptop.gmail_helper import GmailHelper
from Web.Common.exceptions import CVWebAutomationException


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.

    Prerequisite : Create user as "Testuser" with an email "cvlt.pwdtest@gmail.com" in automation setup
                   provide the admin email of the CS as input to testcase.

    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Web Console - Forgot password"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.WEBCONSOLE
        self.show_to_user = True
        self.tcinputs = {
            "webconsole_username": None,
            "webconsole_email": None,
            "password": None,
            "admin_email": None,
        }
        self.browser = None
        self.mail_browser = None
        self.helper = None
        self.driver = None
        self.helper = None
        self.webconsole = None
        self.utils = TestCaseUtils(self)
        self.laptop_utils = LaptopUtils(self)
        self.windows_filename = None
        self.webconsole_username = None
        self.webconsole_email = None
        self.password = None
        self.admin_email = None
        self.pwd_link = None
        self.reset_pwd = None

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.goto_webconsole()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def setup(self):
        """Initializes objects required for this testcase"""
        self.webconsole_username = (self.tcinputs["webconsole_username"])
        self.webconsole_email = (self.tcinputs["webconsole_email"])
        self.password = (self.tcinputs["password"])
        self.admin_email = (self.tcinputs["admin_email"])
        rand_str = str(random.randint(10, 20))
        self.reset_pwd = "Admin!"+rand_str

    @test_step
    def get_reset_pwd_link_from_gmail(self):
        """ Get the reset password link from gmail"""
        self.pwd_link = None
        self.driver = self.browser.driver
        self.helper = GmailHelper(self.driver)
        self.helper.login_to_gmail(self.webconsole_email, self.password)
        self.helper.search_gmail_with_sender(self.admin_email, "Reset your password")
        self.pwd_link = self.helper.get_reset_pwd_link()
        if not self.pwd_link:
            raise CVTestStepFailure("Unable to get the password reset link from gmail")
        self.log.info("Successfully get the password reset link from gmail")
        self.helper.delete_gmail(self.admin_email)

    @test_step
    def verify_with_valid_username(self):
        """ Verify reset password functionality with Username"""
        self.init_tc()
        self.webconsole.forgot_password(self.webconsole_username)
        self.get_reset_pwd_link_from_gmail()
        self.browser.driver.get(self.pwd_link)
        self.webconsole.reset_password(self.reset_pwd, self.reset_pwd)
        self.webconsole.login(self.webconsole_username, self.reset_pwd)
        self.log.info("Successfully login to webconsole with new password")
        self.browser.close()
        self.log.info("***Forgot password validation with ['username'] completed successfuly***")

    @test_step
    def verify_with_valid_email(self):
        """ Verify reset password functionality with email"""
        self.init_tc()
        self.webconsole.forgot_password(self.webconsole_email)
        self.get_reset_pwd_link_from_gmail()
        self.browser.driver.get(self.pwd_link)
        self.webconsole.reset_password(self.reset_pwd, self.reset_pwd)
        self.webconsole.login(self.webconsole_username, self.reset_pwd)
        self.log.info("Successfully login to webconsole with new password")
        self.browser.close()
        self.log.info("***Forgot password validation with ['email id'] completed successfuly***")

    @test_step
    def verify_with_no_username_email(self):
        """ Verify reset password functionality with No Username"""
        self.init_tc()
        try:
            self.webconsole.forgot_password("")
        except CVWebAutomationException as exc:
            self.log.info("Success! As expected: Empty username failed with error: {0}" .format(exc))
        self.browser.close()
        self.log.info("***Forgot password validation with ['empty username'] completed successfuly***")

    def run(self):
        try:
            self.verify_with_valid_username()
            self.verify_with_valid_email()
            self.verify_with_no_username_email()
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            try:
                self.helper.delete_gmail(self.admin_email)
            except Exception as err:
                self.log.info("Failed to delete email{0}".format(err))
            GmailHelper.logout_silently(self.helper)
            Browser.close_silently(self.mail_browser)
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
