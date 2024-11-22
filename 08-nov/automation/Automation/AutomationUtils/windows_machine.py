# -*- coding: utf-8 -*-
# pylint: disable=W0221,W0108

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for performing operations on a machine / computer with Windows Operating System.

This file consists of a class named: Machine, which can connect to the remote machine,
using CVD, if it is a Commvault Client, or using PowerShell, otherwise.

The instance of this class can be used to perform various operations on a machine, like,

    # .  Check if a Directory Exists or not
    # .  Create a new Directory
    # .  Rename a File / Folder
    # .  Remove an existing Directory
    # .  Get the Size of a File / Folder
    # .  Check if a Registry exists or not
    # .  Add / Update a Registry Key / Value
    # .  Get the Value of a Registry Key
    # .  Delete a Registry Key / Value
    # .  Compare the contents of 2 Files / Folders


WindowsMachine
==============

    __init__()                      --  initialize object of the class

    _login_with_credentials()       --  creates PowerShell credentials object and stores in an XML

    _execute_with_credential()      --  execute a script on a remote client using its credentials

    _execute_with_cvd()             --  execute a script on a remote client using the CVD service

    _get_file_hash()                --  returns the hash value of specified file

    _get_folder_hash()              --  returns the set of file paths and hash values

    _execute_script()               --  executes a PowerShell script on the remote machine

    _read_local_file()              --  reads and returns the content of the file

    _copy_file_from_local()         --  copy the file from local machine to the remote machine

    _get_files_or_folders_in_path() --  returns the list of files / folders present at the given
    path based on the operation type given

    _get_client_ip()                -- gets the ip address of the machine

    reboot_client()                 --  Reboots the remote machine

    shutdown_client()                 -- shuts-down the host

    kill_process()                  --  Kills a process in the remote machine

    execute_command()               --  executes a PowerShell command on the remote machine

    check_directory_exists()        --  checks if a directory exists on a remote client or not

    is_file()                       --  Checks if the path is a file or not

    is_directory()                    --  Checks if the path is a directory or not

    check_file_exists()             --  checks if a file exists on a remote client or not

    create_directory()              --  creates a new directory on a remote client
    
    current_time()                  --  Returns current machine time in UTC TZ as a datetime object
    
    current_localtime()             --  returns current machine timezone as a datetime.timezone object

    rename_file_or_folder()         --  renames a file / folder on a remote client

    remove_directory()              --  removes a directory on a remote client

    modify_item_datetime()          --  Changes the last Access time and Modified time of files in unix and windows.
    Also changes creation time in windows.

    get_file_size()                 --  get the size of a file on a remote client

    get_folder_size()               --  get the size of a folder on a remote client

    get_file_stats_in_folder()      --  Gets the total size in bytes by summing up the individual file size for files
                                        present in the directories and subdirectories of the given folder_path

    get_storage_details()           --  gets the details of storage of the client

    get_disk_count()                --  returns the count of the disks on the machine

    get_mounted_disks()             --  Returns the list of mounted disks on the machine

    check_registry_exists()         --  check if a registry exists on a remote client or not

    get_registry_value()            --  get the value of a registry key from a remote client

    get_registry_entries_for_subkey ()      --  Retrieves all the registry entries under a given
    subkey value and/or find a particular subkey or entry.

    create_registry()               --  create a registry key / value on a remote client

    update_registry()               --  update the data of a registry value on a remote client

    remove_registry()               --  remove a registry key / value from a remote client

    mount_network_path()            --  mounts the network shared path to a drive on this machine

    copy_folder_to_network_share()  --  copies the folder from this machine to the network share

    copy_from_network_share()       --  copies the file/folder specified at network share
    to the local machine

    copy_folder()                   --  copies the files specified at a location to
    another location on same local machine

    unmount_drive()                 --  un mounts the drive connected to this machine

    unzip_zip_file()                --  unzip the zip files on the machine

    create_file()                   --  creates a file at the specified path on the remote client

    append_to_file()                --  Appends content to the file present at the specified path

    execute_exe()                   --  executes the exe at the given path on the machine

    copy_from_local()               --  copies the file / folder specified in the input from
    local machine to the remote machine

    get_acl_list()                 --  Gets the list of acl of items
                                       from the machine on a give path

    compare_acl()                  -- Compares the acl of source path with
                                      destination path and checks
                                      whether they are same

    get_file_attributes()           -- get file attributes

    is_stub()                        -- for onepass use, to verify it's tub

    read_file()                     --  returns the contents of the file present at the given path

    delete_file()                   --  deletes the file present at the given path

    change_folder_owner()           --  changes the ownership of the given directory

    create_current_timestamp_folder()   --  create a folder with the current timestamp as the
    folder name inside the given folder path

    get_latest_timestamp_file_or_folder()   --  get the recently created file / folder inside the
    given folder path

    generate_test_data()            --  generates test data at specified path on remote client

    modify_test_data()              --  modify the test data at the given path based on the given
    options

    get_test_data_info()            --  returns information about the items on the given path
    based on the given options

    get_items_list()                --  returns the list of items at the given path

    get_meta_list()                 --  returns the list of meta data of items from the machine
    on the given path

    compare_meta_data()             --  compare the meta data of 2 paths

    get_checksum_list()             --  returns the list of checksum of the files at the given path

    compare_checksum()              --  compares the checksum of 2 paths

    get_files_in_path()             --  returns the list of files present at the given path

    get_folders_in_path()           --  returns the list of folders present at the given path

    get_folder_or_file_names()      --  returns the list of files or folders in a given path

    number_of_items_in_folder()     --  Returns the count of number of items in a folder

    get_files_and_directory_path()  --  returns the list of files and its directory in a given path

    add_firewall_allow_port_rule()  --  adds the inbound rule for the given port number

    start_firewall()                --  turn on firewall services on the current client machine

    add_firewall_machine_exclusion()        --  adds given machine to firewall exclusion list

    remove_firewall_allow_port_rule()       --  removes the inbound rule for the given port number

    stop_firewall()                         --  turn off firewall service on the client machine

    remove_firewall_machine_exclusion()     --  removes given machine from firewall exclusion list

    disconnect()                            --  disconnects the session with the machine

    scan_directory()                --  Scans the directory and returns a list of items under it
    along with its properties

    set_logging_debug_level()       -- set debug log level for given CV service name

    set_logging_filesize_limit()    -- set filesize limit for given CV service name

    lock_file()                     -- Locks the file for a specified interval.

    delete_task()                   -- Deletes the specified task on the client

    wait_for_task()                 -- Wait for scheduled task to complete on client

    create_task()                   -- Create a scheduled task on the machine

    execute_task()                  --  Executes a scheduled task immediately on the machine

    has_active_session()            --  Checks if there is an active session on the machine for a user

    get_login_session_id()          --  Gets the session id for the logged in user

    logoff_session_id()             --  Logs off the user session id for the logged in user on client.

    get_process_id()                --  returns the process id for the given process name with or without command line

    get_process_stats()             --  Gets the process stats like Handle count, memory used, CPU usage, thread count

    get_process_dump()              --  Gets the process dump for the given process ID

    get_hardware_info()             --  returns the hardware specifications of this machine

    block_tcp_port()                --  blocks tcp port on machine for given time interval

    get_port_usage()                --  returns the netstat connection stats for the process or machine

    is_process_running()            --  Checks if the given process is running

    hide_path()                     -- Hides the specific path

    unhide_path()                     -- unhides the specific path

    wait_for_process_to_exit()      --  waits for a given process to exit

    change_system_time()            --  Changes the system time as per the offset seconds
    provided w.r.t to current system time

    lock_files()                    --  Locks  list of files for a specified interval.

    find_lines_in_file()            --  Search for lines in a file for the given words

   get_ace()                        --  To get ace of file/folder for particular user

   modify_ace()                     --  To add or remove ACE on file or folder

   execute_command_unc()            --  Execute command function for unc path

   windows_operation()              -- For execute windows operation

   get_log_file()                   -- Returns the contents of a log file.

   get_logs_for_job_from_file()     -- From a log file object only return those log lines for a particular job ID.

   get_cpu_usage()                 -- gets the cpu performance counters for the given process

    get_file_owner()               -- Get owner of given file

    get_system_time()               -- gets the system time in hours and minutes

    restart_iis()                  -- restarts iis on the machine

    add_minutes_to_system_time()    -- Adds specified number of minutes to current system time

    add_days_to_system_time() -- Adds specified number of days to current system time

    get_active_cluster_node()      --    gets active cluster node

    get_cluster_nodes()         --   Get all nodes of cluster both active and passive

    do_failover()               --   Run Cluster failover

    get_event_viewer_logs_message() -- Gets N newest event viewer log message bodies

    list_shares_on_network_path() -- gets the list of shares on a UNC path

    move_file()                     --  Moves a file item from source_path to destination_path

    get_vm_ip()                     --  To get ip address of a VM

    share_directory()               -- To share a directory using net share

    unshare_directory()             -- To unshare a directory

    get_share_name()                --  To get share name of directory if shared

    get_logs_after_time_t()         --  Returns logs from mentioned file after the given time_t

    restart_all_cv_services()         --  Start all Commvault services using username/password method since SDK cannot
    talk to the machine when services are down

    start_all_cv_services()            -- Start all Commvault services using username/password

    stop_all_cv_services()          --  Stops all Commvault services using username/password method

    get_api_response_locally()      --  Executes local get api call and returns response

    check_if_pattern_exists_in_log  --  Method to check if the given pattern exists in the log file or not

    clear_folder_content()          --  Recursively deletes files/folders in given folder path to make it empty

    run_cvdiskperf()                --  Executes cvdiskperf.exe tool and returns results

    run_cvping()                    --  Executes cvping on machine with provided inputs

    remove_additional_software()    -- Removes the software from client machine.

    copy_file_between_two_machines() -- Copy files between two machines using current machine as Aux

    set_all_disks_online()           -- Sets all the disks in the machine online

    change_inheritance()            --  Disables or enables inheritance on the folder

    copy_file_locally()              -- Copies file from one directory to another

    change_hostname()                -- Changes the hostname of the given windows machine

    add_to_domain()                  -- adds a given windows machine to domain

    disable_ipv6()                   -- disables IPv6 address for the machine

    get_hostname()                   -- Gets the hostname of the machine
    
    get_time_range_logs()           -- Retrieves log lines from a file within a specified time range

Attributes
----------

    **is_connected**        --  returns boolean specifying whether connection is alive or not

    **key**                 --  returns the base path of the Registry Key of Commvault Instance

    **instance**            --  returns the Commvault instance registry currently being interacted
    with

    **instance.setter**     --  set the value of the Commvault instance to interact with

    **tmp_dir**             --  returns the path of the **tmp** directory on the Machine where the
    temporary database files are stored

    **os_sep**              --  returns the path separator based on the OS of the Machine

    **ip_address**          --  returns IP address of the machine

