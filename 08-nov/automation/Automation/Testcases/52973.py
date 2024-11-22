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

    DeploymentClientName    --  the client to update software on

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants, config
from AutomationUtils.machine import Machine
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.DeploymentHelper import DeploymentHelper
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):
    """Class for updating windows client in Admin Console"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Admin Console: Push SP and hotfixes to windows Client"
        self.factory = None
        self.browser = None
        self.driver = None
        self.deployment_helper = None
        self.config_json = None
        self.admin_console = None
        self.package_list = None

    def setup(self):
        self.config_json = config.get_config()
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
            _machine_name = self.config_json.Install.windows_client.machine_host
            _username = self.config_json.Install.windows_client.machine_username
            _password = self.config_json.Install.windows_client.machine_password
            client_machine = Machine(machine_name=_machine_name, username=_username, password=_password)
            installer_obj = InstallHelper(self.commcell, client_machine)
            _minus_value = self.config_json.Install.minus_value
            if client_machine.check_registry_exists("Session", "nCVDPORT"):
                installer_obj.uninstall_client()
            if len(str(self.commcell.commserv_version)) == 4:
                sp_to_install = "SP" + str(int(str(self.commcell.commserv_version)[:2]) - 2)
            else:
                sp_to_install = "SP" + str(self.commcell.commserv_version - _minus_value)
            silent_install_dict = {
                "csClientName": self.commcell.commserv_name,
                "csHostname": self.commcell.commserv_hostname,
                "authCode": self.commcell.enable_auth_code()
            }
            self.log.info(f"Starting install on client {_machine_name}")
            self.log.info(f"SP to install: {sp_to_install}")
            installer_obj.silent_install(client_name=self.config_json.Install.windows_client.client_name,
                                         tcinputs=silent_install_dict,
                                         feature_release=sp_to_install)
            self.log.info(f"Install successful on client {_machine_name}")

            client_obj = self.commcell.clients.get(client_machine.machine_name)
            self.log.info(f"Starting update on client {client_obj.client_name}")
            self.deployment_helper.action_update_software(client_name=client_obj.client_name, reboot=True)
            self.log.info(f"Client {client_obj.client_name} updated successfully")

            if client_obj.is_ready:
                self.log.info("Starting Install Validation")
                install_validation = InstallValidator(client_obj.client_hostname, self,
                                                      machine_object=client_machine, is_push_job=True)
                install_validation.validate_install()
            else:
                raise Exception("Client services are down; Upgrade Unsuccessful")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
