# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file consisting of common operations that may be required for automating any test case.

Any common operations that are not any machine specific can be added to this file.

The instance of the OptionsSelector can be used to perform operations such as,

1. Creating a Unique directory name to restore the contents to
2. Get the Windows client to restore the data to, in case of Out-of-Place restore
3. Get the UNIX client to restore the data to, in case of Out-of-Place restore


OptionsSelector:

    __init__()                      --  initializes instance of the OptionsSelector class

    __repr__()                      --  Representation string for the instance of the
                                        OptionsSelector class

    pop_keys()                      --  Remove specific keys of a dictionary send as a list

    sleep_time()                    --  Calls time.sleep for specified time and logs it

    get_var()                       --  Return default value if variable value is empty

    get_custom_str()                --  Returns a unique string based on pre & post substrings

    _get_restore_dir_name()         --  returns the directory name to restore the contents at

    get_windows_restore_client()    --  returns windows restore client object and restore path

    get_linux_restore_client()      --  returns linux restore client object and restore path

    get_client()                    --  Gets the client data from DB for given query type

    get_ma()                        --  Gets the media agent data from DB for given query type

    get_ready_clients()             --  Takes a list of clients and returns a tuple of
                                        ready clients and number of clients

    get_client_ids()                 --  Gets the client data from DB for given query type

    exec_commserv_query()           --  Executes DB query against Commserve DB

    update_commserve_db()           -- Updates tables on the Commserv DB

    update_commserve_db_via_cre()   --  Updates tables on the Commserv DB using custom reports engine api

    get_paccess_passwd()            -- Gets the pAccess password from registry

    create_storage_pool()           --  Create Storage Pool

    remove_directory()              --  Removes a directory from file system from client

    create_directory()              --  Creates a directory on file system for client

    create_test_data()              --  Creates test data on client

    create_uncompressable_data()    --  Creates uncompressable data on the client

    delete_nth_files_in_directory() --  Deletes every nth file in the directory

    is_regkey_set()                 --  Check if a given registry key is set or not

    check_reg_key()                 --  Check/Gets the registry key value for given registry key
                                            on a client.

    update_reg_key()                --  Updates the registry key value for given registry key on a client

    get_machine_object()            --  Creates/Returns machine object based on user defined
                                            input of client name as string or machine object.

    get_gxglobalparam_val()         --  Fetches value for the given GxGlobalParam property name from CS DB

    is_client_in_client_group()     --  Validate if the client is associated to any of the client groups in the given
                                            list.

    Delete a client on commcell()   -- Deletes a client con commcell

    wait_until_client_ready()       --  Waits for client to be ready until a given interval of time.

    _get_resultset()                --  Gets the resultset from the DB

    delete_credentials()            --  Deletes saved client credentials on the controller for the given client.

    start_rdp_session()             --  Creates a remote desktop connection with the client.
    
    validate_restartservices()      --  Validates if services have restarted or not.

    get_custom_password()           --  Creates a custom password with letters, numbers and special characters.

    convert_size()                  --  converts bytes to human readable memory unit string

    convert_no()                    --  converts number to human readable unit string



CVEntities:
    __init__()                  -- Initialize instance of the CVEntities class

    __repr__()                  -- Representation string for the instance of the
                                    CVEntities class for specific test case

    create()                    -- Creates various commcell entities

    delete()                    -- Deletes various commcell entities

    cleanup()                   -- Deletes all the entities created as part of
                                    multiple testcase calls to create() module

    get_mount_path()            -- Returns the mount path where library shall be
                                    created for a given Media Agent

    create_client_groups()      -- Creates client groups from a given list of client
                                    group names

    delete_client_groups()      -- Deletes client groups from a given dictionary of
                                    client group properties

    update_clientgroup()        -- Updates the properties of an existing client group

    create_sp_copy()
                                -- Creates a storage policy copy for the given storage policy.

    post_delete()                -- Performs the post delete configuration for the entity.

    post_create()                -- Performs the post creation configuration for the entity

    existing_config()            -- Performs configuration for existing entity.

    _get_entity_objects()       -- Private module to get the dependent entity objects
                                    for a given entity.

    _get_target_props()         -- Gets the target entity properties from target: key
                                    if specified, otherwise gets the properties from
                                    individual entity properties.

    _get_target_str()           -- Target string where the entity will be created.

    _purge_entities()           -- Private module to remove entity properties and
                                    object details from cleanup map dictionary

    refresh()                   -- Refreshes the entity dictionaries and individual
                                    entity configuration dictionaries, which are
                                    created dynamically to hold entity properties.

    validate_logs()             --  Method to validate log with required log line

    Properties:
    ----------

    entity_object_map            -- Dictionary containing created entities and their
                                    properties.

_Backupset/_Subclient/_StoragePolicy/_Disklibrary/_Clientgroup:

    __init__()                   -- Initializes instance of specific class  (Private class)

    object()                     -- Gets the associated object and checks if the entity exists

    target()                     -- Gets the target string on which the entity shall be created

    post_delete()                -- Performs the post delete configuration for the entity

    post_create()                -- Performs the post creation configuration for the entity

    get_properties()             -- Takes in dictionary of entity properties to be created and
                                        dictionary of created entities and sets the entity
                                        properties based on input association and defaults.

    existing_config()            -- Performs configuration for existing entity which
                                        will not be created by the CVEntities class,
                                        due to force option set to False.

    add_args()                   -- Returns the keyword arguments to send to add()
                                        module for creating the entity
