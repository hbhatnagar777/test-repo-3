# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
from AutomationUtils import config
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures


class TestCase(CVTestCase):
    """Class for verifying the Retire Client Option when no data is associated with the client"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Retire Client - Retire client when no data is associated with it."
        self.config_json = None
        self.client = None
        self.commcell = None
        self.windows_machine = None
        self.install_helper = None
        self.rc_client = None
        self.status = constants.PASSED
        self.result_string = ""

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        install_helper = InstallHelper(self.commcell)
        self.windows_machine = install_helper.get_machine_objects(1)[0]

    def run(self):
        """Main function for test case execution"""
        try:
            self.install_helper = InstallHelper(self.commcell, self.windows_machine)
            if not self.commcell.clients.has_client(self.install_helper.client_host):
                if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                    self.install_helper.uninstall_client()
                self.log.info(f"Creating {self.windows_machine.os_info} client")
                if self.commcell.is_linux_commserv:
                    # Configuring Remote Cache Client to Push Software to Windows Client
                    self.log.info("Checking for Windows Remote Cache as Linux CS does not support "
                                  "Direct push Installation to Windows Client")
                    rc_client_name = self.config_json.Install.rc_client.client_name
                    if self.commcell.clients.has_client(rc_client_name):
                        self.rc_client = self.commcell.clients.get(rc_client_name)
                job = self.install_helper.install_software(
                    client_computers=[self.windows_machine.machine_name],
                    sw_cache_client=self.rc_client.client_name if self.rc_client else None)
                if not job.wait_for_completion():
                    raise Exception(f"{self.windows_machine.os_info} Client installation Failed")
            self.commcell.clients.refresh()
            self.client = self.commcell.clients.get(self.config_json.Install.windows_client.machine_host)
            install_validation = InstallValidator(
                self.client.client_hostname, self, machine_object=self.windows_machine,
                package_list=[WindowsDownloadFeatures.FILE_SYSTEM.value], is_push_job=True)

            # Retire the client
            self.log.info("Will perform Retire operation now on client %s.", self.client.client_name)
            job = self.client.retire()

            # Check the status of the uninstall job triggered to Retire client
            if not job.wait_for_completion():
                raise Exception(f"Uninstall job failed with error: {job.delay_reason}")

            # Refreshing the clients associated with the commcell Object
            self.commcell.clients.refresh()

            # Verify that the client has been deleted
            if self.commcell.clients.has_client(self.client.client_name):
                raise Exception("Client Still Exists. Check logs to make sure Retire Operation succeeded.")
            install_validation.validate_uninstall()

            self.log.info("Test case to retire a client when no data is associated with it completed successfully.")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if self.commcell.clients.has_client(self.client.client_name):
                self.install_helper.uninstall_client(self.client)
