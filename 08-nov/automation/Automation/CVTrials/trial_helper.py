from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ---------------------------------------------------------------------------

"""
This module provides the function or operations related to Commvault trial
TrialHelper : This class provides methods for trial related operations

TrialHelper
===========

    register_for_free_trial()       -- To register for commvault free trial

    get_registration_mail()         -- To find and select the registration mail

    get_mail_contents()             -- To get the Commvault ID, Password and Activation code
    from the mail send from the sender

    _get_application_name()         -- To get the Commvault Express file name

    _validate_trial_video()         -- To validate the commvault trial install video

    login_to_cloud()                -- To login into Commvault's cloud

    execute_workflow()              -- To execute a workflow

    delete_commvaultone_trial_user() -- To execute workflow on the forevercell

    wait_for_download()             -- To wait for the file to be downloaded from the browser

    execute_command()               -- To execute a command on the remote machine using PsExec

    download_trial_package_from_cloud() -- To download the commvault software trial package

    silent_install_trial_package()  -- To install the commvault software trial package in background

    interactive_install_trial_package() -- To install the commvault software trial package in background

    register_trial_package()        -- To register the commvault software trial package

    configure_core_setup()          -- To configure Adminconsole core setup

    configure_virtualization()      -- To configure Virtualization on the getting started
    page of the admin console

"""

import re
import json
import time
import os
import subprocess

from cvpysdk.commcell import Commcell
from cvpysdk.exception import SDKException

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from AutomationUtils.machine import Machine
from AutomationUtils.constants import CVTRIALS_DIRECTORY, AUTOMATION_DIRECTORY
from AutomationUtils.options_selector import OptionsSelector
from Web.MarketPlace.commvault_trial import CommvaultTrial
from Web.Gmail.gmail import Gmail
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Setup.registration import Registration
from Web.AdminConsole.Setup.login import LoginPage
from Web.AdminConsole.Setup.core_setup import Setup
from Web.AdminConsole.Setup.getting_started import GettingStarted
from Web.AdminConsole.Setup.vsa_getting_started import Virtualization
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Install.installer_constants import QINSTALLER_RETURNCODES


