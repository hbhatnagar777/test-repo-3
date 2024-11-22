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

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from urllib.parse import urlparse
from Web.AdminConsole.Setup.getting_started import GettingStarted


class TestCase(CVTestCase):
    """Class to validate Loopy UI linking, redirection and unlinking"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Loopy]: UI  validation for linking, redirection and unlinking"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.onprem_url = None
        self.metallic_url = None
        self.getting_started = None
        self.tcinputs = {
            'CloudCSHostName': None,
            'CloudCompanyUserName': None,
            'CloudCompanyPassword': None,
        }

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.getting_started = GettingStarted(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def register_to_metallic(self):
        """Register to metallic services"""

        self.getting_started.navigate_to_metallic()
        self.onprem_url = self.admin_console.current_url()
        self.getting_started.link_metallic_account(self.tcinputs['CloudCompanyUserName'],
                                                   self.tcinputs['CloudCompanyPassword'])

    @test_step
    def redirect_to_metallic(self):
        """Redirect to metallic commcell and navigate to different pages"""

        self.navigator.switch_service_commcell("Metallic")
        if not urlparse(self.admin_console.current_url()).netloc == self.tcinputs['CloudCSHostName']:
            raise Exception("Redirection Failed")
        self.metallic_url = self.admin_console.current_url()
        self.navigator.navigate_to_server_groups()
        self.navigator.navigate_to_dashboard()
        self.navigator.navigate_to_jobs()

    @test_step
    def unregister_to_metallic(self):
        """Unregister to metallic services"""

        self.admin_console.driver.get(self.onprem_url)
        self.getting_started.unlink_metallic_account()

    def run(self):
        try:
            self.init_tc()
            self.register_to_metallic()
            self.redirect_to_metallic()
            self.unregister_to_metallic()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