"""

import re
import os
import socket
import subprocess
import sys
import threading
import time
import inspect
import datetime
import paramiko
import _thread
from . import logger
from .options_selector import OptionsSelector
from .constants import (
    ALGORITHM_LIST,
    COPY_FOLDER_THREADS,
    COPY_FOLDER,
    COPY_FILE,
    CREATE_DIRECTORY,
    CREATE_FILE,
    CREATE_FILE_WITHSIZE,
    CREDENTIALS,
    CV_TIME_RANGE_LOGS,
    DELETE_REGISTRY,
    DIRECTORY_EXISTS,
    EXECUTE_COMMAND,
    EXECUTE_EXE,
    FILE_OR_FOLDER_LIST,
    GET_HASH,
    GET_REG_VALUE,
    GET_SIZE,
    GET_SIZE_ONDISK,
    GET_FILE_ATTRIBUTES,
    LATEST_FILE_OR_FOLDER,
    MOUNT_NETWORK_PATH,
    UNMOUNT_NETWORK_PATH,
    REGISTRY_EXISTS,
    REMOVE_DIRECTORY,
    RENAME_ITEM,
    SET_REG_VALUE,
    SCAN_DIRECTORY,
    WINDOWS_ADD_DATA,
    WINDOWS_GENERATE_TEST_DATA_THREAD_COUNT,
    WINDOWS_GET_ASCII_VALUE_FOR_PATH,
    WINDOWS_GET_DATA,
    WINDOWS_MODIFY_DATA,
    WINDOWS_TMP_DIR,
    WINDOWS_DELIMITER,
    WINDOWS_GET_REGISTRY_ENTRY_FOR_SUBKEY,
    WINDOWS_PROBLEM_DATA,
    GET_LOCK,
    DO_CLUSTER_FAILOVER,
    WINDOWS_OPERATION,
    EXECUTE_COMMAND_UNC,
    WINDOWS_GET_PROCESS_STATS,
    WINDOWS_GET_PROCESS_DUMP,
    DO_CLUSTER_GROUP_FAILOVER, BLOCK_PORT
)

from .machine import Machine
from .output_formatter import WindowsOutput
from .script_generator import ScriptGenerator


class WindowsMachine(Machine):
    """Class for performing operations on a Windows OS remote client."""

    def __init__(self, machine_name=None, commcell_object=None, username=None, password=None, **kwargs):
        """Initializes instance of the Machine class.

        Args:
            machine_name        (str)       --  name / ip address of the client to connect to

                if machine name is not provided, then the Machine object for the local machine
                will be created

                default:    None

            commcell_object     (object)    --  instance of the Commcell class from CVPySDK

                default:    None

            username            (str)       --  username for the client to connect to

                    Only Applicable if the client is not a Commvault Client

                default:    None

            password            (str)       --  password for the above specified user

                default:    None

            kwargs              (dict)      -- dictionary of acceptable key-worded arguments
            
        Also, initializes the Client object, if it is Commvault Client.

        Otherwise, it creates a PowerShell credentials object for the client.

        """
        super(WindowsMachine, self).__init__(machine_name, commcell_object, username, password)

        if self.is_commvault_client:
            self._script_generator = ScriptGenerator()

            self._execution_policy = self.client_object.execute_command(
                'powershell.exe Get-ExecutionPolicy'
            )[1].strip()

            # Ensure the PowerShell execution policy is set to Remote Signed
            __ = self.client_object.execute_command(
                'powershell.exe Set-ExecutionPolicy RemoteSigned -Force'
            )

            # check if CVD is able to execute the operation
            self.get_storage_details()
            self._instance = self.client_object.instance

        else:
            if self.is_local_machine:
                process = subprocess.run(
                    'powershell.exe Get-ExecutionPolicy',
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE
                )
                self._execution_policy = process.stdout.decode()

                # Ensure the PowerShell execution policy is set to Remote Signed
                __ = subprocess.run(
                    'powershell.exe Set-ExecutionPolicy RemoteSigned -Force',
                    stdin=subprocess.PIPE
                )

            self._script_generator = ScriptGenerator(self.machine_name, self.credentials_file)

            # check if the credentials given are correct or not
            output = self.execute_command('Get-PSDrive')
            exception = output.exception.lower().replace('\r\n', '')
            del output

            if 'access is denied' in exception:
                # if the operation raised exception, call disconnect, and raise
                # Exception
                self.disconnect()
                raise Exception('Authentication Failed. Invalid credentials provided.')
            elif 'client cannot connect to the destination' in exception:
                # if the operation raised exception, call disconnect, and raise
                # Exception
                self.disconnect()
                raise Exception(
                    'Failed to connect to the Machine. Please ensure the services are running'
                )
            else:
                del exception

            self._instance = 'Instance001'

        self._key = r'HKLM:\SOFTWARE\CommVault Systems\Galaxy\{0}\%s'.format(self.instance)
        self._os_info = "WINDOWS"
        self._log = logger.get_log()
        self.__network_creds = dict()
        self.__drive_to_path = dict()
        self.__used_drive_letters = None

    def __get_drive_letter(self):

        if not self.__drive_to_path:
            output = self.execute_command("Get-PSDrive")
            self.__used_drive_letters = list(next(zip(*output.formatted_output)))
        attempt = 90

        while attempt > 64:
            drive_letter = chr(attempt)
            if (drive_letter not in self.__used_drive_letters) and (
                    drive_letter not in self.__drive_to_path.keys()):
                return drive_letter
            attempt -= 1

        raise Exception("Drive Letter Exhausted")

    def __get_script_args(self, path):
        try:
            nw_path = self.__drive_to_path[path[0]]
        except KeyError:
            return {
                "network_path": "",
                "username": "",
                "password": "",
                "drive": "",
                "path": path
            }
        else:
            list_ = list(self.__network_creds[nw_path].values())
            return {
                "network_path": nw_path.rstrip("\\"),
                "username": list_.pop(0),
                "password": list_.pop(0),
                "drive": list_.pop(0),
                "path": f"{nw_path}{path[2:]}".rstrip("\\")
            }

    def _login_with_credentials(self):
        """Generates the Credentials File for the machine,
            to use for performing operations on the remote client.

        Raises:
            Exception:
                if an error was returned on the error stream

        """
        # Replace any white space ( ) in the PowerShell file path with ' '
        # e.g.; Original Script path:
        # C:\\Program Files\\Commvault\\ContentStore
        #   \\Automation\\AutomationUtils\\Scripts\\Windows\\Creds.ps1
        # Corrected Path:
        # C:\\Program Files\\Commvault\\ContentStore
        #   \\Automation\\AutomationUtils\\Scripts\\Windows\\Creds.ps1
        if 'linux' in sys.platform.lower():
            self._ssh = paramiko.SSHClient()
            self._ssh.load_system_host_keys()
            self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            try:
                self._ssh.connect(
                    self.machine_name, username=self.username, password=self.password, banner_timeout=200)
            except paramiko.AuthenticationException:
                raise Exception('Authentication Failed. Invalid credentials provided.')
        else:
            process = subprocess.Popen(
                [
                    'powershell',
                    CREDENTIALS.replace(" ", "' '"),
                    self.machine_name,
                    self.username,
                    self.password
                ],
                # HACK:the code gets hung at the process.communicate() call, if stdin is not included
                # this issue is yet to be looked into on why this happens
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )

            output, error = process.communicate()

            if error.decode():
                raise Exception(
                    'Failed to create credentials object.\nError: "{0}"'.format(
                        error.decode())
                )

            self.credentials_file = os.path.abspath(output.strip().decode())

    def _execute_with_credential(self, script):
        """Execute the script remotely on a client using the credentials provided,
            if the client is not a Commvault client.

            Args:
                script  (str)   --  path of the script file to execute on the client remotely

            Returns:
                object  -   instance of WindowsOutput class

        """
        # Replace any white space ( ) in the PowerShell file path with ' '
        # e.g.; Original Script path:
        # C:\\Program Files\\Commvault\\ContentStore
        #   \\Automation\\AutomationUtils\\Scripts\\Windows\\GetSize.ps1
        # Corrected Path:
        # C:\\Program Files\\Commvault\\ContentStore
        #   \\Automation\\AutomationUtils\\Scripts\\Windows\\GetSize.ps1
        if 'linux' in sys.platform.lower():
            sftp = self._ssh.open_sftp()
            file = script.rsplit('/')[-1]
            destination = 'c:/temp/'
            if 'temp' not in sftp.listdir('c:'):
                sftp.mkdir(destination)
            destination = destination + file
            sftp.put(script, destination)
            command = 'powershell -File {0}'.format(destination)
            _, stdout, stderr = self._ssh.exec_command(command)
            output = stdout.read()
            error = stderr.read()
            if stderr.channel.status_event._flag:
                exit_code = 0
            else:
                exit_code = 1
            if file in sftp.listdir('c:/temp/'):
                sftp.remove(destination)
            if self._encoding_type:
                return WindowsOutput(
                    exit_code, output.decode(self._encoding_type, "ignore"), error.decode()
                )
            else:
                return WindowsOutput(exit_code, output.decode(), error.decode())

        else:
            # Replicating retry mechanism as mentioned in execute_with_cvd method
            for _ in range(5):
                process = subprocess.Popen(
                    [
                        'powershell',
                        script.replace(" ", "' '")
                    ],
                    # HACK:the code gets hung at the process.communicate() call, if stdin is not included
                    # this issue is yet to be looked into on why this happens
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True
                )
                output, error = process.communicate()
                # Windows API uses unsigned int so -65536=4294901760
                if process.returncode != 4294901760:
                    break
            if self._encoding_type:
                return WindowsOutput(
                    process.returncode, output.decode(self._encoding_type, "ignore"), error.decode()
                )
            else:
                return WindowsOutput(process.returncode, output.decode(), error.decode())

    def _execute_with_cvd(self, script):
        """Execute the script remotely on a client using the CVD service running on the client.
            Only applicable if the client is a Commvault Client.

            Args:
                script  (str)   --  path of the script file to execute on the client remotely

            Returns:
                object  -   instance of WindowsOutput class

        """
        # HACK in Datacenter 2019, Powershell scripts fail intermittently with exit code -65536;
        # Temporary fix to retry until we do not get this exit code
        for _ in range(5):
            if os.path.isfile(script):
                exit_code, output, error_message = self.client_object.execute_script(
                    'PowerShell', script
                )
            else:
                exit_code, output, error_message = self.client_object.execute_command(script)
            if exit_code != -65536:
                break

        return WindowsOutput(exit_code, output, error_message)

    def _get_file_hash(self, file_path, algorithm="MD5"):
        """Returns MD5 hash value of the specified file at the given file path.

          Args:
              file_path       (str)             --  Path of the file to get the hash value of.

              algorithm       (str)             --  Specifies the cryptographic hash function for
                                                    computing the hash value of the contents.

                Default: "MD5".

              The acceptable values for algorithm parameter are:
                 * SHA1
                 * SHA256
                 * SHA384
                 * SHA512
                 * MD5


          Returns:
              str     -   hash value of the given file.

          Raises:
              Exception: If file path doesn't exist.

                  If the algorithm entered is invalid.

                  If failed to get the hash value.

          """
        # checks whether the given directory exists
        if not self.check_file_exists(file_path):
            raise Exception(f"{file_path} file does not exist on {self.machine_name}")

        # checks with the list of supported algorithms
        if algorithm.upper() not in ALGORITHM_LIST:
            raise Exception(f"Algorithm not found under the list {ALGORITHM_LIST}")

        # substitutes the variables into the script and runs it.
        self._script_generator.script = GET_HASH
        data = self.__get_script_args(file_path)
        data.update({
            'type': 'File',
            'ignore': "",
            'ignore_case': "",
            'algorithm': algorithm,
        })
        hash_script = self._script_generator.run(data)
        output = self.execute(hash_script)
        os.unlink(hash_script)

        # raises Exception
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.formatted_output

    def _get_folder_hash(
            self,
            directory_path,
            ignore_folder=None,
            ignore_case=False,
            algorithm="MD5"):
        """Returns set of files and their MD5 hash values present on the input path.

          Args:
              directory_path      (str)   --  path of the directory to get hash values of.

              ignore_folder       (list)  --  list of folders to be ignored.
                Default: None.

              ignore_case         (bool)  --  ignores the case if set to True.
                Default: False.

              algorithm           (str)   --  Specifies the cryptographic hash function
                    to use for computing the hash value of the contents.

                Default: "MD5"

              The acceptable values for algorithm parameter are:
                 * SHA1
                 * SHA256
                 * SHA384
                 * SHA512
                 * MD5


          Returns:
              set     -   set consisting of the file paths and their hash value as tuple

                  set(
                      (file_path1, hash1),

                      (file_path2, hash2)

                  )

          Raises:
              Exception: If specified folder doesn't exist.

                  If the algorithm entered is invalid.

                  If failed to get the hash values.

          """

        # checks whether the given directory exists
        if not self.check_directory_exists(directory_path):
            raise Exception(f"{directory_path} path does not exist on {self.machine_name}")

        # checks with the list of supported algorithms
        if algorithm.upper() not in ALGORITHM_LIST:
            raise Exception(f"Algorithm not found under the list {ALGORITHM_LIST}")

        # converting list to a single string with delimiters in between
        if ignore_folder is None:
            ignore_folder = []
        ignore_string = WINDOWS_DELIMITER.join(ignore_folder).replace("$", "`$")

        # substitutes the variables into the script and runs it.
        self._script_generator.script = GET_HASH
        data = self.__get_script_args(directory_path)
        data.update({
            'type': 'Folder',
            'ignore': ignore_string,
            'ignore_case': ignore_case,
            'algorithm': algorithm,
        })

        hash_script = self._script_generator.run(data)
        output = self.execute(hash_script)
        os.unlink(hash_script)
        if 'is accepting requests' in output.exception.replace('\n', '').replace('\r', ''):
            self._log.info("Https failed. Going via http")
            hash_script = self._script_generator.run(data, http_route=True)
            output = self.execute(hash_script)
            os.unlink(hash_script)

        # raises Exception
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        # parses the output generated from executing the script
        value = output.get_columns(['Path', 'Hash'])
        if not value:
            return set()
        directory_path = data["path"].rstrip('\\').replace(" ", "")
        hash_values = set()
        directory_path = directory_path.replace('/', '')
        # populates the set
        for val in value:
            hash_values.add((val[0].replace(directory_path + '\\', ''), val[1]))

        return hash_values

    @staticmethod
    def _read_local_file(file_path):
        """Reads the contents of the file present on the local machine.

        Args:
            file_path   (str)   --  path of the file to get the contents of

        Returns:
            str     -   contents of the file

        Raises:
            Exception:
                if the file is not valid given at the path

        """
        if not os.path.isfile(file_path):
            raise Exception('Not a valid file at the given path')

        with open(file_path) as file_object:
            contents = file_object.read()

        return contents

    def _copy_file_from_local(self, local_path, remote_path, log_output=False):
        """Copies the file present at the given path to the path specified on the remote machine.

        Args:
            local_path      (str)   --  path of the file on the local machine

            remote_path     (str)   --  path of the directory to which the file should be
            copied on the remote machine

            log_output      (bool)  --  Log file copy output if set to True.
                                        Not if False.

        Returns:
            (bool)  -- True is file copied successfully

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to copy the file

        """
        if self.is_commvault_client:
            self.client_object.upload_file(local_path, remote_path)
        else:
            path, file_name = os.path.split(local_path)

            data = dict((f"{key}_1", value)
                        for (key, value) in self.__get_script_args(path).items())
            data.update(dict((f"{key}_2", value)
                             for (key, value) in self.__get_script_args(remote_path).items()))
            data["source"] = data.pop("path_1")
            data["destination"] = data.pop("path_2")
            data["file_name"] = file_name

            self._script_generator.script = COPY_FILE

            copy_file_script = self._script_generator.run(data)
            output = self.execute(copy_file_script)
            os.unlink(copy_file_script)
            if log_output:
                self._log.info(output.output)
            if output.exit_code != 0:
                raise Exception("copy file from local failed. please check the logs")

        return True

    def _get_files_or_folders_in_path(self, folder_path, operation_type, recurse=True, only_hidden=False, days_old=0):
        """Returns the list of all the files / folders at the given folder path.

        Args:
            folder_path     (str)   --  full path of the folder to get the
                                        list of files / folders from

            operation_type  (str)   --  type of the operation, i.e., whether to get the files
                                        or the folders from the given folder path

                                        Valid values are

                                        -   FILE
                                        -   FOLDER

            recurse         (bool)  --  True - as default value, if needs to recurse through subfolders

            only_hidden     (bool)  --  False - as default value, if it is true it will list only hidden files in the path

            days_old        (int)   --  Number of days old to filter the files or folders

        Returns:
            list    -   list of the files / folders present at the given path

        Raises:
            Exception:
                if path is not valid

                if failed to get the list of files / folders

        """
        if not self.check_directory_exists(folder_path):
            raise Exception('Please give a valid path')

        # Update the script generator with the new parameter 'DaysOld'
        self._script_generator.script = FILE_OR_FOLDER_LIST
        data = {
            'folder_path': folder_path,
            'type': operation_type,
            'Recurse': "$true" if recurse else "$false",
            'OnlyHidden': "$true" if only_hidden else "$false",
            'DaysOld': days_old  # Adding DaysOld parameter to the script data
        }

        script = self._script_generator.run(data)

        output = self.execute(script)
        os.unlink(script)

        # Lambda function is required, as each element of formatted output is a list
        # whereas the output should only be a list with each value being a string
        return list(map(lambda x: ' '.join(x), output.formatted_output))

    def _get_client_ip(self):
        """Gets the ip_address of the machine"""
        cmd = "hostname"
        cmd_output = self.execute_command(cmd)
        hostname = cmd_output.formatted_output
        cmd = "Test-Connection -ComputerName {0} -Count 1 | Select-Object IPV4Address".format(
            hostname)
        cmd_output = self.execute_command(cmd)
        self._ip_address = str(cmd_output.formatted_output[0][0])

    @property
    def is_connected(self):
        """Returns boolean specifying whether the connection to the machine is open or closed."""
        try:
            if self.client_object:
                self._is_connected = self.client_object.is_ready

            elif self.credentials_file:
                # check if the connection is alive or not
                output = self.execute_command('Get-PSDrive')

                if ('client cannot connect to the destination' in output.exception.lower() or
                        'access is denied' in output.exception.lower()):
                    self._is_connected = False
                else:
                    self._is_connected = True

                del output

            elif self.is_local_machine:
                self._is_connected = True

            else:
                self._is_connected = False
        except AttributeError:
            self._is_connected = False

        return self._is_connected

    @property
    def key(self):
        """Returns the value of key attribute."""
        return self._key

    @property
    def instance(self):
        """Returns the value of instance attribute."""
        return self._instance

    @instance.setter
    def instance(self, instance):
        """Sets the value of instance attribute."""
        if 'Instance' in instance:
            self._instance = instance
        else:
            self._instance = 'Instance{0}'.format(instance)

        self._key = r'HKLM:\SOFTWARE\CommVault Systems\Galaxy\{0}\%s'.format(self.instance)

    @property
    def tmp_dir(self):
        """Returns the path of the **tmp** directory on the Windows Machine, where temporary
            database files are stored.

            default value:  C:\\\\tmp

        """
        # create directory should always be called, to ensure that the directory exists,
        # and ADD it if it does not exists on the machine
        if not self.check_directory_exists(WINDOWS_TMP_DIR):
            self.create_directory(WINDOWS_TMP_DIR)
        return WINDOWS_TMP_DIR

    @property
    def os_sep(self):
        """Returns the path separator based on the OS of the Machine."""
        return "\\"

    def reboot_client(self):
        """Reboots the machine.

            Please **NOTE** that the connectivity will go down in this scenario, and the Machine
            class may not be able to re-establish the connection to the Machine.

            In such cases, the user will have to initialize the Machine class instance again.

            Args:
                None

            Returns:
                object  -   instance of the WindowsOutput class

            Raises:
                Exception:
                    if failed to reboot the machine

        """
        output = self.execute_command('Restart-Computer -Force')

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output

    def shutdown_client(self):
        """shutdown the machine.

            This method turns off active host, Required to implement unplanned Failover Test Case.

            Args:
                None

            Returns:
                object  -   instance of the WindowsOutput class

            Raises:
                Exception:
                    if fails to shut down machine.

        """
        output = self.execute_command('Stop-Computer -Force')

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output

    def kill_process(self, process_name=None, process_id=None):
        """Terminates a running process on the client machine with either the given
            process name or the process id.

        Args:
            process_name    (str)   --  Name of the process to be terminate

                                            Example: cvd

            process_id      (str)   --  ID of the process ID to be terminated

        Returns:
            object  -   instance of WindowsOutput class

        Raises:
            Exception:
                if neither the process name nor the process id is given

                if failed to kill the process

        """
        if process_name:
            command = f"Stop-Process -Name {process_name} -Force"
        elif process_id:
            command = f"Stop-Process -Id {process_id} -Force"
        else:
            raise Exception('Please provide either the process Name or the process ID')

        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output

    def execute_command(self, command):
        """Executes a PowerShell command on the machine.

            An instance of the **WindowsOutput** class is returned.

            Output / Exception messages received from command execution are
            available as the attributes of the class instance.

                output_instance.output              --  raw output returned from the command

                output_instance.formatted_output    --  o/p received after parsing the raw output

                output_instance.exception           --  raw exception message

                output_instance.exception_message   --  parsed exception message from the raw o/p


        Args:
            command     (str)   --  PowerShell command to be executed on the machine

        Returns:
            object  -   instance of WindowsOutput class

        """
        self._script_generator.script = EXECUTE_COMMAND
        data = {
            'command': command
        }
        execute_command_script = self._script_generator.run(data)

        output = self.execute(execute_command_script)
        os.unlink(execute_command_script)
        if 'The SSL certificate contains a common name (CN)' in output.exception or \
                'is running and is accepting' in output.exception.replace('\n', '').replace('\r', ''):
            execute_command_script = self._script_generator.run(data, http_route=True)
            output = self.execute(execute_command_script)
            os.unlink(execute_command_script)

        return output

    # OS related functions
    def check_directory_exists(self, directory_path):
        """Check if a directory exists on the client or not.

        Args:
            directory_path  (str)   --  path of the directory to check

        Returns:
            bool    -   boolean value whether the directory exists or not

        """
        if not directory_path:
            return False
        data = self.__get_script_args(directory_path)
        data["directory_path"] = data.pop("path")
        self._script_generator.script = DIRECTORY_EXISTS

        directory_exists_script = self._script_generator.run(data)

        output = self.execute(directory_exists_script)
        os.unlink(directory_exists_script)
        if 'is accepting requests' in output.exception.replace('\n', '').replace('\r', ''):
            directory_exists_script = self._script_generator.run(data, http_route=True)
            output = self.execute(directory_exists_script)
            os.unlink(directory_exists_script)

        return str(output.formatted_output).lower() == 'true'

    def check_file_exists(self, file_path):
        """Check if a file exists on the client or not.

        Args:
            file_path  (str)   --  path of file to check

        Returns:
            bool    -   boolean value whether the file exists or not

        """
        return self.check_directory_exists(file_path)

    def create_directory(self, directory_name, username=None, password=None, force_create=False):
        """Creates a directory on the client, if it does not exist.

        Args:
            directory_name  (str)   --  name / full path of the directory to create

            username        (str)   --  username to access the path

            password        (str)   --  password to access the path

            force_create    (bool)  --  deletes the existing directory and creates afresh

        Returns:
            True    -   if directory creation was successful

        Raises:
            Exception(Exception_Code, Exception_Message):
                if directory already exists

        """
        if username and password:
            drive = self.mount_network_path(directory_name, username, password)
            data = self.__get_script_args(f"{drive}:\\")
            data["directory_name"] = data.get("network_path")
        else:
            data = self.__get_script_args(directory_name)
            data["directory_name"] = data.pop("path")

        data["force_create"] = False

        # currently force_create un-supported for UNC path
        # as check_directory_exists don't have support for unc
        if force_create and not (username and password):
            if self.check_directory_exists(directory_name):
                data["force_create"] = True
        elif not (username and password):
            if self.check_directory_exists(directory_name):
                raise Exception("Directory already exists")

        self._script_generator.script = CREATE_DIRECTORY
        create_directory_script = self._script_generator.run(data)
        output = self.execute(create_directory_script)
        os.unlink(create_directory_script)
        if username and password:
            self.unmount_drive(drive)

        if 'is accepting requests' in output.exception.replace('\n', '').replace('\r', ''):
            create_directory_script = self._script_generator.run(data, http_route=True)
            output = self.execute(create_directory_script)
            os.unlink(create_directory_script)

        if output.exception_message:
            raise Exception(output.exception_code,
                            output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)
        elif output.exit_code != 0 and output.output:
            raise Exception(output.output)

        return True

    def rename_file_or_folder(self, old_name, new_name):
        """Renames a file or a folder on the client.

        Args:
            old_name    (str)   --  name / full path of the directory to rename

            new_name    (str)   --  new name / full path of the directory

        Returns:
            True    -   if the file or folder was renamed successfully

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to rename the file or folder

        """
        self._script_generator.script = RENAME_ITEM
        data = {
            'old_name': old_name,
            'new_name': new_name
        }
        rename_item_script = self._script_generator.run(data)

        output = self.execute(rename_item_script)
        os.unlink(rename_item_script)
        if 'is accepting requests' in output.exception.replace('\n', '').replace('\r', ''):
            rename_item_script = self._script_generator.run(data, http_route=True)
            output = self.execute(rename_item_script)
            os.unlink(rename_item_script)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return True

    def remove_directory(self, directory_name, days=None, username=None, password=None):
        """Removes a directory on the client.

        Args:
            directory_name  (str)   --  name of the directory to remove

            days            (int)   --  directories older than the given days
            will be cleaned up default: None

            username        (str)   -- username to access the path

            password        (str)   -- password to access the path

        Returns:
            True    -   if directory was removed successfully

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to remove the directory
                if entire root path is provided for deletion

        """
        if directory_name in ['/', '\\']:
            raise Exception('Cannot delete entire root path')

        data = dict()
        if username and password:
            drive = self.mount_network_path(directory_name, username, password)
            data = {
                'isUnc': True,
                'directory_name': directory_name,
                'username': username,
                'password': password,
                'drive': drive,
                'network_path': directory_name,
                'days': 0
            }
        elif self.check_directory_exists(directory_name):
            data = {
                'isUnc': False,
                'directory_name': directory_name,
                'username': '',
                'password': '',
                'drive': '',
                'network_path': directory_name,
                'days': 0 if days is None else int(days)
            }
        if data:
            self._script_generator.script = REMOVE_DIRECTORY
            remove_directory_script = self._script_generator.run(data)
            self._log.info("Removing directory [%s]", directory_name)
            output = self.execute(remove_directory_script)
            os.unlink(remove_directory_script)
            if 'is accepting requests' in output.exception.replace('\n', '').replace('\r', ''):
                remove_directory_script = self._script_generator.run(data, http_route=True)
                output = self.execute(remove_directory_script)
                os.unlink(remove_directory_script)
            if username and password:
                self.unmount_drive(drive)
            if output.exception_message:
                raise Exception(output.exception_code,
                                output.exception_message)
            elif output.exception:
                raise Exception(output.exception_code, output.exception)
            elif output.exit_code != 0 and output.output:
                raise Exception(output.output)
            elif "remove-item : cannot remove item" in output.formatted_output.lower():
                raise Exception(output.formatted_output)
        return True

    def modify_item_datetime(self, path, creation_time=None, modified_time=None, access_time=None):
        """ Changes the last Access time and Modified time of files in unix and windows.
            Also changes creation time in windows.

            Args:
                path   (str)   --   full path of a file or folder

                creation_time    (datetime)   --  Create time
                    default -   None

                modified_time    (datetime)   --  Write time
                    default -   None

                access_time      (datetime)   --  Access time
                    default -   None
        """
        commands = []
        time_format = '%m/%d/%Y %H:%M:%S'
        if creation_time is not None:
            command = f"(Get-Item '{path}').CreationTime = '{creation_time.strftime(time_format)}'"
            commands.append(command)

        if modified_time is not None:
            command = f"(Get-Item '{path}').LastWriteTime = '{modified_time.strftime(time_format)}'"
            commands.append(command)

        if access_time is not None:
            command = f"(Get-Item '{path}').LastAccessTime = '{access_time.strftime(time_format)}'"
            commands.append(command)

        self.execute_command(';'.join(commands))

    def get_file_size(self, file_path, in_bytes=False, size_on_disk=False):
        """Gets the size of a file on the client.

        Args:
            file_path   (str)   --  path of the file to get the size of

            in_bytes    (bool)  --  if true returns the size in bytes

            size_on_disk (bool) --  if size on disk should be returned

        Returns:
            float   -   size of the file on the client (in MB)

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to get the size of the file

        """
        data = self.__get_script_args(file_path)
        data["type"] = "File"
        # decide if its size or size on disk
        if size_on_disk:
            self._script_generator.script = GET_SIZE_ONDISK
        else:
            self._script_generator.script = GET_SIZE

        get_size_script = self._script_generator.run(data)

        output = self.execute(get_size_script)
        os.unlink(get_size_script)
        if 'is accepting requests' in output.exception.replace('\n', '').replace('\r', ''):
            get_size_script = self._script_generator.run(data, http_route=True)
            output = self.execute(get_size_script)
            os.unlink(get_size_script)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        if in_bytes:
            return float(output.formatted_output)

        return round(float(output.formatted_output) / 2 ** 20, 2)

    def get_folder_size(self, folder_path, in_bytes=False, size_on_disk=False):
        """Gets the size of a folder on the client.

        Args:
            folder_path     (str)   --  path of the folder to get the size of

            in_bytes        (bool)  --  if true returns the size in bytes

            size_on_disk (bool) --  if size on disk should be returned

        Returns:
            float   -   size of the folder on the client (in MB)

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to get the size of the folder

        """
        data = self.__get_script_args(folder_path)
        data["type"] = "Folder"
        if size_on_disk:
            self._script_generator.script = GET_SIZE_ONDISK
        else:
            self._script_generator.script = GET_SIZE

        get_size_script = self._script_generator.run(data)

        output = self.execute(get_size_script)
        os.unlink(get_size_script)
        if 'is accepting requests' in output.exception.replace('\n', '').replace('\r', ''):
            get_size_script = self._script_generator.run(data, http_route=True)
            output = self.execute(get_size_script)
            os.unlink(get_size_script)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        if in_bytes:
            return float(output.formatted_output.replace('\r\n', ''))

        return round(float(output.formatted_output.replace('\r\n', '')) / 2 ** 20, 2)

    def get_file_stats_in_folder(self, folder_path):
        """Gets the total size in bytes by summing up the individual file size for files present in the directories and
                subdirectories of the given folder_path

                Args:
                    folder_path     (str)   --  path of the folder to get the size of

                Returns:
                    float   -   size of the folder on the client (in Bytes)

                Raises:
                    Exception(Exception_Code, Exception_Message):
                        if failed to get the size of the folder

                """
        return self.get_folder_size(folder_path, in_bytes=True)

    def get_storage_details(self):
        """Gets the details of the Storage on the Client.

        Returns:
            dict    -   dictionary consisting the details of the storage on the client (in MB)

            {
                'total': size_in_MB,

                'available': size_in_MB,

                'drive': {

                    'total': size_in_MB,

                    'available': size_in_MB,
                }
            }

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to get the storage details for the machine

        """
        output = self.execute_command('Get-PSDrive')

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        storage_dict = {
            'total': 0,
            'available': 0
        }

        for value in output.formatted_output:
            try:
                drive_name = value[0]
                used_space = round(float(value[1]) * 1024.0, 2)
                free_space = round(float(value[2]) * 1024.0, 2)
                total_space = round(free_space + used_space, 2)

                storage_dict[drive_name] = {
                    'total': total_space,
                    'available': free_space
                }

                storage_dict['total'] += total_space
                storage_dict['available'] += free_space
            except ValueError:
                continue

        return storage_dict

    def get_disk_count(self):
        """Returns the number of disks on the machine.

        Returns:
            int     -   disk count of the machine

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to get the disk count for the machine

        """
        output = self.execute_command(
            '(Get-WmiObject -Query "select * from Win32_PhysicalMedia").count'
        )

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.formatted_output

    def get_mounted_disks(self):
        """Returns the lists of disks mounted on the machine.

        Returns:
            str     -   Name of disks mounted on the machine

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to get the disk count for the machine

        """
        output = self.execute_command(
            '(Get-ciminstance -query "select Name from CIM_StorageVolume").Name'
        )

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.formatted_output

    # Registry related operations
    def check_registry_exists(self, key, value=None, win_key=None):
        """Check if a registry key / value exists on the client or not.

        Args:
            key     (str)   --  registry path of the key

            value   (str)   --  value of the registry key

            win_key (str)   --  full registry path of non commvault key Example: HKLM:\\SOFTWARE\\Python\\InstallPath

        Returns:
            bool    -   boolean value whether the registry key / value exists or not

        """
        self._script_generator.script = REGISTRY_EXISTS
        data = {
            'key': win_key or self.key % key,
            'value': value
        }
        registry_exists_script = self._script_generator.run(data)

        output = self.execute(registry_exists_script)
        os.unlink(registry_exists_script)

        return str(output.formatted_output).lower() == 'true'

    def get_registry_value(self, commvault_key=None, value=None, win_key=None):
        """Gets the data of a registry key and value on the client.

        Args:
            commvault_key   (str)   --  registry path of the commvault key
                Example: Automation

            value           (str)   --  value of the registry key
                Example: CVAUTOPATH

            win_key         (str)   --  full registry path of non commvault key
                Example: HKLM:\\SOFTWARE\\Python\\PythonCore\\3.6\\InstallPath

        Returns:
            str     -   data of the value of the registry key

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to get the data of the registry key and value

        """
        self._script_generator.script = GET_REG_VALUE
        data = {
            'key': win_key or self.key % commvault_key,
            'value': value
        }
        get_reg_value_script = self._script_generator.run(data)

        output = self.execute(get_reg_value_script)
        os.unlink(get_reg_value_script)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.formatted_output

    def create_registry(self, key, value=None, data=None, reg_type='String'):
        """Creates a registry key / value on the client, if it does not exist.

        Args:
            key         (str)       --  registry path of the key


            value       (str)       --  value of the registry key

                default: None


            data        (str)       --  data for the registry value

                default: None


            reg_type    (str)       --  type of the registry value to add

                Valid values are:

                    - String
                    - Binary
                    - DWord
                    - QWord
                    - MultiString

                default: String


        Returns:
            bool    -   if registry key / value creation was successful


        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to create the registry key

        """
        self._script_generator.script = SET_REG_VALUE
        if not key.startswith('HKLM:') and not key.startswith('HKCC:') and not key.startswith('HKCR:') \
                and not key.startswith('HKU:') and not key.startswith('HKCU:'):
            key = self.key % key
        data = {
            'key': key,
            'value': value,
            'data': data,
            'type': reg_type
        }
        create_registry_script = self._script_generator.run(data)

        output = self.execute(create_registry_script)
        os.unlink(create_registry_script)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.formatted_output == ''

    def update_registry(self, key, value, data=None, reg_type='String'):
        """Updates the value of a registry key on the client.

        Args:
            key     (str)       --  registry path of the key

            value   (str)       --  value of the registry key

            data    (object)    --  data for the registry value

            type    (str)       --  type of the registry value to add

                Valid values are:

                    - String
                    - Binary
                    - DWord
                    - QWord
                    - MultiString

                default: String

        Returns:
            bool    -   if registry value was updated successfully

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to get the storage details for the machine

        """
        self._script_generator.script = SET_REG_VALUE
        data = {
            'key': self.key % key,
            'value': value,
            'data': data,
            'type': reg_type
        }
        update_reg_value_script = self._script_generator.run(data)

        output = self.execute(update_reg_value_script)
        os.unlink(update_reg_value_script)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.formatted_output == ''

    def remove_registry(self, key, value=None):
        """Removes a registry key / value on the client.

        Args:
            key     (str)       --  registry path of the key

            value   (str)       --  value of the registry key

        Returns:
            bool    -   if registry key / value removal was successful

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to remove the registry key

        """
        self._script_generator.script = DELETE_REGISTRY
        data = {
            'key': self.key % key,
            'value': value
        }
        delete_registry_script = self._script_generator.run(data)

        output = self.execute(delete_registry_script)
        os.unlink(delete_registry_script)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.formatted_output == ''

    def is_file(self, path):
        """Checks if the given path is a file or not.

        Args:
            path    (str)   --  full path of the file to be validated

        Returns:
            bool:
                True    -   if the given path is a file

                False   -   if the given path is NOT a file

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed check if its file

        """

        command = f"([IO.FileInfo]'{path}').Attributes -match 'Archive'"
        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.formatted_output

    def is_directory(self, path):
        """Checks if the given path is a directory or not.

        Args:
            path    (str)   --  full path of the directory to be validated

        Returns:
            bool:
                True    -   if the given path is a directory

                False   -   if the given path is NOT a directory

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed check if its directory

        """

        command = f"([IO.FileInfo]'{path}').Attributes -match 'Directory'"
        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.formatted_output

    def mount_network_path(self, network_path, username, password, cifs_client_mount_dir=None):
        """Mounts the specified network path on this machine.

        Args:
            network_path    (str)   --  network path to be mounted on this machine

            username        (str)   --  username to access the network path

                Ex: DOMAIN\\\\USERNAME

            password        (str)   --  password for above mentioned user

            cifs_client_mount_dir (str) -- param currently supported only for unix_machine, added here for consistent
                                            function signature
        Returns:
            str     -   drive letter where the network path is mounted


        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to mount network path

        """
        if network_path not in self.__network_creds:
            drive_letter = self.__get_drive_letter()
            self.__network_creds[network_path] = {
                'username': username,
                'password': password,
                'drive': drive_letter
            }
            self._log.info(f"Mounting path [{network_path}] on client [{self.machine_name}] "
                           f"with user [{username}]")
            self.__drive_to_path[drive_letter] = network_path
            return drive_letter

        self._log.info("Mount path already exists...using it. ")
        return self.__network_creds[network_path]['drive']

    def copy_folder_to_network_share(self, source_path, network_path, username, password, **kwargs):
        """Copies the directory specified at source path to the network share path.

        Args:
            source_path     (str)   --  source directory to be copied

            network_path    (str)   --  network path to copy the files and folders at

            username        (str)   --  username to access network path

                e.g.; Domain\\\\Username

            password        (str)   --  password for the above mentioned user


            \*\*kwargs          (dict)  --  optional arguments

                Available kwargs Options:

                    threads     (int)   -- Number of threads to be used by copy

                    raise_exception (bool) -- set to True to raise exception if copy failed

        Returns:
            bool:
                True    -   if the file/folder was copied successfully

                False   -   if failed to copy the file/folder

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to mount network path

                if failed to copy files to mounted drive

                if failed to un mount network drive

        """
        drive = self.mount_network_path(network_path, username, password)
        try:
            self.copy_folder(source_path, f"{drive}:\\", **kwargs)
        except Exception as exp:
            self.unmount_drive(drive)
            if kwargs.get('raise_exception'):
                raise Exception('copy folder to network share failed') from exp
            return False
        self.unmount_drive(drive)
        return True

    def copy_from_network_share(self, network_path, destination_path, username, password, **kwargs):
        """Copies the file/folder from the given network path to the destination path on
           the machine represented by this Machine class instance.

        Args:
            network_path        (str)   --  full UNC path of the file/folder to be copied

            destination_path    (str)   --  destination folder to copy the file/folder at

            username            (str)   --  username to access the network path

                e.g.; Domain\\\\Username

            password        (str)   --  password for the above mentioned user

            \*\*kwargs          (dict)  --  optional arguments

                Available kwargs Options:

                    threads     (int)   -- Number of threads to be used by copy

                    raise_exception (bool) -- set to True to raise exception if copy failed

                    use_xcopy   (bool)  --  True: If xcopy should be used over robocopy
                                            Default: False

        Returns:
            bool:
                True    -   if the file/folder was copied successfully

                False   -   if failed to copy the file/folder

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to mount network path

                if failed to copy file/folder from mounted drive

                if failed to un mount network drive

        """
        machine_name = network_path.lstrip('\\').split('\\')[0]

        # To find whether path is file or directory creating machine class object
        machine = Machine(machine_name, username=username, password=password)

        try:
            if machine.is_directory(network_path) == 'False':
                path, file_name = os.path.split(network_path)
                drive = self.mount_network_path(path, username, password)
                self._copy_file_from_local(f"{drive}:\\{file_name}", destination_path)
            else:
                drive = self.mount_network_path(network_path, username, password)
                self.copy_folder(f"{drive}:\\", destination_path, **kwargs)

            self.unmount_drive(drive)

        except Exception as exp:
            if kwargs.get('raise_exception'):
                raise Exception('copy from network share failed failed') from exp
            return False
        return True

    def copy_folder(self, source_path, destination_path, optional_params='', **kwargs):
        """Copies the directory/file specified at source path to the destination path.

        Args:
            source_path         (str)   --  source directory to be copied

            destination_path    (str)   --  destination path where the folder has to be copied

            optional_params     (str)   --  just a placeholder arg as of now [used for unix machine]

            \*\*kwargs          (dict)  --  optional arguments

                Available kwargs Options:

                    threads     (int)   -- Number of threads to be used by copy

                    log_output  (bool)  -- True if log the command output. Else False
                                            Default: False

                    use_xcopy (bool)    -- True if you want to do an xcopy instead of robocopy
                                            Default: False

                    recurse (bool)      -- False if you do not want to recurse into subfolders
                                            Default: True
        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to connect to the machine where the copy has to done locally

                if failed to copy files from source to destination

                if either of the source or destination path specifies is wrong

        """
        if kwargs.get('username1', None) and kwargs.get('password1', None):
            drive1 = self.mount_network_path(source_path, kwargs.get('username1'), kwargs.get('password1'))
            data = dict((f"{key}_1", value)
                        for (key, value) in self.__get_script_args(drive1).items())
        else:
            # older behavior
            data = dict((f"{key}_1", value)
                        for (key, value) in self.__get_script_args(source_path).items())

        if kwargs.get('username2', None) and kwargs.get('password2', None):
            drive2 = self.mount_network_path(destination_path, kwargs.get('username2'), kwargs.get('password2'))
            data.update(dict((f"{key}_2", value)
                             for (key, value) in self.__get_script_args(drive2).items()))
        else:
            # older behavior
            data.update(dict((f"{key}_2", value)
                             for (key, value) in self.__get_script_args(destination_path).items()))

        data["source"] = data.pop("path_1")
        data["destination"] = data.pop("path_2")
        data["threads"] = kwargs.get('threads', COPY_FOLDER_THREADS)
        data["use_xcopy"] = "$true" if kwargs.get('use_xcopy') else "$false"
        data["recurse"] = "$true" if kwargs.get('recurse', True) else "$false"

        self._script_generator.script = COPY_FOLDER

        copy_folder_script = self._script_generator.run(data)
        output = self.execute(copy_folder_script)
        os.unlink(copy_folder_script)

        if kwargs.get('username1', None) and kwargs.get('password1', None):
            self.unmount_drive(drive1)
        if kwargs.get('username2', None) and kwargs.get('password2', None):
            self.unmount_drive(drive2)
        if kwargs.get('log_output', False):
            self._log.info(output.output)
        if output.exit_code != 0:
            raise Exception("copy folder failed. please check the logs")

    def unmount_drive(self, drive_letter):
        """Un mounts the drive specified by the drive letter.

        Args:
            drive_letter    (str)   --  drive letter of the windows mount path to be un mounted

                e.g.; Z

        Returns:
                True                --  If successful

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to un mount the network drive

        """
        try:
            path = self.__drive_to_path.get(drive_letter)
            if path:
                del self.__network_creds[path]
                del self.__drive_to_path[drive_letter]
            return True
        except Exception as exp:
            pass

    def create_file(self, file_path, content, file_size=None):
        """Creates a file at specified path on this machine with the given content.

        Args:
            file_path   (str)   --  path of the file to be created

            content     (str)   --  content to be written in the file

            file_size   (int)  -- by default it is None, then it will create
                                    file with related content otherwise,
                                    it will create file with required size
        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to create file

        """
        self._log.info(
            "Creating file [%s], with content [%s], on client [%s]", file_path, content, self.machine_name)

        if file_size is None:
            self._script_generator.script = CREATE_FILE
            data = {
                'path': file_path,
                'content': content.replace('"', '`"')
            }
        elif isinstance(file_size, int):
            self._script_generator.script = CREATE_FILE_WITHSIZE
            data = {
                'FilePath': file_path,
                'Size': str(file_size)
            }
        else:
            raise Exception('file size need to be integer value')

        create_file_script = self._script_generator.run(data)

        output = self.execute(create_file_script)
        os.unlink(create_file_script)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return True

    def append_to_file(self, file_path, content):
        """Appends content to the file present at the specified file path.

            Args:
                file_path   (str)   --  full path of the file to be appended with

                content     (str)   --  content to append to the file

            Returns:
                None    -   if content was appended successfully

            Raises:
                Exception:
                    if no file exists at the given path

                    if failed to append content to file

        """

        command = 'Add-Content "{0}" "{1}" | Out-Null'.format(file_path, content)

        if file_path.startswith('\\'):
            output = self.execute_command_unc(command, file_path)
        else:
            output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def execute_exe(self, exe_path):
        """Execute the exe present at the given path.

        Args:
            exe_path    (str)   --  full path of the exe to be executed

        Returns:
            str     -   output of the exe execution

        Raises:
            Exception:
                if failed to execute the exe

        """

        exe_path = os.path.split(
            self.os_sep + os.path.basename(EXECUTE_EXE))[0]
        self._script_generator.script = EXECUTE_EXE
        data = {
            'exe_path': exe_path,
            'exe_name': os.path.basename(EXECUTE_EXE)
        }

        file_list_script = self._script_generator.run(data)

        output = self.execute(file_list_script)
        os.unlink(file_list_script)

        return output.output

    def copy_from_local(self, local_path, remote_path, **kwargs):
        """Copies the file / folder present at the given path to the path specified on the
            remote machine.

        Args:
            local_path      (str)   --  path of the file / folder on the local machine

            remote_path     (str)   --  path of the directory to which the file / folder
            should be copied on the remote machine

            \*\*kwargs          (dict)  --  optional arguments

                Available kwargs Options:

                    threads     (int)   -- Number of threads to be used by copy

                    raise_exception (bool) -- set to True to raise exception if copy failed

        Returns:

            **bool** output specifying whether the file / folder was copied successfully or not

                True    -   all files / folders were copied successfully

                False   -   failed to copy some files / folders

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to copy the file / folder

        """
        if not os.path.exists(local_path):
            raise Exception(f'Local path: "{local_path}" does not exist')

        if not self.check_directory_exists(remote_path):
            self.create_directory(remote_path)

        try:
            if self.is_commvault_client:
                if os.path.isfile(local_path):
                    self.client_object.upload_file(local_path, remote_path)
                else:
                    self._log.info(
                        "Uploading folder [{0}] to [{1}] on client [{2}]".format(
                            local_path, remote_path, self.machine_name)
                    )
                    self.client_object.upload_folder(local_path, remote_path)

            else:
                if 'linux' in sys.platform.lower():
                    self._log.info(
                        "Uploading folder [{0}] to [{1}] on client [{2}]".format(
                            local_path, remote_path, self.machine_name)
                    )
                    sftp = self._ssh.open_sftp()
                    file_name = None
                    if os.path.isfile(local_path):
                        file_name = local_path.split("/")[-1]
                        local_path = "/".join(("placeholder" + local_path).split("/")[:-1])[len("placeholder"):]
                    for dirpath, dirnames, filenames in os.walk(local_path):
                        remote_machine_path = self.join_path(remote_path, dirpath[len(local_path) + 1:])
                        try:
                            sftp.listdir(remote_machine_path)
                        except IOError:
                            sftp.mkdir(remote_machine_path)
                        if file_name:
                            if file_name in filenames:
                                sftp.put(os.path.join(dirpath, file_name), os.path.join(remote_machine_path, file_name))
                            else:
                                raise Exception("File {0} Not Found".format(file_name))
                        else:
                            for filename in filenames:
                                sftp.put(os.path.join(dirpath, filename), os.path.join(remote_machine_path, filename))
                else:
                    # set the value of ComputerName to `null`, so the PS script is
                    # executed locally, if the machine is not a local machine
                    if not self.is_local_machine:
                        self._script_generator.machine_name = '$null'

                    remote_path = fr"\\{self.machine_name}\{remote_path.replace(':', '$')}"
                    drive = self.mount_network_path(remote_path, self.username, self.password)

                    if os.path.isfile(local_path):
                        self._copy_file_from_local(local_path, f"{drive}:\\")
                    else:
                        self.copy_folder(local_path, f"{drive}:\\", **kwargs)

                    # reset the value of ComputerName back to the machine name, after the PS script has
                    # been executed successfully, only if the machine is not a local machine
                    if not self.is_local_machine:
                        self._script_generator.machine_name = self.machine_name

                    self.unmount_drive(drive)

        except Exception as exp:
            if not self.is_local_machine:
                self._script_generator.machine_name = self.machine_name

            if kwargs.get('raise_exception'):
                raise Exception('copy from local failed') from exp
            return False
        return True

    def read_file(self, file_path, **kwargs):
        """Returns the contents of the file present at the specified file path.

        Args:
            file_path   (str)   --  Full path of the file to get the contents of.

            \*\*kwargs  (dict)  --  Optional arguments

            Available kwargs Options:

                offset          (int)   :   Offset in the file, specified in bytes, from where content should be read.

                search_term     (str)   :   Returns only those lines in the file matching the search term which could
                also be a regular expression pattern.

                end                (int)    :    Offset in the file, specified in bytes, till where content should be read

                last_n_lines (int): Return last n lines from the file

        Returns:
            str     -   String consisting of the file contents.

        Raises:
            Exception:
                If no file exists at the given path.

                If failed to get the contents of the file.

        """

        offset = kwargs.get('offset', None)
        search_term = kwargs.get('search_term', None)
        end = kwargs.get('end', None)
        last_n_lines = kwargs.get('last_n_lines', None)
        encoding = kwargs.get('encoding', None)
        command = "Get-Content \"{}\"".format(file_path)
        if offset:
            command = "[System.Text.Encoding]::ASCII.GetString($({COMMAND} -Raw -Encoding Byte " \
                      "| % {{$_[{OFFSET}..($_.Length-1)]}}))".format(COMMAND=command, OFFSET=offset)
        if end:
            command = "[System.Text.Encoding]::ASCII.GetString($({COMMAND} -Raw -Encoding Byte " \
                      "| % {{$_[0..{OFFSET}]}}))".format(COMMAND=command, OFFSET=end)

        if search_term:
            command = "{COMMAND} " \
                      "| Where-Object {{$_ -match '{SEARCH_TERM}'}}".format(
                COMMAND=command, SEARCH_TERM=search_term)

        if last_n_lines:
            command = "{COMMAND} -tail {LAST_N_LINES}".format(
                COMMAND=command, LAST_N_LINES=last_n_lines)

        if encoding:
            command = "{COMMAND} -Encoding {encoding}".format(
                COMMAND=command, encoding=encoding
            )

        if file_path.startswith('\\'):
            output = self.execute_command_unc(command, file_path)

        else:
            output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.output

    def delete_file(self, file_path):
        """Deletes the file present at the specified file path.

        Args:
            file_path   (str)   --  full path of the file to be removed

        Returns:
            None    -   if the file was removed successfully

        Raises:
            Exception:
                if no file exists at the given path

                if failed to remove the file

        """
        self._log.info("Deleting file [%s] on client [%s]", file_path, self.machine_name)
        command = 'Remove-Item -Force "{0}" | Out-Null'.format(file_path)
        if file_path.startswith('\\'):
            output = self.execute_command_unc(command, file_path)
        else:
            output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def change_folder_owner(self, username, directory_path):
        """Changes the owner of the folder given as the value of directory_path.

        Args:
            username        (str)   --  name of user to give ownership

            directory_path  (str)   --  path of the directory to change ownership

        Returns:
            bool    -   boolean value if ownership change was successful

        Raises:
            NotImplementedError:
                the method has not yet been implemented for Windows Machine

            Exception:
                if specified folder doesn't exist

        """
        raise NotImplementedError('Method Not Implemented')

    def create_current_timestamp_folder(self, folder_path, timestamp="time"):
        """Creates a folder with current date / time as folder name at the given path.

        Args:
            folder_path     (str)   --  absolute path to create the folder at

            timestamp       (str)   --  whether to create a folder with the current date or the
            current time

                To create a folder with the date, pass the value as **date**

                Otherwise it'll always create folder with the current time as the folder name

        Returns:
            str     -   full path of the directory created

        Raises:
            Exception:
                if failed to create the folder

        """
        if timestamp == "date":
            folder_name = datetime.datetime.now().strftime('%Y-%m-%d')
        else:
            folder_name = datetime.datetime.now().strftime('%H-%M-%S')

        directory = self.join_path(folder_path, folder_name)

        if not self.check_directory_exists(directory):
            self.create_directory(directory)

        return directory

    def get_latest_timestamp_file_or_folder(self, folder_path, operation_type="folder"):
        """Get the latest timestamp folder in given path.

        Args:
            folder_path     (str)   --  full path of the folder to get latest
            file / folder from

            operation_type  (str)   --  type of the operation, i.e., whether to get latest file
            or the folder from the given folder path

                Valid values are:

                -   file
                -   folder

                default: folder

        Returns:
            str     -   full path of the directory that was created last inside the given
            folder path

        Raises:
            Exception:
                if failed to get the file / folder with the latest timestamp

        """
        if not self.check_directory_exists(folder_path):
            raise Exception('Please give a valid path')

        self._script_generator.script = LATEST_FILE_OR_FOLDER

        data = {
            'folder_path': folder_path,
            'type': operation_type
        }

        script = self._script_generator.run(data, select_columns=['Name'])

        output = self.execute(script)
        os.unlink(script)

        # lambda function is required, as each element of formatted output is a list
        # whereas the output should only be a list with each value being a string
        output_list = list(map(lambda x: ' '.join(x), output.formatted_output))

        if output_list:
            return self.join_path(folder_path, output_list[0])

    def generate_test_data(
            self,
            file_path,
            dirs=3,
            files=5,
            file_size=20,
            levels=1,
            hlinks=False,
            slinks=False,
            sparse=False,
            hslinks=False,
            sparse_hole_size=1024,
            acls=False,
            unicode=False,
            xattr=False,
            long_path=False,
            long_level=1500,
            problematic=False,
            zero_size_file=True,
            ascii_data_file=False,
            options="",
            **kwargs):
        """Generates and adds random test data at the given path with the specified options.

        Args:
            file_path           (str)   --  directory path where the data will be generated

            dirs                (int)   --  number of directories in each level

                default: 3

            files               (int)   --  number of files in each directory

                default: 5

            file_size           (int)   --  Size of the files in KB

                default: 20

            levels              (int)   --  number of levels to be created

                default: 1

            hlinks              (bool)  --  whether to create hardlink files

                default: False

            slinks              (bool)  --  whether to create symbolic link files

                default: False

            hslinks             (bool)  --  whether to create
                                            symbolic link files with hardlinks.

                default: False
                **support not yet implemented, added here for maintaining signature**
                **this argument will be ignored and not used till it is implemented**

            sparse              (bool)  --  whether to create sparse files

                default: False

            sparse_hole_size    (int)   --  Size of the holes in sparse files in KB

                default: 1024

            long_path           (bool)  --  whether to create long files
                default: False
                **support not yet implemented, added here for maintaining signature**
                **this argument will be ignored and not used till it is implemented**

            long_level          (int)   --  length of the long path
                default: 1500
                **support not yet implemented, added here for maintaining signature**
                **this argument will be ignored and not used till it is implemented**

            acls                (bool)  --  whether to create files with acls

                default: False

            unicode             (bool)  --  whether to create unicode files

                default: False

            problematic         (bool)  --  whether to create problematic data
                default: False
                **support not yet implemented, added here for maintaining signature**
                **this argument will be ignored and not used till it is implemented**

            xattr               (bool)  --  whether to create files with xattr

                default: False

            zero_size_file               (bool)  --  whether to create files
                                            with zero kb

                default: True

            ascii_data_file             (bool)  --  whether to create files within ASCII range [0-9a-zA-Z]

            options             (str)   --  to specify any other
            additional parameters to the script

                default: ""

            \*\*kwargs  (dict)  --  Optional arguments

            Available kwargs Options:

                hole_offset (int)       :   Offset in the file, specified in KB, from where content needs to be read.

                create_only (bool)      :   Only create files of the specified type.
                It will take effect only if dirs is 0.

                attribute_files (str)   :   Create files, with the specified attributes.
                Accepts CSV string with supported values being R,H and RH.

                custom_file_name    (str)   :   Provide a specific name for the file, if it's a.txt
                and 5 files need to be created, the names of the created files will be a1.txt, a2.txt...,a5.txt

                username            (str)   :   Username of the account that needs to be impersonated
                if data needs to be created on a share. Mandatory if value of file_path is a share, begins with \\.

                password            (str)   :   Password of the account that needs to be impersonated
                if data needs to be created on a share. Mandatory if value of file_path is a share, begins with \\.

            Constants:

                WINDOWS_GENERATE_TEST_DATA_THREAD_COUNT  (int)  -- Thread count can be modified in the constants file

                    default: 4

        Returns:
            bool    -   boolean value True is returned if no errors during data generation

        Raises:
            Exception:
                if any error occurred while generating the test data

    """

        script_arguments = {'path': file_path,
                            'dirs': dirs,
                            'files': files,
                            'size_in_kb': file_size,
                            'levels': levels,
                            'options': options,
                            'hole_size_in_kb': sparse_hole_size,
                            'sparse': 'yes' if sparse else 'no',
                            'hlinks': 'yes' if hlinks else 'no',
                            'slinks': 'yes' if slinks else 'no',
                            'acls': 'yes' if acls else 'no',
                            'xattr': 'yes' if xattr else 'no',
                            'zero_size_file': 'yes' if zero_size_file else 'no',
                            'ascii_data_file': 'yes' if ascii_data_file else 'no',
                            'unicode': 'yes' if unicode else 'no',
                            'thread_cnt': WINDOWS_GENERATE_TEST_DATA_THREAD_COUNT,
                            'hole_offset': kwargs.get('hole_offset', 0),
                            'create_only': 'yes' if kwargs.get('create_only', False) else 'no',
                            'attribute_files': kwargs.get('attribute_files', ''),
                            'zip_file_path': 'no', 'zip_exe_path': 'no', 'extr_file_path': 'no',
                            'custom_file_name': kwargs.get('custom_file_name', ''),
                            'server_host_name': '', 'username': '', 'password': ''}

        delete_zip = False
        if problematic:
            tmp_path = self.join_path(self.tmp_dir, str(id(self)))
            cv7z_path = self.join_path(self.client_object.install_directory, "Base", "cv7z.exe")
            extr_path = self.join_path(tmp_path, "extr")
            self.create_directory(tmp_path)
            self._copy_file_from_local(WINDOWS_PROBLEM_DATA, tmp_path)
            custom_zip_path = self.join_path(tmp_path, os.path.basename(WINDOWS_PROBLEM_DATA))
            script_arguments.update({'zip_file_path': custom_zip_path,
                                     'zip_exe_path': cv7z_path,
                                     'extr_file_path': extr_path})
            delete_zip = True

        if file_path.startswith("\\") and 'username' in kwargs:
            script_arguments.update({'server_host_name': ''.join(("\\\\", file_path[2:].split("\\", 1)[0]))})
            script_arguments.update({'username': kwargs['username'], 'password': kwargs['password']})

        self._script_generator.script = WINDOWS_ADD_DATA
        add_test_data = self._script_generator.run(script_arguments)

        output = self.execute(add_test_data)
        os.unlink(add_test_data)

        if delete_zip:
            self.remove_directory(tmp_path)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return True

    def modify_test_data(
            self,
            data_path,
            rename=False,
            modify=False,
            acls=False,
            xattr=False,
            permissions=False,
            slinks=False,
            hlinks=False,
            options="",
            **kwargs):
        """Modifies the test data at the given path based on the specified options.

        Args:
            data_path       (str)   --  directory path where dataset resides.

            rename          (bool)  --  whether to rename all files

                default: False

            modify          (bool)  --  whether to modify data of all files

                default: False

            acls            (bool)  --  whether to change acls of all files

                default: False

            xattr           (bool)  --  whether to change xattr of all files

                default: False

            permissions     (bool)  --  whether to change permission of all files

                default: False

            slinks          (bool)  --  whether to add symbolic link to all files

                default: False

            hlinks          (bool)  --  whether to add hard link to all files

                default: False

            options         (str)   --  to specify any other
            additional parameters to the script.

                default: ""

            \*\*kwargs  (dict)  --  Optional arguments
            available kwargs Options:
                encrypt_file_with_aes  (bool)  -- whether to aes encrypt files
                    default: False

        Returns:
            bool    -   boolean value True is returned if no errors during data generation.

        Raises:
            Exception:
                if any error occurred while modifying the test data

        """
        script_arguments = {'path': data_path,
                            'options': options,
                            'encrypt_file_with_aes': 'yes' if kwargs.get('encrypt_file_with_aes', False) else 'no',
                            'rename': 'yes' if rename else 'no',
                            'modify': 'yes' if modify else 'no',
                            'acls': 'yes' if acls else 'no',
                            'xattr': 'yes' if xattr else 'no',
                            'permissions': 'yes' if permissions else 'no',
                            'slinks': 'yes' if slinks else 'no',
                            'hlinks': 'yes' if hlinks else 'no'}

        self._log.info("Modifying test data in path [%s]", data_path)

        self._script_generator.script = WINDOWS_MODIFY_DATA
        modify_test_data = self._script_generator.run(script_arguments)

        output = self.execute(modify_test_data)
        os.unlink(modify_test_data)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return True

    def get_test_data_info(
            self,
            data_path,
            name=False,
            meta=False,
            checksum=False,
            acls=False,
            xattr=False,
            dirtime=False,
            skiplink=False,
            machinesort=False,
            options="",
            **kwargs):
        """Gets information about the items on the given path based on the given options.

        Args:
            data_path       (str)   --  directory path from where the data should be retrieved.

            name            (bool)  --  whether to get name of all the files

                default: False

            meta            (bool)  --  whether to get meta data of all files

                default: True

            checksum        (bool)  --  whether to get OS checksum of all files

                default: False

            machinesort     (bool)  --  whether to sort the results on the machine

                default: False

            acls            (bool)  --  whether to get acls of all files

                default: False

            xattr           (bool)  --  whether to get xattr of all files

                default: False

            dirtime         (bool)  --  whether to get time stamp of all directories
                default: False
                **support not yet implemented, added here for maintaining signature**
                **this argument will be ignored and not used till it is implemented**

            skiplink        (bool)  --  whether to skip link count of all files
                default: False
                **support not yet implemented, added here for maintaining signature**
                **this argument will be ignored and not used till it is implemented**

            options         (str)   --  to specify any other
            additional parameterS to the script.

                default: ""

            \*\*kwargs  (dict)  --  Optional arguments

            Available kwargs Options:

                custom_meta_list (str)       :   Only return the item properties specified by the value of this argument.
                Accepts CSV string with supported values being Hidden, FullName, LastWriteTime and Size.

        Returns:
            list    -   list of output lines while executing the script.

        Raises:
            Exception:
                if any error occurred while getting the data information.

        """
        script_arguments = {'path': data_path,
                            'options': options,
                            'name': 'yes' if name else 'no',
                            'meta': 'yes' if meta else 'no',
                            'sum': 'yes' if checksum else 'no',
                            'acls': 'yes' if acls else 'no',
                            'xattr': 'yes' if xattr else 'no',
                            'sorted': 'yes' if machinesort else 'no',
                            'dirtime': 'yes' if dirtime else 'no',
                            'custom_meta_list': kwargs.get('custom_meta_list', 'no')}

        self._script_generator.script = WINDOWS_GET_DATA
        get_test_data = self._script_generator.run(script_arguments)

        output = self.execute(get_test_data)
        os.unlink(get_test_data)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.output

    def get_items_list(
            self,
            data_path,
            sorted_output=True,
            include_parents=False):
        """Gets the list of items at the given path.

        Args:
            data_path           (str)    --  Directory path to get the items list.

            sorted              (bool)   --  To specify whether the list should be sorted.

                default: True

            include_parents     (bool)   --  To specify whether parent paths should be included.

                default: False

        Returns:
            list    -   List of the items.

        Raises:
            Exception:
                If any error occurred while getting the items list.

        """

        output_list_final = []
        output_list_1_final = []
        output_list_2_final = []
        find_cmd_1 = f"(Get-ChildItem \"{data_path}\" -Recurse | WHERE {{$_.FullName -notmatch 'unicode'}}).FullName"
        output_1 = self.execute_command(find_cmd_1)

        if output_1.exit_code != 0:
            if output_1.exception_message:
                raise Exception(output_1.exception_code, output_1.exception_message)
            elif output_1.exception:
                raise Exception(output_1.exception_code, output_1.exception)

        # output_2 WILL FOCUS ONLY ON THE "unicode" DATASET
        script_arguments = {'data_path': data_path, 'search_term': 'unicode'}

        self._script_generator.script = WINDOWS_GET_ASCII_VALUE_FOR_PATH
        get_items_list_ascii = self._script_generator.run(script_arguments)

        output_2 = self.execute(get_items_list_ascii)
        os.unlink(get_items_list_ascii)

        if output_2.exit_code != 0:
            if output_2.exception_message:
                raise Exception(output_2.exception_code, output_2.exception_message)
            elif output_2.exception:
                raise Exception(output_2.exception_code, output_2.exception)

        else:
            output_list_1 = output_1.output.split('\n')
            output_list_2 = output_2.output.split('\n')

            for i, item in enumerate(output_list_1):
                output_list_1[i] = str(item).strip()
                output_list_1_final.append(output_list_1[i])

            if output_list_2:
                for i, item in enumerate(output_list_2):
                    output_list_2[i] = str(item).strip()

                    # NO ASCII VALUE FOR ''
                    if output_list_2[i] != '':
                        output_list_2_final.append(output_list_2[i])

                # ASCII TO CHAR CONVERSION FOR output_list_2
                for i, ascii_list in enumerate(output_list_2_final):
                    output_list_2_final[i] = ''.join(
                        list(
                            map(chr, list(
                                map(int, str(ascii_list).split(','))
                            ))
                        )
                    )

            output_list_final.extend(output_list_1_final)
            output_list_final.extend(output_list_2_final)

            if include_parents:
                data_path = data_path + "\\"
                parent_list = []

                # IF data_path IS UNC THEN STRIP FIRST PARENT LEVEL, WHICH IS SERVER NAME
                if data_path.startswith("\\"):
                    for i in range(1, data_path.count("\\") - 2):
                        parent_list.append(data_path.rsplit("\\", i)[0])
                else:
                    for i in range(1, (data_path.count('\\') + 1)):
                        parent_list.append(data_path.rsplit('\\', i)[0])

                output_list_final.extend(parent_list)

            if sorted_output:
                output_list_final.sort()

            # REMOVE EMPTY ITEMS AND RETURN OUTPUT LIST
            output_list_final = [item.replace("\\\\", '\\') for item in output_list_final if item != '']

            return output_list_final

    def get_meta_list(self, data_path, sorted_output=True, dirtime=False, skiplink=False):
        """Gets the list of meta data of items from the machine on a given path.

        Args:
            data_path       (str/list)  --  Directory paths to get meta data of the items list.

            sorted_output   (bool)      --  To specify whether the list should be sorted

            dirtime         (bool)      --  Whether to get time stamp of all directories
                default: False
                **support not yet implemented, added here for maintaining signature**
                **this argument will be ignored and not used till it is implemented**

            skiplink        (bool)      --  Whether to skip link count of all files
                default: False
                **support not yet implemented, added here for maintaining signature**
                **this argument will be ignored and not used till it is implemented**

        Returns:
            list    -   list of meta data of items from the machine

        Raises:
            Exception:
                if any error occurred while getting the meta data of items

        """
        try:
            meta_data = self.get_test_data_info(
                data_path, meta=True, dirtime=dirtime, skiplink=skiplink)
            meta_list = meta_data.split('\n')
            while '' in meta_list:
                meta_list.remove('')

            if sorted_output:
                meta_list.sort()

            return meta_list

        except Exception as excp:
            raise Exception(
                "Error occurred while getting meta data from machine {0}".format(excp))

    def compare_meta_data(self, source_path, destination_path, dirtime=False, skiplink=False):
        """Compares the meta data of source path with destination path and checks if they are same.

         Args:
            source_path         (str)   --  source path of the folder to compare

            destination_path    (str)   --  destination path of the folder to compare

            dirtime             (bool)  --  whether to get time stamp of all directories
                default: False
                **support not yet implemented, added here for maintaining signature**
                **this argument will be ignored and not used till it is implemented**

            skiplink            (bool)  --  whether to skip link count of all files
                default: False
                **support not yet implemented, added here for maintaining signature**
                **this argument will be ignored and not used till it is implemented**

        Returns:
            tuple   -   tuple consisting of a boolean and a string, where:

                bool:

                    returns True if the lists are identical

                    returns False if the contents of the lists are different

                str:

                    empty string in case of True, otherwise string consisting of the
                    differences b/w the 2 lists separated by new-line

        Raises:
            Exception:
                if any error occurred while comparing the meta data of paths

        """
        try:
            source_list = self.get_meta_list(source_path, dirtime=dirtime, skiplink=skiplink)
            destination_list = self.get_meta_list(
                destination_path, dirtime=dirtime, skiplink=skiplink)
            return self._compare_lists(source_list, destination_list)

        except Exception as excp:
            raise Exception(f"Error occurred while comparing the metadata: {excp}")

    def get_checksum_list(self, data_path, sorted_output=True):
        """Gets the list of checksum of items from the machine on a give path
            this is Windows checksum.

         Args:
            data_path       (str/list)  --  Directory paths to get the checksum list.

            sorted_output   (bool)      --  To specify whether the checksum list should be sorted.

        Returns:
            list    -   list of checksum of items from  the machine.

        Raises:
            Exception:
                if any error occurred while getting the checksum of items.

        """
        try:

            checksum_list = []

            data_paths = [data_path] if isinstance(data_path, str) else data_path
            for data_path in data_paths:
                checksum_data = self.get_test_data_info(
                    data_path, checksum=True
                )
                checksum_list.extend(checksum_data.split('\n'))

            while '' in checksum_list:
                checksum_list.remove('')

            # checksum_list = ['1052662027 10240000 /test4.txt', '1154129607 10240000 /test2.txt',
            # '2275727550 10240000 /test3.txt']
            checksum_only_list = []
            for checksum in checksum_list:
                checksum_only_list.append(checksum.split(' ')[0])

            # checksum_only_list = ['1052662027', '1154129607', '2275727550']
            if sorted_output:
                checksum_only_list.sort()

            return checksum_only_list

        except Exception as excp:
            raise Exception(f"Error occurred while getting checksum list from machine {excp}")

    def compare_checksum(self, source_path, destination_path):
        """Compares the checksum of source path with destination path and checks if they are same.

         Args:
            source_path         (str)   --  source path of the folder to compare

            destination_path    (str)   --  destination path of the folder to compare

        Returns:
            tuple   -   tuple consisting of a boolean and a string, where:

                bool:

                    returns True if the lists are identical

                    returns False if the contents of the lists are different

                str:

                    empty string in case of True, otherwise string consisting of the
                    differences b/w the 2 lists separated by new-line

        Raises:
            Exception:
                if any error occurred while comparing the checksum of paths

        """
        try:
            source_list = self.get_checksum_list(source_path)
            destination_list = self.get_checksum_list(destination_path)

            return self._compare_lists(source_list, destination_list)
        except Exception as excp:
            raise Exception(f"Error occurred while comparing the checksums: {excp}")

    def get_registry_entries_for_subkey(
            self,
            subkey,
            recurse=True,
            find_subkey=None,
            find_entry=None):
        """Retrieves all the registry entries under a given subkey value
        and/or find a particular subkey or entry.

        Args:
            subkey      (str)   --  Name of the subkey

            recurse     (bool)  --  Boolean flag to specify whether to
            recurse through subekys of the specified subkey.

                default: True

            find_subkey (str)   --  Value of the subkey that needs to be found.

                default: None

                **support not yet implemented, added here for maintaining signature**

                **this argument will be ignored and not used till it is implemented**

            find_entry  (str)   -- Value of the entry that needs to be found.

                default: False

                **support not yet implemented, added here for maintaining signature**

                **this argument will be ignored and not used till it is implemented**

        Returns:
            str   -   newline separated string containing
            all the registry entries and their values.


        Raises:
            Exception:
                If any error occurred while retrieving
                registry entries from the given subkey value.

        """

        script_arguments = {
            'subkeyname': subkey,
            'recurse': 'yes' if recurse else 'no',
            'findsubkey': find_subkey,
            'findentry': find_entry
        }

        self._script_generator.script = WINDOWS_GET_REGISTRY_ENTRY_FOR_SUBKEY
        get_registry_entry_for_subkey = self._script_generator.run(script_arguments)

        output = self.execute(get_registry_entry_for_subkey)
        os.unlink(get_registry_entry_for_subkey)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.output

    def get_files_in_path(self, folder_path, recurse=True, only_hidden=False, days_old=0):
        """Returns the list of all the files at the given folder path.

        Args:
            folder_path     (str)   --  full path of the folder to get the list of files from

            recurse         (bool)  --  True -- as default value, if needs to recurse through subfolders

            only_hidden     (bool)  --  False -- as default value, it lists only hidden files

            days_old        (int)   --  Number of days old to filter the files

        Returns:
            list    -   list of the files present at the given path

        Raises:
            Exception:
                if path is not valid

                if failed to get the list of files

        """
        return self._get_files_or_folders_in_path(folder_path, 'FILE', recurse, only_hidden, days_old)

    def get_folders_in_path(self, folder_path, recurse=True):
        """Returns the list of all the folders at the given folder path.

        Args:
            folder_path     (str)   --  full path of the folder to get the list of folders from

            recurse (bool) -- True - as default value, if needs to recurse through sub folders

        Returns:
            list    -   list of the folders present at the given path

        Raises:
            Exception:
                if path is not valid

                if failed to get the list of folders

        """
        return self._get_files_or_folders_in_path(folder_path, 'FOLDER', recurse)

    def get_folder_or_file_names(self, folder_path, filesonly=True):
        """Returns the list of files / folders present inside the given folder path on the client.

        Args:
            folder_path     (str)   --  folder path to get the list of files / folders from

            filesonly       (bool)  --  boolean flag to specify whether to get files or folders

        Returns:
            list    -   returns the list of all the files / folders present inside the
            given path based on the **filesonly** flag

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to get list of folders available in the path

        """
        if filesonly:
            cmd = "Get-ChildItem -file {}  | Select-Object Name".format(folder_path)
        else:
            cmd = "Get-ChildItem -dir {}  | Select-Object Name".format(folder_path)

        output = self.execute_command(cmd)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.output

    def get_files_and_directory_path(self, folder_path):
        """Returns the list of files and its directory paths present inside the given
        folder path on the client.

        Args:
            folder_path     (str)   --  folder path to get the list of files
        Returns:
            list    -   returns the list of all the files and its directory present inside the
            given path

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to get list of folders available in the path

        """

        cmd = "Get-ChildItem '{}' -Recurse | Format-List DirectoryName, Name".format(folder_path)
        output = self.execute_command(cmd)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.output

    def number_of_items_in_folder(self, folder_path, include_only='all', recursive=False, filter_name=None):
        """Returns the count of number of items in a folder

            Args:
                folder_path       (str)   --  The folder path to get the count for

                include_only      (str)   --  The type of item to include for counting. Supported values:
                "files" - count only files, "folders" - count only folders, "all" - count both files and folders

                recursive         (bool)  --  Decides to whether to count items recursively in the sub folders

                filter_name       (str)   --  Filter items based on a pattern and include for counting. Example: *.mp3

            Returns:
                (int)   --  Count of number of items in the folder

            Raises:
                Exception: if failed to execute the command

        """

        parameter_type = ''
        if include_only == 'files':
            parameter_type = '-File'
        elif include_only == 'folders':
            parameter_type = '-Directory'

        parameter_recursive = '-Recurse' if recursive else ''
        parameter_filter = '' if not filter_name else f' -Filter "{filter_name}"'

        cmd = f'(Get-ChildItem -Path "{folder_path}" {parameter_type} {parameter_recursive} {parameter_filter} ' \
              f'| Measure-Object).Count'
        output = self.execute_command(cmd)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        try:
            return int(output.formatted_output)
        except ValueError:
            return 0

    def add_firewall_allow_port_rule(self, tunnel_port):
        """Adds the inbound rule for the given port number

        Args:
            tunnel_port (int): port number to be added in the inbound rule

        Returns:
            None: if rule addition is successful

        Raises:
            Exception:
                if command to add the firewall rule fails

        """

        cmd = (
            r'netsh advfirewall firewall add rule name="Allow_{0}" dir=in'
            r' action=allow enable=yes profile=any localport={1} protocol=tcp'
        ).format(
            str(tunnel_port), str(tunnel_port)
        )

        result = self.execute_command(cmd)

        if not (result.exception_message is None and "Ok" in str(result.output)):
            raise Exception("Failed to add inbound rule on windows firewall on client: " +
                            result.exception_message)

    def start_firewall(self, block_connections=False):
        """start firewall services on the current client machine

        Args:
            block_connections (bool) -- Blocks all inbound and outbound connections

        Returns:
            None: if firewall started successfully

        Raises:
            Exception:
                if command to start firewall service fails or connection rules are failed to set

        """
        cmd = "netsh advfirewall set allprofiles state on"
        result = self.execute_command(cmd)
        if not (result.exception_message is None and "Ok" in str(result.output)):
            raise Exception("Failed to enable windows firewall on client computer: " +
                            result.exception_message)
        if block_connections:
            cmd = "cmd /c $(\"netsh advfirewall set allprofiles firewallpolicy blockinbound,blockoutbound\")"
            result = self.execute_command(cmd)
            if not (result.exception_message is None and "Ok" in str(result.output)):
                raise Exception("Failed to set inbound and outbound connection rules on client computer: " +
                                result.exception_message)

    def remove_firewall_allow_port_rule(self, tunnel_port):
        """removes the inbound rule for the given port number

        Args:
            tunnel_port (int): port number to be removed in the inbound rule

        Returns:
            None: if rule deletion is successful

        Raises:
            Exception:
                if command to delete the firewall rule fails

        """
        cmd = r'netsh advfirewall firewall delete rule name="Allow_{0}"'.format(str(tunnel_port))

        result = self.execute_command(cmd)
        if result.exception_message is not None:
            raise Exception("Failed to delete inbound rule on windows firewall on client: " +
                            result.exception_message)

    def stop_firewall(self):
        """turn off firewall service on the current client machine

        Returns:
            None: firewall is turned off successfully

        Raises:
            Exception:
                if command to turn off firewall fails

        """
        cmd = "netsh advfirewall set allprofiles state off"
        result = self.execute_command(cmd)
        if result.exception_message is not None:
            raise Exception("Failed to remove windows firewall on client computer: " +
                            result.exception_message)

    def add_firewall_machine_exclusion(self, machine_to_exclude=None):
        """Adds given machine to firewall exclusion list. If machine details is
           not passed, it considers current machine and adds it to exclusion list.

        Args:
            machine_to_exclude (str): hostname or IP address to be added to
                firewall exclusion list

        Returns:
            None: if machine is successfully added to firewall exclusion list

        Raises:
            Exception:
                if command to add the firewall exclusion rule fails

        """
        if machine_to_exclude is None:
            machine_to_exclude = socket.gethostbyname(socket.gethostname())

        cmd = r'netsh advfirewall firewall add rule name="Exclude_Machine" dir=in ' \
              r'action=allow remoteip="{0}"'.format(machine_to_exclude)

        res = self.execute_command(cmd)
        if not (res.exception_message is None and "Ok" in str(res.output)):
            raise Exception(
                "Failed to exclude machine_to_exclude on remote client computer: " +
                res.output)

    def remove_firewall_machine_exclusion(self, excluded_machine):
        """removes given machine from firewall exclusion list. If machine details is
           not passed, it considers current machine and removes it from exclusion list.

        Args:
            excluded_machine (str): hostname or IP address to be removed from
                firewall exclusion list

        Returns:
            None: if machine is successfully removed from firewall exclusion list

        Raises:
            Exception:
                if command to delete from firewall exclusion rule fails

        """
        cmd = "netsh advfirewall firewall delete rule Exclude_Machine"
        res = self.execute_command(cmd)
        if res.exception_message is not None:
            raise Exception("Failed to remove automation machine from "
                            "exclusion list on remote client: " +
                            res.exception_message)

    def disconnect(self):
        """Disconnects the current session with the machine."""
        if self.is_commvault_client:
            # Reset the Execution Policy of the client
            __ = self.client_object.execute_command(
                f'powershell.exe Set-ExecutionPolicy {self._execution_policy} -Force'
            )
        elif self.is_local_machine:
            __ = subprocess.run(
                f'powershell.exe Set-ExecutionPolicy {self._execution_policy} -Force',
                stdin=subprocess.PIPE
            )

        super(WindowsMachine, self).disconnect()

    def toggle_time_service(self, stop=True):
        """
        Toggles the state of the windows time service
        Args:
            stop:  (bool) -- If set to True will stop the service else will start the service

        Returns:
                None: if Windows time service state is toggled successfully

            Raises:
                Exception:
                    If Time service state was not toggled successfully

        """
        if stop:
            self._log.info("Stopping Time Service")
            service_command = "net stop w32time;Set-Service -Name W32Time -StartupType disabled"
            expected_output = ["stopped successfully", "not started"]
        else:
            self._log.info("Starting Time Service")
            service_command = ("Set-Service -Name W32Time -StartupType automatic;"
                               "net start w32time; w32tm /resync")
            expected_output = ["started successfully", "already been started"]
        service_output = self.execute_command(service_command)
        if not any((x in service_output.output or x in service_output.exception)
                   for x in expected_output):
            raise Exception("Time service could not be toggled successfully with exception: {0}"
                            .format(service_output.exception_message))
        self._log.info("Time service operation completed successfully")

    def current_time(self, timezone_name=None):
        """
        Returns current machine time in UTC TZ as a datetime object

        Args:
            timezone_name:  (String) -- pytz timezone to which the system time will be converted
                                        if not specified will return in UTC

        Returns:
                datetimeobj -- machine's current time

        Raises:
                Exception:
                    If not able to fetch current time

        """
        from pytz import timezone
        try:
            time_output = self.execute_command("$a = Get-Date; "
                                               "$a.ToUniversalTime()."
                                               "ToString(\"dd-MM-yyyy HH:mm:ss\")")
            current_time = datetime.datetime.strptime(time_output.output.strip(), "%d-%m-%Y %H:%M:%S")
            current_time = timezone('UTC').localize(current_time)
            if timezone_name and timezone_name != 'UTC':
                current_time = current_time.astimezone(timezone(timezone_name))
            return current_time
        except Exception as e:
            raise Exception("\n Current Time could not be fetched with exception: {0}".format(e))

    def current_localtime(self):
        """returns current machine timezone as a datetime.timezone object

        Args:
            none
        Returns:
            localtime

        Raises:
            Exception:
                If not able to fetch localtime
        """
        try:
            time_output = self.execute_command("$a = Get-Date; "
                                               "$a.ToString(\"dd-MM-yyyy HH:mm:ss\")")
            current_localtime = datetime.datetime.strptime(time_output.output.strip(), "%d-%m-%Y %H:%M:%S")
            return current_localtime
        except Exception as e:
            raise Exception("\n Local Time could not be fetched with exception: {0}".format(e))

    def scan_directory(self, path, filter_type=None, recursive=True):
        """Scans the directory and returns a list of items under it along with its properties

            Args:
                path            (str)           Path of directory to scan

                filter_type     (str)          Filters the list by item type. Possible values
                are file, directory

                recursive       (bool)          Decides to whether to get items recursively or from
                current directory alone

            Returns:
                list    -       List of items under the directory with each item being a
                dictionary of item properties

        """

        scanned_items = []
        script_arguments = {
            'path': path,
            'recursive': 'yes' if recursive else 'no'
        }

        self._script_generator.script = SCAN_DIRECTORY

        scan_test_data = self._script_generator.run(script_arguments)
        output = self.execute(scan_test_data)
        os.unlink(scan_test_data)

        items = output.output.split('\n')

        for item in items:

            item = item.strip()
            i_props = item.split('\t')

            if item == '':
                continue

            if len(i_props) != 4:
                raise Exception(
                    'Some properties are missing for item [{0}]'.format(str(i_props)))

            if filter_type is not None and filter_type != i_props[1]:
                continue

            scanned_items.append({
                'path': i_props[0],
                'type': i_props[1],
                'size': i_props[2],
                'mtime': i_props[3]
            })

        return scanned_items

    def get_file_attributes(self, file_path):
        """Gets the attributes of a file on the client.

            Args:
                file_path   (str)   --  path of the file to get the size of

            Returns:
                string   -   file attributes info

            Raises:
                Exception(Exception_Code, Exception_Message):
                    if failed to get the size of the file

        """
        self._script_generator.script = GET_FILE_ATTRIBUTES
        data = {
            'FilePath': file_path,
        }
        get_file_attributes_script = self._script_generator.run(data)
        output = self.execute(get_file_attributes_script)
        os.unlink(get_file_attributes_script)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.formatted_output

    def get_acl_list(self, data_path, sorted_output=True):
        """Gets the list of acl of items from the machine on a give path

              Args:
                 data_path     (str)   -- data folder path to get the acl list

                 sorted_output (bool)  --  to specify whether
                                           the acl list should be sorted.
                                           default is True
                                           mean the output result is sorted
             Returns:
                 list    -   list of acl of items

             Raises:
                 Exception:
                     if any error occurred while getting the acl of items.
         """
        try:
            acl_data = self.get_test_data_info(data_path, acls=True)
            acl_list = acl_data.split('\r\n')
            while '' in acl_list:
                acl_list.remove('')

            if sorted_output:
                acl_list.sort()

            return acl_list

        except Exception as excp:
            raise Exception(
                "Error occurred at getting ACL from machine {0}".format(excp))

    def compare_acl(self, source_path, destination_path):
        """Compares the acl of source path with destination path
             and checks if they are same.

              Args:
                 source_path         (str)  -- source path to compare

                 destination_path    (str)  -- destination path to compare

            Returns:
                 bool, str   -   Returns True
                                  if acls of source and destination are same
                                 diff output between source and destination
            Raises:
                 Exception:
                     if any error occurred while comparing the acl of paths.
        """

        try:
            source_list = self.get_acl_list(source_path)
            destination_list = self.get_acl_list(destination_path)
            return self._compare_lists(source_list, destination_list)
        except Exception as excp:
            raise Exception(
                'Error occurred while comparing the acls: ' + str(excp))

    def is_stub(self, file_name, is_nas_turbo_type=False):
        """
        This function will windows file's attributes
        to check whether file is stub
        Args:

            file_name (str): file full name

            is_nas_turbo_type  (bool): True for NAS based client.

        Return: True is the file is stub otherwise return False
        Raises:
            Exception:
                    if error occured

        """

        if is_nas_turbo_type:
            _stub_file_attributes = set(['OFFLINE'])
        else:
            _stub_file_attributes = set(['OFFLINE', 'SPARSEFILE', 'REPARSEPOINT'])

        try:
            _ret_val = self.get_file_attributes(file_name)
            _ret_val_list = _ret_val.replace(r'\r\n', '').split(',')
            _washed_list = []
            for _each_item in _ret_val_list:
                _washed_list.append(_each_item.strip(' ').upper())

            return bool(_stub_file_attributes.issubset(set(_washed_list)))

        except Exception as excp:
            raise Exception("exception raised on with error %s" % str(excp))

    def set_logging_debug_level(self, service_name, level='5'):
        """set debug log level for given CV service name.

              Args:
                 service_name         (str)  -- name of valid CV service name

                 level                (str)  -- log level to be set
                        default : 5

            Returns:
                 None
            Raises:
                 Exception:
                     if any error occurred while updating debug log level
        """
        self.create_registry(
            'EventManager',
            value=service_name +
                  '_DEBUGLEVEL',
            data=level,
            reg_type='DWord')
        self.create_registry(
            'EventManager',
            value=service_name + '_DEBUGLEVEL_UNTIL',
            data=int(time.time()) + 7 * 86400,
            reg_type='DWord')

    def set_logging_filesize_limit(self, service_name, limit='5'):
        """set debug log level for given CV service name.

                      Args:
                         service_name         (str)  -- name of valid CV service name

                         limit                (str)  -- file size in MB , default : 5
                    Returns:
                         None
                    Raises:
                         Exception:
                             if any error occurred while updating debug log level
        """
        self.create_registry(
            'EventManager',
            value=service_name +
                  '_MAXLOGFILESIZE',
            data=limit,
            reg_type='DWord'
        )

    def delete_task(self, taskname):
        """ Deletes the specified task on the client
            Args:
                taskname (str): Taskname to delete

            Returns:
                Output for the task execution command
        """
        task = "schtasks /Delete /TN " + taskname + " /F"
        self._log.info("Deleting task on client [%s]: [%s]", task, self.machine_name)
        return self.execute_command(task)

    def wait_for_task(
            self,
            taskname,
            taskstatus='Ready',
            retry_interval=20,
            time_limit=15,
            hardcheck=True):
        """ Wait for scheduled task to complete on client

            Args:
                taskname          (str)    -- Name of the task to check for completion

                taskstatus        (str)    -- Expected task status
                                                'Running' OR 'Ready'

                retry_interval    (int)    -- Interval (in seconds), checked in a loop. Default = 2

                time_limit        (int)    -- Time limit to check for. Default (in minutes) = 15

                hardcheck         (bool)   -- If True, module will exception out if task is not complete.
                                              If False, module will return with non-truthy value

            Returns:
                True/False        (bool)   -- In case task is Ready/Not Ready

            Raises:
                Exception if :

                    - failed during execution of module
                    - Task did not reach the expected state

        """
        try:
            task_output = []
            time_limit = time.time() + time_limit * 60
            while True:
                command = "schtasks /Query /TN \"" + taskname + "\" /FO LIST"
                command_output = self.execute_command(command)
                task_output = "".join(
                    [s for s in command_output.output.strip().splitlines(True) if s.strip()])

                if taskstatus in task_output or time.time() >= time_limit:
                    break

                self._log.info("Waiting for [%s] seconds. Task status [%s]", retry_interval, task_output)
                time.sleep(retry_interval)

            if taskstatus not in task_output:
                if not hardcheck:
                    return False

                raise Exception(
                    "Task [{0}] did not reach expected state [{1}]".format(
                        taskname, taskstatus))

            self._log.info("Task [%s] expected state:[%s] reached.", taskname, taskstatus)
            self._log.info("Task state: [%s]", task_output)
            return True

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def create_task(self, taskoptions):
        """ Create a scheduled task on the machine
            Args:
                taskoptions     (str)    : Task options for the schtasks /create command

            Returns:
                Output for the task execution command
        """
        task = ''.join([r'schtasks /Create ', taskoptions])
        self._log.info("Creating task on client [%s]: [%s]", self.machine_name, task)
        output = self.execute_command(task)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)
        return output

    def execute_task(self, taskname):
        """ Executes a scheduled task immediately on the machine
            Args:
                taskname     (str)    : Task name to execute

            Returns:
                Output for the task execution command
        """
        task = "schtasks /Run /TN " + taskname
        self._log.info("Executing task on client [%s]: [%s]", self.machine_name, task)
        return self.execute_command(task)

    def has_active_session(self, username):
        """ Check if a user has an active session on the Machine
            Args:
                username     (str)    : User Name for which to check the active user session

            Returns:
                True if user has an active session
                False if not
        """
        user = username[username.index("\\") + 1:] if '\\' in username else username
        machine = self.machine_name
        query_user = "query session " + user
        session_output = self.execute_command(query_user)
        if session_output.exception_message is None:
            session_info = session_output.formatted_output
            username_index = session_info.find(user)
            if username_index != -1:
                if session_info.find("Active") == -1:
                    self._log.error("Failed to get active session for the user [{0}] on client [{1}]"
                                    .format(username, machine))
                else:
                    self._log.info("Active session found for user [{0}] on client [{1}]".format(username, machine))
                    return True
            else:
                self._log.error("No active session entry for the user [{0}] was found".format(username))
        else:
            self._log.error("Failed to get active session information for user [{0}]".format(username))

        return False

    def get_login_session_id(self, username):
        """ Gets the session id for the logged in user
            Args:
                username     (str)    : User Name for which to check the active user session

            Returns:
                user's session id (int)

            Raises:
                Exception: If failed to get session id for the user
        """
        self._log.info("Getting session id for the user [{0}]".format(username))
        username = username[username.index("\\") + 1:] if '\\' in username else username
        command = "query session " + username + " |select -skip 1|%{$_.SubString(41,5).Trim()}"
        output = self.execute_command(command)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)
        self._log.info("Session id for the user [{0}] is [{1}]".format(username, output.formatted_output))
        return output.formatted_output

    def logoff_session_id(self, sessionid):
        """ Logs off a user with given session id

            Args:
                sessionid (str): Active OR Disconnected user session id of the user

            Raises:
                Exception: If failed to logg off user
        """
        self._log.info("Logging off user session [{0}] on the client [{1}]".format(sessionid, self.machine_name))
        output = self.execute_command("logoff " + sessionid)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)
        return output

    def lock_file(self, file=None, **kwargs):
        """Locks a file on the client machine, thus causing the file to get failed during backup without VSS.
        To unlock the file locked using this method, execute the PS command Stop-Process -Id <Process_ID>

        Args:
            file    (str)   --  Name of the file that needs to be locked.

            \*\*kwargs  (dict)  --  Optional arguments

            Available kwargs Options:
                interval        (int)   :   Specifies the interval (in seconds) for which the file needs to be locked.

                    default : 60 (in seconds)

                file_list       (list)  :   Specifies a list of files which need to be locked.

                shared_read_write   (bool) : Opens a handle on the file in shared read and shared write mode, leaving
                the file to be backed up partially, i.e. file is backed up as it's being updated.

        Returns:
            int  - Process ID of the PS Session that has locked the file.

        Raises:
            Exception:
                If an error occurred when trying to lock the file.

        """

        file_list = [file] if file else kwargs.get('file_list', None)
        if not file_list:
            msg = "Either file or file_list has to provided. Both cannot be empty."
            raise Exception(msg)

        interval = kwargs.get('interval', 60)

        # FOR INFO ON HANDLE, REFER https://docs.microsoft.com/en-us/dotnet/api/system.io.file.open
        if kwargs.get('shared_read_write'):
            handle = "'Open', 'ReadWrite', 'ReadWrite'"
        else:
            # Read FOR EXCLUSIVE LOCK DOES NOT WORK ON Windows Server 2019, CHANGING IT TO ReadWrite ONLY FOR THIS OS.
            handle = "'Open', 'ReadWrite', 'None'" if "Windows Server 2019" in self.client_object.os_info else "'Open', 'Read', 'None'"

        pid_list = []
        for file in file_list:
            cmd = f"Start-Process -FilePath powershell.exe -ArgumentList \"[System.IO.File]::Open('{file}', {handle}) " \
                  f"| Out-Null ; Start-Sleep -Seconds {interval}\" -PassThru " \
                  f"| Format-Table -HideTableHeaders -Property @{{e={{$_.Id}}}} | Out-String"

            output = self.execute_command(cmd)

            if output.exception_message:
                raise Exception(output.exception_code, output.exception_message)
            elif output.exception:
                raise Exception(output.exception_code, output.exception)

            pid_list.append(int(output.formatted_output))

        if len(pid_list) == 1:
            return pid_list[0]
        return pid_list

    def block_tcp_port(self, port, time_interval=600, **kwargs):
        """blocks given tcp port no on machine for given time interval

            Args:

                port            (int)   --  Port no to block

                time_interval   (int)   --  time interval upto which port will be blocked

            kwargs Options:

                is_sql_port_lock    (bool)  --   Specifies whether this operation is for blocking sql dynamic port

            Returns:

                None

            Raises:

                Exception:

                    if failed to block the port
        """
        is_sql_port_lock = kwargs.get('is_sql_port_lock', False)
        script_arguments = {
            'port': port,
            'time': time_interval,
            'issql': 'yes' if is_sql_port_lock else 'no'
        }
        self._script_generator.script = BLOCK_PORT
        block_port = self._script_generator.run(script_arguments)
        existing_process = self.get_process_id(process_name='powershell.exe')
        _thread = threading.Thread(target=self.execute,
                                   args=(block_port, None))
        _thread.start()
        # wait for above thread to complete its script execution
        time.sleep(30)
        if is_sql_port_lock:
            # wait for cvd thread to update back new port to all webserver via
            # workqueue req. default is 5mins so let's wait for 2X time
            time.sleep(10 * 60)
        cmd = f"Get-NetTCPConnection -State Listen -LocalPort {port} | select OwningProcess"
        output = self.execute_command(cmd)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)
        elif 'No matching MSFT_NetTCPConnection' in output.output:
            raise Exception("Failed to block tcp port")
        pid_list = []
        if not isinstance(output.formatted_output, str):
            for pid in output.formatted_output:
                pid_list.append(pid[0])
        elif output.formatted_output != '':
            pid_list.append(output.formatted_output)
        pid_list = list(set(pid_list))
        new_process = self.get_process_id(process_name='powershell.exe')
        if pid_list[0] not in new_process:
            raise Exception("No new process found for blocked port")
        elif pid_list[0] in existing_process:
            raise Exception("Blocked port process id exists even before blocking")
        os.unlink(block_port)

    def get_hardware_info(self):
        """ returns the hardware specifications of this machine like cores/Logical processor count/RAM/Architecture

        Returns:

            dict        --  containing all the CPU hardware info

                    Example : {
                                  "MachineName": "xyz",
                                  "CPUModel": "Intel(R) Xeon(R) CPU E5-2450 0 @ 2.10GHz",
                                  "NumberOfCores": "5",
                                  "NumberOfLogicalProcessors": "5",
                                  "OSArchitecture": "64",
                                  "MaxClockSpeed": "2100",
                                  "RAM": "13GB",
                                  "OS": "WINDOWS",
                                  "OSFlavour": "Windows 2012 R2",
                                  "Storage": {
                                    "total": 614297.6,
                                    "available": 305438.72,
                                    "C": {
                                      "total": 614297.6,
                                      "available": 305438.72
                                    }
                                  }
                                }

        Raises:
                Exception:
                    if any error occurred while getting the details

        """
        cmd = f"Get-WmiObject -class Win32_processor | " \
              f"Format-List @{{ Label=\"MachineName\"; Expression={{$_.systemname}}}}," \
              f"@{{ Label=\"CPUModel\"; Expression={{$_.Name}}}}," \
              f"@{{ Label=\"NumberOfCores\"; Expression={{$_.NumberOfCores}}}}," \
              f"@{{ Label=\"NumberOfLogicalProcessors\"; Expression={{$_.NumberOfLogicalProcessors}}}}," \
              f"@{{ Label=\"OSArchitecture\"; Expression={{$_.Addresswidth}}}}," \
              f"@{{ Label=\"MaxClockSpeed\"; Expression={{$_.MaxClockSpeed}}}}"
        output = self.execute_command(command=cmd)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)
        output_list = output.output.split('\r\n')
        output_dict = {}
        separator = ':'
        for i, item in enumerate(output_list):
            if separator not in item:
                continue
            value = item.split(separator)
            output_dict[value[0].strip()] = value[1].strip()
        cmd = f"(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum).sum/1gb"
        output = self.execute_command(command=cmd)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)
        output_dict["RAM"] = f"{output.formatted_output}GB"
        output_dict["OS"] = self.os_info
        output_dict["OSFlavour"] = self.os_flavour
        output_dict["Storage"] = self.get_storage_details()
        return output_dict

    def get_process_id(self, process_name, command_line_keyword=None):
        """ returns the process id for the given process.

        Args:

            process_name                (str)       --  Name of the process

            command_line_keyword        (str)       --  Keyword which needs to be present in command line arguments

        Returns:

            list         --  list of Process id [Empty list if no process is found]

        Raises:

                Exception:

                    if any error occurred while getting the process id

        """
        cmd = f"Get-WmiObject Win32_Process -Filter \"Name = '{process_name}'"
        if command_line_keyword is not None:
            cmd = f"{cmd} AND CommandLine like '%{command_line_keyword}%'"
        cmd = f"{cmd}\" | select ProcessId"
        output = self.execute_command(cmd)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)
        pid_list = []
        if not isinstance(output.formatted_output, str):
            for pid in output.formatted_output:
                pid_list.append(pid[0])
        elif output.formatted_output != '':
            pid_list.append(output.formatted_output)
        success = all(isinstance(process_id, str) and process_id.isnumeric() for process_id in pid_list)
        if success:
            return pid_list
        raise Exception(f"Something went wrong with PID fetch. Output is : {output.formatted_output}")

    def get_process_stats(self, process_id):
        """Gets the process stats like Handle count, memory used, CPU usage, thread count at the requested time
        for the given process ID

            Args:
                process_id      (str)   --      The process ID to get the stats for

            Returns:
                (dict)  --  A dictionary with the stat and it's value (int).
                            Empty dictionary if process ID does not exist.

                Example: {
                    'handle_count': 100,
                    'memory': 456202665  # in bytes
                    'thread_count': 20
                    'cpu_usage': 2
                }

            Raises:
                Exception - If any error while executing the script

        """

        result = {}

        if not process_id:
            return result

        script_arguments = {
            'process_id': process_id
        }

        self._script_generator.script = WINDOWS_GET_PROCESS_STATS

        script = self._script_generator.run(script_arguments)
        output = self.execute(script)
        os.unlink(script)

        if not output.formatted_output.strip():
            return {}

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        all_processes = output.formatted_output.split('\n')  # When process id is 0 we get multiple results
        stats = all_processes[0]

        stats_split = stats.split(',')
        for stat in stats_split:
            stat_data = stat.split('=')
            name = stat_data[0].strip()
            value = stat_data[1].strip()
            try:
                value = int(float(value))
            except ValueError:
                value = 0
            result[name] = value

        return result

    def get_process_dump(self, process_id, dump_path=None, file_name=None):
        """Gets the process dump for the given process ID

            Args:
                process_id      (str)   --      The process ID to get the stats for

                dump_path       (str)   --      The folder where the process dump should be stored. Leave default to
                automatically pick a drive with free space

                file_name       (str)   --      The name of the dump file. Default is process name and process id

            Returns:
                (str)  --  The path of the process dump file

            Raises:
                Exception - If any error while executing the script

            Note:
                We are not using GxAdmin.exe to take process dump to support setups without CV installed. Also,
                process dump operation fails when file name contains space.

        """

        if not process_id:
            raise Exception('No process ID provided to take dump')

        if not dump_path:
            drives_dict = self.get_storage_details()
            dump_path = ''
            for drive in drives_dict:
                if isinstance(drives_dict[drive], dict) and drives_dict[drive]['available'] >= 5120:
                    dump_path = drive + ':\\'
                    break

        if not file_name:
            current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%I-%M-%S-%p')
            file_name = f'%process_name%-%process_id%-{current_timestamp}'

        script_arguments = {
            'process_id': process_id,
            'dump_path': dump_path,
            'file_name': file_name
        }

        self._script_generator.script = WINDOWS_GET_PROCESS_DUMP

        script = self._script_generator.run(script_arguments)
        output = self.execute(script)
        os.unlink(script)

        if not output.formatted_output:
            raise Exception('Unable to get process dump file path. Output [%s]', output.formatted_output)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        dump_file_path = output.formatted_output.strip()
        if not self.check_file_exists(dump_file_path):
            raise Exception('Process dump file not present [%s]. Output [%s]', dump_file_path, output.formatted_output)

        return dump_file_path

    def get_port_usage(self, process_id=None, all_protocols=True):
        """ gets the netstat connection stats for the process or machine

        Args:

            process_id          (str)       --  process id

                if None, then netstat output of machine is returned

            all_protocols       (bool)      --  specifies whether to get tcp & udp connections or only TCP connection
                                                    Default : TRUE

                        if true, both tcp & udp connection details are returned

                        if false, then only tcp connection details are returned

        Returns:

            dict    --  containing connection state and no of connections in those state

        Raises:

            Exception:

                if failed to find the process id

        """
        out_dict = {}
        cmd = f"Get-NetTCPConnection"
        if process_id is not None:
            cmd = f"{cmd} -OwningProcess {process_id}"
        cmd = f"{cmd} | group state -NoElement"
        output = self.execute_command(cmd)
        if output.exception_message and 'No MSFT_NetTCPConnection objects found' not in output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception and 'No MSFT_NetTCPConnection objects found' not in output.exception:
            raise Exception(output.exception_code, output.exception)
        else:
            if isinstance(output.formatted_output, list):
                for state in output.formatted_output:
                    out_dict[state[1]] = state[0]
        if all_protocols:
            cmd = f"Get-NetUDPEndpoint"
            if process_id is not None:
                cmd = f"{cmd} -OwningProcess {process_id}"
            cmd = f"{cmd} | group state -NoElement"
            output = self.execute_command(cmd)
            if output.exception_message and 'No MSFT_NetUDPEndpoint objects found' not in output.exception_message:
                raise Exception(output.exception_code, output.exception_message)
            elif output.exception and 'No MSFT_NetUDPEndpoint objects found' not in output.exception:
                raise Exception(output.exception_code, output.exception)
            else:
                if isinstance(output.formatted_output, list):
                    for state in output.formatted_output:
                        out_dict['UDP'] = state[0]
        return out_dict

    def is_process_running(self, process_name, time_out=0, poll_interval=0):
        """Checks if a given process is running on the index server
            Args:
                process_name(str)   -- Name of the process

                time_out(int)       -- wait for n seconds
                    Default(0)secs

                poll_interval(int)      -- keep checking for process in n secs
                    Default(0)secs

            Returns:
                Boolean result

        """
        try:
            flag = False
            current_time = time.time()
            end_time = current_time + time_out
            while current_time <= end_time:
                cmd = ("(Get-Process | where-object{$_.ProcessName -eq \"%s\"}).Count"
                       % process_name)
                out = self.execute_command(cmd)
                if len(out.exception) == 0 and int(out.output) > 0:
                    self._log.info("Found process running: %s", process_name)
                    flag = True
                    return flag
                elif len(out.exception) > 0:
                    self._log.exception(
                        "Exception code: %s, Exception Message: %s, Output Msg: %s",
                        out.exception_code, out.exception_message, out.output
                    )
                time.sleep(poll_interval)
                current_time = time.time()
            self._log.info("Process not found: %s with in stipulated time: %d ", process_name, time_out)
            return flag
        except Exception as excp:
            raise Exception("Exception raised while is process running: %s" % str(excp))

    def hide_path(self, path):
        """ hides specified path on the machine
                Args:
                    path   (str)   --  path to be hidden on machine

                Returns:
                    None

                Raises:
                    Exception(Exception_Code, Exception_Message):
                        if failed to hidden a file
        """
        command = 'attrib +s +h {0}'.format(path)
        self._log.debug("running command {0} to hide file".format(command))
        output = self.execute_command(command)
        if output.exception:
            raise Exception(output.exception_code, output.exception)

    def unhide_path(self, path):
        """unhides specified path on the machine

                Args:
                    path   (str)   --  path to be unhidded on machine

                Returns:
                    None

                Raises:
                    Exception(Exception_Code, Exception_Message):
                        if failed to unhide a file

         """
        command = 'attrib -s -h {0}'.format(path)
        self._log.debug("running command {0} to unhide file".format(command))
        output = self.execute_command(command)
        if output.exception:
            raise Exception(output.exception_code, output.exception)

    def wait_for_process_to_exit(self, process_name, time_out=600, poll_interval=10):
        """Waits for given process to exit
            Args:
                process_name(str)   -- Name of the process

                time_out(int)       -- wait for n seconds
                    Default(600)secs

                poll_interval(int)      -- keep checking for process in n secs
                    Default(10)secs

            Returns:
                Boolean result

        """
        try:
            flag = False
            current_time = time.time()
            end_time = current_time + time_out
            while current_time <= end_time:
                if not self.is_process_running(process_name):
                    self._log.info("Process exited: %s", process_name)
                    flag = True
                    return flag
                time.sleep(poll_interval)
                current_time = time.time()
            self._log.info("Process didn't exited: %s within stipulated time: %d ", process_name, time_out)
            return flag
        except Exception as excp:
            raise Exception("Exception raised while waiting for process to exit: %s" % str(excp))

    def change_system_time(self, offset_seconds=0):
        """Changes the system time as per the offset seconds provided w.r.t to current system time
           Note: you should remember to deal with windows time service while using this function,
           As even after changing the time, windows time service will revert back the changed time
           to the correct time.


            Args:
                offset_seconds      (int)   --  Seconds to offset the system time.
                Example, 60 will change the system time to 1 minute forward and -180 will change
                system time 3 minutes backward

            Returns:
                None

            Raises:
                Exception, if the powershell command execution fails

        """

        command = 'set-date -date (get-date).AddSeconds({0})'.format(offset_seconds)

        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def lock_files(self, files_list=list(), lock=True, timeout=300):
        """Locks a file on the client machine, thus causing the file to get failed during backup without VSS.
                To unlock the file locked using this method, execute the PS command Stop-Process -Id <Process_ID>

                Args:

                    files_list    (List)   --  list of  files that needs to be locked.

                    lock  (str)  --   to specify option to lock or unlock Optinal arguments

                    interval        (int)   :   Specifies the interval (in seconds) for which
                                                the file needs to be locked.
