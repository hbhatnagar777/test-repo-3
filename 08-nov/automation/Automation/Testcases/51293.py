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
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator


class TestCase(CVTestCase):
    """Class for uninstalling packages in windows machine in Admin Console"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Install- Admin Console- Uninstall packages - Windows "
        self.factory = None
        self.browser = None
        self.driver = None
        self.deployment_helper = None
        self.admin_console = None
        self.windows_machine = None
        self.windows_helper = None

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
        install_helper = InstallHelper(self.commcell)
        self.windows_machine = install_helper.get_machine_objects(1)[0]
        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)

    def run(self):
        """Main function for test case execution"""

        try:
            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                self.windows_helper.uninstall_client(delete_client=True)
            silent_install_dict = {
                "csClientName": self.commcell.commserv_name,
                "csHostname": self.commcell.commserv_hostname,
                "authCode": self.commcell.enable_auth_code()
            }
            _package = "MEDIA_AGENT"
            self.log.info(f"Starting install on client {self.windows_machine.machine_name}")
            self.windows_helper.silent_install(client_name="windows_client",
                                               tcinputs=silent_install_dict, packages=_package)
            self.commcell.clients.refresh()
            if self.commcell.clients.has_client(self.windows_machine.machine_name):
                client_obj = self.commcell.clients.get(self.windows_machine.machine_name)
                if client_obj.is_ready:
                    self.log.info("Check Readiness of Client is successful")
            else:
                self.log.error("Client failed Registration to the CS")
                raise Exception(f"Client: {self.windows_machine.machine_name} failed registering to the CS,"
                                f" Please check client logs")

            self.log.info(f"Package to be uninstalled {_package}")
            self.deployment_helper.action_uninstall_software(
                client_name=self.tcinputs.get('DeploymentClientName'), packages=_package)
            if client_obj.is_ready:
                self.log.info("Starting Install Validation")
                install_validation = InstallValidator(client_obj.client_hostname, self,
                                                      machine_object=self.windows_machine)
                install_validation.validate_install()
            else:
                raise Exception("Client services are down!!")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
