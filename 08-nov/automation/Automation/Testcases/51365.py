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

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.DeploymentHelper import DeploymentHelper
from Web.AdminConsole.Helper import adminconsoleconstants as acc
from Web.AdminConsole.AdminConsolePages.maintenance import Maintenance
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):
    """Class for updating unix client in Admin Console"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Admin Console: Push SP and hotfixes to unix Client"
        self.factory = None
        self.browser = None
        self.driver = None
        self.login_obj = None
        self.deployment_helper = None
        self.maintenance = None
        self.admin_console = None

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

    def run(self):
        """Main function for test case execution"""

        try:
            schedule_options = {
                'frequency': 'Weekly',
                'hours': '01',
                'mins': '00',
                'session': 'AM',
                'days': ['Wednesday'],
                'repeatWeek': '4',
                'exceptions': True,
                'day_exceptions': True,
                'week_exceptions': False,
                'exception_days': ['1', '2'],
                'repeat': True,
                'repeat_hrs': '24',
                'repeat_mins': '00',
                'until_hrs': '11',
                'until_mins': '59',
                'until_sess': 'PM'
            }

            self.deployment_helper.edit_download_schedule(
                download_option=acc.DownloadOptions.LATEST_HF_FOR_INSTALLED_SP.value,
                os_to_download=[acc.DownloadOSID.WINDOWS_64.value,
                                acc.DownloadOSID.UNIX_LINUX64.value],
                schedule_options=schedule_options
            )

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
