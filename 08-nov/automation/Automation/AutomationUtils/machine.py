# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for performing operations on a machine / computer.

This file consists of a class named: Machine, which can connect to the remote machine,
using CVD, if it is a Commvault Client, or using PowerShell, otherwise.

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


Machine
=======

    __new__()                       --  ping the machine, to get the OS details, whether
    Windows / UNIX, and initialize the class instance accordingly

    __init__()                      --  initialize object of the class

    _login_with_credentials()       --  creates a connection to the remote client

    _execute_with_credential()      --  execute a script on a remote client using its credentials

    _execute_with_cvd()             --  execute a script on a remote client using the CVD service

    _get_file_hash()                --  returns the hash value of specified file

    _get_folder_hash()              --  returns the set of file paths and hash values

    _compare_lists()                --  compares the source list with the destination list and
    checks if they are the same or not

    _convert_size()                 --  converts the given float size to appropriate size in
    B / KB / MB / GB, etc.

    _validate_ignore_files()        --  returns list of files from diff of 2 folders after ignoring
    the list of files given in ignore_files list

    _get_client_ip()                -- gets the ip address of the machine

    get_log_file()                  -- Returns the contents of a log file.

    get_cpu_usage()                 -- gets the cpu performance counters for the given process

    get_unc_path()                  --  generates the unc path for the input path

    execute()                       --  execute the given script remotely on a remote client

    execute_command()               --  executes a command on the remote machine

    check_directory_exists()        --  check if a directory exists on a remote client or not

    check_file_exists()             --  checks if a file exists on a remote client or not

    create_directory()              --  create a new directory on a remote client
    
    current_time()                  --  Returns current machine time in UTC TZ as a datetime object
    
    current_localtime()             --  returns current machine timezone as a datetime.timezone object

    rename_file_or_folder()         --  renames a file / folder on a remote client

    is_file()                       -- Checks if the path is a file or not

    is_directory()                  --  Checks if the path is a directory or not

    is_process_running()            -- Checks if a given process is running on the index server

    get_process_id()                --  returns the process id for the given process name with or without command line

    get_process_stats()             --  Gets the process stats like Handle count, memory used, CPU usage, thread count

    get_process_dump()              --  Gets the process dump for the given process ID

    get_hardware_info()             --  returns the hardware specifications of this machine

    block_tcp_port()                --  blocks tcp port on machine for given time interval

    get_port_usage()                --  returns the netstat connection stats for the process or machine

    remove_directory()              --  remove a directory on a remote client

    get_file_size()                 --  get the size of a file on a remote client

    get_folder_size()               --  get the size of a folder on a remote client

    get_file_stats_in_folder()       --  Gets the total size in bytes by summing up the individual file size for
                                        files present in the directories and subdirectories of the given folder_path

    get_storage_details()           --  returns the storage details of this machine

    get_disk_count()                --  returns the count of the disks on the machine

    check_registry_exists()         --  check if a registry exists on a remote client or not

    get_registry_value()            --  get the value of a registry key from a remote client

    create_registry()               --  create a registry key / value on a remote client

    update_registry()               --  update the data of a registry value on a remote client

    remove_registry()               --  remove a registry key / value from a remote client

    compare_files()                 --  compares the contents of 2 files

    compare_folders()               --  compares the contents of 2 folders

    copy_from_local()               --  copies the file / folder specified in the input from
    local machine to the remote machine

    copy_folder_to_network_share()  --  copies the folder specified to the network share

    copy_from_network_share()       --  copies the file/folder specified at network share
    to the local machine

    copy_folder()                   --  copies the files specified at a location to
    another location on same local machine

    copy_folder_to_network_share()  --  copies the folder from this machine to the network share

    read_file()                     --  read the contents of the file present at input path

    delete_file()                   --  removes the file present at the input path

    change_folder_owner()           --  changes the ownership of the given directory

    create_current_timestamp_folder()   --  create a folder with the current timestamp as the
    folder name inside the given folder path

    get_latest_timestamp_file_or_folder()   --  get the recently created file / folder inside the
    given folder path

    get_files_in_path()             --  returns the list of files present at the given path

    get_folders_in_path()           --  returns the list of folders present at the given path

    number_of_items_in_folder()     --  Returns the count of number of items in a folder

    join_path()                     --  joins the path using the separator based on the OS of the
    Machine

    get_file_hash()                 --  returns the hash value of specified file

    get_folder_hash()               --  returns the set of file paths and hash values

    generate_executable()           --  generates an executable of the python file

    generate_test_data()            --  generates test data at specified path on remote client

    disconnect()                    --  disconnects the session with the machine

    scan_directory()                --  Scans the directory and returns a list of items under it
    along with its properties

    add_firewall_allow_port_rule()  --  adds the inbound rule for the given port number

    start_firewall()                --  turn on firewall services on the current client machine

    add_firewall_machine_exclusion()    --  adds given machine to firewall exclusion list

    remove_firewall_allow_port_rule()   --  removes the inbound rule for the given port number

    stop_firewall()                     --  turn off firewall service on the client machine

    remove_firewall_machine_exclusion() --  removes given machine from firewall exclusion list

    reboot_client()                     --  reboots the machine

    shutdown_client()                   --  shutdown the host

    is_stub()                           --  for onepass to identify stub

    get_checksum_list()                 --  Gets the list of checksum of items
    from the machine on a give path

    compare_acl()                       --  Compares the acl of src and dest path
    and checks if they are same

    kill_process()                      --  terminates a running process on the client machine
    either with the given process name or the process id

    modify_content_of_file()        --  append data to a file at specified path on this machine

    add_user()                      --  create new user account using values passed to method

    hide_path()                     -- Hides the specified path

    unhide_path()                     -- unhides the specified path

    delete_users()                  --  delete a user account and Files in the user's
    home directory

    change_file_permissions()       --  change file mode bits for the given file or directory path

    nfs4_setfacl()                  -- manipulates the NFSv4 Access Control List (ACL) of
    one or more files (or directories)

    nfs4_getfacl()                  -- get NFSv4 file/directory access control lists

    get_snapshot()                  -- gets meta data(ls -l) and md5sum of each file
    in the given directory

    unmount_path()                  --  dis mounts the network path mounted at specified path

    set_logging_debug_level()       -- set debug log level for given CV service name

    set_logging_filesize_limit()    -- set the filesize limit for given CV service name

    append_to_file()                --  Appends content to the file present at the specified path

    read_csv_file()                 --  Reads the provided CSV file and returns a dictionary structure of its data

    change_system_time()            --  Changes the system time as per the offset seconds
    provided w.r.t to current system time

    get_ace()                        --  To get ace of file/folder for particular user

    modify_ace()                     --  To add or remove ACE on file or folder

    execute_command_unc()            --  Execute command function for unc path

    windows_operation()              -- For execute windows operation

    add_minutes_to_system_time()     -- Adds specified number of minutes to current system time

    add_days_to_system_time()        -- Adds specified number of days to current system time

    get_active_cluster_node()        --    gets active cluster node

    get_cluster_nodes()              --   Get all nodes of cluster both active and passive

    do_failover()                    --   Run Cluster failover

    has_active_session()             -- Checks if there is an active session on the machine for a user

    get_login_session_id()           --  Gets the session id for the logged in user

    logoff_session_id()              --  Logs off the user session id for the logged in user on client.

    get_file_owner()                 -- Get the owner of the file

    get_file_group()                --  Get the group of the file/directory

    get_logs_for_job_from_file()     -- Return those log lines for a particular job ID
    
    get_time_range_logs()           -- Retrieves log lines from a file within a specified time range
    
    get_event_viewer_logs_message()  -- Gets N newest event viewer log message bodies

    list_shares_on_network_path() -- gets the list of shares on a UNC path

    modify_test_data()              --  Modifies the test data at the given path

    get_items_list()                --  returns the list of items at the given path

    compare_checksum()              --  compares the checksum of 2 paths

    move_file()                     --	Moves a file item from source_path to destination_path

    modify_item_datetime()          --  Changes the last Access time and Modified time of files in unix and windows.
    Also changes creation time in windows.

    get_vm_ip()                     --  To get ip address of a VM

    share_directory()               -- To share a directory using net share

    unshare_directory()             -- To unshare a directory

    get_share_name()                -- To get share name of directory if shared exists

    get_logs_after_time_t()         -- retrives logs of a logfile after time t.

    lock_file()                     -- To lock a local file.

    mount_network_path()            -- Mounts the specified network path on this machine.

    restart_all_cv_services()       --  Restart all Commvault services using username/password method since SDK cannot
    talk to the machine when services are down

    start_all_cv_services()         --  Start all Commvault services using username/password

    stop_all_cv_services()          --  Stop all Commvault services using username/password method

    get_api_response_locally()      --  Executes local get api call and returns response

    unzip_zip_file()                --  To unzip a file at a given path.

    check_if_pattern_exists_in_log  --  Method to check if the given pattern exists in the log file or not

    fill_zero_disk()                --  Filling 1Mb block of the disk with all zeros

    create_local_filesystem         --  Creates filesystem on the local disk

    mount_local_path                --  Mounts local disk to local path on the machine

    clear_folder_content()          --  Recursively deletes files/folders in given folder path to make it empty

    run_cvdiskperf()                --  Executes cvdiskperf.exe tool and returns results

    run_cvping()                    --  Executes cvping on machine with provided inputs

    find_lines_in_file()            --  Search for lines in a file for the given words

    check_user_exist()              --  Checks if user exists or not

    remove_additional_software()    -- This method will remove the 3rd party software

    copy_file_between_two_machines()-- Copy files between two machines using current machine as Aux

    change_inheritance()            --  Disables or enables inheritance on the folder

    copy_file_locally()             -- Copies file from one directory to another

    change_hostname()               -- Changes the hostname of a given machine

    add_to_domain()                 -- adds a given windows machine to domain

    disable_ipv6                    -- disables IPv6 address for the machine

    get_hostname                    -- Gets the hostname of the machine

    get_ibmi_version()              --  Gets the version and release of IBMi client.


