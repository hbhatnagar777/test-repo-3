# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations for silent install

SilentinstallHelper
===================

    __init__()                          --  initialize instance of the silent install class
    silent_install                      --  Main module for fresh silent installation
    get_commands_to_remote_execute      --  Commands to execute on the remote machine for silent installation
    download_file_from_http_server      --  This method is used to download configuration xml files from server.

    _get_packages_to_install            --  Dictionary of packages(packages id : package name) to be installed
    _get_hard_dependent_packages        --  Get the hard depenedent packages for selected package
    _get_soft_dependent_packages        --  Get the list of soft dependent packages for any package
    _get_pkg_displayname                --  Frame dictionary of names of hard and soft depenedent package
"""
import os
import time
from AutomationUtils import config, logger, constants
from AutomationUtils.machine import Machine
from Install import installer_constants, installer_utils
from Install.bootstrapper_helper import BootstrapperHelper
from Install.install_xml_helper import InstallXMLGenerator
from cvpysdk.deployment.deploymentconstants import OSNameIDMapping


class SilentInstallHelper:

    @staticmethod
    def create_installer_object(client_name, feature_release, machine_obj, inputs):
        """Returns the instance of one of the Subclasses WindowsInstallation /
        DebianInstallation based on the OS details of the remote client.

        """

        if machine_obj.os_info.upper() == 'WINDOWS':
            obj = WindowsInstallation(client_name, feature_release, machine_obj, inputs)
        else:
            obj = DebianInstallation(client_name, feature_release, machine_obj, inputs)

        return obj

    def __init__(self, client_name, feature_release, machine_obj, inputs):
        """
            Initialize instance of the SilentInstallHelper class.
                Args:
                    client_name -- Client Name provided for installation

                    feature_release -- feature release of the bootstrapper

                    machine_obj -- machine object

                    inputs (dict)
                    --  Inputs for Installation should be in a dictionary
                            Supported key / value for inputs:

                            Mandatory:
                                csClientName        (str)        Commserve Client Name
                                csHostname          (str)        Commserve Hostname

                                Windows Client
                                commservePassword   (str)        Commserve password - Encoded (v3 Encoded Password)

                                Unix Client
                                commservePassword   (str)        Commserve Password without Encoding/Encrypting
                                (OR)
                                authCode            (str)        AuthCode provided for the particular user/company

                            Optional:
                                revetsnap           (bool)       Specifies whether silent install on snap reverted vm or not
                                machineobj          (obj)        Machine class object for snap reverted vm
                                commserveUsername   (str)        Commserve Username
                                useExistingDump     (str)        Use existing dump for Dm2/Workflow Engine ("0" or "1")
                                useExsitingCSdump   (str)        Use CS dump ("0" or "1")
                                CommservDumpPath    (str)        Dump path for Commserve
                                install32base       (str)        install 32bit software on 64bit Machine ("0" or "1")
                                restoreOnlyAgents   (str)       "0 or "1"
                                DM2DumpPath         (str)        Dump path for DM2 webservice
                                WFEngineDumpPath    (str)        Dump path for Workflow Engine
                                decoupledInstall    (str)        "0 or "1"
                                enableFirewallConfig (str)       "0 or "1"
                                firewallConnectionType (str)     "0" or "1" or "2"
                                httpProxyConfigurationType(str)  "0" or "1" or "2"
                                httpProxyPortNumber (str)        Port Number eg: "6256"
                                httpProxyHostName   (str)        Hostname of the proxy machine
                                portNumber          (str)        Port number to connect to the CVD eg:8410
                                enableProxyClient   (str)        Enable Client as a proxy "0" or "1"
                                proxyClientName     (str)        Proxy Client Name / Client Name on the commcell
                                proxyHostname       (str)        Proxy Client Hostname
                                proxyPortNumber     (str)        Proxy client Port Number to be used
                                sqlSaPassword       (str)        Sa (user) password for SQL access
                                installDirectoryUnix(str)        Path on which software to be installed on Unix Client
                                installDirectoryWindows(str)     Path on which software to be installed on Win Client
                                clientGroupName     (str)        Client Group on the CS
                                networkGateway      (str)        Network Gateway flag - client uses to connect to CS
                                mediaPath           (str)        Filer Path required for Windows/Unix installations
                                                                 (Path till CVMedia)
                                oem_id              (int)        OEM ID to used for Installation (Metallic/Commvault)
                                cmdline_args        (dict)       Command line arguments to be passed for silent install

            Note:
                Unix Installation Requires Filer Path/ Media Path ( Path till CVMedia) -- mediaPath
        """
        self.inputs = inputs
        self.log = logger.get_log()
        self.config_json = config.get_config()
        self.machine_obj = machine_obj
        self.local_machine = Machine()
        self.bootstrapper_obj = None
        self.remote_media_path = None
        self.client_name = client_name
        self.test_results_path = constants.TEMP_DIR
        self.os_type = None
        self.remote_dir = installer_constants.REMOTE_FILE_COPY_LOC
        self.xml_helper = InstallXMLGenerator(client_name, self.machine_obj, inputs)
        self.instance = inputs.get("instance", "Instance001")
        self.oem_id = inputs.get('oem_id', 1)
        self.bootstrapper_installation = inputs.get('mediaPath') is None
        self.feature_release = feature_release if '_' in feature_release \
            else installer_utils.get_latest_recut_from_xml(feature_release)

    def silent_install(self, packages_list, is_revert=False):
        """
            Installs the client on the remote machine depending on the feature release using bootstrapper.
            :arg
                packages_list (list of package id)   -- list of features to be installed
                                                        eg: packages_list=[1, 51, 702] for Windows
                                                        eg: packages_list=[1002, 1101] for Unix
                is_revert   (bool)   -- specifies whether vm used is reverted snap or not
        """
        raise NotImplementedError("Module not implemented for the class")

    def get_commands_to_remote_execute(self, media_path):
        """
            Commands to be executed on the remote Machine
        :param
            media_path: Path of the Media on remote machine (Path where Setup.exe / silent_install is Present)
        :return:
            bat file that has all the list of commands
        """
        raise Exception("Method not implemented for this Class")


class WindowsInstallation(SilentInstallHelper):
    """Class for performing Install operations on a Windows client."""

    def __init__(self, client_name, feature_release, machine_obj, inputs):
        """
            Args:
                    client_name -- Client Name provided for installation

                    feature_release -- feature release of the bootstrapper

                    machine_obj -- machine object

                    inputs (dict) --  Inputs for Installation should be in a dictionary

            Note:
                Unix Installation Requires Filer Path/ Media Path (Path till CVMedia) -- mediaPath

        """
        super(WindowsInstallation, self).__init__(client_name, feature_release, machine_obj, inputs)
        self.os_type = OSNameIDMapping.WINDOWS_64.value

    def create_task_and_execute(self, exec_bat_file, task_name="Install", is_revert=False):
        """
        This method can be used to create a task on remote machine in Task Scheduler and execute it.
        Args:
            exec_bat_file: (str) Batch file to be triggered on Remote machine
            task_name:  (str) Name of the task to be created in task scheduler
            is_revert:  (bool)  Specifies whether vm used is reverted snap or not

        Returns: None

        """
        systime = self.machine_obj.add_minutes_to_system_time(3).strip()
        task_options = f"/tn \"{task_name}\" /tr \"{exec_bat_file}\" /sc daily /st {systime} " \
                       f"/rl HIGHEST /f"
        if self.machine_obj.password and self.machine_obj.username:
            task_options = f"{task_options} /ru {self.machine_obj.username} /rp {self.machine_obj.password}"
        self.machine_obj.create_task(task_options)
        try:
            _interval = 60
            if is_revert:
                _interval = 1
            self.machine_obj.wait_for_task(task_name, taskstatus="Running", retry_interval=_interval)
            self.machine_obj.wait_for_task(task_name, retry_interval=240, time_limit=300)
            self.log.info('Checking the return status of Task')
            ps_query = f"(schtasks /query /FO LIST /V /TN \"{task_name}\"  | findstr \"Result\").substring(12).trim()"
            output = self.machine_obj.execute_command(ps_query)
            if output.output.strip() == '5':
                self.log.info("Machine requires a reboot. Installer will resume after reboot")
                _res = self.machine_obj.reboot_client()
                time.sleep(600)
                self.log.info("Waiting for Installer to resume after reboot")
                if not self.machine_obj.wait_for_process_to_exit('Setup', 14400, 600):
                    raise Exception(f"Scheduled Task Failed with return code {output.output}")
            elif output.output.strip() != '0':
                raise Exception(f"Scheduled Task Failed with return code {output.output}")
            else:
                self.log.info("Scheduled Task Complete")
        except Exception as exp:
            raise Exception('Failed to execute task') from exp
        finally:
            self.machine_obj.delete_task("\"" + task_name + "\"")

    def silent_install(self, packages_list, is_revert=False):
        """
            Installs the client on the remote machine depending on the feature release using bootstrapper.
            Args:
            packages_list (list of package id)   -- list of features to be installed eg: packages_list=[1, 51, 702]
                                                        for Window
            is_revert   (bool)   -- specifies whether vm used is reverted snap or not
        """
        _current = None
        _drive_letter = ''
        try:
            if not self.bootstrapper_installation:
                media_path = self.inputs.get("mediaPath")
                if media_path[:2] == r'\\':
                    _drive_letter = self.machine_obj.mount_network_path(
                        media_path, self.config_json.Install.dvd_username, self.config_json.Install.dvd_password) + ':'
                self.remote_media_path = media_path
            else:
                # Windows use Bootstrapper to Install the packages
                self.bootstrapper_obj = BootstrapperHelper(self.feature_release, self.machine_obj, oem_id=self.oem_id)
                self.bootstrapper_obj.extract_bootstrapper()
                self.remote_media_path = self.bootstrapper_obj.remote_drive + \
                                         installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH
            packages_to_be_installed = installer_utils.get_packages_to_install(packages_list, self.os_type,
                                                                               self.feature_release)
            self.log.info("Packages to be installed on the remote machine : %s" % str(packages_to_be_installed))
            root = self.xml_helper.silent_install_xml(packages_to_be_installed)
            xml_path = self.xml_helper.write_xml_to_file(root, "silent_install_windows.xml")
            install_batch_file = self.get_commands_to_remote_execute(self.remote_media_path, drive_letter=_drive_letter)
            self.log.info("Copying file [{0}] on Client [{1}] at [{2}]"
                          "".format(install_batch_file, self.machine_obj.machine_name, self.remote_dir))

            # Copying batch file and the XML on the remote machine
            self.machine_obj.copy_from_local(install_batch_file, self.remote_dir)
            self.machine_obj.copy_from_local(xml_path, self.remote_dir)
            exec_bat_file = os.path.join(self.remote_dir, os.path.basename(install_batch_file))
            task_name = 'Silent Installation Schedule'
            if is_revert and 'machineobj' in self.inputs:
                _current = self.machine_obj
                self.machine_obj = self.inputs['machineobj']
                self.log.info('Changing machine object with credential instead of client')
                self.inputs.pop('machineobj')
                self.inputs.pop('revertsnap')
            self.create_task_and_execute(exec_bat_file, task_name, is_revert)
            if _current:
                self.machine_obj = _current
                self.log.info('Reverting Changed machine object')

        except Exception as err:
            self.log.exception(str(err))
            raise Exception(f"Silent Installation Failed for the machine {self.machine_obj.machine_name}")
        finally:
            if _drive_letter != '':
                self.machine_obj.execute_command(f"net use /delete {_drive_letter}")

    def silent_upgrade(self):
        """
            Upgrades the client on the remote machine depending on the feature release using bootstrapper.
            Args: None

        """
        _drive_letter = ''
        try:
            if self.bootstrapper_installation:
                # Use Bootstrapper to Upgrade the client.
                self.bootstrapper_obj = BootstrapperHelper(self.feature_release, self.machine_obj, oem_id=self.oem_id)
                self.bootstrapper_obj.extract_bootstrapper()
                self.remote_media_path = self.bootstrapper_obj.remote_drive + \
                                         installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH
            else:
                media_path = self.inputs.get("mediaPath")
                if media_path[:2] == r'\\':
                    _drive_letter = self.machine_obj.mount_network_path(
                        media_path, self.config_json.Install.dvd_username, self.config_json.Install.dvd_password) + ':'
                self.remote_media_path = media_path
            install_batch_file = self.get_commands_to_remote_execute(
                self.remote_media_path, upgrade=True, drive_letter=_drive_letter)
            self.log.info("Copying file [{0}] on Client [{1}] at [{2}]"
                          "".format(install_batch_file, self.machine_obj.machine_name, self.remote_dir))

            # Copying batch file and the XML on the remote machine
            self.machine_obj.copy_from_local(install_batch_file, self.remote_dir)
            exec_bat_file = os.path.join(self.remote_dir, os.path.basename(install_batch_file))

            task_name = 'Upgrade Installation Schedule'
            self.create_task_and_execute(exec_bat_file, task_name=task_name)

        except Exception as err:
            self.log.exception(str(err))
            raise Exception(f"Silent Upgrade Failed for the machine {self.machine_obj.machine_name}")
        finally:
            if _drive_letter != '':
                self.machine_obj.execute_command(f"net use /delete {_drive_letter}")

    def get_commands_to_remote_execute(self, media_path, upgrade=False, drive_letter=''):
        """
            Commands to be executed on the remote Machine
        :param
            media_path: Path of the Media on remote machine (Path where Setup.exe / silent_install is Present)
        :return:
            bat file that has all the list of commands
        """
        try:
            cmd_list = []
            cmdline_args_string = ""
            if self.inputs.get("cmdline_args"):
                commands = []
                cmdline_args = self.inputs.get("cmdline_args")
                for cmd in cmdline_args:
                    if not cmdline_args[cmd]:
                        commands.append(" /" + cmd)
                    else:
                        commands.append(" /" + cmd + " " + cmdline_args[cmd])
                cmdline_args_string = ''.join(commands) + " "

            if not self.bootstrapper_installation:
                _pass = '%%'.join(self.config_json.Install.dvd_password.split('%'))
                cmd_list.append(f'net use {drive_letter} /delete')
                cmd_list.append(f'net use {drive_letter} "{media_path}" {_pass} /USER:'
                                f'{self.config_json.Install.dvd_username}')
                media_path = drive_letter
            if not upgrade:
                cmd_list.append(media_path + f"\\Setup.exe /silent /install /resume /play \"" +
                                installer_constants.REMOTE_FILE_COPY_LOC +
                                "\\silent_install_windows.xml\"" +
                                f"{cmdline_args_string}" +
                                " >> " + installer_utils.get_batch_output_file())
            else:
                cmd_list.append(media_path + f"\\Setup.exe /wait /upgrade /silent /resume /ForceReboot "
                                             f"{cmdline_args_string} " +
                                " >> " + installer_utils.get_batch_output_file())

            cmd_list.append("set exitcode=%ERRORLEVEL%" + ">> " + installer_utils.get_batch_output_file())
            cmd_list.append("EXIT %exitcode%" + ">> " + installer_utils.get_batch_output_file())
            install_batch_file = installer_utils.create_batch_file_for_remote(cmd_list, file_name="silent_install.bat")
            return install_batch_file

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in creating a Batch file")


class DebianInstallation(SilentInstallHelper):
    """Class for performing Install operations on a debian/Mac client."""

    def __init__(self, client_name, feature_release, machine_obj, inputs):
        """
        Args:
                    client_name -- Client Name provided for installation

                    feature_release -- feature release of the bootstrapper

                    machine_obj -- machine object

                    inputs (dict) --  Inputs for Installation should be in a dictionary

            Note:
                Unix Installation Requires Filer Path/ Media Path ( Path till CVMedia) -- mediaPath

        """
        super(DebianInstallation, self).__init__(client_name, feature_release, machine_obj, inputs)
        self.os_type = OSNameIDMapping.UNIX_LINUX64.value

    def silent_install(self, packages_list, is_revert=False):
        """
            Installs the client on the remote machine depending on the feature release using bootstrapper.
            :arg
                packages_list (list of package id)   -- list of features to be installed
                                                        eg: packages_list=[1, 51, 702] for Windows
                                                        eg: packages_list=[1002, 1101] for Unix
                is_revert   (bool)   -- specifies whether vm used is reverted snap or not
        """
        _current = None
        try:
            self.remote_dir = installer_constants.UNIX_REMOTE_FILE_COPY_LOC
            if self.inputs.get("mediaPath"):
                _media_path_lower = self.inputs.get("mediaPath").lower()
                self.remote_media_path = self.inputs.get("mediaPath")
                base_name = os.path.basename(os.path.normpath(_media_path_lower))
                if 'unix' not in base_name:
                    self.remote_media_path = os.path.join(self.inputs.get("mediaPath"), "Unix")
                self.remote_media_path = self.remote_media_path.replace("\\", "/")
            else:
                self.bootstrapper_obj = BootstrapperHelper(self.feature_release, self.machine_obj, oem_id=self.oem_id)
                self.bootstrapper_obj.extract_bootstrapper()
                self.remote_media_path = installer_constants.UNIX_DEFAULT_DRIVE_LETTER + \
                                         installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH
            packages_to_be_installed = installer_utils.get_packages_to_install(packages_list, self.os_type,
                                                                               self.feature_release)
            self.log.info("Packages to be installed on the remote machine : %s" % str(packages_to_be_installed))
            root = self.xml_helper.silent_install_xml(packages_to_be_installed)
            # dict = installer_utils.etree_to_dict(root)
            xml_path = self.xml_helper.write_xml_to_file(root, "silent_install_unix.xml")
            install_command = self.get_commands_to_remote_execute(self.remote_media_path)

            self.machine_obj.copy_from_local(xml_path, self.remote_dir)
            self.log.info("Executing command [{0}] on client [{1}]".format(install_command,
                                                                           self.machine_obj.machine_name))
            if is_revert and 'machineobj' in self.inputs:
                _current = self.machine_obj
                self.machine_obj = self.inputs['machineobj']
                self.log.info('Changing machine object with credential instead of client')
                self.inputs.pop('machineobj')
                self.inputs.pop('revertsnap')
            return_code = self.machine_obj.execute_command(install_command)
            if _current:
                self.machine_obj = _current
                self.log.info('Reverting Changed machine object')
            if not return_code.exit_code == 0:
                self.log.error("Silent Installation Failed")
                raise Exception("Installation Failure Reason: %s" % return_code.formatted_output)

            self.log.info("Silent Installation Successful for the machine")

        except Exception as err:
            self.log.exception(str(err))
            raise Exception(f"Silent Installation Failed of the machine {self.machine_obj.machine_name}")

    def silent_upgrade(self):
        """
            Performs a service Pack Upgrade on the remote machine depending on the feature release using bootstrapper.
        """
        try:
            self.remote_dir = installer_constants.UNIX_REMOTE_FILE_COPY_LOC
            if self.inputs.get("mediaPath"):
                _media_path_lower = self.inputs.get("mediaPath").lower()
                base_name = os.path.basename(os.path.normpath(_media_path_lower))
                if 'unix' not in base_name:
                    self.remote_media_path = os.path.join(self.inputs.get("mediaPath"), "Unix")
                else:
                    self.remote_media_path = self.inputs.get("mediaPath")
                self.remote_media_path = self.remote_media_path.replace("\\", "/")
            else:
                self.bootstrapper_obj = BootstrapperHelper(self.feature_release, self.machine_obj, oem_id=self.oem_id)
                self.bootstrapper_obj.extract_bootstrapper()
                self.remote_media_path = installer_constants.UNIX_DEFAULT_DRIVE_LETTER + \
                                         installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH
            install_command = self.get_commands_to_remote_execute(self.remote_media_path, upgrade=True)
            self.log.info("Executing command [{0}] on client [{1}]".format(install_command,
                                                                           self.machine_obj.machine_name))
            return_code = self.machine_obj.execute_command(install_command)
            if not return_code.exit_code == 0:
                self.log.error("Silent Upgrade Failed")
                raise Exception("Upgrade Failure Reason: %s" % return_code.formatted_output)

            self.log.info("Silent Upgrade is Successful on the machine")

        except Exception as err:
            self.log.exception(str(err))
            raise Exception(f"Silent Installation Failed of the machine {self.machine_obj.machine_name}")

    def silent_repair(self):
        try:
            self.remote_dir = installer_constants.UNIX_REMOTE_FILE_COPY_LOC
            if self.inputs.get("mediaPath"):
                _media_path_lower = self.inputs.get("mediaPath").lower()
                self.remote_media_path = self.inputs.get("mediaPath")
                base_name = os.path.basename(os.path.normpath(_media_path_lower))
                if 'unix' not in base_name:
                    self.remote_media_path = os.path.join(self.inputs.get("mediaPath"), "Unix")
                self.remote_media_path = self.remote_media_path.replace("\\", "/")
            else:
                self.bootstrapper_obj = BootstrapperHelper(self.feature_release, self.machine_obj, oem_id=self.oem_id)
                self.bootstrapper_obj.extract_bootstrapper()
                self.remote_media_path = installer_constants.UNIX_DEFAULT_DRIVE_LETTER + \
                                         installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH

            install_command = self.get_commands_to_remote_execute(self.remote_media_path, repair=True)

            self.log.info("Executing command [{0}] on client [{1}]".format(install_command,
                                                                           self.machine_obj.machine_name))

            return_code = self.machine_obj.execute_command(install_command)
            if not return_code.exit_code == 0:
                self.log.error("Silent Installation Failed")
                raise Exception("Installation Failure Reason: %s" % return_code.formatted_output)

            self.log.info("Silent Installation Successful for the machine")

        except Exception as err:
            self.log.exception(str(err))
            raise Exception(f"Silent Installation Failed of the machine {self.machine_obj.machine_name}")

    def get_commands_to_remote_execute(self, media_path, upgrade=False, repair=False):
        """
            Commands to be executed on the remote Machine
        :param
            media_path: Path of the Media on remote machine (Path where Setup.exe / silent_install is Present)
        :return:
            Install Commands for Remote Execute
        """
        try:
            cmdline_args_string = ""
            if self.inputs.get("cmdline_args"):
                commands = []
                cmdline_args = self.inputs.get("cmdline_args")
                for cmd in cmdline_args:
                    if not cmdline_args[cmd]:
                        commands.append("  -" + cmd)
                    else:
                        commands.append("  -" + cmd + " " + cmdline_args[cmd])
                cmdline_args_string = ''.join(commands) + " "

            if media_path[:2] == "//":
                mounted_path = installer_utils.mount_network_path(media_path, self.machine_obj, self)

                install_command = f"{mounted_path}/silent_install -p " + \
                                  installer_constants.UNIX_REMOTE_FILE_COPY_LOC + \
                                  "/silent_install_unix.xml" + cmdline_args_string
                if upgrade:
                    install_command = f"{mounted_path}/silent_install -upgrade " + self.instance \
                                      + cmdline_args_string

                if repair:
                    install_command = f"{mounted_path}/cvpkgadd -reinstall " + \
                                      "-instance Instance001"
                self.log.info(install_command)

            elif self.bootstrapper_installation:
                if upgrade:
                    cmdl = "-upgrade " + self.instance if upgrade \
                        else "-p " + installer_constants.UNIX_REMOTE_FILE_COPY_LOC + "/silent_install_unix.xml"
                elif repair:
                    cmdl = "-reinstall " + self.instance if repair \
                        else "-p " + installer_constants.UNIX_REMOTE_FILE_COPY_LOC + "/silent_install_unix.xml"
                else:
                    cmdl = "-p " + installer_constants.UNIX_REMOTE_FILE_COPY_LOC + "/silent_install_unix.xml"
                cmdl += cmdline_args_string
                install_command = self.bootstrapper_obj.launch_bootstrapper(media_path, cmdl)

            else:
                install_command = f"{media_path}/silent_install -p " + \
                                  installer_constants.UNIX_REMOTE_FILE_COPY_LOC + "/silent_install_unix.xml" \
                                  + cmdline_args_string
                if upgrade:
                    install_command = f"{media_path}/silent_install " + cmdline_args_string

                if repair:
                    install_command = f"{media_path}/cvpkgadd -reinstall " + self.instance + cmdline_args_string

            self.machine_obj.execute_command("chmod -R 0775 " + self.remote_dir)
            self.log.info(install_command)
            return install_command

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in getting the Commands for Installation")
