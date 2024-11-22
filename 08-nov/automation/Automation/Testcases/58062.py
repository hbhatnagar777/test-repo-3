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

"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants, config
from Install.install_validator import InstallValidator
from Install import installer_messages, installer_utils
from AutomationUtils.options_selector import OptionsSelector
from Install.install_helper import InstallHelper
from cvpysdk.deployment.deploymentconstants import DownloadOptions, DownloadPackages


class TestCase(CVTestCase):
    """Negative Testcase : Push updates to a client when its RC is not in sync."""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Negative Scenario - Push updates to a client when its RC is not in sync."
        self.config_json = None
        self.rc_machine_obj = None
        self.unix_machine_obj = None
        self.option_selector = None
        self.install_helper = None
        self.windows_install_helper = None
        self.unix_install_helper = None
        self.service_pack = None
        self.rc_client = None
        self.result_string = ""
        self.status = constants.PASSED

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        self.install_helper = InstallHelper(self.commcell)
        machine_objects = self.install_helper.get_machine_objects()
        self.rc_machine_obj = machine_objects[0]
        self.unix_machine_obj = machine_objects[1]
        self.option_selector = OptionsSelector(self.commcell)
        self.windows_install_helper = InstallHelper(self.commcell, self.rc_machine_obj)
        self.unix_install_helper = InstallHelper(self.commcell, self.unix_machine_obj)

    def get_service_pack_to_install(self, minus_value=0):
        """
        This method determines the service pack and it's path for Installation
        Returns: None
        """

        self.log.info(f"Service Pack Installed on the CS: {self.commcell.commserv_version}")

        self.log.info("Determining Media Path for Installation")
        if self.tcinputs.get('MediaPath') is None:
            media_path = self.config_json.Install.media_path
        else:
            media_path = self.tcinputs.get('MediaPath')
        _service_pack = "SP" + str(int(self.commcell.commserv_version))
        _service_pack_to_install = _service_pack
        if "{sp_to_install}" in media_path:
            if '_' in _service_pack:
                _service_pack_to_install = _service_pack.split('_')[0]
        _service_pack = _service_pack.lower().split('sp')[1]
        _minus_value = self.config_json.Install.minus_value
        if len(_service_pack) == 4:
            _service_pack_to_install = int(str(_service_pack)[:2]) - _minus_value
        else:
            _service_pack_to_install = int(_service_pack) - _minus_value
        self.log.info(f"Service pack to Install {_service_pack_to_install}")
        if '_' not in _service_pack:
            _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack_to_install)
            media_path = media_path.replace("{sp_to_install}", _service_pack_to_install)
        self.service_pack = _service_pack_to_install
        self.tcinputs.update({"mediaPath": media_path})

    def run(self):
        """Main function for test case execution"""
        try:
            bootstrapper_install = True
            # Installing clients: SP Lower than CS Installed
            silent_install_dict = {
                "csClientName": self.commcell.commserv_name,
                "csHostname": self.commcell.commserv_hostname,
                "authCode": self.commcell.enable_auth_code()
            }
            self.get_service_pack_to_install(self.config_json.Install.minus_value)
            if self.unix_machine_obj.check_registry_exists("Session", "nCVDPORT"):
                self.unix_install_helper.uninstall_client(delete_client=True)
            if self.rc_machine_obj.check_registry_exists("Session", "nCVDPORT"):
                self.windows_install_helper.uninstall_client(delete_client=True)
            if not bootstrapper_install:
                silent_install_dict.update({"mediaPath": self.tcinputs["mediaPath"]})

            self.unix_install_helper.silent_install(client_name="unix_client",
                                                    tcinputs=silent_install_dict,
                                                    feature_release=self.service_pack)

            if self.commcell.is_linux_commserv:
                # Configuring Remote Cache Client to Push Software to Windows Client
                self.log.info("Checking for Windows Remote Cache as Linux CS does not support "
                              "Direct push Installation to Windows Client")
                rc_client_name = self.config_json.Install.rc_client.client_name
                if self.commcell.clients.has_client(rc_client_name):
                    self.rc_client = self.commcell.clients.get(rc_client_name)
            push_job = self.windows_install_helper.install_software(
                client_computers=[self.rc_machine_obj.machine_name],
                sw_cache_client=self.rc_client.client_name if self.rc_client else None)
            if not push_job.wait_for_completion(5):
                self.log.error("Push Job for Windows Machine failed. Please check the Logs")
            download_job = self.commcell.download_software(
                options=DownloadOptions.LATEST_HOTFIXES.value,
                os_list=[DownloadPackages.WINDOWS_64.value, DownloadPackages.UNIX_LINUX64.value])

            if not download_job.wait_for_completion():
                raise Exception("Software Cache on CS is empty; Can't Sync Software to Remote Cache ")
            self.log.info("Refreshing Client List on the CS")
            self.commcell.refresh()
            time.sleep(20)
            rc_client = self.commcell.clients.get(self.rc_machine_obj.machine_name)
            rc_helper = self.commcell.get_remote_cache(rc_client.client_name)
            unix_client = self.commcell.clients.get(self.unix_machine_obj.machine_name)
            cache_path = self.option_selector.get_drive(self.rc_machine_obj)+"rc_temp"
            rc_helper.configure_remotecache(cache_path=cache_path)
            rc_helper.configure_packages_to_sync(win_os=["WINDOWS_64"],
                                                 win_package_list=["FILE_SYSTEM", "MEDIA_AGENT"],
                                                 unix_os=["UNIX_LINUX64"],
                                                 unix_package_list=["FILE_SYSTEM", "MEDIA_AGENT"])

            rc_helper.assoc_entity_to_remote_cache(client_name=unix_client.client_name)
            sync_job = self.commcell.sync_remote_cache([rc_client.client_name])
            if not sync_job.wait_for_completion():
                self.log.error("Remote Cache Sync Job Failed")

            self.log.info("Sync up Job Successful")
            rc_cache_path = rc_helper.get_remote_cache_path() + "\\CVMedia"

            if self.rc_machine_obj.check_directory_exists(rc_cache_path):
                self.rc_machine_obj.remove_directory(rc_cache_path)

            install_job = unix_client.push_servicepack_and_hotfix()

            if install_job.wait_for_completion():
                raise Exception("Installing updates successful with empty Remote Cache")

            job_status = install_job.delay_reason

            if installer_messages.QINSTALL_SWCACHE_PACKAGES_MISSING not in job_status:
                self.log.error("Job Failed due to some other reason than the expected one.")
                raise Exception(job_status)

            self.log.info("JobFailingReason:%s", job_status)
            sync_job = sync_job.resubmit()
            if not sync_job.wait_for_completion():
                raise Exception("Remote Cache Sync Job Failed")

            self.log.info("Sync up Job Successful")
            install_job = install_job.resubmit()
            if install_job.wait_for_completion():
                self.log.info("Packages successfully installed on the machine")
                install_validation = InstallValidator(unix_client.client_hostname, self,
                                                      machine_object=self.unix_machine_obj,
                                                      is_push_job=True)
                install_validation.validate_install()
                rc_helper.delete_remote_cache_contents()

            else:
                job_status = install_job.delay_reason
                self.log.error(f"Failed to Install updates on the client: {unix_client.client_name}")
                raise Exception(job_status)

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
