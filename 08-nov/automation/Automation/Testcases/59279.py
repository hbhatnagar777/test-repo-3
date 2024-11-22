
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

from cvpysdk.deployment.deploymentconstants import DownloadOptions as download_constants
from cvpysdk.deployment.deploymentconstants import DownloadPackages
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures
from cvpysdk.deployment.deploymentconstants import OSNameIDMapping
from AutomationUtils import config
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Install.install_helper import InstallHelper
from Install.softwarecache_helper import SoftwareCache
from Install.softwarecache_validation import RemoteCache
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.Helper.DeploymentHelper import DeploymentHelper
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):
    """Class for validating download, remote cache sync, MR update, upgrade of lower feature release"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Download, remote cache sync, MR update, upgrade of lower feature release"
        self.commcell = None
        self.config_json = None
        self.software_cache_obj = None
        self.remote_cache_val_obj = None
        self.factory = None
        self.browser = None
        self.driver = None
        self.admin_console = None
        self.deployment_helper = None
        self.rc_machine = None
        self.associate_client = None
        self.install_helper_remotecache = None
        self.install_helper_associate_client = None

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
        self.rc_machine = Machine(
            self.config_json.Install.rc_client.machine_host,
            username=self.config_json.Install.rc_client.machine_username,
            password=self.config_json.Install.rc_client.machine_password)
        self.associate_client = Machine(
            self.config_json.Install.associate_client.machine_host,
            username=self.config_json.Install.associate_client.machine_username,
            password=self.config_json.Install.associate_client.machine_password)
        self.deployment_helper = DeploymentHelper(self, self.admin_console)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Installing Remote Cache Client")
            self.install_helper_remotecache = InstallHelper(self.commcell, self.rc_machine)
            if not self.commcell.clients.has_client(self.config_json.Install.rc_client.machine_host):
                self.install_helper_remotecache.silent_install(
                    client_name=self.config_json.Install.rc_client.client_name,
                    tcinputs={"csClientName": self.commcell.commserv_name,
                              "csHostname": self.commcell.commserv_hostname,
                              "commservePassword": self.config_json.Install.cs_password,
                              "mediaPath": self.tcinputs.get("mediaPath")},
                    feature_release=f"SP{int(self.commcell.commserv_version)-1}")

            self.log.info("Installing windows client to associate to Remote cache")
            if not self.commcell.clients.has_client(self.config_json.Install.associate_client.machine_host):
                self.install_helper_associate_client = InstallHelper(self.commcell, self.associate_client)
                self.install_helper_associate_client.silent_install(
                    client_name=self.config_json.Install.associate_client.client_name,
                    tcinputs={"csClientName": self.commcell.commserv_name,
                              "csHostname": self.commcell.commserv_hostname,
                              "commservePassword": self.config_json.Install.cs_password},
                    feature_release=f"SP{int(self.commcell.commserv_version)-2}")

            rc_client_obj = self.commcell.clients.get(self.config_json.Install.rc_client.machine_host)

            win_os_to_sync = ["WINDOWS_32", "WINDOWS_64"]
            unix_os_to_sync = ["UNIX_LINUX64", "UNIX_AIX"]
            win_packages_to_sync = ["FILE_SYSTEM", "MEDIA_AGENT"]
            unix_packages_to_sync = ["FILE_SYSTEM", "MEDIA_AGENT"]

            self.log.info("Configuring %s client as Remote cache", rc_client_obj.client_name)
            self.software_cache_obj = SoftwareCache(self.commcell, rc_client_obj)
            self.software_cache_obj.configure_remotecache()
            self.software_cache_obj.configure_packages_to_sync(win_os_to_sync,
                                                               win_packages_to_sync,
                                                               unix_os_to_sync,
                                                               unix_packages_to_sync)
            self.log.info("Associating windows client to remote cache")
            associate_client_obj = self.commcell.clients.get(self.config_json.Install.associate_client.machine_host)
            self.commcell.get_remote_cache(rc_client_obj.client_name).assoc_entity_to_remote_cache(
                client_name=associate_client_obj.client_name)

            self.log.info("Downloading and Syncing remote cache")
            self.log.info("Deleting cache")
            self.commcell.commserv_cache.delete_cache()

            self.log.info("Commiting cache")
            self.commcell.commserv_cache.commit_cache()

            self.log.info(f"Downloading SP{int(self.commcell.commserv_version) - 1}")
            job_obj = self.commcell.download_software(
                options=download_constants.SERVICEPACK_AND_HOTFIXES.value,
                service_pack=str(int(self.commcell.commserv_version) - 1),
                sync_cache=False,
                os_list=[DownloadPackages.WINDOWS_64.value, DownloadPackages.UNIX_LINUX64.value],
                cu_number=self.software_cache_obj.get_latest_maintenance_release(int(self.commcell.commserv_version) - 1))
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run download software job with error: %s", job_obj.delay_reason)

            self.log.info(f"Downloading SP{int(self.commcell.commserv_version) - 2}")
            job_obj = self.commcell.download_software(
                options=download_constants.SERVICEPACK_AND_HOTFIXES.value,
                service_pack=str(int(self.commcell.commserv_version) - 2),
                sync_cache=False,
                cu_number=self.software_cache_obj.get_latest_maintenance_release(int(self.commcell.commserv_version) - 2))
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run download software job with error: %s", job_obj.delay_reason)

            self.log.info(f"Downloading latest hotfixes for SP{self.commcell.commserv_version}")
            job_obj = self.commcell.download_software(
                options=download_constants.LATEST_HOTFIXES.value, sync_cache=False)
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run download software job with error: %s", job_obj.delay_reason)

            job_obj = self.commcell.sync_remote_cache(client_list=[rc_client_obj.client_name])
            if not job_obj.wait_for_completion():
                raise Exception("Failed to run sync job with error: %s", job_obj.delay_reason)

            final_list_to_check = self.software_cache_obj.get_media_to_sync()
            win_os_id = [eval(f"OSNameIDMapping.{each}.value") for each in win_os_to_sync]
            unix_os_id = [eval(f"OSNameIDMapping.{each}.value") for each in unix_os_to_sync]
            win_packages = [eval(f"WindowsDownloadFeatures.{packages}.value") for packages in win_packages_to_sync]
            unix_packages = [eval(f"UnixDownloadFeatures.{packages}.value") for packages in unix_packages_to_sync]

            configured_os_pkg_list = {}
            self.log.info("Validating remote cache")

            if len(win_os_id) != 0:
                for each in win_os_id:
                    configured_os_pkg_list[each] = win_packages
            if len(unix_os_id) != 0:
                for each in unix_os_id:
                    configured_os_pkg_list[each] = unix_packages
            for key in final_list_to_check:
                self.remote_cache_val_obj = RemoteCache(
                    client_obj=rc_client_obj,
                    commcell=self.commcell, media=key, os_ids=final_list_to_check[key])
                if bool(configured_os_pkg_list):
                    self.remote_cache_val_obj.validate_remote_cache(configured_os_pkg_list)
                else:
                    self.remote_cache_val_obj.validate_remote_cache(configured_os_pkg_list, sync_all=True)

            self.log.info("*********Installing Maintenance Release on RC and associated clients********")
            mr_install_job_obj = self.commcell.push_servicepack_and_hotfix(
                client_computers=[rc_client_obj.client_name, associate_client_obj.client_name],
                maintenance_release_only=True)
            if not mr_install_job_obj.wait_for_completion():
                raise Exception("Failed to run install updates job with error: %s", mr_install_job_obj.delay_reason)

            self.log.info("*********************Upgrading RC and associated clients********************")
            upgrade_job_obj = self.commcell.push_servicepack_and_hotfix(
                client_computers=[rc_client_obj.client_name, associate_client_obj.client_name])
            if not upgrade_job_obj.wait_for_completion():
                raise Exception("Failed to run install updates job with error: %s", upgrade_job_obj.delay_reason)

            self.log.info("Validating Upgrade")
            self.deployment_helper.validate_install(client_name=associate_client_obj.client_name)
            self.log.info("Upgrade completed successfully")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            if self.commcell.clients.has_client(self.config_json.Install.rc_client.machine_host):
                self.install_helper_remotecache.uninstall_client()
            if self.commcell.clients.has_client(self.config_json.Install.associate_client.machine_host):
                self.install_helper_associate_client.uninstall_client()
