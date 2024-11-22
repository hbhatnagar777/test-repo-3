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

    Hostname    --  the client to install software on

    Username    --  username of the host machine

    Password    --  password of the host machine

    Packages       --   comma separated string of packages to be uninstalled
        Example: Packages = "File System, Oracle"

    **Note**

            * If  "All" is given in Packages, it will install all the packages

            * Install or uninstall can be done only on packages listed on the Admin Console

            * This test case is for new client without multiple instances

            * Give the full hostname of the client machine as input

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants, config
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.DeploymentHelper import DeploymentHelper
from Web.AdminConsole.Helper.adminconsoleconstants import Packages
from Web.AdminConsole.adminconsole import AdminConsole
from Install import installer_constants, installer_utils
from Install.install_validator import InstallValidator
from Install.install_helper import InstallHelper
from cvpysdk.deployment.deploymentconstants import DownloadPackages, DownloadOptions, WindowsDownloadFeatures


class TestCase(CVTestCase):

    """Class for installing new windows client and adding software to the client in Admin Console"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Install- Admin Console - Install new windows client"
        self.factory = None
        self.browser = None
        self.driver = None
        self.config_json = None
        self.deployment_helper = None
        self.rc_client = None
        self.admin_console = None
        self.status = constants.PASSED
        self.result_string = ''
        self.tcinputs = {
            "ServicePack": None
        }

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

    def run(self):
        """Main function for test case execution"""

        try:
            _machine_name = self.config_json.Install.windows_client.machine_host
            _username = self.config_json.Install.windows_client.machine_username
            _password = self.config_json.Install.windows_client.machine_password
            _service_pack = self.tcinputs.get("ServicePack")

            _client_machine = Machine(machine_name=_machine_name, username=_username, password=_password)
            _install_helper = InstallHelper(self.commcell, _client_machine)
            if _client_machine.check_registry_exists("Session", "nCVDPORT"):
                _install_helper.uninstall_client(delete_client=True)

            _sp_transaction = installer_utils.get_latest_recut_from_xml(_service_pack)
            latest_cu = installer_utils.get_latest_cu_from_xml(_sp_transaction)
            self.log.info(f"Starting Download of {_service_pack} and CU{latest_cu}")
            job = self.commcell.download_software(
                options=DownloadOptions.SERVICEPACK_AND_HOTFIXES.value,
                os_list=[DownloadPackages.UNIX_LINUX64.value, DownloadPackages.WINDOWS_64.value],
                service_pack=_service_pack.lower().split('sp')[-1],
                cu_number=int(latest_cu))
            self.log.info("Job %s started for downloading packages", job.job_id)
            if not job.wait_for_completion():
                raise Exception("Failed to run download job with error: " + job.delay_reason)
            self.log.info("Successfully finished Downloading packages")

            _package_list = [WindowsDownloadFeatures.FILE_SYSTEM.name, WindowsDownloadFeatures.MEDIA_AGENT.name]

            install_path = OptionsSelector.get_drive(_client_machine) + "commvault"
            self.log.info(f"Starting Install on client {_client_machine.machine_name}")
            if self.commcell.is_linux_commserv:
                # Configuring Remote Cache Client to Push Software to Windows Client
                self.log.info("Checking for Windows Remote Cache as Linux CS does not support "
                              "Direct push Installation to Windows Client")
                rc_client_name = self.config_json.Install.rc_client.client_name
                if self.commcell.clients.has_client(rc_client_name):
                    self.rc_client = self.commcell.clients.get(rc_client_name)
            self.deployment_helper.add_server_new_windows_or_unix_server(
                hostname=[_machine_name], username=_username, password=_password,
                packages=[Packages[_package_list[0]].value], log_path=installer_constants.DB2LOGLOCATION,
                install_path=install_path, remote_cache=self.rc_client.client_name if self.rc_client else None)
            self.log.info(f"Install on client {_client_machine.machine_name} Successful")

            self.log.info(f"Adding {_package_list[1]} package on client {_client_machine.machine_name}")
            self.deployment_helper.action_add_software(
                client_name=self.deployment_helper.get_client_name_from_hostname(_machine_name),
                select_all_packages="ALL" in _package_list, packages=[Packages[_package_list[1]].value])
            self.log.info(f"Adding {_package_list[1]} package on client {_client_machine.machine_name} successful")

            client_obj = self.commcell.clients.get(_client_machine.machine_name)
            if client_obj.is_ready:
                self.log.info("Starting Install Validation")
                _package_list = [WindowsDownloadFeatures[str(x)].value for x in _package_list]
                install_validation = InstallValidator(client_obj.client_hostname, self,
                                                      machine_object=_client_machine, package_list=_package_list,
                                                      is_push_job=True)
                install_validation.validate_install()
            else:
                raise Exception("Client services are down; Install Unsuccessful")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
