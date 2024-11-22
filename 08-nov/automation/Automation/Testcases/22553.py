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

    get_packages()   -- returns the list of installed packages on a client.

    validate_unix_packages -- validate packages installed on unix client.

    validate_win_packages  -- validate packages installed on windows client. 

Design Steps:
    1. Push Install on Unix or Windows Machine with FILE_SYSTEM, MEDIA_AGENT packages.
    2. Validate required packages installed.
    3. Uninstall from unix or windows machine. 

Sample Input - 
        "22553": {
            "ClientName": "ClientName",
            "MachineHostName": "HostName",
            "MachineUsername": "Username",
            "MachinePassword": "Password"
        }


"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from Install.install_helper import InstallHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Re-Install - Push or Remote Install -Wins and ALL UNIX -No Netware"
        self.machine_obj = None
        self.machine_name = None
        self.install_helper = None
        self.installer_flags = None
        self.client_obj = None
        self.options_selector = None

        self.win_packages = None
        self.unix_packages = None

        self.tcinputs = {
            "ClientName": None,
            "MachineHostName": None,
            "MachineUsername": None,
            "MachinePassword": None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.options_selector = OptionsSelector(self.commcell)

        # Create Machine object
        self.machine_obj = self.options_selector.get_machine_object(
                machine=self.tcinputs['MachineHostName'],
                username=self.tcinputs['MachineUsername'],
                password=self.tcinputs['MachinePassword'])

        self.machine_name = self.machine_obj.machine_name
        self.log.info("Machine hostname %s", self.machine_name)
        self.win_packages = {
            "File System Core": 1,
            "File System": 702,
            "MediaAgent": 51,
            "Storage Accelerator": 54
        }

        self.unix_packages = {
            "File System Core": 1002,
            "File System": 1101,
            "MediaAgent": 1301
        }
    
    def get_packages(self):
        """ 
        Returns the list of installed packages. 
        """
        client_prop = self.client_obj.properties
        package_details = client_prop['client']['versionInfo']['PatchStatus']
        package_installed = {}
        for obj in package_details:
            pkg_name = obj.get('packageInfo').get('packageName')
            pkg_id = obj.get('packageInfo').get('packageId')
            self.log.info(f"Installed Package Id: {pkg_id} Name: {pkg_name}")
            package_installed[pkg_name] = int(pkg_id)
        return package_installed

    def validate_unix_packages(self):
        """
        Verifies the package installed on the unix machine.
        """
        client_packages = self.get_packages()
        for package in self.unix_packages:
            if client_packages[package] != self.unix_packages[package]:
                raise Exception(f"Package Validation Failed for {package}")
        self.log.info('Package Validation Successful.')
    
    def validate_win_packages(self):
        """
        Verifies the package installed on the windows machine.
        """
        client_packages = self.get_packages()
        for package in self.win_packages():
            if client_packages[package] != self.win_packages[package]:
                raise Exception(f"Package Validation Failed for {package}")
        self.log.info('Package Validation Successful.')

    def run(self):
        """Main function for test case execution"""
        try:
            # Get Install Helper Object to Push Software
            self.install_helper = InstallHelper(self.commcell, self.machine_obj)

            # Check if MA is already installed.
            if self.commcell.clients.has_client(self.machine_name):
                self.log.info("Client already present, uninstalling client!")
                client_obj = self.commcell.clients.get(self.machine_name)
                self.log.info(f"Client Object Value {client_obj}")
                return client_machine_obj

            # Pushing Packages from CS to the windows client
            self.log.info(f"Starting a Push Install Job: {self.machine_name}")
            push_job = self.install_helper.install_software(
                            client_computers=[self.machine_name],
                            features=['FILE_SYSTEM', 'MEDIA_AGENT'],
                            username=self.tcinputs['MachineUsername'],
                            password=self.tcinputs['MachinePassword']
            )

            self.log.info(f"Job Launched Successfully, Will wait until Job: {push_job.job_id} Completes")
            if push_job.wait_for_completion():
                self.log.info("Push Upgrade Job Completed successfully")

            else:
                job_status = push_job.delay_reason
                self.log.error(f"Job failed with an error: {job_status}")
                raise Exception(job_status)

            # Refreshing the Client list, so New Client Visible on GUI
            self.log.info("Refreshing Client List on the CS")
            self.commcell.refresh()

            # Check if the services are up on Client and is Reachable from CS
            self.log.info("Initiating Check Readiness from the CS")
            if self.commcell.clients.has_client(self.machine_name):
                self.client_obj = self.commcell.clients.get(self.machine_name)
                if self.client_obj.is_ready:
                    self.log.info("Check Readiness of CS successful")
            else:
                self.log.error("Client failed Registration to the CS")
                raise Exception(f"Client: {self.machine_name} failed registering to the CS, "
                                f"Please check client logs")

            # Validate Packages Installed
            if self.machine_obj.os_info == 'UNIX':
                self.validate_unix_packages()
            else:
                self.validate_win_packages()

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""

        if self.status != "FAILED":
            self.log.info(
                "Testcase shows successful execution, cleaning up the test environment ...")
            self.log.info("Uninstalling the windows client!")
            if self.commcell.clients.has_client(self.machine_name):
                client_obj = self.commcell.clients.get(self.machine_name)
                self.log.info(f"Client Object Value {client_obj}")
                self.install_helper.uninstall_client(delete_client=True, instance=client_obj.instance)
        else:
            self.log.error(
                "Testcase shows failure in execution, not cleaning up the test environment ...")
