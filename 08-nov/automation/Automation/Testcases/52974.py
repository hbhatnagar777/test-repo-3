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
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.DeploymentHelper import DeploymentHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from Install import installer_utils


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
        self.package_list = None
        self.admin_console = None
        self.unix_machine = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
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
        install_helper = InstallHelper(self.commcell)
        self.unix_machine = install_helper.get_machine_objects(2)[0]

    def run(self):
        """Main function for test case execution"""

        try:
            install_helper = InstallHelper(self.commcell, self.unix_machine)
            if self.unix_machine.check_registry_exists("Session", "nCVDPORT"):
                install_helper.uninstall_client()
            _minus_value = self.config_json.Install.minus_value
            if len(str(self.commcell.commserv_version)) == 4:
                sp_to_install = "SP" + str(int(str(self.commcell.commserv_version)[:2]) - 2)
            else:
                sp_to_install = "SP" + str(self.commcell.commserv_version - _minus_value)
            silent_install_dict = {
                "csClientName": self.commcell.commserv_name,
                "csHostname": self.commcell.commserv_hostname,
                "authCode": self.commcell.enable_auth_code()
            }
            self.log.info("Determining Media Path for Installation")
            media_path = self.tcinputs.get('MediaPath') if self.tcinputs.get('MediaPath') else ''
            _service_pack_to_install = installer_utils.get_latest_recut_from_xml(sp_to_install)
            if "{sp_to_install}" in media_path:
                media_path = media_path.replace("{sp_to_install}", _service_pack_to_install)

            self.log.info(f"Service Pack used for Installation: {sp_to_install}")
            self.log.info(f"Media Path used for Installation: {media_path}")
            silent_install_dict.update({"mediaPath": media_path})

            self.log.info(f"Starting install on client {self.unix_machine.machine_name}")
            install_helper.silent_install(client_name="acunixclient", tcinputs=silent_install_dict,
                                          feature_release=sp_to_install)
            self.log.info(f"Install successful on client {self.unix_machine.machine_name}")

            client_obj = self.commcell.clients.get(self.unix_machine.machine_name)
            self.log.info(f"Starting update on client {client_obj.client_name}")
            self.deployment_helper.action_update_software(client_name=client_obj.client_name, reboot=True)
            self.log.info(f"Client {client_obj.client_name} updated successfully")

            if client_obj.is_ready:
                self.log.info("Starting Install Validation")
                install_validation = InstallValidator(client_obj.client_hostname, self,
                                                      machine_object=self.unix_machine, is_push_job=True)
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
