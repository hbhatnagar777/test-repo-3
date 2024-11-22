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
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants, config
from AutomationUtils.machine import Machine
from Install import installer_messages
from Install.install_helper import InstallHelper


class TestCase(CVTestCase):
    """Negative Testcase : Push software to a client which is not reachable."""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Negative Scenario - Push software to a client which is not reachable."
        self.cs_machine = None
        self.rc_machine = None
        self.rc_client = None
        self.status = constants.PASSED
        self.result_string = ""
        self.windows_machine = None
        self.config_json = config.get_config()

    def setup(self):
        """Initializes pre-requisites for this test case"""
        install_helper = InstallHelper(self.commcell)
        self.cs_machine = Machine(machine_name=self.commcell.commserv_hostname, commcell_object=self.commcell)
        self.windows_machine = install_helper.get_machine_objects(type_of_machines=1)[0]

    def run(self):
        """Main function for test case execution"""
        try:
            windows_helper = InstallHelper(self.commcell, self.windows_machine)
            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                windows_helper.uninstall_client()
            self.cs_machine.add_host_file_entry(windows_helper.client_host, "0.0.0.0")

            # Configuring Windows Remote Cache for Fresh Push Install to Windows Machine
            if self.commcell.is_linux_commserv:
                # Configuring Remote Cache Client to Push Software to Windows Client
                self.log.info("Checking for Windows Remote Cache as Linux CS does not support "
                              "Direct push Installation to Windows Client")
                rc_client_name = self.config_json.Install.rc_client.client_name
                if self.commcell.clients.has_client(rc_client_name):
                    self.rc_machine = Machine(machine_name=rc_client_name, commcell_object=self.commcell)
                    self.rc_machine.add_host_file_entry(windows_helper.client_host, "0.0.0.0")
                    self.rc_client = self.commcell.clients.get(rc_client_name)

            job = windows_helper.install_software(
                client_computers=[windows_helper.client_host],
                features=['FILE_SYSTEM', 'MEDIA_AGENT'],
                sw_cache_client=self.rc_client.client_name if self.rc_client else None)
            if job.wait_for_completion(5):
                self.log.error(f"The machine is reachable with Hostname :{windows_helper.client_host}")
                raise Exception("Host file entry failed and client installation successful")

            self.cs_machine.remove_host_file_entry(windows_helper.client_host)
            if self.rc_client:
                self.rc_machine.remove_host_file_entry(windows_helper.client_host)
            job_status = job.delay_reason

            if not (installer_messages.QINSTALL_ERROR_CREATE_TASK in job_status or
                    installer_messages.QINSTALL_ERROR_ACCESS_REMOTE_REG in job_status):
                self.log.error("Job Failed due to some other reason than the expected one.")
                raise Exception(job_status)

            self.log.info("JobFailingReason:%s", job_status)

        except Exception as exp:
            self.log.error("Failed with an error: %s", exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.cs_machine.remove_host_file_entry(self.windows_machine.machine_name)
