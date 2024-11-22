# -*- coding: utf-8 -*-
# pylint: disable=W0703

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for performing operations on a machine / computer with UNIX Operating System.

This file consists of a class named: Machine, which can connect to the remote machine,
using CVD, if it is a Commvault Client, or using UNIX Shell, otherwise.

The instance of this class can be used to perform various operations on a machine, like,

    #.  Check if a Directory Exists or not
    #.  Create a new Directory
    #.  Rename a File / Folder
    #.  Remove an existing Directory
    #.  Get the Size of a File / Folder
    #.  Check if a Registry exists or not
    #.  Add / Update a Registry Key / Value
    #.  Get the Value of a Registry Key
    #.  Delete a Registry Key / Value
    #.  Compare the contents of 2 Files / Folders


UnixMachine
===========

    __init__()                      --  initialize object of the class

    _login_with_credentials()       --  establishes an SSH session to the client using paramiko

    _execute_with_credential()      --  execute a script on a remote client using its credentials

    _execute_with_cvd()             --  execute a script on a remote client using the CVD service

    _get_file_hash()                --  returns the hash value of specified file

    _get_folder_hash()              --  returns the set of file paths and hash values

    _execute_script()               --  executes a UNIX Shell script on the remote machine

    _copy_file_from_local()         --  copy a file from the controller machine to the remote
    machine

    _get_files_or_folders_in_path() --  returns the list of files / folders present at the given
    path based on the operation type given

    _get_client_ip()                -- gets the ip address of the machine

    copy_file_locally()              -- Copies file from one directory to another or copies files in same directory

    reboot_client()                 --  Reboots the remote machine

    kill_process()                --  Kills a process in the remote machine

    execute_command()               --  executes a UNIX Shell / bash command on the remote machine

    check_directory_exists()        --  checks if a directory exists on a remote client or not

    check_file_exists()             --  checks if a file exists on a remote client or not

    create_directory()              --  creates a new directory on a remote client

    rename_file_or_folder()         --  renames a file / folder on a remote client

    remove_directory()              --  removes a directory on a remote client

    get_file_size()                 --  get the size of a file on a remote client

    get_file_stats_in_folder()       --  Gets the total size in bytes by summing up the individual file size for files
                                        present in the directories and subdirectories of the given folder_path

    get_folder_size()               --  get the size of a folder on a remote client

    get_storage_details()           --  gets the details of storage of the client

    check_registry_exists()         --  check if a registry exists on a remote client or not

    get_registry_value()            --  get the value of a registry key from a remote client

    create_registry()               --  create a registry key / value on a remote client

    update_registry()               --  update the data of a registry value on a remote client

    remove_registry()               --  remove a registry key / value from a remote client

    copy_from_local()               --  copy a file / folder from the controller machine
    to the remote machine

    copy_folder()                   --  copy a folder from one location to another on same
    local machine

    create_file()                   --  creates a file on the remote machine

    append_to_file()                --  Appends content to the file present at the specified path

    mount_network_path()            --  mounts the network shared path

    unmount_path()                  --  dis mounts the network path mounted at specified path

    copy_folder_to_network_share()  --  copies the source folder from controller to network path

    copy_folder_from_network_share() -- copies the folder from network path to the local

    generate_test_data()            --  generates and adds random testdata on the specified path

    modify_test_data()              --  Modifies the test data at the given path

    get_test_data_info()            --  Gets information about the items on the given path

    get_uname_output()              --  Gets the uname output from the machine

    get_registry_dict()             --  Gets dictionary of all the commvault registry
    keys and values

    get_items_list()                --  Gets the list of items at the given path

    get_meta_list()                 --  Gets the list of meta data of items
    from the machine on a give path

    compare_meta_data()             --  Compares the meta data of source path with destination path
    and checks if they are same.

    get_checksum_list()             --  Gets the list of checksum of items
    from the machine on a give path

    compare_checksum()              --  Compares the checksum of source path with destination path
    and checks if they are same

    get_acl_list()                  --  Gets the list of acl of items
    from the machine on a give path

    compare_acl()                   --  Compares the acl of source path with destination path
    and checks if they are same

    get_xattr_list()                --  Gets the list of xattr of items
    from the machine on a give path

    compare_xattr()                 --  Compares the xattr of source path with destination path
    and checks if they are same

    get_disk_count()                --  returns the number of disks on the machine

    change_folder_owner()           --  changes the owner of the given folder as the given user

    get_files_in_path()             --  returns the list of files present at the given path

    get_folders_in_path()           --  returns the list of folders present at the given path

    get_folder_or_file_names()      --  Returns the list of files / folders present inside the
    given folder path on the client.

    number_of_items_in_folder()     --  Returns the count of number of items in a folder

    disconnect()                    --  disconnects the session with the machine

    modify_file_time()              -- modify file's time,
                                    it can modify file Atime, Mtime and Ctime

    is_stub()                       -- to verify whether file is stub

    get_process_id()                --  returns the process id for the given process name with or without command line

    get_process_stats()             --  Gets the process stats like Handle count, memory used, CPU usage, thread count

    get_hardware_info()             --  returns the hardware specifications of this machine

    get_port_usage()                --  returns the netstat connection stats for the process or machine

    is_process_running()            -- Checks if a given process is running on the index server

    wait_for_process_to_exit()      --  waits for a given process to exit

    add_firewall_machine_exclusion()--  Adds given machine to firewall exclusion list

    add_firewall_allow_port_rule()  --  Adds the inbound rule for the given port number

    start_firewall()                --  turn on firewall services on the current client machine

    remove_firewall_allow_port_rule()-- removes the inbound rule for the given port number

    stop_firewall()                  -- turn off firewall service on the current client machine

    remove_firewall_machine_exclusion()
                                     -- removes given machine from firewall exclusion list

    get_firewall_state()             -- get the state of firewall on current machine

    mount_nfs_share()                -- mounts the given NFS mount path

    get_snapshot()                   -- gets (ls -l) meta data and md5sum of each file
    in the given directory

    scan_directory()                --  Scans the directory and returns a list of items under it
    along with its properties

    is_path_mounted()               --  check whether given path is mounted locally

    rsync_local()                   --  sync source and destination local folders on the client
    machine

    add_user()                      --  create new user account using values passed to method

    delete_users()                  --  delete a user account and Files in the user's
    home directory

    change_file_permissions()       --  change file mode bits for the given file or directory path

    get_file_permissions()          --  Gets the file permissions of the given file or directory

    nfs4_setfacl()                  -- manipulates the NFSv4 Access Control List (ACL) of
    one or more files (or directories)

    nfs4_getfacl()                  -- get NFSv4 file/directory access control lists

    set_logging_debug_level()       -- set debug log level for given CV service name

    set_logging_filesize_limit()    -- set filesize limit for given CV service

    get_cpu_usage()                 -- gets the cpu performance counters for the given process

    get_log_file()                   -- Returns the contents of a log file.

    has_active_session()            -- Checks if there is an active session on the machine for a user

    get_file_owner()                -- Get the owner of the file

    get_file_group()                --  Get the group of the file/directory

    get_logs_for_job_from_file()     -- Return those log lines for a particular job ID
    
    get_time_range_logs()           -- Retrieves log lines from a file within a specified time range

    move_file()                     --  Moves a file item from source_path to destination_path

    get_modified_time()             --  Gets the modified time of a file at the specified path

    modify_item_datetime()          --  Changes the last Access time and Modified time of files in unix and windows.
    Also changes creation time in windows.

    start_all_cv_services()         --  Start all Commvault services using username/password method since SDK cannot
    talk to the machine when services are down

    stop_all_cv_services()          --  Stop all Commvault services using username/password method

    get_api_response_locally()      --  Executes local get api call and returns response

    current_time()                  --  Returns current machine time in UTC TZ as a datetime object
    
    current_localtime()             -- Returns the current local time of the machine as a datetime object.

    unzip_zip_file                  --  To unzip a file at a given path.

    change_system_time()            --  Changes the system time as per the offset seconds
    provided w.r.t to current system time

    toggle_time_service()           --  Toggles the state of the unix ntp time service

    check_if_pattern_exists_in_log  --  Method to check if the given pattern exists in the log file or not

    fill_zero_disk()                   --  Filling 1Mb block of the disk with all zeros

    create_local_filesystem         --  Creates filesystem on the local disk

    mount_local_path                --  Mounts local disk to local path on the machine

    clear_folder_content()          --  Recursively deletes files/folders in given folder path to make it empty

    run_cvdiskperf()                --  Executes cvdiskperf.exe tool and returns results

    run_cvping()                    --  Executes cvping on machine with provided inputs

    find_lines_in_file()            --  Search for lines in a file for the given words

    check_user_exist()              --  Checks if user exists or not

    remove_additional_software()    -- This method will remove the 3rd party software

    copy_file_between_two_machines  --  Transfer files between two machines.

    change_hostname                 --  Changes the hostname of the given unix machine

    add_to_domain                   --  adds a given unix machine to domain

    disable_ipv6                    --  disables IPv6 address for the machine

    get_hostname                    --  Gets the hostname of the machine

Attributes
----------

    **is_connected**        --  returns boolean specifying whether connection is alive or not

    **key**                 --  returns the base path of the Registry Key of Commvault Instance

    **os_flavour**          --  returns the flavour of the UNIX distribution

    **instance**            --  returns the Commvault instance registry currently being interacted
    with

    **instance.setter**     --  set the value of the Commvault instance to interact with

    **tmp_dir**             --  returns the path of the **tmp** directory on the Machine where the
    temporary database files are stored

    **os_sep**              --  returns the path separator based on the OS of the Machine

    **shell_command**       --  returns the OS specific shell command (bash/ksh)

    **ip_address**          --  returns IP address of the machine

    **os_pretty_name**      --  Returns the pretty name value of the OS

