# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------

"""
This module provides the Install related functions or operations that are common to FS 

RFsInstallHelper:

    silent_install_task():          -> Launch the silent install task on Windows machine

    get_silent_install_command()    -> Get the silent install command for the OS flavour

    silent_install_machine():       -> Trigger Silent Install of file server

"""

import time
from selenium.webdriver.common.by import By

class RFsInstallHelper:
    
    def __init__(self, admin_console):
        """
        Initializes RFsInstallHelper class
        Args:
            admin_console(AdminConsole): adminconsole object
        """
        self._admin_console = admin_console

    def silent_install_task(self, command, machine):
        """Launch the silent install task
            Args:
                command (str)       :          silent installer command

                machine (Machine()) :          Machine instance of the client machine
        """
        task_name = 'Silent Installation Schedule'
        systime = machine.add_minutes_to_system_time(3).strip()
        task_options = f"/tn \"{task_name}\" /tr \"{command}\" /sc daily /st {systime} " \
                       f"/rl HIGHEST  /it /f"
        if machine.password and machine.username:
            task_options = f"{task_options} /ru {machine.username} /rp {machine.password}"
        machine.create_task(task_options)
        self._admin_console.log.info("Silent Install Task created, sleeping for 3 minutes.")
        time.sleep(180)
        try:
            machine.wait_for_task(task_name, taskstatus="Ready", retry_interval=60)
            self._admin_console.log.info('Checking the return status of Task')
            ps_query = f"(schtasks /query /FO LIST /V /TN \"{task_name}\"  | findstr \"Result\").substring(12).trim()"
            output = machine.execute_command(ps_query)
            if output.output.strip() == '5':
                self._admin_console.log.info("Machine requires a reboot. Installer will resume after reboot")
                _res = machine.reboot_client()
                time.sleep(600)
                self._admin_console.log.info("Waiting for Installer to resume after reboot")
                if not machine.wait_for_process_to_exit('Setup', 14400, 600):
                    raise Exception(f"Scheduled Task Failed with return code {output.output}")
            elif output.output.strip() != '0':
                raise Exception(f"Scheduled Task Failed with return code {output.output}")
            else:
                self._admin_console.log.info("Scheduled Task Complete")
        except Exception as exp:
            raise Exception('Failed to execute task') from exp
        finally:
            machine.delete_task("\"" + task_name + "\"")
        
    def get_silent_install_command(self, cmd_txt):
        """get the silent install command for the OS flavour
            Args:
                cmd_txt (str):      String representing corresponding OS installer
        """
        return self._admin_console.driver.find_element(
            By.XPATH, f"//p[contains(text(), '{cmd_txt}')]").text

    def silent_install_machine(self, installinputs, **kwargs):
        """Trigger Silent Install of file server
            Args:
                installinputs {}:          install inputs dict
        """
        from AutomationUtils.machine import Machine
        from AutomationUtils.options_selector import OptionsSelector
        from Install.installer_constants import REMOTE_FILE_COPY_LOC
        log_directory = REMOTE_FILE_COPY_LOC
        remote_machine_obj = Machine(installinputs.get("remote_clientname"),
                              username=installinputs.get("remote_username"),
                              password=installinputs.get("remote_userpassword"))

        drive = OptionsSelector.get_drive(remote_machine_obj, size=50)
        dir_name = kwargs.get("dir_name", "metallic_install")
        install_directory = remote_machine_obj.join_path(drive, dir_name)

        # To create log directory on the machine
        if not remote_machine_obj.check_directory_exists(log_directory):
            remote_machine_obj.create_directory(log_directory)
            self._admin_console.log.info('Successfully created log directory in path "%s"', log_directory)

        # To remove install directory if exists
        if remote_machine_obj.check_directory_exists(install_directory):
            remote_machine_obj.remove_directory(install_directory)
            self._admin_console.log.info('Successfully removed directory %s', install_directory)

        # To create install directory on the machine
        remote_machine_obj.create_directory(install_directory)
        self._admin_console.log.info('Successfully created install directory in path "%s"', install_directory)

        cmd_text = "./silent_install"
        if "windows (32-bit)" in installinputs['os_type'].lower():
            cmd_text = "WindowsFileServer32.exe"
        elif "windows" in installinputs['os_type'].lower():
            cmd_text = "WindowsFileServer64.exe"
        silent_command = self.get_silent_install_command(cmd_text)

        media_path = installinputs.get('full_package_path')
        remote_machine_obj.copy_from_local(media_path, install_directory)

        if "windows" not in installinputs['os_type'].lower():
            tar_name = media_path.split("\\")[-1]
            output = remote_machine_obj.execute_command(f'cd {install_directory} && tar -xvf {tar_name}')

            if (not output.exit_code == 0) and (installinputs.get('os_type') not in ['aix', 'hp-ux', 'solaris', 'powerpc']):
                self._admin_console.log.error("Tar file Extraction Failed")
                raise Exception("Failed to extracted the tar file: %s" % output.formatted_output)
            self._admin_console.log.info('Successfully extracted the tar file on the client machine')

            extracted_package = install_directory.rstrip('/') + '/' + tar_name.split(".")[0] + '/pkg'
            output = remote_machine_obj.execute_command(f'cd {extracted_package} && {silent_command}')

        else:
            silent_command = rf'''cmd.exe /c "{install_directory}\{silent_command}"'''
            self._admin_console.log.info(f"Silent Install command to execute: {silent_command}")
            batch_file = rf'{install_directory}\install.bat'
            if not remote_machine_obj.create_file(batch_file, silent_command):
                raise Exception('Batch file creation failed')

            self.silent_install_task(command=f'"{batch_file}"', machine=remote_machine_obj)

        self._admin_console.log.info('Successfully executed the silent installer command, sleeping for 5 minutes')
        time.sleep(300)
        if remote_machine_obj.check_registry_exists("Session", "nCVDPORT"):
            self._admin_console.log.info('Custom Package installation successful')
        else:
            raise Exception('Custom Package install failed !!')

        # To remove install directory on the machine
        try:
            remote_machine_obj.remove_directory(install_directory)
            self._admin_console.log.info('Successfully deleted install directory in path "%s"', install_directory)
        except Exception as exp:
            self._admin_console.log.info("Failed to clean up the directory")
