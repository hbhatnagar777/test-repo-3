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

    run_copy_software() -- run copy software

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Inputs:

    feature_release     --  feature release of the bootstrapper
"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils import config
from Install import installer_constants
from Install.install_helper import InstallHelper
from Install.softwarecache_helper import SoftwareCache
from Install.softwarecache_validation import RemoteCache
from Install.bootstrapper_helper import BootstrapperHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.DeploymentHelper import DeploymentHelper
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):
    """Class for downloading media using bootstrapper and then copy to CS cache"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("Install - Admin Console - Copy Software - Windows and Unix media downloaded using bootstrapper")
        self.factory = None
        self.browser = None
        self.driver = None
        self.login_obj = None
        self.deployment_helper = None
        self.maintenance = None
        self.tcinputs = {
            'feature_release': None
        }
        self.admin_console = None
        self.machine_obj = None
        self.bootstrapper_obj = None
        self.config_json = None
        self.machine_objects = None
        self.remote_cache_val_obj = None
        self.software_cache_obj = None
        self.client_obj = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        self.machine_obj = Machine(self.commcell.commserv_client)
        self.bootstrapper_obj = BootstrapperHelper(feature_release=self.tcinputs.get(
            'feature_release'), machine_obj=self.machine_obj, bootstrapper_download_os="Windows,Unix")
        install_helper = InstallHelper(self.commcell)
        self.machine_objects = install_helper.get_machine_objects()

    def run_copy_software(self):
        """
        Runs copy software
        """
        self.factory = BrowserFactory()
        self.browser = self.factory.create_browser_object()
        self.browser.open()
        self.driver = self.browser.driver
        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'],
                                 stay_logged_in=True)
        self.deployment_helper = DeploymentHelper(self, self.admin_console)

        self.log.info("Copying Windows Media to CS Cache")
        self.deployment_helper.run_copy_software(
            media_path=f"{self.bootstrapper_obj.remote_machine_drive}{installer_constants.WINDOWS_BOOTSTRAPPER_DOWNLOADPATH}",
            auth=False)

        self.log.info("Copying Unix Media to CS Cache")
        self.deployment_helper.run_copy_software(
            media_path=f"{self.bootstrapper_obj.remote_machine_drive}{installer_constants.UNIX_BOOTSTRAPPER_DOWNLOADPATH}",
            auth=False,
            sync_remote_cache=True,
            clients_to_sync="All")

    def run(self):
        """Main function for test case execution"""

        try:
            configured_os_pkg_list = {}
            for machine in self.machine_objects:
                install_helper = InstallHelper(self.commcell, machine)
                if not self.commcell.clients.has_client(install_helper.client_host):
                    self.log.info("Creating {0} client".format(machine.os_info))
                    job = install_helper.install_software()
                    if not job.wait_for_completion():
                        raise Exception("{0} Client installation Failed".format(machine.os_info))
                self.commcell.clients.refresh()
                self.client_obj = self.commcell.clients.get(install_helper.client_host)
                self.software_cache_obj = SoftwareCache(self.commcell, self.client_obj)
                self.software_cache_obj.configure_remotecache()
                self.software_cache_obj.configure_packages_to_sync()
                self.log.info(
                    "Deleting remote cache contents on {0} client".format(machine.os_info))
                self.software_cache_obj.delete_remote_cache_contents()

            windows_client_obj = self.commcell.clients.get(
                self.config_json.Install.windows_client.machine_host)
            unix_client_obj = self.commcell.clients.get(
                self.config_json.Install.unix_client.machine_host)

            self.log.info("Downloading Media using Bootstrapper")
            self.bootstrapper_obj.extract_bootstrapper()
            self.bootstrapper_obj.download_payload_from_bootstrapper()

            self.log.info("Download completed successfully. Starting Copy Software")
            self.run_copy_software()

            self.log.info("Validating unix remote cache")
            self.remote_cache_val_obj = RemoteCache(
                client_obj=unix_client_obj,
                commcell=self.commcell)
            self.remote_cache_val_obj.validate_remote_cache(configured_os_pkg_list, sync_all=True)
            self.log.info("Validating windows remote cache")
            self.remote_cache_val_obj = RemoteCache(
                windows_client_obj,
                commcell=self.commcell)
            self.remote_cache_val_obj.validate_remote_cache(configured_os_pkg_list, sync_all=True)

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.bootstrapper_obj.cleanup()
