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
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from Install.softwarecache_helper import SoftwareCache
from Install.softwarecache_validation import RemoteCache
from Install.install_helper import InstallHelper
from Install.installer_constants import DEFAULT_COMMSERV_USER
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for validating parallel remote cache sync"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Parallel sync of remote caches"
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
            for machine in self.machine_objects:
                install_helper = InstallHelper(self.commcell, machine)
                if not self.commcell.clients.has_client(install_helper.client_host):
                    if machine.check_registry_exists("Session", "nCVDPORT"):
                        install_helper.uninstall_client(delete_client=True)
                    self.log.info(f"Creating {machine.os_info} client")
                    if self.commcell.is_linux_commserv and 'windows' in machine.os_info.lower():
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
                install_helper.restart_services()
                client_obj = self.commcell.clients.get(install_helper.client_host)
                self.software_cache_obj = SoftwareCache(self.commcell, client_obj)
                self.software_cache_obj.configure_remotecache()
                self.software_cache_obj.configure_packages_to_sync()
                self.log.info(f"Deleting remote cache contents on {machine.os_info} client")
                self.software_cache_obj.delete_remote_cache_contents()

            windows_client_obj = self.commcell.clients.get(
                self.config_json.Install.windows_client.machine_host)
            unix_client_obj = self.commcell.clients.get(
                self.config_json.Install.unix_client.machine_host)

            self.log.info("Scenario - Job1 - Sync job for unix client."
                          " Job2 - Sync job for windows client. "
                          "Expected Outcome - Both jobs should succeed.")
            self.log.info("Start sync job for unix client")
            unix_sync = self.commcell.sync_remote_cache([unix_client_obj.client_name])
            self.log.info("Sync Job %s submitted", unix_sync.job_id)

            self.log.info("Start sync job for windows client")
            win_sync = self.commcell.sync_remote_cache([windows_client_obj.client_name])
            self.log.info("Sync Job %s submitted", win_sync.job_id)

            configured_os_pkg_list = {}

            if not unix_sync.wait_for_completion():
                raise Exception("Sync job failed. Details: %s", unix_sync.delay_reason)
            self.log.info("Job %s passed", unix_sync.job_id)
            self.log.info("Validating unix remote cache")
            self.remote_cache_val_obj = RemoteCache(
                client_obj=unix_client_obj,
                commcell=self.commcell,
                machine_obj=self.machine_objects[1])
            self.remote_cache_val_obj.validate_remote_cache(configured_os_pkg_list, sync_all=True)

            if not win_sync.wait_for_completion():
                raise Exception("Sync job failed. Details: %s", win_sync.delay_reason)
            self.log.info("Job %s passed", win_sync.job_id)
            self.log.info("Validating windows remote cache")
            self.remote_cache_val_obj = RemoteCache(
                windows_client_obj,
                commcell=self.commcell,
                machine_obj=self.machine_objects[0])
            self.remote_cache_val_obj.validate_remote_cache(configured_os_pkg_list, sync_all=True)

            self.log.info("Parallel sync of RCs succeeded.")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            for machine in self.machine_objects:
                install_helper = InstallHelper(self.commcell, machine)
                if self.commcell.clients.has_client(install_helper.client_host):
                    self.log.info(f"Cleaning up installed {machine.os_info} client")
                    install_helper.uninstall_client()