Attributes
----------

    **os_info**     --  returns the OS details of the client (Windows / UNIX)

    **os_sep**      --  returns the path separator based on the OS of the Machine

    **ip_address**  --  returns IP address of the machine


Usage
-----

    -   For creating an object of any machine, i.e., Windows / UNIX, the user should only
        initialize an object of the Machine class, which internally takes care of detecting the OS
        of the machine, and initialize the appropriate object.

    -   Machine class object can be initialized in 3 ways:

        -   If the machine is a Commcell client:

            >>> machine = Machine(machine_name, commcell_object)

        -   If the machine is a Commcell client, and user already has the client object:

            >>> machine = Machine(client_object)

            **NOTE:** the client_object should be given as the value for the machine_name argument

        -   If the machine is not a Commcell client:

            >>> machine = Machine(machine_name, username=username, password=password)

        -   If the machine is the Local Machine:

            >>> machine = Machine(local_machine_name)

                        OR

            >>> machine = Machine()


"""

from difflib import Differ
import getpass
import math
import os
import re
import sys
import socket
import time
from cvpysdk.client import Client
from .pyping import ping


class Machine:
    """Class for performing operations on a remote client."""

    def __new__(cls, machine_name=None, commcell_object=None, *args, **kwargs):
        """Returns the instance of one of the Subclasses WindowsMachine / UnixMachine,
            based on the OS details of the remote client.

            If Commcell Object is given, and the Client is Commvault Client:
                Gets the OS Info from Client OS Info attribute

            Otherwise, Pings the client, and decides the OS based on the TTL value.

            TTL Value: 64 (Linux) / 128 (Windows) / 255 (UNIX)

        """
        if machine_name:
            client = None

            if isinstance(machine_name, Client):
                client = machine_name
            else:
                if (commcell_object is not None and
                        commcell_object.clients.has_client(machine_name)):
                    client = commcell_object.clients.get(machine_name)

            if client:
                for attempt in range(1, 4):
                    if not client.readiness_details.is_ready(cs_cc_network_check=True):
                        if attempt != 3:
                            time.sleep(60)
                            continue
                        else:
                            exception = ('Check readiness for the client: "{0}" failed. '
                                     'Please ensure the services are up and running').format(client.client_name)
                            raise Exception(exception)
                    else:
                        break
                if 'windows' in client.os_info.lower():
                    from .windows_machine import WindowsMachine
                    return object.__new__(WindowsMachine)
                elif 'open vms' in client.os_info.lower():
                    from .openvms_machine import OpenVMSMachine
                    return object.__new__(OpenVMSMachine)
                elif 'unix' in client.os_info.lower():
                    if 'hdfs_user' in kwargs:
                        from .hadoop_machine import HadoopMachine
                        return object.__new__(HadoopMachine)
                    from .unix_machine import UnixMachine
                    return object.__new__(UnixMachine)
                elif 'iseries' in client.os_info.lower() or 'ibm i' in client.os_info.lower():
                    from .ibmi_machine import IBMiMachine
                    return object.__new__(IBMiMachine)
        else:
            machine_name = socket.gethostname()

        response = ping(machine_name)

        # Extract TTL value form the response.output string.
        try:
            ttl = int(re.match(r"(.*)ttl=(\d*) .*",
                               response.output[2]).group(2))
        except AttributeError:
            raise Exception(
                'Failed to connect to the machine.\nError: "{0}"'.format(
                    response.output)
            )

        if ttl <= 64:
            from .unix_machine import UnixMachine
            return object.__new__(UnixMachine)
        elif ttl <= 128:
            from .windows_machine import WindowsMachine
            return object.__new__(WindowsMachine)
        elif ttl <= 255:
            if 'hdfs_user' in kwargs:
                from .hadoop_machine import HadoopMachine
                return object.__new__(HadoopMachine)
            from .unix_machine import UnixMachine
            return object.__new__(UnixMachine)
        else:
            raise Exception(
                'Got unexpected TTL value.\nTTL value: "{0}"'.format(ttl))
            # https://social.technet.microsoft.com/Forums/windowsserver/en-US/86e490e2-72be-4e2f-bb45-85fa2f52c876/os-check-for-unix-or-linux?forum=winserverpowershell

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

        Note: If you are facing issues with creating machine object, check the following things on the controller
            machine and the machine you are trying to connect:

            1. You should be running python interpreter with administrator privelage
            2. Firewalls must be turned off
            3. Check if Remote services(such as Remote desktop services, remote desktop configuration) are running
                in services.msc
            4. Check if netlogon is running under services.msc
            5. Run "winrm quickconfig" in powershell once.
            6. Run "powershell.exe Set-ExecutionPolicy RemoteSigned -Force" in powershell.
        """
        self.machine_name = machine_name
        self.username = username
        self.password = password
        self.commcell_object = commcell_object
        self.credentials_file = None

        self.is_commvault_client = False
        self.client_object = None
        self.is_local_machine = False

        self._os_info = None
        self._ip_address = None
        self._os_flavour = None
        self._client = None
        self._script_generator = None
        self._is_connected = None
        self._encoding_type = None
        temp = []
        self._ssh = None

        if not self.machine_name:
            self.machine_name = machine_name = socket.gethostname()

        if isinstance(machine_name, Client):
            self.is_commvault_client = True
            self.client_object = machine_name
            self.commcell_object = self.client_object._commcell_object
            self.machine_name = machine_name = self.client_object.client_name

        for value in socket.gethostbyname_ex(socket.gethostname()):
            if isinstance(value, str):
                # value will have the FQDN of the controller
                # machine name should either match the FQDN, or just the hostname
                # MachineName.Domain.com        //      MachineName.
                temp.append(
                    machine_name.lower() == value.lower() or
                    f'{machine_name}.'.lower() in value.lower()
                )
            elif isinstance(value, list):
                for name in value:
                    temp.append(
                        machine_name.lower() == name.lower() or
                        f'{machine_name}.'.lower() in name.lower()
                    )
            else:
                temp.append(machine_name.lower() in value)

        self.is_local_machine = any(temp)

        del temp

        if self.is_local_machine:
            self.credentials_file = None

            # this check needs to be performed in case, automation controller is a CS client
            # and a helper needs to operate on the same client, and they require the client object
            # to be present to get the log / install directory, or do some Commvault specific
            # operations on the client
            if (self.client_object is None and
                    self.commcell_object is not None and
                    commcell_object.clients.has_client(machine_name)):
                self.client_object = self.commcell_object.clients.get(machine_name)

            # executing the script via CVD will take more time here, as we'll have to
            # make the API call to the WebServer, which will then go to the CommServer, and
            # then to the client via CVD, which will then execute the script and return the
            # results
            self.is_commvault_client = False

        elif self.username is not None:
            if self.password is None:
                prompt = 'Please provide the password of the Machine: "{0}", for User: "{1}": '
                self.password = getpass.getpass(
                    prompt.format(self.machine_name, self.username))

            self._login_with_credentials()

        elif (self.client_object is None and
              self.commcell_object is not None and
              commcell_object.clients.has_client(machine_name)):
            self.is_commvault_client = True
            self.client_object = self.commcell_object.clients.get(machine_name)

        elif self.client_object is None:
            exception = (
                'Client: "{0}" is not a Local Machine / Commvault client. '
                "Please provide the client's username and password"
            ).format(machine_name)

            raise Exception(exception)

        self._is_connected = True

        if not self.username and self.commcell_object:
            self.username = self.commcell_object._user

    def __repr__(self):
        """String representation of the instance of this class.

        Returns:
            str - string about the details of the Machine class instance

        """
        representation_string = 'Machine class instance of Host: "{0}"'.format(
            self.machine_name)

        try:
            return representation_string + ', for User: "{0}"'.format(self.username)
        except AttributeError:
            return representation_string

    def __enter__(self):
        """Returns the current instance.

        Returns:
            object - the initialized instance referred by self

        """
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Disconnects the current session with the machine."""
        self.disconnect()

    def _login_with_credentials(self):
        """Establish connection with the remote Client, if the client is not a Commvault client."""
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def current_time(self, timezone_name=None):
        """
            Returns current machine time in UTC TZ as a datetime object

            Args:
                timezone_name:  (String) -- pytz timezone to which the system time will be
                                            converted if not specified will return in UTC

            Returns:
                    datetimeobj -- machine's current time

            Raises:
                    Exception:
                        If not able to fetch current time

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    # Execution

    def current_localtime(self):
        """returns current machine timezone as a datetime.timezone object

        Args:
            none
        Returns:
            datetime.timezone -- machine's current timezone

        Raises:
            Exception:
                If not able to fetch current timezone
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def _execute_with_credential(self, script, script_arguments=None):
        """Execute the script remotely on a client using the credentials provided,
            if the client is not a Commvault client.

        Args:
            script              (str)   --  path of the script file to execute on the
                                            remote client.

            script_arguments    (str)   --  arguments to be passed to the script.
                Default: None.

        Returns:
            object  -   instance of UnixOutput class

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def _execute_with_cvd(self, script, script_arguments=None):
        """Execute the script remotely on a client using the CVD service running on the client.
            Only applicable if the client is a Commvault Client.

        Args:
            script  (str)           --  path of the script file to execute on the client remotely

            script_arguments (str)  --  arguments to the script
                Default: None

        Returns:
            object  -   instance of UnixOutput class

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    @staticmethod
    def _compare_lists(source_list, destination_list, sort_list=False):
        """Compares the source list with destination list
            and checks if they are same.

         Args:
            source_list         (list)  --  list1 to compare the contents of

            destination_list    (list)  --  list2 to compare the contents of

            sort_list           (bool)  --  boolean flag specifying whether the lists should
            be sorted before the comparison or not

                default: False

        Returns:
            tuple   -   tuple consisting of a boolean and a string, where:

                bool:

                    returns True if the lists are identical

                    returns False if the contents of the lists are different

                str:

                    empty string in case of True, otherwise string consisting of the
                    differences b/w the 2 lists separated by new-line

        """
        if sort_list:
            source_list.sort()
            destination_list.sort()

        diff_output = ""

        if source_list == destination_list:
            return True, diff_output

        diff = Differ().compare(source_list, destination_list)
        diff_output = '\n'.join(
            [x for x in list(diff) if not x.startswith('  ')])

        return False, diff_output

    @staticmethod
    def _convert_size(input_size):
        """Converts the given float size to appropriate size in B / KB / MB / GB, etc.

        Args:
            size    (float)     --  float value to convert

        Returns:
            str     -   size converted to the specific type (B, KB, MB, GB, etc.)

        """
        if input_size == 0:
            return '0B'

        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(input_size, 1024)))
        power = math.pow(1024, i)
        size = round(input_size / power, 2)
        return '%s %s' % (size, size_name[i])

    @staticmethod
    def _validate_ignore_files(different_files, ignore_files=None):
        """Removes the ignore files list from the difference obtained after comparing folders.

        Args:
            different_files      (list)  --  list of different files

            ignore_files         (list)  --  list of files that has to be ignored

                default: None

        Returns:
            list    -   list of remaining different files

        """
        diff = []
        if ignore_files is None:
            ignore_files = []

        for different_file in different_files:
            item = different_file.split("\\")[-1].strip().lower()
            found = False

            # Check if any different file starts with pattern in ignore_files
            # list
            for pattern in ignore_files:
                if item.startswith(pattern.replace("*", "")):
                    found = True
                    break

            # Append the file which didn't match with items in ignore_file list
            if not found:
                diff.append(different_file)

        return diff

    def _execute_script(self, script_path, data=None):
        """Executes the script at the given script path on the machine.

            Args:
                script_path     (str)   --  PowerShell / UNIX shell/bash script to be
                executed on the machine

                    script should be of same format as other
                    PowerShell / UNIXShell scripts present in:

                        -   PowerShell  -   ..\\\\Scripts\\\\Windows\\\\

                        -   UNIX shell / bash  -   ..\\\\Scripts\\\\UNIX\\\\

                data            (dict)  --  dictionary consisting of the variables and its values,
                to be substituted in the script

            Returns:
                object  -   instance of Output class corresponding to WindowsOutput for
                WindowsMachine and UnixOutput for UnixMachine

        """
        if data is None:
            data = {}

        self._script_generator.script = script_path
        execute_script = self._script_generator.run(data)

        output = self.execute(execute_script)
        os.unlink(execute_script)

        return output

    def _get_client_ip(self):
        """Gets the ip_address of the machine"""
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def set_encoding_type(self, encoding_type):
        """
        set encoding types
        Args:
            encoding_type (str): Encoding type
                        Example:: utf8 or ascii
        """
        self._encoding_type = encoding_type

    def execute_script(self, script_path, data=None):
        """Executes a PowerShell / Shell script on the machine.

            Args:
                script_path     (str)   --  script to be executed on the machine

                    script should be of same format as other scripts present in

                        ..\\\\Scripts\\\\

                data            (dict)  --  dictionary consisting of the variables and its values,
                to be substituted in the script

            Returns:
                object  -   instance of WindowsOutput / UnixOutput class
        """
        return self._execute_script(script_path, data)

    @property
    def os_info(self):
        """Returns the OS Info of this machine."""
        return self._os_info

    @property
    def os_flavour(self):
        """Returns the OS flavour of this machine."""
        return self._os_flavour

    @property
    def os_sep(self):
        """Returns the path separator based on the OS of the Machine."""
        raise NotImplementedError(
            'Property Not Implemented by the Child Class')

    @property
    def ip_address(self):
        """Returns the IP address of the Machine."""
        if self._ip_address is None:
            self._get_client_ip()
        return self._ip_address

    @property
    def instance(self):
        """Returns the value of instance attribute."""
        raise NotImplementedError(
            'Property Not Implemented by the Child Class')

    def get_unc_path(self, path):
        """Returns the unc path for the specified path

        Args:
            path    (str)   --  path on this machine

        Returns:
            str     -   unc path formed from the given path

        """
        if self.os_info == "WINDOWS":
            return "\\\\{0}\\{1}".format(socket.getfqdn(self.machine_name) or self.machine_name, path.replace(':', '$'))

        return path

    def execute(self, script, script_arguments=None):
        """Execute the script remotely on a client.

        Args:
            script              (str)   --  path of the script file to execute on the
            remote client

            script_arguments    (str)   --  arguments to be passed to the script

                **This is applicable only for UNIX machines right now**

                default: None
            
            

        """
        if self.is_commvault_client is True:
            execution_method = self._execute_with_cvd
        else:
            execution_method = self._execute_with_credential

        if script_arguments:
            return execution_method(script, script_arguments)

        return execution_method(script)

    def execute_command(self, command):
        """Executes a command on the machine.

            An instance of the **Output** class is returned.

            Output / Exception messages received from command execution are
            available as the attributes of the class instance.

                output_instance.output              --  raw output returned from the command

                output_instance.formatted_output    --  o/p received after parsing the raw output

                output_instance.exception           --  raw exception message

                output_instance.exception_message   --  parsed exception message from the raw o/p


        Args:
            command     (str)   --  command to be executed on the machine

        Returns:
            object  -   instance of Output class

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    # OS related functions
    def check_directory_exists(self, directory_path):
        """Check if a directory exists on the client or not.

        Args:
            directory_path  (str)   --  path of the directory to check

        Returns:
            bool    -   boolean value whether the directory exists or not

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def check_file_exists(self, file_path):
        """Check if a file exists on the client or not.

        Args:
            file_path  (str)   --  path of file to check

        Returns:
            bool    -   boolean value whether the file exists or not

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def create_directory(self, directory_name, force_create=False):
        """Creates a directory on the client, if it does not exist.

        Args:
            directory_name  (str)   --  name / full path of the directory to create

            force_create    (bool)  --  deletes the existing directory and creates afresh

        Returns:
            None    -   if directory creation was successful

        Raises:
            Exception:
                if directory already exists

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def rename_file_or_folder(self, old_name, new_name):
        """Renames a file or a folder on the client.

        Args:
            old_name    (str)   --  name / full path of the directory to rename

            new_name    (str)   --  new name / full path of the directory

        Returns:
            None    -   if directory was renamed successfully

        Raises:
            Exception:
                if failed to rename the directory

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def remove_directory(self, directory_name, days=None):
        """Removes a directory on the client.

        Args:
            directory_name  (str)   --  name of the directory to remove

            days            (int)   --  directories older than the given days
            will be cleaned up

                default: None

        Returns:
            True    -   if directory was removed successfully

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to remove the directory

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_file_size(self, file_path, in_bytes=False, size_on_disk=False):
        """Gets the size of a file on the client.

        Args:
            file_path   (str)   --  path of the file to get the size of

            in_bytes    (bool)  --  if true returns the size in bytes

            size_on_disk (bool) --  if size on disk should be returned

        Returns:
            float   -   size of the file on the client

        Raises:
            Exception:
                if failed to get the size of the file

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_folder_size(self, folder_path, in_bytes=False, size_on_disk=False):
        """Gets the size of a folder on the client.

        Args:
            folder_path     (str)   --  path of the folder to get the size of

            in_bytes        (bool)  --  if true returns the size in bytes

            size_on_disk    (bool)  --  if size on disk should be returned

        Returns:
            float   -   size of the folder on the client

        Raises:
            Exception:
                if failed to get the size of the folder

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_file_stats_in_folder(self, folder_path):
        """Gets the total size in bytes by summing up the individual file size for files present in the directories and
                subdirectories of the given folder_path

                Args:
                    folder_path     (str)   --  path of the folder to get the size of

                Returns:
                    float   -   size of the folder on the client (in Bytes)

                Raises:
                    Exception:
                        if failed to get the size of the folder
                        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_storage_details(self, root=False):
        """Gets the details of the Storage on the Client.
            Returns the details of all paths, if root is set to the default value False.
            If root is set to True, it returns the details of only `/`

        Args:
            root    (bool)  --  boolean flag to specify whether to return details of all paths,
                                    or the details of the path mounted on root(/)

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_disk_count(self):
        """Returns the number of disks on the machine.

        Returns:
            int     -   disk count of the machine

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to get the disk count for the machine

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    # Registry related operations
    def check_registry_exists(self, key, value=None):
        """Check if a registry key / value exists on the client or not.

        Args:
            key     (str)   --  registry path of the key

            value   (str)   --  value of the registry key

        Returns:
            bool    -   boolean value whether the registry key / value exists or not

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def create_registry(self, key, value, data, reg_type):
        """Creates a registry key / value on the client, if it does not exist.

        Args:
            key     (str)       --  registry path of the key

            value   (str)       --  value of the registry key

            data    (str)       --  data for the registry value

            reg_type(str)       --  datatype of the registry key

        Returns:
            bool    -   if registry key / value creation was successful

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to create the registry key

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def update_registry(self, key, value, data=None, reg_type='String'):
        """Updates the value of a registry key / Adds the key (if it does not exist) on the client.

        Args:
            key     (str)       --  registry path of the key

            value   (str)       --  value of the registry key

            data    (str)       --  data for the registry value

            reg_type(str)       --  type of the registry value to add

                Valid values are:

                    - String
                    - Binary
                    - DWord
                    - QWord
                    - MultiString

        Returns:
            bool    -   if registry value was updated successfully

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def compare_files(
            self,
            destination_machine,
            source_file_path,
            destination_file_path,
            algorithm="MD5"):
        """Compares the contents of the 2 files given.

        Args:
            destination_machine     (object)    --  Machine class object for destination
            machine

            source_file_path        (str)       --  path of the source file to compare

            destination_file_path   (str)       --  path of the destination file to compare

            algorithm               (str)       --  Specifies the cryptographic hash function for
                                                    computing the hash value of the contents.

                Default: "MD5".

              The acceptable values for algorithm parameter are:
                 * SHA1
                 * SHA256
                 * SHA384
                 * SHA512
                 * MD5

        Returns:
            bool    -   boolean whether the files are same or not

                True:   files are same

                False:  files are different

        Raises:
            Exception:
                If source_file_path does not exist.

                If destination_file_path does not exist.

        """
        source_hash = self._get_file_hash(source_file_path, algorithm=algorithm)
        destination_hash = destination_machine.get_file_hash(
            destination_file_path, algorithm=algorithm)

        return source_hash == destination_hash

    def compare_folders(
            self,
            destination_machine,
            source_path,
            destination_path,
            ignore_files=None,
            ignore_folder=None,
            ignore_case=False,
            algorithm="MD5"):
        """Compares the two directories on different machines.

              Args:
                  destination_machine     (object)    --  Machine class object for destination
                                                          machine.

                  source_path             (str)       --  path on source machine that is to be
                                                          compared.

                  destination_path        (str)       --  path on destination machine that is
                                                          to be compared.

                  ignore_files            (str)       --  files/patterns that are to be ignored.

                  ignore_folder           (list)      --  list of folders to be ignored.
                    Default: None.

                  ignore_case             (bool)      --  ignores the case if set to True.
                    Default: False.

                  algorithm               (str)       --  Specifies the cryptographic hash
                                                          function to use for computing the
                                                          hash value of the contents.

                   Default: "MD5".

                    The acceptable values for algorithm parameter are:
                       * SHA1
                       * SHA256
                       * SHA384
                       * SHA512
                       * MD5


              Returns:
                  list    -   file paths which are different on the destination machine.

              """
        from . import logger
        log = logger.get_log()
        source_hash = self._get_folder_hash(source_path, ignore_folder=ignore_folder,
                                            ignore_case=ignore_case, algorithm=algorithm)
        log.info("Source Hash : {0}".format(source_hash))
        destination_hash = destination_machine.get_folder_hash(destination_path,
                                                               ignore_folder=ignore_folder,
                                                               ignore_case=ignore_case,
                                                               algorithm=algorithm)
        log.info("Destination Hash : {0}".format(destination_hash))
        difference = source_hash - destination_hash
        log.info("Difference : {0}".format(difference))
        if bool(difference):
            return self._validate_ignore_files(dict(difference).keys(), ignore_files)

        return []

    def copy_from_local(self, local_path, remote_path, **kwargs):
        """Copies the file / folder present at the given path to the path specified on the
            remote machine.

        Args:
            local_path      (str)   --  path of the file / folder on the local machine

            remote_path     (str)   --  path of the directory to which the file / folder
            should be copied on the remote machine

            \*\*kwargs      (dict)  --  optional arguments

                Available kwargs Options:

                    threads     (int)   -- Number of threads to be used by copy

                    raise_exception (bool) -- set to True to raise exception if copy failed

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def copy_folder(self, source_path, destination_path, optional_params='', **kwargs):
        """Copies the directory/file specified at source path to the destination path.

        Args:
            source_path         (str)   --  source directory to be copied

            destination_path    (str)   --  destination path where the folder has to be copied

            \*\*kwargs          (dict)  --  optional arguments

                Available kwargs Options:

                    threads     (int)   -- Number of threads to be used by copy

                    raise_exception (bool) -- set to True to raise exception if copy failed

                    recurse     (bool)  --  False if you do not want to recurse into subfolders
                                            Default: True

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to connect to the machine where the copy has to done locally

                if failed to copy files from source to destination

                if either of the source or destination path specifies is wrong

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def copy_from_network_share(self, network_path, destination_path, username, password, **kwargs):
        """Copies the file/folder from the given network path to the destination path on
           the machine represented by this Machine class instance.

        Args:
            network_path        (str)   --  full UNC path of the file/folder to be copied

            destination_path    (str)   --  destination folder to copy the file/folder at

            username            (str)   --  username to access the network path

                e.g.; Domain\\\\Username

            password        (str)   --  password for the above mentioned user

            \*\*kwargs      (dict)  --  optional arguments

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

                if failed to copy file/folder from mounted drive

                if failed to un mount network drive

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def read_file(self, file_path, **kwargs):
        """Returns the contents of the file present at the specified file path.

        Args:
            file_path   (str)   --  full path of the file to get the contents of

            \*\*kwargs  (dict)  --  Optional arguments

        Returns:
            str     -   string consisting of the file contents

        Raises:
            Exception:
                if no file exists at the given path

                if failed to get the contents of the file

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_files_in_path(self, folder_path, recurse=True, days_old=0):
        """Returns the list of all the files at the given folder path.

        Args:
            folder_path     (str)   --  full path of the folder to get the list of files from

            recurse (bool) -- True -- as default value, if needs to recurse through sub folders

            days_old        (int)   --  Number of days old to filter the files or folders

        Returns:
            list    -   list of the files present at the given path

        Raises:
            Exception:
                if failed to get the list of files

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_folders_in_path(self, folder_path, recurse=True):
        """Returns the list of all the folders at the given folder path.

        Args:
            folder_path     (str)   --  full path of the folder to get the list of folders from

            recurse (bool) -- True -- as default value, if needs to recurse through sub folders

        Returns:
            list    -   list of the folders present at the given path

        Raises:
            Exception:
                if failed to get the list of folders

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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

        raise NotImplementedError('Method Not Implemented by the Child Class')

    def join_path(self, path, *args):
        """Joins the paths given in the args list with the given path using the os separator based
            on the OS / Type of the Machine

        Args:
            path    (str)       --  root path to join the rest of the elements to

            *args   (tuple)     --  list of the elements of path to join to the root path

        Returns:
            str     -   full path generated after joining all the elements using the OS sep

        """
        return self.os_sep.join(
            [path.rstrip(self.os_sep)]
            + [arg.rstrip(self.os_sep) for arg in args]
        )

    def get_file_hash(self, file_path, algorithm="MD5"):
        """Returns MD5 hash value of the specified file at the given file path.

          Args:
              file_path       (str)   --  Path of the file to get the hash value of.

              algorithm       (str)   --  Specifies the cryptographic hash function for
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
        return self._get_file_hash(file_path, algorithm=algorithm)

    def get_folder_hash(self, directory_path, ignore_folder=None,
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

                Default: "MD5".

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
        return self._get_folder_hash(
            directory_path,
            ignore_folder=ignore_folder,
            ignore_case=ignore_case,
            algorithm=algorithm
        )

    def compare_lists(self, source_list, destination_list, sort_list=False):
        """Compares the source list with destination list
            and checks if they are same.

         Args:
            source_list         (list)  --  list1 to compare the contents of

            destination_list    (list)  --  list2 to compare the contents of

            sort_list           (bool)  --  boolean flag specifying whether the lists should
            be sorted before the comparison or not

                default: False

        Returns:
            tuple   -   tuple consisting of a boolean and a string, where:

                bool:

                    returns True if the lists are identical

                    returns False if the contents of the lists are different

                str:

                    empty string in case of True, otherwise string consisting of the
                    differences b/w the 2 lists separated by new-line

        """
        return self._compare_lists(source_list, destination_list, sort_list=sort_list)

    def generate_executable(self, file_path, directory_path=None):
        """Converts a Python file into an Executable file

            Args:
                file_path                 (str)    --  path of the python file

                directory_path            (str)    --  destination folder of the executable file

            Returns:
                str    --  Path of the executable file

            Raises:
                Exception:
                    if specified path doesn't exist

                    if the directory cannot be created

                    if pyinstaller fails due to errors in python file

        """
        # Check whether the given file is a python file or not
        if file_path.split('.')[1] != 'py':
            raise Exception('Method accepts only python files')

        # Check if the Python file exists
        if not os.path.exists(file_path):
            raise Exception(f"Python File not found at : {file_path}")

        file_directory, file_name = os.path.split(file_path)
        file_name = file_name.replace('.py', '.exe')
        if directory_path is None:
            directory_path = file_directory

        # Check if the directory exists
        if not os.path.exists(directory_path):
            try:
                os.mkdir(directory_path)
            except Exception as exception:
                raise Exception(exception)

        pyinstaller_path = os.path.join(os.path.dirname(sys.executable), 'Scripts', 'pyinstaller.exe')
        command = f'&"{pyinstaller_path}" --distpath "{directory_path}" --onefile "{file_path}" --clean'
        output = self.execute_command(command)

        if 'error' in output.exception or 'not recognized' in output.exception:
            raise Exception(output.exception)
        else:
            return self.join_path(directory_path, file_name)

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
        """Generates and adds random test data at the given path with the specified options

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def disconnect(self):
        """Disconnects the current session with the machine.

            Deletes the object's attributes.

            Removes the Credentials File as well, if it was created.

        """
        self._is_connected = False

        del self.commcell_object
        del self.username
        del self.password
        del self.client_object

        try:
            os.unlink(self.credentials_file)
        except (OSError, TypeError):
            # Continue silently, as the file might already have been removed
            pass

        del self.credentials_file
        del self.is_commvault_client

        del self._client
        del self._script_generator

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

        raise NotImplementedError('Method Not Implemented by the Child Class')

    def reboot_client(self):
        """Reboots the machine.

            Please NOTE that the connectivity will go down in this scenario, and the Machine
            class may not be able to re-establish the connection to the Machine.

            In such cases, the user will have to initialize the Machine class instance again.

            Args:
                None

            Returns:
                object  -   instance of the UnixOutput class

            Raises:
                Exception:
                    if failed to reboot the client

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def shutdown_client(self):
        """shutdown the machine.

            This method turns off active host, Required to implement unplanned Failover Test Case.

            Args:
                None

            Returns:
                object  -   instance of the WindowsOutput class

            Raises:
                Exception:
                    if it fails to shut down machine.

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def kill_process(self, process_name=None, process_id=None):
        """Terminates a running process on the client machine either with the given
            process name or the process id.

            Args:
                process_name    (str)   --  Name of the process to be terminate

                                                Example: cvd

                process_id      (str)   --  ID of the process ID to be terminated

            Returns:
                object  -   instance of the UnixOutput class

            Raises:
                Exception:
                    if neither the process name nor the process id is given

                    if failed to kill the process
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def is_stub(self, file_name, is_nas_turbo_type=False):
        """This function will verify whether file is stub

            Args:
                file_name (str): file full name

                is_nas_turbo_type  (bool): True for NAS based client.

             Return: True if the file is stub otherwise return False

             Raises:
                Exception:
                        if error occurred
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def block_tcp_port(self, port, time_interval=600, **kwargs):
        """blocks given tcp port no on machine for given time interval

            Args:

                port            (int)   --  Port no to block

                time_interval   (int)   --  time interval upto which port will be blocked

            kwargs options:

                is_sql_port_lock    (bool)  --   Speicifes whether this operation is for blocking sql dynamic port

            Returns:

                None

            Raises:

                Exception:

                    if failed to block the port
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_port_usage(self, process_id=None, all_protocols=True):
        """ get the netstat output from the machine

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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

        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_checksum_list(self, data_path, sorted_output=True):
        """Gets the list of checksum of items from the machine on a give path
        here it just creates an interface, child class will implement
        detail function

             Args:
                data_path      (str)   --  directory path
                                            to get the checksum list

                sorted_output  (bool)  --  to specify whether
                                            the checksum list should be sorted.

            Returns:
                list    -   list of checksum of items from  the machine

            Raises:
                Exception:
                    if any error occurred while getting the checksum of items.

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def stop_firewall(self):
        """turn off firewall service on the current client machine
        Returns:
            None: firewall is turned off successfully
        Raises:
            Exception:
                if command to turn off firewall fails
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def modify_content_of_file(self, file_path, content='CVappended'):
        """append data to a file at specified path on this machine

        Args:
            file_path   (str)   --  path of file to be modified

            content     (str)   --  content that is to be appended to file

        Returns:
            None

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to append data to file

        """
        command = 'echo {1} >> {0}'.format(file_path, content)
        output = self.execute_command(command)
        if output.exception:
            raise Exception(output.exception_code, output.exception)

    def hide_path(self, path):
        """hide specified path on the machine

                Args:
                    path   (str)   --  path to be hidden on machine

                Returns:
                    None

                Raises:
                    Exception(Exception_Code, Exception_Message):
                        if failed to hidden a file

                """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def unhide_path(self, path):
        """unhide specified path on the machine

                Args:
                    path   (str)   --  path to be unhidded on machine

                Returns:
                    None

                Raises:
                    Exception(Exception_Code, Exception_Message):
                        if failed to unhide a file

                """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def nfs4_setfacl(self, object_path, ace_type, ace_principal, ace_permissions, ace_flags='',
                     user_group_flag=False):
        """manipulates the NFSv4 Access Control List (ACL) of one or more files (or directories),
           provided they are on a mounted NFSv4 filesystem which supports ACLs.

            Args:
                object_path      (str)    -- path of file or directory for which ACL
                need to be applied

                ace_type         (str)    -- action which need to taken (Allow/Deny)

                ace_principal    (str)    -- people for which we are applying the access

                ace_permissions  (object) -- permissions which needs to be applied

                ace_flags       (str)     -- different types inheritance (d/f/n/i)

                user_group_flag (bool)    -- when ace_principal is group this flag need to be set

            Returns:
                None

            Raises:
                Exception:
                    if any error occurs in applying ACL
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def set_logging_filesize_limit(self, service_name, limit='5'):
        """set max log file size limit for a CV service_name.

            Args:
                 service_name         (str)  -- name of valid CV service name

                 limit                (str)  -- log level to be set , default : 5

            Returns:
                 None
            Raises:
                 Exception:
                     if any error occurred while updating debug log level
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')


    def delete_task(self, taskname):
        """ Deletes the specified task on the client
            Args:
                taskname (str): Taskname to delete

            Returns:
                Output for the task execution command
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def wait_for_task(
            self,
            taskname,
            taskstatus='Ready',
            retry_interval=20,
            time_limit=5,
            hardcheck=True):
        """ Wait for scheduled task to complete on client

            Args:
                taskname          (str)    -- Name of the task to check for completion

                taskstatus        (str)    -- Expected task status
                                                'Running' OR 'Ready'

                retry_interval    (int)    -- Interval (in seconds), checked in a loop. Default = 2

                time_limit        (int)    -- Time limit to check for. Default (in minutes) = 5

                hardcheck         (bool)   -- If True, module will exception out if task is not complete.
                                              If False, module will return with non-truthy value

            Returns:
                True/False        (bool)   -- In case task is Ready/Not Ready

            Raises:
                Exception if :

                    - failed during execution of module
                    - Task did not reach the expected state

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def create_task(self, taskoptions):
        """ Create a scheduled task on the machine
            Args:
                taskoptions     (str)    : Task options for the schtasks /create command

            Returns:
                Output for the task execution command
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def execute_task(self, taskname):
        """ Executes a scheduled task immediately on the machine
            Args:
                taskname     (str)    : Task name to execute

            Returns:
                Output for the task execution command
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def has_active_session(self, user):
        """ Check if a user has an active session on the Machine
            Args:
                user     (str)    : User Name for which to check the active user session

            Returns:
                True if user has an active session
                False if not
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_login_session_id(self, username):
        """ Gets the session id for the logged in user
            Args:
                username     (str)    : User Name for which to check the active user session

            Returns:
                user's session id (int)

            Raises:
                Exception: If failed to get session id for the user
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def logoff_session_id(self, sessionid):
        """ Logs off a user with given session id

            Args:
                sessionid (str): Active OR Disconnected user session id of the user

            Raises:
                Exception: If failed to logg off user
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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

        raise NotImplementedError('Method Not Implemented by the Child Class')

    def read_csv_file(self, file_path):
        """Reads the provided CSV file and returns a dictionary structure of its data

            Args:
                file_path   (str)   --  The path of the CSV file to open

            Returns:
                List of dictionaries with key as the CSV header

            Raises:
                Exception:
                    if the file failed to open

                    if failed to parse CSV data

        """

        import csv
        from io import StringIO

        file_cnt = self.read_file(file_path)
        file_obj = StringIO(file_cnt)
        return csv.DictReader(file_obj)

    def change_system_time(self, offset_seconds=0):
        """Changes the system time as per the offset seconds provided w.r.t to current system time

            Args:
                offset_seconds      (int)   --  Seconds to offset the system time.
                Example, 60 will change the system time to 1 minute forward and -180 will change
                system time 3 minutes backward

            Returns:
                None

            Raises:
                Exception, if the powershell command execution fails

        """

        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_ace(self, user, path):
        """Get ACEs of a file or folder for particular user

        Args:
            user            (str)   --  User for which ACEs are required

            path            (str)   --  File or folder path

        Returns:
                list       -- list of ACEs for that user
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
                                        1- Permission will be set to target
                                        folder and only to child folder
                                        2 -permission will be to target folder,
                                         all subfolder and files
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
                                        1- Permission will be set to target folder and only to child folder
                                        2 -permission will be to target folder, all subfolder and files
        Returns:
            output       -- Depends on the task

        Raises:
                Exception, if the powershell command execution fails

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')
    
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
        NotImplementedError("Method is Implemented by child class")
        

    def get_cpu_usage(self, client, interval, totaltime, processname, outputpath, wait_for_completion):
        """Gets the CPU usage for a process on the remote machine in given intervals for given total time.

        Args:
            client (obj)           -- Client object for a remote machine
            interval (int)         -- interval in seconds for which it will get the cpu usage for a process
            totaltime (int)        -- total time in minutes for which it will get the cpu usage for a process
            processname (str)      -- Process name for which cpu usage to be generated.
            outputpath  (str)      -- Output path to which the generated output to be written
            wait_for_completion (boolean)   -- Waits until the command completes

        Return: Return True if the command is executed

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def add_minutes_to_system_time(self, minutes=1):
        """Adds specified number of minutes to current system time
            Args:
                minutes(int)   -- Minutes to add
                    Default - 1

            Raises:
                Exception, if the powershell command execution fails

            Returns:
                String name of the owner result"""

        raise NotImplementedError('Method Not Implemented by the Child Class')

    def add_days_to_system_time(self, days=1):
        """Adds specified number of days to current system time
            Args:
                days(int)   -- Days to add
                    Default - 1

            Raises:
                Exception, if the powershell command execution fails

            Returns:
                String name of the owner result"""

        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_active_cluster_node(self, cluster_name):
        """This method return active windows cluster active node

        Args:
            cluster_name          (str)   --   Cluster client name

        Returns:
            active_node     -   returns Active node Cluster

        Raises:
            None

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_cluster_nodes(self, cluster_name):
        """Returns all cluster nodes

        Args:
            cluster_name          (str)   --   Cluster client name

        Returns:
            nodes        (list)     --   Returns all cluster nodes

        Raises:
            None

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def do_failover(self, activenode, passivenode):
        """Run Failover method switch between cluster nodes

        Args:
            activenode          (str)   --   Active cluster node

            passivenode          (str)  --   Passive  cluster node

        Returns:
            None

        Raises:
            None

        """

        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_file_owner(self, file_path):
        """Get the owner of the file
            Args:
                file_path(str)   -- Path of the file

            Returns:
                String name of the owner result"""

        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_file_group(self, file_path):
        """Get the group of the file/directory
            Args:
                file_path(str)   -- Path of the file

            Returns:
                String name of the group result"""

        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_subnet(self):
        """

        Get Subnet mask of the machine

        Returns:
            (str) Subnet Mask of machine
        """
        raise NotImplementedError("Method not implemented by the child Class")

    def get_default_gateway(self):
        """

        Get Default Gateway of the machine

        Returns:
            (str) Default Gateway
        """
        raise NotImplementedError("Method not implemented by the child Class")

    def is_dhcp_enabled(self):
        """

        Whether DHCP is enabled on the machine
        Returns: (bool) DHCP enabled
        """
        raise NotImplementedError("Method not implemented by the child Class")

    def get_dns_servers(self):
        """

        Gets all DNS servers from the machine
        Returns: (list) DNS servers
        """
        raise NotImplementedError("Method not implemented by the child Class")

    def add_host_file_entry(self, hostname, ip_addr):
        """

        Add an entry to host file

        Args:
            hostname (str): hostname of the entry

            ip_addr (str): ip address to assign to the hostname

        Raises:
            Exception if host file change fails

        """
        raise NotImplementedError("Method not implemented by the child Class")

    def remove_host_file_entry(self, hostname):
        """

        Remove the host file entry by hostname

        Args:
            hostname    (str): hostname of the entry to be removed

        Raises:
            Exception if host file entry change fails
        """
        raise NotImplementedError("Method not implemented by the child Class")

    def get_logs_for_job_from_file(self, job_id=None, log_file_name=None, search_term=None):
        """From a log file object only return those log lines for a particular job ID.

        Args:
            job_id          (str)   --  Job ID for which log lines need to be fetched.
                default -   None

            log_file_name   (bool)  --  Name of the log file in case of cv client else log name with full path
                default -   None

            search_term     (str)   --  Only capture those log lines containing the search term.
                default -   None

        Returns:
            str     -   \r\n separated string containing the requested log lines.

            None    -   If no log lines were found for the given job ID or containing the given search term.

        Raises:
            None

        """
        raise NotImplementedError("Method not implemented by the child Class")
        
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
        raise NotImplementedError("Method not implemented by the child Class")

    def get_event_viewer_logs_message(self, newest_n=1):
        """

         Fetches the message body for n newest event viewer logs with Source as "ContentStore"

         Args:
             newest_n (int) : Newest n log messages that have to be fetched

        Raises:
            Exception, if the powershell command execution fails

        Returns: Message body for n newest event viewer Application logs with source ContentStore
        """
        raise NotImplementedError("Method not implemented by the child Class")

    def list_shares_on_network_path(self, network_path, username, password):
        """
        Lists the shares on an UNC path

        Args:
                network_path    (str)   --  network path of fileserver

                username        (str)   --  username to access the network path

                Ex: DOMAIN\\\\USERNAME

                password        (str)   --  password for above mentioned user

            Returns:
                list    -       List of shares on the given network path

            Raises:
                Exception(Exception Name):

                    if failed to mount network path

                    if command returns an exception

        """

        raise NotImplementedError('Method Not Implemented by the Child Class')

    def modify_test_data(self,
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

            \*\*kwargs  (dict)  --  Optional arguments
            available kwargs Options:
                encrypt_file_with_aes  (bool)  -- whether to aes encrypt files
                    default: False

        Returns:
            bool    -   boolean value True is returned
                        if no errors during data generation.

        Raises:
            Exception:
                if any error occurred while modifying the test data.

        """

        raise NotImplementedError('Method Not Implemented by the Child Class')

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

        raise NotImplementedError('Method Not Implemented by the Child Class')

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

        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError("Method not implemented by the child Class")

    def modify_item_datetime(self, path, creation_time=None, modified_time=None, access_time=None):
        """
        Changes the last Access time and Modified time of files in unix and windows.
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
        raise NotImplementedError("Method not implemented by the child Class")

    def get_vm_ip(self, vm_name=None):
        """
        To get ip address of a VM

        Args:
            vm_name         (str)   -- Name of the VM

        Returns:
            ip address of the vm
       """

        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_share_name(self, directory):
        """
        To get share name of already shared directory

        Args:
            directory   (str)   --  full path string of shared directory
        
        Returns:
            share_name  (str)   --  Name of the network share for given directory if shared
            None                --  if given directory is not shared
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def mount_network_path(self, network_path, username, password, cifs_client_mount_dir=None):
        """Mounts the specified network path on this machine.

        Args:
            network_path    (str)   --  network path to be mounted on this machine

            username        (str)   --  username to access the network path

                Ex: DOMAIN\\\\USERNAME

            password        (str)   --  password for above mentioned user

            cifs_client_mount_dir (str) -- if provided mount the network_path to this(only unixmachine is supported)

        Returns:
            str     -   drive letter where the network path is mounted


        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to mount network path

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def restart_all_cv_services(self):
        """Start all Commvault services using username/password method since SDK cannot talk to the machine
        when services are down. Use SDK service control methods if services are already running.

            Returns:
                None

            Raises:
                Exception while trying to execute command to start the service

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def start_all_cv_services(self):
        """Start all Commvault services using username/password method since SDK cannot talk to the machine
        when services are down. Use SDK service control methods if services are already running.

        Services will not start when system time modification is detected, so force start them with -force flag

            Returns:
                None

            Raises:
                Exception while trying to execute command to start the service

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def stop_all_cv_services(self):
        """Stops all Commvault services using username/password method.

            Returns:
                None

            Raises:
                Exception while trying to execute command to start the service

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def unzip_zip_file(self, zip_file_path, where_to_unzip):
        """Implemented in unix machine

       Args:
            zip_file_path (string): Path where ZIP file is located.
            where_to_unzip (string): Path at which we have to extarct our file.
        Returns:
            None
        Raises:
                Exception while trying to execute command.
        """
        raise NotImplementedError('Method not Implemented in Windows Client Machine')

    def check_if_pattern_exists_in_log(self, pattern, log_file_name):
        """ Method to check if the given pattern exists in the log file or not

        Args:
            pattern         (str)   -- pattern to be searched inside log file

            log_file_name   (str)   -- log file name

        Returns:
            True if pattern exists, False otherwise
        """
        raise NotImplementedError('Method not Implemented in Child class')

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

            """

        raise NotImplementedError('Method Not Implemented by the Child Class')

    def create_local_filesystem(self, filesystem, disk):
        """creates filesystem locally on the machine on the disk
        filesystems supported ['btrfs', 'cramfs', 'ext2', 'ext3', 'ext4', 'fat', 'minix', 'msdos', 'vfat', 'xfs']

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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

        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def run_cvping(self, destination, family_type='UseIPv4', port='8400'):
        """Executes cvping on machine with provided inputs

            Args:

                Destination     (str)       --  Destination machine name or IP

                family_type     (str)       --  Address to be used in ping.

                        Supported Values are UseIPv4, UseIPv6 or UseIPAny. Default is UseIPv4

                port            (str)       --  Port no to be used in ping (Default:8400)

            Returns:

                bool    --  Whether CVping succeeded or not for given input

            Raises:

                Exception:

                    if failed to find cvping in base folder
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

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

                    sequential      (bool)      --  Specifies whether it is sequential or random access for read/write
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
        raise NotImplementedError('Method Not Implemented by the Child Class')

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

        raise NotImplementedError('Method Not Implemented by the Child Class')

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
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def remove_additional_software(self,package):
        """This method will remove all the 3rd party software from the client machine

        Args:
            package (str): software we have to remove.

        Raises:
            NotImplementedError: if it failed to execute
        """
        
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def copy_file_between_two_machines(self, src_file_path, destination_machine_conn, destination_file_path):
        """
        Transfer files between two machines.
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def verify_installed_packages(self, packages):
        """verify the packages are installed on the client

        Args:
            packages (list): list of package ids. for package id, please refer to the corresponding constants

        Raises:
            NotImplementedError: if it failed to execute
        """
        
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def change_inheritance(self, folder_path, disable_inheritance=True):
        """Disables or enables inheritance on the folder
            Args:
                folder_path         (str)   -   Full path of the folder
                disable_inheritance (bool)  -   whether to disable or enable inheritance on folder

            Raises:
                If given folder is not present on machine -
                    Provided folder : folder_path is not present on machine : machine_name
        """

        raise NotImplementedError('Method Not Implemented by the Child Class')

    def copy_file_locally(self, source, destination):
        """
        Copies file from one directory to another
        Args:
            source(str)         --  Source file path
            destination(str)    --  destination file path

        Raises:
            NotImplementedError: if it failed to execute
        """

        raise NotImplementedError('Method Not Implemented by the Child Class')

    def change_hostname(self, new_hostname):
        """
        Changes the hostname of a given machine

        Args:
            new_hostname (str): hostname to be set on the machine

        Raises:
            NotImplementedError: if it failed to execute
        """

        raise NotImplementedError('Method Not Implemented by the Child Class')

    def add_to_domain(self, domain_name, username, password):
        """
        adds a given windows machine to domain
        Args:
            domain_name(str)    -   name of the domain
            username(str)       -   Username for the domain controller
            password(str)       -   password for the domain controller

        Raises:
            NotImplementedError: if it failed to execute
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def disable_ipv6(self):
        """
        disables IPv6 address for the machine
        Raises:
            NotImplementedError: if it failed to execute
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def get_hostname(self):
        """
        Gets the hostname of the machine
        Raises:
            NotImplementedError: if it failed to execute
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')
    
    def get_ibmi_version(self, value="*CURRENT"):
        """Gets the version and release of IBMi client.
        Args:
            value     (str)   --  Version to return
            Valid values : "*SUPPORTED", "*CURRENT"

        Returns:
            str   -   Version of the IBMi client
        Raises:
            Exception:
                if failed to get the version from client

                """
        raise NotImplementedError('Method Not Implemented by the Child Class')