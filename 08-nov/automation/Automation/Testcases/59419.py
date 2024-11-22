# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Testcase for install/uninstall of BLR package from Command center
Sample json
    "HostName": "vm1",
    "UserName": "admin",
    "Password": "password",
"""
from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure


class TestCase(CVTestCase):
    """Class for executing Command Center DR replica"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Install/Uninstall BLR package from CC"
        self.tcinputs = {
            "HostName": None,
            "UserName": None,
            "Password": None,
        }
        self.utils = None
        self.hostname = None
        self.username = None
        self.password = None

        self.admin_console = None
        self.servers = None
        self.file_servers = None

    def login(self):
        """Logs in to command center"""
        self.admin_console = AdminConsole(BrowserFactory().create_browser_object().open(),
                                          self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(
            self.inputJSONnode['commcell']['commcellUsername'],
            self.inputJSONnode['commcell']['commcellPassword'],
        )
        self.servers = Servers(self.admin_console)

    def logout(self):
        """Logs out of command center"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.admin_console.browser)

    def setup(self):
        """Sets up the variables for the test case"""
        try:
            self.utils = TestCaseUtils(self)
            self.hostname = self.tcinputs['HostName']
            self.username = self.tcinputs['UserName']
            self.password = self.tcinputs['Password']

        except Exception as exp:
            raise CVTestCaseInitFailure(f"Failed to initialize testcase") from exp

    def monitor_job_completion(self, job_id):
        """Monitors that the job has completed"""
        job = self.commcell.job_controller.get(job_id)
        self.log.info('Waiting for job [%s] to complete', job_id)
        job.wait_for_completion()
        self.utils.assert_comparison(job.status, 'Completed')

    @test_step
    def install_new_client(self):
        """Install the BLR package on the new client"""
        self.admin_console.navigator.navigate_to_servers()
        blr_install_jobid = self.servers.add_server_new_windows_or_unix_server(hostname=[self.hostname],
                                                                               username=self.username,
                                                                               password=self.password,
                                                                               os_type="Windows",
                                                                               packages=["Block Level Replication"],
                                                                               reboot=True)
        self.logout()
        self.monitor_job_completion(blr_install_jobid)
        self.commcell.clients.refresh()
        self.client = self.commcell.clients.get(self.hostname)

    @test_step
    def verify_driver_installation(self):
        """Verifies that the BLR driver was successfully installed"""
        for _ in range(15):
            if self.client.is_ready:
                break
            self.log.info('Waiting for client [%s] to be ready', self.client.client_name)
            sleep(60)
        client_machine = Machine(machine_name=self.client, commcell_object=self.commcell)
        log_file_name = 'DriverInstaller.log'
        if not client_machine.is_file(client_machine.join_path(self.client.log_directory, log_file_name)):
            raise CVTestStepFailure(f"Log file {log_file_name} doesn't exist")
        if 'CvFsBlr Installed successfully' not in client_machine.get_log_file(log_file_name):
            raise CVTestStepFailure(f"Driver not installed. Please check logs")

    @test_step
    def retire_server(self):
        """Retires the client from the servers page"""
        self.client = self.commcell.clients.get(self.hostname)
        self.admin_console.navigator.navigate_to_servers()
        retire_jobid = self.servers.retire_server(self.client.client_name)
        self.monitor_job_completion(retire_jobid)

        self.commcell.clients.refresh()
        if self.commcell.clients.has_client(self.client.client_name):
            self.servers.delete_server(self.client.client_name)
        self.client = None

    def run(self):
        try:
            self.login()

            self.install_new_client()
            self.verify_driver_installation()

            self.login()
            self.retire_server()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        self.logout()
