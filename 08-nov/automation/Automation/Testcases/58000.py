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
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Install.install_helper import InstallHelper
from Install.softwarecache_helper import SoftwareCache
from Install.softwarecache_validation import RemoteCache
from Web.Common.page_object import handle_testcase_exception
from cvpysdk.deployment.deploymentconstants import DownloadOptions as download_constants
from Install import installer_messages
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures,UnixDownloadFeatures,OSNameIDMapping


class TestCase(CVTestCase):
    """Class for validating remote cache sync when one or more clients are unreachable"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Negative Scenario - Remote cache sync when one or more clients are unreachable"
        self.commcell = None
        self.config_json = None
        self.software_cache_obj = None
        self.remote_cache_val_obj = None
        self.machine_objects = None
        self.rc_client = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        install_helper = InstallHelper(self.commcell)
        self.machine_objects = install_helper.get_machine_objects()

    def run(self):
        """Main function for test case execution"""
        try:

            win_os_to_sync = ["WINDOWS_32", "WINDOWS_64"]
            unix_os_to_sync = ["UNIX_LINUX64", "UNIX_AIX"]
            win_packages_to_sync = ["FILE_SYSTEM", "MEDIA_AGENT"]
            unix_packages_to_sync = ["FILE_SYSTEM", "MEDIA_AGENT"]
            for machine in self.machine_objects:
                install_helper = InstallHelper(self.commcell, machine)
                if not self.commcell.clients.has_client(install_helper.client_host):
                    self.log.info(f"Creating {machine.os_info} client")
                    if machine.check_registry_exists("Session", "nCVDPORT"):
                        install_helper.uninstall_client()
                    if self.commcell.is_linux_commserv:
                        # Configuring Remote Cache Client to Push Software to Windows Client
                        self.log.info("Checking for Windows Remote Cache as Linux CS does not support "
                                      "Direct push Installation to Windows Client")
                        rc_client_name = self.config_json.Install.rc_client.client_name
                        if self.commcell.clients.has_client(rc_client_name):
                            self.rc_client = self.commcell.clients.get(rc_client_name)
                    job = install_helper.install_software(
                        client_computers=[machine.machine_name],
                        sw_cache_client=self.rc_client.client_name if self.rc_client else None)

                    if not job.wait_for_completion():
                        raise Exception(f"{machine.os_info} Client installation Failed")
                self.commcell.clients.refresh()
                client_obj = self.commcell.clients.get(install_helper.client_host)
                self.log.info("Configuring %s client as Remote cache", client_obj.client_name)
                self.software_cache_obj = SoftwareCache(self.commcell, client_obj)
                self.software_cache_obj.configure_remotecache()
                self.software_cache_obj.configure_packages_to_sync(win_os_to_sync, win_packages_to_sync,
                                                                   unix_os_to_sync, unix_packages_to_sync)

            windows_client_obj = self.commcell.clients.get(
                self.config_json.Install.windows_client.machine_host)
            unix_client_obj = self.commcell.clients.get(
                self.config_json.Install.unix_client.machine_host)

            self.log.info("Stopping services of unix client to make remote cache unreachable")
            unix_client_obj.stop_service()

            self.log.info("Downloading and Syncing remote cache")
            failed_reason = installer_messages.QDOWNLOAD_SOFTWARE_SYNC_ERROR
            failed_reason = failed_reason.replace("MACHINE_NAME", unix_client_obj.name)

            job_obj = self.commcell.download_software(
                options=download_constants.LATEST_HOTFIXES.value)

            if job_obj.wait_for_completion():
                self.log.info("Downloading job failed. Please check logs")
                raise Exception("Download job failed")
            jobdetails = job_obj.delay_reason

            if failed_reason not in jobdetails:
                self.log.error("Job failed with other reason than expected")
                raise Exception(jobdetails)

            self.log.info("Download job failed as expected. Details: %s", jobdetails)

            win_os_id = [eval(f"OSNameIDMapping.{each}.value") for each in win_os_to_sync]
            unix_os_id = [eval(f"OSNameIDMapping.{each}.value") for each in unix_os_to_sync]
            win_packages = [eval(f"WindowsDownloadFeatures.{packages}.value") for packages in win_packages_to_sync]
            unix_packages = [eval(f"UnixDownloadFeatures.{packages}.value") for packages in unix_packages_to_sync]

            configured_os_pkg_list = {}
            self.log.info("Validating remote cache")
            self.remote_cache_val_obj = RemoteCache(
                client_obj=windows_client_obj,
                commcell=self.commcell,
                machine_obj=self.machine_objects[0])
            if len(win_os_id) != 0:
                for each in win_os_id:
                    configured_os_pkg_list[each] = win_packages
            if len(unix_os_id) != 0:
                for each in unix_os_id:
                    configured_os_pkg_list[each] = unix_packages
            if bool(configured_os_pkg_list):
                self.remote_cache_val_obj.validate_remote_cache(configured_os_pkg_list)
            else:
                self.remote_cache_val_obj.validate_remote_cache(configured_os_pkg_list, sync_all=True)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            for machine in self.machine_objects:
                install_helper = InstallHelper(self.commcell, machine)
                if self.commcell.clients.has_client(install_helper.client_host):
                    self.log.info(f"Cleaning up installed {machine.os_info} client")
                    install_helper.uninstall_client()
