# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils import constants
import paramiko
import subprocess

class TestCase(CVTestCase):
    """Class for executing test cases from other languages in autocenter"""

    def __init__(self):
        """Initializes the test case class object"""
        super().__init__()
        self.name = "Default developer test case"
        self.ssh_client = None
        self.machine = None
        self.tcinputs = {
            "command": ""
        }

    def setup(self):
        """Setup function for this test case"""
        self.command = self.tcinputs["command"]

        # If remote machine credentials are not passed in the input, the command will be executed on the local machine
        self.remote_hostname = self.tcinputs.get("hostname")
        self.remote_username = self.tcinputs.get("username")
        self.remote_password = self.tcinputs.get("password")
        self.port = self.tcinputs.get('port', 22)  # Needed only if SSH is running on a port other than 22

    def run(self):
        """Main function for test case execution"""
        self.status = constants.FAILED
        output = None

        if self.remote_hostname:
            try:
                output = self.execute_command_via_ssh()
            except Exception as err:
                self.log.error(f"Execution via SSH failed with exception: {str(err)}")

                # Fall back to the second method
                try:
                    output = self.execute_command_via_ps()
                except Exception as err:
                    self.log.error(f"Execution via WinRM failed with exception: {str(err)}")
        else:
            try:
                output = self.execute_command_locally()
            except Exception as err:
                self.log.error(f"Local command execution failed with exception: {str(err)}")

        if not output:
            self.result_string = "Couldn't fetch any information from the remote/local machine! Please ensure that either SSH or WinRM is properly configured."
            return

        self.log.info(f'Raw output => {output}')
        output_dict = eval(output)
        self.log.info(f'Parsed Output => {output_dict}')

        """
            Expected Output Format: 
                {'errorCode': 500, 'errorMessage': 'Plan Creation Failed'}
        """

        if 'errorCode' not in output_dict:
            raise Exception(f'errorCode is missing in the received response: {output_dict}')

        error_code = int(output_dict['errorCode'])
        error_message = output_dict.get("errorMessage",'')

        if error_code != 0:
            self.result_string = error_message
        else:
            self.status = constants.PASSED

    def tear_down(self):
        """Tear down function for this test case"""
        try:
            if self.ssh_client:
                transport = self.ssh_client.get_transport()
                if transport and transport.is_active():
                    self.ssh_client.close()

            if self.machine:
                self.machine.disconnect()

        except Exception as err:
            self.log.error(f'Exception occurred while closing the connection: {err}')

    def execute_command_via_ssh(self) -> str:
        """
        Helper function to connect via SSH and run the command remotely
        
        Note: Ensure SSH works from the controller to the remote machine.
        
        Follow the below steps to enable SSH on Windows Servers:
            1. Search for "Optional Features" in Windows Search.
            2. Click on "Add a feature".
            3. Install OpenSSH Server.
            4. Start "OpenSSH SSH Server" service from services.msc (If the service does not list here, try uninstalling, restart the server, and reinstall the OpenSSH Server).
            5. Go to service properties and set mode as "Automatic".

        If you run into any issue following the above steps, download and install OpenSSH from the GitHub repo 'PowerShell/Win32-OpenSSH'

        To ensure if SSH is properly configured:
            Manually, try connecting to the remote machine using SSH protocol on port 22
        """
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.ssh_client.connect(self.remote_hostname, self.port, self.remote_username, self.remote_password)

        stdin, stdout, stderr = self.ssh_client.exec_command(self.command)

        output = stdout.read().decode('utf-8')

        self.ssh_client.close()
        return output

    def execute_command_via_ps(self) -> str:
        """
        Helper function to connect via PowerShell and run the command remotely

        Prerequisites:
            1. Check if Remote services (such as Remote Desktop Services, Remote Desktop Configuration) are running in services.msc
            2. Check if Netlogon is running under services.msc
            3. Run "winrm quickconfig" in PowerShell once.
            4. Run "powershell.exe Set-ExecutionPolicy RemoteSigned -Force" in PowerShell.

        To ensure if WinRM is correctly configured:
            Command: Test-WSMan -ComputerName "<RemoteComputerNameOrIP>"
        """
        self.machine = Machine(self.remote_hostname, username=self.remote_username, password=self.remote_password)

        output = self.machine.execute_command(self.command)
        self.machine.disconnect()
        self.machine = None

        if exception := output.exception_message:
            raise exception

        return output.formatted_output

    def execute_command_locally(self) -> str:
        """Helper function to execute command locally"""
        self.log.info('No hostname passed. Running command locally...')
        process = subprocess.Popen(self.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Wait for the command to finish and capture the output
        stdout, stderr = process.communicate()
        output = stdout.decode('utf-8')
        error = stderr.decode('utf-8')

        if return_code := process.returncode:
            self.log.error(f'Command failed with return code: {return_code}')
            raise Exception(error)

        return output
