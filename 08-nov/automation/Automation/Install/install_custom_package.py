# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file for performing install operations

InstallCustomPackage: Helper class to perform Custom package Install

InstallCustomPackage:

    copy_media_to_client()           -- To copy media tp remote client

    install_custom_package()         -- To install custom package on remote client

WindowsInstallCustomPackage:

    execute_command()                -- To execute script on remote client

    install_custom_package()         -- To install custom package on remote windows client

UnixInstallCustomPackage:

    install_custom_package()         -- To install custom package on remote unix client

"""
import os
import json
import time
import tarfile
import xml.etree.ElementTree as ET
from AutomationUtils import logger, constants, config
from AutomationUtils.machine import Machine
from AutomationUtils.constants import AUTOMATION_DIRECTORY
from AutomationUtils.options_selector import OptionsSelector
from Install.installer_constants import REMOTE_FILE_COPY_LOC


class InstallCustomPackage:
    """
        Helper file for Custom package install.

    """

    def __new__(cls, commcell, remote_machine_credentials, remote_client_os_name="windows"):
        """
        Returns (obj) -- Return the class object based on the OS
        """
        if "windows" in remote_client_os_name.lower():
            return object.__new__(WindowsInstallCustomPackage)
        elif "unix" in remote_client_os_name.lower():
            return object.__new__(UnixInstallCustomPackage)

    def __init__(self, commcell, remote_machine_credentials, remote_client_os_name="windows"):
        """
        Initialize the InstallCustomPackage object

        Args:
            commcell (obj)                        -- commcell object

            remote_machine_credentials (dict)     --  Inputs for Installation should be in a dictionary

                Supported key / value for inputs:

                Mandatory:

                    remote_clientname        (str)   -- Clientname of remote machine

                    remote_username          (str)   -- Username to connect to client machine(Domain\\Username)

                    remote_userpassword      (str)   -- Password to to connect to client machine

            remote_client_os_name:               --  OS type of remote client

        """
        self.commcell = commcell
        self.log = logger.get_log()
        self.local_machine = Machine()
        self.remote_machine_credentials = remote_machine_credentials
        self.remote_client_os_name = remote_client_os_name
        self.remote_clientname = remote_machine_credentials["remote_clientname"]
        self.remote_username = remote_machine_credentials["remote_username"]
        self.remote_userpassword = remote_machine_credentials["remote_userpassword"]
        self.machine = Machine(self.remote_clientname,
                               username=self.remote_username,
                               password=self.remote_userpassword)
        self.log.info('Successfully created machine class object for machine %s', self.machine.machine_name)
        self.options_selector = None

    def copy_media_to_client(self, media_path, remote_loc):
        """
            To copy media from controller to remote client machine

            Args:
                media_path         (str)   -- Path where media resides

                remote_loc         (str)   -- Destination path
        """
        output = self.machine.copy_from_local(media_path, remote_loc, raise_exception=True)
        if not output:
            raise Exception(f'Failed to copy media to the machine {self.machine.machine_name}')
        self.log.info('Successfully copied media to machine %s', self.machine.machine_name)

    def install_custom_package(self, full_package_path=None, username=None, password=None, authcode=None, **kwargs):
        """
            To install custom package on the remote client machine

            Args:
                full_package_path         (str)   -- Full package path of seed package in Controller

                username                (str)   -- Username to authenticate client

                password                (str)   -- Password to authenticate client

                authcode                (str)   -- Authcode to authenticate client

            Returns:
                object:
        """
        raise Exception("Method not implemented for this Class")


class WindowsInstallCustomPackage(InstallCustomPackage):
    """Class for performing Custom Package Install operations on a Windows client."""

    def __init__(self, commcell, remote_machine_credentials, remote_client_os_name="windows"):
        """
                Initialize the WindowsInstallCustomPackage object

                Args:
                    commcell (obj)                        -- commcell object

                    remote_machine_credentials (dict)     --  Inputs for Installation should be in a dictionary

                        Supported key / value for inputs:

                        Mandatory:

                            remote_clientname        (str)   -- Clientname of remote machine

                            remote_username          (str)   -- Username to connect to client machine(Domain\\Username)

                            remote_userpassword      (str)   -- Password to to connect to client machine

                    remote_client_os_name:               -- OS type of remote client

        """
        super().__init__(commcell, remote_machine_credentials, remote_client_os_name)
        self.id = None
        self.log_directory = REMOTE_FILE_COPY_LOC
        self.install_directory = None
        self.OEMId = "119"

    # noinspection PyBroadException
    def execute_command(self, command=None, interactive=True):
        """
            To execute the command on the remote machine using PaExec.exe

            Args:

                command     (str)   -- Command to execute on the remote machine

                interactive (bool)  -- Boolean whether install will be interactive

            Returns:
                (int)       -- Return code of the command executed
        """

        task_name = 'Interactive Installation Schedule'
        systime = self.machine.add_minutes_to_system_time(3).strip()
        task_options = f"/tn \"{task_name}\" /tr \"{command}\" /sc daily /st {systime} " \
                       f"/ru {self.machine.username} /rp {self.machine.password} /rl HIGHEST /f"
        if interactive:
            task_options = f"{task_options} /it"
        else:
            task_options = f"{task_options} /np"

        self.machine.create_task(task_options)
        try:
            if interactive:
                self.machine.wait_for_task(task_name, taskstatus="Running", retry_interval=60)
                self.machine.wait_for_task(task_name, retry_interval=120, time_limit=240)
                self.log.info('Checking the return status of Task')
                ps_query = (f"(schtasks /query /FO LIST /V /TN \"{task_name}\"  | findstr \"Result\")"
                            f".substring(12).trim()")
                output = self.machine.execute_command(ps_query)
                if output.output.strip() == '5':
                    self.log.info("Machine requires a reboot. Installer will resume after reboot")
                    _res = self.machine.reboot_client()
                    time.sleep(600)
                    self.log.info("Waiting for Installer to resume after reboot")
                    if not self.machine.wait_for_process_to_exit('Setup', 14400, 600):
                        raise Exception(f"Scheduled Task Failed with return code {output.output}")
                elif output.output.strip() != '0':
                    raise Exception(f"Scheduled Task Failed with return code {output.output}")
                else:
                    self.log.info("Scheduled Task Complete")
            else:
                self.log.info("Waiting 3 minutes for installation process to start.")
                time.sleep(180)
                if self.machine.is_process_running("Setup", time_out=180, poll_interval=15):
                    if self.machine.wait_for_process_to_exit("Setup"):
                        self.log.info("Installation process has completed.")
                    else:
                        raise Exception("Installation process never started. Failing out.")

        except Exception as exp:
            raise Exception('Failed to execute task') from exp
        finally:
            self.machine.delete_task("\"" + task_name + "\"")

    def install_custom_package(self, full_package_path=None, username=None, password=None, authcode=None, **kwargs):
        """
                To install custom package on the remote client machine

                Args:
                    full_package_path         (str)   -- Full package path of seed package in Controller

                    username                (str)   -- Username to authenticate client

                    password                (str)   -- Password to authenticate client

                    authcode                (str)   -- Authcode to authenticate client

                Keyword Args:
                    silent_install          (bool)  -- Boolean value whether to install silently

        """
        custom_package_flag = kwargs.get("custom_package_flag", False)
        silent_install = kwargs.get("silent_install", False)
        plan_name = kwargs.get("plan_name", None)
        # Input Json
        if not custom_package_flag:
            input_json = kwargs.get("input_json", {
                "commcellUser": username,
                "commcellPassword": password,
                "SelectedPackages": [1],
                "OEMID": kwargs.get(self.OEMId, "1"),
            })
            if authcode:
                input_json["authcode"] = authcode
        else:
            with open(f'{AUTOMATION_DIRECTORY}\\CustomPackageInput.json', 'r') as file:
                data = file.read()

            # parse file
            input_json = json.loads(data)

        # To initialize options selector class
        self.options_selector = OptionsSelector(self.commcell)

        # To select drive with enough space
        self.log.info('Selecting drive on the machine based on space available')
        drive = self.options_selector.get_drive(self.machine, size=50)
        if drive is None:
            raise Exception(f"Installation cancelled, Insufficient space on machine {self.machine.machine_name}")
        self.log.info('selected drive: %s', drive)

        # Directory to copy the batch file, installer and interactive install exe
        dir_name = kwargs.get("dir_name", 'metallic_install')
        self.install_directory = self.machine.join_path(drive, dir_name)

        # To create log directory on the machine
        if not self.machine.check_directory_exists(self.log_directory):
            self.machine.create_directory(self.log_directory)
            self.log.info('Successfully created log directory in path "%s"', self.log_directory)

        # To remove install directory if exists
        if self.machine.check_directory_exists(self.install_directory):
            self.machine.remove_directory(self.install_directory)
            self.log.info('Successfully removed directory %s', self.install_directory)

        # To create install directory on the machine
        self.machine.create_directory(self.install_directory)
        self.log.info('Successfully created install directory in path "%s"', self.install_directory)

        # Interactive install exe to perform install interactively
        exe_file = rf'{AUTOMATION_DIRECTORY}\CompiledBins\InteractiveInstall.exe'

        # To copy the exe file
        self.copy_media_to_client(exe_file, self.install_directory)

        # To generate the user input json
        user_input = rf'{AUTOMATION_DIRECTORY}\UserInput.json'
        with open(user_input, 'w') as file:
            file.write(json.dumps(input_json))

        # To copy the user input json
        self.copy_media_to_client(user_input, self.install_directory)

        # Seed package directory
        seed_package_folder = rf'{self.install_directory}\seed_package'

        # To copy the seed package
        if not custom_package_flag:
            self.copy_media_to_client(full_package_path, seed_package_folder)
            pkg_name = full_package_path.split("\\")[-1]
            seed_package = rf'{seed_package_folder}\{pkg_name}'
            batch_file = rf'{self.install_directory}\install.bat'
            user_input = rf'{self.install_directory}\UserInput.json'

            if not silent_install:
                install_exe = rf'{self.install_directory}\InteractiveInstall.exe'
                installer_path = rf'{self.install_directory}\installer'
                setup_exe = rf'{installer_path}\Setup.exe'

                self.log.info('Extracting the installer')
                extract_command = rf'''"{seed_package}" /d "{installer_path}" /silent /noinstall'''
                output = self.machine.execute_command(rf'''cmd.exe /c "{extract_command}"''')
                if output.exception:
                    raise Exception(f'Installer extraction failed with error: {output.exception}')
                self.log.info('Successfully extracted the installer to %s', installer_path)

        else:
            self.id = kwargs.get("self.id")
            batch_file = rf'{self.install_directory}\install.bat'
            install_exe = rf'{self.install_directory}\InteractiveInstall.exe'
            user_input = rf'{self.install_directory}\UserInput.json'
            setup_exe = f"C:\\AUTOMATION_LOC\\{self.id}\\WinX64\\Setup.exe"

        # To generate the installation.bat file
        if not silent_install:
            command = rf'''"{install_exe}" -PATH "{setup_exe}" -PLAY "{user_input}"
                          set errorCode = %ERRORLEVEL%
                          EXIT %errorCode%
                          '''
        else:
            command = rf'''"{seed_package}" /silent /install /authcode "{authcode}" /plan "{plan_name}"
                set errorCode = %ERRORLEVEL%
                EXIT %errorCode%'''

        if not self.machine.create_file(batch_file, command):
            raise Exception('Batch file creation failed')

        self.log.info('Install logs are written to InteractiveInstall.log inside %s on the client machine',
                      self.log_directory)
        self.log.info('Custom Package installation started')
        self.execute_command(command=f'"{batch_file}"', interactive=not silent_install)

        if self.machine.check_registry_exists("Session", "nCVDPORT"):
            self.log.info('Custom Package installation successful')
        else:
            raise Exception('Custom Package install failed !!')

        # To remove install directory on the machine
        try:
            self.machine.remove_directory(self.install_directory)
            self.log.info('Successfully deleted install directory in path "%s"', self.install_directory)
        except Exception as exp:
            self.log.info("Failed to clean up the directory")


class UnixInstallCustomPackage(InstallCustomPackage):
    """Class for performing Custom Package Install operations on a Unix client."""

    def __init__(self, commcell, remote_machine_credentials, remote_client_os_name):
        """
                Initialize the UnixInstallCustomPackage object

                Args:
                    commcell (obj)                        -- commcell object

                    remote_machine_credentials (dict)     --  Inputs for Installation should be in a dictionary

                        Supported key / value for inputs:

                        Mandatory:

                            remote_clientname        (str)   -- Clientname of remote machine

                            remote_username          (str)   -- Username to connect to client machine(Domain\\Username)

                            remote_userpassword      (str)   -- Password to to connect to client machine

                    remote_client_os_name:                --  OS type of remote client

        """
        super().__init__(commcell, remote_machine_credentials, remote_client_os_name)
        self.install_directory = None
        self.domain = None
        self.client_auth_tag = None
        self.user_login_tag = None

    def install_custom_package(self, full_package_path=None, username=None, password=None, authcode=None, **kwargs):
        """
                To install custom package on the remote client machine

                Args:
                    full_package_path         (str)   -- Full package path of seed package in Controller

                    username                (str)   -- Username to authenticate client

                    password                (str)   -- Encrypted password to authenticate client

                    authcode                (str)   -- Authcode to authenticate client

        """
        # To initialize options selector class
        self.options_selector = OptionsSelector(self.commcell)

        # To select drive with enough space
        self.log.info('Selecting drive on the machine based on space available')
        drive = self.options_selector.get_drive(self.machine, size=50)
        if drive is None:
            raise Exception(f"Installation cancelled, Insufficient space on machine {self.machine.machine_name}")
        self.log.info('selected drive: %s', drive)

        # Directory to copy the tar file
        self.install_directory = rf'{drive}metallic_install'

        # To remove install directory if exists
        if self.machine.check_directory_exists(self.install_directory):
            self.machine.remove_directory(self.install_directory)
            self.log.info('Successfully removed directory %s', self.install_directory)

        # To create install directory on the machine
        self.machine.create_directory(self.install_directory)
        self.log.info('Successfully created install directory in path "%s"', self.install_directory)

        # To remove seed folder if exists
        seed_folder = rf'{AUTOMATION_DIRECTORY}\SeedFolder'
        if self.local_machine.check_directory_exists(seed_folder):
            self.local_machine.remove_directory(seed_folder)
            self.log.info('Successfully removed already existing tar directory %s', seed_folder)

        self.log.info('Extracting the tar file')
        seed_tar = tarfile.open(full_package_path)
        seed_tar.extractall(seed_folder)
        pkg = os.listdir(seed_folder)[0]
        remote_path = '/pkg/'
        if not pkg == 'pkg':
            remote_path = rf'/{pkg}/pkg/'
            pkg += '\\pkg'
        self.log.info('Extracted the tar file to %s', seed_folder)

        if '\\' in username:
            self.domain = username.split('\\')[0]
            username = username.split('\\')[1]

        tree = ET.parse(rf'{seed_folder}\{pkg}\default.xml')
        root = tree.getroot()
        self.client_auth_tag = root.find('ClientAuthentication')
        if self.client_auth_tag is None:
            self.client_auth_tag = ET.SubElement(root, 'ClientAuthentication')
            self.user_login_tag = ET.SubElement(self.client_auth_tag, 'userAccountToLogin')
            if self.domain:
                self.user_login_tag.set('domainName', self.domain)
            self.user_login_tag.set('password', password)
            self.user_login_tag.set('userName', username)

        else:
            if self.domain:
                self.client_auth_tag.find('userAccountToLogin').set('domainName', self.domain)
            if password:
                self.client_auth_tag.find('userAccountToLogin').set('password', password)
            if username:
                self.client_auth_tag.find('userAccountToLogin').set('userName', username)
        if authcode:
            root.find('organizationProperties').set('authCode', authcode)
        tree.write(f'{seed_folder}\\{pkg}/new_default.xml')
        self.log.info('Successfully edited the xml file')

        # Copy seed package to client
        self.log.info('Copying Seed Package to client machine')
        self.copy_media_to_client(full_package_path, self.install_directory)

        self.log.info('Extracting tar file in remote client')
        tar_name = full_package_path.split("\\")[-1]
        output = self.machine.execute_command(f'cd {self.install_directory} && tar -xvf {tar_name}')

        if not output.exit_code == 0:
            self.log.error("Tar file Extraction Failed")
            raise Exception("Failed to extracted the tar file: %s" % output.formatted_output)
        self.log.info('Successfully extracted the tar file on the client machine')

        # Copy xml file to client
        self.log.info('Copying XML file to client machine')
        xml_path = rf'{seed_folder}\{pkg}\new_default.xml'
        self.copy_media_to_client(xml_path, self.install_directory + remote_path)

        self.log.info('Setting Folder permissions')
        output = self.machine.execute_command("chmod -R 0775 " + self.install_directory)

        if not output.exit_code == 0:
            self.log.error("Setting Folder permissions Failed")
            raise Exception("Failed to Execute permission setting: %s" % output.formatted_output)
        self.log.info('Successfully set Folder permissions')

        self.log.info('Waiting for package to be installed on client')
        output = self.machine.execute_command(f'cd {self.install_directory + remote_path} '
                                              f'&& ./silent_install -p new_default.xml')

        if not output.exit_code == 0:
            self.log.error("Seed Package Installation Failed")
            raise Exception("Failed to install package: %s" % output.formatted_output)
        self.log.info('Successfully installed Package on client')

        # To remove install directory on the client machine
        self.machine.remove_directory(self.install_directory)
        self.log.info('Successfully deleted Installation directory in path "%s"', self.install_directory)

        # To remove seed folder on local machine
        self.local_machine.remove_directory(seed_folder)
        self.log.info('Successfully removed seed folder %s from local machine', seed_folder)