class TrialHelper:
    """Helper file for performing commvault trial related operations"""

    def __init__(self, testcase):
        """
        TrialHelper class initialization

        Args:
            testcase    (object)    -- object of TestCase class

        """
        self.commcell = testcase.commcell
        self.log = testcase.log
        self.tcinputs = testcase.tcinputs
        self.testcase = testcase
        self._trial_details = {}

        self._driver = None
        self._admin_console = None
        self.url = None
        self.trial = None
        self.gmail = None
        self.setup = None
        self.job = None
        self.virtualization = None
        self.getting_started = None

        if hasattr(testcase, 'driver'):
            self.driver = testcase.driver

        self.machine = Machine()
        self.options_selector = None

    @property
    def driver(self):
        """Returns the driver object"""
        return self._driver

    @driver.setter
    def driver(self, driver):
        """Sets the driver related classes"""
        if not driver:
            return
        self._driver = driver
        self.trial = CommvaultTrial(self.driver)
        self.gmail = Gmail(self.driver)

    @property
    def admin_console(self):
        """Returns the admin console object"""
        return self._admin_console

    @admin_console.setter
    def admin_console(self, admin_console):
        """Sets the admin console object and initialises the classes which use driver"""
        if not admin_console:
            return
        self._admin_console = admin_console
        self.setup = Setup(self._admin_console)
        self.virtualization = Virtualization(self.admin_console)
        self.driver = self._admin_console.driver

    @property
    def trial_details(self):
        """Returns the details for trial related operations"""
        return self._trial_details or self.get_mail_contents(self.tcinputs.get('GmailUsername'))

    def register_for_free_trial(
            self,
            username=None,
            password=None,
            first_name=None,
            last_name=None,
            phone=None,
            postal_code=None,
            company=None,
            email=None,
            country=None):
        """
        To register for commvault free trial

        Args:
            username        (str)   -- Cloud username to perform trial related operations

            password        (str)   -- Password for the Trial account

            first_name      (str)   -- First name of the new user

            last_name       (str)   -- Last name of the new user

            phone           (str)   -- Phone number of the new user

            postal_code     (str)   -- postal code of the new user

            company         (str)   -- Company the user belongs

            email           (str)   -- Email ID of the new user

            country         (str)   -- Country of the new user

        """
        url = "https://cloud.commvault.com/webconsole/RestServlet/Login"
        payload = {
            "username": username,
            "password": password
        }
        cvpysdk = self.commcell._cvpysdk_object
        flag, response = cvpysdk.make_request('POST', url=url, payload=payload)

        if flag:
            if response.json() and 'token' in response.json():
                authtoken = response.json()['token']
            else:
                raise SDKException('Response', '102')
        else:
            raise SDKException('Response', '101', cvpysdk._update_response_(response.text))

        headers = {
            'Accept': 'application/json',
            'Content-type': 'application/json',
            'Authtoken': authtoken
        }

        url = "https://cloud.commvault.com/webconsole/RestServlet/wapi/Generate%20Trial%20Activation%20Code"

        payload = {
            "Email": email,
            "FirstName": first_name,
            "LastName": last_name,
            "Phone": phone,
            "Company": company,
            "Country": country,
            "TrialId": "7",
            "PartnerId": "0"
        }

        flag, response = cvpysdk.make_request('POST', url=url, payload=payload, headers=headers)

        if flag:
            if response.json() and 'jobId' in response.json():
                job_id = response.json()['jobId']
                self.log.info(f'Job: {job_id} started successfully')
            else:
                raise SDKException('Response', '102')
        else:
            raise SDKException('Response', '101', cvpysdk._update_response_(response.text))

        self.log.info("Successfully registered commvault free trial")

    def get_registration_mail(
            self,
            sender=None):
        """
        To find and select the latest commvault registration mail

        Args:
            sender      (str)   -- Full Email ID of the sender

        """
        # To login to the Gmail page
        self.gmail.navigate_to_gmail()
        self.gmail.login(
            username=self.tcinputs.get('GmailUsername'),
            password=self.tcinputs.get('GmailPassword')
        )

        count = 0
        while count < 300:
            try:
                self.gmail.select_latest_mail_from_sender(sender)
                self.log.info('Registration mail received successfully in : %s seconds', count)
                return
            except Exception:
                time.sleep(10)
                count += 10

        raise Exception('Commvault registration mail not received within 5 minutes')

    def get_mail_contents(
            self,
            sender=None):
        """
        To get the Commvault ID, Password and Activation code from the mail send from the sender

        Args:
            sender      (str)   -- Full Email ID of the sender

        Returns:
            (dict)      -- dict of the mail contents

                 sample:

                    {
                    "Commvault ID": "value",
                    "Password": "value",
                    "Activation code": "value"
                    }

        """
        # To select the latest mail from the sender
        self.get_registration_mail(sender)

        # To get the username and password from mail
        try:
            element = self.driver.find_element(By.XPATH, "//b[text()='Password']/..")
        except Exception:
            raise Exception('Unable to locate the Password in the mail')

        self._trial_details['Commvault ID'] = re.search("Commvault ID: (.*)", element.text).group(1)
        self._trial_details['Password'] = re.search("Password: (.*)", element.text).group(1)

        # To get the activation code
        try:
            element = self.driver.find_element(By.XPATH, "//p/b[contains(text(), 'Trial Activation Code')]/..")
            self._trial_details['Activation Code'] = element.text.split(
                'Trial Activation Code: ')[1].split('\n')[0].strip()
        except Exception:
            raise Exception('Unable to locate the Activation code in the mail')

        self.log.info('Mail contents are successfully retrieved')
        return self.trial_details

    def _get_application_name(self):
        """To get the Commvault Express file name"""
        element = "//td[contains(text(),'CommvaultExpress')]"
        if self.trial.check_if_entity_exists('xpath', element):
            file_name = self.driver.find_element(By.XPATH, element).text
            self.log.info('Trial software file name: "%s"', file_name)
            return file_name
        raise Exception('Commvault Express not found in trial download page')

    def _validate_trial_video(self):
        """To validate the commvault Trial video"""
        try:
            # To pause the video to get the time
            self.driver.find_element(By.XPATH, '//button[@class="ytp-play-button ytp-button"]').click()
            self.trial.wait_for_completion()
            if (self.driver.find_element(By.CLASS_NAME, "ytp-time-duration").text == '2:49' and
                    self.trial.check_if_entity_exists('xpath', '//a[contains(text(),"Commvault")]')):
                self.log.info('Commvault trial video validation successful')
            else:
                self.log.error('Commvault trial install video changed')
                raise Exception
        except Exception:
            raise Exception('Commvault Trial video validation failed, please check the logs')

    def login_to_cloud(
            self,
            username=None,
            password=None,
            stay_logged_in=True):
        """
        To login into Commvault's cloud

        Args:
            username        (str)   -- Cloud username to login

            password        (str)   -- Cloud password to login

            stay_logged_in  (bool)  -- set to true will keep user logged in
                                        default: True

        """
        self.trial.fill_form_by_id("username", username)
        self.driver.find_element(By.ID, "continuebtn").click()
        self.trial.wait_for_completion()
        self.trial.fill_form_by_id("password", password)

        if stay_logged_in:
            self.driver.find_element(By.ID, 'stayactivebox')
        else:
            self.trial.checkbox_deselect("stayactivebox")

        self.trial.select_hyperlink('Login')

    def execute_workflow(
            self,
            commcell=None,
            workflow_name=None):
        """
        To execute the workflow on the given commcell machine

        Args:
            commcell        (obj)   -- Commcell class object

            workflow_name   (str)   -- Name of the workflow to be executed on the commcell machine

        """
        self.log.info('Executing "%s" workflow', workflow_name)
        workflow = commcell.workflows.get(workflow_name)
        _, job = workflow.execute_workflow()

        if not job.wait_for_completion():
            raise Exception(
                "Failed to execute the workflow with error: " + job.delay_reason
            )

        self.log.info('Successfully Executed "%s" Workflow', workflow_name)

    def delete_commvaultone_trial_user(
            self,
            cloud_username=None,
            cloud_password=None):
        """
        To execute workflow on the forevercell machine

        Args:
            cloud_username  (str)   -- Cloud username to login to the cloud machine

            cloud_password  (str)   -- Cloud password to login

        """
        commcell = Commcell(
            'cloud.commvault.com',
            cloud_username,
            cloud_password)

        self.execute_workflow(commcell, 'delete commvault one trial user')

    def wait_for_download(self, file_path=None, wait_time=300):
        """
        To wait for the file to be downloaded from the browser

        Args:
            file_path   (str)   -- Full path of the file to be downloaded

            wait_time   (int)   -- Time to wait for the download to complete in seconds
                                    default: 300

        """
        time_taken = 0

        while time_taken <= wait_time:
            if self.machine.check_file_exists(file_path):
                self.log.info("File downloaded successfully at the location '%s'", file_path)
                return

            time.sleep(10)
            time_taken += 10

        raise Exception('File not downloaded within the time limit given')

    def execute_command(
            self,
            hostname=None,
            username=None,
            password=None,
            machine=None,
            paexec_path=None,
            command=None):
        """
        To execute the command on the remote machine using PsExec.exe

        Args:
            hostname    (str)   -- Full hostname of the machine to execute command on

            username    (str)   -- Username to connect to the machine

            password    (str)   -- Password to connect to the machine

            command     (str)   -- Command to execute on the remote machine
            paexec_path (str):  -- paexec.exe path
            machine     (obj):  -- Machine object

        Returns:
            (int)       -- Return code of the command executed

        """
        if not machine:
            machine = Machine(hostname, username=username, password=password)

        if paexec_path:
            cmd = (f'cmd.exe /c "{paexec_path}"'
                   f' "\\\\localhost"'
                   f' -i 0'
                   f' "{command}"')
        else:
            cmd = f'cmd.exe /c "{command}"'

        return machine.execute_command(cmd)

    def download_trial_package_from_cloud(
            self,
            sender=None,
            path=None):
        """
        To download the commvault software trial package

        Args:

            sender      (str)   -- Sender of the registration mail

            path        (str)   -- FUll path to download the file

        """
        # To open the registration mail and get the contents
        contents = self.get_mail_contents(sender)

        # To open new tab
        self.trial.open_new_tab()

        # To switch to the new tab
        self.trial.switch_to_latest_tab()

        # Disable SSO to overcome popup login
        self.trial.navigate('https://cloud.commvault.com/webconsole/login/index.jsp?disableSSO')

        # To login to cloud
        self.login_to_cloud(contents.get('Commvault ID'), contents.get('Password'))

        # To close the new tab
        self.trial.close_current_tab()

        # To switch to the open tab
        self.trial.switch_to_latest_tab()

        # # To click on install video link from the mail received
        # self.gmail.select_hyperlink('installation video')
        #
        # # To switch to the open tab
        # self.trial.switch_to_latest_tab()
        #
        # # To validate install video
        # self._validate_trial_video()
        #
        # # To close the new tab
        # self.trial.close_current_tab()
        #
        # # To switch to the open tab
        # self.trial.switch_to_latest_tab()

        # To click on install video link from the mail received
        self.gmail.select_hyperlink('Quick Start Guide')

        # To sleep for 30s for the PDF page to load
        time.sleep(30)

        # To switch to the open tab
        self.trial.switch_to_latest_tab()

        try:
            # To validate quick start guide
            self.driver.find_element(By.XPATH, 
                '//embed[@src="http://documentation.commvault.com/commvault/v11_sp16/others/pdf/'
                'Quick_Start_for_the_Commvault_Trial_Package.pdf"]'
            )
            self.log.info('Quick start guide validation successful')
        except Exception:
            raise Exception('Commvault quick start guide changed')

        # To close the new tab
        self.trial.close_current_tab()

        # To switch to the open tab
        self.trial.switch_to_latest_tab()

        # To click on telephone support link
        self.driver.find_element(By.XPATH, '//a[contains(text(),"Support")]').click()
        self.trial.wait_for_completion()

        # To switch to the open tab
        self.trial.switch_to_latest_tab()

        # To validate support document
        if self.trial.check_if_entity_exists('xpath', '//h1[contains(text(),"Telephone-Based Support")]'):
            self.log.info('Telephone support document validation successfull')
        else:
            raise Exception('Telephone support document validation failed')

        # To close the new tab
        self.trial.close_current_tab()

        # To switch to the open tab
        self.trial.switch_to_latest_tab()

        # To click on the privacy document link
        self.driver.find_element(By.XPATH, '//a[text()="privacy policy"]').click()
        self.trial.wait_for_completion()

        # To switch to the open tab
        self.trial.switch_to_latest_tab()

        # To validate privacy document
        if self.trial.check_if_entity_exists('xpath', '//h2[contains(text(),"Commvault Privacy Policy")]'):
            self.log.info('Privacy document validation successfull')
        else:
            raise Exception('Privacy document validation failed')

        # To close the new tab
        self.trial.close_current_tab()

        # To switch to the open tab
        self.trial.switch_to_latest_tab()

        # To open the download link from the mail
        self.gmail.select_hyperlink('here')

        # To switch to the open tab
        self.trial.switch_to_latest_tab()

        # To start download
        self.driver.find_element(By.XPATH, '//button/span[contains(text(),"Download")]').click()
        self.trial.wait_for_completion()

        self.log.info('Selected download button')

        # To go to the new tab if download asks for confirmation
        self.trial.switch_to_latest_tab()
        if self.trial.check_if_entity_exists('id', 'proceed'):
            self.driver.find_element(By.ID, 'proceed').click()
            self.log.info("Proceeding further with download")

        self.log.info("Download started")

        # sleep for 5 minutes for download to complete
        wait = 300
        if wait > 0 and not self.machine.get_files_in_path(path):
            time.sleep(10)
            wait -= 10

        # To check if the file is successfully downloaded
        file_path = self.machine.get_files_in_path(path)

        if not file_path or 'CommvaultExpress' not in file_path[0]:
            raise Exception('File not downloaded within the 5 minutes')
        self.log.info("File downloaded successfully at the location '%s'", file_path[0])

        # To include file path in the contents
        contents['SoftwarePath'] = file_path[0]
        contents['FileName'] = os.path.split(file_path[0])[1]

        # To set all the trial related contents
        self._trial_details = contents

    def silent_install_trial_package(
            self,
            hostname=None,
            username=None,
            password=None,
            software_path=None):
        """
        To install the commvault trial package in the background

        Args:
            hostname        (str)   -- Full hostname of the machine to install package on

            username        (str)   -- Username of the machine

            password        (str)   -- Password of the machine

            software_path   (str)   -- Full path of the commvault trial software package

        """
        # To create machine class object for the machine to install trial package on
        machine = Machine(hostname, username=username, password=password)
        self.log.info(
            'Successfully created machine class object for machine %s',
            machine.machine_name
        )

        # To initialize options selector class
        self.options_selector = OptionsSelector(self.commcell)

        # To select drive with enough space
        self.log.info('Selecting drive on the machine based on space available')
        drive = self.options_selector.get_drive(machine, size=50)
        if drive is None:
            raise Exception(f"Installation cancelled, Insufficient space on machine {machine.machine_name}")
        self.log.info('selected drive: %s', drive)

        # Directory to copy the batch file and the trial application
        install_directory = machine.join_path(drive, 'commvault_trial')

        # To remove install directory if exists
        if machine.check_directory_exists(install_directory):
            machine.remove_directory(install_directory)
            self.log.info('Successfully removed directory %s', install_directory)

        # To create install directory on the machine
        machine.create_directory(install_directory)
        self.log.info(
            'Successfully created Commvault trial directory in path "%s"',
            install_directory)

        # Batch file to trigger commvault trial installation
        batch_file = machine.join_path(CVTRIALS_DIRECTORY, 'silent_install.bat')

        # To copy the batch file
        output = machine.copy_from_local(batch_file, install_directory, raise_exception=True)

        # To validate if copy succeeded
        if not output:
            raise Exception(
                f'Failed to copy silent install batch file to the machine {machine.machine_name}')
        self.log.info('Successfully copied the silent install batch file to machine %s', machine.machine_name)

        # To copy the commvault trial software
        output = machine.copy_from_local(software_path, install_directory, raise_exception=True)

        # To validate if copy succeeded
        if not output:
            raise Exception(
                f'Failed to copy the Trial software to the machine {machine.machine_name}')
        self.log.info(
            'Successfully copied the Trial software to machine %s', machine.machine_name)

        batch_file = machine.join_path(install_directory, 'silent_install.bat')
        exe_path = machine.join_path(install_directory, os.path.split(software_path)[1])

        self.log.info('Waiting for Commvault Package installation to complete')
        output = self.execute_command(hostname=hostname,
                                      username=username,
                                      password=password,
                                      command=f'"{batch_file}" "{exe_path}"')

        if output == 0:
            self.log.info('Installation Completed successfully')
        else:
            error = QINSTALLER_RETURNCODES.get(output, 1)
            self.log.error('Installation Status: "%s"', error)
            raise Exception(f'Installation failed with error code: {output} status: {error}')

        # To sleep for 5 minutes
        self.log.info('Sleeping for 5 minutes, for the services to come up')
        time.sleep(300)

        # To remove install directory on the machine
        machine.remove_directory(install_directory)
        self.log.info(
            'Successfully deleted Commvault trial directory in path "%s"',
            install_directory)

    def interactive_install_trial_package(
            self,
            hostname=None,
            username=None,
            password=None,
            software_path=None,
            input_json=None,
            machine=None,
    ):
        """
        To install the commvault trial package interactively

        Args:
            hostname        (str)   -- Full hostname of the machine to install package on

            username        (str)   -- Username of the machine

            password        (str)   -- Password of the machine

            software_path   (str)   -- Full path of the commvault trial software package

            input_json      (dict)  -- Input for interactive install exe
                                Refer: Automation/Install/InteractiveInstall/UserInput.cs

            machine:

        """
        # To create machine class object for the machine to install trial package on
        if not machine:
            machine = Machine(hostname, username=username, password=password)
        self.log.info(
            'Successfully created machine class object for machine %s',
            machine.machine_name
        )

        # To initialize options selector class
        self.options_selector = OptionsSelector(self.commcell)

        # To select drive with enough space
        self.log.info('Selecting drive on the machine based on space available')
        drive = self.options_selector.get_drive(machine, size=50)
        if drive is None:
            raise Exception(f"Installation cancelled, Insufficient space on machine {machine.machine_name}")
        self.log.info('selected drive: %s', drive)

        # Directory to copy the batch file, trial application and interactive install exe
        install_directory = machine.join_path(drive, 'commvault_trial')
        log_directory = machine.join_path(drive, 'AUTOMATION_LOC')

        # To remove install directory if exists
        if machine.check_directory_exists(install_directory):
            machine.remove_directory(install_directory)
            self.log.info('Successfully removed directory %s', install_directory)

        # To remove log directory if exists
        if machine.check_directory_exists(log_directory):
            machine.remove_directory(log_directory)
            self.log.info('Successfully removed directory %s', log_directory)

        # To create install directory on the machine
        machine.create_directory(install_directory)
        self.log.info(
            'Successfully created Commvault trial directory in path "%s"',
            install_directory)

        # To create log directory on the machine
        machine.create_directory(log_directory)
        self.log.info(
            'Successfully created Commvault trial log directory in path "%s"',
            log_directory)

        # Interactive install exe to perform install interactively
        exe_file = machine.join_path(AUTOMATION_DIRECTORY, 'CompiledBins', 'InteractiveInstall.exe')

        # To copy the exe file
        output = machine.copy_from_local(exe_file, install_directory, raise_exception=True)

        # To validate if copy succeeded
        if not output:
            raise Exception(
                f'Failed to copy interactive install exe to the machine {machine.machine_name}')
        self.log.info('Successfully copied the interactive install exe to machine %s', machine.machine_name)

        # To copy the commvault trial software
        output = machine.copy_from_local(software_path, install_directory, raise_exception=True)

        # To validate if copy succeeded
        if not output:
            raise Exception(
                f'Failed to copy the Trial software to the machine {machine.machine_name}')
        self.log.info(
            'Successfully copied the Trial software to machine %s', machine.machine_name)

        # To generate the user input json
        user_input = self.machine.join_path(CVTRIALS_DIRECTORY, 'UserInput.json')

        with open(user_input, 'w')as file:
            file.write(json.dumps(input_json))

        # To copy the user input json
        output = machine.copy_from_local(user_input, install_directory, raise_exception=True)

        # To validate if copy succeeded
        if not output:
            raise Exception(
                f'Failed to copy the user input json to the machine {machine.machine_name}')
        self.log.info(
            'Successfully copied the User input json to machine %s', machine.machine_name)

        batch_file = machine.join_path(install_directory, 'install.bat')
        bootstrapper_path = machine.join_path(install_directory, os.path.split(software_path)[1])
        install_exe = machine.join_path(install_directory, 'InteractiveInstall.exe')
        installer_path = machine.join_path(install_directory, 'installer')
        user_input = machine.join_path(install_directory, 'UserInput.json')
        paexec_path = machine.join_path(installer_path, 'ThirdParty', 'CVInstallThirdParty', 'paexec.exe')

        # To generate the install.bat file
        command = f'cmd.exe /c {bootstrapper_path} /d {installer_path} /silent /noinstall'
        output = machine.execute_command(command)

        if output.exit_code != 0:
            raise Exception(f'Bootstrapper failed with error code: {output.exit_code} status: {output.output}')

        command = rf'''"{install_exe}" -PATH "{machine.join_path(installer_path, 'Setup.exe')}" -PLAY "{user_input}"
        set errorCode = %ERRORLEVEL%
        EXIT %errorCode%'''

        if not machine.create_file(batch_file, command):
            raise Exception('Batch file creation failed')

        self.log.info('Waiting for Commvault Package installation to complete')
        output = self.execute_command(machine=machine, command=batch_file, paexec_path=paexec_path)

        if output.exit_code == 0:
            self.log.info('Interactive Installer exe Completed successfully')
        else:
            error = QINSTALLER_RETURNCODES.get(output, 1)
            self.log.error('Installer Status: "%s"', error)
            raise Exception(f'Installer failed with error code: {output} status: {error}')

        if not input_json.get('IsToDownload'):
            # To sleep for 5 minutes
            self.log.info('Sleeping for 5 minutes, for the services to come up')
            time.sleep(300)

            # To validate if Adminconsole is opened in the browser
            command = ('Write-Host (Get-WmiObject Win32_Process '
                       '| select CommandLine '
                       '| Select-String -Pattern "adminconsole")')
            output = machine.execute_command(command)
            if 'adminconsole' not in output.output:
                raise Exception('Admin console not opened in browser')
            self.log.info('Admin console URL validation successful')

        # To remove install directory on the machine
        machine.remove_directory(install_directory)
        self.log.info(
            'Successfully deleted Commvault trial directory in path "%s"',
            install_directory)

    def register_trial_package(
            self,
            url=None,
            commcell_username=None,
            commcell_password=None,
            activation_code=None,
            new_user=False,
            first_name=None,
            last_name=None,
            company_name=None,
            phone_number=None,
            address1=None,
            address2=None,
            city=None,
            state=None,
            postal_code=None,
            country=None
    ):
        """
        To register commvault trial package

        Args:
            url                 (str)   -- Admin console URL

            commcell_username   (str)   -- username to login to admin console

            commcell_password   (str)   -- password to login to admin console

            activation_code     (str)   -- Activation code for the commcell

            new_user            (bool)  -- Set to True, to register a new user
                                            default: False

            first_name          (str)   -- First name of the user

            last_name           (str)   -- Last name of the user

            company_name        (str)   -- Company name

            phone_number        (str)   -- The complete phone no with country and area code
                                            Example:    001-002-1234567890

            address1            (str)   -- Line 1 of the address

            address2            (str)   -- Line 2 of the address

            city                (str)   -- Name of the city

            state               (str)   -- Name of the state

            postal_code         (str)   -- Postal code of the place

            country             (str)   -- Name of the country

        **Note** First 4 inputs are required for registering a existing user, for a new user all inputs are required

        """
        # To initialize the registration page
        registration = Registration(self.driver)

        # To navigate to the admin console page
        registration.navigate(url)

        # To wait for a maximum of 5 minutes for the page to load
        timeout = 300
        try:
            element_present = EC.presence_of_element_located((By.NAME, 'username'))
            WebDriverWait(self.driver, timeout).until(element_present)
        except TimeoutException:
            self.log.error('Waited for 5 minutes, Admin Console page is not reachable')
            raise Exception('Waited for 5 minutes, Admin Console page is not reachable')

        if new_user:
            # To register a new user
            registration.fill_user_details(
                commcell_username,
                commcell_password,
                activation_code
            )

            registration.fill_contact_details(
                first_name,
                last_name,
                company_name,
                phone_number
            )

            registration.fill_mailing_address(
                address1,
                address2,
                city,
                state,
                postal_code,
                country
            )
        else:
            # To register the account in adminconsole
            registration.register_existing_account(
                email=commcell_username,
                password=commcell_password,
                activation_code=activation_code
            )

        # To login to admin console
        login = LoginPage(self.driver)
        login.login(commcell_username, commcell_password)

        self.log.info('Registration and Login Successful')

    def configure_core_setup(
            self,
            pool_name=None,
            media_agent=None,
            username=None,
            password=None,
            path=None,
            partition_path=None):
        """
        To configure core setup page of Admin console

        Args:
            pool_name       (str)   -- Name of the storage pool to be created

            media_agent     (str)   -- media agent to be selected, by default it is selected

            username        (str)   -- Username for the network path

            password        (str)   -- Password for the network path

            path            (str)   -- Path to be selected as storage

            partition_path  (str)   -- DDB partition path

        """
        # To configure core setup
        if not self.setup:
            raise CVWebAutomationException("Helper object has not been configured with admin"
                                           "console object")
        setup = self.setup

        # To get started with the configuration
        setup.select_get_started()
        self.log.info('Successfully selected "Getting Started button"')

        # To add storage pool
        setup.add_storage_pool(
            pool_name=pool_name,
            media_agent=media_agent,
            username=username,
            password=password,
            path=path,
            partition_path=partition_path,
        )
        self.log.info('Successfully added storage pool')

        # To create server backup plan
        # Using default Admin console values for backup
        time.sleep(60)
        setup.create_server_backup_plan()
        self.log.info('Successfully created server backup plan')

        # To validate if core setup configuration is completed or not
        if setup.admin_console.check_if_entity_exists('xpath', '//div[@data-ng-if="coreSetupCompleted"]'):
            self.log.info('Successfully configured core setup')
        else:
            raise Exception('Core setup configuration failed please check the logs')

    def configure_virtualization(
            self,
            url=None,
            commcell_username=None,
            commcell_password=None,
            hostname=None,
            machine_username=None,
            machine_password=None,
            group_name=None,
            virtual_machines=None):
        """
        To configure Virtualization on the getting started page of the admin console
        and to run VSA backup job

        Args:
            url                 (str)   -- Admin console URL

            commcell_username   (str)   -- username to login to admin console

            commcell_password   (str)   -- password to login to admin console

            hostname            (str)   -- Full hostname of the machine

            machine_username    (str)   -- username to access the machine

            machine_password    (str)   -- Password for accessing the machine

            group_name          (str)   -- Name for the VM group

            virtual_machines    (list)  -- List of vms to select

        """
        # To login to admin console
        login = LoginPage(self.driver)

        # To navigate to admin console URL
        login.navigate(url)

        login.login(commcell_username, commcell_password)

        self.getting_started = GettingStarted(self.driver)

        # To track backup job
        self.job = Jobs(self.driver)

        # To navigate to the virtualization page of the admin console
        self.getting_started.navigate_to_getting_started()
        self.getting_started.configure_wizard_for_solution('Virtualization')

        if not self.virtualization:
            raise Exception("Please set admin console to set virtualization object")
        # To add a new hypervisor
        self.virtualization.add_hypervisor(
            hostname=hostname,
            hypervisor_name=hostname,
            username=machine_username,
            password=machine_password
        )
        self.log.info('Successfully added new hypervisor %s', hostname)
        self.virtualization.wait_for_completion()

        # To add a new VM group
        self.virtualization.add_vm_group(
            group_name=group_name,
            virtual_machines=virtual_machines
        )
        self.log.info('Successfully added new VM group %s', group_name)

        # To run first backup job
        self.virtualization.run_backup()

        # To refresh the page
        self.virtualization.refresh_page()

        # To get the Job ID from the page
        job = self.driver.find_element(By.XPATH, '//h1[@class="page-title ng-binding"]').text
        job_id = re.findall(r'\d+', job)[0]
        jobs = Jobs(self.driver)
        output = jobs.job_completion(job_id)

        if 'Completed' not in output.get('Status'):
            self.log.info('virtualization Backup failed')
            raise Exception('virtualization Backup failed')

        self.log.info('Virtualization backup successful')
        self.log.info('Virtualization configuration successful')