"""

import os
import posixpath
import random
import string
import subprocess
import time
import socket
import paramiko
import datetime

from . import logger

from .options_selector import OptionsSelector
from .constants import ALGORITHM_LIST
from .constants import UNIX_DELIMITER
from .constants import GET_UNIX_HASH
from .constants import UNIX_CREATE_REGISTRY
from .constants import UNIX_MANAGE_DATA
from .constants import UNIX_PROBLEM_DATA
from .constants import UNIX_REGISTRY_EXISTS
from .constants import UNIX_GET_CPU_USAGE
from .constants import UNIX_SET_REG_VALUE
from .constants import UNIX_TMP_DIR
from .constants import UNIX_GET_PROCESS_STATS
from .constants import UNIX_GET_CV_TIME_RANGE_LOGS
from .machine import Machine
from .output_formatter import UnixOutput
from .script_generator import ScriptGenerator


class UnixMachine(Machine):
    """Class for performing operations on a UNIX OS remote client."""

    def __init__(self, machine_name=None, commcell_object=None, username=None, password=None,
                 **kwargs):
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
                key_filename        (str/list)  --  string or list containing ppk key location(s) for

                        machines that require a private key for SSH

                    default:    None

                run_as_sudo         (bool)      --  variable for running commands as sudo for machines

                        where root login is disabled


        Also, initializes the Client object, if it is Commvault Client.

        Otherwise, it creates a paramiko SSH client object for the client.

        """
        self.key_filename = kwargs.get('key_filename', None)
        super(UnixMachine, self).__init__(machine_name, commcell_object, username, password)
        self._script_generator = ScriptGenerator()

        if self.is_commvault_client:
            self._instance = self.client_object.instance
        else:
            self._instance = 'Instance001'

        self._key = r'/etc/CommVaultRegistry/Galaxy/{0}/%s/.properties'.format(self.instance)

        self.run_as_sudo = kwargs.get('run_as_sudo', False)

        self._shell_command = None
        self._os_info = "UNIX"
        self._os_flavour = None
        self.log = logger.get_log()

    @property
    def os_flavour(self):
        """Returns the flavor os the os"""
        if self._os_flavour is None:
            self._os_flavour = self.get_uname_output()
            if self._os_flavour == "OS400":
                self._shell_command = "ksh "
        return self._os_flavour

    def _login_with_credentials(self):
        """Establishes a SSH connection to the UNIX client."""
        self._client = paramiko.SSHClient()

        self._client.load_system_host_keys()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self._client.connect(
                self.machine_name, username=self.username, password=self.password,
                key_filename=self.key_filename)
        except paramiko.AuthenticationException:
            raise Exception('Authentication Failed. Invalid credentials provided.')

    def _execute_with_credential(self, script, script_arguments=None):
        """Execute the script remotely on a client using the credentials provided,
            if the client is not a Commvault client.

        Args:
            script              (str)   --  path of the script file to execute on the
                                            remote client.

            script_arguments    (str, optional)   --  arguments to be passed to the script.
                                                      Defaults to None.

        Returns:
            object  -   instance of UnixOutput class

        """
        script_arguments = '' if script_arguments is None else script_arguments

        if self.is_local_machine:
            if os.path.isfile(script):
                script = '{2} {0} {1}'.format(
                    script, script_arguments, self.shell_command).strip()
            else:
                script = '{0} {1}'.format(script, script_arguments).strip()

            process = subprocess.run(
                script,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            return UnixOutput(process.returncode, process.stdout.decode(), process.stderr.decode())
        else:
            if not self.is_connected:
                self._login_with_credentials()
            remove_temp_file = False

            if os.path.isfile(script):
                script_base_name = "{0}{1}".format(
                    str(id(self)), os.path.basename(script))
                sftp = self._client.open_sftp()
                sftp.put(
                    os.path.abspath(script),
                    '/tmp/{0}.temp'.format(script_base_name)
                )
                sftp.close()
                time.sleep(0.25)
                __, stdout, stderr = self._client.exec_command(
                    "tr -d '\r' < /tmp/{0}.temp > /tmp/{0}; rm -rf /tmp/{0}.temp".format(script_base_name)
                )
                while True:
                    if stdout.channel.exit_status_ready():
                        break
                script = (
                    '{2} /tmp/{0} {1}'.format(script_base_name,
                                              script_arguments,
                                              self.shell_command)
                )
                remove_temp_file = True
            else:
                script = '%s %s' % (script, script_arguments)

            __, stdout, stderr = self._client.exec_command(script)

            output = stdout.read()
            error = stderr.read()

            while True:
                while stdout.channel.recv_ready():
                    output = '%s%s' % (output, stdout.read())

                while stderr.channel.recv_ready():
                    error = '%s%s' % (error, stderr.read())

                if stdout.channel.exit_status_ready():
                    break

            exit_code = stdout.channel.recv_exit_status()

            if remove_temp_file is True:
                self._client.exec_command(
                    'rm -rf /tmp/{0}'.format(script_base_name))

            return UnixOutput(exit_code, output.decode(), error.decode())

    def _execute_with_cvd(self, script, script_arguments=None):
        """Execute the script remotely on a client using the CVD service running on the client.
            Only applicable if the client is a Commvault Client.

        Args:
            script  (str)   --  path of the script file to execute on the client remotely

            script_arguments (str)  --  arguments to the script

        Returns:
            object  -   instance of UnixOutput class

        """
        if os.path.isfile(script):
            exit_code, output, error_message = self.client_object.execute_script(
                'UnixShell', script, script_arguments
            )
        else:
            exit_code, output, error_message = self.client_object.execute_command(
                script, script_arguments
            )

        return UnixOutput(exit_code, output, error_message)

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
            raise Exception(
                "{0} file does not exist on {1}".format(
                    file_path, self.machine_name
                )
            )

        # checks with the list of supported algorithms
        if algorithm.upper() not in ALGORITHM_LIST:
            raise Exception(
                "Algorithm not found under the list {0}".format(
                    str(ALGORITHM_LIST)
                )
            )

        # executes script
        default_command = '{0}sum {1}'.format(algorithm.lower(), file_path)

        os_flavour = {
            'darwin': '{0} {1}'.format(algorithm.lower(), file_path)
        }

        command = os_flavour.get(self.os_flavour.lower(), default_command)

        output = self.execute(command)

        # raises exception
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        if self.os_flavour.lower() == 'darwin':
            return str(output.formatted_output).split('=')[1].upper().lstrip()
        return str(output.formatted_output).split()[0].upper()

    def _get_folder_hash(self, directory_path, ignore_folder=None,
                         ignore_case=False, algorithm="MD5"):
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
            raise Exception(
                "{0} path does not exist on {1}".format(
                    directory_path, self.machine_name
                )
            )

        directory_path = f'"{directory_path}"'

        # checks with the list of supported algorithms
        if algorithm.upper() not in ALGORITHM_LIST:
            raise Exception(
                "Algorithm not found under the list {0}".format(
                    str(ALGORITHM_LIST)
                )
            )

        # converting list to a single string with delimiters in between
        if ignore_folder is None:
            ignore_folder = []
        ignore_string = UNIX_DELIMITER.join(ignore_folder)

        # forming arguments to be passed while executing the script file
        default_algorithm = "{0}sum".format(algorithm.lower())

        os_flavour = {
            'darwin': "{0}".format(algorithm.lower())
        }
        algorithm = os_flavour.get(self.os_flavour.lower(), default_algorithm)
        argument_list = [directory_path, "'{}'".format(ignore_string),
                         str(ignore_case).lower(), algorithm]
        script_arguments = " ".join(argument_list)

        # executes script
        output = self.execute(GET_UNIX_HASH, script_arguments)
        directory_path = directory_path[1:-1]

        def format_output(output_list):
            """Parses the output list received from UnixOutput class object,
                and returns a set of paths, and their hash value

            Args:
                output_list     (list)  --  list of the output to parse

            Returns:
                set     -   set consisting of the file paths and their hash value as tuple
                    set(
                        (file_path1, hash1),
                        (file_path2, hash2)

                    )

            """
            hash_values = set()
            if not isinstance(output_list, list):
                output_list = [[output_list]]

            for output_value in output_list:
                value = output_value[::-1]
                value[0] = value[0].replace(
                    directory_path + '/', '').replace('/', '\\')
                value[-1] = value[-1].upper()
                hash_values.add(tuple(value))

            return hash_values

        # raises exception
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return format_output(output.formatted_output)

    def _copy_file_from_local(self, local_path, remote_path=None):
        """Copies the local file to the remote UNIX client.

        Args:
            local_path      (str)   --  path of the local file to copy

            remote_path     (str)   --  path on the client to copy the file at
                    copies the file to Desktop, if not provided

                default: None

        Raises:
            Exception:
                if local_path is not a valid file

                if failed to copy the file

        """
        if os.path.isfile(local_path):
            file_name = os.path.basename(local_path)
        else:
            raise Exception('Input path is not a valid file')

        if remote_path is None:
            remote_path = '/root/Desktop/'

        self.log.info(
            "Copy local file from [{0}] to [{1}] on client [{2}]".format(local_path, remote_path, self.machine_name)
        )

        if self.is_commvault_client:
            self.client_object.upload_file(local_path, remote_path)
        else:
            if not self.check_directory_exists(remote_path):
                self.create_directory(remote_path)

            remote_path = posixpath.join(remote_path, file_name)

            try:
                sftp = self._client.open_sftp()
                sftp.put(local_path, remote_path)
                sftp.close()
            except (OSError, PermissionError):
                raise Exception(
                    'Failed to copy the file. Please check the permissions')

        return True

    def _get_files_or_folders_in_path(self, folder_path, operation_type, recurse=True, days_old=0):
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

        operation_type = 'f' if operation_type == 'FILE' else 'd'

        # If days_old is greater than 0, modify the command to filter files by age
        if int(days_old) > 0:
            # Using the `-mtime` option in find command
            # `+` means "more than" in terms of days
            cmd = f'find {folder_path} -type {operation_type} -mtime +{days_old}'
        else:
            cmd = f'find {folder_path} -type {operation_type}'

        if not recurse:
            cmd += ' -maxdepth 1'
        output = self.execute_command(cmd)

        if isinstance(output.formatted_output, list):
            return list(map(lambda x: ' '.join(x), output.formatted_output))
        else:
            return [output.formatted_output]

    def _get_client_ip(self):
        """Gets the ip_address of the machine"""
        cmd = "hostname -I"
        cmd_output = self.execute_command(cmd)
        ip_addresses = cmd_output.output.split(" ")
        self._ip_address = ip_addresses[0]

    @property
    def is_connected(self):
        """Returns boolean specifying whether the connection to the machine is open or closed."""
        try:
            if self.client_object:
                self._is_connected = self.client_object.is_ready

            elif self._client:
                try:
                    # use the command `df` instead of `ls`, as it is not
                    # available on NAS filers
                    __, __, __ = self._client.exec_command('df', timeout=5)
                    self._is_connected = True
                except Exception:
                    self._is_connected = False

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

        self._key = r'/etc/CommVaultRegistry/Galaxy/{0}/%s/.properties'.format(
            self.instance)

    @property
    def tmp_dir(self):
        """Returns the path of the **tmp** directory on the UNIX Machine, where temporary
            database files are stored.

            default value:  /tmp/

        """
        # create directory should always be called, to ensure that the directory exists,
        # and ADD it if it does not exists on the machine
        if not self.check_directory_exists(UNIX_TMP_DIR):
            self.create_directory(UNIX_TMP_DIR)
        return UNIX_TMP_DIR

    @property
    def os_sep(self):
        """Returns the path separator based on the OS of the Machine."""
        return "/"

    @property
    def shell_command(self):
        """Returns the platform specific shell command"""
        self._shell_command = "bash "

        if self.os_flavour == "OS400":
            self._shell_command = "ksh "

        return self._shell_command

    @property
    def os_distro(self):
        """Returns the distro name of the OS"""
        command = "cat /etc/os-release | grep '\\bID='"
        output = self.execute_command(command).formatted_output
        return output.split("=")[-1].replace('"', '').lower()

    @property
    def os_pretty_name(self):
        """Returns the pretty name value of the OS"""
        command = "cat /etc/os-release | grep '^PRETTY_NAME='"
        output = self.execute_command(command).formatted_output
        return output.split("=")[-1].replace('"', '').lower().split("(")[0].strip()

    def reboot_client(self):
        """Reboots the machine.

            Please **NOTE** that the connectivity will go down in this scenario, and the Machine
            class may not be able to re-establish the connection to the Machine.

            In such cases, the user will have to initialize the Machine class instance again.

            Args:
                None

            Returns:
                object  -   instance of the UnixOutput class

            Raises:
                Exception:
                    if failed to reboot the machine

        """
        output = self.execute_command('reboot')

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
            object  -   instance of UnixOutput class

        Raises:
            Exception:
                if neither the process name nor the process id is given

                if failed to kill the process

        """
        if process_name:
            command = f'pkill -f {process_name}'
        elif process_id:
            command = f'kill -9 {process_id}'
        else:
            raise Exception('Please provide either the process Name or the process ID')

        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output

    def execute_command(self, command):
        """Executes a UNIX Shell command on the machine.

        An instance of the **UnixOutput** class is returned.

        Output / Exception messages received from command execution are
        available as the attributes of the class instance.

            output_instance.output              --  raw output returned from the command

            output_instance.formatted_output    --  o/p received after parsing the raw output

            output_instance.exception           --  raw exception message

            output_instance.exception_message   --  parsed exception message from the raw o/p


        Args:
            command     (str)   --  UNIX Shell command to be executed on the machine

        Returns:
            object  -   instance of UnixOutput class

        """
        return self.execute(command)

    # OS related functions
    def check_directory_exists(self, directory_path):
        """Checks if a directory exists on the client or not.

        Args:
            directory_path  (str)   --  path of the directory to check

        Returns:
            bool    -   boolean value whether the directory exists or not

        """
        output = self.execute(
            'if test -d "{0}"; then echo "TRUE"; fi'.format(directory_path))

        return str(output.formatted_output).lower() == 'true'

    def check_file_exists(self, file_path):
        """Checks if a file exists on the client or not.

        Args:
            file_path  (str)   --  name of the file to check

        Returns:
            bool    -   boolean value whether the file exists or not

        """
        output = self.execute(
            'if test -f "{0}"; then echo "TRUE"; fi'.format(file_path))

        return str(output.formatted_output).lower() == 'true'

    def create_directory(self, directory_name, force_create=False):
        """Creates a directory on the client, if it does not exist.

        Args:
            directory_name  (str)   --  name / full path of the directory to create

            force_create    (bool)  --  deletes the existing directory and creates afresh

        Returns:
            True    -   if directory creation was successful

        Raises:
            Exception:
                if directory already exists

        """
        sudo = ''
        if self.run_as_sudo:
            sudo = 'sudo '

        if force_create:
            if self.check_directory_exists(directory_name):
                output = self.execute(f"{sudo} rm -rf {directory_name}")
                if output.exception_message:
                    raise Exception(output.exception_message)

        else:
            if self.check_directory_exists(directory_name):
                raise Exception("Directory already exists")
        output = self.execute(sudo + 'mkdir -p {0}'.format(directory_name))
        if output.exception_message:
            raise Exception(output.exception_message)

        if self.run_as_sudo:
            # Doing this since on a non-root login, created directories only have read access.
            # We need to do this to be able to write data to it
            permission_output = self.execute(f"{sudo} chmod 757 {directory_name}")
            if permission_output.exception_message:
                raise Exception(output.exception_message)
        return True

    def rename_file_or_folder(self, old_name, new_name):
        """Renames a file or a folder on the client.

        Args:
            old_name    (str)   --  name / full path of the directory to rename

            new_name    (str)   --  new name / full path of the directory

        Returns:
            None    -   if the file or folder was renamed successfully

        Raises:
            Exception:
                if failed to rename the file or folder

        """
        sudo = ''
        if self.run_as_sudo:
            sudo = 'sudo '
        output = self.execute(sudo + 'mv {0} {1}'.format(old_name, new_name))

        if output.exception_message:
            raise Exception(output.exception_message)
        elif output.exception:
            raise Exception(output.exception)

        return output.formatted_output == ''

    def remove_directory(self, directory_name, days=None):
        """Removes a directory on the client.
            If days is specified then directories older than given days
            will be cleaned up

        Args:
            directory_name  (str)   --  name / full path of the directory to remove

            days            (int)   --  dirs older than the given days will be cleaned up

                default: None

        Returns:
            None    -   if directory was removed successfully

        Raises:
            Exception:
                if any error occurred during cleanup
                if entire root path is provided for deletion

        """
        if directory_name in ['/', '\\']:
            raise Exception('Cannot delete entire root path')

        sudo = ''
        if self.run_as_sudo:
            sudo = 'sudo '
        self.log.info("Removing directory [{0}]".format(directory_name))
        if days is None:
            output = self.execute(sudo + 'rm -rf {0}'.format(directory_name))
            return output.output == '' and output.exception == ''

        else:
            cleanup_cmd = (
                    'find  "' + directory_name
                    + '"/* -prune -type d -mtime +'
                    + str(days)
                    + r' -exec rm -rf "{}" \;'
            )

            output = self.execute(cleanup_cmd)

            if output.exit_code != 0:
                raise Exception(
                    "Error occurred while cleaning up the test data "
                    + output.output
                    + output.exception
                )

    def get_file_size(self, file_path, in_bytes=False, size_on_disk=False):
        """Gets the size of a file on the client.

        Args:
            file_path   (str)   --  path of the file to get the size of

            in_bytes    (bool)  --  if true returns the size in bytes

            size_on_disk (bool) --  if size on disk should be returned.

        Returns:
            float   -   size of the file (in MB) and in bytes if in_bytes is set to True

        Raises:
            Exception:
                if failed to get the size of the file

        """

        # size_on_disk will be ignored on Unix as du command provides correct size.
        if size_on_disk:
            command = 'du {0}'.format(file_path)
        else:
            command = 'du -b {0}'.format(file_path)
        output = self.execute(command)

        if output.exception_message:
            raise Exception(output.exception_message)
        elif output.exception:
            raise Exception(output.exception)

        size = -1
        if isinstance(output.formatted_output, str):
            size = float(output.formatted_output.split('\t')[0])
        elif isinstance(output.formatted_output, list):
            size = float(output.formatted_output[-1][0])

        if in_bytes:
            return round(float(str(output.formatted_output).split()[0]))
        if size_on_disk:
            return round(size / 1024.0, 2)
        else:
            return round(float(str(output.formatted_output).split()[0]) / (1024.0 * 1024.0), 2)  # Returns size in MB

    def get_file_stats_in_folder(self, folder_path):
        """Gets the total size in bytes by summing up the individual file size for files present in the directories and
        subdirectories of the given folder_path

        Args:
            folder_path     (str)   --  path of the folder to get the size of

        Returns:
            float   -   size of the folder on the client (in bytes)

        Raises:
            Exception:
                if failed to get the size of the folder
                """
        command = f'find {folder_path} -type f -exec du -ab {{}} \;'
        output = self.execute(command)

        if output.exception_message:
            raise Exception(output.exception_message)
        elif output.exception:
            raise Exception(output.exception)

        output = output.formatted_output
        if not isinstance(output, list):
            return float(output.split("\t")[0])

        tot_size = 0
        for file in output:
            tot_size += float(file[0])
        return tot_size

    def get_folder_size(self, folder_path, in_bytes=False, size_on_disk=False):
        """Gets the size of a folder on the client.

        Args:
            folder_path     (str)   --  path of the folder to get the size of

            in_bytes        (bool)  --  if true returns the size in bytes

            size_on_disk    (bool)  --  if size on disk should be returned

        **Note:** size_on_disk will not be honored on Unix as default size returned on Unix system is same
        as size_on_disk.

        Returns:
            float   -   size of the folder (in MB) and in bytes if in_bytes is set to True

        Raises:
            Exception:
                if failed to get the size of the folder

        """

        # size_on_disk will be ignored on Unix as du command provides correct size.
        if size_on_disk:
            command = 'du {0}'.format(folder_path)
        else:
            command = 'du -b "{0}"'.format(folder_path)
        output = self.execute(command)

        if output.exception_message:
            raise Exception(output.exception_message)
        elif output.exception:
            raise Exception(output.exception)

        size = -1
        if isinstance(output.formatted_output, str):
            size = float(output.formatted_output.split('\t')[0])
        elif isinstance(output.formatted_output, list):
            size = float(output.formatted_output[-1][0])

        if in_bytes:
            return size
        if size_on_disk:
            return round(size / 1024.0, 2)
        else:
            return round(size / (1024.0 * 1024.0), 2)  # Returns the size in MB

    def get_storage_details(self, root=False, use_mountpoint_as_key=False):
        """Gets the details of the Storage on the Client.
            Returns the details of all paths, if root is set to the default value False.
            If root is set to True, it returns the details of only `/`

        Args:
            root    (bool)  --  boolean flag to specify whether to return details of all paths,
                                    or the details of the path mounted on root(/)

            use_mountpoint_as_key (bool)
                            --  boolean flag to specify to return the dict with mountpoint as key
                                    (in-case drive name is repeated, etc)

        Returns:
            dict - dictionary consisting the details of the storage on the client (in MB)

            {
                'total': size_in_MB,

                'available': size_in_MB,

                'drive': {
                    'total': size_in_MB,

                    'available': size_in_MB,

                }

            }

        """
        default_command = 'df -Pk'

        os_flavor = {
            'hp-ux': 'df -Pk'
        }

        command = os_flavor.get(self.os_flavour.lower(), default_command)

        if root is True:
            command += ' .'

        if 'aix' in self.os_flavour.lower():
            command += " | awk '{print $1, $2, $4, $3, $5, $6}'"

        output = self.execute(command)
        storage_dict = {
            'total': 0,
            'available': 0,
            'mountpoint': ["/"]
        }

        for value in output.formatted_output:
            try:
                drive_name = value[0]
                total_space = round(float(value[1]) / 1024.0, 2)
                free_space = round(float(value[3]) / 1024.0, 2)
                mount_point = str(value[5])

                if use_mountpoint_as_key:
                    storage_dict[mount_point] = {
                        'total': total_space,
                        'available': free_space,
                        'drivename': drive_name
                    }
                else:
                    storage_dict[drive_name] = {
                        'total': total_space,
                        'available': free_space,
                        'mountpoint': mount_point
                    }

                storage_dict['total'] += total_space
                storage_dict['available'] += free_space
                storage_dict['mountpoint'].append(mount_point)
            except ValueError:
                continue

        return storage_dict

    # Registry related operations
    def check_registry_exists(self, key, value=None):
        """Check if a registry key / value exists on the client or not.

        Args:
            key     (str)   --  registry path of the key

            value   (str)   --  value of the registry key

        Returns:
            bool    -   boolean value whether the registry key / value exists or not

        Raises:
            Exception:
                if the registry key does not exist

        """
        self._script_generator.script = UNIX_REGISTRY_EXISTS
        data = {
            'file': self.key % key,
            'key': value
        }
        registry_exists_script = self._script_generator.run(data)

        output = self.execute(registry_exists_script)
        os.unlink(registry_exists_script)

        if 'No such file or directory' in output.exception_message:
            return False
        elif output.exception_message:
            raise Exception(output.exception_message)
        elif output.exception:
            raise Exception(output.exception)

        return output.formatted_output != ''

    def get_registry_value(self, key=None, value=None, commvault_key=None):
        """Gets the data of a registry key and value on the client.

        Args:
            key     (str)       --  registry path of the key

            value   (str)       --  value of the registry key

            commvault_key   (str)   --  registry path of the commvault key
                    Example: Automation

        Returns:
            str     -   data of the value of the registry key

        """
        self._script_generator.script = UNIX_REGISTRY_EXISTS
        data = {
            'file': self.key % (key if key else commvault_key),
            'key': value
        }

        get_reg_value_script = self._script_generator.run(data)

        output = self.execute(get_reg_value_script)
        os.unlink(get_reg_value_script)

        if output.exception_message:
            raise Exception(output.exception_message)
        elif output.exception:
            raise Exception(output.exception)

        return output.formatted_output

    def create_registry(self, key, value, data, reg_type='String'):
        """Creates a registry key / value on the client, if it does not exist.

            Args:
                key     (str)       --  registry path of the key

                value   (str)       --  value of the registry key

                data    (str)       --  data for the registry value

                reg_type(str)       --  type of the registry value to add

            Returns:
                bool    -   if registry key / value creation was successful

            Raises:
                Exception(Exception_Code, Exception_Message):
                    if failed to create the registry key

        """
        # call create directory to create the directory path if user wants to create a sub key
        if self.os_sep in key:
            self.create_directory((self.key % key).strip('.properties'))

        self._script_generator.script = UNIX_CREATE_REGISTRY
        data = {
            'file': self.key % key,
            'key': value,
            'value': data
        }

        create_registry_script = self._script_generator.run(data)

        output = self.execute(create_registry_script)
        os.unlink(create_registry_script)

        return output.formatted_output == '' and output.exception == ''

    def update_registry(self, key, value, data, reg_type='String'):
        """Updates the value of a registry key / Adds the key (if it does not exist) on the client.

        Args:
            key     (str)       --  registry path of the key

            value   (str)       --  value of the registry key

            data    (str)       --  data for the registry value

            reg_type    (str)       --  type of the registry value to add

                Valid values are:

                    - String
                    - Binary
                    - DWord
                    - QWord
                    - MultiString

        Returns:
            bool    -   if registry value was updated successfully

        """
        self._script_generator.script = UNIX_SET_REG_VALUE
        data = {
            'file': self.key % key,
            'key': value,
            'value': data,
            'type': reg_type
        }

        update_reg_value_script = self._script_generator.run(data)

        output = self.execute(update_reg_value_script)
        os.unlink(update_reg_value_script)

        return output.formatted_output == '' and output.exception == ''

    def remove_registry(self, key, value=None):
        """Removes a registry key / value on the client.

        Args:
            key     (str)       --  registry path of the key

            value   (str)       --  value of the registry key

        Returns:
            None    -   if registry key / value removal was successful

        """
        if value is not None:
            command = 'sed -i "/^{0}/d" {1}'.format(value, self.key % key)
        else:
            command = 'rm -f {0}'.format(self.key % key)

        output = self.execute(command)

        if output.exception_message:
            raise Exception(output.exception_message)
        elif output.exception:
            raise Exception(output.exception)

        return output.formatted_output == ''

    def copy_from_local(self, local_path, remote_path, **kwargs):
        """Copies the file / folder present at the given path to the path specified on the
            remote machine.

        Args:
            local_path      (str)   --  path of the file / folder on the local machine

            remote_path     (str)   --  path of the directory to which the file / folder
            should be copied on the remote machine

            \*\*kwargs          (dict)  --  optional arguments (not used in Unix machine)

        Returns:
            (bool, list)    -   tuple consisting of a

            **bool** output specifying whether the file / folder was copied successfully or not

                True    -   all files / folders were copied successfully

                False   -   failed to copy some files / folders

            **list** consisting of the items failed to be copied

                list consisiting of items that were not copied

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to copy the file / folder

        """
        if not os.path.exists(local_path):
            raise Exception(f'Local Path [{local_path}] specified does not exist')

        if os.path.isfile(local_path):
            return self._copy_file_from_local(local_path, remote_path)

        status = True
        failed_items_list = []

        if not self.check_directory_exists(remote_path):
            self.create_directory(remote_path)

        if self.is_commvault_client:
            self.client_object.upload_folder(local_path, remote_path)
        else:
            for item in os.listdir(local_path):
                local_item_path = posixpath.join(local_path, item)
                remote_item_path = posixpath.join(remote_path, item)

                if os.path.isfile(local_item_path):
                    try:
                        self._copy_file_from_local(
                            local_item_path, remote_path)
                    except Exception:
                        failed_items_list.append(local_item_path)
                        status = False
                else:
                    try:
                        # Removing the old code to create directory with the
                        # already existing method which takes care of folder
                        # permission if login user is not root
                        self.create_directory(remote_item_path)
                    except (OSError, PermissionError):
                        continue
                    status = self.copy_from_local(
                        local_item_path, remote_item_path)

        return status, failed_items_list

    def create_file(self, file_path, content, file_size=None):
        """Creates a file at specified path on this machine

        Args:
            file_path   (str)   --  path of file to be created

            content     (str)   --  content that is to be written to file

            file_size    (int)  -- by default it is None, then it will create
                                    file with related content otherwise,
                                    it will create file with required size

        Returns:
            bool    -   file creation was successful or not

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to create file

        """
        self.log.info(
            "Creating file [{0}], with content [{1}], on client [{2}]".format(file_path, content, self.machine_name)
        )

        if file_size is None:
            command = 'echo -e "{1}" > "{0}"'.format(file_path, content)
            output = self.execute(command)
        elif isinstance(file_size, int):
            _create_file_with_size = \
                r"dd if=/dev/urandom of=%s bs=1024 count=%s" % (
                    file_path, str(round(file_size / 1024)))
            output = self.execute(_create_file_with_size)
        else:
            raise Exception('file size need to be integer value')

        if output.exception_message:
            if output.exception_message.find('records in') > 0:
                # for create stub with size the dd operation actual
                #  will return message
                # for onepass create data with size return result processing
                return True
            else:
                raise Exception(output.exception_code,
                                output.exception_message
                                )
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return str(output.formatted_output).lower() == ''

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
        output = self.execute_command('echo "{1}" >> {0}'.format(file_path, content))

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def mount_network_path(self, network_path, username, password, cifs_client_mount_dir=None):
        """Mounts the specified cifs share path on this machine

        Args:
            network_path    (str)   --  cifs share path that is to be mounted

            username        (str)   --  username to access network path
                Ex: DOMAIN\\USERNAME

            password        (str)   --  password to access network path

            cifs_client_mount_dir (str) -- if provided mount the network_path to this
        Returns:
            (str)   -   mounted drive name

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to mount network path

        """
        random_string = "".join(
            [random.choice(string.ascii_letters) for _ in range(4)])
        mount_path = "/Mount" + random_string

        if cifs_client_mount_dir and type(
                cifs_client_mount_dir) is str:  # if mount path is already provided then use it
            mount_path = cifs_client_mount_dir

        self.create_directory(mount_path)

        network_path = network_path.replace("\\", "/")
        username = username.split("\\")
        username, domain = username[1], username[0]

        mount_command = r'mount -t cifs -o username={0},password={1},domain={2} "{3}" {4}'.format(
            username, password, domain, network_path, mount_path
        )

        self.log.info("Executing mount command [{0}] on client [{1}]".format(mount_command, self.machine_name))

        output = self.execute_command(mount_command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return mount_path

    def get_process_dump(self, process_id, dump_path=None):
        """Gets the process dump for the given process ID

            Args:
                process_id      (str)   --      The process ID to collect the dump for
                dump_path       (str)   --      Path where core file is created

            Returns:
                None

            Raises:
                Exception - If any error while executing the script

            Note:
                We are using gcore to generate dump of the process. The dump should be present at dCOREDIR directory.
        """
        if not dump_path:
            dump_path = self.get_registry_value('EventManager', 'dEVLOGDIR')
        cmd = f'cd {dump_path} && gcore {process_id}'
        output = self.execute(cmd)
        output = output.formatted_output
        if 'Saved' in output[-2][0]:
            core_file = output[-2][2]
            dump_file_path = f'{dump_path}/{core_file}'
            return dump_file_path
        else:
            raise Exception(f"Core file couldn't be created on {dump_path} with output {output}")

    def unmount_path(self, mount_path, delete_folder=False, force_unmount=False):
        """Dis mounts the mounted path

        Args:
            mount_path    (str)   --  path which is mounted on this machine

            delete_folder (str)   --  delete folder after unmount is successful

            force_unmount (str)   --  force unmount in case of stale mount points
        Returns:
            bool    - dis mount network path operation status

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to mount network path
        """
        # added -f -l to force unmount in case of unreachable NFS server and lazy unmount
        if force_unmount:
            unmount_cmd = r'umount -f -l ' + mount_path
        else:
            unmount_cmd = r'umount ' + mount_path

        output = self.execute_command(unmount_cmd)

        if output.exception_message:
            if 'device is busy' in output.exception_message:
                lsof_cmd = "lsof -b | grep -i " + mount_path
                output = self.execute_command(lsof_cmd)
                self.log.info("process accessing the share. output of lsof command %s" %
                              output.output)
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        if delete_folder:
            if not self.remove_directory(mount_path):
                raise Exception("Exception while deleting folder: unmount_path()")

        return True

    def copy_folder_to_network_share(self, source_path, network_path, username, password, **kwargs):
        """Copies the source directory on controller machine to cifs share share path

        Args:
            source_path     (str)   --  source directory whose contents are to be copied

            network_path    (str)   --  cifs share path where the files are to be copied

            username        (str)   --  username to access network path
                Ex: DOMAIN\\USERNAME

            password        (str)   --  password to access network path

            \*\*kwargs          (dict)  --  optional arguments (not used in Unix machine)

        Returns:
            bool    -   status of copy folder to network path

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to mount network path


                if failed to copy files to mounted drive

                if failed to un mount network drive

        """
        # Mount Network shared path on this machine
        mount_path = self.mount_network_path(network_path, username, password)

        copy_cmd = r'cp -R "{0}" "{1}"'.format(source_path, mount_path)

        output = self.execute(copy_cmd)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        # Un mount network shared path
        self.unmount_path(mount_path)

        return True

    def copy_folder(self, source_path, destination_path, optional_params='', **kwargs):
        """Copies the directory specified at source path to the destination path.

        Args:
            source_path     (str)   --  source directory to be copied

            destination_path    (str)   --  destination path where the folder has to be copied

            optional_params   (str)  --  optional parameters which need to be passed for
            copy command. Example -f (force copy), -p (preserve meta data) etc

            \*\*kwargs          (dict)  --  optional arguments (Not used in Unix machine)
                Available kwargs Options:

                    recurse     (bool)  --  False if you do not want to recurse into subfolders
                                            Default: True

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to connect to the machine where the copy has to done locally

                if failed to copy files from source to destination

                if either of the source or destination path specifies is wrong

        """
        source_path = f'"{self.join_path(source_path, self.os_sep)}"'
        destination_path = f'"{self.join_path(destination_path, self.os_sep)}"'
        # remove '-' if passed
        optional_params = optional_params.replace('-', '')
        if kwargs.get('recurse', True):
            # older behavior. not changing this.
            # [cp is a bit un-consistent with recurse(-R). adding a note below for reference]
            # if src is /dirsrc (say has files f1, f2, subdir/) and dest is /dirdest:
            #   if dest dir doesn't exist:
            #       cp creates it and final data will be /dirdest/f1, /dirdest/f2, /dirdest/subdir/
            #       [i.e., it copies data that is ** inside /dirsrc **]
            #   if dest dir exists:
            #       final data will be /dirdest/dirsrc/f1, /dirdest/dirsrc/f2, /dirdest/dirsrc/subdir/
            #       [i.e., cp copies ** /dirsrc/ also ** to dest]
            optional_params = ' -R' + optional_params
        else:
            # since recurse(-R) is false, append '*' to source path to copy all files in src
            # if recurse is false, cp requires dest. dir to be already present hence creating it.
            # if src is /dirsrc (say has files f1, f2, subdir/) and dest is /dirdest,
            # final data will be /dirdest/f1, /dirdest/f2. subdir will be skipped
            if not self.check_directory_exists(destination_path):
                self.create_directory(destination_path)
            source_path = f'{source_path}*'
            optional_params = (' -' + optional_params) if optional_params else ''

        copy_cmd = r'cp{2} {0} {1}'.format(source_path, destination_path, optional_params)
        output = self.execute(copy_cmd)

        if output.exception_message:
            # skip raising exception if recurse is off and exception message has omitting dir
            # as it is expected to skip sub dir's with recurse off
            if not ((not kwargs.get('recurse', True)) and ('omitting directory' in output.exception_message.lower())):
                raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def copy_file_locally(self, source, destination):
        """
        Copies file from one directory to another or copies file in same directory
        Args:
            source(str)         --  Source file path
            destination(str)    --  destination file path
        Raises:
            Exception when copy file fails
        """
        command = f'cp -p {source} {destination}'
        output = self.execute_command(command)
        if output.exception_message:
            raise Exception(output.exception_code,
                            output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def read_file(self, file_path, **kwargs):
        """Returns the contents of the file present at the specified file path.

        Args:
            file_path   (str)   --  Full path of the file to get the contents of.

            \*\*kwargs  (dict)  --  Optional arguments

            Available kwargs Options:

                offset  (int)   :   Offset in the file, specified in bytes, from where content needs to be read.

        Returns:
            str     -   string consisting of the file contents

        Raises:
            Exception:
                if no file exists at the given path

                if failed to get the contents of the file

        """
        offset = kwargs.get('offset', None)
        search_term = kwargs.get('search_term', None)

        if offset:
            output = self.execute_command("tail {FILE_PATH} -c +`expr {OFFSET} + 1`".format(FILE_PATH=file_path,
                                                                                            OFFSET=offset))
        elif search_term:
            output = self.execute_command('grep \"{SEARCH_TERM}\" {FILE_PATH}'.format(SEARCH_TERM=search_term,
                                                                                      FILE_PATH=file_path))
        else:
            output = self.execute_command('cat {0}'.format(file_path))

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
        self.log.info("Deleting file [{0}] on client [{1}]".format(file_path, self.machine_name))

        output = self.execute_command('rm -f "{0}"'.format(file_path))

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def generate_test_data(
            self,
            file_path,
            dirs=3,
            files=5,
            file_size=20,
            levels=1,
            hlinks=True,
            slinks=True,
            hslinks=False,
            sparse=True,
            sparse_hole_size=1024,
            acls=False,
            unicode=False,
            xattr=False,
            long_path=False,
            long_level=1500,
            problematic=False,
            zero_size_file=True,
            options="",
            **kwargs):
        """Generates and adds random test data
            at the given path with the specified options

        Args:
            file_path           (str)   --  directory path where
                                            the data will be generated.

            dirs                (int)   --  number of directories
                                            in each level

                default: 3

            files               (int)   --  number of files
                                            in each directory

                default: 5

            file_size           (int)   --  Size of the files in KB

                default: 20

            levels              (int)   --  number of levels to be created

                default: 1

            hlinks              (bool)  --  whether to create
                                            hardlink files

                default: True

            slinks              (bool)  --  whether to create
                                            symbolic link files

                default: True

            hslinks             (bool)  --  whether to create
                                            symbolic link files with hardlinks.

                default: False

            sparse              (bool)  --  whether to create sparse files

                default: True

            sparse_hole_size    (int)   --  Size of the holes
                                            in sparse files in KB

                default: 1024

            long_path           (bool)  --  whether to create long files

                default: False

            long_level          (int)   --  length of the long path

                default: 1500

            acls                (bool)  --  whether to create
                                            files with acls

                default: False

            unicode             (bool)  --  whether to create
                                            unicode files

                default: False

            problematic         (bool)  --  whether to create
                                            problematic data

                default: False

            xattr               (bool)  --  whether to create files
                                            with xattr

                default: False

            zero_size_file               (bool)  --  whether to create files
                                            with zero kb

                default: True

            options             (str)   --  to specify any other
                                            additional parameters
                                            to the script.

                default: ""

        Returns:
            bool    -   boolean value True is returned
                        if no errors during data generation.

        Raises:
            Exception:
                if any error occurred while generating the test data.

        """
        script_arguments = (
            "-optype add -path \"{0}\" -dirs {1} -files {2} -sizeinkb {3} -levels {4}".format(
                file_path,
                str(dirs),
                str(files),
                str(file_size),
                str(levels)))

        if hlinks:
            script_arguments = "{0} -hlinks yes".format(script_arguments)
        else:
            script_arguments = "{0} -hlinks no".format(script_arguments)

        if slinks:
            script_arguments = "{0} -slinks yes".format(script_arguments)
        else:
            script_arguments = "{0} -slinks no".format(script_arguments)

        if hslinks:
            script_arguments = "{0} -hslinks yes".format(script_arguments)
        else:
            script_arguments = "{0} -hslinks no".format(script_arguments)

        if sparse:
            script_arguments = ("{0} -sparse yes"
                                " -holesizeinkb {1}".format(
                script_arguments, str(sparse_hole_size)))
        else:
            script_arguments = "{0} -sparse no".format(script_arguments)

        if long_path:
            script_arguments = ("{0} -long yes"
                                " -longlevel {1}".format(
                script_arguments, str(long_level)))
        else:
            script_arguments = "{0} -long no".format(script_arguments)

        if acls:
            script_arguments = "{0} -acls yes".format(script_arguments)
        else:
            script_arguments = "{0} -acls no".format(script_arguments)

        if xattr:
            script_arguments = "{0} -xattr yes".format(script_arguments)
        else:
            script_arguments = "{0} -xattr no".format(script_arguments)

        if unicode:
            script_arguments = "{0} -unicode yes".format(script_arguments)
        else:
            script_arguments = "{0} -unicode no".format(script_arguments)

        if self.os_flavour == 'OpenVMS':
            script_arguments = "{0} -isopenvms yes".format(script_arguments)
        else:
            script_arguments = "{0} -isopenvms no".format(script_arguments)

        delete_tar = False
        if problematic:
            tar_tmp_path = "/tmp/{0}".format(str(id(self)))
            self.create_directory(tar_tmp_path)
            self._copy_file_from_local(UNIX_PROBLEM_DATA, tar_tmp_path)
            custom_tar_path = "{0}/{1}".format(tar_tmp_path,
                                               os.path.basename(UNIX_PROBLEM_DATA))
            script_arguments = "{0} -customtar {1}".format(
                script_arguments, custom_tar_path)
            delete_tar = True

        script_arguments = "{0} {1}".format(script_arguments, options)

        output = self.execute(UNIX_MANAGE_DATA, script_arguments)

        if delete_tar:
            self.remove_directory(tar_tmp_path)
        if output.exit_code != 0:
            raise Exception(
                "Error occurred while generating test data "
                + output.output
                + output.exception
            )
        return True

    def modify_test_data(self,
                         data_path,
                         rename=False,
                         modify=False,
                         acls=False,
                         xattr=False,
                         permissions=False,
                         slinks=False,
                         hlinks=False,
                         options=""):
        """Modifies the test data at the given path
            based on the specified options

        Args:
            data_path   (str)   --  directory path where
                                    dataset resides.

            rename              (bool)  --  whether to rename all files

                default: False

            modify              (bool)  --  whether to modify

                                            data of all files
                default: False

            hlinks              (bool)  --  whether to add hard link
                                            to all files

                default: False

            permissions         (bool)  --  whether to change permission
                                            of all files

                default: False

            slinks              (bool)  --  whether to add symbolic link
                                            to all files

                default: False

            acls                (bool)  --  whether to change
                                            acls of all files

                default: False

            xattr               (bool)  --  whether to change
                                            xattr of all files

                default: False

            options             (str)   --  to specify any other
                                            additional parameters
                                            to the script.

                default: ""

        Returns:
            bool    -   boolean value True is returned
                        if no errors during data generation.

        Raises:
            Exception:
                if any error occurred while modifying the test data.

        """
        script_arguments = "-optype change -path \"{0}\"".format(data_path)

        if rename:
            script_arguments = "{0} -rename yes".format(script_arguments)
        else:
            script_arguments = "{0} -rename no".format(script_arguments)

        if modify:
            script_arguments = "{0} -modify yes".format(script_arguments)
        else:
            script_arguments = "{0} -modify no".format(script_arguments)

        if permissions:
            script_arguments = "{0} -permissions yes".format(script_arguments)
        else:
            script_arguments = "{0} -permissions no".format(script_arguments)

        if hlinks:
            script_arguments = "{0} -hlinks yes".format(script_arguments)
        else:
            script_arguments = "{0} -hlinks no".format(script_arguments)

        if slinks:
            script_arguments = "{0} -slinks yes".format(script_arguments)
        else:
            script_arguments = "{0} -slinks no".format(script_arguments)

        if acls:
            script_arguments = "{0} -acls yes".format(script_arguments)
        else:
            script_arguments = "{0} -acls no".format(script_arguments)

        if xattr:
            script_arguments = "{0} -xattr yes".format(script_arguments)
        else:
            script_arguments = "{0} -xattr no".format(script_arguments)

        script_arguments = "{0} {1}".format(script_arguments, options)
        self.log.info("Modifying test data in path [{0}]".format(data_path))
        output = self.execute(UNIX_MANAGE_DATA, script_arguments)

        if output.exit_code != 0:
            raise Exception(
                "Error occurred while modifying test data "
                + output.output
                + output.exception
            )
        return True

    def get_test_data_info(self,
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
        """Gets information about the items on the given path
            based on the given options

        Args:
            data_path             (str)   --  directory path from where
                                              the data should be retrieved.

            name                  (bool)  --  whether to get
                                              name of all the files

                default: False

            meta                  (bool)  --  whether to get
                                              meta data of all files

                default: True

            checksum              (bool)  --  whether to get
                                              OS checksum of all files

                default: False

            machinesort           (bool)  --  whether to sort
                                              the results on the machine

                default: False

            acls                  (bool)  --  whether to get
                                              acls of all files

                default: False

            xattr                 (bool)  --  whether to get
                                              xattr of all files

                default: False

            dirtime               (bool)  --  whether to get
                                              time stamp of all directories

                default: False

            skiplink              (bool)  --  whether to skip
                                              link count of all files

                default: False

            options               (str)   --  to specify any other
                                              additional parameters
                                              to the script.

                default: ""

            **kwargs  (dict)  --  Optional arguments

            Available kwargs Options:

                custom_meta_list (str)       :   Only return the item properties specified by the value of this argument.
                Accepts CSV string with supported values being LastWriteTime, LastAccessTime and CreationTime.


        Returns:
            list    -   list of output lines while executing the script.

        Raises:
            Exception:
                if any error occurred while getting the data information.

        """
        script_arguments = "-optype get -path \"{0}\"".format(data_path)

        if name:
            script_arguments = "{0} -name yes".format(script_arguments)
        else:
            script_arguments = "{0} -name no".format(script_arguments)

        if meta:
            script_arguments = "{0} -meta yes".format(script_arguments)
        else:
            script_arguments = "{0} -meta no".format(script_arguments)

        if checksum:
            script_arguments = "{0} -sum yes".format(script_arguments)
        else:
            script_arguments = "{0} -sum no".format(script_arguments)

        if acls:
            script_arguments = "{0} -acls yes".format(script_arguments)
        else:
            script_arguments = "{0} -acls no".format(script_arguments)

        if xattr:
            script_arguments = "{0} -xattr yes".format(script_arguments)
        else:
            script_arguments = "{0} -xattr no".format(script_arguments)

        if dirtime:
            script_arguments = "{0} -dirtime yes".format(script_arguments)
        else:
            script_arguments = "{0} -dirtime no".format(script_arguments)

        if skiplink:
            script_arguments = "{0} -skiplink yes".format(script_arguments)
        else:
            script_arguments = "{0} -skiplink no".format(script_arguments)

        if machinesort:
            script_arguments = "{0} -sorted yes".format(script_arguments)
        else:
            script_arguments = "{0} -sorted no".format(script_arguments)

        if kwargs and kwargs.get('custom_meta_list'):
            script_arguments = "{0} -custom_meta_list {1}".format(script_arguments,
                                                                  kwargs.get('custom_meta_list', 'no'))

        script_arguments = "{0} {1}".format(script_arguments, options)

        output = self.execute(UNIX_MANAGE_DATA, script_arguments)

        if output.exit_code != 0:
            raise Exception(
                "Error occurred while getting the data information "
                + output.output
                + output.exception
            )
        else:
            return output.output

    def get_uname_output(self, options="-s"):
        """Gets the uname output from the machine

        Args:
            options     (str)   --  options to uname command
                default: "-s"
        Returns:
            str    -   uname output

        Raises:
            Exception:
                if any error occurred while getting the uname output.

        """
        uname_cmd = r'uname  {0}'.format(options)
        output = self.execute(uname_cmd)

        if output.exit_code != 0:
            raise Exception(
                "Error occurred while getting uname output. "
                + output.output
                + output.exception
            )
        else:
            return output.formatted_output

    def get_registry_dict(self):
        """Gets dictionary of all the commvault registry keys and values
             from the machine

        Returns:
            dict    -   commvault registry keys and values

        Raises:
            Exception:
                if any error occurred while getting the registry keys

        """
        reg_command = ('find /etc/CommVaultRegistry/Galaxy/'
                       + self.instance + '/ -name .properties -exec cat {} \;')
        output = self.execute(reg_command)

        if output.exit_code != 0:
            raise Exception(
                "Error occurred while getting all registry keys "
                + output.output
                + output.exception
            )

        reg_list = output.output.split('\n')
        if not reg_list:
            raise Exception("No output returned for command :  " + reg_command)

        # Convert the list output to dict of key value pairs.
        reg_dict = {}

        for record in reg_list:
            item = record.split(' ', 1)
            item_len = len(item)
            if item_len == 1:
                reg_dict[item[0].strip()] = ""
            elif item_len == 2:
                reg_dict[item[0].strip()] = item[1].strip()

        return reg_dict

    def get_items_list(
            self,
            data_path,
            sorted_output=True,
            include_parents=False):
        """Gets the list of items at the given path.

        Args:
            data_path           (str)    --  directory path
                                             to get the items list

            sorted              (bool)   --  to specify whether
                                             the list should be sorted.

                default: True

            include_parents     (bool)   --  to specify whether
                                             parent paths should be include

                default: False

        Returns:
            list    -   list of the items

        Raises:
            Exception:
                if any error occurred while getting the items list.

        """
        find_cmd = r'find  "{0}" '.format(data_path)
        output = self.execute(find_cmd)

        if output.exit_code != 0:
            raise Exception(
                "Error occurred while getting items list from machine "
                + output.output
                + output.exception
            )
        else:
            output_list = output.output.split('\n')
            if include_parents:
                data_path = data_path.replace("//", "/")
                parent_list = ["/"]
                for itr in range(1, data_path.count('/')):
                    parent_list.append(data_path.rsplit('/', itr)[0])
                output_list.extend(parent_list)

            if sorted_output:
                output_list.sort()
            # remove empty items and return output list
            while '' in output_list:
                output_list.remove('')
            return output_list

    def get_meta_list(
            self,
            data_path,
            sorted_output=True,
            dirtime=False,
            skiplink=False):
        """Gets the list of meta data of items from the machine on a give path

         Args:
            data_path     (str)   --  directory path
                                        to get meta data of the items list

            sorted_output (bool)  --  to specify whether
                                        the list should be sorted.

            dirtime       (bool)  --  whether to get
                                        time stamp of all directories

                default: False

            skiplink      (bool)  --  whether to skip
                                        link count of all files

                default: False

        Returns:
            list    -   list of meta data of items from  the machine

        Raises:
            Exception:
                if any error occurred while getting the meta data of items.

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
                'Error occurred while getting meta data from machine '
                + str(excp)
            )

    def compare_meta_data(self, source_path, destination_path, dirtime=False, skiplink=False):
        """Compares the meta data of source path with destination path
            and checks if they are same.

         Args:
            source_path         (str)   -- source path to compare

            destination_path    (str)   -- destination path to compare

            dirtime             (bool)  --  whether to get
                                        time stamp of all directories

                default: False

            skiplink            (bool)  --  whether to skip
                                        link count of all files

                default: False

        Returns:
            bool, str   -   Returns True, if metadata of source and destination are same
                diff output between source and destination

        Raises:
            Exception:
                if any error occurred
                    while comparing the meta data of paths.

        """

        try:
            source_list = self.get_meta_list(source_path, dirtime=dirtime, skiplink=skiplink)
            destination_list = self.get_meta_list(
                destination_path, dirtime=dirtime, skiplink=skiplink)
            return self._compare_lists(source_list, destination_list)
        except Exception as excp:
            raise Exception(
                'Error occurred while comparing the metadata: ' + str(excp)
            )

    def get_checksum_list(self, data_path, sorted_output=True):
        """Gets the list of checksum of items from the machine on a give path
            this is Unix checksum , can't be used for md5sum comparision

             Args:
                data_path      (str/list)   --  directory path
                                            to get the checksum list

                sorted_output  (bool)  --  to specify whether
                                            the checksum list should be sorted.

            Returns:
                list    -   list of checksum of items from  the machine

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
            raise Exception(
                'Error occurred while getting checksum list from machine '
                + str(excp)
            )

    def compare_checksum(self, source_path, destination_path):
        """Compares the checksum of source path with destination path
            and checks if they are same. (This is Unix checksum)

         Args:
            source_path         (str) -- source path to compare

            destination_path    (str) -- destination path to compare

        Returns:
            bool, str   -   Returns True, if checksum of source and destination
               are samediff output between source and destination

        Raises:
            Exception:
                if any error occurred
                    while comparing the checksum of paths.

        """

        try:
            source_list = self.get_checksum_list(source_path)
            destination_list = self.get_checksum_list(destination_path)
            return self._compare_lists(source_list, destination_list)
        except Exception as excp:
            raise Exception(
                'Error occurred while comparing the checksums: ' + str(excp)
            )

    def get_acl_list(self, data_path, sorted_output=True):
        """Gets the list of acl of items from the machine on a give path

         Args:
            data_path     (str)   -- directory path to get the acl list

            sorted_output (bool)  -- to specify whether
                                        the acl list should be sorted.

        Returns:
            list    -   list of acl of items from  the machine

        Raises:
            Exception:
                if any error occurred while getting the acl of items.

        """
        try:
            acl_data = self.get_test_data_info(data_path, acls=True)
            if 'linux' in self.os_flavour.lower():
                acl_list = acl_data.split('# file:')
            elif 'darwin' in self.os_flavour.lower():
                output_list = acl_data.split('\n')
                acl_dict = {}
                acl_list = []
                current_key = ""
                for item in output_list:
                    if item.startswith(("d", "-", "l")):
                        meta_data = item.split(maxsplit=8)
                        if len(meta_data) < 9:
                            current_key = "/"
                        else:
                            current_key = meta_data[8]
                        acl_dict[current_key] = ""
                    elif item.startswith(
                            (" 0", " 1", " 2", " 3", " 4",
                             " 5", " 6", " 7", " 8", " 9")):
                        acl_dict[current_key] = "{0}{1}".format(
                            acl_dict[current_key], item)
                for key, value in iter(acl_dict.items()):
                    if value != "":
                        acl_list.append("{0} ::: {1}".format(key, value))
            else:
                acl_list = acl_data.split('\n')

            while '' in acl_list:
                acl_list.remove('')

            if sorted_output:
                acl_list.sort()

            return acl_list

        except Exception as excp:
            raise Exception(
                'Error occurred while getting acl list from machine '
                + str(excp)
            )

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
                'Error occurred while comparing the acls: ' + str(excp)
            )

    def get_xattr_list(self, data_path, sorted_output=True):
        """Gets the list of xattr of items from the machine on a give path

         Args:
            data_path      (str)   --  directory path to get the xattr list

            sorted_output  (bool)  --  to specify whether
                                        the xattr list should be sorted.

        Returns:
            list    -   list of xattr of items from  the machine

        Raises:
            Exception:
                if any error occurred while getting the xattr of items.

        """
        try:
            xattr_data = self.get_test_data_info(data_path, xattr=True)

            if 'linux' in self.os_flavour.lower():
                xattr_list = xattr_data.split('Attribute')
            else:
                xattr_list = xattr_data.split('\n')

            while '' in xattr_list:
                xattr_list.remove('')

            if sorted_output:
                xattr_list.sort()

            return xattr_list

        except Exception as excp:
            raise Exception(
                'Error occurred while getting xattr list from machine '
                + str(excp)
            )

    def compare_xattr(self, source_path, destination_path):
        """Compares the xattr of source path with destination path
            and checks if they are same.

         Args:
            source_path         (str)   -- source path to compare

            destination_path    (str)   -- destination path to compare

        Returns:
            bool, str   -   Returns True
                             if xattr of source and destination are same
                            diff output between source and destination

        Raises:
            Exception:
                if any error occurred while comparing the xattr of paths.

        """

        try:
            source_list = self.get_xattr_list(source_path)
            destination_list = self.get_xattr_list(destination_path)
            return self._compare_lists(source_list, destination_list)
        except Exception as excp:
            raise Exception(
                'Error occurred while comparing the xattrs: ' + str(excp)
            )

    def get_disk_count(self):
        """
        returns the number of disk in the machine

        return:
            disk_count  (int)   - disk count of the machine

        Raises:
                Exception(Exception_Code, Exception_Message):
                    if failed to get the disk count for the machine

        """

        output = self.execute_command('lsblk')
        mount_paths = set()
        for value in output.formatted_output[1:]:
            try:
                if len(value) > 6:
                    mount_paths.add(value[6])
            except ValueError:
                continue

        return len(mount_paths)

    def change_folder_owner(self, username, directory_path):
        """Changes the owner of the folder given as the value of directory_path.

        Args:
            username        (str)   --  name of user to give ownership

            directory_path  (str)   --  path of the directory to change ownership

        Returns:
            bool    -   boolean value if ownership change was successful

        Raises:
            Exception:
                if specified folder doesn't exist

        """
        if not self.check_directory_exists(directory_path):
            raise Exception(
                "{0} path does not exist on {1}".format(
                    directory_path, self.machine_name
                )
            )

        command = 'if chown {0} {1}; then echo "TRUE"; fi'.format(
            username, directory_path)

        output = self.execute(command)
        return str(output.formatted_output).lower() == 'true'

    def get_files_in_path(self, folder_path, recurse=True, only_hidden=False, days_old=0):
        """Returns the list of all the files at the given folder path.

        Args:
            folder_path     (str)   --  full path of the folder to get the list of files from
            recurse (bool) -- True -- as default value, if needs to recurse through sub folders
            only_hidden (bool) -- False -- as default value, if it lists only hidden files
            days_old (int) -- Number of days old to filter the files

        Returns:
            list    -   list of the files present at the given path

        Raises:
            Exception:
                if path is not valid
                if failed to get the list of files
        """
        return self._get_files_or_folders_in_path(folder_path, 'FILE', recurse, days_old)

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
            Exception:
                if path is not valid

                if failed to get the list of files / folders
        """

        folder_path = folder_path + self.os_sep if folder_path[-1] != self.os_sep else folder_path

        if not self.check_directory_exists(folder_path):
            raise Exception('Please give a valid path [{0}]'.format(folder_path))

        operation_type = 'f' if filesonly else 'd'

        default_command = "find {0}* -maxdepth 0 -type {1} -printf '%f '".format(folder_path, operation_type)
        os_flavour = {
            'darwin': "find {0}* -maxdepth 0 -type {1} ".format(folder_path, operation_type)
        }
        if filesonly:
            cmd = os_flavour.get(self.os_flavour.lower(), default_command)

        else:
            cmd = os_flavour.get(self.os_flavour.lower(), default_command)

        output = self.execute_command(cmd)

        if self.os_flavour.lower() == 'darwin':
            processed_output = []
            output_list = list(map(lambda x: ' '.join(x), output.formatted_output))
            for each_file in output_list:
                processed_output.append(os.path.basename(each_file))
            return processed_output

        else:
            if isinstance(output.formatted_output, list):
                return output.formatted_output
            return output.formatted_output.split(' ')

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
                Exception if failed to execute the command

        """

        parameter_type = ''
        if include_only == 'files':
            parameter_type = '-type f'
        elif include_only == 'folders':
            parameter_type = '-type d'

        parameter_recursive = '' if recursive else '-maxdepth 1'
        parameter_filter = '' if not filter_name else f' -name {filter_name}'

        cmd = f'find {folder_path} {parameter_recursive} {parameter_type} {parameter_filter} | wc -l'

        output = self.execute_command(cmd)

        try:
            return int(output.formatted_output)
        except ValueError:
            return 0

    def disconnect(self):
        """Disconnects the current session with the machine."""
        if self._client:
            self._client.close()

        super(UnixMachine, self).disconnect()

    def add_firewall_allow_port_rule(self, tunnel_port):
        """Adds the inbound rule for the given port number

        Args:
            tunnel_port (int): port number to be added in the inbound rule

        Returns:
            None: if rule addition is successful

        Raises:
            Exception:
                if command to add the firewall rule fails

                if current os flavor is not supported

        """

        # firewall-offline-cmd is used instead of firewall-cmd to handle the errors
        rule_cmd = {"Linux": "firewall-offline-cmd --direct --add-rule ipv4 filter "
                             "INPUT 0 -p tcp --dport {0} -j ACCEPT",
                    "Darwin": "echo \"pass in proto tcp from any port {0}\" | pfctl -f -"}

        if self.os_flavour not in rule_cmd:
            raise Exception(
                "current OS flavor {0} is not supported".format(self.os_flavour))

        cmd_success = False

        if self.os_flavour == "Linux":  # for linux we need to stop firewall first
            if self.get_firewall_state():
                self.stop_firewall()

        # define the command based on os flavor
        cmd = rule_cmd[self.os_flavour].format(tunnel_port)

        cmd_output = self.execute_command(cmd)

        # As the command status differs for OSX and Linux, we need to handle it separately
        if self.os_flavour == "Linux":
            if "success" in cmd_output.output:
                cmd_success = True
        else:
            if not cmd_output.exit_code:
                cmd_success = True

        if not cmd_success:
            raise Exception("adding firewall rule command {0} failed with "
                            "error {1}".format(cmd, cmd_output.output))

    def start_firewall(self):
        """start firewall services on the current client machine

        Returns:
            None: if firewall started successfully

        Raises:
            Exception:
                if command to start firewall service fails

                if current os flavor is not supported

        """

        start_firewall_cmd = {"Linux": "systemctl enable firewalld",
                              "Darwin": "/usr/libexec/ApplicationFirewall/socketfilterfw "
                                        "--setglobalstate on"}

        if self.os_flavour not in start_firewall_cmd:
            raise Exception(
                "current OS flavor {0} is not supported".format(self.os_flavour))

        cmd_success = False

        # define the command based on the os flavor
        cmd = start_firewall_cmd[self.os_flavour]
        cmd_output = self.execute_command(cmd)

        # As the command status differs for OSX and Linux, we need to handle it separately
        if self.os_flavour == "Linux":
            if not cmd_output.exit_code:
                cmd_success = True
        else:
            if "enabled" in cmd_output.output:
                cmd_success = True

        if not cmd_success:
            raise Exception("starting firewall service command {0} failed with "
                            "error {1}".format(cmd, cmd_output.output))

    def remove_firewall_allow_port_rule(self, tunnel_port):
        """removes the inbound rule for the given port number

        Args:
            tunnel_port (int): port number to be removed in the inbound rule

        Returns:
            None: if rule deletion is successful

        Raises:
            Exception:
                if command to delete the firewall rule fails

                if current os flavor is not supported

        """

        # firewall-offline-cmd is used instead of firewall-cmd to handle the errors
        rule_cmd = {"Linux": "firewall-offline-cmd --direct --remove-rule ipv4 filter "
                             "INPUT 0 -p tcp --dport {0} -j ACCEPT",
                    "Darwin": "pfctl -F rules"}  # TODO: need to explore on -a <anchors> options to
        # clear a specific rule

        if self.os_flavour not in rule_cmd:
            raise Exception(
                "current OS flavor {0} is not supported".format(self.os_flavour))

        cmd_success = False

        # define the command based on os flavor
        cmd = rule_cmd[self.os_flavour].format(tunnel_port)

        cmd_output = self.execute_command(cmd)

        # As the command status differs for OSX and Linux we need to handle it
        if self.os_flavour == "Linux":
            # in case of exception this rule may not be added. Hence "not in list"
            # is handled here
            msgs = ["success", "not in list"]
            if "success" in cmd_output.output or \
                    "not in list" in cmd_output.exception_message:
                cmd_success = True
        else:
            if not cmd_output.exit_code:
                cmd_success = True

        if not cmd_success:
            raise Exception("deleting firewall rule command {0} failed with "
                            "error {1}".format(cmd, cmd_output.output))

    def stop_firewall(self):
        """turn off firewall service on the current client machine

        Returns:
            None: firewall is turned off successfully

        Raises:
            Exception:
                if command to turn off firewall fails

                if current os flavor is not supported

        """
        stop_firewall_cmd = {"Linux": "service firewalld stop",
                             "Darwin": "/usr/libexec/ApplicationFirewall/socketfilterfw "
                                       "--setglobalstate off"}

        if self.os_flavour not in stop_firewall_cmd:
            raise Exception(
                "current OS flavor {0} is not supported".format(self.os_flavour))

        cmd_success = False

        # define the command based on os flavor
        cmd = stop_firewall_cmd[self.os_flavour]
        cmd_output = self.execute_command(cmd)

        # As the command status differs for OSX and Linux, we need to handle it separately
        if self.os_flavour == "Linux":
            if not cmd_output.exit_code:
                cmd_success = True
        else:
            if "disabled" in cmd_output.output:
                cmd_success = True

        if not cmd_success:
            raise Exception("turn off firewall command {0} failed with "
                            "error {1}".format(cmd, cmd_output.output))

    def add_firewall_machine_exclusion(self, machine_to_exclude=None):
        """Adds given machine to firewall exclusion list. If machine details is
           not passed, it considers current machine and adds it to exclusion list.

        Args:
            machine_to_exclude  (str)   --  hostname or IP address to be added to
            firewall exclusion list

        Returns:
            None    -   if machine is successfully added to firewall exclusion list

        Raises:
            Exception:
                if command to add the firewall exclusion rule fails

                if current os flavor is not supported

        """

        add_firewall_exclusion = {"Linux": "firewall-offline-cmd --direct --add-rule ipv4 filter "
                                           "INPUT 0 -s {0} -j ACCEPT",
                                  "Darwin": "echo \"pass in from {0} to any\" | pfctl -f -"}

        if self.os_flavour not in add_firewall_exclusion:
            raise Exception(
                "current OS flavor {0} is not supported".format(self.os_flavour))

        if machine_to_exclude is None:
            machine_to_exclude = socket.gethostbyname(socket.gethostname())

        if self.os_flavour == "Linux":  # for linux we need to stop firewall first
            if self.get_firewall_state():
                self.stop_firewall()

        # define the command based on os flavor
        cmd = add_firewall_exclusion[self.os_flavour].format(machine_to_exclude)

        cmd_output = self.execute_command(cmd)

        if cmd_output.exit_code:
            raise Exception("adding firewall exclusion rule command {0} failed "
                            "with error {1}".format(cmd, cmd_output.output))

    def remove_firewall_machine_exclusion(self, excluded_machine=None):
        """removes given machine from firewall exclusion list. If machine details is
           not passed, it considers current machine and removes it from exclusion list.

                excluded_machine (str): hostname or IP address to be removed from
                    firewall exclusion list

        Returns:
            None: if machine is successfully removed from firewall exclusion list

        Raises:
            Exception:
                if command to delete from firewall exclusion rule fails

                if current os flavor is not supported

        """
        if excluded_machine is None:
            excluded_machine = socket.gethostbyname(socket.gethostname())

        remove_firewall_exclusion = {"Linux": "firewall-offline-cmd --direct --remove-rule "
                                              "ipv4 filter INPUT 0 -s {0} -j ACCEPT",
                                     "Darwin": "pfctl -F rules"
                                     }

        if self.os_flavour not in remove_firewall_exclusion:
            raise Exception(
                "current OS flavor {0} is not supported".format(self.os_flavour))

        # define the command based on os flavor
        cmd = remove_firewall_exclusion[self.os_flavour].format(excluded_machine)
        cmd_output = self.execute_command(cmd)
        if cmd_output.exit_code:
            raise Exception("removing firewall exclusion command {0} failed with "
                            "error {1}".format(cmd, cmd_output.output))

    def get_firewall_state(self):
        """get the current state of the firewall service on the current machine

        Returns:
            True (bool): if firewall service is running

            False (bool): if firewall service is not running

            bool    -   boolean value if ownership change was successful

        Raises:
            Exception:

                if command to get the firewall state rule fails

                if current os flavor is not supported

                if specified folder doesn't exist

        """
        firewall_cmd = {"Linux": "firewall-cmd --state",
                        "Darwin": "/usr/libexec/ApplicationFirewall/socketfilterfw "
                                  "--getglobalstate"
                        }
        if self.os_flavour not in firewall_cmd:
            raise Exception(
                "current OS flavor {0} is not supported".format(self.os_flavour))

        firewall_state_string = {"Linux": "running", "Darwin": "is enabled"}
        firewall_status = False

        cmd = firewall_cmd[self.os_flavour]

        cmd_output = self.execute_command(cmd)
        if firewall_state_string[self.os_flavour] in cmd_output.output:
            firewall_status = True

        return firewall_status

    def mount_nfs_share(self, nfs_client_mount_dir, server, share, cleanup=False, version="4"):
        """ mounts the given NFS mount path

            Args:
                nfs_client_mount_dir  (str)  --  local directory for nfs mount path

                server                (str)  --  nfs server hostname or ip address

                share                 (str)  --  nfs server share path

                cleanup               (bool) --  flag to unmount before mounting

                version               (str) --   nfs v3 or v3 client. Expected (3 or 4)


            Returns:
                None

            Raises:
                Exception(Exception_Code, Exception_Message):
                    if failed to mount network path
        """
        if cleanup:
            self.unmount_path(nfs_client_mount_dir)

        # Create Directory to mount

        self.create_directory(nfs_client_mount_dir, True)
        if version is not None:
            # Mount the object store as NFS share on client machine
            cmd = "/usr/bin/mount -t nfs -o vers={3} {0}:{1} {2}".format(
                server,
                share,
                nfs_client_mount_dir,
                version)
        else:
            cmd = "/usr/bin/mount -t nfs {0}:{1} {2}".format(server,
                                                             share,
                                                             nfs_client_mount_dir)

        self.log.info("running mount command {0}".format(cmd))
        output = self.execute_command(cmd)
        if output.exit_code != 0:
            raise Exception("mountNFS_share(): exception while mounting "
                            "Share. output:{0}, exception:{1}".format(output.exception,
                                                                      output.exception_message))

    def get_snapshot(self, directory_path):
        """
        gets meta data(ls -l) and md5sum of each file in the given directory

        Args:
            directory_path     (str)   - path of the folder to get the data

         Returns:
                file_list   (list)-   list containing ["%m %n %u %g %s \" -exec md5sum]

        Raises:
            Exception:
                if failed to get the list of files

        """

        cmd = "find " + directory_path + " ! -type d -printf \"%m %n %u %g %s %f\n \" " \
                                         "-exec md5sum \{\} \;"
        output = self.execute_command(cmd)
        if output.exit_code != 0:
            raise Exception("get_snapshot(): Error occurred while executing cmd "
                            "cmd:{0}, output:{1}, exception:{2}".format(cmd,
                                                                        output.output,
                                                                        output.exception))
        return output.output.split('\n')

    def scan_directory(self, path, filter_type=None, recursive=True):
        """Scans the directory and returns a list of items under it along with its properties

            Args:
                path            (str)           Path of directory to scan

                filter_type     (str)           Filters the list by item type. Possible values
                are file, directory

                recursive       (bool)          Decides to whether to get items recursively or from
                current directory alone

            Returns:
                list    -       List of items under the directory with each item being a
                dictionary of item properties

        """

        scanned_items = []
        all_items = []
        recursive = ' -maxdepth 1 ' if not recursive else ''

        files_out = self.execute_command(
            'find {0} {1} -type f -printf "%p;file;%s;%C@|"'.format(path, recursive))

        if files_out.exit_code != 0:
            raise Exception('Failed to scan files under path [{0}]'.format(path))
        else:
            all_items = all_items + files_out.output.split('|')

        folders_out = self.execute_command(
            'find {0} {1} -type d -printf "%p;directory;%s;%C@|"'.format(path, recursive))

        if folders_out.exit_code != 0:
            raise Exception('Failed to scan folders under path [{0}]'.format(path))
        else:
            all_items = all_items + folders_out.output.split('|')

        symlink_out = self.execute_command(
            'find {0} {1} -type l  -printf "%p;file;%s;%C@|"'.format(path, recursive))

        if symlink_out.exit_code != 0:
            raise Exception('Failed to scan symlinks under path [{0}]'.format(path))
        else:
            all_items = all_items + symlink_out.output.split('|')

        for item in all_items:
            item = item.strip()

            if item == '':
                continue

            i_props = item.split(';')

            if len(i_props) != 4:
                raise Exception(
                    'Some properties are missing for item [{0}]'.format(str(i_props)))

            if filter_type is not None and filter_type != i_props[1]:
                continue

            scanned_items.append({
                'path': i_props[0],
                'type': i_props[1],
                'size': i_props[2],
                'mtime': int(float(i_props[3]))
            })

        return scanned_items

    def is_path_mounted(self, mount_path):
        """ check whether given path is mounted

            Args:
                mount_path  (str)  --  local directory for nfs mount path

            Returns:
                True  -- if mount_path is mounted

                False -- if mount_path is not mounted

            Raises:
                Exception(Exception_Code, Exception_Message):
                    if failed to mount network path
        """

        is_mounted = False
        cmd = "mount | grep -c {0} ".format(mount_path)
        output = self.execute_command(cmd)
        if output.exception:
            raise Exception("is_path_mounted(): Error occurred while executing cmd "
                            "cmd:{0}, output:{1}, exception:{2}".format(cmd,
                                                                        output.output,
                                                                        output.exception))
        if int(output.output) >= 1:
            is_mounted = True

        return is_mounted

    def rsync_local(self, source, destination):
        """sync source and destination local folders on the client machine
            Args:
                source (string)      --  source path of directory

                destination (string) -- destination path of directory

            Returns:
                None

            Raises:
                Exception:
                    if any error occurs in the rsync command execution
        """

        cmd = "/usr/bin/rsync -avz --delete {0} {1}".format(source, destination)
        output = self.execute_command(cmd)
        if output.exit_code != 0:
            raise Exception("rsync(): Error occurred while executing cmd "
                            "cmd:{0}, output:{1}, exception:{2}".format(cmd,
                                                                        output.output,
                                                                        output.exception))

    def modify_file_time(self, path, which_time=None):
        """
        Changes the file modification time or access time .

            Args:
                path (str): file full path

                which_time (str): default value -None it will change file
                                  modification time,
                                  access time and create time to current time
                                  'mtime'  -will change file Mtime
                                  'atime'  -will change file Atime
            Returns:
                no return,
                in case fail to change file time, it will raise exception

            Raises:
                Exception:
                    if specified file doesn't exist

         """
        try:
            if not self.check_file_exists(path):
                raise Exception(
                    "{0} path does not exist on {1}".format(
                        path, self.machine_name))
            if which_time == 'atime':
                time_attr = '-a'
            elif which_time == 'mtime':
                time_attr = '-m'
            else:
                time_attr = ''

            command = 'touch %s %s' % (time_attr, path)
            output = self.execute(command)
            if output.exit_code != 0:
                raise Exception("fail to modify file time,raise exception")
        except Exception as excp:
            raise Exception("Exception raised with error %s" % excp)

    def is_stub(self, file_name, is_nas_turbo_type=False):
        """
        This function will use unix cxfs_util function to verify
        whether file is stub

            Args:
                file_name (str): file full name

                is_nas_turbo_type  (bool): True for NAS based client.
                    default -   None

             Return: True if the file is stub otherwise return False

             Raises:
                Exception:
                        if error occurred
        """
        try:
            if not self.check_file_exists(file_name):
                raise Exception(
                    "{0} path does not exist on {1}".format(
                        file_name, self.machine_name))
            binary_name = "cxfs_util"
            _reg_value_dict = self.get_registry_dict()
            if 'dBASEHOME' not in _reg_value_dict:
                raise Exception('fail to get client machine base folder, ' +
                                'we need simpana product installed before ' +
                                'run this test case, please check setup ' +
                                'and re-run again')
            else:
                _base_folder = _reg_value_dict['dBASEHOME'] + '/'
                _cmd = "cd %s; . ../galaxy_vm; . ./cvprofile; %s%s -l %s " % (
                    _base_folder, _base_folder, binary_name, file_name)
                output = self.execute(_cmd)
                if output.exit_code == 0:
                    if output.formatted_output.upper().find('NOT A STUB') == -1:
                        return True
                    else:
                        return False
                else:
                    raise Exception("Exception raised at is_stub function")
        except Exception:
            raise Exception("exception raised at is_stub function ")

    def get_hardware_info(self):
        """ returns the hardware specifications of this machine like cores/logical processor count/RAM/Architecture

        Returns:

            dict        --  containing all the CPU hardware info

                    Example : {
                                  "MachineName" : "xyz",
                                  "CPUModel": "Intel(R) Xeon(R) Silver 4116 CPU @ 2.10GHz",
                                  "NumberOfLogicalProcessors": "16",
                                  "OSArchitecture": "x86_64",
                                  "MaxClockSpeed": 2095,
                                  "NumberOfCores": "16",
                                  "MachineName": "cvsnalinux.sna.commvault.com",
                                  "RAM": "15GB",
                                  "OS": "UNIX",
                                  "OSFlavour": "Linux",
                                  "Storage": {
                                    "total": 436366.66,
                                    "available": 417951.17,
                                    "mountpoint": "///dev/dev/shm/run/sys/fs/cgroup/boot/home/run/user/0",
                                    "/dev/mapper/centos-root": {
                                      "total": 350819,
                                      "available": 332589.14,
                                      "mountpoint": "/"
                                    }
                                  }
                                }

        Raises:
                Exception:
                    if any error occurred while getting the details

        """
        cmd = f"lscpu"
        output = self.execute_command(command=cmd)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)
        output_list = output.output.split('\n')
        output_dict = {}
        temp_dict = {}
        separator = ':'
        for i, item in enumerate(output_list):
            if separator not in item:
                continue
            value = item.split(separator)
            temp_dict[value[0]] = value[1].strip()
        output_dict['CPUModel'] = temp_dict['Model name']
        output_dict['NumberOfLogicalProcessors'] = temp_dict['CPU(s)']
        output_dict['OSArchitecture'] = temp_dict['Architecture']
        output_dict['MaxClockSpeed'] = int(float(temp_dict['CPU MHz']))
        output_dict['NumberOfCores'] = temp_dict['Core(s) per socket']
        cmd = f"hostname"
        output = self.execute_command(command=cmd)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)
        output_dict['MachineName'] = output.formatted_output
        cmd = f"free -g | grep -w Mem | tr -s [:space:] ,"
        output = self.execute_command(command=cmd)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)
        output_dict['RAM'] = f"{output.output.split(',')[1]}GB"
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
        cmd = f"ps -ef | grep -w " + process_name + " | grep -v grep"
        if command_line_keyword is not None:
            cmd = f"{cmd} | grep -w {command_line_keyword}"
        cmd = f"{cmd} | awk '{{print $2}}'"
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
        return pid_list

    def get_process_stats(self, process_id):
        """Gets the process stats like Handle count, memory used, CPU usage, thread count at the requested time
        for the given process ID

            Args:
                process_id      (str)   --      The process ID to get the stats for

            Returns:
                (dict)  --  A dictionary with the stat and it's value (int).
                            Empty dictionary if process ID does not exist.

                Example: {
                    'handle_count': '100',
                    'memory': '456202665'  # in bytes
                    'thread_count': '20'
                    'cpu_usage': '2'
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

        self._script_generator.script = UNIX_GET_PROCESS_STATS

        script = self._script_generator.run(script_arguments)
        output = self.execute(script)
        os.unlink(script)

        if not output.formatted_output.strip():
            return {}

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        all_processes = output.formatted_output.split('\n')  # When we get multiple results by any chance
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

    def get_port_usage(self, process_id=None, all_protocols=True):
        """ get the netstat connection stats for the process or machine

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
        if process_id is not None and not self.is_process_running(process_name=str(process_id)):
            raise Exception("Specified process is not running")
        state_list = [
            'established',
            'time-wait',
            'closed',
            'close-wait',
            'listening',
            'closing',
            'fin-wait-1',
            'fin-wait-2']
        cmd = ''
        for state in state_list:
            cmd = f"{cmd} ss state {state} -tp"
            if process_id is not None:
                cmd = f"{cmd} | grep -w \"pid={process_id}\""
            cmd = f"{cmd} | wc -l ; "
        cmd = cmd[:-3]
        output = self.execute_command(cmd)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)
        else:
            if isinstance(output.formatted_output, list):
                for state in range(len(state_list)):
                    out_dict[state_list[state]] = output.formatted_output[state][0]
        if all_protocols:
            cmd = f"ss -upa"
            if process_id is not None:
                cmd = f"{cmd} | grep -w \"pid={process_id}\""
            cmd = f"{cmd} | wc -l"
            output = self.execute_command(cmd)
            if output.exception_message:
                raise Exception(output.exception_code, output.exception_message)
            elif output.exception:
                raise Exception(output.exception_code, output.exception)
            else:
                out_dict['UDP'] = output.formatted_output
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
                cmd = ("ps -ef | grep -w " + process_name + " | grep -v grep")
                out = self.execute_command(cmd)
                if len(out.exception) == 0 and out.output is not None and out.output != "":
                    self.log.info("Found process running: %s", process_name)
                    flag = True
                    return flag
                elif len(out.exception) > 0:
                    self.log.exception(
                        "Exception code: %s, Exception Message: %s, Output Msg: %s",
                        out.exception_code, out.exception_message, out.output
                    )
                time.sleep(poll_interval)
                current_time = time.time()
            self.log.info("Process [%s] not found with in stipulated time: %d ", process_name, time_out)
            return flag
        except Exception as excp:
            raise Exception("Exception raised while is process running: %s" % str(excp))

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
                    self.log.info("Process exited: %s", process_name)
                    flag = True
                    return flag
                time.sleep(poll_interval)
                current_time = time.time()
            self.log.info("Process didn't exited: %s within stipulated time: %d ", process_name, time_out)
            return flag
        except Exception as excp:
            raise Exception("Exception raised while waiting for process to exit: %s" % str(excp))

    def add_user(self, user, encrypted_password):
        """create new user account using values passed to method

        Args:
            user                (str)   --  username string to be used to create account

            encrypted_password  (str)   --  The encrypted password, as returned by crypt(3)

        Returns:
            None

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to create user account

        """
        # TODO: encrypted_password = crypt.crypt(self.default_password)
        cmd = '/usr/sbin/adduser {0} -p \'{1}\''.format(user, encrypted_password)
        self.log.debug("running command {0} to add user".format(cmd))
        output = self.execute_command(cmd)
        if output.exception:
            raise Exception("Error while adding user:{0)\n"
                            "output:{1} error:{2}".format(user,
                                                          output.formatted_output,
                                                          output.exception_message))

    def delete_users(self, users):
        """delete a user account and Files in the user's home directory

        Args:
            users   (list)   --  list of valid existing usernames

        Returns:
            None

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to delete user

        """
        for user in users:
            cmd = "/usr/sbin/userdel -f -r {0}".format(user)
            self.log.debug("running command {0} to delete user".format(cmd))
            output = self.execute_command(cmd)
            if output.exception and \
                    'is currently used by process' not in output.exception:
                raise Exception("Error while deleting user:{0}\n"
                                "output:{1} error:{2}".format(user,
                                                              output.formatted_output,
                                                              output.exception_message))

    def change_file_permissions(self, file_path, file_permissions):
        """change file mode bits for the given file or directory path

        Args:
            file_path            (str)   --  path of file to be modified with mode bits

            file_permissions     (str)   --  valid RWX bits which needs to be set

        Returns:
            None

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to change file mode bits

        """
        cmd = "chmod {0} {1}".format(file_permissions, file_path)
        self.log.debug("running command {0} to change file permission".format(cmd))
        output = self.execute_command(cmd)
        if output.exception:
            raise Exception("Error while changing user permissions\n"
                            "output:{0} error:{1}".format(output.output,
                                                          output.exception_message))

    def get_file_permissions(self, file_path):
        """Gets the file permissions of the given file or directory

            Args:

                file_path       (str)   --  Path of the file to retrieve permissions for

            Returns:
                (str)   --      Returns the 3 digit octal file permissions number. Example: 776

            Raises:
                Exception, if failed to execute command to get the file permissions number

        """

        cmd = "stat --format '%a' '{0}'".format(file_path)

        output = self.execute_command(cmd)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.output.strip()

    def nfs4_setfacl(self, object_path, ace_type, ace_principal, ace_permissions, ace_flags='',
                     user_group_flag=False):
        """manipulates the NFSv4 Access Control List (ACL) of one or more files (or directories),
           provided they are on a mounted NFSv4 filesystem which supports ACLs.

            Args:
                object_path      (str)    -- path of file or directory for which ACL
                need to be applied

                ace_type         (str)    -- action which need to taken (Allow/Deny)

                ace_principal    (str)    -- people for which we are applying the access
                (1004/testuser1)

                ace_permissions  (object) -- permissions which needs to be applied (r/w/a/x)

                ace_flags       (str)     -- different types inheritance (d/f/n/i)

                user_group_flag (bool)    -- when ace_principal is group this flag need to be set

            Returns:
                None

            Raises:
                Exception:
                    if any error occurs in applying ACL
        """
        ace_group_prinicipal = ''
        if user_group_flag:
            ace_group_prinicipal = 'g'

        cmd = "/usr/bin/nfs4_setfacl -a {0}:{1}{5}:{2}:{3} {4}".format(ace_type,
                                                                       ace_flags,
                                                                       ace_principal,
                                                                       ace_permissions,
                                                                       object_path,
                                                                       ace_group_prinicipal)
        self.log.info("running set ACL command {0}".format(cmd))
        output = self.execute_command(cmd)
        if output.exception:
            raise Exception("Error while running command nfs4_setfacl."
                            "output:{0} error:{1}".format(output.output,
                                                          output.exception_message))

    def nfs4_getfacl(self, object_path):
        """get NFSv4 file/directory access control lists

            Args:
                object_path   (str)     -- path of file or directory for which ACL
                need to be applied

            Returns:
                current ACLs set for the given path

            Raises:
                Exception:
                    if any error occurs in retrieving ACLs
        """
        cmd = "/usr/bin/nfs4_getfacl {0}".format(object_path)
        self.log.info("running get ACL command {0}".format(cmd))
        output = self.execute_command(cmd)
        if output.exception:
            raise Exception("Error while running command nfs4_getfacl."
                            "output:{0} error:{1}".format(output.output,
                                                          output.exception_message))
        return output.output

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
        self.create_registry('EventManager', value=service_name + '_DEBUGLEVEL',
                             data=level)
        self.create_registry('EventManager', value=service_name + '_DEBUGLEVEL_UNTIL',
                             data=int(time.time()) + 7 * 86400)

    def set_logging_filesize_limit(self, service_name, limit='5'):
        """set max log file size limit for given CV service name

                      Args:
                         service_name         (str)  -- name of valid CV service name

                         limit                (str)  -- file size in MB , default : 5

                    Returns:
                         None
                    Raises:
                         Exception:
                             if any error occurred while updating debug log level
                """
        self.create_registry('EventManager', value=service_name + '_MAXLOGFILESIZE',
                             data=limit)

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

    def get_cpu_usage(self, client, interval, totaltime, processname, outputpath, wait_for_completion):
        """Gets the CPU usage for a process on the remote machine in given intervals for given total time.

        Args:
            client (obj)           -- Client object for a remote machine
            interval (int)         -- interval in seconds for which it will get the cpu usage for a process
            totaltime (int)        -- totaltime in minutes for which it will get the cpu usage for a process
            processname (str)      -- Process name for which cpu usage to be generated.
            outputpath  (str)      -- Output path to which the generated output to be written
            wait_for_completion (boolean)   -- Waits until the command completes

        Return: Return True if the command is executed

        """
        self.log.info("Getting cpu performance counters for Unix machine on process %s", processname)
        script_arguments = "{0} {1} {2} {3} {4}".format("mac009", interval, totaltime, processname, outputpath)
        self._copy_file_from_local(UNIX_GET_CPU_USAGE, "/temp/")
        cmd = "bash /temp/GetCPUusage.bash"
        client.execute_command(cmd, script_arguments=script_arguments, wait_for_completion=False)
        '''self.client_object.execute_script(script_type = "UnixShell", script=UNIX_GET_CPU_USAGE, script_arguments=script_arguments,
                                           wait_for_completion=False)'''
        return True

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
        session_output = self.execute_command("who | grep -w " + user + " | grep console | grep -v grep")
        if not session_output.exception_message:
            user_info = session_output.formatted_output
            if user not in user_info:
                self.log.error("Failed to get active session for the user [{0}] on client [{1}]"
                               .format(username, machine))
            else:
                self.log.info("Active session found for user [{0}] on client [{1}]".format(username, machine))
                return True
        else:
            self.log.error("Failed to get active session information for user [{0}]".format(username))

        return False

    def get_file_owner(self, file_path):
        """Get the owner of the file
            Args:
                file_path(str)   -- Path of the file

            Returns:
                String name of the owner result"""

        cmd = "stat --format '%U' '{0}'".format(file_path)

        output = self.execute_command(cmd)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.output.strip()

    def get_file_group(self, file_path):
        """Get the group of the file/directory
            Args:
                file_path(str)   -- Path of the file/directory

            Returns:
                String name of the group result"""

        cmd = "stat --format '%G' '{0}'".format(file_path)

        output = self.execute_command(cmd)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        return output.output.strip()

    def get_subnet(self):
        """

        Get Subnet Mask of the machine

        Returns: (str) Subnet mask of the machine


        """
        command = f"ifconfig | grep '{self.ip_address}'"
        output = self.execute_command(command)
        output = output.formatted_output
        properties = output.split("  ")

        for property in properties:
            prop, value = property.split(" ")
            if prop == "netmask":
                return value

        raise Exception("No property named Netmask Found")

    def get_default_gateway(self):
        """

        Get Default Gateway of the machine

        Returns: (str) Default Gateway of the machine

        """
        command = "ip route | grep default"
        output = self.execute_command(command)
        default_gateway = output.formatted_output.split(" ")[2]
        return default_gateway

    def is_dhcp_enabled(self):
        """

        Whether DHCP is enabled on the machine
        Returns: (bool) DHCP enabled
        """
        if self.os_distro == 'centos':
            command = "cat /etc/sysconfig/network-scripts/ifcfg-en*"
            output = self.execute_command(command).output.strip().split("\n")
            for line in output:
                if line.split("=")[-1].strip() == "dhcp":
                    return True
            return False

    def get_dns_servers(self):
        """

        Gets all DNS servers from the machine
        Returns: (list) DNS servers
        """
        command = "cat /etc/resolv.conf"
        output = self.execute_command(command).output.strip().split("\n")
        return [line.split()[-1] for line in output if line and line.startswith('nameserver')]

    def add_host_file_entry(self, hostname, ip_addr):
        """

        Add an entry to host file

        Args:
            hostname    (str): hostname of the entry

            ip_addr     (str): ip address to assign to the hostname

        Raises:
            Exception if host file change fails

        """
        path = "/etc/hosts"
        command = f"echo '{ip_addr}\t{hostname}' >> {path}"

        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def remove_host_file_entry(self, hostname):
        """

        Remove the host file entry by hostname

        Args:
            hostname (str): hostname of the entry to be removed

        Raises:
            Exception if host file entry change fails
        """
        path = "/etc/hosts"
        command = f"sed -i '/{hostname}/d' {path}"
        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

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
        log_file_path = None
        # GET ONLY LOG LINES CONTAINING A PARTICULAR JOB ID AND SEARCH TERM.
        if self.client_object:
            log_file_path = self.join_path(
                self.client_object.log_directory, log_file_name)
        else:
            log_file_path = log_file_name
        if job_id is None:
            unix_output = self.execute_command(command="grep -E '{}' {}".format(search_term,
                                                                                log_file_path))
        else:
            unix_output = self.execute_command(command="grep -E ' {} .*{}|{}.* {} ' {}".format(job_id, search_term,
                                                                                               search_term, job_id,
                                                                                               log_file_path))
        unix_output = unix_output.output.strip().split('\n')
        job_log_lines = ""
        for line in unix_output:
            if line.strip() == "":
                continue
            job_log_lines = "".join((job_log_lines, line, "\r\n"))

        return job_log_lines

    def get_time_range_logs(self, file_path, start_time, end_time="", search=""):
        """Retrieves log lines from a file within a specified time range.

        Args:
            file_path (str): The path to the log file.
            start_time (str): The start time for filtering log lines in format 'mm/dd HH:MM:SS'.
            end_time (str, optional): The end time for filtering log lines. If empty, retrieves all logs till the current time. Defaults to "".
            search (str, optional): A search term to filter log lines. Defaults to "".
    
        Returns:
            str: The log lines within the specified time range.
    
        Raises:
            Exception: If there is an error reading the log file or processing the log lines.
        """
        self._script_generator.script = UNIX_GET_CV_TIME_RANGE_LOGS
        if search:
            # Replace single quote in search term to avoid issues in shell command execution
            search = search.replace("'", "'\\''")
        data = {
            'log_file': file_path,
            'start_time': start_time,
            'end_time': end_time,
            'search': search
        }

        get_cv_logs_script = self._script_generator.run(data)

        output = self.execute(get_cv_logs_script)
        os.unlink(get_cv_logs_script)

        if output.exception_message:
            raise Exception(output.exception_message)
        elif output.exit_code != 0:
            raise Exception(f"Error occurred while fetching logs: {output.exception}")

        return output.output
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
        self.log.info("Moving file [%s] to [%s] on client [%s]", source_path, destination_path, self.machine_name)
        command = 'mv "{0}" "{1}"'.format(source_path, destination_path)
        output = self.execute_command(command)
        self.log.info(output.formatted_output)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

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
        time_format = '%Y%m%d%H%M.%S'

        if access_time is not None:
            self.log.info("Changing File [%s] last access time property to [%s].", path,
                          access_time.strftime(time_format))
            command = 'touch -a -t {0} {1}'.format(access_time.strftime(time_format), path)
            output = self.execute_command(command)
            self.log.info(output.formatted_output)
            if output.exception_message:
                raise Exception(output.exception_code, output.exception_message)
            elif output.exception:
                raise Exception(output.exception_code, output.exception)

        if modified_time is not None:
            self.log.info("Changing File [%s] last modified time property to [%s].", path,
                          modified_time.strftime(time_format))
            command = 'touch -m -t {0} {1}'.format(modified_time.strftime(time_format), path)
            output = self.execute_command(command)
            self.log.info(output.formatted_output)
            if output.exception_message:
                raise Exception(output.exception_code, output.exception_message)
            elif output.exception:
                raise Exception(output.exception_code, output.exception)

    def start_all_cv_services(self):
        """Start all Commvault services using username/password method since SDK cannot talk to the machine
        when services are down. Use SDK service control methods if services are already running.

            Returns:
                None

            Raises:
                Exception while trying to execute command to start the service

        """

        command = f'commvault start -instance {self.instance}'

        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

    def stop_all_cv_services(self):
        """Stops all Commvault services using username/password method

            Returns:
                None

            Raises:
                Exception while trying to execute command to start the service

        """

        command = f'commvault stop -instance {self.instance}'

        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

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

        command = f'DIR="{path}"; if [ -d "$DIR" ]; then echo "True"; else echo "False"; fi;'

        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        if output.formatted_output == 'True':
            return True
        return False

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

        command = f'FILEPATH="{path}"; if [ -f "$FILEPATH" ]; then echo "True"; else echo "False"; fi;'

        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        if output.formatted_output == 'True':
            return True
        return False

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
        dir_path = option_obj.get_drive(self)
        file_name = f"{dir_path}Get_API_Call_{option_obj.get_custom_str()}.txt"
        # for some reason wget -x option is not working on few linux clients, hence adding logic to create dir
        if not self.check_directory_exists(directory_path=dir_path):
            self.create_directory(directory_name=dir_path)
        cmd = f"wget -O '{file_name}' '{api_url}'"
        # wget output is not getting rendered properly. so going with file existence check
        self.execute_command(cmd)
        if not self.check_file_exists(file_path=file_name):
            raise Exception(f"Wget error for command [{cmd}]. Please check")
        response = self.read_file(file_path=file_name)
        self.delete_file(file_path=file_name)
        return response

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
            time_output = self.execute_command(r"date --universal +%d-%m-%Y\ %H:%M:%S")
            current_time = datetime.datetime.strptime(time_output.output.strip(),
                                                      "%d-%m-%Y %H:%M:%S")
            current_time = timezone('UTC').localize(current_time)
            if timezone_name and timezone_name != 'UTC':
                current_time = current_time.astimezone(timezone(timezone_name))
            return current_time
        except Exception:
            raise Exception("\n Current Time could not be fetched with exception: {0}".
                            format(time_output.exception_message))
                        
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
        time_output = self.execute_command(r"date +%d-%m-%Y\ %H:%M:%S")
        current_localtime = datetime.datetime.strptime(time_output.output.strip(),
                                                  "%d-%m-%Y %H:%M:%S")
        return current_localtime

    def unzip_zip_file(self, zip_file_path, where_to_unzip):
        """Used to unzip a zipped file at given location

        Args:
            zip_file_path (string): Path where ZIP file is located.
            where_to_unzip (string): Path at which we have to extarct our file.
        Returns:
            None
        """
        cmd = "cd {0};sudo /usr/bin/unzip -o {1}".format(
            where_to_unzip, zip_file_path)
        output = self.execute_command(cmd)

        if output.exception_message:
            raise Exception(output.exception_code,
                            output.exception_message)

    def change_system_time(self, offset_seconds):
        """Changes the system time as per the offset seconds provided w.r.t to current system time

            Args:
                offset_seconds      (int)   --  Seconds to offset the system time.
                Example, 60 will change the system time to 1 minute forward and -180 will change
                system time 3 minutes backward

            Returns:
                None

            Raises:
                Exception

        """
        cmd = f"date --set='{offset_seconds} seconds'"
        output = self.execute_command(cmd)

        if output.exception_message:
            raise Exception(output.exception_code,
                            output.exception_message)

    def toggle_time_service(self, stop=True):
        """
        Toggles the state of the Unix ntp time service
        Args:
            stop:  (bool) -- If set to True will stop the service else will start the service

        Returns:
                None: if Unix time service state is toggled successfully

            Raises:
                Exception:
                    If Time service state was not toggled successfully

        """
        maximum_attempts_restart = 3
        if stop:
            self.log.info("Stopping Time Service")
            service_command = "sudo timedatectl set-ntp 0"
            expected_output = ['NTP enabled: no']
        else:
            self.log.info("Starting Time Service")
            service_command = ("sudo timedatectl set-ntp 1")
            expected_output = ['NTP enabled: yes', 'NTP synchronized: yes']
        self.execute_command(service_command)
        service_output = self.execute_command('sudo timedatectl')
        # If starting back time server, run for maximum_attempts_restart as sometimes it doesn't synchronize
        if not stop:
            for i in range(maximum_attempts_restart):
                self.execute_command(service_command)

            service_output = self.execute_command('sudo timedatectl')

        # Check if expected output is there, else raise exception
        if not any((x in service_output.output) for x in expected_output):
            raise Exception("Time service could not be toggled successfully with exception: {0}"
                            .format(service_output.exception_message))

        self.log.info("Time service operation completed successfully")

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
                      "sed -n \"/%s/s/://gp\" %s") % (
                      pattern, self.join_path(client_log_directory, log_file_name))
        output = self.execute_command(command).formatted_output
        if output != '':
            return True
        return False

    def fill_zero_disk(self, disk):
        """Filling 1Mb block of the disk with all zeros

               Args:
                   disk    (str)   --  disk

               Returns:
                   bool:
                       True    -   Filling the disk with all zeros
               Raises:
                   Exception(Exception_Code, Exception_Message):
                       if failed to do so

                Need to handle error cases
        """

        sudo = ''
        if self.run_as_sudo:
            sudo = 'sudo '
        output = self.execute(sudo + f"lsblk | grep {disk}")
        if output.exit_code != 0:
            raise Exception("Error no disk found")
        output = self.execute(sudo + f"dd if=/dev/zero of=/dev/{disk} bs=1M count=1")

        if output.exit_code != 0:
            raise Exception(
                f"Error occurred while cleaning up the test data, output: {output.output}"
                f"exception: {output.exception}"
            )
        else:
            return True

    def create_local_filesystem(self, filesystem, disk):
        """creates filesystem locally on the machine on the disk

                Args:
                    filesystem  (str)   --  filesystem type
                    disk    (str)   --  disk(unmounted)

                Returns:
                    bool:
                        True    -   created filesystem
                Raises:
                    Exception(Exception_Code, Exception_Message):
                        if failed to create filesystem

         """
        filesystem_supported = ['btrfs', 'cramfs', 'ext2', 'ext3', 'ext4', 'fat', 'minix', 'msdos', 'vfat', 'xfs']
        if filesystem not in filesystem_supported:
            raise Exception(f"Filesystem {filesystem} is not supported, supported f"
                            f"ilesystems are {filesystem_supported} ")
        sudo = ''
        if self.run_as_sudo:
            sudo = 'sudo '
        storage = self.get_storage_details()
        if disk not in storage:
            output = self.execute(f"{sudo}echo yes | mkfs -t {filesystem} {disk}")
            if output.exit_code != 0:
                raise Exception(f"Cannot create Filesystem with "
                                f"Exception: {output.exception}, {output.exception_message}")
            self.log.info(f"created filesystem {filesystem} over disk {disk}, Output: {output.output}")
            return True
        raise Exception(f"Disk {disk} already mounted, will not create filesystem over it")

    def mount_local_path(self, disk, mount_path):
        """mounts local disk to local path on the machine

        Args:
            disk    (str)   --  disk to mount
            mount_path  (str)   --  path where to mount

        Returns:
            bool:
                True    -   Mounted the path
        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to mount
    """
        storage = self.get_storage_details()
        sudo = ''
        if self.run_as_sudo:
            sudo = 'sudo '
        if not self.check_directory_exists(mount_path):
            self.create_directory(mount_path)

        is_mounted = self.is_path_mounted(mount_path)
        if is_mounted:
            raise Exception(f"Path {mount_path} is already mounted, cannot mount")

        if disk not in storage:
            output = self.execute(f"{sudo}mount {disk} {mount_path}")
            if output.exit_code >= 1:
                raise Exception(f"Mount failure with exception, Exception: {output.exception_message}")
            self.log.info(f"Mounted disk {disk} on path {mount_path} successfully")
            return True
        raise Exception(f"Disk {disk} is already mounted on path {storage.get(disk).get('mountpath')}")

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
        cmd = f"rm -rf {folder_path}/*"
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
        cmd = f"{install_directory}/cvping {destination} -{family_type} {port}"
        if not self.check_file_exists(file_path=f"{install_directory}/cvping"):
            raise Exception(f"cvping tool is not installed on this client.")
        output = self.execute_command(cmd)
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
        if not self.check_file_exists(file_path=f"{install_directory}/CVDiskPerf"):
            raise Exception(f"CVDiskPerf tool is not installed on this client. Make sure MA package is installed")
        command = f"{install_directory}/CVDiskPerf {cmd_opts}"
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

        grep = ''
        for word in words:
            grep += f' | grep -i "{word}"'

        command = f'cat "{file_path}" {grep}'
        output = self.execute_command(command)

        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)

        lines = output.formatted_output
        if isinstance(lines, str):  # When result is one line, it is a string instead of list.
            lines = [lines]
        return lines

    def check_user_exist(self, username):
        """
        Checks if user exists or not
        Args:
            username   (str)   --  The username we need to check
        Returns:
            True if user exists
            False if user does not exists

        Raises:
            Exception, if failed to open file
        """
        command = 'cat /etc/passwd'
        username = '%s:' % username
        output = self.execute_command(command)
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif output.exception:
            raise Exception(output.exception_code, output.exception)
        return username in output.output

    def remove_additional_software(self, package):
        """This method will remove all the 3rd party software from the machine
         Args:
                package   (str)       --  Package to remove

        """
        raise NotImplementedError("Method not implemented for Unix")

    def copy_file_between_two_machines(self, src_file_path, destination_machine_conn, destination_file_path):
        """
        Transfer files between two machines.
        Args:
            src_file_path (str) -> Source file path
            destination_machine(Machine) -> Machine where data needs to be copied
            destination_file_path (str) -> Destination file path
        """
        self._login_with_credentials()
        sftp = self._client.open_sftp()

        file_name = src_file_path.split(self.os_sep)[-1]

        aux_machine = Machine()
        aux_path = f"{aux_machine.get_registry_value(commvault_key='Base', value='dGALAXYTEMPDIR')}{aux_machine.os_sep}{file_name}"
        self.log.info(f"Transferring Aux File From {src_file_path} To {aux_path}")
        sftp.get(src_file_path, aux_path)

        destination_machine_conn._login_with_credentials()
        sftp = destination_machine_conn._client.open_sftp()
        sftp.put(aux_path, destination_file_path)

    def verify_installed_packages(self, packages):
        """verify the packages are installed on the client
        Args:
            packages (list): list of package ids. for package id, please refer to the corresponding constants
        """
        for pkg_id in packages:
            if self.get_registry_value(
                    commvault_key="/Installer/Subsystems/" + str(pkg_id),
                    value="nINSTALL") != "1":
                raise Exception(
                    "Packages are not installed correctly")
        self.log.info("Packages are installed successfully")

    def change_hostname(self, new_hostname):
        """
        Changes the hostname of the given unix machine
        Args:
            new_hostname(str)   -   new hostname

        Returns:
            bool    - true/false on hostname change of the client

        Raises:
            Exception if updating hostname fails
        """
        if self.os_flavour == "Linux":
            command = f"hostnamectl set-hostname {new_hostname}"
            command_op = self.execute_command(command)
            if command_op.exception_message:
                raise Exception(command_op.exception_code,
                                command_op.exception_message)
            elif command_op.exception:
                raise Exception(command_op.exception_code, command_op.exception)
        else:
            raise Exception(f"This flavour of linux is not supported [{self.os_flavour}]")

    def add_to_domain(self, domain_name, username, password):
        """
        adds a given unix machine to domain
        Args:
            domain_name(str)    -   name of the domain
            username(str)       -   Username for the domain controller
            password(str)       -   password for the domain controller

        Raises:
            Exception,  if client is already part of the domain
                        if client addition to domain fails
        """

        if self.os_flavour == "Linux":
            add_domain_command = f"echo '{password}' | realm join {domain_name} -v -U '{username}'"
            command_op = self.execute_command(add_domain_command)
            success_message = "Successfully enrolled machine in realm"
            if command_op.exception_message:
                if not success_message.lower() in command_op.exception_message.lower():
                    raise Exception(command_op.exception_code,
                                    command_op.exception_message)
            elif command_op.exception:
                raise Exception(command_op.exception_code, command_op.exception)
        else:
            raise Exception(f"This flavour of linux is not supported [{self.os_flavour}]")

    def disable_ipv6(self):
        """
        disables IPv6 address for the linux machine
        Raises:
            Exception, if given os flavour is not Linux
                       if command fails to execute
        """
        if self.os_flavour == "Linux":
            disable_ipv6_cmd = "sysctl -w net.ipv6.conf.all.disable_ipv6=1;  " \
                               "systemctl restart NetworkManager"
            command_op = self.execute_command(disable_ipv6_cmd)
            if command_op.exception_message:
                raise Exception(command_op.exception_code,
                                command_op.exception_message)
            elif command_op.exception:
                raise Exception(command_op.exception_code, command_op.exception)
        else:
            raise Exception(f"This flavour of linux is not supported [{self.os_flavour}]")

    def get_hostname(self):
        """Gets the hostname of the machine
        Returns:
            string containing the hostname
        Raises:
            Exception, if given os flavour is not Linux
                       if command fails to execute
        """
        if self.os_flavour == "Linux":
            cmd = "hostname"
            command_op = self.execute_command(cmd)
            if command_op.exception_message:
                raise Exception(command_op.exception_code,
                                command_op.exception_message)
            elif command_op.exception:
                raise Exception(command_op.exception_code, command_op.exception)
            return command_op.formatted_output
        else:
            raise Exception(f"This flavour of linux is not supported [{self.os_flavour}]")