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

Inputs:

    UpdatePath     --   path of the diag
"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils import config
from Install import installer_constants
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.DeploymentHelper import DeploymentHelper
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):
    """Class for copying diag to CS cache"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("Install - Admin Console - Copy Software - Windows and Unix diag")
        self.factory = None
        self.browser = None
        self.driver = None
        self.login_obj = None
        self.deployment_helper = None
        self.maintenance = None
        self.tcinputs = {
            'WindowsUpdatePath': None,
            'UnixUpdatePath': None
        }
        self.admin_console = None
        self.config_json = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.factory = BrowserFactory()
        self.browser = self.factory.create_browser_object()
        self.browser.open()
        self.driver = self.browser.driver
        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'],
                                 stay_logged_in=True)
        self.deployment_helper = DeploymentHelper(self, self.admin_console)
        self.config_json = config.get_config()

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Copying Windows diag to CS Cache")
            self.deployment_helper.run_copy_software(
                media_path=self.tcinputs.get('WindowsUpdatePath'), auth=True,
                username=self.tcinputs.get('username', self.config_json.Install.dvd_username),
                password=self.tcinputs.get('password', self.config_json.Install.dvd_password))

            self.log.info("Copying Unix diag to CS Cache")
            self.deployment_helper.run_copy_software(
                media_path=self.tcinputs.get('UnixUpdatePath'), auth=True,
                username=self.tcinputs.get('username', self.config_json.Install.dvd_username),
                password=self.tcinputs.get('password', self.config_json.Install.dvd_password))

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
