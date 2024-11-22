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
import random
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants, config
from AutomationUtils.machine import Machine
from Install.installer_constants import DEFAULT_COMMSERV_USER
from Install.install_validator import InstallValidator
from Install.install_helper import InstallHelper
from Install import installer_utils
from cvpysdk.commcell import Commcell
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures


class TestCase(CVTestCase):
    """Testcase : Fresh Push Install to Windows Client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Fresh Push Install to Windows Client"
        self.config_json = None
        self.rc_client = None
        self.windows_machine = None
        self.windows_hostname = None
        self.windows_helper = None
        self.client_obj = None
        self.associate_machine = None
        self.update_acceptance = False
        self.media_path = None
        self.install_helper = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=DEFAULT_COMMSERV_USER,
                                     commcell_password=self.config_json.Install.cs_password)
        self.install_helper = InstallHelper(self.commcell, tc_object=self)
        self.windows_machine = self.install_helper.get_machine_objects(type_of_machines=1)[0]
        self.windows_hostname = self.windows_machine.machine_name
        self.update_acceptance = self.config_json.Install.update_acceptance_database

    def run(self):
        """Main function for test case execution"""
        try:
            if self.update_acceptance:
                self.install_helper.install_acceptance_insert()
            # Get Install Helper Object to Push Software
            self.windows_helper = InstallHelper(self.commcell, self.windows_machine)

            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                self.windows_helper.uninstall_client(delete_client=True)

            # Configuring Windows Remote Cache for Fresh Push Install to Windows Machine
            # Please provide RC Client Name on config file - [Install.rc_client.client_name]
            if self.commcell.is_linux_commserv:
                # Configuring Remote Cache Client to Push Software to Windows Client
                self.log.info("Checking for Windows Remote Cache as Linux CS does not support "
                              "Direct push Installation to Windows Client")
                is_windows = False
                rc_client_name = self.config_json.Install.rc_client.client_name
                if self.commcell.clients.has_client(rc_client_name):
                    self.rc_client = self.commcell.clients.get(rc_client_name)
                    if "windows" in self.rc_client.os_info.lower():
                        is_windows = True

                # Finding a Windows Machine and Configuring it as an RC
                if not is_windows:
                    # Since LinuxCS do not support direct push install of windows client, installing a windows client
                    # to act as an RC
                    self.associate_machine = Machine(
                        machine_name=self.config_json.Install.associate_client.machine_host,
                        username=self.config_json.Install.associate_client.machine_username,
                        password=self.config_json.Install.associate_client.machine_password)
                    associate_helper = InstallHelper(self.commcell, self.associate_machine)
                    if self.associate_machine.check_registry_exists("Session", "nCVDPORT"):
                        associate_helper.uninstall_client(delete_client=False)

                    silent_install_dict = {
                        "csClientName": self.commcell.commserv_name,
                        "csHostname": self.config_json.Install.commserve_client.machine_host,
                        "authCode": self.commcell.enable_auth_code()
                    }
                    self.log.info(f"Installing an associate windows client on {self.associate_machine.machine_name}")
                    associate_helper.silent_install(client_name="associate_windows_client",
                                                    tcinputs=silent_install_dict)

                    self.rc_client = None
                    self.log.info("Finding any Windows Machine from Client List to Configure it as an RC")
                    all_clients_list = self.commcell.clients.all_clients
                    for client_name in all_clients_list:
                        if "windows" in self.commcell.clients.get(client_name).os_info.lower():
                            self.log.info(f"Found windows machine: {client_name}--> Configuring it as RC")
                            self.rc_client = self.commcell.clients.get(client_name)
                            break

                    if self.rc_client is None:
                        self.log.error("Please configure a Windows Machine as RC to Push Software")
                        self.log.error("Linux CS do not support Push Software to Windows Machine")
                        raise Exception("Windows RC needed to push software to a new Windows Client")

                self.log.info(f"Configuring {self.rc_client.client_name} as Remote Cache")
                rc_helper = self.commcell.get_remote_cache(self.rc_client.client_name)
                cache_path = f"{self.rc_client.install_directory}\\SoftwareCache"
                rc_helper.configure_remotecache(cache_path=cache_path)
                self.log.info(f"Configured Remote Cache Path: {cache_path}")
                rc_helper.configure_packages_to_sync(win_os=["WINDOWS_64"],
                                                     win_package_list=["FILE_SYSTEM", "MEDIA_AGENT"])
                self.log.info(f"Starting a Sync Job on the client : {self.rc_client.client_name}")
                sync_job = self.commcell.sync_remote_cache(client_list=[self.rc_client.client_name])
                if sync_job.wait_for_completion(20):
                    self.log.info("WindowsX64 Packages Synced to RC successfully")

                else:
                    job_status = sync_job.delay_reason
                    self.log.error("Sync Job Failed; Please check the Logs on CS")
                    raise Exception(job_status)

            # Pushing Packages from CS to the client
            self.log.info(f"Starting a Push Install Job on the Machine: {self.windows_hostname}")
            push_job = self.windows_helper.install_software(
                            client_computers=[self.windows_hostname],
                            features=['FILE_SYSTEM'],
                            username=self.config_json.Install.windows_client.machine_username,
                            password=self.config_json.Install.windows_client.machine_password,
                            sw_cache_client=self.rc_client.client_name if self.rc_client else None)

            self.log.info(f"Job Launched Successfully, Will wait until Job: {push_job.job_id} Completes")
            if push_job.wait_for_completion():
                self.log.info("Push Upgrade Job Completed successfully")

            else:
                job_status = push_job.delay_reason
                self.log.error(f"Job failed with an error: {job_status}")
                raise Exception(job_status)

            # Refreshing the Client list to me the New Client Visible on GUI
            self.log.info("Refreshing Client List on the CS")
            self.commcell.refresh()

            # Check if the services are up on Client and is Reachable from CS
            self.log.info("Initiating Check Readiness from the CS")
            if self.commcell.clients.has_client(self.windows_hostname):
                self.client_obj = self.commcell.clients.get(self.windows_hostname)
                if self.client_obj.is_ready:
                    self.log.info("Check Readiness of CS successful")
                    self.client_obj.display_name = self.name.replace(" ", "_") + "_" + str(random.randint(1000, 9999))
            else:
                self.log.error("Client failed Registration to the CS")
                raise Exception(f"Client: {self.windows_hostname} failed registering to the CS, "
                                f"Please check client logs")

            self.log.info("Starting Install Validation")
            install_validation = InstallValidator(self.client_obj.client_hostname, self,
                                                  machine_object=self.windows_machine,
                                                  package_list=[WindowsDownloadFeatures.FILE_SYSTEM.value],
                                                  is_push_job=True)
            install_validation.validate_install()
            if self.update_acceptance:
                self.install_helper.install_acceptance_update('Pass', '-', self.windows_machine.machine_name)

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            if self.update_acceptance:
                _service_pack = installer_utils.get_latest_recut_from_xml("SP" + str(self.commcell.commserv_version))
                self.install_helper.install_acceptance_update(
                    'Fail', str(exp).replace("'", ''), self.windows_machine.machine_name,
                    _service_pack.split('_R')[-1])

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.FAILED:
            installer_utils.collect_logs_after_install(self, self.windows_machine)
            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                self.windows_helper.uninstall_client(delete_client=False)
