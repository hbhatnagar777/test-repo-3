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

Inputs:
    InstallPath - no_space_drive

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config, constants
from Install import installer_messages
from Install.install_helper import InstallHelper
from cvpysdk.deployment.deploymentconstants import DownloadPackages, DownloadOptions


class TestCase(CVTestCase):
    """Negative Testcase : Push software to a client with not enough disk space"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Negative Scenario - Push software to a client with not enough disk space"
        self.config_json = None
        self.windows_machine = None
        self.windows_install_helper = None
        self.rc_client = None
        self.result_string = ''
        self.status = constants.PASSED

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        install_helper = InstallHelper(self.commcell)
        self.windows_machine = install_helper.get_machine_objects(type_of_machines=1)[0]
        self.windows_install_helper = InstallHelper(self.commcell, self.windows_machine)

    def run(self):
        """Main function for test case execution"""
        try:
            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                self.windows_install_helper.uninstall_client(delete_client=True)

            _os_to_download = [DownloadPackages.WINDOWS_64.value, DownloadPackages.UNIX_LINUX64.value]
            self.log.info("Starting Download Software Job")
            job_obj = self.commcell.download_software(options=DownloadOptions.LATEST_HOTFIXES.value,
                                                      os_list=_os_to_download)
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Download Software Job Successful")
            else:
                self.log.error("Download job failed")
            self.log.info("Starting Installation on Windows client")
            if self.commcell.is_linux_commserv:
                # Configuring Remote Cache Client to Push Software to Windows Client
                self.log.info("Checking for Windows Remote Cache as Linux CS does not support "
                              "Direct push Installation to Windows Client")
                rc_client_name = self.config_json.Install.rc_client.client_name
                if self.commcell.clients.has_client(rc_client_name):
                    self.rc_client = self.commcell.clients.get(rc_client_name)
            job_install = self.windows_install_helper.install_software(
                client_computers=[self.windows_install_helper.client_host],
                features=['FILE_SYSTEM', 'MEDIA_AGENT'],
                install_path=self.config_json.Install.windows_client.no_space_drive,
                sw_cache_client=self.rc_client.client_name if self.rc_client else None
            )
            if job_install.wait_for_completion(5):
                self.log.error("Installation Successful! Please provide a low space directory")
                raise Exception("Client installation Successful even with Not enough disk space")

            job_status = job_install.delay_reason
            if installer_messages.QINSTALL_LOW_DISK_SPACE not in job_status:
                self.log.error("Job Failed due to some other reason than the expected one.")
                raise Exception(job_status)
            else:
                self.log.info("Job Failed with the expected JPR")

            self.log.info("JobFailingReason:%s", job_status)

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
