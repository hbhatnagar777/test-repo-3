# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  initialize TestCase class

    setup()                 --  setup function of this test case

    run()                   --  run function of this test case

    tear_down()             --  tear down function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from Install.installer_constants import DEFAULT_COMMSERV_USER
from Install.install_validator import InstallValidator
from Install.update_helper import UpdateHelper
from AutomationUtils import config, constants
from AutomationUtils.machine import Machine
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures, WindowsDownloadFeatures


class TestCase(CVTestCase):
    """Testcase : Push SP update of windows and unix Web Servers"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Push SP update of windows and unix Web Servers"
        self.windows_machine = None
        self.unix_machine = None
        self.config_json = None
        self.update_helper = None
        self.company = None
        self.tcinputs = {
            'ServicePack': None
        }
        self.result_string = ''
        self.status = constants.PASSED

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                commcell_username=DEFAULT_COMMSERV_USER,
                commcell_password=self.config_json.Install.cs_password)
        self.company = self.config_json.Install.rc_automation.company
        self.windows_machine = Machine(
            machine_name=self.config_json.Install.win_web_server.machine_host,
            username=self.config_json.Install.win_web_server.machine_username,
            password=self.config_json.Install.win_web_server.machine_password)
        self.unix_machine = Machine(
            machine_name=self.config_json.Install.unix_web_server.machine_host,
            username=self.config_json.Install.unix_web_server.machine_username,
            password=self.config_json.Install.unix_web_server.machine_password)
        self.update_helper = UpdateHelper(self.commcell)

    def run(self):
        """Run function of this test case"""
        try:

            _windows_client_obj = self.commcell.clients.get(self.windows_machine.machine_name)
            _unix_client_obj = self.commcell.clients.get(self.unix_machine.machine_name)
            clients = [_windows_client_obj.client_name, _unix_client_obj.client_name]

            # Push SP upgrade on clients
            self.log.info(f"Push SP upgrade on clients {clients[0]}, {clients[1]}")
            job_obj = self.commcell.push_servicepack_and_hotfix(
                client_computers=clients, reboot_client=True)
            if self.update_helper.check_job_status(job_obj, wait_time=90):
                self.log.info(f"Successfully finished Upgrading clients")
            else:
                raise Exception("Upgrade job failed!!")
            self.log.info("Initiating Check Readiness from the CS")
            for each_client in [self.windows_machine.machine_name, self.unix_machine.machine_name]:
                if self.commcell.clients.has_client(each_client):
                    client_obj = self.commcell.clients.get(each_client)
                    if client_obj.is_ready:
                        self.log.info(f"Check Readiness of Client {each_client} is successful")
                else:
                    self.log.error(f"Client {each_client} failed Registration to the CS")
                    raise Exception(
                        f"Client: {each_client} failed registering to the CS, Please check client logs")

                self.log.info(f"Starting Upgrade Validation of client {each_client}")
                if each_client == self.windows_machine.machine_name:
                    pkg_list = [WindowsDownloadFeatures.WEB_SERVER.value]
                else:
                    pkg_list = [UnixDownloadFeatures.WEB_SERVER.value]
                install_validation = InstallValidator(each_client, self, is_push_job=True,package_list=pkg_list)
                install_validation.validate_install()

        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED
