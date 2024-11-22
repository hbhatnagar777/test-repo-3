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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

**Note** Requires trials.txt file for testcase execution if not case is skipped

"""

import json

from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.AdminConsole.Setup.login import LoginPage
from CVTrials.trial_helper import TrialHelper
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for registering commvault trial package"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Commvault Express trial - core setup completion"
        self.helper = None
        self.browser = None
        self.driver = None
        self.trial_file = None
        self.contents = None

        self.machine = Machine()
        self.utils = TestCaseUtils(self)

    def setup(self):
        """Initializes pre-requisites for this test case"""
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.driver = self.browser.driver
        self.helper = TrialHelper(self)

    def run(self):
        """Main function for test case execution"""
        try:
            try:
                self.trial_file = self.machine.join_path(constants.CVTRIALS_DIRECTORY, 'trials.txt')
                self.contents = json.loads(self.machine.read_file(self.trial_file))
                assert self.contents['status'] == 'passed'
                self.contents['status'] = 'failed'
            except Exception as err:
                self.log.error(err)
                self.status = constants.SKIPPED
                return

            # To login to admin console
            login = LoginPage(self.driver)

            url = f"{self.contents['URL']}/#/gettingStarted"
            # To navigate to admin console page
            login.navigate(url)

            login.login(
                self.contents.get('Commvault ID'),
                self.contents.get('Password')
            )

            # Convert URL like 'http://server.com/adminconsole' -> 'server.com'
            self.helper.admin_console = AdminConsole(self.browser, self.contents['URL'].split('/')[-2])
            self.helper.configure_core_setup(
                pool_name='CommvaultonePool',
                path=r'C:\Commvaultone',
                partition_path=r'C:\Commvaultone'
            )

            self.contents['status'] = "passed"

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            with open(self.trial_file, 'w') as file:
                file.write(json.dumps(self.contents))

    def tear_down(self):
        """To clean-up the test case environment created"""
        # To close the browser
        Browser.close_silently(self.browser)
