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
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.DeploymentHelper import DeploymentHelper
from Web.AdminConsole.Helper import adminconsoleconstants as acc
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):
    """Class for downloading updates using the second option"""
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = ("Install- Admin Console - Verify download software for LTS "
                     "option 'Upgrade to Latest Release")
        self.factory = None
        self.browser = None
        self.driver = None
        self.login_obj = None
        self.deployment_helper = None
        self.maintenance = None
        self.admin_console = None

    def setup(self):
        self.factory = BrowserFactory()
        self.browser = self.factory.create_browser_object()
        self.browser.open()
        self.driver = self.browser.driver
        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'],
                                 stay_logged_in=True)
        self.deployment_helper = DeploymentHelper(self, self.admin_console)

    def run(self):
        try:
            self.deployment_helper.run_download_software(
                download_option=acc.DownloadOptions.LATEST_SP.value,
                os_to_download=[acc.DownloadOSID.WINDOWS_64.value])

            self.deployment_helper.run_download_software(
                download_option=acc.DownloadOptions.LATEST_SP.value,
                os_to_download=[acc.DownloadOSID.WINDOWS_64.value,
                                acc.DownloadOSID.UNIX_LINUX64.value])

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
