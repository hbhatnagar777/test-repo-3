# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    init_tc()       --  to initialize basic elements

    send_mail()     --  to send mail report to the user

    generate_html() --  generates the HTML body for the mail

    get_all_methods()   --  returns all the navigation methods in command center

    navigate_to_all()   --  navigates to all the command center pages

    run()           --  run function of this test case

"""

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.mailer import Mailer

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import (
    CVWebAutomationException,
    CVTestCaseInitFailure
)
from Web.Common.page_object import TestStep

from Web.AdminConsole.adminconsole import AdminConsole

from Reports.utils import TestCaseUtils

_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for basic command center integration"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Command Center page load acceptance"
        self.browser = None
        self.driver = None
        self.admin_console = None
        self.navigator = None
        self.utils = None
        self.mailer = None
        self.locale_errors = []
        self.notification_errors = []

    def init_tc(self):
        """ To initialize basic elements needed for the testcase run"""
        try:
            self.utils = TestCaseUtils(self)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.driver = self.browser.driver
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                username=self.inputJSONnode['commcell']['commcellUsername'],
                password=self.inputJSONnode['commcell']['commcellPassword'],
                stay_logged_in=True)
            self.navigator = self.admin_console.navigator

            self.mailer = Mailer({'receiver': self.tcinputs["email_receiver"]}, self.commcell)
        except Exception as exp:
            raise CVTestCaseInitFailure(exp) from exp

    def send_mail(self, html_content):
        """ Send mail """
        self.mailer.mail("Command center pages with issues", html_content)

    def generate_html_page(self):
        """ Generate html page for mail"""
        html = ("<body><p>Hello, localization and notification"
                " errors found on <a href>%s</a><br/><br/> Browser used for this TC: "
                "<b>%s</b></p>" % (self.admin_console.base_url,
                                   self.browser.driver.name.upper()))
        html += '''
        <table style="width:100%" border="2">
            <tr>
                <th>S.NO</th>
                <th>PAGE URL</th>
                <th>FAILURE REASON</th>
            </tr>
        '''

        count = 1
        for error in self.locale_errors:
            html += f'''
            <tr>
                <td align='center'>{count}</td>
                <td align='center'>{error}</td>
                <td align='center'>Locale errors found</td>
            </tr>
            '''
            count += 1
        for error in self.notification_errors:
            html += f'''
            <tr>
                <td align='center'>{count}</td>
                <td align='center'>{error}</td>
                <td align='center'>Notification errors found</td>
            </tr>
            '''
            count += 1
        html += "</table><br><br>"
        return html

    def get_all_methods(self):
        """ Returns all navigation methods in Adminconsole """
        return [method_name for method_name in dir(self.navigator) if 'navigate_to_' in method_name]

    @test_step
    def navigate_to_all(self, methods):
        """ Navigates to all methods exposed in navigation class """
        for each_method in methods:
            nav_method = getattr(self.navigator, each_method)
            try:
                nav_method()
                try:
                    self.admin_console.check_for_locale_errors()
                except CVWebAutomationException as exp:
                    self.log.error(exp)
                    self.locale_errors.append(self.driver.current_url)

                if self.admin_console.get_notification(wait_time=1):
                    self.log.error('Notifications found on %s page loading', self.driver.current_url)
                    self.notification_errors.append(self.driver.current_url)

                if each_method == 'navigate_to_getting_started':
                    self.browser.driver.back()
            except Exception as exp:
                self.log.exception("unable to access [%s] with error %s", each_method, exp)

    def run(self):
        """ Main function for test case execution """
        try:
            self.init_tc()
            method_names = self.get_all_methods()
            self.navigate_to_all(method_names)

            if self.locale_errors or self.notification_errors:
                html = self.generate_html_page()
                self.send_mail(html_content=html)

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
