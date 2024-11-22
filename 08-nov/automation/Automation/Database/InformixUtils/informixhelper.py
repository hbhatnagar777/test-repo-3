# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing Informix related operations.

InformixsHelper is a only class defined in this file.

InformixHelper: Class for performing Informix related operation



InformixHelper:
=================
    __init__()                                  --  initialize InformixHelper object

    informix_server_operation()                 --  method to perform Informix related operations
    like start/stop/status in client

    get_informix_server_status()                --  checks for the Informix server status
    in client

    start_informix_server()                     --  starts the Informix server in client

    stop_informix_server()                      --  stops the Informix server in client

    bring_server_online()                       --  brings the server to online from
    quiescent mode

    mark_disabled_dbspace_down()                --  prepares the automation dbspace for partial
    restore by marking it disabled and down

    create_dbspace()                            --  creates a dbspace inside the server

    drop_dbspace()                              --  drops the dbspace inside the server

    cl_full_backup_entire_instance()            --  performs commandline full backup of
    Entire Instance.

    cl_incremental_entire_instance()            --  performs commandline level 1 incremental
    backup of Entire Instance.

    cl_inc_entire_instance_level_2()            --  performs commandline level 2 incremental
    backup of Entire Instance

    cl_restore_entire_instance()                --  performs commandline restore of Entire Instance

    cl_full_backup_whole_system()               --  performs commandline full backup
    of Whole System.

    cl_incremental_whole_system()               --  performs commandline level 1 incremental
    backup of Whole System.

    cl_inc_whole_system_level_2()               --  performs commandline level 2 incremental
    backup of Whole System

    cl_restore_whole_system()                   --  performs commandline restore of Whole System

    cl_table_level_restore()                    --  performs commandline table level restore

    cl_table_level_aux_restore()                --  performs commandline table level restore
    from secondary copy

    cl_aux_copy_restore()                       --  performs commandline entire instance restore
    from secondary copy

    cl_aux_restore_whole_system()               --  performs commandline whole instance restore
    from secondary copy

    cl_aux_log_only_restore()                   --  performs commandline log only restore from
    secondary copy

    cl_log_only_restore()                       --  performs commandline log only restore

    cl_physical_restore()                       --  performs commandline physical restore

    cl_physical_whole_sys_restore()             --  performs commandline physical restore of
    whole system

    cross_machine_restore()                     --  performs commandline cross machine restore
    of Entire Instance/Whole System

    list_dbspace()                              --  Lists all dbspaces in the server

    create_database()                           --  creates a database inside the dbspace

    drop_database()                             --  drops a database if it exists

    get_database_list()                         --  gets all the database names in the server

    check_if_db_exists()                        --  checks if the specified database exists

    create_table()                              --  creates a table inside a database

    insert_rows()                               --  inserts test data inside a table

    populate_data()                             --  populates the Informix server for testing

    delete_test_data()                          --  deletes the data generated for testing

    collect_meta_data()                         --  collects the meta data of a database server

    row_count()                                 --  returns number of rows in the table specified

    execute_query()                             --  runs the query on informix db

    reconnect()                                 --  re-Connects to informix DB

    get_last_log_number()                       --  gets number of the last informix log backed up

    get_afileid()                               --  gets afile id of a backup object for given job
    id and file type

    cross_machine_operations()                  --  fetches all the necessary information required
    to start cross machine restore

    cross_config_only_restore()                 --  performs cross machine restore of config files
    and modifies replaced onconfig file as required for restore

    get_rename_dbspace_command()                --  returns the rename command string to be used
    for the cross machine restore between two servers with different dbspace structures

    get_command_line_job()                      --  finds the commandline job id launched by cl
    jobs and returns job object

    cl_switch_log()                             --  performs commandline switch log operation

    cl_log_only_backup()                        --  performs commandline log only backup

    drop_table()                                --  drops the table from specified database

    is_log_backup_to_disk_enabled()             --  method to check if log backup to disk feature is enabled
    for instance or not

    run_sweep_job_using_regkey()                --  Sets SweepStartTime regkey and waits for the sweep job
    to finish

    get_child_jobs()                            --  Method to get the list of child jobs for a parent job

    create_sweep_schedule_policy()              --  method to create sweep schedule policy

Attributes
----------

    **base_directory**     --  returns Base directory path of the client machine

