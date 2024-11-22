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

    DeploymentClientName    --  the client to uninstall software on

    Packages       --   comma separated string of packages to be uninstalled
        Example: Packages = "File System, Oracle"

        **Note**
            * If  "All" is given in Packages, it will uninstall all the packages

            * Install or uninstall can be done only on packages listed on the Admin Console

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.DeploymentHelper import DeploymentHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper import adminconsoleconstants as acc


class TestCase(CVTestCase):
    """Class for uninstalling unix packages in Admin Console"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Admin Console: Push uninstall single and all packages - Unix"
        self.factory = None
        self.browser = None
        self.driver = None
        self.login_obj = None
        self.deployment_helper = None
        self.admin_console = None
        self.tcinputs = {
            "DeploymentClientName": None,
            "Packages": None
        }

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
            uninstall_list = self.deployment_helper.get_package_names()
            packages = [eval("acc.Packages." + packages + ".value") for packages in uninstall_list]
            self.deployment_helper.action_uninstall_software(
                client_name=self.tcinputs.get('DeploymentClientName'),
                packages=packages
            )

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