.

                Raises:

                    Exception:
                        If an error occurred when trying to lock the file.
                """
        file_str = ','.join(map(str, files_list))
        if lock:
            # substitutes the variables into the script and runs it.

            self._script_generator.script = GET_LOCK
            data = {
                'path': file_str,
                'timeout': timeout
            }

            def run_lock_script(testcase, data):
                self._script_generator.run(data)
                lock_script = testcase._script_generator.run(data)
                _ = testcase.execute(lock_script)
                os.unlink(lock_script)

            _thread.start_new_thread(run_lock_script, (self, data))

    def find_lines_in_file(self, file_path, words):
        """Search for lines in a file for the given words

            Args:
                file_path   (str)   --  The path of the file to search words for

                words       (list)  --  The list of words to search for

            Returns:
                The lines found in the file for the given words

            Raises:
                Exception, if the file failed to open

        """

        command = '(get-content -path "{0}" '.format(file_path)

        for word in words:
            if "\"" in word:
                command += " | select-string -pattern '{0}'".format(word)
            else:
                command += ' | select-string -pattern "{0}"'.format(word)
        command += ') -join "`n"'
        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        lines = output.formatted_output
        if isinstance(lines, str):  # When result is one line, it is a string instead of list.
            lines = [lines]
        return lines

    def windows_operation(
            self,
            user,
            path,
            action=None,
            permission=None,
            get_acl=False,
            modify_acl=False,
            folder=False,
            remove=False,
            inheritance="0"):
        """Windows specific operations

                Args:
                    user            (str)   --  User for which ACEs are required

                    path            (str)   --  File or folder path

                    action          (str)   --  Allow or deny for ACEs

                    permission      (str)   --  Permission to set or remove to file

                    get_acl          (bool)  --  To get ACEs of a file for particular user

                    modify_acl       (bool)  --  To add or remove particular ACE for file

                    folder          (bool)  --  To modify  ACE of folder , default is for file

                    remove             (bool)  --  To remove the ACE, default is to add

                    inheritance       (str)  -- 0 - permission will be set only to target folder
                                                1- Permission will be set to target folder
                                                     and only to child folder
                                                    2 -permission will be to target folder,
                                                    all subfolder and files

                Returns:

                        output       -- Depends on the task

                Raises:

                        Exception, if the powershell command execution fails

                """

        script_arguments = {'user': user,
                            'action': action if action else 'no',
                            'permission': permission if permission else 'no',
                            'path': path,
                            'getacl': 'yes' if get_acl else 'no',
                            'modifyacl': 'yes' if modify_acl else 'no',
                            'folder': 'yes' if folder else 'no',
                            'remove': 'yes' if remove else 'no',
                            'targetfolder': inheritance if inheritance else "0"
                            }
        self._script_generator.script = WINDOWS_OPERATION
        windows_operation = self._script_generator.run(script_arguments)

        output = self.execute(windows_operation)
        os.unlink(windows_operation)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.output

    def get_ace(self, user, path):
        """Get ACEs of a file or folder for particular user

        Args:
            user            (str)   --  User for which ACEs are required

            path            (str)   --  File or folder path

        Returns:
            list       -- list of ACEs for that user

        Raises:

                Exception, if the powershell command execution fails


        """

        try:

            self._log.info("Getting ACL of %s for user %s", path, user)
            acl_data = self.windows_operation(user, path, get_acl=True)
            self._log.info("ACE for %s is %s", user, acl_data)
            acl_list = acl_data.split('\r\n')
            while '' in acl_list:
                acl_list.remove('')
            acl_list.sort()

            return acl_list

        except Exception as excp:
            raise Exception("Error occurred at getting ACL from machine {0}".format(excp))

    def modify_ace(
            self,
            user,
            path,
            permission,
            action,
            folder=False,
            remove=False,
            inheritance="0"):
        """Modify ACEs of a file or folder for particular user

        Args:
            user            (str)   --  User for which ACEs are set or remove

            path            (str)   --  File or folder path

            action          (str)   --  Allow or Deny for ACEs
                                        Valid Input-  Allow or Deny

            permission      (str)   --  Permission to set or remove to file
                                        Valid input -Read, ReadAndExeute, Write,Modify,FullControl

            folder          (bool)  --  To modify  ACE of folder , default is for file

            remove          (bool)  --  To remove the ACE, default is to add

            inheritance      (str)  -- 0 - permission will be set only to target folder
                                        1- Permission will be set to target folder
                                        and only to child folder
                                        2 -permission will be to target folder,
                                        all subfolder and files
        Raises:

                Exception, if the powershell command execution fails

        """

        try:
            self._log.info("Modify %s permission for user %s", permission, user)

            response = self.windows_operation(
                user,
                path,
                action,
                permission,
                modify_acl=True,
                folder=folder,
                remove=remove,
                inheritance=inheritance)
            if response is True:
                self._log.info("Successfully modify ACE for %s", path)

        except Exception as excp:
            raise Exception("Error occurred at modify ACL from machine {0}".format(excp))

    def execute_command_unc(self, command, path):
        """Executes a PowerShell command on the machine.

            An instance of the **WindowsOutput** class is returned.

            Output / Exception messages received from command execution are
            available as the attributes of the class instance.

                output_instance.output              --  raw output returned from the command

                output_instance.formatted_output    --  o/p received after parsing the raw output

                output_instance.exception           --  raw exception message

                output_instance.exception_message   --  parsed exception message from the raw o/p


        Args:
            command     (str)   --  PowerShell command to be executed on the machine

            path        (str)   --  UNC path on which command will be executed

        Returns:
            object  -   instance of WindowsOutput class

        Raises:

                Exception, if the powershell command execution fails


                """
        self._script_generator.script = EXECUTE_COMMAND_UNC
        script_arguments = {
            'command': command,
            'path': path
        }
        execute_command_script = self._script_generator.run(script_arguments)

        output = self.execute(execute_command_script)
        os.unlink(execute_command_script)

        return output

    def get_log_file(self, log_file_name, all_versions=False):
        """Returns the contents of a log file.

        Args:
            log_file_name   (str)   --  Name of the log file.

            all_versions    (bool)  --  Whether to parse all the older versions of the log file as well.
            If it's false, it will only read and return the contents of the most recent version of the file.

            **support not yet implemented.**
            **This argument will be ignored and not used till it is implemented**

        Returns:
            str     -   \r\n separated string containing the requested log lines.

        Raises:
            None

        """

        if all_versions:
            raise NotImplementedError("all_versions not implemented yet.")
        return self.read_file(self.join_path(self.client_object.log_directory, log_file_name))

    def get_logs_for_job_from_file(self, job_id=None, log_file_name=None, search_term=None):
        """From a log file object only return those log lines for a particular job ID.

        Args:
            job_id          (str)   --  Job ID for which log lines need to be fetched.
                default -   None

            log_file_name   (bool)  --  Name of the log file in case of cv client else log name along with path
                default -   None

            search_term     (str)   --  Only capture those log lines containing the search term.
                default -   None

        Returns:
            str     -   \r\n separated string containing the requested log lines.

            None    -   If no log lines were found for the given job ID or containing the given search term.

        Raises:
            None

        """
        # GET ONLY LOG LINES FOR A PARTICULAR JOB ID
        # search_term = "  pid      thread_id       date            time         job_id        rest_of_the_line "
        # regex       = " \d+? \s+? [\d\w]+?  \s+? [\d\w/]+?  \s+? [\d\w:] \s+? re.escape(job_id) \s  .* "
        log_file_path = None
        if job_id is None:
            log_line_ptrn = r"\d+?\s+?[\d\w]+?\s+?[\d\w/]+?\s+?[\d\w:]+?\s.*"
        else:
            log_line_ptrn = r"\d+?\s+?[\d\w]+?\s+?[\d\w/]+?\s+?[\d\w:]+?\s+?" + \
                re.escape(job_id) + r"\s.*"
        if self.client_object:
            log_file_path = self.join_path(
                self.client_object.log_directory, log_file_name)
        else:
            log_file_path = log_file_name
        job_log_lines = self.read_file(
            log_file_path, search_term=log_line_ptrn).split("\r\n")

        # IF A SEARCH TERM IS SPECIFIED, GET ONLY THOSE LOG LINES FOR THE GIVEN JOB ID CONTAINING THE SEARCH TERM
        if search_term and job_log_lines != "":
            job_log_lines_with_search_term = ""
            for line in job_log_lines:
                if line.find(search_term) != -1:
                    job_log_lines_with_search_term = "".join((job_log_lines_with_search_term, line, "\r\n"))
            job_log_lines = job_log_lines_with_search_term

        if job_log_lines != "":
            return job_log_lines

    def get_time_range_logs(self, file_path, start_time, end_time="", search=""):
        """Retrieves log lines from a file within a specified time range.

            Args:
                file_path (str): The path to the log file.
                start_time (str): The start time for filtering log lines format 'mm/dd HH:MM:SS'.
                end_time (str, optional): The end time for filtering log lines. If empty, retrieves all logs till the current time. Defaults to "".
                search (str, optional): A search term to filter log lines. Defaults to "".
        
            Returns:
                str: The log lines within the specified time range.
        
            Raises:
                Exception: If there is an error reading the log file or processing the log lines.
        """
        self._script_generator.script = CV_TIME_RANGE_LOGS
        if search:
            search = search.replace("'", "''")
        data = {
            'log_file': file_path,
            'start_time': start_time,
            'end_time': end_time,
            'search': search
        }
        script = self._script_generator.run(data)

        output = self.execute(script)
        os.unlink(script)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exit_code != 0:
            raise Exception(f"Error occurred while fetching logs: {output.output}")
    
        return output.output
    def get_cpu_usage(self, client, interval, totaltime, processname, outputpath, wait_for_completion):
        """Gets the CPU usage for a process on the remote machine in given intervals for given total time.

        Args:
            client (obj)           -- Client object for a remote machine
            interval (int)         -- interval in seconds for which it will get the cpu usage for a process
            totaltime (int)        -- total counters that needs to be generated
            processname (str)      -- Process name for which cpu usage to be generated.
            outputpath  (str)      -- Output path to which the generated output to be written
            wait_for_completion (boolean)   -- Waits until the command completes

        Return: Return True if the command is executed

        """

        self._log.info("Getting cpu performance counters for Windows machine on process %s", processname)
        cmd = 'typeperf  "\Process("' + processname + '")\% Processor Time" > config.txt typeperf -cf C:\\config.txt -o ' + \
              outputpath + ' -f CSV -y -si ' + str(interval)
        client.execute_command(cmd, wait_for_completion=wait_for_completion)
        return True

    def get_file_owner(self, file_path):
        """Get the owner of the file
            Args:
                file_path(str)   -- Path of the file

            Returns:
                String name of the owner result"""
        try:
            command = 'Get-Item "' + file_path + '" | fl @{N="Owner";E={$_.GetAccessControl().Owner}}'
            output = self.execute_command(command)
            if len(output.exception) != 0:
                raise Exception("Exception while getting owner through powershell")
            output = output.output.split("Owner : ")
            return str(output[1]).strip()
        except Exception as excp:
            raise excp

    def get_system_time(self):
        """Gets the system time for a 24 hour format

        Returns:
            String with hours and minutes in it in 24 hour format

        Raises:
            Exception, if the powershell command execution fails

        """

        command = 'get-date -Format HH:mm'

        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.output

    def restart_iis(self):
        """Restarts iis on the machine

        Raises:
            Exception, if the powershell command execution fails

        """

        output = self.execute_command("iisreset")

        if 'Internet services successfully restarted' not in output.formatted_output:
            raise Exception("iisreset was not successful")
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def add_minutes_to_system_time(self, minutes=1):
        """Adds specified number of minutes to current system time
            Args:
                minutes(int)   -- Minutes to add
                    Default - 1

            Raises:
                Exception, if the powershell command execution fails

            Returns:
                String name of the owner result"""
        command = '(get-date).AddMinutes({0}).ToString("HH:mm")'.format(minutes)

        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.output

    def add_days_to_system_time(self, days=1):
        """Adds specified number of days to current system time
            Args:
                minutes(int)   -- Days to add
                    Default - 1

            Raises:
                Exception, if the powershell command execution fails

            Returns:
                String name of the owner result"""
        current = self.current_time()
        new_date = current + datetime.timedelta(days)
        command = 'set-date -date "{0}"'.format(new_date)

        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def get_active_cluster_node(self, cluster_name):
        """This method return active windows cluster active node

        Args:
            cluster_name          (str)   --   Cluster client name

        Returns:
            active_node     -   returns Active node Cluster

        Raises:
            None

        """
        cmd = "Get-WMIObject Win32_ComputerSystem -ComputerName {0} ".format(cluster_name)
        output = self.execute_command(cmd)
        active_node = None
        li = output.formatted_output.split("\n")
        for element in li:
            if element.startswith('Name'):
                mylist = element.split(":")
                active_node = mylist[1].replace('\r', '').strip()
        return active_node

    def get_cluster_nodes(self, cluster_name):
        """Returns all cluster nodes

        Args:
            cluster_name          (str)   --   Cluster client name

        Returns:
            nodes        (list)     --   Returns all cluster nodes

        Raises:
            None

        """
        cmd = "Get-ClusterNode"
        nodes = list()
        output = self.execute_command(cmd)
        for i in output.formatted_output:
            nodes.append(i[0])
        return nodes

    def do_failover(self, active_node=None, passive_node=None, cluster_group=None):
        """Run Failover

        Args:
            active_node          (str)   --   Active cluster node

            passive_node          (str)  --   Passive  cluster node

            cluster_group          (str)  --   CLuster group/role name

        Returns:
            None

        Raises:
            Exception, if the powershell command execution fails

        """
        if cluster_group:
            self._script_generator.script = DO_CLUSTER_GROUP_FAILOVER
            data = {
                'clustergroup': cluster_group
            }
        else:
            self._script_generator.script = DO_CLUSTER_FAILOVER
            data = {
                'activenode': active_node,
                'passivenode': passive_node
            }

        self._script_generator.run(data)
        lock_script = self._script_generator.run(data)
        output = self.execute(lock_script)
        os.unlink(lock_script)
        if output.exception_message:
            raise Exception(output.exception_code,
                            output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def get_subnet(self):
        """

        Get subnet mask of the machine

        Returns: (str) subnet mask
        """
        command = "ipconfig /all | find 'Subnet Mask'"
        command_op = self.execute_command(command)
        op = command_op.formatted_output.split(":")[1]
        return op

    def get_default_gateway(self):
        """"

        Get default gateway of the machine

        Returns: (str) Default Gateway
        """
        command = "ipconfig /all | find 'Default Gateway'"
        command_op = self.execute_command(command)
        op = command_op.formatted_output.split(":")[1]
        return op

    def is_dhcp_enabled(self):
        """

        Whether DHCP is enabled on the machine
        Returns: (bool) DHCP enabled
        """
        command = "ipconfig /all | find 'DHCP Enabled'"
        command_op = self.execute_command(command).formatted_output
        for dhcp_line in command_op.split("\r\n"):
            op = dhcp_line.split(":")[-1].lower().strip()
            if op == "yes":
                return True
        return False

    def get_dns_servers(self):
        """

        Gets all DNS servers from the machine
        Returns: (list) DNS servers
        """
        command = "ipconfig /all"
        output = self.execute_command(command).formatted_output
        adapters = [line.strip() for idx, line in enumerate(output.split("\r\n\r\n")) if idx % 2 != 0]
        dns = []
        for adapter in adapters:
            lines = [line.strip() for line in adapter.split("\r\n")]
            block_start_line_nos = [idx for idx, line in enumerate(lines) if '. :' in line]
            for idx, block_start in enumerate(block_start_line_nos):
                if "dns servers" in lines[block_start].lower():
                    # Add the first DNS server to list
                    dns.append(lines[block_start].split(". :")[-1].strip())
                    # Loop for all the next DNS servers till next block is encountered
                    dns_block = (lines[block_start + 1:block_start_line_nos[idx + 1]]
                                 if idx < len(block_start_line_nos) else lines[block_start + 1:])
                    for dns_server in dns_block:
                        dns.append(dns_server.strip())
        return dns

    def add_host_file_entry(self, hostname, ip_addr):
        """

        Add an entry to host file

        Args:
            hostname (str): hostname of the entry

            ip_addr (str): ip address to assign to the hostname

        Raises:
            Exception if host file change fails

        """
        path = r"$Env:windir\System32\drivers\etc\hosts"
        command = f"'\n{ip_addr} \t\t {hostname}' | Out-File -encoding ASCII -append {path}"
        command_op = self.execute_command(command)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)

    def remove_host_file_entry(self, hostname):
        """

        Remove the host file entry by hostname

        Args:
            hostname    (str): hostname of the entry to be removed

        Raises:
            Exception if host file entry change fails
        """
        path = r"$Env:windir\System32\drivers\etc\hosts"
        hostname = fr"\b{hostname}\b"  # Remove only the entry that exactly matches with hostname.
        command = f'(Get-Content {path} | Select-String -pattern "{hostname}" -NotMatch) |' \
                  f' Out-File -encoding ASCII {path}'
        command_op = self.execute_command(command)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)

        # Remove Blank lines
        command = f'(gc {path}) | ? ' + '{$_.trim() -ne "" }' + f'| set-content {path}'
        command_op = self.execute_command(command)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)

    def copy_file_locally(self, source, destination):
        """
        Copies file from one directory to another
        Args:
            source(str)         --  Source file path
            destination(str)    --  destination file path
        Raises:
            Exception when copy file fails
        """
        command = f"echo F | xcopy '{source}' '{destination}' /E /I /y"
        command_op = self.execute_command(command)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)

    def change_hostname(self, new_hostname):
        """
        Changes the hostname of the given windows machine
        Args:
            new_hostname(str)   -   new hostname

        Returns:
            bool    - true/false on hostname change of the client

        Raises:
            Exception when changing hostname fails
        """
        command = f"Rename-Computer -NewName {new_hostname} -force"
        command_op = self.execute_command(command)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)

    def add_to_domain(self, domain_name, username, password):
        """
        adds a given windows machine to domain
        Args:
            domain_name(str)    -   name of the domain
            username(str)       -   Username for the domain controller
            password(str)       -   password for the domain controller

        Raises:
            Exception,  if client is already part of the domain
                        if client addition to domain fails
        """
        check_domain_command = f"wmic computersystem get domain | findstr /V 'Domain'"
        command_op = self.execute_command(check_domain_command)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)
        old_domain_name = command_op.formatted_output.strip()
        if old_domain_name != "WORKGROUP":
            raise Exception("Given Machine is already part of a domain")
        add_domain_command = f"Add-Computer -DomainName '{domain_name}' " \
                             "-Credential (New-Object System.Management.Automation.PSCredential " \
                             f"-ArgumentList '{domain_name}\\{username}', (ConvertTo-SecureString {password} -AsPlainText -Force))"
        command_op = self.execute_command(add_domain_command)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)

    def disable_ipv6(self):
        """
        disables IPv6 address for the machine
        Raises:
            Exception when disable IPV6 on network adapter fails
        """
        disable_ip_v6_cmd = "Get-NetAdapter | ForEach-Object {" \
                            "Set-NetAdapterBinding -Name $_.Name -ComponentID ms_tcpip6 -Enabled $False" \
                            "}"
        command_op = self.execute_command(disable_ip_v6_cmd)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)

    def get_hostname(self):
        """
        Gets the hostname of the machine
        Return:
            string containing the hostname of the machine
        """
        cmd = "hostname"
        cmd_output = self.execute_command(cmd)
        return cmd_output.formatted_output

    def get_event_viewer_logs_message(self, newest_n=1):
        """

         Fetches the message body for n newest event viewer logs with Source as "ContentStore"

         Args:
             newest_n (int) : Newest n log messages that have to be fetched

        Raises:
            Exception, if the powershell command execution fails

        Returns: Message body for n newest event viewer Application logs with source ContentStore
        """
        command = "Get-EventLog -LogName Application -Newest 1 -EntryType Information -Source ContentStore | Select-Object -Property Message | Format-Table -Wrap -AutoSize"
        # Execute Command
        execution_output = self.execute_command(command=command)
        if execution_output.exception_message is None:
            output = execution_output.output
            return output
        elif execution_output.exception_message:
            raise Exception(execution_output.exception_code, execution_output.exception_message)

    def list_shares_on_network_path(self, network_path, username, password):
        """
        Lists the shares on an UNC path

        Args:
                network_path    (str)   --  network path of fileserver

                username        (str)   --  username to access the network path

                Ex: DOMAIN\\\\USERNAME

                password        (str)   --  password for above mentioned user

            ** if all inputs are passed as empty, then it will return list of shares on local machine **

            Returns:
                list    -       List of shares on the given network path

            Raises:
                Exception(Exception Name):

                    if failed to mount network path

                    if command returns an exception
        """

        path = network_path
        if not path.startswith('\\\\'):
            path = ''.join(['\\\\', path])

        # if path , username & password is empty, then consider as local machine
        if username != '' and password != '':
            command = 'net use /user:{0} {1} {2}'.format(username, path, password)
            output = self.execute_command(command)
            if output.exception_message is not None:
                raise Exception(output.exception)

        if network_path == '':
            path = f"{path}127.0.0.1"

        output = self.execute_command('net view {0}'.format(path))
        if output.exception_message is not None:
            raise Exception(output.exception)

        temp_list = output.formatted_output
        shares_list = []
        for item in temp_list[:-1]:
            shares_list.append(item[0])

        return shares_list

    def move_file(self, source_path, destination_path):
        """Moves a file item from source_path to destination_path

                Args:
                    source_path   (str)   --  full path of the file to be moved(including file name).

                    destination_path    (str) -- full path of the destination where file to be moved.

                Returns:
                    None    -   if the file was moved successfully

                Raises:
                    Exception:
                        if no file exists at the given path

                        if failed to move the file
        """
        self._log.info("Moving file [%s] to [%s] on client [%s]", source_path, destination_path, self.machine_name)
        command = 'Move-Item -Path "{0}" -Destination "{1}"'.format(source_path, destination_path)
        output = self.execute_command(command)

        self._log.info(output.formatted_output)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def get_vm_ip(self, vm_name=None):
        """
        To get ip address of a VM

        Args:
            vm_name         (str)   -- Name of the VM

        Returns:
            ip address of the vm
       """
        command = f"""(Get-VM -Name {vm_name}|Select -ExpandProperty NetworkAdapters).IPAddresses|where""" \
                  rf"""{{$_ -match "^(?:[0-9]{{1,3}}\.){{3}}[0-9]{{1,3}}$"}}"""
        output = self.execute_command(command)
        if output.exit_code == 0 and output.formatted_output != '':
            self._log.info("IP address of %s is %s", vm_name, output.formatted_output)
            return output.formatted_output
        else:
            raise Exception("Failed to get ip address of %s with exception %s", vm_name, output.exception_message)

    def share_directory(self, share_name, directory, **kwargs):
        """
        To share a directory using NET SHARE

        Args:
            share_name (str) -- Custom name for the share
            directory (str) -- Full network path of the directory to be shared
            **kwargs (dict) -- Available kwargs Options:

                    user     (str)   -- User to grant the permission to (default : everyone)

                    permission (str) -- permission to be granted to the user (default : FULL)
                                        (Options : READ | CHANGE | FULL)

        Returns:
            None: if folder is shared successfully

        Raises:
            Exception:
                if command to share fails

        """
        if kwargs.get('user'):
            user = kwargs.get('user')
        else:
            user = "everyone"
        if kwargs.get('permission'):
            permission = kwargs.get('permission')
        else:
            permission = "FULL"
        cmd = "cmd /c $(\"net share {0}={1} /GRANT:{2},{3}\")".format(share_name, directory, user, permission)
        result = self.execute_command(cmd)
        if not (result.exception_message is None and "{0} was shared successfully".format(share_name)
                in str(result.output)):
            raise Exception("Failed to share " + result.exception_message)

    def unshare_directory(self, share_name):
        """
        To unshare a directory

        Args:
            share_name(str) -- The share name of the net share to be unshared

        Returns:
            None: if folder is unshared successfully

        Raises:
            Exception:
                if command to unshare fails

        """
        cmd = "cmd /c net share {0} /delete /yes".format(share_name)
        result = self.execute_command(cmd)
        if not (result.exception_message is None and "{0} was deleted successfully".format(share_name)
                in str(result.output)):
            raise Exception("Failed to delete share " + result.exception_message)

    def get_share_name(self, directory):
        """
        To get share name of already shared directory

        Args:
            directory   (str)   --  full path string of shared directory

        Returns:
            share_name  (str)   --  Name of the network share for given directory if shared
            None                --  if given directory is not shared
        """
        shares_result = self.execute_command('net share')
        share_directories = shares_result.get_column('name')
        if directory in share_directories:
            row_index = share_directories.index(directory)
            return shares_result.get_column('Share')[row_index]

    def get_logs_after_time_t(self, log_file_name, time_t, search_function=None):
        """
            Fetches logs line after time t, and containing search_function

            Args:
                log_file_name     (str)   --  log_file name

                time_t          (datetime) -- time after which logs required

                search_function (str)     --  any function name to be searched on log lines

            Returns:
                required_log_lines (list) --  list of log lines qualified from search
        """
        required_log_lines = []
        logs = self.get_log_file(log_file_name=log_file_name)
        for line in logs.split("\n"):
            tokens = line.split()
            if len(tokens) < 1 or tokens[0][0] == '*':
                continue
            time_tokens = [int(t) for t in tokens[3].split(":")]
            date_tokens = [int(t) for t in tokens[2].split("/")]
            line_time = time_t.replace(day=date_tokens[1],
                                       month=date_tokens[0],
                                       hour=time_tokens[0],
                                       minute=time_tokens[1],
                                       second=time_tokens[2])
            if line_time < time_t:
                continue

            if search_function:
                res = re.search(search_function, tokens[5])
                if not res:
                    continue

            required_log_lines.append(line)

        return required_log_lines

    def restart_all_cv_services(self):
        """Start all Commvault services using username/password method since SDK cannot talk to the machine
        when services are down. Use SDK service control methods if services are already running.

            Returns:
                None

            Raises:
                Exception while trying to execute command to start the service

        """

        install_directory = self.get_registry_value('Base', 'dBASEHOME')

        command = f'start-process -WorkingDirectory "{install_directory}" ' \
                  f'-FilePath "GxAdmin.exe" ' \
                  f'-ArgumentList "-consoleMode -restartsvcgrp all" -Verb RunAs -Wait'

        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def start_all_cv_services(self, force_start=True):
        """start all Commvault services using username/password method since SDK cannot talk to the machine
        when services are down. Use SDK service control methods if services are already running.

        Args:
            force_start         (bool)  If true, services will be restarted forcefully, even if system time is modified

            Returns:
                None

            Raises:
                Exception while trying to execute command to start the service

        """

        install_directory = self.get_registry_value('Base', 'dBASEHOME')

        argument_list = "-consoleMode -startsvcgrp all "
        if force_start:
            argument_list = argument_list + "-force"

        command = f'start-process -WorkingDirectory "{install_directory}" ' \
                  f'-FilePath "GxAdmin.exe" ' \
                  f'-ArgumentList "{argument_list}" -Verb RunAs -Wait'

        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def stop_all_cv_services(self, force_stop=True):
        """Stops all Commvault services using username/password method.

        Args:
            force_stop         (bool)  If true, services will be stopped forcefully

            Returns:
                None

            Raises:
                Exception while trying to execute command to stop the service

        """

        install_directory = self.get_registry_value('Base', 'dBASEHOME')

        argument_list = "-consoleMode -stopsvcgrp all "
        if force_stop:
            argument_list = argument_list + "-kill"

        command = f'start-process -WorkingDirectory "{install_directory}" ' \
                  f'-FilePath "GxAdmin.exe" ' \
                  f'-ArgumentList "{argument_list}" -Verb RunAs -Wait'

        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def get_api_response_locally(self, api_url):
        """Executes api locally and returns response as string

                Args:

                    api_url         (str)       --  API url

                Returns:

                    Str         --      API response

                Raises:

                    Exception:

                            if failed to get response
        """
        option_obj = OptionsSelector(self.commcell_object)
        file_name = f"{option_obj.get_drive(self)}Get_API_Call_{option_obj.get_custom_str()}.txt"
        cmd = f"(Invoke-WebRequest -UseBasicParsing -uri '{api_url}').content"
        cmd = f"{cmd} | Out-File {file_name}"
        output = self.execute_command(cmd)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)
        if not self.check_file_exists(file_path=file_name):
            raise Exception(f"Invoke-WebRequest error for command - [{cmd}]. Please check")
        response = self.read_file(file_path=file_name)
        self.delete_file(file_path=file_name)
        return response

    def check_if_pattern_exists_in_log(self, pattern, log_file_name):
        """ Method to check if the given pattern exists in the log file or not

        Args:
            pattern         (str)   -- pattern to be searched inside log file

            log_file_name   (str)   -- log file name

        Returns:
            True if pattern exists, False otherwise
        """
        client_log_directory = self.client_object.log_directory
        command = (
                      "(Select-String -Path \"%s\" -Pattern"
                      " \"%s\")") % (
                      self.join_path(client_log_directory, log_file_name), pattern)
        output = self.execute_command(command).formatted_output
        if output != '':
            return True
        return False

    def mount_nfs_share(self, nfs_client_mount_dir, server, share, cleanup=False, version="4"):
        """ mounts the given NFS mount path

            Args:
                nfs_client_mount_dir  (str)  --  local directory for nfs mount path

                server                (str)  --  nfs server hostname or ip address

                share                 (str)  --  nfs server share path

                cleanup               (bool) --  flag to unmount before mounting

                version               (str) --   nfs v3 or v3 client. for windows machine we
                        are using symbolic link. this option is not required. added only
                        for compatibility reason. this option will be ignored for windows
                        platform
            Returns:
                None

            Raises:
                Exception(Exception_Code, Exception_Message):
                    if failed to mount network path
        """
        if cleanup:
            self.unmount_path(nfs_client_mount_dir)

        # Create Directory to mount
        nfs_client_dir = os.path.dirname(nfs_client_mount_dir)
        if not self.check_directory_exists(nfs_client_dir):
            self.create_directory(nfs_client_dir, True)

        # Mount the object store as NFS share on client machine
        share = share.strip('/').strip('\r')
        cmd = "New-Item -ItemType SymbolicLink -Path {2} -Target \\\{0}\\{1}".format(server,
                                                                                     share,
                                                                                     nfs_client_mount_dir)
        self._log.info("running mount command {0}".format(cmd))
        output = self.execute_command(cmd)
        if output.exit_code:
            raise Exception("mountNFS_share(): exception while mounting "
                            "Share. output:{0}, exception:{1}".format(output.exception,
                                                                      output.exception_message))

    def get_snapshot(self, directory_path):
        """
        gets folder hash of the directory.

        Args:
            directory_path     (str)   - path of the folder to get the data

         Returns:
                file_list   (list)-   list containing [file path and md5 hash]

        Raises:
            Exception:
                If specified folder doesn't exist.

                If the algorithm entered is invalid.

                If failed to get the hash values.

        """
        output = self.get_folder_hash(directory_path=directory_path)
        snapshot = []
        for hash in output:
            snapshot.append(str(hash[0]) + " " + str(hash[1]))
        return snapshot

    def unmount_path(self, mount_path, delete_folder=False, force_unmount=False):
        """to remove symbolic path (shared path)

        Args:
            mount_path (str): path of symbolic link
        """
        cmd = "(Get-Item {0}).Delete()".format(mount_path)
        self._log.info("running unmount command {0}".format(cmd))
        output = self.execute_command(cmd)
        if output.exception_message:
            raise Exception(output.exception_code,
                            output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        elif output.exit_code and output.output:
            raise Exception(output.output)

    def is_path_mounted(self, mount_path):
        """To check if the given mount path is symbolic link or not

        Args:
            mount_path (str): path for symbolic link

        Returns:
            bool: true if given path is symbolic link
        """
        cmd = '(Get-Item "{0}").LinkType -eq "SymbolicLink"'.format(mount_path)
        output = self.execute_command(cmd)
        if output.exception_message:
            raise Exception(output.exception_code,
                            output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        elif output.exit_code != 0 and output.output:
            raise Exception(output.output)

        return output.formatted_output == 'True'

    def clear_folder_content(self, folder_path):
        """ Empties the given folder path. Recursively deletes all files & folders inside given folder path

                Args:

                    folder_path     (str)   --  Folder path which needs to be emptied

                Returns:

                    None

                Raises:

                    Exception:

                        if failed to empty the folder content


        """
        cmd = f"Get-ChildItem -Path '{folder_path}' -Recurse| Foreach-object {{Remove-item -Recurse -path $_.FullName }}"
        output = self.execute_command(command=cmd)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def run_cvping(self, destination, family_type='UseIPv4', port='8400'):
        """Executes cvping on machine with provided inputs

            Args:

                Destination     (str)       --  Destination machine name or IP

                family_type     (str)       --  Address to be used in ping.

                       Supported Values are UseIPv4, UseIPv6 or UseIPAny. Default is UseIPv4

                port            (str)       --  Port no to be used in ping (Default:8400)

            Returns:

                bool        --  Whether CVping succeeded or not for given input

            Raises:

                Exception:

                    if failed to find cvping in base folder
        """
        install_directory = self.get_registry_value('Base', 'dBASEHOME')
        if not self.check_file_exists(file_path=f"{install_directory}\\cvping.exe"):
            raise Exception(f"cvping tool is not installed on this client.")
        cmd = f"cvping {destination} -{family_type} -port {port}"
        output = self.execute_command(cmd)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)
        if 'Successfully connected to' in output.output:
            return True
        return False

    def run_cvdiskperf(
            self,
            path,
            sequential=True,
            stat=True,
            block_size=65536,
            block_count=16384,
            file_count=6,
            thread_count=6):
        """Executes cvdiskperf tool on given path and returns results

                Args:

                    path            (str)       --  Path where we need to run cvdiskperf tool

                    sequential      ( bool)      --  Specifies whether it is sequential or random access for read/write
                                                        Default = True

                    stat            (bool)      --  Specifies whether to measure time taken for each file operations
                                                        Default = True

                    block_size      (int)       --  Buffer size used to perform single read/write operations in bytes
                                                        Default = 65536 bytes

                    block_count     (int)       --  Total number of blocks written or read from a file
                                                        Default = 16384

                    file_count      (int)       --  Number of files in the read and write operations
                                                        Default = 6

                    thread_count    (int)       --  Number of threads used to perform read.write in parallel
                                                        Default = 6

                Returns:

                    dict        --  containing cvdiskperf result

        """
        option_obj = OptionsSelector(self.commcell_object)
        file_name = f"{option_obj.get_drive(self)}Get_cvdiskperf_{option_obj.get_custom_str()}.txt"
        access_type = "-SEQUENTIAL"
        if not sequential:
            access_type = "-RANDOM"
        cmd_opts = f"-PATH {path} -OUTFILE {file_name} {access_type} -BLOCKSIZE {block_size} " \
                   f"-BLOCKCOUNT {block_count} -FILECOUNT {file_count} -THREADCOUNT {thread_count}"
        if stat:
            cmd_opts = f"{cmd_opts} -STAT"
        install_directory = self.get_registry_value('Base', 'dBASEHOME')
        if not self.check_file_exists(file_path=f"{install_directory}\\cvdiskperf.exe"):
            raise Exception(f"CVDiskPerf tool is not installed on this client. Make sure MA/FS package is installed")
        command = f'start-process -WorkingDirectory "{install_directory}" ' \
                  f'-FilePath "cvdiskperf.exe" ' \
                  f'-ArgumentList "{cmd_opts}" -Verb RunAs -Wait'
        output = self.execute_command(command)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)
        if not self.check_file_exists(file_path=file_name):
            raise Exception("CVDiskPerf tool result file doesn't exists")
        content = self.read_file(file_path=file_name)
        content_list = content.split('\n')
        out_dict = {}
        stats = ''
        for line in content_list:
            line = line.strip()
            if line.startswith('Size of'):
                stats = f"{stats}{line},"
            elif ':' in line:
                splitted_line = line.split(':', 1)
                out_dict[splitted_line[0].strip()] = splitted_line[1].strip()
        if stats != '' and stat:
            stats = stats[:-1]
            out_dict["Stats"] = stats
        self.delete_file(file_path=file_name)
        if not out_dict:
            raise Exception("CVDiskPerf execution failed. Please check the parameter value passed")
        return out_dict

    def remove_additional_software(self, package):
        """This method will remove all the 3rd party software from the machine.
        This command will automatically reboot the machine is reboot is required.
         Args:

                    package   (str)       --  Package to remove

        """
        cmd = f'$MyApp = Get-WmiObject -Class Win32_Product | Where-Object{{$_.Name -eq "{package}"}};$MyApp.Uninstall()'
        self._log.info(f"Removing {package} package from File server machine. Command will reboot the host machine")
        self._log.info("Executing command : " + cmd)
        self.execute_command(cmd)

    def copy_file_between_two_machines(self, src_file_path, destination_machine_conn, destination_file_path):
        """
        Transfer files between two machines.
        """
        raise NotImplementedError("Method not implemented for Windows")

    def verify_installed_packages(self, packages):
        """verify the packages are installed on the client
        Args:
            packages (list): list of package ids. for package id, please refer to the corresponding constants
        """
        for pkg_id in packages:
            if self.get_registry_value(
                    commvault_key="InstalledPackages\\" + str(pkg_id),
                    value="sInstallState") != "Installed":
                raise Exception(
                    "Packages are not installed correctly")
        self._log.info("Packages are installed successfully")

    def change_inheritance(self, folder_path, disable_inheritance=True):
        """Disables or enables inheritance on the folder
            Args:
                folder_path         (str)   -   Full path of the folder
                disable_inheritance (bool)  -   whether to disable or enable inheritance on folder

            Raises:
                If given folder is not present on machine -
                    Provided folder : folder_path is not present on machine : machine_name
        """
        change_inheritance = ['e', 'd'][disable_inheritance]
        if not self.check_directory_exists(folder_path):
            raise Exception(f"Provided folder : {folder_path} is not present on machine : {self.machine_name}")
        self.execute_command(f"icacls {folder_path} /inheritance:{change_inheritance}")

    def unzip_zip_file(self, file_path, destination_folder):
        """
            Unzip the zipped files on machine

            Args:
                destination_folder   (str)  -   Full path of the destination folder where zip file need to be extracted
                file_path            (str)  -   Full path of the zip file

            Raises:
                Exception -
                    if unable to unzip files
        """
        cmd = f"Expand-Archive -Force {file_path} {destination_folder}"

        output = self.execute_command(command=cmd)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def set_all_disks_online(self):
        """
        Sets all the disks in the machine online
        Returns:
            None
        Raises:
            Exception:
                if command execution fails
        """
        cmd = "Get-Disk|Where-Object IsOffline -Eq $True | Set-Disk -IsOffline $False"
        output = self.execute_command(command=cmd)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)