"""

import os
import time
from datetime import datetime, timedelta
from AutomationUtils import logger, constants
from AutomationUtils import database_helper
from AutomationUtils import machine
from AutomationUtils.script_generator import ScriptGenerator
from Database.dbhelper import DbHelper

class InformixHelper(object):
    """Helper class to perform Informix operations"""

    def __init__(
            self,
            commcell,
            instance,
            subclient,
            hostname,
            server,
            user_name,
            password,
            service,
            run_log_only_backup=False):
        """Initialize the InformixHelper object.

            Args:
                commcell        (obj)  --  Commcell object

                instance        (obj)  --  instance object

                subclient       (obj)  --  subclient object

                hostname        (str)  --  Hostname of the client machine

                server          (str)  --  Informix Server name

                user_name       (str)  --  Username of Informix server

                password        (str)  --  Password of Informix server

                service         (str)  --  Informix service assocoiated with the server

                run_log_only_backup (bool)  --  flag to determine if the log only backup needs to be run
                when the object is created
                    default: False

            Returns:
                object - instance of InformixHelper class

        """
        self._hostname = hostname
        self._commcell = commcell
        self._instance = instance
        self._subclient = subclient
        self._informix_server_name = instance.instance_name
        self._informix_directory = instance.informix_directory
        self.server = server
        self.user_name = user_name
        self.password = password
        self.service = service
        self.machine_object = machine.Machine(
            self._hostname, self._commcell)
        self._csdb = database_helper.get_csdb()
        self.log = logger.get_log()
        self.start_informix_server()
        self.informix_db = database_helper.Informix(
            self._hostname,
            server,
            user_name,
            password,
            "sysmaster",
            service)
        if run_log_only_backup:
            self.log.info("Running log only backup")
            self.cl_log_only_backup(
                self._instance._agent_object._client_object.client_name,
                self._instance._agent_object._client_object.instance,
                self.base_directory)


    def informix_server_operation(self,
                                  operation,
                                  database_name=None,
                                  client_name=None,
                                  instance=None,
                                  base_directory=None,
                                  copy_precedence=None,
                                  token_file_path=None,
                                  server_number=None,
                                  arguments=None):
        """ Method to perform Informix server specific operations\
            like start/stop/status in client.

            Args:
                operation       (Str)   -- Operations to perform on Informix Server

                                            Acceptable Values:

                                                start/stop/status/online/create_dbspace/
                                                drop_dbspace/create_db

                database_name   (str)   -- Database name to create/delete

                    default: None

                client_name     (str)   -- Name of the Informix Client

                    default: None

                instance        (str)   -- Instance of the client

                    default: None

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                copy_precedence (str)   -- Copy precedence of secondary copy

                    default:None

                token_file_path (str)   -- Token file path for commandline
                job authentication

                    default: None

                server_number   (str)   -- Informix Server number specified
                in onconfig file

                    default: None

                arguments       (str)   -- Extra arguments to be passed with
                onbar -r command during cross machine restore

                    default: None

            Returns:
                Returns script execution output on success
        """
        script_generator = ScriptGenerator()

        if "unix" in self.machine_object.os_info.lower():
            script_generator.script = constants.UNIX_INFORMIX_SERVER_OPERATIONS
        else:
            script_generator.script = constants.WINDOWS_INFORMIX_SERVER_OPERATIONS
        os_name = None
        if not "windows" in self.machine_object.os_info.lower():
            if not base_directory is None:
                for i in ["aix", "solaris"]:
                    if i in self.machine_object.os_flavour.lower():
                        os_name = "aix/solaris"
            version = None
            if os_name == "aix/solaris" and (not base_directory is None):
                version = self._instance.version
                if version is None:
                    raise Exception(
                        "Unable to fetch the version details from instance properties")
                if "fc" in version.lower():
                    base_directory = base_directory + "64"
                else:
                    base_directory = base_directory + "32"
                self.log.info("LD_LIBRARY_PATH will be set as:%s", base_directory)
        data_input = {
            "INFORMIX_DIR": self._informix_directory,
            "SERVER_NAME": self._informix_server_name,
            "OPERATION": operation,
            "DATABASE": database_name,
            "CLIENT_NAME": client_name,
            "INSTANCE": instance,
            "BASE_DIR": base_directory,
            "COPY_PRECEDENCE": copy_precedence,
            "TOKEN_FILE_PATH":token_file_path,
            "SERVER_NUM": server_number,
            "ARGUMENTS": arguments,
            "OS_NAME": os_name,
            "SQLHOSTS_FILE": self._instance.sql_host_file
        }

        execute_script = script_generator.run(data_input)
        output = self.machine_object.execute(
            execute_script)
        os.unlink(execute_script)
        if "dbspace_down" in operation.lower():
            return output.formatted_output
        if output.exception_message:
            raise Exception(output.exception_message)
        if output.exception:
            raise Exception(output.exception)
        return output.formatted_output

    def get_informix_server_status(self):
        """ Checks for the informix server status in client.

            Returns:
                Returns True if server is Up

                Returns False if server is down
        """
        status = self.informix_server_operation("status")
        if "On-Line" in status or "True" in status:
            return True
        return False

    def start_informix_server(self):
        """ Starts the Informix server in client.

        Raises:
            Exception:
                if unable to start server

        """
        if self.get_informix_server_status():
            self.log.info("Informix server is already started")
        else:
            self.informix_server_operation("start")
            if self.get_informix_server_status():
                self.log.info("Informix server is started")
            else:
                raise Exception("Unable to start informix server")

    def stop_informix_server(self):
        """ Stops the Informix server in client.

            Raises:
                Exception:
                    if unable to stop server

        """
        if not self.get_informix_server_status():
            self.log.info("Informix server is already stopped")
        else:
            self.informix_server_operation("stop")
            if not self.get_informix_server_status():
                self.log.info("Informix server is stopped")
            else:
                raise Exception("Unable to stop informix server")

    def bring_server_online(self):
        """ Brings the server to online from quiescent mode.

            Raises:
                Exception:
                    if unable to bring server to online mode

        """
        if self.get_informix_server_status():
            self.log.info("Informix server is already Online")
        else:
            self.informix_server_operation("online")
            if self.get_informix_server_status():
                self.log.info("Informix server is now Online")
            else:
                raise Exception("Unable to bring informix server to online")

    def mark_disabled_dbspace_down(self):
        """Prepares dbspace cvauto1 for partial restore by marking it disabled and down.
        Stop server, delete dbspace chunk file, start server and mark disabled dbspace down
            Raises:
                Exception:
                    if no dbspace was in disabled state
        """
        self.stop_informix_server()
        del_file = self.machine_object.join_path(self._instance.informix_directory, "cvauto1")
        self.log.info("Deleting file %s", del_file)
        self.machine_object.delete_file(del_file)
        self.log.info("Mark disabled dbspace as down")
        output = self.informix_server_operation("dbspace_down")
        if "IO errors" in output:
            raise Exception("Mark disabled dbspace returned {0}".format(output))

    def create_dbspace(self):
        """ Creates a dbspace inside the server.

            Returns:
                Returns True on success

            Raises:
                    Exception:
                        if unable to create DBSpace

        """
        output = self.informix_server_operation("create_dbspace")
        if "Space successfully added".lower() in output.lower():
            return True
        if "Space already exists".lower() in output.lower():
            return True
        raise Exception("Failed to create DBspace")

    def drop_dbspace(self):
        """ Drops the dbspace inside the server.

            Returns:
                Returns True on success

        """
        output = self.informix_server_operation("drop_dbspace")
        if "Space successfully dropped".lower() in output.lower():
            return True
        return False

    def cl_full_backup_entire_instance(
            self, client_name, instance, base_directory=None, token_file_path=None):
        """ Performs commandline full backup of Entire Instance.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                token_file_path (str)   -- Token file path for commandline
                job authentication

                    default: None
        """
        response = self.informix_server_operation(
            operation="cl_full_entire_instance",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            token_file_path=token_file_path)
        self.log.info("Response from Client:%s", response)

    def cl_incremental_entire_instance(
            self, client_name, instance, base_directory=None, token_file_path=None):
        """ Performs commandline level 1 incremental backup of Entire Instance.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                token_file_path (str)   -- Token file path for commandline
                job authentication

                    default: None
        """
        response = self.informix_server_operation(
            operation="cl_incremental_entire_instance",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            token_file_path=token_file_path)
        self.log.info("Response from Client:%s", response)

    def cl_inc_entire_instance_level_2(
            self, client_name, instance, base_directory=None, token_file_path=None):
        """ Performs commandline level 2 incremental backup of Entire Instance.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                token_file_path (str)   -- Token file path for commandline
                job authentication

                    default: None
        """
        response = self.informix_server_operation(
            operation="cl_incremental_entire_instance_2",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            token_file_path=token_file_path)
        self.log.info("Response from Client:%s", response)

    def cl_restore_entire_instance(
            self, client_name, instance, base_directory=None, token_file_path=None):
        """ Performs commandline restore of Entire Instance.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                token_file_path (str)   -- Token file path for commandline
                job authentication

                    default: None
        """
        response = self.informix_server_operation(
            operation="cl_restore_entire_instance",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            token_file_path=token_file_path)
        self.log.info("Response from Client:%s", response)

    def cl_full_backup_whole_system(
            self, client_name, instance, base_directory=None, token_file_path=None):
        """ Performs commandline full backup of Whole System.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                token_file_path (str)   -- Token file path for commandline
                job authentication

                    default: None
        """
        response = self.informix_server_operation(
            operation="cl_full_whole_system",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            token_file_path=token_file_path)
        self.log.info("Response from Client:%s", response)

    def cl_incremental_whole_system(
            self, client_name, instance, base_directory=None, token_file_path=None):
        """ Performs commandline level 1 incremental backup of Whole System.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                token_file_path (str)   -- Token file path for commandline
                job authentication

                    default: None
        """
        response = self.informix_server_operation(
            operation="cl_incremental_whole_system",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            token_file_path=token_file_path)
        self.log.info("Response from Client:%s", response)

    def cl_inc_whole_system_level_2(
            self, client_name, instance, base_directory=None, token_file_path=None):
        """ Performs commandline level 2 incremental backup of Whole System.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                token_file_path (str)   -- Token file path for commandline
                job authentication

                    default: None
        """
        response = self.informix_server_operation(
            operation="cl_incremental_whole_system_2",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            token_file_path=token_file_path)
        self.log.info("Response from Client:%s", response)

    def cl_restore_whole_system(
            self, client_name, instance, base_directory=None, token_file_path=None):
        """ Performs commandline restore of Whole System.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                token_file_path (str)   -- Token file path for commandline
                job authentication

                    default: None
        """
        response = self.informix_server_operation(
            operation="cl_restore_whole_system",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            token_file_path=token_file_path)
        self.log.info("Response from Client:%s", response)

    def cl_table_level_restore(
            self, client_name, instance, base_directory=None, token_file_path=None):
        """ Performs commandline table level restore.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                token_file_path (str)   -- Token file path for commandline
                job authentication

                    default: None
        """
        db_object = database_helper.Informix(
            self._hostname,
            self.server,
            self.user_name,
            self.password,
            "auto1",
            self.service)
        self.execute_query(
            db_object,
            "drop table if exists tabTableLevelRestore;",
            False)
        db_object.close()
        response = self.informix_server_operation(
            operation="table_level_restore",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            token_file_path=token_file_path)
        self.log.info("Response from Client:%s", response)

    def cl_table_level_aux_restore(
            self, client_name, instance, base_directory=None, copy_precedence=2):
        """ Performs commandline table level restore from secondary copy.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                copy_precedence (str)   -- Copy precedence of secondary copy

                    default: 2
        """
        db_object = database_helper.Informix(
            self._hostname,
            self.server,
            self.user_name,
            self.password,
            "auto1",
            self.service)
        self.execute_query(
            db_object,
            "drop table if exists tabTableLevelRestore;",
            False)
        db_object.close()
        response = self.informix_server_operation(
            operation="aux_copy_table_level_restore",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            copy_precedence=copy_precedence)
        self.log.info("Response from Client:%s", response)

    def cl_aux_copy_restore(
            self,
            client_name,
            instance,
            base_directory=None,
            copy_precedence=2):
        """ Performs commandline entire instance restore from secondary copy.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                copy_precedence (str)   -- Copy precedence of secondary copy

                    default: 2
        """
        response = self.informix_server_operation(
            operation="secondary_copy_restore",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            copy_precedence=copy_precedence)
        self.log.info("Response from Client:%s", response)

    def cl_aux_restore_whole_system(
            self,
            client_name,
            instance,
            base_directory=None,
            copy_precedence=2):
        """ Performs commandline whole instance restore from secondary copy.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                copy_precedence (str)   -- Copy precedence of secondary copy

                    default: 2
        """
        response = self.informix_server_operation(
            operation="secondary_copy_restore_whole_instance",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            copy_precedence=copy_precedence)
        self.log.info("Response from Client:%s", response)

    def cl_aux_log_only_restore(
            self,
            client_name,
            instance,
            base_directory=None,
            copy_precedence=2):
        """ Performs commandline log only restore from secondary copy.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                copy_precedence (str)   -- Copy precedence of secondary copy

                    default: 2
        """
        response = self.informix_server_operation(
            operation="secondary_copy_log_only_restore",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            copy_precedence=copy_precedence)
        self.log.info("Response from Client:%s", response)

    def cl_log_only_restore(
            self,
            client_name,
            instance,
            base_directory=None,
            token_file_path=None):
        """ Performs commandline log only restore.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                token_file_path (str)   -- Token file path for commandline
                job authentication

                    default: None
        """
        response = self.informix_server_operation(
            operation="log_only_restore",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            token_file_path=token_file_path)
        self.log.info("Response from Client:%s", response)

    def cl_physical_restore(
            self,
            client_name,
            instance,
            base_directory=None,
            token_file_path=None):
        """ Performs commandline physical restore.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                token_file_path (str)   -- Token file path for commandline
                job authentication

                    default: None
        """
        response = self.informix_server_operation(
            operation="physical_restore",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            token_file_path=token_file_path)
        self.log.info("Response from Client:%s", response)

    def cl_physical_whole_sys_restore(
            self,
            client_name,
            instance,
            base_directory=None,
            token_file_path=None):
        """ Performs commandline physical restore of whole system.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                token_file_path (str)   -- Token file path for commandline
                job authentication

                    default: None
        """
        response = self.informix_server_operation(
            operation="physical_restore_whole_system",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            token_file_path=token_file_path)
        self.log.info("Response from Client:%s", response)

    def cross_machine_restore(
            self,
            operation,
            client_name,
            instance,
            server_number,
            arguments=None,
            base_directory=None,
            token_file_path=None):
        """ Performs commandline cross machine restore of Entire Instance/Whole System

            Args:
                operation       (str)   -- Specifies which restore to perform

                        Accepted Values:

                                WHOLE_SYSTEM/ENTIRE_INSTANCE

                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance name of the client

                server_number   (str)   -- Informix server number
                as specified in onconfig file of source

                arguments       (str)   -- extra arguments to be passed along
                with onbar -r command

                    default: None

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                token_file_path (str)   -- Token file path for commandline
                job authentication

                    default: None

            Returns:
                Returns script execution output on success

        """
        response = self.informix_server_operation(
            operation=operation + "_CROSS_MACHINE",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            token_file_path=token_file_path,
            server_number=server_number,
            arguments=arguments)
        self.log.info("Response from Client:%s", response)

    def list_dbspace(self):
        """ Lists all dbspaces in the server

            Returns:
                Returns list of dbspaces in server

            Raises:
                Exception:
                    if unable to list dbspaces
        """
        return self.informix_db.list_dbspace()

    def create_database(self,
                        database_name):
        """ Creates a database inside the dbspace.

            Args:

                database_name   (str)   -- Database name to create

            Returns:
                Returns True on success

            Raises:
                Exception:
                    if unable to create Database

        """
        self.informix_server_operation("create_db", database_name)
        if self.informix_db.check_if_db_exists(database_name):
            self.log.info("Database %s created successfully", database_name)
            return True
        raise Exception("Failed to create database")

    def drop_database(self,
                      database_name):
        """ Drops a database if it exists.

            Args:

                database_name   (str)   -- Database name to delete

            Returns:
                Returns True on success

            Raises:
                Exception:
                    if unable to drop Database
        """
        self.log.info("Dropping database %s", database_name)
        return self.informix_db.drop_database(database_name)

    def get_database_list(self):
        """ Gets all the database names in the server.

            Returns:
                Returns database list

            Raises:
                BaseException:
                    if unable get the database list
        """
        return self.informix_db.get_database_list()

    def check_if_db_exists(self,
                           database):
        """ Checks if the specified database exist.

            Args:
                database     (str)   -- Database name to check

            Returns:
                Returns True if DB exists

                Returns False if DB doesn't exist
        """
        database_list = []
        database_list = self.informix_db.get_database_list()
        if database in database_list:
            return True
        return False

    def create_table(self,
                     table_name,
                     informix_db=None,
                     database=None):
        """ Creates a table inside a database.

            Args:
                table_name  (str)   -- Table name to create

                informix_db (obj)   -- Informix object from database_helper

                    default: None

                database    (str)   -- Database name

                    default: None

            Raises:
                BaseException:
                    if unable create table
        """
        try:
            if informix_db is None:
                # Establish the connection with informix db
                informix_db = database_helper.Informix(
                    self._hostname,
                    self.server,
                    self.user_name,
                    self.password,
                    database,
                    self.service)
            query = "create table %s (ANAME varchar(25),BNAME \
            varchar(25),CNAME varchar(25),DNAME varchar(25),\
            Ename varchar(25),FNAME varchar(25));" % (table_name)
            self.execute_query(informix_db, query, False)

        except BaseException:
            self.log.info("Exception in creating table")
            raise Exception("Unable to create the table")

    def insert_rows(self,
                    table_name,
                    informix_db=None,
                    database=None,
                    scale=13):
        """ Inserts test data inside a table.

            Args:
                table_name  (str)   -- Table name to populate data

                informix_db (obj)   -- Informix object from database_helper

                    default: None

                database    (str)   -- Database name

                    default: None

                scale       (int)   -- This value specifies the number of rows\
                                        to be inserted in the database. For value\
                                        n of scale, 2^n rows are inserted in the db.

                    default: 13

            Raises:
                BaseException:
                        if unable create table
        """
        try:
            if informix_db is None:
                # Establish the connection with informix db
                informix_db = database_helper.Informix(
                    self._hostname,
                    self.server,
                    self.user_name,
                    self.password,
                    database,
                    self.service)
            query = "insert into %s values('test_data1',\
            'test_data2','test_data3','test_data4','test_data5',\
            'test_data6')" % (table_name)
            self.execute_query(informix_db, query, True)

            while scale:
                scale -= 1
                query = "insert into %s select * from %s" % (
                    table_name, table_name)
                self.execute_query(informix_db, query, True)

            self.log.info("database is populated with test data")

        except BaseException:
            self.log.info("Exception in populate table")
            raise Exception("Unable to insert data in the table")

    def populate_data(self,
                      scale=None):
        """ Populates the Informix server for testing.

            Args:
                scale       (list)  -- This list consists the number of\
                                        database/table/rows to be created in\
                                        [database,tables,rows] format

                    default: None

            Raises:
                BaseException:
                    if unable to create dbspace

                    if unable to create database
        """
        # Delete existing automation test data
        self.delete_test_data()

        if scale is None:
            scale = [10, 10, 12]
        self.log.info("creating the dbspace:cvauto1")
        response = self.create_dbspace()
        if not response:
            raise Exception("Unable to create dbspace")

        self.log.info("DBspace is created")

        if isinstance(scale, str):
            temp = scale.split(',')
            scale = list()
            scale.append(int(temp[0].split("[")[1].strip()))
            scale.append(int(temp[1].strip()))
            scale.append(int(temp[2].split("]")[0].strip()))

        self.log.info("creating databases inside the dbspace")

        for i in range(0, scale[0]):
            database_name = f"auto{str(i + 1)}_{str(int(time.time()))}"
            if "auto1_" in database_name:
                database_name = "auto1"
            self.log.info("creating database:%s", database_name)
            response = self.create_database(database_name)
            if not response:
                raise Exception("Unable to create database")
            self.log.info("database %s is created", database_name)
            self.log.info("creating tables in %s database", database_name)

            database_object = database_helper.Informix(self._hostname,
                                                       self.server,
                                                       self.user_name,
                                                       self.password,
                                                       database_name,
                                                       self.service)

            for j in range(0, scale[1]):
                table_name = "tab" + str(j + 1)
                self.log.info(
                    "Creating a table %s inside %s database",
                    table_name,
                    database_name)
                self.create_table(table_name,
                                  informix_db=database_object)

                self.insert_rows(table_name,
                                 informix_db=database_object,
                                 scale=scale[2])
            self.log.info("Closing the connection to this database")
            database_object.close()

    def delete_test_data(self):
        """ Deletes the data generated for testing.

            Raises:
                BaseException:
                    if unable to delete test data
        """
        dbspace_list = self.list_dbspace()
        if "cvauto1" in dbspace_list:
            self.log.info("Dropping all test databases")
            database_list = self.informix_db.get_database_list()
            dbname_starting_with_auto = [x for x in database_list if x.startswith("auto")]
            for dbname in dbname_starting_with_auto:
                self.informix_db.drop_database(dbname)
            self.log.info("dropping the dbspace:cvauto1")
            response = self.drop_dbspace()
            if not response:
                raise Exception("Unable to drop dbspace")
        self.log.info("DBspace is dropped")
        self.log.info("All the test data is cleared")

    def collect_meta_data(self):
        """ Collects the meta data of a database server

            Raises:
                BaseException:
                        if unable to collect meta data
        """
        # Get all the database list
        database_list = self.informix_db.get_database_list()
        self.log.info("Database list: %s", database_list)
        meta_data = {}
        for database in database_list:
            database_object = database_helper.Informix(self._hostname,
                                                       self.server,
                                                       self.user_name,
                                                       self.password,
                                                       database,
                                                       self.service)
            query = "select tabname from systables where tabname like 'tab%';"

            table_list = self.execute_query(database_object, query, False).rows
            table_list_new = []
            for i in table_list:
                table_list_new.append(i[0])
            table_size_map = {}
            for table in table_list_new:
                query = "select count(*) from %s;" % (table)
                table_size = self.execute_query(
                    database_object, query, False).rows
                table_size = int(table_size[0][0])
                table_size_map[table] = table_size
            meta_data[database] = table_size_map
        self.log.info("META DATA=%s", meta_data)
        return meta_data

    def row_count(self,
                  table_name,
                  informix_db=None,
                  database=None):
        """ Returns number of rows in the table specified.

            Args:
                table_name  (str)   -- Table name to count the rows

                informix_db (obj)   -- Informix object from database_helper

                    default: None

                database    (str)   -- Database name

                    default: None

            Returns:
                Returns number of rows in the table

            Raises:
                BaseException:
                    if unable get row count of table
        """
        if informix_db is None:
            # Establish the connection with informix db
            informix_db = database_helper.Informix(
                self._hostname,
                self.server,
                self.user_name,
                self.password,
                database,
                self.service)
        return informix_db.row_count(table_name)

    def execute_query(self, informix_db_object, query, commit=True):
        """Runs the query on informix db.

            Args:

                informix_db (obj)   -- Informix object from database_helper

                query       (str)   -- Query to be run in informix database

                commit      (bool)  -- Commit flag for the query

                    default: True

            Returns:
                Returns dbresponse object
        """
        return informix_db_object.execute(query, commit=commit)

    def reconnect(self):
        """Re-Connects to informix DB"""
        self.informix_db = database_helper.Informix(
            self._hostname,
            self.server,
            self.user_name,
            self.password,
            "sysmaster",
            self.service)

    def get_last_log_number(self, job_id):
        """Gets number of the last informix log backed up

                Args:
                    job_id   (str)   -- Backup Job ID to get the last log number

                Returns:
                    Returns last log number backed up for the given job

                Raises:
                    Exception:
                        if failed to get the last log number from cs db
        """
        query = "select name from archfile where jobid={0} and fileType=4".format(
            job_id)
        self._csdb.execute(query)
        cur = self._csdb.fetch_all_rows()

        if cur:
            last_log_file_name = cur[len(cur)-1][0]
            last_log_file_name = last_log_file_name.split(".")[0]
            if "unix" in self.machine_object.os_info.lower():
                last_log_file_name = last_log_file_name.split("/")[-1]
            else:
                last_log_file_name = last_log_file_name.split('\\')[-1]
            return int(last_log_file_name)
        raise Exception("Failed to get the last log number from cs db")

    def get_afileid(self, job_id, file_type):
        """Gets afile id of a backup object for given job id and file type
                Args:
                    job_id (int)  -- Backup Job ID to fetch afile ids of the job
                Returns:
                    afileid (int) -- id for first record from archfile table
                                     for a given job and file type
                Raises:
                    Exception:
                        If no archfile id is retrieved for given job id and file type
        """
        query = "select id from archfile where jobid={0} and fileType={1}".format(
            job_id, file_type)
        self._csdb.execute(query)
        cur = self._csdb.fetch_all_rows()
        if cur:
            cur.reverse()
            afileid = cur[len(cur)-1][0]
            return int(afileid)
        raise Exception("Failed to get the arch file ID from cs db")

    def cross_machine_operations(
            self,
            destination_helper_object):
        """fetches all the necessary information required to start
        cross machne restore

            Args:
                destination_helper_object       (obj)   -- informix helper class object of
                destination client

            Returns:

                Returns a list containing details reagarding informix servers

                        [
                        source_server_number,
                        destination_server_number,
                        dest_onconfig_path,
                        dest_oncfg_path,
                        dest_ixbar_path,
                        source_onconfig_path]

        """
        dest_etc_folder_location = destination_helper_object.machine_object.join_path(
            destination_helper_object._instance.informix_directory, "etc")
        self.log.info("ETC folder path in destination is: %s", dest_etc_folder_location)
        source_etc_folder_location = self.machine_object.join_path(
            self._instance.informix_directory, "etc")
        self.log.info("ETC folder path in source is: %s", source_etc_folder_location)
        dest_onconfig_path = destination_helper_object.machine_object.join_path(
            dest_etc_folder_location,
            destination_helper_object._instance.on_config_file)
        self.log.info("onconfig file path in destination is: %s", dest_onconfig_path)
        source_onconfig_path = self.machine_object.join_path(
            source_etc_folder_location,
            self._instance.on_config_file)
        self.log.info("onconfig file path in source is: %s", source_onconfig_path)
        self.log.info("Fetching source and destination server number")
        command_1 = "awk '/^(\s*)SERVERNUM/{ print $2 }' %s" % (source_onconfig_path)
        command_2 = "awk '/^(\s*)SERVERNUM/{ print $2 }' %s" % (dest_onconfig_path)
        if "windows" in self.machine_object.os_info.lower():
            command_1 = (
                "(Get-Content \"%s\" | "
                "Where-Object {$_ -match \"^SERVERNUM.*\"} | "
                "Foreach {$Matches[0]}).split()[1]") % (source_onconfig_path)
            command_2 = (
                "(Get-Content \"%s\" | "
                "Where-Object {$_ -match \"^SERVERNUM.*\"} | "
                "Foreach {$Matches[0]}).split()[1]") % (dest_onconfig_path)
        source_server_number = self.machine_object.execute_command(
            command_1).formatted_output
        destination_server_number = destination_helper_object.machine_object.execute_command(
            command_2).formatted_output
        self.log.info("Source Server number: %s", source_server_number)
        self.log.info("Destination Server number: %s", destination_server_number)
        dest_ixbar_path = destination_helper_object.machine_object.join_path(
            dest_etc_folder_location,
            "ixbar.{0}".format(destination_server_number))
        self.log.info("ixbar file path in destination is: %s", dest_ixbar_path)

        dest_oncfg_path = destination_helper_object.machine_object.join_path(
            dest_etc_folder_location,
            "oncfg_{0}.{1}".format(
                destination_helper_object._instance.instance_name,
                destination_server_number))
        self.log.info("oncfg file path in destination is: %s", dest_oncfg_path)
        return [
            source_server_number,
            destination_server_number,
            dest_onconfig_path,
            dest_oncfg_path,
            dest_ixbar_path,
            source_onconfig_path]

    def cross_config_only_restore(
            self,
            destination_helper_object,
            dest_onconfig_path):
        """performs cross machine restore of config files and modifies
        replaced onconfig file as required for restore

            Args:

                destination_helper_object       (obj)   -- informix helper class object of
                destination client

                dest_onconfig_path              (str)   -- Path to onconfig file in
                destination machine

        """
        self.log.info("Stopping destination informix server to perform restore")
        destination_helper_object.stop_informix_server()
        self.log.info(
            "Copying the config files from source to destination"
            " using GUI restore")
        self.log.info("*******Starting  cross machine config files restore Job**********")
        job = self._instance.restore_out_of_place(
            self.list_dbspace(),
            destination_helper_object.machine_object.machine_name,
            destination_helper_object._instance.instance_name,
            physical_restore=False,
            logical_restore=False)

        self.log.info(
            "started the cross machine config files restore Job with Id:%s",
            job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run data only restore job with error: {1}".format(
                    job.delay_reason
                )
            )
        self.log.info("Cross machine config files Restore job is now completed")

        command_1 = "sed -i \"s/^DBSERVERALIASES.*/DBSERVERALIASES/g\" {0}".format(
            dest_onconfig_path)
        if "windows" in self.machine_object.os_info.lower():
            command_1 = (
                "(Get-Content \"%s\") | "
                "Foreach-Object {$_ -replace \"^DBSERVERALIASES.*\",\"DBSERVERALIASES\"} "
                "| Set-Content \"%s\"") % (dest_onconfig_path, dest_onconfig_path)
        self.log.info("adding proper server alias in oncongig file")
        destination_helper_object.machine_object.execute_command(command_1)

    def get_rename_dbspace_command(
            self,
            source_onconfig_path,
            dest_onconfig_path,
            dest_helper_object):
        """returns the rename command string to be used for the cross machine
        restore between two servers with different dbspace structures

                Args:
                source_onconfig_path           (str)  -- Path to onconfig file in source machine

                dest_onconfig_path             (str)  -- Path to onconfig file in destination
                machine

                dest_helper_object             (obj)  -- informix helper class object of
                destination client

            Returns:

                Returns a string containing rename command

        """
        command_1 = "awk '/^(\s*)ROOTPATH/{ print $2 }' %s" % (source_onconfig_path)
        command_2 = "awk '/^(\s*)ROOTPATH/{ print $2 }' %s" % (dest_onconfig_path)
        if "windows" in self.machine_object.os_info.lower():
            command_1 = (
                "(Get-Content \"%s\" | "
                "Where-Object {$_ -match \"^ROOTPATH.*\"} | "
                "Foreach {$Matches[0]}).split()[1]") % (source_onconfig_path)
            command_2 = (
                "(Get-Content \"%s\" | "
                "Where-Object {$_ -match \"^ROOTPATH.*\"} | "
                "Foreach {$Matches[0]}).split()[1]") % (dest_onconfig_path)
        source_root_path = self.machine_object.execute_command(
            command_1).formatted_output.split("rootdbs")[0]
        destination_root_path = dest_helper_object.machine_object.execute_command(
            command_2).formatted_output.split("rootdbs")[0]
        self.log.info("Informix source server rootpath: %s", source_root_path)
        self.log.info("Informix destination server rootpath: %s", destination_root_path)
        if source_root_path == destination_root_path:
            raise Exception("Rootpath of destination and source server is same."
                            "This testcase is to check if cross machine restore"
                            " works between two servers whose dbspace paths"
                            " are different.")
        self.log.info("Constructing the command for restore.")
        restore_command = "-rename -p {0}rootdbs -o 0 -n {1}rootdbs -o 0".format(
            source_root_path,
            destination_root_path)
        if 'windows' in self.machine_object.os_info.lower():
            restore_command = "-rename -p {0}rootdbs.000 -o 0 -n {1}rootdbs.000 -o 0".format(
                source_root_path,
                destination_root_path)
        for db_space in self.list_dbspace():
            if not db_space.lower() in ["cvauto1", "rootdbs"]:
                restore_command = "{0} -rename -p {1}{4}_{3}_p_1 -o 0 -n {2}{5}_{3}_p_1 -o 0".format(
                    restore_command,
                    source_root_path,
                    destination_root_path,
                    db_space,
                    self._instance.instance_name,
                    dest_helper_object._instance.instance_name)
        restore_command = "\"{0} -rename -p {1} -o 0 -n {2} -o 0\"".format(
            restore_command,
            self.machine_object.join_path(self._instance.informix_directory, "cvauto1"),
            dest_helper_object.machine_object.join_path(
                dest_helper_object._instance.informix_directory,
                "cvauto1"))
        self.log.info("Restore command being passed: %s", restore_command)
        return restore_command

    def get_command_line_job(self):
        """Finds the commandline job id launched by cl jobs and returns job object

            Returns:

                Returns job object

        """
        command = "tac {0}/IFXXBSA.log | grep -m 1 -oh 'Got the Job Id as:[0-9]*'".format(
            self.machine_object.client_object.log_directory)
        if "windows" in self.machine_object.os_info.lower():
            command = ("(Select-String -Path \"%s\IFXXBSA.log\" -Pattern"
                       " 'Got the Job Id as:[0-9]*' | foreach {$_.Matches.Value})[-1]") %(
                           self.machine_object.client_object.log_directory)
        job_id = self.machine_object.execute_command(command).formatted_output.split(
            "Id as:")[-1].strip()
        return self._commcell.job_controller.get(job_id)

    def cl_switch_log(
            self,
            client_name,
            instance,
            base_directory=None,
            token_file_path=None):
        """ Performs commandline switch log operation.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                token_file_path (str)   -- Token file path for commandline
                job authentication

                    default: None
        """
        response = self.informix_server_operation(
            operation="switch_log",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            token_file_path=token_file_path)
        self.log.info("Response from Client:%s", response)

    def cl_log_only_backup(
            self,
            client_name,
            instance,
            base_directory=None,
            token_file_path=None):
        """ Performs commandline log only backup.

            Args:
                client_name     (str)   -- Name of the Informix Client

                instance        (str)   -- Instance of the client

                base_directory  (str)   -- Commvault Base directory path of client

                    default: None

                token_file_path (str)   -- Token file path for commandline
                job authentication

                    default: None
        """
        response = self.informix_server_operation(
            operation="log_only_backup",
            client_name=client_name,
            instance=instance,
            base_directory=base_directory,
            token_file_path=token_file_path)
        self.log.info("Response from Client:%s", response)

    def drop_table(self, table_name, database_name):
        """ Drops the table from specified database

            Args:
                table_name          (str)   -- Name of the table

                database_name       (str)   -- Database Name

        """
        self.log.info("Creating database object for db: %s", database_name)
        database_helper.Informix(
            self._hostname,
            self.server,
            self.user_name,
            self.password,
            database_name,
            self.service).execute(
                "drop table if exists %s cascade;" % (table_name),
                commit=True)

    @property
    def base_directory(self):
        """ Returns Base directory of the client machine """
        return self.machine_object.join_path(
            self.machine_object.client_object.install_directory,
            "Base")

    def is_log_backup_to_disk_enabled(self):
        """ Method to check if log backup to disk feature is enabled
        for instance or not

        Returns: True if log backup to disk is enabled. False Otherwise

        """
        query = "select * from APP_InstanceProp where componentNameId="\
            f"{self._instance.instance_id} and attrName='Dump Sweep Schedule' and modified=0"
        self._csdb.execute(query)
        cur = self._csdb.fetch_all_rows()
        if cur:
            if len(cur[0][0]) == 0:
                return False
            return True
        raise Exception("Failed to check log backup to disk status")

    def run_sweep_job_using_regkey(self, media_agent=None):
        """ Sets SweepStartTime regkey and waits for the sweep job to finish

            Args:
                media_agent(str)   -- Name of the media agent where logs are dumped
        """
        cli_subclient = self._instance.backupsets.get('default').subclients.get('(command line)')
        after_two_mins = datetime.now() + timedelta(minutes=2)
        hours = int(after_two_mins.hour)
        mins = int(after_two_mins.minute)
        self.log.info("Setting SweepStartTime registry Key on CS")
        if media_agent:
            self.log.info("Setting SweepStartTime registry key on MA")
            media_agent_client_obj = self._commcell.clients.get(media_agent)
            media_agent_client_obj.add_additional_setting(
                f"InformixAgent/Sweep/{cli_subclient.subclient_id}",
                "SweepStartTime",
                "STRING",
                f"{hours}:{mins}")
        else:
            self.log.info("Setting SweepStartTime registry Key on CS")
            self._commcell.add_additional_setting(
                f"InformixAgent/Sweep/{cli_subclient.subclient_id}",
                "SweepStartTime",
                "STRING",
                f"{hours}:{mins}")
        try:
            self.log.info("Sleeping for 3 mins before checking sweep job")
            time.sleep(180)
            count = 15
            dbhelper = DbHelper(self._commcell)
            while count:
                count -= 1
                last_job = dbhelper._get_last_job_of_subclient(cli_subclient)
                if last_job:
                    self.log.info("Checking if the job ID:%s is sweep job", last_job)
                    job_obj = self._commcell.job_controller.get(last_job)
                    if "(command line)" in job_obj.subclient_name.lower() and \
                            "log commit" in job_obj.backup_level.lower():
                        break
                self.log.info("Sleeping for 1 minute")
                time.sleep(60)
            if not count:
                raise Exception("Sweep job did not trigger in 15 mins")
            self.log.info("Sweep job:%s", job_obj.job_id)
        except Exception as exp:
            self.log.error("Unable to trigger sweep job")
            raise Exception(exp)
        finally:
            if media_agent:
                self.log.info("Deleting SweepStartTime registry Key from MA")
                media_agent_client_obj.delete_additional_setting(
                    f"InformixAgent/Sweep/{cli_subclient.subclient_id}",
                    "SweepStartTime")
            else:
                self.log.info("Deleting SweepStartTime registry Key from CS")
                self._commcell.delete_additional_setting(
                    f"InformixAgent/Sweep/{cli_subclient.subclient_id}",
                    "SweepStartTime")
            self.log.info(
                "SweepStartTime registry key is deleted Successfully")

    def get_child_jobs(self, parent_job):
        """ Method to get the list of child jobs for a parent job
        Args:
            parent_job(int) -- job id of the parent backup
        Returns:
            List of child jobs linked to the parent job
        """
        query = f"select childJobId from JMJobDataLink where parentJobId = {parent_job}"
        self.log.info("QUERY: %s", query)
        self._csdb.execute(query)
        cur = self._csdb.fetch_all_rows()
        self.log.info("RESULT: %s", cur)
        if cur:
            return [int(row[0]) for row in cur]
        raise Exception("There are no child jobs for this backup")

    def create_sweep_schedule_policy(self, name="informix_sweep_schedule", association=None, sweep_time=24):
        """method to create sweep schedule policy

        Args:
            name    (str)       -- Name of the schedule policy

            association (list)  -- Association to the schedule policy
                default: None (automatically associated to instance level)

                format:
                    association = [{
                                    "clientName": client_name,
                                    "backupsetName": backupsetName,
                                    "subclientName": subclientName,
                                    "instanceName": instanceName,
                                    "appName": "Informix"
                                }]

            sweep_time  (int)   --  Frequency of sweep job (within 1 to 24)
                default: 24

        """
        pattern = [{'name': 'Dummy_name',
                    'pattern': {"freq_type":
                                    'automatic',
                                "use_storage_space_ma": True,
                                "sweep_start_time": sweep_time*3600
                                }}]
        types = [{"appGroupName": "Informix"}]
        if not association:
            association = [{
                "clientName": self._instance._agent_object._client_object.client_name,
                "instanceName": self._instance.instance_name,
                "appName": "Informix"
            }]
        self._commcell.schedule_policies.add(
            name=name, policy_type='Data Protection',
            associations=association, schedules=pattern, agent_type=types)
