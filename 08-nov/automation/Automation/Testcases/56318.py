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

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants, config
from Install.install_helper import InstallHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.DeploymentHelper import DeploymentHelper
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):
    """Class for retiring client from Admin Console"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Retire Client from Admin Console"
        self.factory = None
        self.browser = None
        self.driver = None
        self.admin_console = None
        self.deployment_helper = None
        self.machine_objects = None
        self.unix_machine = None
        self.config_json = None
        self.rc_client = None
        self.status = constants.PASSED
        self.result_string = ''

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.factory = BrowserFactory()
        self.browser = self.factory.create_browser_object()
        self.browser.open()
        self.driver = self.browser.driver
        self.config_json = config.get_config()
        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'],
                                 stay_logged_in=True)
        self.deployment_helper = DeploymentHelper(self, self.admin_console)
        install_helper = InstallHelper(self.commcell)
        self.machine_objects = install_helper.get_machine_objects()
        self.unix_machine = install_helper.get_machine_objects(2)[0]

    def run(self):
        """Main function for test case execution"""

        try:
            install_helper = InstallHelper(self.commcell, self.unix_machine)
            if not self.commcell.clients.has_client(install_helper.client_host):
                if self.unix_machine.check_registry_exists("Session", "nCVDPORT"):
                    install_helper.uninstall_client(delete_client=True)
                self.log.info(f"Creating {self.unix_machine.os_info} client")
                if self.commcell.is_linux_commserv:
                    # Configuring Remote Cache Client to Push Software to Windows Client
                    self.log.info("Checking for Windows Remote Cache as Linux CS does not support "
                                  "Direct push Installation to Windows Client")
                    rc_client_name = self.config_json.Install.rc_client.client_name
                    if self.commcell.clients.has_client(rc_client_name):
                        self.rc_client = self.commcell.clients.get(rc_client_name)
                job = install_helper.install_software(
                    client_computers=[self.unix_machine.machine_name],
                    sw_cache_client=self.rc_client.client_name if self.rc_client else None)

                if not job.wait_for_completion():
                    raise Exception(f"{self.unix_machine.os_info} Client installation Failed")

            self.commcell.clients.refresh()
            if self.commcell.clients.has_client(self.unix_machine.machine_name):
                client_obj = self.commcell.clients.get(self.unix_machine.machine_name)
                if client_obj.is_ready:
                    self.log.info("Check Readiness of Client is successful")
            else:
                self.log.error("Client failed Registration to the CS")
                raise Exception(f"Client: {self.unix_machine.machine_name} failed registering to the CS,"
                                f" Please check client logs")

            self.log.info(f"Retiring client {client_obj.client_name}")
            self.deployment_helper.retire_server(server_name=client_obj.client_name)

            self.commcell.clients.refresh()
            if self.commcell.clients.has_client(self.unix_machine.machine_name):
                raise Exception("Client not removed from CS")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