"""
import math
import sys
import copy
import datetime
import time
import random
import inspect
import subprocess
import string
import math

from cvpysdk.client import Client
from cvpysdk.commcell import Commcell
from cvpysdk.policies.storage_policies import StoragePolicy

from Web.API.customreports import CustomReportsEngineAPI
from Server.serverhandlers import argtypes, returntype
from Server.JobManager.jobmanager_helper import JobManager
from AutomationUtils import defines

from . import logger
from . import database_constants
from . import constants
from .machine import Machine
from .database_helper import get_csdb, MSSQL
from AutomationUtils import database_helper
from . import cvhelper


class OptionsSelector(object):
    """Class that provides common utilities for running automation"""

    def __init__(self, commcell):
        """Initializes CommonUtils object

            Args:
                commcell    (object)    --  CvPySDK commcell object

        """
        self._commcell = commcell
        self._log = logger.get_log()
        self.arg_map = {}
        self.commserve_instance = "\\commvault"
        self.mssql = None
        #If CS is on Linux, there is no SQL instance called commvault.
        #So it needs to be set to only while making SQL connection with Windows CS.
        if self._commcell.is_linux_commserv:
            self.commserve_instance = ""

    def __repr__(self):
        """Representation string for the instance of the OptionsSelector class."""
        return "OptionsSelector class instance"

    @staticmethod
    def pop_keys(source_dict, source_keys):
        ''' Remove keys of a dictionary'''
        for key in source_keys:
            source_dict.pop(key, None)
        return source_dict

    def sleep_time(self, _time=60, logmessage=None):
        ''' Sleep for the specified interval of time. Default time = 60 seconds.'''
        if logmessage is not None:
            self._log.info(str(logmessage))

        self._log.info("Sleeping for [%s] seconds", str(_time))
        time.sleep(_time)

    @staticmethod
    def get_var(prop, defaultval):
        ''' Return default property value if property value is empty'''
        return defaultval if prop is None or prop == '' else prop

    @staticmethod
    def get_custom_str(presubstr=None, postsubstr=None):
        ''' Returns a unique string based on pre and post sub strings '''
        try:
            presubstr = constants.DESCRIPTION if presubstr is None else presubstr
            postsubstr = str(random.randint(100, 1000)) if postsubstr is None else postsubstr
            _time = '{date:%m-%d-%Y_%H_%M_%S}'.format(date=datetime.datetime.now())
            return '_'.join([presubstr, str(_time), postsubstr])

        except Exception as exp:
            raise Exception("\n {0}: [{1}]".format(inspect.stack()[0][3], str(exp)))

    @staticmethod
    def _get_restore_dir_name():
        """Returns the directory name with current time to restore the contents at."""
        from datetime import datetime
        current_time = datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')
        return 'CVAutomationRestore-' + current_time

    @staticmethod
    def get_drive(machine, size=5120, deferred_drives=None, **kwargs):
        """Iterates over the drives and returns drive with free space greater than specified

            Args:
                machine     (object)    --  Machine class object on which the free space is to be
                                                determined

                size        (int)       --  free space required on this machine
                                            default: 5120 MB

                deferred_drives (list)  --  defers using these drives unless no other drives are available
                                            Ex : ['C', 'D']

                kwargs:
                    max_size    (bool)  --  if True, returns drive with most free space

            Returns:
                str     -   drive path on which free space is greater than specified size
        """
        if deferred_drives is None:
            deferred_drives = ['C']
        if machine.os_info == 'WINDOWS':
            drives_dict = machine.get_storage_details()

            if kwargs.get('max_size'):
                if 'total' in drives_dict:
                    del drives_dict['total']
                if 'available' in drives_dict:
                    del drives_dict['available']
                max_drive = max(
                    drives_dict.keys(), 
                    key=lambda d: drives_dict[d].get('available')
                )
                return max_drive

            for drive in drives_dict:
                if (isinstance(drives_dict[drive], dict) and
                        drives_dict[drive]['available'] >= size and drive not in deferred_drives):
                    return drive + ":\\"
            for drive in drives_dict:
                if (isinstance(drives_dict[drive], dict) and
                        drives_dict[drive]['available'] >= size and drive in deferred_drives):
                    return drive + ":\\"
        else:
            drives_dict = machine.get_storage_details(True)

            if drives_dict['available'] >= size:
                return '/Users/root/commvault_automation/'

        raise OSError(
            "Low disk space on {0}. Please free up some space.".format(machine.machine_name)
        )

    @staticmethod
    def get_custom_password(length=8, strong=False):
        """Creates and returns a custom password of length specified containing 
            letters, numbers and special characters.

            Args:
                length      (int)       --  length of the required custom password

                strong      (bool)      --  enforce strong combination of characters if true and length>=8
            
            Returns:
                str     -   custom password of specified length
        """
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(characters) for _ in range(length))
        if not strong or length < 8:
            return password
        lower_char = random.choice(string.ascii_lowercase)
        upper_char = random.choice(string.ascii_uppercase)
        digit = random.choice(string.digits)
        special_char = random.choice(string.punctuation)
        return f'{password[:-4]}{lower_char}{upper_char}{special_char}{digit}'

    def get_windows_restore_client(self, size=5120):
        """Iterates over the list of available Windows clients on the Commcell,
            and Returns the instance of the Machine class for the valid client,
            and the directory path to restore the contents at.

            The Restore Directory is created on the drive which has the minimum required free
            space available.

                e.g.:
                    C:\\CVAutomationRestore-DATETIME

                    E:\\CVAutomationRestore-DATETIME

            Args:
                size    (int)   --  minimum available free space required on restore machine

                    default: 5120 MB

            Returns:
                (object, str)   -   (instance of the Machine class, the restore directory path)

                    object  -   instance of the Machine class for the Windows client

                    str     -   directory path to restore the contents at

            Raises:
                Exception:
                    if no windows client with specified size exists on commcell

                    if any exception is raised while determining restore client
        """
        self._log.info("Get Windows restore client from commcell")

        try:
            for client in self._commcell.clients.all_clients:
                client_object = self._commcell.clients.get(client)

                if 'windows' in client_object.os_info.lower():
                    try:
                        windows_client = Machine(client_object.client_name, self._commcell)
                    except Exception:
                        # raises Exception if machine is not reachable / services are down
                        # continue to next client in such cases
                        continue

                    try:
                        drive = self.get_drive(windows_client, size)
                    except OSError:
                        continue

                    dir_path = drive + self._get_restore_dir_name()
                    windows_client.create_directory(dir_path)

                    self._log.info(
                        "Windows Restore Client obtained: %s", windows_client.machine_name
                    )
                    self._log.info("Windows Restore location: %s", dir_path)
                    return windows_client, dir_path

            raise Exception(
                "No Windows client with size equal or more than {0}MB exists on commcell".format(
                    size
                )
            )
        except Exception as excp:
            raise Exception("Failed to get windows restore client with error: {0}".format(excp))

    def get_linux_restore_client(self, size=5120):
        """Iterates over the list of available UNIX clients on the Commcell,
            and Returns the instance of the Machine class for the valid client,
            and the directory path to restore the contents at.

            The Restore Directory is created in the Desktop of root on the client,
            which has the minimum required free space available.

                e.g.:
                    /root/Desktop/CVAutomationRestore-DATETIME

            Args:
                size    (int)   --  minimum available free space required on restore machine

                    default: 5120 MB

            Returns:
                (object, str)   -   (instance of the Machine class, the restore directory path)

                    object  -   instance of the Machine class for the Windows client

                    str     -   directory path to restore the contents at

            Raises:
                Exception:
                    if no linux client with specified size exists on commcell

                    if any exception is raised while determining restore client
        """
        self._log.info("Get UNIX restore client from commcell")

        try:
            for client in self._commcell.clients.all_clients:
                client_object = self._commcell.clients.get(client)

                if ('linux' in client_object.os_info.lower() or
                        'unix' in client_object.os_info.lower()):
                    try:
                        linux_client = Machine(client_object.client_name, self._commcell)
                    except Exception:
                        # raises Exception if machine is not reachable / services are down
                        # continue to next client in such cases
                        continue

                    try:
                        mount_path = self.get_drive(linux_client, size)
                    except OSError:
                        continue

                    dir_path = mount_path + self._get_restore_dir_name()
                    linux_client.create_directory(dir_path)

                    self._log.info(
                        "Linux Restore Client obtained: %s", linux_client.machine_name
                    )
                    self._log.info("Linux Restore location: %s", dir_path)

                    return linux_client, dir_path
            raise Exception(
                "No Linux client with size equal or more than {0} MB exists on commcell".format(
                    size
                )
            )
        except Exception as exp:
            raise Exception("Failed to get linux restore client with error: {0}".format(exp))

    def get_client(self, query_type='all', num=1, ready=True, entity='client', *args, **kwargs):
        """Fetches the details from Commserve DB with specific requirement.
            Requirement is mapped to query_type

            Args:
                query_type   (str)   -- query type to execute, to fetch data from Commserver DB

                num (int)             -- Number of clients to return
                                         Default value = 1
                                         If num='all' fetch all available clients

                ready (bool)          -- True - Clients passing readiness check will be returned
                                         False - Clients whether ready or not shall be returned

                entity (str)          -- Supported strings -> 'client' or 'mediaagent'
                                            Default is 'client'

                *args -- Arguments to this module to control module execution and return value

                    'all': Returns tuple with (<first column list>, Complete resultset)

                **kwargs (dict) -- Contains name value pairs for various arguments

            Returns:
                (list) -- First column list from the resultset

                (tuple) -- tuple with (<first column list>, Complete resultset)

            Raises:
                Exception:
                    if query argument value is not supported

                    if failed to execute DB query.

            Usage:
                get_client() - Returns 1 ready client

                get_client('all', 3, False)
                    Returns 3 clients [ Might or might not be ready ]

                get_client('non_ma', 2)
                    Returns 2 clients on which media agent is not installed/configured

                clients = get_client()
                    Returns 1 ready client.
                    Return type - (Str)
                    clients = 'client1'

                clients = get_client('all', 3, False)
                    Returns 3 client(s) [ Might or might not be ready ] [False]
                    Return type - (List)
                    clients = ['client1', 'client2', 'client3']

                clients = get_client('non_ma', 3)
                    Returns 3 'ready' clients on which media agent is not installed
                    Return type - (list)
                    clients = ['client1', 'client2', 'client3']

                clients = get_client('all', 3, True, 'all')
                    Returns 3 ready client list and their resultset
                    Return type - tuple
                    clients = (['client1', 'client2'], [<client1 resultset>, <client2 resultset>])

        """

        exception_ = "Failed to get {0} details with error".format(entity)
        validate = bool(num)

        try:
            rs_list = self._get_resultset(entity, query_type, validate, **kwargs)
            num = len(rs_list[0]) if (num is None or num == 'all') else num

            if num > len(rs_list[0]):
                raise Exception("Number of required {0}(s): [{1}], Available"
                                " (from DB): [{2}]".format(entity, num, len(rs_list[0])))

            if ready:
                new_list = self.get_ready_clients(rs_list[0], num)[0]
            else:
                new_list = rs_list[0][:num]

            if args and args[0] == 'all':
                # Tuple-> (['cl1', 'cl2'], [cl1 db resultset , cl2 db resultset])
                return (new_list, rs_list[1][:num])

            if num == 1:
                # String-> 'cl1'
                return new_list[0]

            # List-> ['cl1', 'cl2']
            return new_list

        except Exception as excp:
            raise Exception("\n {0}: {1} {2}".format(inspect.stack()[0][3], exception_, str(excp)))

    def get_ma(self, query_type='disk', num=1, ready=True, *args, **kwargs):
        """Fetches the details from Commserve DB with specific requirement.
            Requirement is mapped to query

            Args:
                query   (str)   -- query type to execute, to fetch data from Commserver DB

                    Supported types:

                        diskless: No disk library is configured

                        disk    : At least 1 disk library configured

                        windows : Windows media agent

                        aliasname : Gets the media agent from alias name

                        any : Gets any active media agent (windows or linux)

                num (int)             -- Number of media agents to fetch from DB
                                         Default value : 1

                ready (bool)           -- True  - Media agents passing readiness check shall be
                                                    returned

                                          False - All clients whether ready or not shall be
                                                      returned

                *args -- Arguments to this module to control module execution and return value

                    'all': Returns tuple with (<first column list>, Complete resultset)

                    -Otherwise returns a list or a string based on the argument 'num' value

                **kwargs (dict) -- Contains name value pairs for various arguments

            Returns:
                (list) -- First column list from the resultset

                (tuple) -- tuple with (<first column list>, Complete resultset)

            Raises:
                Exception:
                    if query argument value is not supported

                    if failed to execute DB query.

            Usage:
                ma = get_ma()
                    Returns 1 ready media agent of any platform
                    Return type - (Str)
                    ma = 'client1'

                ma = get_ma('windows')
                    Returns 1 ready media agent (Windows)
                    Return type - (Str)
                    ma = 'client1'

                ma = get_ma('aliasname', ready=False, mount_path='C:\\disklib01')
                    Returns Disklibrary alias for given mount_path  [ May or may not be ready ]
                    Return type - (Str)
                    ma = 'client1'

                ma = get_ma('disk', 3, True, 'all')
                    Returns 3 ready media agents with at least one disk library configured
                    and their resultset
                    Return type - tuple
                    ma = (['client1', 'client2'], [<client1 resultset>, <client2 resultset>])
        """

        self.arg_map = {
            'aliasname': ['mount_path']
        }

        return self.get_client(query_type, num, ready, 'mediaagent', *args, **kwargs)

    def get_ready_clients(self, clients, num=None, validate=True, os_type=None):
        """ Takes a list of clients and returns a list of ready clients

            Args:
                clients(list)    -- list of clients on which check readiness needs to
                                    be performed.

                num (int)        -- Total number of clients to be fetched which pass
                                    readiness checked from 'clients'
                                    Default = 1 client

                validate (bool)  -- Validate if number of clients which passed
                                    readiness check equals 'num' [Total clients
                                    to be fetched]

                os_type (string) -- OS info for the clients for which readiness has to be checked
                                    Eg, "Unix"
            Returns:
                (tuple)        -- (Clients list passed readiness check,
                                    total clients passed)

            Raises:
                Exception:
                    If failed to get client list
        """
        try:
            clientlist = []
            num = len(clients) if num is None else num
            _clients = self._commcell.clients

            if os_type is not None:
                os_type_clients = []
                for client in clients:
                    if os_type in _clients.get(client).os_info:
                        os_type_clients.append(client)
                clients = os_type_clients

            self._log.info("Number of ready clients to fetch = [{0}]".format(num))

            for client in clients:
                if not isinstance(client, str):
                    continue

                client_ = _clients.get(client)
                self._log.info("Executing readiness check on [{0}]".format(client))

                if client_.is_ready:
                    self._log.info("Readiness check passed.")

                    clientlist.append(client)
                    if len(clientlist) >= num:
                        break
                else:
                    self._log.info("Readiness check failed.")

            if validate and num > len(clientlist):
                raise Exception("Required client(s): [{0}], Clients passed readiness"
                                " check: [{1}]".format(num, len(clientlist)))

            self._log.info("Ready clients fetched: [{0}]".format(clientlist))

            self._log.info("Number of clients fetched: [{0}]".format(len(clientlist)))

            return (clientlist, len(clientlist))

        except Exception as excp:
            raise Exception("\n {0} failed to get ready client(s) with"
                            " error {1}".format(inspect.stack()[0][3], str(excp)))

    def get_client_ids(self,
                       query_type='GROUP_ID',
                       entity='client',
                       id_value=None):
        """Fetches the details from Commserve DB with specific requirement.
           Requirement is mapped to query_type

            Args:
                query_type(str)         -- query type to execute, to fetch data from Commserver DB

                entity    (str)         --  Supported string -> 'client' Default is 'client'

                id_value  (str)         --  value to be passed to filter the query

            Returns:
                (tuple) -- tuple with (<first column list>, Complete resultset)

            Raises:
                Exception:

                    if failed to execute DB query.

        """
        try:

            exception_ = "Failed to get [{0}] details with error".format(entity)
            self._log.info("Started executing DB query for entity: {0} with query_typ: {1}"
                           .format(entity, query_type))
            class_name = database_constants.CLASS_MAP[entity]
            class_obj = getattr(database_constants, class_name)
            dbquery = getattr(class_obj, query_type.upper()).value
            if id_value:
                dbquery = dbquery.format(id_value)
            rs_tuple = self.exec_commserv_query(dbquery)
            return rs_tuple[0]

        except Exception as excp:
            raise Exception("\n {0} {1}".format(exception_, str(excp)))

    def exec_commserv_query(self, query):
        """ Executes a DB query against Commserv Database

            Args:
                query (str) -- Database query to execute

            Returns:
                (tuple) -- tuple with (<first column list>, Complete resultset)

            Raises:
                Exception:
                    - if failed to get data from DB
        """
        try:

            self._log.info("Executing DB query: \n %s", str(query))
            csdb = database_helper.CommServDatabase(self._commcell)
            database_helper.set_csdb(csdb)
            csdb = get_csdb()
            csdb.execute(query)
            cur = csdb.fetch_all_rows()
            data = [item[0] for item in cur]

            self._log.info("Commserv DB resultset: [{0}]".format(cur))

            # Return tuple of 1st column list and the complete resultset
            return (data, cur)

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def update_commserve_db(
            self, query, user_name='sqladmin_cv',
            password=None, dbserver=None, dbname=None,
            retryattempts=3, log_query=True, driver=None
    ):
        """ Updates tables in Commserv Database
 
             Args:
                query          (str)    --  Database query to execute

                user_name      (str)    --  Database user name

                password       (str)    --  Database password

                dbserver       (str)    --  Database server and instance.

                dbname         (str)    --  Name of the database

                retryattempts  (int)    --  The number of attempts to retry

                log_query      (bool)   --  Logs the query before executing

                driver      (str)   --  SQL driver name

            Raises:
                Exception:
                    - if failed to update data in DB
        """
        if self.mssql is None:
            cs_machine_obj = Machine(self._commcell.commserv_client)
            if not password:
                self._log.info("Retrieving SQL password from the registry")
                encrypted_pass = cs_machine_obj.get_registry_value(r"Database", "pAccess")
                self._log.info("Decrypting the retrieved password from the registry")
                password = cvhelper.format_string(self._commcell, encrypted_pass).split("_cv")[1]
            if not dbserver:
                db_instance = self.commserve_instance if not self._commcell.is_linux_commserv else ''
                dbserver = self._commcell.commserv_hostname + db_instance
            if not dbname:
                dbname = "CommServ"
            if not driver:
                driver = defines.driver if cs_machine_obj.os_info.lower() == 'windows' else defines.unix_driver
            counter = 1
            while counter < retryattempts:
                try:
                    self.mssql = MSSQL(dbserver, user_name, password, dbname, driver)
                    break
                except Exception as e:
                    self._log.error("Failed to open connection with dbserver:" + dbserver)
                    self._log.info("Exception: " + str(e))
                    self.sleep_time(60)
                    counter = counter+1

        if not self.mssql:
            raise Exception(f'Unable to connect with CommServ database [{dbserver}] [{dbname}]')

        if log_query:
            self._log.info("Executing DB query: \n %s", str(query))

        return self.mssql.execute(query)   

    def update_commserve_db_via_cre(self, sql, port=80, protocol='http'):
        """Updates table in commserve db using custom reports engine api

            Args:
                sql     (str)  - The SQL Query to execute

                port    (int)  - port used by webconsole tomcat

                protocol  (str) - http or https

            Raises:
                Exception:
                    - if failed to update data in DB
        """
        cre = CustomReportsEngineAPI(machine=self._commcell.webconsole_hostname,
                                     authtoken=self._commcell.auth_token,
                                     port=port,
                                     protocol=protocol)

        return cre.execute_sql(sql=sql)

    def get_paccess_passwd(self):
        """Gets pAccess password from  Regsitry

            Return:
                    password for pAccess
        """
        cs_machine_obj = Machine(self._commcell.commserv_client)
        encrypted_pass = cs_machine_obj.get_registry_value(r"Database", "pAccess")
        password = cvhelper.format_string(self._commcell, encrypted_pass).split("_cv")[1]

        return password

    def remove_directory(self, targethost, directory):
        '''Removes a directory on a commcell client

            Args:
                targethost    (str)/(Machine object)
                                       -- Machine on which the directory has to be
                                            removed

                directory     (str)    -- Directory that needs to be removed

            Returns:
                None

            Raises:
                Exception:
                    if failed to remove directory
        '''
        try:
            machine = self.get_machine_object(targethost)
            machine_name = machine.machine_name

            if not machine.remove_directory(directory):
                raise Exception("Failed to delete directory [{0}] on [{1}]".format(directory, machine_name))

        except Exception as exp:
            raise Exception("\n {0}: [{1}]".format(inspect.stack()[0][3], str(exp)))

    def create_directory(self, targethost, directory=None, dirstring="TestData"):
        '''Creates a directory on a commcell client

            Args:
                targethost    (str)/(Machine object)
                                       -- Machine on which the directory has to be created

                directory     (str)    -- Directory that needs to be created

                dirstring     (str)    -- In case directory is not provided, a new directory will
                                            be created with this string as sub-directory under
                                            parent directory.

            Returns:
                directory that was created

            Raises:
                Exception:
                    if failed to create directory
        '''
        try:
            machine = self.get_machine_object(targethost)
            _name = machine.machine_name

            if directory is None:
                topdir = self.get_drive(machine) + constants.TESTDATA_DIR_NAME
                directory = machine.os_sep.join([topdir, dirstring, OptionsSelector.get_custom_str('Auto', 'subdir')])

            if machine.check_directory_exists(directory):
                self._log.info("Directory [{0}] exists on [{1}]".format(directory, _name))
                return directory

            self._log.info("Creating directory [{0}] on [{1}]".format(directory, _name))
            _ = machine.create_directory(directory)

            return directory

        except Exception as exp:
            raise Exception("\n {0}: [{1}]".format(inspect.stack()[0][3], str(exp)))

    def create_test_data(self,
                         client,
                         file_path=None,
                         levels=constants.DEFAULT_DIR_LEVEL,
                         file_size=constants.DEFAULT_FILE_SIZE,
                         **kwargs):
        ''' Creates test data on the client machine provided

        Args:
            client (str)/(Machine object)
                                --  Client name on which data needs to be created

            data_path  (str)    --  Path where test data is to be generated
                                    Default: Will be defined if not set

            level (int)         --  Depth of folders under test data

            size (int)          --  size of each test file to be generated in KB

            kwargs (dict)                    -- dictionary of optional arguments

            Available kwargs Options:

                options             (str)   --  to specify any other additional parameters
                        default: ""

        Returns:
            Parent directory path to test data directory path

        Raises:
            Exception:
                When failed to create testdata
        '''
        try:
            machine = self.get_machine_object(client)
            machine_name = machine.machine_name

            options = kwargs.get('options', "")

            if file_path is None:
                file_path = self.create_directory(machine)

            self._log.info("Creating test data on client {0} with level [{1}], file size [{2}]"
                           "KB, path [{3}] and options [{4}]".format(
                               machine_name, str(levels), str(file_size), file_path, options))

            machine.generate_test_data(file_path=file_path, levels=levels, file_size=file_size, options=options)
            return file_path

        except Exception as exp:
            raise Exception("\n {0}: [{1}]".format(inspect.stack()[0][3], str(exp)))

    def create_uncompressable_data(self, client, path, size, num_of_folders=1, username=None,
                                   password=None, delete_existing=False, file_size=0, prefix='', suffix=''):
        """
        Creates uncompressable data on the client machine provided

        Args:

            client  -- (str/[Machine/Client] Object) -- Client on which data needs to be created

            path    -- (str)                -- Path where data is to be created

            size    -- (float)              -- Data in GB to be created for each folder
                                               (restrict to one decimal point)

            num_of_folders -- (int)         -- Number of folders to generate, each with given size

            username -- (str)               -- Username to access client, Default: None

            password -- (str)               -- Password to access client, Default: None

            delete_existing -- (bool)       -- Delete the existing directory and create afresh
                                               (Default: False)

            file_size   -- (int)            -- Size of Files to be generated in KB, Default: 0(Random Size)

            prefix      -- (str)            -- Prefix of name for the files generated

            suffix      -- (str)            -- Suffix of name for the files generated
        Returns:
              (boolean)
        """
        size = int(size * 1024)
        size_d = str(size) + "MB"
        client_machine = self.get_machine_object(client, username=username, password=password)
        data = dict()

        data['prefix'] = prefix
        data['suffix'] = suffix
        if client_machine.os_info == 'UNIX':
            script_path = constants.CREATE_UNCOMPRESSABLE_DATA_UNIX
            data['totalsize'] = size
            data['filesize'] = file_size
        elif client_machine.os_info == 'WINDOWS':
            script_path = constants.CREATE_UNCOMPRESSABLE_DATA_WINDOWS
            data['totalsize'] = size_d
            data['filesize'] = str(file_size) + "KB"
            if not suffix:
                data['suffix'] = '.bin'  # setting default suffix to .bin to not change older behavior
        else:
            raise Exception("We dont have support for this OS Flavour yet")

        def generate_data():
            # data['directory']->directory where script generates data, data['size']->size of data
            output = client_machine.execute_script(script_path, data)
            if client_machine.os_info == 'UNIX' and output.exception_code:
                raise Exception(output.exception_code, output.exception_message)
            elif client_machine.os_info != 'UNIX' and output.exception_message:
                raise Exception(output.exception_code, output.exception_message)
            elif client_machine.os_info != 'UNIX' and output.exception:
                raise Exception(output.exception_code, output.exception)

        if delete_existing:
            if client_machine.check_directory_exists(path):
                client_machine.remove_directory(path)

        self._log.info("creating uncompressable data at: [%s]", path)
        if not client_machine.check_directory_exists(path):
            client_machine.create_directory(path)
        if num_of_folders == 0:
            data['directory'] = path
            generate_data()
        for _ in range(num_of_folders):
            data['directory'] = client_machine.join_path(path, self.get_custom_str())
            client_machine.create_directory(data['directory'])
            generate_data()
        return True

    def delete_nth_files_in_directory(self, client, path, selector=2, operation='delete', username=None, password=None):
        """Deletes files in a directory in specified pattern

        Args:

            client      (str/[Machine/Client] Object) -- Client on which data needs to be created

            path        (str)       -- Directory path where data is to be deleted

            selector    (int)       -- integer to denote which file needs to be selected

            operation   (str)       -- (delete/keep)
                                       (delete every nth file selected/keep every nth file selected and delete others)

            username    (str)       -- Username to access client, Default: None

            password    (str)       -- Password to access client, Default: None
        Returns:
              (boolean)
        """
        client_machine = self.get_machine_object(client, username=username, password=password)
        if not client_machine.check_directory_exists(path):
            raise Exception("Target directory doesn't exist")

        data = dict()
        data['directory'] = client_machine.join_path(path, '')
        if operation == 'delete':
            self._log.info("deleting every (%d file) at [%s] in alphanumeric order", selector, path)
            data['deletefactor'] = selector
            data['keepfactor'] = 0
        elif operation == 'keep':
            self._log.info("deleting all files at [%s] excluding every (%d file) in alphanumeric order", path, selector)
            data['deletefactor'] = 0
            data['keepfactor'] = selector

        if client_machine.os_info.lower() == 'unix':
            script_path = constants.DELETE_NTH_FILES_UNIX
        elif client_machine.os_info.lower() == 'windows':
            script_path = constants.DELETE_NTH_FILES_WINDOWS

        output = client_machine.execute_script(script_path, data)
        if client_machine.os_info == 'UNIX' and output.exception_code:
            raise Exception(output.exception_code, output.exception_message)
        elif client_machine.os_info != 'UNIX' and output.exception_message:
            raise Exception(output.exception_code, output.exception_message)
        elif client_machine.os_info != 'UNIX' and output.exception:
            raise Exception(output.exception_code, output.exception)
        return True

    def is_regkey_set(self, client_obj, regkey, keyname, retry_time=10, time_limit=10, hardcheck=True, keyvalue=None):
        """ Check if a given registry key is set or not

            Args:

                client_obj (obj)           -- Client object

                regkey (str)               -- Registry key path

                keyname (str)              -- Registry key name

                retry_time    (int)        -- Interval (in seconds), checked in a loop. Default = 10

                time_limit        (int)    -- Time limit to check for. Default (in minutes) = 10

                hardcheck         (bool)   -- If True, function will exception out in case regkey value not set
                                              If False, function will return with non-truthy value
                                              Default: True

            Returns:
                True/False        (bool)   -- In case reg key value not set/notset

            Raises:
                Exception if :

                    - failed during execution of module
                    - if reg key was not set in time

        """
        try:
            regkey_value = self.check_reg_key(client_obj, regkey, keyname, keyvalue, False)

            time_limit = time.time() + time_limit * 60
            while True:
                if (regkey_value) or (time.time() >= time_limit):
                    break
                else:
                    self._log.info(
                        "Sleep for %s seconds. Registry %s->%s value not as expected.", str(retry_time), regkey, keyname
                    )
                    time.sleep(retry_time)
                    regkey_value = self.check_reg_key(client_obj, regkey, keyname, keyvalue, False)

            if not regkey_value:
                if not hardcheck:
                    return False

                raise Exception("Registry %s->%s not set.", regkey, keyname)

            return True

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def update_reg_key(self, client, reg_key, key_name):
        """ Updates the registry key value for given registry key on a client

        Args:
            client    (str)/(Machine object)   --  Client name or Machine class object.

            reg_key    (str)                   --  Registry key path. e.g -> 'LaptopCache'

            key_name   (str)                   --  Reg key name to get the value. e.g -> 'StartNewJob'

        Raises:
            Exception:

                - if module failed to execute due to some error
        """
        try:
            # read the registry to check the status
            machine = self.get_machine_object(client)

            self._log.info("Updating [{0}] reg key value [{1}] on [{2}]".format(reg_key, key_name, machine))

            if machine.check_registry_exists(reg_key, key_name):
                machine.update_registry(reg_key, key_name, '1')
                self._log.info("{0} is updated successfully with value : [{1}]".format(key_name, '1'))
            else:
                raise Exception("{0} does not exist in registry".format(key_name))

        except Exception as excp:
            raise Exception("\n Updating [{0}] failed {1} {2}".format(key_name, inspect.stack()[0][3], str(excp)))

    def check_reg_key(self, client, reg_key, flag, expected_value=None, fail=True):
        """ Check/Gets the registry key value for given registry key on a client

            Args:
                clients    (str)/(Machine object)
                                           -- Client name

                reg_key    (str)           -- Registry key path. e.g -> 'Session'

                flag       (str)           -- Reg key name to check the value.
                                                e.g -> 'nChatterFlag'

                expected_value
                           (str/int)       -- Expected value if provided will be validated and
                                                module will return the key value or False based
                                                on the 'fail' argument.

                fail       (bool)          -- If true, will throw exception in case of failed
                                                validation.
                                              If false, will return False if validation fails

            Returns:
                (bool)                     -- Based on validation failed (False)

                (str/int)                  -- If validation succeeds or reg key value exists in
                                                registry, then return value of registry.

            Raises:
                Exception:
                    - if validation failed (fail = True)

                    - if module failed to execute due to some error
        """
        try:
            log = self._log
            machine = self.get_machine_object(client)

            if machine.check_registry_exists(reg_key, flag):
                value = machine.get_registry_value(reg_key, flag)

                if expected_value is not None:
                    log.info("{0}->{1} reg key value: {2}, expected: {3}".format(reg_key, flag, value, expected_value))
                    if str(value) != str(expected_value):
                        raise Exception("[{0}] value not as expected in registry".format(flag))
                    return True

                log.info("{0}->{1} value: [{2}]".format(reg_key, flag, value))
                return value
            else:
                if expected_value is not None:
                    raise Exception("{0} does not exist in registry".format(flag))
                log.error("{0}->{1} reg key does not exist".format(reg_key, flag))

        except Exception as excp:
            if not fail:
                return False

            raise Exception(
                "\n {0} validation failed {1} {2}".format(flag, inspect.stack()[0][3], str(excp))
            )

    def get_machine_object(self, machine, username=None, password=None, retry_interval=None, time_limit=None):
        """ Creates/Returns machine object based on user defined input of client name as string
            or machine object.

            Args:
                machine
                (str/[Machine/Windows/Unix object]/Client Object) -- Client string or object

                username  (str)                                   -- Username to access client
                                                                        Default: None

                password  (str)                                   -- Password to access client
                                                                        Default: None

                retry_interval    (int)                           -- Interval (in seconds), checked in a loop.
                                                                        Default = 2

                time_limit        (int)                           -- Time limit to check for.
                                                                        Default (in minutes) = 5

            Returns:

                Machine object

            Raises:
                Exception:

                    - if failed to get the machine object
        """
        try:
            if isinstance(machine, Machine):
                return machine
            retry_interval = 2 if not retry_interval else retry_interval
            time_limit = 5 if not time_limit else time_limit

            self._log.info("""Creating Machine class instance for machine [{0}] with user [{1}], password [{2}]"""
                           .format(machine, username, password))

            if not isinstance(machine, str) and not isinstance(machine, Client):
                raise Exception("Wrong input type for <machine> to get_machine_object.")

            time_limit = time.time() + time_limit * 60
            while True:
                try:
                    if time.time() >= time_limit:
                        self._log.error("Timed out after [{0}min]".format(time_limit))
                        break

                    if username is not None:
                        machine_obj = Machine(machine, username=username, password=password)
                    else:
                        machine_obj = Machine(machine, self._commcell)

                    return machine_obj

                except Exception as excp:
                    self._log.info("Failed to create machine object with exception {0}".format(str(excp)))
                    self._log.info("Waiting for [{0}] seconds before retry".format(retry_interval))
                    time.sleep(retry_interval)

            raise Exception("Failed to create machine object")

        except Exception as excp:
            raise Exception("\n {0}: [{1}]".format(inspect.stack()[0][3], str(excp)))

    def get_gxglobalparam_val(self, name):
        """Fetches value for the given GxGlobalParam property name from CS DB

            Args:

                name    (str)    -- Name of the settings to fetch

            Returns:
                (str)    -- Value of the Gxglobal param name

            Raises:
                Exception:
                    - If failed to get the property value
        """
        try:
            self.arg_map = {'value_from_name': ['name']}

            rs_list = self._get_resultset('gxglobalparam', 'value_from_name', name=name)
            value = str(rs_list[0][0])

            self._log.info("GxGlobalParam value = [{0}] for name [{1}]".format(value, name))

            return value

        except Exception as excp:
            self._log.error("Failed! to fetch the Gxglobal param value for [{0}]".format(name))
            raise Exception("\n {0}: [{1}]".format(inspect.stack()[0][3], str(excp)))

    def is_client_in_client_group(self, client, client_groups):
        """ Validate if the client is associated to any of the client groups in the given list

            Args:

                client (str)            - Client name

                client_groups (list)    - Client group list

                Returns:
                    False : If client is not associated to any one of the client groups in the list

                    True: If client is associated to all client groups in the list

                Raises:
                    Exception:
                        - In  case of any error
        """
        try:
            _flag = True  # Should be assumed true for all clients. If any validation fail return False

            # Validate client is part of client group list provided in the args
            for _source in client_groups:
                cg = self._commcell.client_groups
                cg.refresh()
                all_clients = map(lambda x:x.lower(), cg.get(_source).associated_clients)
                result = client.lower() in list(all_clients)
                if result:
                    self._log.info("Client [{0}] is associated to client group: [{1}]".format(client, _source))
                else:
                    self._log.error("Client [{0}] is not associated with client group [{1}]".format(client, _source))
                    _flag = False

            return _flag

        except Exception as excp:
            raise Exception("\n [{0}]: [{1}]".format(inspect.stack()[0][3], str(excp)))

    def delete_client(self, client, commcell_name=None, disable_delete_auth_workflow=False):
        """ Delete a client on commcell

            Args:

                client (str)            - Client name

                Raises:
                    Exception:
                        - In  case of any failure
        """
        try:
            if commcell_name:
                self._commcell=commcell_name

            if (disable_delete_auth_workflow and
                    self._commcell.workflows.has_workflow("DeleteClientAuthorization")):
                self._log.info("DeleteClientAuthorization is present in the commcell, "
                               "updating the flags in db")
                self.update_commserve_db("update WF_Definition set Restricted=0,"
                                                  "flags=6 where name = 'DeleteClientAuthorization'")
                self._log.info("deleting DeleteClientAuthorization workflow from commcell")
                self._commcell.workflows.delete_workflow("DeleteClientAuthorization")
            
            self._commcell.clients.refresh()
            if self._commcell.clients.has_client(client):
                # Delete any pending jobs for the client before deleting the client.
                JobManager(commcell=self._commcell).kill_active_jobs(client)
                self._log.info("Deleting client {0}".format(client))
                self._commcell.clients.delete(client)

        except Exception as excp:
            raise Exception("\n [{0}]: [{1}]".format(inspect.stack()[0][3], str(excp)))

    def wait_until_client_ready(self, client, retry_interval=5, time_limit=5, hardcheck=True):
        """ Waits for client to be ready until a given interval of time.

            Args:
                client            (str)    -- Client name

                retry_interval    (int)    -- Interval (in seconds), checked in a loop. Default = 2

                time_limit        (int)    -- Time limit to check for. Default (in minutes) = 5

                hardcheck         (bool)   -- If True, function will exception out in case client is not ready.
                                              If False, function will return with non-truthy value

            Returns:
                True/False        (bool)   -- In case client reaches/not reaches client ready state

            Raises:
                Exception if :

                    - failed during execution of module
                    - client is not ready

        """
        try:
            self._log.info("Waiting for check readiness to succeed for client [{0}]".format(client))
            client_object = self._commcell.clients.get(client)

            time_limit = time.time() + time_limit * 60
            while True:
                # Sometimes the client check readiness response is not success and exceptions out of an attempt out of
                # multiple attempts in a loop
                # Do not want to quit and fail testcase because of the API response failure.
                try:
                    client_is_ready = client_object.is_ready
                except Exception as excp:
                    self._log.error("Exception during client check readiness: [{0}]".format(excp))
                    client_is_ready = False

                if client_is_ready or time.time() >= time_limit:
                    break
                else:
                    self._log.info("Waiting for [{0}] seconds. Client not ready.".format(retry_interval))
                    time.sleep(retry_interval)

            if not client_is_ready:
                if not hardcheck:
                    return False

                raise Exception("Client [{0}] is not ready.".format(client))

            self._log.info("Client [{0}] is ready.".format(client))
            return True

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def _get_resultset(self, entity, query_type, validate=True, **kwargs):
        """ Gets the result set from DB for given query and arguments

            Args:

                entity (str)            - Entity for which to execute the query. Entity is mapped
                                            to database_constants enum classes.

                query_type (str)        - Type of query to execute as defined in
                                            database_constants for a given entity class

                validate (bool)         - Validate if the resultset is not empty

                kwargs (dict)           - Dictionary containing the key value pair for the
                                            arguments passed to the modules

                Returns:
                    - (tuple) -- tuple with (<first column list>, Complete resultset)

                Raises:
                Exception:
                    - When arguments list required is not passed to execute a given query

                    - When failed to get the resultset from the Database
        """
        try:
            module = inspect.stack()[0][3]
            exception_ = "Failed to get [{0}] details with error".format(entity)
            argerror_ = "Invalid argument in [{0}] for query type {1}".format(module, query_type)

            class_name = database_constants.CLASS_MAP[entity]
            class_obj = getattr(database_constants, class_name)
            dbquery = getattr(class_obj, query_type.upper()).value
            args = []

            if self.arg_map:
                for arg in self.arg_map.get(query_type.lower(), []):
                    assert arg in kwargs, "{0}= argument required".format(arg)
                    args.append(kwargs[arg])

            dbquery = dbquery.format(*args) if args else dbquery
            rs_tuple = self.exec_commserv_query(dbquery)

            if validate:
                assert rs_tuple[0] and rs_tuple, "DB resultset is empty."

            return rs_tuple

        except AssertionError as aserr:
            self._log.error("{0}:[{1}]".format(argerror_, dbquery))
            raise Exception("\n {0} {1}".format(exception_, str(aserr)))

        except Exception as excp:
            raise Exception("\n {0} {1}".format(exception_, str(excp)))

    def validate_logs(self, client_machine, validatelog, linetovalidate=None):
        """
        Method to validate log with required log line

           Args:

                client_machine   (obj)   -- machine object

                validatelog     (str)    -- Log file name which need to be validated

                linetovalidate   (str)   -- line to be validated in log file

            Returns:
                True if it found the line to validate in waiting time


            Raises:
                Exception:

                    if there is no log file found
                    if there is no log line found in waiting time

        """
        try:
            waiting_time = 60 * 2
            validateunclog = client_machine.get_unc_path(validatelog)
            if client_machine.check_file_exists(validatelog):
                if linetovalidate is not None:
                    for line in list(open(validateunclog)):
                        if linetovalidate in line:
                            return True
                        self.sleep_time(5, "Waiting for cvd log to get the [{0}]".format(linetovalidate))
                    return False

                for _count in range(waiting_time):
                    content = client_machine.read_file(validatelog)
                    if (len(content.split("\n"))) > 2:
                        return True
                    self.sleep_time(1, "Waiting for cvd log to get the [{0}]".format(linetovalidate))
                return False

            raise Exception("no log line found in cvd log")
        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def delete_credentials(self, machine, hostname=None):
        """Deletes saved client credentials on the controller for the given client.

            machine    (str/object):    Machine name or object of Machine class
                                        This machine object should have enough privledges to execute commands in
                                        administrative mode (e.g query session should return all users logged in)

            hostname   (str):           Machine's hostname
                                            Default: None. Will get from Machine object

            Returns: None

            Raises:
                Exception - If failed to delete existing credentials
        """
        try:
            controller = Machine()
            machine_obj = self.get_machine_object(machine)

            # Currently this module is specific to Windows only. For other platforms if the user session is
            # not active return False.
            if not machine_obj.os_info.lower() == "windows":
                return False

            if not hostname:
                hostname = machine.machine_name
            delete_creds = ' '.join(["cmdkey", "/delete", hostname])
            self._log.info("Deleting existing credentials for client: {0}".format(delete_creds))
            controller.execute_command(delete_creds)

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def start_rdp_session(self, machine, user, password, hostname=None):
        """Creates a remote desktop connection with the client.

            machine    (str/object):    Machine name or object of Machine class
                                        This machine object should have enough privledges to execute commands in
                                        administrative mode (e.g query session should return all users logged in)

            hostname   (str):           Machine's hostname
                                            Default: None. Will get from Machine object

            user       (str):           Domain / Local User for which session has to be created

            password   (str):           Password for domain/local user

            Returns: (bool)/(handler object)
                True if active user session already exists for the client
                False if platform is not Windows and session does not exist on the machine
                Session Handler object for the opened RDP session

            Raises:
                Exception - If remote login is not successful
        """
        try:
            controller = Machine()
            machine_obj = self.get_machine_object(machine)

            # Check if RDP session already exists for the user on the client:
            if machine_obj.has_active_session(user):
                return True

            # Currently this module is specific to Windows only. For other platforms if the user session is
            # not active return False.
            if not machine_obj.os_info.lower() == "windows":
                return False

            if not hostname:
                hostname = machine.machine_name
            self.delete_credentials(machine_obj)
            set_password = ' '.join(["cmdkey", "/generic:" + hostname, "/user:" + user, "/pass:" + password])
            rdp_session = "mstsc /v:" + hostname
            self._log.info("Setting credentials with command: {0}".format(set_password))
            controller.execute_command(set_password)
            self._log.info("Starting RDP session on client [{0}] with user [{1}]".format(hostname, user))
            self._log.info("Executing command: {0}".format(rdp_session))
            rdp_session_handler = subprocess.Popen(rdp_session, shell=True)
            self.sleep_time(7)

            counter = 0
            while True:
                if machine_obj.has_active_session(user):
                    break
                if counter > 50:
                    raise Exception("Failed to open RDP session for client [{0}] with user [{1}]".format(machine, user))
                self.sleep_time(
                    15, "Check if RDP session was opened for user [{0}] on client [{1}]".format(user, hostname)
                )
                counter += 1

            self.delete_credentials(machine_obj)
            return rdp_session_handler

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def validate_restartservices(self, client, timeout=120):
        """Validates if restart services is successful on client
        
        client    (object):    Client object on which to validate restart services
        timeout   (int):       Time in seconds to wait
        """

        start_time = time.time()
        timeout = timeout * 2
        self._log.info("wait for services to go down")
        while time.time() - start_time < timeout:
            try:
                if not client.is_ready:
                    self._log.info("Services went down in restart services activity")
                    break
            except Exception:
                raise Exception("Services didnt went down")

        self.sleep_time(5, "Wait for 5 seconds to check for services to come up")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                if client.is_ready:
                    self._log.info("Services came up in restart services activity")
                    break
            except Exception:
                raise Exception("Services didnt come up")

    def convert_size(self, size_bytes):
        """converts bytes to human readable memory unit string

            Args:

                size_bytes      (int)       --  Size in bytes

            returns:

                str --  Readable size format
        """
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return "%s %s" % (s, size_name[i])

    def convert_no(self, number):
        """converts given no to human readable number unit string

                   Args:

                       number      (int)       --  input no

                   returns:

                       str --  Human Readable number format
        """
        # Define the suffixes for each power of 1000
        suffixes = [' ', 'K', 'M', 'B', 'T', 'P', 'E', 'Z', 'Y']
        # Determine the appropriate suffix for the given number
        suffix_index = 0
        while number >= 1000 and suffix_index < len(suffixes) - 1:
            number /= 1000.0
            suffix_index += 1
        # Format the number with the appropriate suffix
        return '{:.1f}{}'.format(number, suffixes[suffix_index])


class CVEntities(object):
    ''' Class to create/delete various commcell objects '''

    def __init__(self, init_object):
        ''' Initialize instance of CVEntities class

        Args:
        init_object : Should be either the commcell or the testcase object'''

        # Pre-initialized attributes applicable for all instances of the class
        self._init_object = init_object
        if isinstance(init_object, Commcell):
            self._commcell = init_object
        else:
            self._testcase = init_object
            self._commcell = self._testcase.commcell

        self.log = logger.get_log()
        self._utility = OptionsSelector(self._commcell)

        # Instance attributes
        self._entity_config = {}
        ''' Based on type of entity_config sent to create/delete modules, this
                dictionary will be constructed with entity and it's properties
                and will be fed to the private <entity_name>_create() modules
         '''

        self.entity_props = {}
        '''
            Contains dependent objects and properties for entities created with
            create module.
        '''

        self._created_entities = {}
        '''
            Contains details of entities already created as part of create() modules.
            This is dynamic and it's life is limited to the create/delete calls.
            Once all required objects are created, this is reset with refresh()
            This is utilized to access properties of created entities by other
            dependent entities during runtime of create(), delete() modules
        '''

        self._entity_object_map = {}
        '''
            _entity_object_map will be updated with entity properties whenever a
                call is made to the create() module.

            This dictionary mapping will be used by cleanup module to delete the
                entities in the map.

            From the testcase 'finally:' block user just needs to call
                entities.cleanup() to delete all the entities created by testcase.
                where entities is an instance of CVEntities class.

            Sample dictionary mapping:
            {
                'backupset'        :[{ backupset1 object properties },
                                     { backupset2 object properties } ...],
                'subclient'        :[{ subclient1 object properties },
                                     { subclient2 object properties } ...],
                'disklibrary'      :[{ disklibrary1 object properties },
                                     { disklibrary2 object properties } ...],
                'storagepolicy'    :[{ storagepolicy1 object properties },
                                     { storagepolicy2 object properties } ...],
            }
        '''

    def __repr__(self):
        """Representation string for the instance of the CVEntities class."""
        return "CVEntities class instance"

    def __del__(self):
        """Destroy the objects created in the class """
        self._utility = None

    def create(self, input_entities=None):
        '''Method to create commcell entities

        Note: All possible usages and examples of create() module are provided in detail
                in testcase 52713.

        definitions:
        -----------
            entity     :    backupset, subclient, library, storagepolicy, clientgroup
                                etc. to be created on Commcell.

            target     :    where the entity will be created

            property   :    entity name, client, agent etc..

            force      :    Set to True:
                            ------------
                            The existing entity with same name on commcell for a
                            given target will be deleted and the entity will be
                            created again.

                            Be careful in using this option for entities which
                            already exists, as an attempt will be made to delete them
                            It will remove all data associated with the entity.

                             Set to False:
                             -------------
                             The existing entity (if it exists) shall not be deleted
                             and will return existing entities properties.

                             If the entity did not exist, a new entity will be
                             created on target and will also be removed as part of
                             cleanup()

        Args:
        -----
            entity_config  (dict or list or string)

                -- Could be a dictionary containing entity and properties of the
                    entity which needs to be created

                -- Could be a list of entities to create

                -- Can be a single entity (string) to create

            Common target properties can be defined as part of 'target' key
            Common target properties can be
            'target':
            {
                'client': "<client name>",
                'agent': "<agent name>",
                'instance': "<instance name>",
                'storagepolicy': "<storage policy>",
                'mediaagent': "<media agent>",
                'library': "<library name>",
                'force': False
            },

            Common properties that could be relevant to disklibrary:
                mediaagent
                force  (Default: True)

            Common properties that could be relevant to storagepolicy:
                mediaagent
                library
                force  (Default: True)

            Common properties that could be relevant to backupset:
                client
                agent
                instance
                force  (Default: True)

            Common properties that could be relevant to subclient:
                client
                agent
                instance
                force  (Default: True)

            Common properties that could be relevant to clientgroup:
                force  (Default: True)

            Defaults will be used in case the entity properties are not defined in
            the input configuration to create() module

            Default client = TestCase initialized client
            Default storagepolicy = TestCase initialized subclient's storage policy
            Default mediaagent = TestCase initialized subclient's media agent
            Default library = TestCase initialized subclient's library

            If all entities have to be created with these target properties, then
                they can be defined in 'target' key as values.

            In case some individual entities need to be created on different target
                properties then can be defined as part of that entity's properties.

            Entity properties shall always override the target properties.

            Names of the entities can be skipped too. If name is not provided then
                entity with a unique name would be created.

        Returns:
        -------
            A dictionary with key(s) as entity type and value(s) as entity properties
            Sample e.g:

            {
                'backupset':
                {
                    'agent': "File System" Agent instance for Client: "client1",
                    'agent_name': 'file system',
                    'object': Backupset class instance for Backupset:
                                    "bkp01" for Instance:
                                    "defaultinstancename" of Agent: "file system",
                    'client': Client class instance for Client: "client1",
                    'client_name': 'client1',
                    'force': True,
                    'id': '4004',
                    'instance': Instance class instance for Instance:
                                    "DefaultInstanceName" of Agent: "file system",
                    'instance_name': 'defaultinstancename',
                    'name': 'bkp01',
                    'target': 'client1->file system->defaultinstancename'
                 },
                'disklibrary':
                {
                    'object': DiskLibrary class instance for library:
                                    "lib01" of Commcell:
                                    "csclient",
                    'force': True,
                    'id': '1484',
                    'mediaagent': MediaAgent class instance for MA:
                                    "csclient", of Commcell: "csclient",
                    'mediaagent_name': 'csclient',
                    'mount_path': 'C:\\DiskLibrary',
                    'name': 'lib01',
                    'password': '',
                    'target': 'csclient->C:\\DiskLibrary',
                    'username': ''
                },
                'storagepolicy':
                {
                    'dedup_path': None,
                    'force': True,
                    'id': '676',
                    'incremental_sp': None,
                    'library': DiskLibrary class instance for library:
                                    "lib01" of Commcell: "csclient",
                    'library_name': 'lib01',
                    'mediaagent': MediaAgent class instance for MA:
                                    "csclient", of Commcell: "csclient",
                    'mediaagent_name': 'csclient',
                    'name': 'sp01',
                    'retention_period': 5,
                    'object': Storage Policy class instance for Storage Policy
                                        : "sp01",
                    'target': 'csclient->lib01'
                },
                'subclient':
                {
                    'agent': "File System" Agent instance for Client: "client1",
                    'agent_name': 'file system',
                    'backupset': Backupset class instance for Backupset:
                                    "bkp01" for Instance:
                                    "defaultinstancename" of Agent: "file system",
                    'backupset_name': 'bkp01',
                    'client': Client class instance for Client: "client1",
                    'client_name': 'client1',
                    'content': None,
                    'force': True,
                    'id': '5931',
                    'instance': Instance class instance for Instance:
                                "DefaultInstanceName" of Agent: "file system",
                    'instance_name': 'defaultinstancename',
                    'name': 'sc01',
                    'storagepolicy_name': 'sp01',
                    'object': Subclient class instance for Subclient:
                                "sc01" of Backupset: "bkp01",
                    'target': 'client1->file system->defaultinstancename->bkp01'
                },
                'clientgroup':
                {
                    'object': ClientGroup class instance for ClientGroup: "cg3",
                    'clients': ['client1', 'client2', 'client3'],
                    'default_client': True,
                    'description': '',
                    'enable_backup': True,
                    'enable_data_aging': True,
                    'enable_restore': True,
                    'force': True,
                    'id': '1167',
                    'name': 'cg3',
                    'target': []
                }
            }

        Raises:
                Exception:

                    If the entity_config is not a supported type

                    If the entity_config keys are not a part of supported entity types

                    Post creation configuration failed
        '''

        try:
            log = self.log
            self.refresh()

            log.info("Create entities configuration: \n {}".format(str(input_entities)))

            # Create a dictionary mapping based on input type to the module
            if isinstance(input_entities, type(None)):
                self._entity_config = constants.ORDERED_ENTITIES_DICT
            elif isinstance(input_entities, list):
                self._entity_config = {item: {} for item in input_entities}
            elif isinstance(input_entities, dict):
                if not input_entities:
                    self._entity_config = constants.ORDERED_ENTITIES_DICT
                else:
                    self._entity_config = copy.deepcopy(OptionsSelector.get_var(input_entities, dict()))
            elif isinstance(input_entities, str):
                self._entity_config[input_entities] = {}

            for key in self._entity_config:
                if key not in constants.ORDERED_ENTITIES and key != 'target':
                    raise Exception("Wrong input {0} configured. Key(s) can be "
                                    " {1}".format(key, constants.ORDERED_ENTITIES))

            # Loop through each entity and create
            for entity in constants.ORDERED_ENTITIES:
                if entity not in self._entity_config:
                    continue

                log.info("Entity = [{0}]".format(entity))

                # Call the entity class object and work in it's context
                entity_class = "_%s" % entity.capitalize()
                entity_obj = getattr(sys.modules[__name__], entity_class)(self._init_object)
                props = self._get_entity_objects(entity_obj.associated_entities, entity)
                setattr(entity_obj, 'props', props)
                target = entity_obj.target()
                (assocobj, has_obj) = entity_obj.object()
                name = props['name']
                args = [entity, name, target]
                create = True

                if has_obj:
                    log.info("{0} [{1}] already exists for {2}".format(*args))

                    if props['force']:
                        log.info("Deleting {0} [{1}] for {2}".format(*args))
                        obj = assocobj.get(name)
                        id_ = getattr(obj, entity_obj.entity_id)
                        assocobj.delete(name)
                        self._purge_entities(entity, {'name': name, 'id': id_})
                    else:
                        obj = assocobj.get(name)
                        create = False
                        _ = entity_obj.existing_config()
                        props = entity_obj.props
                        target = props.get('target', '')

                if create:
                    log.info("Creating {0} [{1}] for {2}".format(*args))
                    if props.get('istape'):
                        kwargs = entity_obj.add_tape_args()
                        obj = assocobj.add_tape_sp(**kwargs)
                        # For tape storage policy the object is not returned from sdk instead the sdk response text
                        # is returned or the policy name. Will fix this with any change from SDK side later.
                        obj = assocobj.get(name)
                    else:
                        kwargs = entity_obj.add_args()
                        obj = assocobj.add(**kwargs)

                try:
                    props = entity_obj.props
                    props['id'] = getattr(obj, entity_obj.entity_id)
                    props['object'] = obj
                    props['target'] = target
                    setattr(entity_obj, 'props', props)
                    entity_obj.post_create(obj)
                    (_, has_obj) = entity_obj.object()
                    assert has_obj, "Validation failed for {0} [{1}]".format(entity, name)

                except Exception:
                    self.log.error("Post creation configuration failed")
                    raise
                finally:
                    props = entity_obj.props

                    # Only update the cleanup entity object if the entity has been created
                    # by create() module. Do not want to remove pre-existing entities.
                    if create:
                        obj_list = self._entity_object_map.get(entity, [])
                        obj_list.append(props)
                        self._entity_object_map[entity] = obj_list

                    self.log.info("{0} [{1}] properties \n {2}".format(entity.capitalize(), props['name'], str(props)))
                    self._created_entities[entity] = dict(props)
                    self.entity_props[entity] = props

            return {entity: properties for entity, properties in self.entity_props.items()}

        except Exception as excp:
            raise Exception("\n {0}: [{1}]".format(inspect.stack()[0][3], str(excp)))
        finally:
            props = None

    @argtypes(dict)
    def delete(self, input_entities=None):
        '''Method to delete commcell entities

        Args:
            entity_config (dict)   -- Dictionary containing the entity(s) as key,
                                        and value(s) as a dictionary of the entity
                                        properties.
            Example Usage:
                entities = CVEntities()
                all_inputs = entities.create()
                self._entities.delete(all_inputs)

        Returns:
            None

        Raises Exception:
            - If failed to delete any entity
        '''

        try:
            log = self.log
            self.refresh()
            log.info("Deleting following entities: \n {}".format(str(input_entities)))
            self._entity_config = input_entities

            for entity in constants.DELETE_ENTITIES_ORDER:

                if entity not in self._entity_config:
                    continue

                props = self._entity_config[entity]
                name = props.get('name')
                target = props.get('target')
                has_entity = False
                entity_class = "_%s" % entity.capitalize()
                entityobj = getattr(sys.modules[__name__], entity_class)(self._init_object, props)
                (target_obj, has_entity) = entityobj.object()

                if target_obj is None:
                    raise Exception("Failed to get parent object for {0}".format(entity))

                if not has_entity:
                    log.info("{0} {1} doesn't exist".format(entity, target))
                    continue

                # Delete entity
                log.info("Deleting {0} [{1}] for [{2}]".format(entity, name, target))

                target_obj.delete(name)
                self._purge_entities(entity, props)
                entityobj.post_delete()
                (_, has_obj) = entityobj.object()
                assert not has_obj, "{0} [{1}] still exists. Failed to delete".format(entity, name)

        except Exception as excp:
            raise Exception("\n {0}: [{1}]".format(inspect.stack()[0][3], str(excp)))

    def cleanup(self):
        ''' Delete all entities in the self._entity_object_map dictionary

        Args:
            None

            Sample self._entity_object_map dictionary mapping:
            {
                'backupset'        :[{ backupset1 object properties },
                                     { backupset2 object properties } ...],
                'subclient'        :[{ subclient1 object properties },
                                     { subclient2 object properties } ...],
                'disklibrary'      :[{ disklibrary1 object properties },
                                     { disklibrary2 object properties } ...],
                'storagepolicy'    :[{ storagepolicy1 object properties },
                                     { storagepolicy2 object properties } ...],
                'clientgroup'      :[{ clientgroup object properties },
                                     { clientgroup object properties } ...],
            }

            Returns:
                None

            Raises Exception:
                - If failed to delete any entity
         '''

        try:
            self.refresh()

            self.log.info("***Cleaning up created entities as part of environmental changes***")
            self.log.info("Cleanup configuration \n {0}".format(str(self._entity_object_map)))

            cleanup_failed = False

            for entity_key in constants.DELETE_ENTITIES_ORDER:
                if entity_key in self._entity_object_map:
                    for props in self._entity_object_map[entity_key]:
                        # If cleanup is set to False for the entity, then skip cleanup.
                        if not props['cleanup']:
                            continue

                        # Deletion may fall during cleanup due to various reasons
                        # Cleanup should happen for all entities and should not stop
                        try:
                            self.delete({entity_key: props})
                        except Exception as exp:
                            self.log.error("Cleanup failed for {0}".format(entity_key))
                            self.log.error("Exception: {0}".format(str(exp)))
                            cleanup_failed = True

            if cleanup_failed:
                raise Exception("Failed to cleanup entities.")

        except Exception as exp:
            raise Exception("\n {0}: [{1}]".format(inspect.stack()[0][3], str(exp)))

    @argtypes(str)
    @returntype(str)
    def get_mount_path(self, mediagent):
        ''' Returns the mount path where library shall be created for a given
            Media Agent

        Args:
            mediagent (str)    -- Media agent client name

        Returns:
            mount_path (str)    -- Directory path where disk library will be created
        '''
        mount_path = self._utility.create_directory(mediagent, dirstring="DiskLibrary")
        self.log.info("Mount path for disklibrary = {0}".format(mount_path))
        return mount_path

    @argtypes(list)
    def create_client_groups(self, client_groups):
        """ Creates client groups from a given list of client group names
            These client groups will be empty and without any clients

        Args:
            client_groups    (list)  -- Names of client groups to be created

        Returns:
            Client group properties dictionary with name to properties mapping
            e.g:
            {
                'testproxy':
                {
                    'name': testproxy,
                    'clients': [],
                    'description': '',
                    'enable_backup': True,
                    'enable_restore': True,
                    'enable_data_aging': True,
                    'id': '1119',
                    'force': True,
                    'target': [],
                    'clientgroup': ClientGroup class instance for ClientGroup
                                         :"testproxy"
                },
                'test':
                {
                    'name': testproxy,
                    'clients': [],
                    'description': '',
                    'enable_backup': True,
                    'enable_restore': True,
                    'enable_data_aging': True,
                    'id': '1119',
                    'force': True,
                    'target': [],
                    'clientgroup': ClientGroup class instance for ClientGroup
                                         :"test"
                },

            }

        Raises:
            Exception
                - When failed to create any client group

        Example:
            ["testproxy", "test"]

        """
        try:
            client_groups_properties = {}
            for client_group in client_groups:
                client_group_props = self.create(
                    {
                        'clientgroup':
                            {
                                'name': client_group,
                                'clients': [],
                                'description': '',
                                'enable_backup': True,
                                'enable_restore': True,
                                'enable_data_aging': True,
                            },
                    }
                )

                key = client_group_props['clientgroup']['name']
                value = client_group_props['clientgroup']

                client_groups_properties[key] = value

            return client_groups_properties

        except Exception as excp:
            raise Exception("\n {0}: [{1}]".format(inspect.stack()[0][3], str(excp)))

    @argtypes(dict)
    def delete_client_groups(self, client_groups):
        """ Deletes client groups from a given dictionary of client group properties

        Args:
            client_groups    (dict)  -- Client group properties dictionary

        e.g:
            {
                'testproxy':
                {
                    'name': testproxy,
                    'clients': [],
                    'description': '',
                    'enable_backup': True,
                    'enable_restore': True,
                    'enable_data_aging': True,
                    'id': '1119',
                    'force': True,
                    'target': [],
                    'clientgroup': ClientGroup class instance for ClientGroup
                                         :"testproxy"
                },
                'test':
                {
                    'name': testproxy,
                    'clients': [],
                    'description': '',
                    'enable_backup': True,
                    'enable_restore': True,
                    'enable_data_aging': True,
                    'id': '1119',
                    'force': True,
                    'target': [],
                    'clientgroup': ClientGroup class instance for ClientGroup
                                         :"test"
                },
            }

        Returns:
            None

        Raises:
            Exception
                - When failed to delete any client group

        Example:
            ["testproxy", "test"]

        """
        try:
            for name in client_groups:
                self.delete({'clientgroup': client_groups[name]})

        except Exception as excp:
            raise Exception("\n {0}: [{1}]".format(inspect.stack()[0][3], str(excp)))

    def update_clientgroup(self,
                           clientgroup,
                           new_name=None,
                           description=None,
                           clients_to_add=None,
                           overwrite=False,
                           clients_to_remove=None):
        """Modifies client group properties

            Args:
                clientgroup (obj)       -- Client group object

                new_name (str)          -- New client group name

                description (str)       -- New client group description

                add_clients(list)       -- List of clients to be added to the client
                                            group.

                overwrite   (bool)      -- if set to true will remove old clients,
                                            and add new clients

                remove_clients(list)    -- List of clients to be added to the
                                            client group.
            Returns:
                None

            Raises:
                Exception - if any error occurred while updating the
                                client group properties.
        """
        try:
            log = self.log
            name = clientgroup.clientgroup_name

            def get_associated_clients():
                ''' Logs associated clients in a client group '''
                clients = clientgroup.associated_clients
                log.info("Associated clients for client group {0} are {1}".format(name, clients))

            if new_name is not None:
                log.info("Changing name of client group [{0}] to [{1}]".format(name, new_name))
                clientgroup.clientgroup_name = new_name
                name = new_name

            if description is not None:
                log.info("Changing client group [{0}] description to "
                         "[{1}]".format(clientgroup.description, description))
                clientgroup.description = description

            if clients_to_add is not None:
                get_associated_clients()
                log.info("Adding clients {0} to the client group "
                         "[{1}]".format(clients_to_add, name))
                clientgroup.add_clients(clients_to_add, overwrite)
                get_associated_clients()

            if clients_to_remove is not None:
                get_associated_clients()
                log.info("Removing clients {0} from the client group "
                         "[{1}]".format(clients_to_remove, name))
                clientgroup.remove_clients(clients_to_remove)
                get_associated_clients()

        except Exception as excp:
            raise Exception("\n {0}: [{1}]".format(inspect.stack()[0][3], str(excp)))

    def create_storage_pool(self, storage_pool_name=None, mountpath=None, mediaagent=None, ddb_ma=None, deduppath=None):
        """ Create storage pool

            Args:
                storage_pool_name (str)    -- Storage pool name to create

                mountpath (str)            -- Mount Path

                media_agent (str)          -- Media Agent associated to it

                ddb_ma (str)               -- DDB media agent

                deduppath (str)            -- Dedup Path

            Returns:
                (obj)        -- Storage pool object

            Raises:
                Exception:
                    - In case failed while creating storage pool
        """
        try:
            storage_pools = self._commcell.storage_pools
            utils = self._utility
            storage_pool_name = utils.get_custom_str('spool') if storage_pool_name is None else storage_pool_name

            media_agent = utils.get_ma('windows') if mediaagent is None else mediaagent
            mountpath = utils.create_directory(media_agent, dirstring="mountpath") if mountpath is None else mountpath
            deduppath = utils.create_directory(media_agent, dirstring="deduppath") if deduppath is None else deduppath
            ddb_ma = media_agent if ddb_ma is None else ddb_ma

            if storage_pools.has_storage_pool(storage_pool_name):
                self.log.info("Storage pool [{0}] already exists".format(storage_pool_name))
                return storage_pools.get(storage_pool_name)

            self.log.info("Creating storage pool [{0}] on Media Agent [{1}] with mount path [{2}]".format(
                storage_pool_name, media_agent, mountpath))
            return storage_pools.add(storage_pool_name, mountpath, media_agent, ddb_ma, deduppath)

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def create_sp_copy(self,
                       storage_policy,
                       copy_name,
                       library,
                       mediaagent,
                       drive_pool=None,
                       spare_pool=None,
                       tape_library_id=None,
                       drive_pool_id=None,
                       spare_pool_id=None,
                       force=True):
        """ Creates a storage policy copy for the given storage policy.

            Args:
                storage_policy    (obj/str)   -- storage policy name OR corresponding storage
                                                    policy SDK instance of class StoragePolicy

                copy_name         (str)       -- name of the storage policy copy to create

                library           (str)       -- Library name to associate to copy

                mediaagent        (str)       -- Media agent associated to the input library

                drive_pool         (str)      -- Drive pool name in case library is TapeLibrary

                spare_pool         (str)      -- Spare pool name in case library is TapeLibrary

                tape_library_id    (int)      -- Tape library id in case library is TapeLibrary

                drive_pool_id      (int)      -- Drive pool id

                spare_pool_id      (int)      -- Spare pool id

                force              (bool)      -- If True, will delete any existing copy with the
                                                    same name

                                                  If False, will not create the copy and will log
                                                      error.

            Returns:
                None

            Raises:
                Exception if :

                    - failed during execution of module
        """
        try:

            # If storage_policy is not an instance of StoragePolicy SDK class, then get the
            # storage policy object from name
            if not isinstance(storage_policy, StoragePolicy):
                storage_policies = self._commcell.storage_policies
                storage_policy = storage_policies.get(storage_policy)

            args = ['StoragePolicy copy', copy_name, storage_policy]
            create = True

            if storage_policy.has_copy(copy_name):
                self.log.info("{0} [{1}] already exists for {2}".format(*args))
                if force:
                    self.log.info("Deleting {0} [{1}] for {2}".format(*args))

                    storage_policy.delete_secondary_copy(copy_name)

                    self.log.info("Deleted {0} [{1}] successfully".format(*args))
                else:
                    self.log.error("Copy not created as it already exits.")
                    create = False

            if create:
                self.log.info("Creating {0} [{1}] for {2}".format(*args))

                storage_policy.create_secondary_copy(copy_name,
                                                     library,
                                                     mediaagent,
                                                     drive_pool,
                                                     spare_pool,
                                                     tape_library_id,
                                                     drive_pool_id,
                                                     spare_pool_id)

                self.log.info("Created {0} [{1}] for {2}".format(*args))

        except Exception as excp:
            raise Exception("\n {0}:[{1}]".format(inspect.stack()[0][3], str(excp)))

    def post_delete(self):
        ''' Performing post delete configuration'''
        pass

    def post_create(self, *_):
        ''' Performing post creation configuration'''
        pass

    def existing_config(self):
        ''' Performs configuration for existing entity'''
        pass

    @argtypes(list, str)
    @returntype(dict)
    def _get_entity_objects(self, object_types=None, entity_type=None):
        '''Method to retrieve entity objects/properties

        This module creates relevant entity objects/properties for the
        object_types and returns a dictionary of entity properties/objects


        Args:

            object_types  (list)  --    List of objects to be returned by module
                                        e.g:
                                        ['client',
                                        'agent',
                                        'instance',
                                        'backupset',
                                        'mediaagent',
                                        'library']

            entity_type    (str)   --   One of the entity types
                                        e.g:
                                        'backupset'
                                        'subclient'
                                        'disklibrary'
                                        'storagepolicy'
                                        'clientgroup'
        Returns:
            Dictionary containing properties required to create the entity mentioned
            in entity_type

        Raises:
            Exception:
                if failed to get object/properties for an entity
        '''

        all_objects = {}

        try:
            props = self._entity_config.get(entity_type)
            props = OptionsSelector.get_var(props, dict())

            # If name is not defined, define name for entity_type
            name = props.get('name')
            if name is None:
                name = OptionsSelector.get_custom_str(entity_type)
            props['name'] = name

            # Set force and cleanup option for the entity
            for _option in ['force', 'cleanup']:
                _opt = self._get_target_props(_option, entity_type)
                props[_option] = OptionsSelector.get_var(_opt, constants.DEFAULT_ENTITY_FORCE)
                if not isinstance(props[_option], bool):
                    raise Exception("Get properties failed for {0}.  force option should be bool"
                                    " (True/False)".format(entity_type))

            entity_class = "_%s" % entity_type.capitalize()
            entity = getattr(sys.modules[__name__], entity_class)(self._init_object, props)
            props = entity.get_properties(self._entity_config, self._created_entities)

            # Validate common entity properties and values
            for obj_type in object_types:

                # Find the obj_type in individual/target properties
                # May come out to be None, in which case would be assigned default
                # assignments.
                val = self._get_target_props(obj_type, entity_type)
                if val is None or val == '':
                    val = getattr(self, 'default_' + obj_type)

                obj_name_key = '_'.join([obj_type, 'name'])

                # Get entity objects for each property
                if obj_type == 'client':
                    obj = self._commcell.clients.get(val)
                    obj_name = obj.client_name

                elif obj_type == 'agent':
                    obj = all_objects['client'].agents.get(val)
                    obj_name = obj.agent_name

                elif obj_type == 'instance':
                    obj = all_objects['agent'].instances.get(val)
                    obj_name = obj.instance_name

                elif obj_type == 'backupset':
                    obj = all_objects['instance'].backupsets.get(props[obj_name_key])
                    obj_name = obj.backupset_name

                elif obj_type == 'mediaagent':
                    obj_name = props.get(obj_name_key)
                    obj = self._commcell.media_agents.get(obj_name)

                elif obj_type == 'library':
                    obj_name = props.get(obj_name_key)
                    obj = self._commcell.disk_libraries.get(obj_name)

                if obj is None:
                    raise Exception("Unable to get {0} object".format(obj_type))

                all_objects[obj_type] = obj
                all_objects[obj_name_key] = obj_name

            props.update(all_objects)

            self.log.info("{0} properties to be created \n {1}".format(entity_type.capitalize(),
                                                                       str(all_objects)))

            return props

        except Exception as excp:
            raise Exception("\n {0}:[{1}]".format(inspect.stack()[0][3], str(excp)))
        finally:
            all_objects = None

    def _get_target_props(self, entity_prop, entity_type, entity_config=None):
        ''' Returns the property value based on whether the target property is defined
            in the entity map

        Args:
            entity_prop (str)     --
                                    One of the supported entity property types
                                        e.g:
                                            'backupset'
                                            'subclient'
                                            'disklibrary'
                                            'storagepolicy'
                                            'mediaagent'
                                            'library' ... etc

            entity_type    (str)   --   One of the supported entity types
                                        e.g:
                                        'backupset'
                                        'subclient'
                                        'disklibrary'
                                        'storagepolicy'
                                        'clientgroup'

            entity_config (dict)   -- Entity properties if specified by user

        Returns:
            None

        Raises:
            Exception:
                if failed to get the entity property
        '''
        try:
            if entity_config is None:
                entity_config = self._entity_config

            prop_value = None
            # Get property value from common properties, but if individual
            # property is defined then give preference to it and override the
            # common property
            if entity_prop in entity_config.get('target', []):
                prop_value = entity_config['target'].get(entity_prop)

            properties = entity_config.get(entity_type)
            properties = OptionsSelector.get_var(properties, dict())
            if properties.get(entity_prop) is not None:
                prop_value = properties.get(entity_prop)

            return prop_value

        except Exception as excp:
            raise Exception("\n {0}:[{1}]".format(inspect.stack()[0][3], str(excp)))

    @staticmethod
    def _get_target_str(dest_targets=None):
        ''' Gets a target string where entities shall be created '''
        return "->".join(dest_targets)

    @argtypes(str, dict)
    def _purge_entities(self, entity, entity_objects):
        ''' Updates the entity object map and removes properties for a
                entity in self._entity_object_map

        Args:
            entity (str)          --
                                    One of the supported entity types
                                        e.g:
                                            'backupset'
                                            'subclient'
                                            'disklibrary'
                                            'storagepolicy'

            entity_objects (dict) --
                                    Entity properties
                                        e.g:
                                            {
                                                'force': True,
                                                'incremental_sp': None,
                                                'library': 'library_name',
                                                'mediaagent': 'ma_name',
                                                'name': 'storagepolicy_name',
                                                'retention_period': 5,
                                                'target': 'ma_name->library_name'
                                            }

        Returns:
            None

        Raises:
            Exception:
                if failed to remove the entity properties to the cleanup map
        '''

        try:
            self.log.info("Removing {0} [{1}] from cleanup map".format(entity,
                                                                       entity_objects['name']))

            entity_list = self._entity_object_map.get(entity, [])
            updated_entity_list = []

            for entity_dict in entity_list:
                if (entity_dict.get('id') != entity_objects['id'] and
                        entity_dict.get('name') != entity_objects['name']):
                    updated_entity_list.append(entity_dict)

            self._entity_object_map[entity] = updated_entity_list

        except Exception as excp:
            raise Exception("\n {0}:[{1}]".format(inspect.stack()[0][3], str(excp)))

    @property
    def entity_object_map(self):
        ''' Returns dictionary containing the entity properties created
            from the create() function calls '''
        return self._entity_object_map

    @property
    def default_client(self):
        ''' Returns default testcase client '''
        try:
            client = self._testcase.client
            return client.client_name
        except Exception as _:
            self.log.info("Unable to get default client name")
            return None

    @property
    def default_agent(self):
        ''' Returns default testcase agent name'''
        try:
            agent = self._testcase.agent
            return agent.agent_name
        except Exception as _:
            self.log.info("Unable to get default agent")
            return None

    @property
    def default_instance(self):
        ''' Returns default testcase instance '''
        try:
            instance = self._testcase.instance
            return instance.instance_name
        except Exception as _:
            self.log.info("Unable to get default instance")
            return None

    @property
    def default_backupset(self):
        ''' Returns default testcase backupset '''
        try:
            backupset = self._testcase.backupset
            return backupset.backupset_name
        except Exception as _:
            self.log.info("Unable to get default backupset")
            return None

    @property
    def default_subclient(self):
        ''' Returns default testcase subclient '''
        try:
            subclient = self._testcase.subclient
            return subclient.subclient_name
        except Exception as _:
            self.log.info("Unable to get default subclient")
            return None

    @property
    def default_storagepolicy(self):
        ''' Returns default testcase subclient's storagepolicy'''
        try:
            subclient = self._testcase.subclient
            return subclient.storage_policy
        except Exception as _:
            self.log.info("Unable to get default storagepolicy")
            return None

    @property
    def default_mediaagent(self):
        ''' Returns default testcase media agent '''
        try:
            subclient = self._testcase.subclient
            return subclient.storage_ma
        except Exception as _:
            self.log.info("Unable to get default media agent name")
            return None

    @property
    def default_library(self):
        ''' Returns default testcase subclient's library name '''
        try:
            subclient = self._testcase.subclient
            storagepolicy = self._commcell.storage_policies.get(subclient.storage_policy)
            return storagepolicy.library_name
        except Exception as _:
            self.log.info("Unable to get default library")
            return None

    def refresh(self):
        ''' Refreshes the properties/dynamic dictionary of the CVEntities class'''
        self._created_entities.clear()
        self.entity_props.clear()
        self._entity_config.clear()


class _Backupset(CVEntities):
    ''' Class to support CVEntities class with common backupset operations'''

    associated_entities = ['client', 'agent', 'instance']
    entity_id = 'backupset_id'

    def __init__(self, init_object, entity_properties=None):
        """Initializes Backupset class object
        Args:
            init_object (object) : Should be either the commcell or the testcase object

            entity_properties (dict) : Entity properties to be created/modified."""

        # Pre-initialized attributes applicable for all instances of the class
        if isinstance(init_object, Commcell):
            self._commcell = init_object
        else:
            self._testcase = init_object
            self._commcell = self._testcase.commcell

        super(_Backupset, self).__init__(self._commcell)
        self.log = logger.get_log()
        self.props = entity_properties

    def object(self):
        ''' Get associated object and checks if backupset exist'''
        name = self.props['name']
        bkpset = self.props['instance'].backupsets
        self.props['backupsets'] = bkpset
        bkpset.refresh()

        # Return tuple of (object, True/False)
        return (bkpset, bkpset.has_backupset(name))

    def target(self):
        ''' Returns target string where backupset shall be created '''
        client = self.props['client_name']
        agent = self.props['agent_name']
        instance = self.props['instance_name']
        target = self._get_target_str([client, agent, instance])
        self.props['target'] = target
        return target

    def get_properties(self, *_):
        ''' Sets entity properties based on dynamic evaluation of input properties

            Returns:
                - Modified entity properties based on dynamic evaluation
        '''
        # Entity properties
        self.props['on_demand_backupset'] = self.props.get('on_demand_backupset', False)
        return self.props

    def add_args(self):
        ''' Returns the keyword arguments for add() module'''
        return {
            'backupset_name': self.props['name'],
            'on_demand_backupset': self.props['on_demand_backupset']
        }


class _Subclient(CVEntities):
    ''' Class to support CVEntities class with common subclient operations'''

    associated_entities = ['client', 'agent', 'instance', 'backupset']
    entity_id = 'subclient_id'

    def __init__(self, init_object, entity_properties=None):
        """Initializes Subclient class object
        Args:
            init_object (object) : Should be either the commcell or the testcase object

            entity_properties (dict) : Entity properties to be created/modified."""

        # Pre-initialized attributes applicable for all instances of the class
        if isinstance(init_object, Commcell):
            self._commcell = init_object
        else:
            self._testcase = init_object
            self._commcell = self._testcase.commcell

        super(_Subclient, self).__init__(self._commcell)
        self.log = logger.get_log()
        self.props = entity_properties

    def object(self):
        ''' Gets the associated object and checks if the subclient exists '''
        name = self.props['name']
        subc = self.props['backupset'].subclients
        self.props['subclients'] = subc
        subc.refresh()

        # Return tuple of (object, True/False)
        return (subc, subc.has_subclient(name))

    def target(self):
        ''' Returns target string on which the subclient shall be created '''
        client = self.props['client_name']
        agent = self.props['agent_name']
        instance = self.props['instance_name']
        backupset = self.props['backupset_name']
        target = self._get_target_str([client, agent, instance, backupset])
        self.props['target'] = target
        return target

    def post_delete(self):
        ''' Performing post delete configuration for subclient '''
        if self.props.get('cleanup_content'):
            # Delete subclient content
            self._utility.remove_directory(self.props['client_name'], self.props['content'][0])

    def post_create(self, subclient):
        ''' Perform post creation configuration for subclient

        Args:
            subclient (object)  -- subclient object

        Raises:
            Exception:
                - failed to do post creation configuration'''
        try:
            content = self.props.get('content')

            if content is not None:
                cleanup_content = False
                if isinstance(content, list):
                    subclient.content = content
                elif content == 'skip':
                    self.log.info("Skipping content creation for subclient")
                else:
                    raise Exception("Unsupported subclient content type [{0}] passed as argument.".format(content))
            else:
                subclient.content = [self._utility.create_test_data(self.props['client_name'],
                                                                    self.props['data_path'],
                                                                    self.props['level'],
                                                                    self.props['size'])]
                cleanup_content = True

            self.log.info("Setting subclient content {0}".format(subclient.content))

            self.props['content'] = subclient.content
            self.props['cleanup_content'] = self.props.get('cleanup_content', cleanup_content)

            if self.props.get('filter_content'):
                subclient.filter_content = self.props.get('filter_content')
                self.props['filter_content'] = subclient.filter_content

        except Exception as excp:
            raise Exception("\n {0}:[{1}]".format(inspect.stack()[0][3], str(excp)))

    def get_properties(self, entity_config, created_entities):
        ''' Sets entity properties based on dynamic evaluation of input properties

            Args:
                entity_config (dict) -- Dict of properties of all entities to be created

                created_entities (dict) -- Dict of created entities and their properties

            Returns:
                - Modified entity properties based on dynamic evaluation
        '''
        # Target properties
        for _type in ['storagepolicy', 'backupset']:
            _name = self._get_target_props(_type, 'subclient', entity_config)

            if _name is None and _type in entity_config:
                _name = created_entities[_type].get('name')

            if _type == 'storagepolicy':
                _default = self.default_storagepolicy

            elif _type == 'backupset':
                _default = self.default_backupset

            _name = OptionsSelector.get_var(_name, _default)
            self.props['_'.join([_type, 'name'])] = _name

            if _name is None:
                raise Exception("Failed to fetch {0} for {1}".format(_type, 'subclient'))

        # Entity properties
        self.props['subclient_type'] = self.props.get('subclient_type', None)
        self.props['description'] = self.props.get('description', constants.DESCRIPTION)
        self.props['content'] = self.props.get('content')
        self.props['filter_content'] = self.props.get('filter_content')
        self.props['data_path'] = self.props.get('data_path', None)
        self.props['level'] = self.props.get('level', constants.DEFAULT_DIR_LEVEL)
        self.props['size'] = self.props.get('size', constants.DEFAULT_FILE_SIZE)
        self.props['pre_scan_cmd'] = self.props.get('pre_scan_cmd', None)

        return self.props

    def existing_config(self):
        ''' Performs configuration for existing subclient '''
        self.props.pop('content', None)
        self.props.pop('filter_content', None)

    def add_args(self):
        ''' Returns the keyword arguments for add() module'''
        return {
            'subclient_name': self.props['name'],
            'storage_policy': self.props['storagepolicy_name'],
            'subclient_type': self.props['subclient_type'],
            'description': self.props['description'],
            'pre_scan_cmd':self.props['pre_scan_cmd'],
        }


class _Storagepolicy(CVEntities):
    ''' Class to support CVEntities class with common storagepolicy operations'''

    associated_entities = ['mediaagent', 'library']
    entity_id = 'storage_policy_id'

    def __init__(self, init_object, entity_properties=None):
        """Initializes Storagepolicy class object
        Args:
            init_object (object) : Should be either the commcell or the testcase object

            entity_properties (dict) : Entity properties to be created/modified."""

        # Pre-initialized attributes applicable for all instances of the class
        if isinstance(init_object, Commcell):
            self._commcell = init_object
        else:
            self._testcase = init_object
            self._commcell = self._testcase.commcell

        super(_Storagepolicy, self).__init__(self._commcell)
        self.log = logger.get_log()
        self.props = entity_properties

    def object(self):
        ''' Gets the associated object and checks if the storagepolicy exists '''
        name = self.props['name']
        storagepolicy = self._commcell.storage_policies
        self.props['storagepolicies'] = storagepolicy
        storagepolicy.refresh()

        # Return tuple of (object, True/False)
        return (storagepolicy, storagepolicy.has_policy(name))

    def target(self):
        ''' Returns target string on which the storagepolicy shall be created '''
        target = self._get_target_str([self.props['mediaagent_name'], self.props['library_name']])
        self.props['target'] = target
        return target

    def post_create(self, *_):
        ''' Perform post creation configuration for storage policy '''
        # Create Storage policy copy
        if 'copy_name' in self.props:
            self.create_sp_copy(self.props['object'],
                                self.props['copy_name'],
                                self.props['library_name'],
                                self.props['mediaagent_name'],
                                self.props['drive_pool'],
                                self.props['spare_pool'],
                                self.props['tape_library_id'],
                                self.props['drive_pool_id'],
                                self.props['spare_pool_id'])

    def get_properties(self, entity_config, created_entities):
        ''' Sets entity properties based on dynamic evaluation of input properties

            Args:
                entity_config (dict) -- Dict of properties of all entities to be created

                created_entities (dict) -- Dict of created entities and their properties

            Returns:
                - Modified entity properties based on dynamic evaluation
        '''
        # Target properties
        mediaagent = self._get_target_props('mediaagent', 'storagepolicy', entity_config)
        library = self._get_target_props('library', 'storagepolicy', entity_config)
        if library is None and 'disklibrary' in entity_config:
            library = created_entities['disklibrary'].get('name')
            if not mediaagent:
                mediaagent = created_entities['disklibrary'].get('mediaagent_name')

        if library is None:
            library = self.default_library
            mediaagent = self.default_mediaagent

        if library is None:
            raise Exception("Failed to assign library and mediaagent for storagepolicy entity")

        self.props['library_name'] = library
        self.props['mediaagent_name'] = mediaagent

        # Entity properties
        self.props['dedup_path'] = self.props.get('dedup_path')
        self.props['incremental_sp'] = self.props.get('incremental_sp')
        self.props['retention_period'] = self.props.get('retention_period', 5)
        self.props['drivepool'] = self.props.get('drivepool', '')
        self.props['scratchpool'] = self.props.get('scratchpool', 'Default Scratch')
        self.props['incremental_sp_tape'] = self.props.get('incremental_sp_tape')
        self.props['istape'] = self.props.get('istape', False)
        self.props['number_of_streams'] = self.props.get('number_of_streams')
        self.props['ocum_server'] = self.props.get('ocum_server')
        self.props['dr_sp'] = self.props.get('dr_sp', False)

        # Storage policy copy properties
        if 'copy_name' in self.props:
            self.props['copy_name'] = self.props.get('copy_name',
                                                     OptionsSelector.get_custom_str('copy'))
            self.props['spare_pool'] = self.props.get('spare_pool')
            self.props['spare_pool_id'] = self.props.get('spare_pool_id')
            self.props['tape_library_id'] = self.props.get('tape_library_id')
            self.props['drive_pool'] = self.props.get('drive_pool')
            self.props['drive_pool_id'] = self.props.get('drive_pool_id')

        return self.props

    def existing_config(self):
        ''' Performs configuration for existing storagepolicy '''
        self.props = OptionsSelector.pop_keys(self.props,
                                              ['dedup_path', 'incremental_sp',
                                               'retention_period', 'drivepool',
                                               'scratchpool'])
        self.props['target'] = self.props['library'].library_name

    def add_args(self):
        ''' Returns the keyword arguments for add() module'''
        return {
            'storage_policy_name': self.props['name'],
            'library': self.props['library_name'],
            'media_agent': self.props['mediaagent_name'],
            'dedup_path': self.props['dedup_path'],
            'incremental_sp': self.props['incremental_sp'],
            'retention_period': self.props['retention_period'],
            'number_of_streams': self.props['number_of_streams'],
            'ocum_server': self.props['ocum_server'],
            'dr_sp': self.props['dr_sp']
        }

    def add_tape_args(self):
        ''' Returns the keyword arguments for add_tape_sp() module'''
        return {
            'storage_policy_name': self.props['name'],
            'library': self.props['library_name'],
            'media_agent': self.props['mediaagent_name'],
            'drive_pool': self.props['drivepool'],
            'scratch_pool': self.props['scratchpool']
        }


class _Disklibrary(CVEntities):
    ''' Class to support CVEntities class with common disklibrary operations'''

    associated_entities = ['mediaagent']
    entity_id = 'library_id'

    def __init__(self, init_object, entity_properties=None):
        """Initializes Disklibrary class object
        Args:
            init_object (object) : Should be either the commcell or the testcase object

            entity_properties (dict) : Entity properties to be created/modified."""

        # Pre-initialized attributes applicable for all instances of the class
        if isinstance(init_object, Commcell):
            self._commcell = init_object
        else:
            self._testcase = init_object
            self._commcell = self._testcase.commcell

        super(_Disklibrary, self).__init__(self._commcell)
        self.log = logger.get_log()
        self.props = entity_properties

    def object(self):
        ''' Gets the associated object and checks if the disklibrary exists '''
        name = self.props['name']
        disklibrary = self._commcell.disk_libraries
        self.props['disklibraries'] = disklibrary
        disklibrary.refresh()

        # Return tuple of (object, True/False)
        return (disklibrary, disklibrary.has_library(name))

    def target(self):
        ''' Returns target string on which the disklibrary shall be created '''
        target = self._get_target_str([self.props['mediaagent_name'], self.props['mount_path']])
        self.props['target'] = target
        return target

    def post_delete(self):
        ''' Perform post delete configuration for disklibrary '''
        if self.props.get('cleanup_mount_path') and (
                self.props.get('mediaagent_name') is not None and
                self.props.get('mount_path') is not None):
            # Delete disklibrary mount path on the Media Agent
            self._utility.remove_directory(self.props['mediaagent_name'],
                                           self.props['mount_path'])

    def get_properties(self, entity_config, *_):
        ''' Sets entity properties based on dynamic evaluation of input properties

            Args:
                entity_config (dict) -- Dict of properties of all entities to be created

            Returns:
                - Modified entity properties based on dynamic evaluation
        '''
        # Target properties
        mediaagent = self._get_target_props('mediaagent', 'disklibrary', entity_config)
        if mediaagent is None or mediaagent == '':
            mediaagent = self.default_mediaagent

        if mediaagent is None or mediaagent == '':
            mediaagent = self._utility.get_ma('any')

        self.props['mediaagent_name'] = mediaagent
        self.log.info("Media agent for creating disklibrary: {0}".format(mediaagent))

        if mediaagent is None:
            raise Exception("Failed to fetch media agent for creating disk library")

        # Entity properties
        self.props['mount_path'] = self.props.get('mount_path')

        if self.props['mount_path'] is None:
            self.props['mount_path'] = self.get_mount_path(mediaagent)
        else:
            self.props['input_mount_path'] = True

        self.props['cleanup_mount_path'] = self.props.get('cleanup_mount_path',
                                                          bool(self.props['mount_path']))
        self.props['username'] = self.props.get('username', '')
        self.props['password'] = self.props.get('password', '')

        return self.props

    def existing_config(self):
        ''' Performs configuration for existing disklibrary '''
        if not self.props.get('input_mount_path', False):
            self._utility.remove_directory(self.props['mediaagent_name'], self.props['mount_path'])
        self.props = OptionsSelector.pop_keys(self.props, ['mediaagent_name',
                                                           'mediaagent', 'username',
                                                           'password', 'mount_path'])
        self.props['target'] = ''

    def add_args(self):
        ''' Returns the keyword arguments for add() module'''
        return {
            'library_name': self.props['name'],
            'media_agent': self.props['mediaagent_name'],
            'mount_path': self.props['mount_path'],
            'username': self.props['username'],
            'password': self.props['password']
        }


class _Clientgroup(CVEntities):
    ''' Class to support CVEntities class with common clientgroup operations'''

    associated_entities = []
    entity_id = 'clientgroup_id'

    def __init__(self, init_object, entity_properties=None):
        """Initializes Clientgroup class object
        Args:

            init_object (object)     : Should be either the commcell or the testcase object

            entity_properties (dict) : Entity properties """

        # Pre-initialized attributes applicable for all instances of the class
        if isinstance(init_object, Commcell):
            self._commcell = init_object
        else:
            self._testcase = init_object
            self._commcell = self._testcase.commcell

        super(_Clientgroup, self).__init__(self._commcell)
        self.log = logger.get_log()
        self.props = entity_properties

    def object(self):
        ''' Gets the associated object and checks if the clientgroup exists '''
        name = self.props['name']
        clientgroup = self._commcell.client_groups
        self.props['clientgroups'] = clientgroup
        clientgroup.refresh()

        # Return tuple of (object, True/False)
        return (clientgroup, clientgroup.has_clientgroup(name))

    def target(self):
        ''' Returns target string on which the clientgroup shall be created '''
        target = self.props['clients']
        self.props['target'] = target
        return target

    def get_properties(self, entity_config, created_entities):
        ''' Sets entity properties based on dynamic evaluation of input properties

            Args:
                entity_config (dict) -- Dict of properties of all entities to be created

                created_entities (dict) -- Dict of created entities and their properties

            Returns:
                - Modified entity properties based on dynamic evaluation
        '''
        clients = self._get_target_props('clients', 'clientgroup', entity_config)
        default_client_flag = self.props.get('default_client', True)

        # If no clients are provided in input dictionary and default client
        # has to be set in the client group then assign default client.
        # Other wise set clients as empty.
        if clients is None and default_client_flag:
            for key in constants.DELETE_ENTITIES_ORDER:
                if key in entity_config and key != 'clientgroup':
                    _client = created_entities[key].get('client_name')
                    if _client is not None:
                        clients = [_client]
                        break

            clients = self.default_client if clients is None else clients

        self.props['clients'] = clients if clients is not None else []

        # Entity properties
        self.props['description'] = self.props.get('description', constants.DESCRIPTION)
        for item in ['enable_backup', 'enable_restore', 'enable_data_aging']:
            self.props[item] = self.props.get(item, True)

        return self.props

    def add_args(self):
        ''' Returns the keyword arguments for add() module'''
        return {
            'clientgroup_name': self.props['name'],
            'clients': self.props['clients'],
            'clientgroup_description': self.props['description'],
            'enable_backup': self.props['enable_backup'],
            'enable_restore': self.props['enable_restore'],
            'enable_data_aging': self.props['enable_data_aging'],
            'scg_rule': self.props.get('scg_rule')

        }
