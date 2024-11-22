from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

**Note**
1. Requires trials.txt file for testcase execution if not case is skipped

2. For Internet Explorer follow below configurations

    * set same Security level in all zone

    * disable "Enable protected mode"

    * Allow websites in less privileged zone to access this zone

"""

import json

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Setup.login import LoginPage


class TestCase(CVTestCase):
    """Class to perform admin console validation on different browsers"""
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Commvault Express trial - Browser verification for AdminConsole (Chrome, Firefox, IE)"
        self.browser = None
        self.driver = None
        self.helper = None
        self.trial_file = None
        self.contents = None
        self.result_string = ''

        self.machine = Machine()

    def login(self, url, username, password, browser_type):
        """To login to admin console page"""
        # To open the browser based on the Type
        browser = f"Browser.Types.{browser_type}"
        self.browser = BrowserFactory().create_browser_object(eval(browser))
        self.browser.open()
        self.log.info("Opened browser: %s", browser_type)

        self.driver = self.browser.driver
        self.helper = LoginPage(self.driver)

        # To login to adminconsole
        self.helper.navigate(url)
        self.helper.login(username, password)
        self.helper.wait_for_completion()

        # To validate admin console login
        self.driver.find_element(By.XPATH, '//span[text()="Dashboard"]')
        self.log.info("%s browser login validation successful", browser_type)

    def run(self):
        """Main function for test case execution"""
        try:
            self.trial_file = self.machine.join_path(constants.CVTRIALS_DIRECTORY, 'trials.txt')
            self.contents = json.loads(self.machine.read_file(self.trial_file))
            assert self.contents['status'] == 'passed'

        except Exception as err:
            self.log.error(err)
            self.status = constants.SKIPPED
            return

        browser_list = ["CHROME", "IE", "FIREFOX"]

        for browser in browser_list:
            try:
                self.login(
                    self.contents.get('URL'),
                    self.contents.get('Commvault ID'),
                    self.contents.get('Password'),
                    browser
                )
                self.helper.logout()
                self.log.info("%s browser Admin console validation successful", browser)
            except Exception as exp:
                self.log.error("%s browser validation failed\nerror: %s", browser, exp)
                self.result_string += f'\n{browser} browser validation failed \t\nerror: "{exp}"'
            finally:
                try:
                    Browser.close_silently(self.browser)
                except Exception as exp:
                    self.log.error('Exception occurred when closing the %s browser: "%s"', browser, exp)

        if self.result_string:
            self.status = constants.FAILED
