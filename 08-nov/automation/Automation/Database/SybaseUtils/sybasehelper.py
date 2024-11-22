# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing sybase operations

    This File has two classes : SybaseHelper , SybaseCVHelper

    SybaseHelper: Helper to perform operations/manipulations on sybase application

    __init__()                          --  initializes SybaseHelper object

    sybase_helper_cleanup()             --  Removes temp directories created
                                            during sybase helper object initialization

    get_sybase_user_password()          --  Return sybase SA username
                                            based on client and instance parameter

    get_local_user_password()           --  Returns local admin user password
                                            configured in sybase instance

    execute_sybase_command()            --  Creates temp file with sybase
                                            command and execute the same on remote machine

    execute_sybasehadr_command()        --  Creates temp file with sybase
                                            command and execute the same on remote machine

    create_sybase_device()              --  Creates device
                                            in given sybase instance

    drop_sybase_device()                --  Drops device in given sybase instance

    create_sybase_database()            --  Creates database
                                            inside given sybase instance

    get_database_list()                 --  Get list of databases
                                            in given sybase instance

    get_table_list()                    --  Fetch table list for given database

    get_table_content()                 --  Gets contents of given
                                            table in given database

    check_database_state()              --  To bring sybase databases online

    is_system_database()                --  To check if given
                                            database is sybase system database

    get_logfile_free_size()             --  To get log file free
                                            size for sybase database

    check_if_table_exists()             --  To check if given tables
                                            exists under given database

    check_if_database_exists()          --  To check if given
                                            database exists

    drop_sybase_table()                 --  Drops table in given
                                            database in sybase instance

    create_sybase_table()               --  Creates table in
                                            given database and insert data into it

    insert_data()                       --  Inserts data to given
                                            table inside given database name

    deactivate_sybase_hadr_admin        --  To Deactivate Sybase Hadr Admin

    shutdown_sybase_server()            --  To shutdown sybase instance

    shutdown_with_no_wait()             --  To shutdown sybase server with no wait

    shutdown_sybasehadr_rma()           --  To shutdown Sybase Hadr RMA server

    shutdown_sybasehadr_rep()           --  To shutdown Sybase Hadr Replication Server

    is_server_running()                 --  Checks the status of sybase server

    get_device_path()                   --  Fetch base device
                                            path for given sybase instance

    get_device_name()                   --  Returns list of devices for given database

    drop_sybase_database()              --  Drop database inside
                                            given sybase instance

    set_cumulative()                    --  Configure incremental dump
                                            settings on given database

    remove_user_db()                    --  To remove user database from other
                                            subclient to avoid duplicate entry in partial restore

    enable_encryption_for_db()          --  Enables encryption for a user database


    SybaseCVHelper : Helper to perform operations involving commvault and application


    sybase_populate_data()                      --  To populate one database,
                                                    one table inside that database and
                                                    populate content to the user table

    single_table_populate()                     --  To populate single
                                                    table with data in given database

    get_all_database_tables()                   --  To return dictionary containing
                                                    all tables lists of all sybase databases

    comparing_dict_of_list ()                   --  To compare two dictionary of lists items


    sybase_cleanup_test_data()                  --  To cleanup the test
                                                    database and tables inside it

    cleanup_tables()                            --  Cleanup list of tables in given database

    sybase_delete_database_from_subclient()     --  To delete temp database
                                                    entry from subclient content

    enable_fs_based_snap()                      --  Enables intellisnap with
                                                    Fs based backup copy option

    enable_dump_based_snap()                    --  Enables dump based
                                                    backup copy with required options

    snap_backup()                               --  To initiate snap sybase
                                                    backup and validate the same


    get_storage_policy()                        --  To get storage policy
                                                    for default subclient in given
                                                    sybase instance


    backup_and_validation()                     --  To launch requested
                                                    backup job and validate the same

    concurrent_backup_based_restore()           --  To perform two restores
                                                    based on concurrent log backups

    drop_user_databases()                       --  Drops list of given user databases

    restore_to_disk_and_validation()            --  Performs restore to disk
                                                    [Application free restore]
                                                    and validates the restore


    directive_file()                            --  Creates ondemand
                                                    input file on remote client

    sybase_full_restore()                       --  Performs Full Sybase server restore


    single_database_restore()                   --  Performs single database restore
                                                    with provided parameters

    table_validation()                          --  Compares table list and Table content lists

    get_end_time_of_job()                       --  Returns end time of given
                                                    job with one minute added

    create_sybase_subclient()                   --  Creates subclient with given
                                                    content under given sybase instance

    backup_syntax_check()                       --  Checks sybase syntax for given backup job

    encrypted_db_backup_syntax                  --  Checks if encryption keys were backed up successfully

"""
import time
import datetime
import threading
from AutomationUtils import logger
from AutomationUtils import cvhelper
from AutomationUtils import machine
from AutomationUtils import constants
from AutomationUtils import idautils


class SybaseHelper(object):
    """Helper class to perform Sybase operations"""

    def __init__(self,
                 commcell,
                 instance,
                 client,
                 hadr=False):
        """
        Initializes sybasehelper object

            Args:
                commcell  (object)     --  commcell object on which operations
                                           to be performed

                instance  (object)     --  sybase instance object on
                                           which operations to be performed

                client    (object)     --  sybase remote client object on
                                           which operations to be performed
        """

        self.log = logger.get_log()
        self.commcell = commcell
        self.instance = instance
        self.client = client
        self.client_name = client.client_name
        self.instance_name = instance.instance_name
        self.controller_object = machine.Machine()
        self.machine_object = machine.Machine(self.client)
        self.csdb = None
        self.platform = self.machine_object.os_info
        if hadr:
            node_props = self.instance.get_node_properties(clientId=self.client.client_id)

            self.sybase_server = node_props.get('sybaseProps', {}).get('backupServer')[:-3]
            self.sybase_home = node_props.get('sybaseProps', {}).get('sybaseHome')
            self.sybase_sa_username = node_props.get('sybaseProps', {}).get('saUser').get('userName')
        else:
            self.sybase_server = self.instance.instance_name
            self.sybase_home = instance.sybase_home
            self.sybase_sa_username = instance.sa_user

        self.sybase_sa_userpassword = None
        self.cv_home_path = client.install_directory
        if self.platform.lower() == 'windows':
            self.sybasecmd = 'isql '
        else:
            self.sybasecmd = """. {0}/SYBASE.sh;isql""".format(
                self.sybase_home)
        self.thread_id = str(threading.get_ident())
        self.temp_folder_name = """SybaseTemp_{0}""".format(self.thread_id)
        self.common_dir_path = self.controller_object.join_path(constants.TEMP_DIR,
                                                                self.temp_folder_name)

        self.common_directory_creation = self.controller_object.create_directory(
            self.common_dir_path, force_create=True)
        self.remote_path = self.machine_object.join_path(self.cv_home_path,
                                                         self.temp_folder_name)

        self.machine_object.create_directory(self.remote_path, force_create=True)

    def sybase_helper_cleanup(self):
        """
        To remove temp directories created
        during sybase helper object initialization
        """
        self.controller_object.remove_directory(self.common_dir_path)
        self.machine_object.remove_directory(self.remote_path)

    def get_sybase_user_password(self, hadr=False):
        """
        Returns sybase SA Password for given sybase instance

        Args:
            hadr(bool)  --  True if instance is Sybase hadr

        Returns:
            (str)       --      returns sybase SA user password

        Raises:
            Exception
                if failed to get password from csdb

        """
        if hadr:
            query2 = (f"select attrVal from APP_DBClusterInstanceProp where componentNameId = (select id from "
                      f"APP_DBClusterInstance where clientId = {self.client.client_id}) and attrName like 'SYBASE SA "
                      f"password'")
        else:
            query2 = ("select attrVal from app_instanceprop where(componentnameid={0} "
                      "and attrName in ('SYBASE password'))".format(self.instance.instance_id))
        self.csdb.execute(query2)
        cur = self.csdb.fetch_one_row()
        if cur:
            sybase_sa_userpassword = cur[0]
        else:
            raise Exception(
                "Failed to get the sybase user password"
                "for given instance from commserve database")
        sybase_sa_userpassword = cvhelper.format_string(
            self.commcell, sybase_sa_userpassword)
        return sybase_sa_userpassword

    def get_local_user_password(self):
        """
        Returns local admin user password configured in sybase instance

            Returns:
                (str)       --      returns local admin user password for sybase instance

            Raises:
                Exception
                    if failed to get password from csdb

        """
        query2 = ("select attrVal from app_instanceprop where(componentnameid={0} "
                  "and attrName in ('SYBASE NT password'))".format(self.instance.instance_id))
        self.csdb.execute(query2)
        cur = self.csdb.fetch_one_row()
        if cur:
            local_admin_password = cur[0]
        else:
            raise Exception(
                "Failed to get the sybase user password"
                "for given instance from commserve database")
        local_admin_password = cvhelper.format_string(self.commcell,
                                                      local_admin_password)
        return local_admin_password

    def execute_sybase_command(self, cmd, temp_input_file_name):
        """
        Creates temp file with sybase command
        and execute the same on remote machine and returns the output

            Args:
                cmd                     (str)   --  sybase command to be
                                                    executed on remote client


                temp_input_file_name    (str)   --  temporary input file to be created
                                                    on controller and copied to remote machine

            Returns:
                (object)      -   object of output class for given command

            Raises:
                Exception:

                    if failed to copy the file to remote machine

                    if login to sybase server fails

                    if unable to open input file

        """
        exit_cmd = "go\nexit\n"
        sybase_server_name = self.sybase_server
        local_filename = self.controller_object.join_path(self.common_dir_path,
                                                          temp_input_file_name)
        self.log.info("Sybase Command : %s", cmd)

        # Create local temp file and write the the command on the controller to local file
        self.log.info(
            "Create local temp file and write the"
            " command on the controller to local file")
        platform = self.machine_object.os_info
        if platform.lower() == 'unix':
            fp = open(local_filename, 'w', newline='\n')
        else:
            fp = open(local_filename, 'w')
        if cmd:
            fp.write(cmd)
            fp.write(exit_cmd)
        else:
            cmd = "exit\n"
            fp.write(cmd)
        fp.close()

        # Copy the local file from controller to remote machine
        self.log.info("Copy the local file from controller to remote machine")
        copy_status = self.machine_object.copy_from_local(
            local_filename, self.remote_path)
        self.log.info("copy_status :%s", copy_status)
        if not copy_status:
            raise Exception("Failed to copy file to remote machine.Exiting")

        # Execute the sybase command on remote machine using copied temp file
        remote_file = self.machine_object.join_path(self.remote_path, temp_input_file_name)
        self.log.info(
            "Execute the sybase command on remote machine using copied temp file")
        cmd = """{0} -U {1} -P {2} -S {3} -i \"{4}\"""".format(
            self.sybasecmd,
            self.sybase_sa_username,
            self.sybase_sa_userpassword,
            sybase_server_name,
            remote_file)
        self.log.info(cmd)
        cmd_output = self.machine_object.execute_command(cmd)

        # Check if login failure happened or not
        if cmd_output.output.find("Login failed.") >= 0:
            raise Exception("Login to Sybase server failed : {0}".format(cmd_output.output))

        # Checking if input file is valid for sybase command execution
        if (cmd_output.output).find("Unable to open input file") >= 0:
            time.sleep(20)
            cmd_output = self.machine_object.execute_command(cmd)
            if (cmd_output.output).find("Unable to open input file") >= 0:
                raise Exception(
                    "Failed to open the input file given to sybase ISQL command. Exiting ")

        # Cleanup temp file on controller and on remote machine
        self.log.info("Cleanup temp file on controller and on remote machine")
        self.controller_object.delete_file(local_filename)
        file_name = self.machine_object.join_path(self.remote_path, temp_input_file_name)
        self.machine_object.delete_file(file_name)
        self.log.info("output : %s", cmd_output.output)
        return cmd_output

    def execute_sybasehadr_command(self, port, cmd, temp_input_file_name):
        """
        Creates temp file with sybase command
        and execute the same on remote machine and returns the output

            Args:
                port                    (int)  -- server port
                cmd                     (str)   --  sybase command to be
                                                    executed on remote client


                temp_input_file_name    (str)   --  temporary input file to be created
                                                    on controller and copied to remote machine

            Returns:
                (object)      -   object of output class for given command

            Raises:
                Exception:

                    if failed to copy the file to remote machine

                    if login to sybase server fails

                    if unable to open input file

        """
        sybasecmd = """. {0}/DM/SYBASE.sh;isql""".format(self.sybase_home)

        exit_cmd = "go\nexit\n"
        sybase_server_name = self.sybase_server
        local_filename = self.controller_object.join_path(self.common_dir_path,
                                                          temp_input_file_name)
        self.log.info("Sybase Command : %s", cmd)

        # Create local temp file and write the the command on the controller to local file
        self.log.info(
            "Create local temp file and write the"
            " command on the controller to local file")
        platform = self.machine_object.os_info
        if cmd:
            if platform.lower() == 'unix':
                content = cmd+'\n'+exit_cmd
            else:
                content = cmd+exit_cmd
            self.controller_object.create_file(local_filename, content)
        else:
            content = "exit\n"
            self.controller_object.create_file(local_filename, content)

        # Copy the local file from controller to remote machine
        self.log.info("Copy the local file from controller to remote machine")
        copy_status = self.machine_object.copy_from_local(
            local_filename, self.remote_path)
        self.log.info("copy_status :%s", copy_status)
        if not copy_status:
            raise Exception("Failed to copy file to remote machine.Exiting")

        # Execute the sybase command on remote machine using copied temp file
        remote_file = self.machine_object.join_path(self.remote_path, temp_input_file_name)
        cmd = """{0} -U {1} -P {2} -S {3}:{4} -i \"{5}\"""".format(
            sybasecmd,
            self.sybase_sa_username,
            self.sybase_sa_userpassword,
            sybase_server_name,
            port,
            remote_file)
        self.log.info(cmd)
        cmd_output = self.machine_object.execute_command(cmd)

        # Check if login failure happened or not
        if cmd_output.output.find("Login failed.") >= 0:
            raise Exception("Login to Sybase server failed : {0}".format(cmd_output.output))

        # Checking if input file is valid for sybase command execution
        if cmd_output.output.find("Unable to open input file") >= 0:
            time.sleep(20)
            cmd_output = self.machine_object.execute_command(cmd)
            if cmd_output.output.find("Unable to open input file") >= 0:
                raise Exception(
                    "Failed to open the input file given to sybase ISQL command. Exiting ")

        # Cleanup temp file on controller and on remote machine
        self.log.info("Cleanup temp file on controller and on remote machine")
        self.controller_object.delete_file(local_filename)
        file_name = self.machine_object.join_path(self.remote_path, temp_input_file_name)
        self.machine_object.delete_file(file_name)
        self.log.info("output : %s", cmd_output.output)
        return cmd_output

    def create_sybase_device(self, device_name, device_path):
        """
        Creates device in given sybase instance

            Args:
                device_name     (str)   --  name of the sybase device to be created

                device_path     (str)   --  device file path for
                                            the sybase device creation

            Returns:
                bool    -  returns True when device creation succeeds

            Raises:
                Exception:
                    if it fails to create sybase device

        """
        temp_input_file_name = """cd{0}.txt""".format(self.thread_id)
        self.log.info("Drop the device if its already existing")
        drop_status = self.drop_sybase_device(device_name, device_path)
        self.log.info("Device drop status : %s", drop_status)
        self.log.info("Going to create device with provided parameters")
        cmd = """disk init name={0}, physname='{1}', size='50M' \n""".format(
            device_name, device_path)
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        if str(cmd_output.output).find("Msg ") >= 0:
            self.log.error("Device %s with path %s creation failed %s",
                           device_name, device_path, cmd_output.output)
            raise Exception("Failed to create device:{0}".format(device_name))
        else:
            self.log.info("Device %s with path %s creation succeeded %s",
                          device_name, device_path, cmd_output.output)
            return True

    def drop_sybase_device(self, device_name, device_file):
        """
        Drops device in given sybase instance

            Args:
                device_name     (str)   --  name of sybase device to be dropped

                device_file     (str)   --  device file path of sybase device to be dropped

            Returns:
                (bool)   -   status based on drop device operation result

                    True  -  returns True if device dropped successfully

                    False -  returns False if device drop fails

        """
        status = False
        temp_input_file_name = """dd{0}.txt""".format(self.thread_id)
        self.log.info("Going to drop given device with provided parameters")
        cmd = """sp_dropdevice {0} \n""".format(device_name)
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        if str(cmd_output.output).find("Device dropped.") >= 0:
            self.log.info("Device %s dropped successfully", device_name)
            self.log.info("device file to be deleted : %s", device_file)
            self.machine_object.delete_file(device_file)
            status = True
        else:
            self.log.error("Device %s drop failed with error: %s", device_name, cmd_output.output)
        return status

    def create_sybase_database(self, database_name, data_device, log_device):
        """
        Create database inside given sybase instance

            Args:
                    database_name   (str)   --  sybase database name to be created

                    data_device     (str)   --  sybase data device name
                                                for database creation

                    log_device      (str)   --  sybase log device name
                                                for database creation

            Returns:
                    (bool)    -   status based on create database operation result

                        True       -    returns True if database created without any issues

            Raises:
                Exception:
                    if database creation fails

        """
        temp_input_file_name = """cdb{0}.txt""".format(self.thread_id)
        cmd = """create database {0} on {1}='10M' log on {2}='10M' \n""".format(
            database_name, data_device, log_device)
        self.log.info("creating database with provided parameters")
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        if str(cmd_output.output).find(
                "Database '{0}' is now online.".format(database_name)) >= 0:
            self.log.info("Database %s created successfully", database_name)
            return True
        else:
            self.log.info("Database %s creation failed %s", database_name, cmd_output.output)
            raise Exception("Failed to create database:{0}".format(database_name))

    def get_database_list(self):
        """
        Returns list of databases in given sybase instance

            Returns:
                (bool)      -     status based on database list fetch operation

                    True       -     returns True if database list returned successfully

                (list)      -     list of database available
                                  in sybase instance

        """
        db_list = []
        temp_input_file_name = """gdl{0}.txt""".format(self.thread_id)
        cmd = """select name from sysdatabases\n"""
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        if (cmd_output.output) == '':
            cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        output = cmd_output.formatted_output
        whole_list = output[0:(len(output) - 2)]
        for i in whole_list:
            for j in i:
                s = str(j)
                db_list.append(s)
        if self.platform.lower() == "unix":
            database_list = db_list[2:]
        else:
            database_list = db_list
        self.log.info("Database list is : %s", database_list)
        return True, database_list

    def get_table_list(self, database_name):
        """
        Returns list of tables inside given database

            Args:
                database_name       (str)   --  database name whose table list to listed

            Returns:
                (bool)      -     status based on table list fetch operation

                     True       -     returns True if table list returned successfully

                (list)    -   list of tables available in given database

        """
        tb_list = []
        temp_input_file_name = """tbl{0}.txt""".format(self.thread_id)
        cmd1 = """use {0} \n""".format(database_name)
        cmd2 = """go\n"""
        cmd3 = """select name from sysobjects\n"""
        cmd = """{0}{1}{2}""".format(cmd1, cmd2, cmd3)
        self.log.info(cmd)
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        if (cmd_output.output) == '':
            cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        output = cmd_output.formatted_output
        whole_list = output[0:(len(output) - 2)]
        for i in whole_list:
            for j in i:
                s = str(j)
                tb_list.append(s)
        if self.platform.lower() == "unix":
            table_list = tb_list[2:]
        else:
            table_list = tb_list
        self.log.info("Table list of database : %s", database_name)
        self.log.info(table_list)
        return True, table_list

    def get_table_content(self, database_name, table_name):
        """
        Fetch contents of given table in given database

            Args:
                database_name       (str)   --  database name where the table exists

                table_name          (str)   --  table name whose content
                                                needs to be displayed

            Returns:
                (bool)      -     status based on table content list fetch operation

                     True       -     returns True if table content returned successfully

                (list)    -   list of table content available in given table

            Raises:
                Exception
                    if given table does not exists in that database

        """
        temp_input_file_name = """tbc{0}.txt""".format(self.thread_id)
        table_exists = self.check_if_table_exists(database_name, table_name)
        if not table_exists:
            raise Exception(
                "Given table %s does not exists in database : %s",
                table_name,
                database_name)
        cmd = """select * from {0}..{1} \n""".format(database_name, table_name)
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        output = cmd_output.formatted_output
        tb_list = output[0:(len(output) - 2)]
        if self.platform.lower() == "unix":
            table_list = tb_list[2:]
        else:
            table_list = tb_list
        self.log.info("Table : %s Content : %s", table_name, table_list)
        return True, table_list

    def check_database_state(self, database_name):
        """
        Checks if database is online.
        if database is offline, it makes the database online

            Args:
                database_name       (str)   --  database name whose
                                                state needs to be checked

            Returns:
                    (bool)    -   status based on online state of database

                        True   -  returns True when database state is online

                        False  -  returns False when database state is offline

        """
        status = False
        db_skip = ['sybsecurity', 'sybmgmtdb']
        if database_name not in db_skip:
            temp_input_file_name = """cst{0}.txt""".format(self.thread_id)
            cmd = """online database {0} \n""".format(database_name)
            cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
            message = "Database '{0}' is now online.".format(database_name)
            if cmd_output.output.find(message) >= 0:
                self.log.info("Database %s is online", database_name)
                status = True
        else:
            status = True
        return status

    def is_system_database(self, database_name):
        """
        Check if given database is sybase system database or not

            Args:
                database_name       (str)   --  database name for
                                                system database check

            Returns:
                    (bool)    -   status based on database is system database or not

                        True  - if given database is system database

                        False - if given database is not system database

        """
        status = False
        system_databases = ('master', 'model', 'tempdb', 'sybsystemdb',
                            'sybsystemprocs', 'sybsecurity', 'sybmgmtdb', 'dbccdb')
        if str(system_databases).find(database_name) >= 0:
            self.log.info("Database %s is a system database", database_name)
            status = True
        else:
            self.log.info("Database %s is not a system database", database_name)
        return status

    def get_logfile_free_size(self, database_name):
        """
        To get log file free size for given database

            Args:
                database_name    (str)   --  database name whose log
                                             file free size to be fetched

            Returns:
               (bool)  -   status based on free size fetched or not

                        True  - if log file free size fetched successfully

               (str)   -    string representing the log
                            file free size of given database

        """
        temp_input_file_name = """lfs{0}.txt""".format(self.thread_id)
        cmd = """sp_helpdb  {0} \n""".format(database_name)
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        self.log.info(cmd_output.output)
        output = cmd_output.output
        output = str(output).split("log only free kbytes = ")
        output = output[1].split(" ")
        output = output[0].replace("\n", "")
        return True, output

    def check_if_table_exists(self, database_name, table_name):
        """
        To check if table exists in given database

            Args:
                database_name       (str)   --  database name in which
                                                given table name exists

                table_name          (str)   --  table name to be checked if
                                                it exists in given database

            Returns:
               (bool)      -     status based on table existence

                     True       -     returns True if table exists

                     False      -     returns False if table does not exists

        """
        status = False
        self.log.info("Check if given database exists")
        db_status = self.check_if_database_exists(database_name)
        if db_status:
            temp_input_file_name = """cte{0}.txt""".format(self.thread_id)
            cmd1 = """use {0} \n""".format(database_name)
            cmd2 = """go\n"""
            cmd3 = """sp_tables {0} \n""".format(table_name)
            cmd = """{0}{1}{2}""".format(cmd1, cmd2, cmd3)
            cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
            self.log.info(cmd_output.output)
            if str(cmd_output.output).find("(0 rows affected)") >= 0:
                self.log.info("Table %s is not existing in database %s", table_name, database_name)
            else:
                self.log.info("Table %s is existing in database %s", table_name, database_name)
                status = True
        else:
            self.log.error("Given Database does not exists or cannot be used")
        return status

    def check_if_database_exists(self, database_name):
        """
        To check if table exists in given database

            Args:
                database_name  (str)   --  database name in which
                                           given table name exists

            Returns:
                (bool)      -     status based on database existence

                     True       -     returns True if database exists

                     False      -     returns False if database does not exists

        """
        status = False
        temp_input_file_name = """cde{0}.txt""".format(self.thread_id)
        cmd3 = """sp_helpdb {0} \n""".format(database_name)
        cmd_output = self.execute_sybase_command(cmd3, temp_input_file_name)
        self.log.info(cmd_output.output)
        if str(cmd_output.output).find("Msg ") >= 0:
            self.log.info("Issue with database : %s , error : %s", database_name, cmd_output.output)
        else:
            self.log.info("Given database : %s exists", database_name)
            status = True
        return status

    def drop_sybase_table(self, database_name, table_name):
        """
        Drop table in given database

            Args:
                database_name       (str)   --  database in which table exists

                table_name          (str)   --  table name to be dropped

            Returns:
                (bool)      -     status based on drop operation result

                     True       -     returns True if drop table succeeds

                     False      -     returns False if drop table fails

        """
        status = False
        temp_input_file_name = """drt{0}.txt""".format(self.thread_id)
        cmd1 = """use {0} \n""".format(database_name)
        cmd2 = """go\n"""
        cmd3 = """drop table {0} \n""".format(table_name)
        cmd = """{0}{1}{2}""".format(cmd1, cmd2, cmd3)
        self.log.info("check if table exists for drop operation")
        table_status = self.check_if_table_exists(database_name, table_name)
        if table_status:
            cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
            self.log.info("Dropped table successfully")
            status = True
        else:
            self.log.info("Given table name : %s does not exists", table_name)
        return status

    def create_sybase_table(self, database_name, table_name):
        """Create table in given database  and insert data into it

            Args:
                database_name       (str)   --  database in which table to be created

                table_name          (str)   --  table to be created in given database

            Returns:
                (bool)      -     status based on create table operation result

                    True       -     returns True if table creation succeeds

                    False      -     returns False if table creation fails

        """
        status = False
        temp_input_file_name = """ct{0}.txt""".format(self.thread_id)
        cmd1 = """use {0} \n""".format(database_name)
        cmd2 = """go\n"""
        cmd3 = """create table {0} (name varchar(30), ID integer not null) \n""".format(
            table_name)
        cmd = """{0}{1}{2}""".format(cmd1, cmd2, cmd3)
        self.log.info("check if table exists in create table function ")
        table_status = self.check_if_table_exists(database_name, table_name)
        if table_status:
            self.log.info(
                "Since the table exists , going to drop before creation")
            status = self.drop_sybase_table(database_name, table_name)
        else:
            self.log.info(
                "Given tablename does not exists. create the table ")
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        self.log.info("create table command output is ")
        self.log.info(cmd_output.formatted_output)
        if (cmd_output.output).find("Msg ") >= 0:
            self.log.info("Unable to create table:%s", str(cmd_output.output))
        else:
            self.log.info("Table data Population")
            insert_status = self.insert_data(database_name, table_name)
            if insert_status:
                self.log.info("Data inserted successfully into given table")
                status = True
            else:
                self.log.error("Data insertion to new table failed")
        return status

    def insert_data(self, database_name, table_name):
        """
        Insert data to given table inside given database name

            Args:
                    database_name       (str)   --  database in which table to be populated

                    table_name          (str)   --  table to be populated with data

            Returns:
                    (bool)      -     status based on data insertion result

                         True       -     returns True if data insertion succeeds

                         False      -     returns False if data insertion fails

        """
        status = False
        temp_input_file_name = """ins{0}.txt""".format(self.thread_id)
        self.log.info("check if table exists")
        table_status = self.check_if_table_exists(database_name, table_name)
        if table_status:
            self.log.info("Given table exists.Inserting data to given table")
            cmd_main = ""
            for count in range(1, 300):
                cmd = """insert into {0}..{1} values('commvault',1) \n""".format(
                    database_name, table_name)
                cmd_main = """{0}{1}""".format(cmd_main, cmd)
            cmd_output = self.execute_sybase_command(
                cmd_main, temp_input_file_name)
            self.log.info("Table data Population done")
            status = True
        else:
            self.log.info("Given table does not exists")
        return status

    def deactivate_sybase_hadr_admin(self):
        """
        TO deactiavte sybase Hadr Admin

            Raises
                Exception:
                    If Hadr Admin deactivation fails

        """
        temp_input_file_name = """dsha{0}.txt""".format(self.thread_id)
        cmd = """sp_hadr_admin deactivate, '30'\n"""
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        self.log.info(cmd_output.output)
        if str(cmd_output.output).find(
                "Deactivation failed due to log drain failure") >= 0:
            self.log.info("Deactivate Sybase HADR admin failed due to log drain failure")
            return False
        elif str(cmd_output.output).find(
                "success") >= 0:
            self.log.info("Sybase HADR Admin deactivated")
            return True
        return False

    def shutdown_sybase_server(self):
        """
        To shutdown sybase instance

            Raises:
                Exception:
                    if it fails to shutdown the server

        """
        temp_input_file_name = """sds{0}.txt""".format(self.thread_id)
        cmd = """shutdown\n"""
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        self.log.info(cmd_output.output)
        if str(cmd_output.output).find(
                " Net-Library operation terminated due to disconnect") >= 0:
            self.log.info("Shutdown server : %s is successful", self.sybase_server)
            return True
        else:
            raise Exception("Failed to shutdown the server:{0}".format(
                self.sybase_server))

    def shutdown_with_no_wait(self):
        """
            To shutdown sybase node with no wait

                    Raises:
                        Exception:
                            if it fails to shutdown the server

            """
        temp_input_file_name = """swnw{0}.txt""".format(self.thread_id)
        cmd = """shutdown with nowait\n"""
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        self.log.info(cmd_output.output)
        if str(cmd_output.output).find(
                " Net-Library operation terminated due to disconnect") >= 0:
            self.log.info("Shutdown with no wait server : %s is successful", self.sybase_server)
            return True
        else:
            raise Exception("Failed to shutdown with no wait server:{0}".format(
                self.sybase_server))

    def shutdown_sybasehadr_rma(self):
        """
                To shutdown sybase RMA server

                    Raises:
                        Exception:
                            if it fails to shutdown the server

        """
        temp_input_file_name = """ssrma{0}.txt""".format(self.thread_id)
        cmd = """shutdown\n"""
        cmd_output = self.execute_sybasehadr_command('4909', cmd, temp_input_file_name)
        self.log.info(cmd_output.output)
        if str(cmd_output.output).find(
                "Shutdown") >= 0:
            self.log.info("Shutdown RMA server : %s is successful", self.sybase_server)
            return True
        else:
            raise Exception("Failed to shutdown the RMA server:{0}".format(
                self.sybase_server))

    def shutdown_sybasehadr_rep(self):
        """
                To shutdown sybase REP server

                    Raises:
                        Exception:
                            if it fails to shutdown the server

                """
        temp_input_file_name = """ssrep{0}.txt""".format(self.thread_id)
        cmd = """shutdown\n"""
        cmd_output = self.execute_sybasehadr_command('5005', cmd, temp_input_file_name)
        self.log.info(cmd_output.output)
        if str(cmd_output.output).find(
                "Net-Library operation terminated due to disconnect") >= 0:
            self.log.info("Shutdown REP server : %s is successful", self.sybase_server)
            return True
        else:
            raise Exception("Failed to shutdown the REP server:{0}".format(
                self.sybase_server))

    def is_server_running(self):
        """
        Check the status of sybase server

            Returns:
                    (bool)      -     status based on server running

                         True       -     returns True if server is running

                         False      -     returns False if server is stopped

        """
        status = False
        temp_input_file_name = """isr{0}.txt""".format(self.thread_id)
        cmd = None
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        output = cmd_output.output
        if str(cmd_output.output).find("CT-LIBRARY error:") >= 0:
            self.log.info("Sybase server:%s is not running:%s", self.sybase_server, output)
        else:
            self.log.info("Sybase server:%s is running:%s", self.sybase_server, output)
            status = True
        return status

    def get_device_path(self, device_name='master'):
        """
        Fetch base device path for given sybase instance

          Args:
              device_name       (str)       --  device name whose path to be determined
                                                default : master

          Returns:
              (bool)    -   status based on fetch operation result

                    True    -   returns True if device path is fetched

              (str)     -   string representing the device path

        """
        temp_input_file_name = """gdp{0}.txt""".format(self.thread_id)
        cmd = """select phyname from sysdevices where name = '{0}'\n""".format(device_name)
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        output = cmd_output.formatted_output
        if self.platform.lower() == 'unix':
            p = output[2]
        else:
            p = output[0]
        path = p[0]
        i = len(path) - 1
        while i >= 0:
            if path[i] != "/" and path[i] != "\\":
                device_file = path[0:i]
            else:
                break
            i = i - 1
        self.log.info("Device Path:%s", device_file)
        return True, device_file

    def get_device_name(self, database_name):
        """
        Fetch devices for given database

          Args:
              database_name       (str)       --  database name whose devices to be determined

          Returns:
              (list)        -   list of devices associated with that database

        """
        device_names = []
        temp_input_file_name = """gdn{0}.txt""".format(self.thread_id)
        cmd = ("select sde.name from master..sysdatabases sda,master..sysdevices sde,"
               " master..sysusages su where su.dbid=sda.dbid and"
               " su.vdevno=sde.vdevno and sda.name = '{0}'\n".format(database_name))
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        self.log.info(cmd_output.formatted_output)
        output = cmd_output.formatted_output
        whole_list = output[0:(len(output) - 2)]
        if self.platform.lower() == "unix":
            device_list = whole_list[2:]
        else:
            device_list = whole_list
        for device in device_list:
            name = str(device).strip("[]").strip("''")
            device_names.append(name)
        self.log.info("device list of database : %s is %s", database_name, device_names)
        return device_names

    def drop_sybase_database(self, database_name):
        """
        Drop database inside given sybase instance

            Args:
                database_name       (str)   --  database to be dropped

            Returns:
                (bool)      -   status based on drop operation result

                    True    -   returns True if database drop succeeds

            Raises:
                Exception:
                    if drop database fails

        """
        temp_input_file_name = """ddb{0}.txt""".format(self.thread_id)
        cmd = """drop database {0} \n""".format(database_name)
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        (status, db_list) = self.get_database_list()
        if database_name in db_list:
            raise Exception("Failed to drop database:{0}".format(database_name))
        else:
            self.log.info("Database dropped successfully")
            return True

    def set_cumulative(self, database_name):
        """
        To set incremental dumps for given database

        Args:
            database_name       (str)       --      database whose incremental dumps to be enabled

        Returns:
            (bool)      -       return True if the settings set successfully

        Raises:
            Exception
                if setting configuration fails

        """
        self.log.info("Setting Cumulative for database : %s", database_name)
        temp_input_file_name = """sc{0}.txt""".format(self.thread_id)
        cmd1 = "use master\ngo\n"
        cmd2 = "sp_dboption {0},'allow incremental dumps',true \n".format(database_name)
        cmd3 = "{0}{1}".format(cmd1, cmd2)
        self.log.info(cmd3)
        cmd_output = self.execute_sybase_command(cmd3, temp_input_file_name)
        output = cmd_output.output
        if output.find("Database option 'allow incremental dumps' turned ON for database") >= 0:
            return True
        else:
            raise Exception("Error in setting incremental dumps for given database.")

    def remove_user_db(self, dbname):
        """
        Remove user database from other
        subclient to avoid duplicate entry in partial restore

            Args:
                dbname (str)   --  database name to be removed from subclient content

            Returns:
                   (bool)      -   status based on deleting user db from subclient

                        True    -   returns True if database removed from subclient

                        False   -   returns False if database failed gto get removed
        """
        status = False
        self.log.info("Inside remove user database method")
        subclient_dict = self.instance.subclients._get_subclients()
        subclient_list = []
        for key in subclient_dict.keys():
            subclient_list.append(str(key))
        self.log.info("subclient list for given server:%s", subclient_list)
        for sub in subclient_list:
            sub_object = self.instance.subclients.get(sub)
            original_content = sub_object.content
            if dbname in original_content:
                original_content.remove(dbname)
                sub_object.content = original_content
                status = True
                break
        return status

    def log_backup_to_disk(self, database_name, cv_instance):
        """
        Perform log backup to disk
        for given database

        Args:
            database_name       (str)       --      name of the database for
                                                    log backup to disk

            cv_instance         (str)       --      commvault instance number
                                                    on client

        Raises:
            Exception
                if log backup to disk command fails

        """
        self.log.info("Running log backup to disk for database : %s", database_name)

        # log backup to disk command with 2 streams
        cmd = (f"dump transaction {database_name} to 'SybGalaxy:: -disk -vm {cv_instance}'"
               f" with blocksize=65536\n")
        self.log.info("Log Backup to disk command")
        self.log.info(cmd)
        temp_input_file_name = """log_to_disk_{0}.txt""".format(self.thread_id)
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        if cmd_output.output.find("DUMP is complete") >= 0:
            self.log.info("Log backup to disk ran successfully")
        else:
            raise Exception("Log backup to disk failed: {0}".format(cmd_output.output))

    def enable_encryption_for_db(self, db_name, key):
        """Encrypts the given db with the encryption key mentioned
           Args:

           db_name        (str)     --      User database name

           Key            (str)     --      Encryption key name
        """

        self.log.info(f"Encrpyting Database {db_name} with {key}")
        temp_input_file_name = """encrpyt_db_{0}.txt""".format(self.thread_id)
        cmd = f"alter database {db_name} encrypt with {key} \n"
        cmd_output = self.execute_sybase_command(cmd, temp_input_file_name)
        if str(cmd_output.output).find("Initiated encryption tasks") >= 0:
            self.log.info("Database successfully encrypted")
        else:
            raise Exception("Encrypting database failed:{0}".format(cmd_output.output))


class SybaseCVHelper(object):
    """Class to perform operations involving sybase and commvault entity"""

    def __init__(self, sybase_helper):
        self.sybase_helper = sybase_helper
        self.common_utils_object = idautils.CommonUtils(
            self.sybase_helper.commcell)
        self.log = logger.get_log()

    def sybase_populate_data(self, database_name, table_name):
        """
        Populate one database,one table inside
        that database and populate content to the user table

            Args:
                    database_name       (str)   --   database in which table to be created

                    table_name          (str)   --   table to be created in given database

            Raises:
                Exception:
                    if table creation fails

                    if data population fails

        """

        # Checking Sybase Server status
        server_status = self.sybase_helper.is_server_running()
        if server_status:
            self.log.info("\n Sybase Server is up and running")
        else:
            raise Exception(
                "Server is not up and running. so exiting. Unable to populate test data ")
        # Getting Device Path for creating sybase devices
        status, device_path = self.sybase_helper.get_device_path()
        data_device_path = """{0}data_{1}.dat""".format(
            device_path, database_name)
        log_device_path = """{0}log_{1}.dat""".format(
            device_path, database_name)
        data_device_name = """data_{0}""".format(database_name)
        log_device_name = """log_{0}""".format(database_name)
        self.log.info("drop databases before creating new one")
        db1_status = self.sybase_helper.drop_sybase_database(database_name)
        self.log.info("create device")
        # create device with given parameters
        data_device_status = self.sybase_helper.create_sybase_device(
            data_device_name, data_device_path)
        if data_device_status:
            self.log.info("Data Device created successfully")
        log_device_status = self.sybase_helper.create_sybase_device(
            log_device_name, log_device_path)
        if log_device_status:
            self.log.info("Log Device created successfully")
        self.log.info("create database")
        # create new user databases as per inputs
        db_status = self.sybase_helper.create_sybase_database(
            database_name, data_device_name, log_device_name)
        if db_status:
            self.log.info("Database %s created", database_name)
        self.log.info("create table ")
        # create new table inside DB38572 database before full backup
        table_status = self.sybase_helper.create_sybase_table(
            database_name, table_name)
        if table_status:
            self.log.info(
                "Test table %s in database %s is created",
                table_name,
                database_name)
        else:
            raise Exception(
                "Test Data Population failed during table creation")

    def single_table_populate(self, database_name, table_name):
        """
        Populate single table with data in given database

            Args:
                    database_name       (str)   --  database in which table to be created

                    table_name          (str)   --  table to be created in given database

           Raises:
                Exception:
                    if test table creation fails

        """
        table_status = self.sybase_helper.create_sybase_table(
            database_name, table_name)
        if table_status:
            self.log.info("Test table %s in database %s is created", table_name, database_name)
        else:
            raise Exception("Test table creation failed")

    def get_all_database_tables(self):
        """
        Returns dictionary containing all tables lists of all sybase databases

            Returns:
                dict(list)  -   dictionary of list containing all
                                table list of each database in sybase server

            Raises:
                Exception:
                    if any of user database state not online

                    if table list  fetch fails

        """
        all_table_list = {}
        status, db_list = self.sybase_helper.get_database_list()
        for each_db in db_list:
            self.log.info("Check database state before fetching table lists")
            time.sleep(20)
            status = self.sybase_helper.check_database_state(each_db)
            if not status:
                time.sleep(20)
                status = self.sybase_helper.check_database_state(each_db)
                if not status:
                    raise Exception(
                        "Database state of {0} is not online to fetch tables".format(each_db))
            (status_code, table_list) = self.sybase_helper.get_table_list(each_db)
            if not status_code:
                raise Exception(
                    "Error in getting table list for database :{0}".format(each_db))
            all_table_list[each_db] = table_list
        return all_table_list

    def comparing_dict_of_list(self, dict_first, dict_second):
        """
        Compares two dictionaries of lists

            Args:
                dict_first      (dict)  --  first dictionary of lists for comparison

                dict_second     (dict)  --  second dictionary of lists for comparison

            Returns:
                    (bool)    -   boolean value whether comparison succeeded or not

                        True    -   returns True if two dict matches

                        False   -   returns False if dict does not match

        """
        status = False
        dl1 = len(dict_first)
        dl2 = len(dict_second)
        count = 0
        if dl1 == dl2:
            self.log.info("dict length equal")
            for eachkey in dict_second:
                list_1 = dict_first[eachkey]
                list_2 = dict_second[eachkey]
                list_status = (list_1 == list_2)
                if not list_status:
                    self.log.info("List of Key : %s not matching", eachkey)
                    break
                else:
                    count = count + 1
                    continue
            if count == dl1:
                self.log.info("All dict list are equal")
                status = True
        else:
            log_message = "Dictionary value doesn't match for :{0}:{1}".format(dict_first,
                                                                               dict_second)
            self.log.info(log_message)
        return status

    def sybase_cleanup_test_data(self, database_name):
        """
        To cleanup the test database and device

            Args:
                    database_name   (str)   --  database to be cleaned
                                                up after test case run

            Raises:
                Exception
                    if sybase server is down

        """
        server_status = self.sybase_helper.is_server_running()
        if server_status:
            device_list = self.sybase_helper.get_device_name(database_name)
            self.log.info("Device list is %s for the database %s", device_list, database_name)
            drop_db = self.sybase_helper.drop_sybase_database(database_name)
            self.log.info("Getting device list of database :%s and will drop", database_name)
            for device in device_list:
                status, device_path = self.sybase_helper.get_device_path(device)
                file_name = "{0}.dat".format(device)
                file_path = self.sybase_helper.machine_object.join_path(device_path, file_name)
                self.log.info("Device path to be cleaned up : %s", file_path)
                drop_dev1 = self.sybase_helper.drop_sybase_device(device, file_path)
                self.log.info("Device %s drop status :%s", device, drop_dev1)
        else:
            raise Exception("Server is not up and running to perform cleanup")

    def cleanup_tables(self, database_name, table_list):
        """
        Cleanup tables in given database without deleting the database

            Args:
                database_name   (str)   --  name of the database

                table_list      (list)  --  list of tables to be removed

            Raises:
                Exception
                    if table cannot be dropped

        """
        for table in table_list:
            status = self.sybase_helper.drop_sybase_table(database_name, table)
            if not status:
                raise Exception("Unable to drop table :%s", table)

    def sybase_delete_database_from_subclient(self, subclient, database_name):
        """
        Cleanup database name created during the TC run from subclient

            Args:
                subclient           (object)   -- Object of subclient class

                database_name       (str)      -- database to be cleaned up
                                                  after test case run

        """
        current_db_list = subclient.content
        new_list = []
        for dbname in current_db_list:
            if dbname == database_name:
                self.log.info("Database removed from list:%s", dbname)
            else:
                new_list.append(dbname)
                self.log.info("database name appended : %s", dbname)
        subclient.content = new_list

    def enable_fs_based_snap(self, subclient, proxy_name, snap_engine):
        """
        Enables intellisnap with FS based backup copy option

            Args:
                subclient       (object)    --      Object of subclient class

                proxy_name      (str)       --      string representing the proxy machine
                                                    to be used for backup copy operation

                engine_name     (str)       --      snap engine name

            Returns:
                (bool)    -   status based on enabling FS based snap

                        True    -   returns True if snap enabled successfully

            Raises:
                Exception
                    When intellisnap not enabled at client level

        """
        client = self.sybase_helper.client
        if client.is_intelli_snap_enabled:
            subclient.is_snapenabled = True
            subclient.snap_proxy = proxy_name
            subclient.snap_engine = snap_engine
            subclient.use_dump_based_backup_copy = False
            return True
        else:
            raise Exception("Intellisnap is not enabled at client level")

    def enable_dump_based_snap(
            self,
            subclient,
            proxy_name,
            snap_engine,
            dump_based_backup_copy_option=constants.SYBASE_DUMP_BASED_WITH_CONFIGURED_INSTANCE,
            configured_instance_name=None,
            custom_instance_properties=None):
        """
        Enables dump based backup copy with required options

            Args:
                subclient                      (object)   --   Object of subclient class

                proxy_name                     (str)      --   string representing
                                                               the proxy machine
                                                               to be used for backup
                                                               copy operation

                snao_engine                    (str)      --   name of snap engine to be used
                                                               for intellisnap

                dump_based_backup_copy_option  (int)      --   set dumpcopy option
                                                               CONFIGURED_INSTANCE,
                                                               AUXILIARY_SERVER
                                                               default:CONFIGURED_INSTANCE

                configured_instance_name       (str)      --   name of configured instance
                                                               default : None

                custom_instance_properties     (dict)     --   dict of custom instance
                                                               properties in below format
                                                               default : None

                Sample dict:

                instance_properties = {
                    'sybaseHome':sybase_home,
                    'sybaseASE':sybase_ase,
                    'sybaseOCS':sybase_ocs,
                    'sybaseUser':sybase_user
                    }

            Returns:
                (bool)    -   status based on enabling Dump based snap

                        True    -   returns True if snap enabled successfully

                        False   -   returns False if snap could not be enabled

            Raises:
                Exception
                    When intellisnap not enabled at client level

        """
        status = False
        client = self.sybase_helper.client
        if client.is_intelli_snap_enabled:
            if ('windows' in client.os_info.lower()) and (
                    dump_based_backup_copy_option ==
                    constants.SYBASE_DUMP_BASED_WITH_AUXILIARY_SERVER):
                self.log.info(
                    "Windows client with auxiliary server requires"
                    "manual subclient property configuration.")
                if (subclient.is_snapenabled) and (
                        subclient.dump_based_backup_copy_option ==
                        constants.SYBASE_DUMP_BASED_WITH_AUXILIARY_SERVER):
                    self.log.info("Getting auxiliary server properties")
                    aux_properties = subclient.auxiliary_sybase_server
                    if not (None in aux_properties.values()):
                        self.log.info(
                            "Auxiliary Server properties are set already")
                        status = True
            else:
                subclient.is_snapenabled = False
                subclient.snap_proxy = proxy_name
                subclient.snap_engine = snap_engine
                if dump_based_backup_copy_option == 1:
                    self.log.info("Dump based operation using configured instance:%s",
                                  configured_instance_name)
                    subclient.use_dump_based_backup_copy = True
                    subclient.dump_based_backup_copy_option = 1
                    if configured_instance_name is None:
                        raise Exception(
                            "Configured instance name cannot be empty")
                    subclient.configured_instance = configured_instance_name
                else:
                    self.log.info(
                        "Dump based backup copy operation with"
                        "auxiliary server")
                    subclient.use_dump_based_backup_copy = True
                    subclient.dump_based_backup_copy_option = 2
                    subclient.auxiliary_sybase_server = custom_instance_properties
                status = True
                subclient.is_snapenabled = True
        else:
            raise Exception("Intellisnap is not enabled at client level ")
        return status

    def snap_backup(self,
                    subclient,
                    create_backup_copy_immediately=True):
        """
        To initiate snap sybase backup and validate the same

            Args:

                subclient                       (object)   --   subclient object on which snap
                                                                backup needs to be triggered

                create_backup_copy_immediately   (bool)    --   Sybase snap job needs
                                                                this backup copy operation


            Returns:

                (bool)      --          returns True if snap and backup copy
                                        succeeds including the validation part

            Raises:
                Exception:
                    if it fails to run backup copy job

                    if it fails in snap to tape check or job type check

        """

        snap_job_type_check = False
        backup_copy_type_check = False
        snap_tape_check = False

        # Initiate Full Snap backup job with inline backup copy triggered

        snap_job = subclient.backup(
            backup_level='full',
            create_backup_copy_immediately=create_backup_copy_immediately)
        if not snap_job.wait_for_completion():
            raise Exception(
                "Failed to run FULL Snap backup job with error: {0}".format(
                    snap_job.delay_reason))

        # Getting inline backup copy job ID
        self.log.info("wait for 3 mins before fetching backup copy job ID")
        time.sleep(180)

        backup_copy_job_id = self.common_utils_object.get_backup_copy_job_id(snap_job.job_id)
        self.log.info("Inline backup copy job ID : %s", backup_copy_job_id)

        # Snap job type validation
        job_type = snap_job.job_type

        if job_type.lower() == 'snap backup':
            self.log.info("Snap Backup successfully initiated")
            snap_job_type_check = True

        # Monitoring inline backup copy job
        backup_copy_job = self.sybase_helper.commcell.job_controller.get(
            job_id=backup_copy_job_id)
        if not backup_copy_job.wait_for_completion():
            raise Exception(
                "Failed to run backup copy with error: {0}".format(
                    backup_copy_job.delay_reason))

        # backup copy type validation

        backup_copy_details = backup_copy_job.details
        actual_copy_type = backup_copy_details['jobDetail']['generalInfo']['operationType']
        if actual_copy_type == 'Backup Copy':
            self.log.info("Backup Copy Operation Type verified")
            backup_copy_type_check = True

        # validate the snap to tape movement on snap job after inline copy
        # completion

        snap_to_tape_status = (snap_job.details)[
            'jobDetail']['generalInfo']['snapToTapeStatus']
        if snap_to_tape_status == 3:
            snap_tape_check = True

        if (snap_job_type_check) and (
                backup_copy_type_check) and (snap_tape_check):
            self.log.info("Snap Job and Backup Copy Job succeeded")
            return True
        else:
            raise Exception(
                "Overall snap and backup copy Failed.Check Logs for further details")

    def get_storage_policy(self):
        """

            Returns:
                (str)           -      storage policy of default subclient
        """
        subclient = self.sybase_helper.instance.subclients.get("default")
        storage_policy = subclient.storage_policy
        return storage_policy

    def backup_and_validation(self,
                              subclient,
                              backup_type='full',
                              do_not_truncate_log=False,
                              sybase_skip_full_after_logbkp=False,
                              create_backup_copy_immediately=False,
                              backup_copy_type=2,
                              directive_file=None,
                              **kwargs):
        """
        Launch requested backup job and validate the same

            Args:
                subclient                       (object)  --    subclient for backup

                backup_type                     (str)     --    backup type.
                                                                full|incremental|differential
                                                                default: full

                do_not_truncate_log             (bool)    --    Sybase truncate log option
                                                                for incremental backup
                                                                default : False

                sybase_skip_full_after_logbkp   (bool)    --    Sybase backup option for incremental
                                                                default : False

                create_backup_copy_immediately  (bool)    --    Sybase snap job needs this
                                                                backup copy operation
                                                                default : False

                backup_copy_type                (int)     --    backup copy job to be launched
                                                                based on below two options
                                                                default : 2, possible values :
                                                                1 (USING_STORAGE_POLICY_RULE),
                                                                2( USING_LATEST_CYCLE)

                directive_file                  (str)     --    input file for ondemand backup
                                                                containing database list
                                                                default : None

                **Kwargs                       (dict)    --    Keyword Arguments

                    Keyword arguments allowed -

                    syntax_check             (bool)      --    True if you want to check syntax of backup from logs

                    db                       (list)      --   List of names of database whose backup syntax is to
                                                              be checked

            Returns:
                (object)           -   returns object of job class

            Raises:
                Exception
                    if failed to launch backup job

                    if backup validation fails

        """
        # Backup Job launching
        backup_job = subclient.backup(backup_level=backup_type,
                                      do_not_truncate_log=do_not_truncate_log,
                                      sybase_skip_full_after_logbkp=sybase_skip_full_after_logbkp,
                                      create_backup_copy_immediately=create_backup_copy_immediately,
                                      backup_copy_type=backup_copy_type,
                                      directive_file=directive_file)
        if not backup_job.wait_for_completion():
            raise Exception(
                "Failed to run backup job with error: {0}".format(
                    backup_job.delay_reason))
        if backup_job.state in ["Completed w/ one or more errors", "Failed", "Killed"]:
            self.log.info("Backup JOB ID: %s", backup_job.job_id)
            self.log.info("Backup State : %s", backup_job.state)
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, backup_job.delay_reason))

        # backup job validation
        if backup_type.lower() == 'full':
            actual_backup_type = "Full"
        elif backup_type.lower() == 'incremental':
            actual_backup_type = "Transaction Log"
        elif backup_type.lower() == 'differential':
            actual_backup_type = 'Differential'
        status = self.common_utils_object.backup_validation(
            backup_job.job_id, actual_backup_type)
        if status:
            if kwargs and kwargs.get("syntax_check"):
                if not self.backup_syntax_check(actual_backup_type, backup_job.job_id, kwargs.get("db")):
                    raise Exception(
                        "Failed in backup job syntax validation: {0}".format(backup_job.job_id))
            self.log.info("Backup Validation successfull")
            return backup_job
        else:
            raise Exception(
                "Failed in job validation: {0}".format(backup_job.job_id))

    def backup_syntax_check(self, backup_type, job_id, db):
        """Checks the syntax of the backup job through the ClSybAgent logs
           Args:
                backup_type      (str)     --     Type of backup operation being performed, Full, Transaction Log
                                                  or Differential

                job_id           (str)     --     Job ID of the particular backup job

                db               (list)    --     List of database names whose syntax is to be checked

            Returns :
                  (Bool)     --       True if syntax check passes, False if it fails
        """
        if backup_type == "Full":
            logs = self.sybase_helper.machine_object.get_logs_for_job_from_file(job_id=job_id,
                                                                                log_file_name="ClSybAgent.log",
                                                                                search_term="dump database")
            for db_name in db:
                search_term = "dump database " + db_name
                if search_term not in logs:
                    return False
                self.log.info(f"Syntax validation for full backup, database {db_name} completed")
            return True
        if backup_type == "Transaction Log":
            logs = self.sybase_helper.machine_object.get_logs_for_job_from_file(job_id=job_id,
                                                                                log_file_name="ClSybAgent.log",
                                                                                search_term="dump transaction")
            for db_name in db:
                search_term = "dump transaction " + db_name
                if search_term not in logs:
                    return False
                self.log.info(f"Syntax validation for Transaction Log backup, database {db_name} completed")
            return True
        if backup_type == "Differential":
            logs = self.sybase_helper.machine_object.get_logs_for_job_from_file(job_id=job_id,
                                                                                log_file_name="ClSybAgent.log",
                                                                                search_term="dump database")
            for db_name in db:
                search_term = "dump database " + db_name + " cumulative"
                if search_term not in logs:
                    return False
                self.log.info(f"Syntax validation for cumulative incremental backup, database {db_name} completed")
            return True

    def encrypted_db_backup_syntax(self, job_id, keys):
        """Checks if given encrypted keys were backed up in backup job
            Args :

            job_id         (str)     --     Job ID of the particular backup job
            Keys           (List)    --     List of keys present in the sybase instance
        """

        logs = self.sybase_helper.machine_object.get_logs_for_job_from_file(job_id=job_id,
                                                                            log_file_name="ClSybAgent.log",
                                                                            search_term="updateSybaseEncrKeyDetailToCSDB")
        for key in keys:
            if key not in logs:
                raise Exception(f"Key", key, "Not backed up in backup job")
        self.log.info("All given encrypted keys were backed up in the backup job")

    def concurrent_backup_based_restore(self,
                                        tl1_end_time,
                                        tl2_end_time,
                                        tl1_table_lists,
                                        tl2_table_lists,
                                        user_table_list,
                                        database_name):
        """
        Perform two restores based on concurrent log backups

            Args:
                tl1_end_time        (str)  -- end time of transaction log backup 1

                tl2_end_time        (str)  -- end time of transaction log backup 2

                tl1_table_lists     (list) -- Table Lists of user database after TL1 backup

                tl2_table_lists     (list) -- Table Lists of user database after TL2 backup

                user_table_list     (list) -- list of user tables created

                database_name       (str)  -- name of user database to be restored

            Returns:
                bool          -     status based on restore jobs and its validation

                    True      -     returns True if restore and its validation passes

                    False     -     returns False if restore and its validation fails

            Raises:
                Exception
                    if restore job fails

        """
        res_db_list = []
        partial_restore_1_status = False
        partial_restore_2_status = False

        table_content_before = dict.fromkeys(user_table_list, None)
        for table in user_table_list:
            status, table_content_before[table] = self.sybase_helper.get_table_content(database_name,
                                                                                       table)

        # Perform restore to end time of TL1 backup
        self.log.info("Partial Restore 1 to end time of TL1 backup")
        res_db_list.append(database_name)
        partial_restore_1_status = self.single_database_restore(database_name,
                                                                user_table_list[:2],
                                                                expected_table_list=tl1_table_lists,
                                                                timevalue=tl1_end_time,
                                                                concurrent_flag=True)
        if partial_restore_1_status:
            self.log.info("Partial restore to end time of TL1 succeeded")
        else:
            self.log.info(
                "Restore validation Failed during partial restore to end time of TL1 backup:")
        # Perform restore to end time of TL2 backup
        self.log.info("Partial Restore 2 to end Time of TL2 backup")
        partial_restore_2 = self.sybase_helper.instance.restore_database(
            database_list=[database_name],
            timevalue=tl2_end_time)

        if not partial_restore_2.wait_for_completion():
            raise Exception("Failed to run Restore job with error: {0}".format(
                partial_restore_2.delay_reason))

        table_content_after = dict.fromkeys(user_table_list, None)
        for table in user_table_list:
            status, table_content_after[table] = self.sybase_helper.get_table_content(database_name,
                                                                                      table)

        # Partial restore 2 validation
        self.log.info("Partial Restore 2 validation")

        status, table_lists_after_restore2 = self.sybase_helper.get_table_list(
            database_name)

        database_content_status = self.table_validation(tl2_table_lists,
                                                        table_lists_after_restore2,
                                                        table_content_before,
                                                        table_content_after)

        if database_content_status:
            self.log.info("Partial restore to end time of TL2 succeeded")
            partial_restore_2_status = True
        else:
            self.log.info(
                "Restore validation Failed during partial restore to end time of TL2 backup:")

        if partial_restore_1_status and partial_restore_2_status:
            return True
        else:
            raise Exception("Restore failed.Check the logs")

    def drop_user_databases(self, db_list):
        """
        To drop all user database in sybase instance

            Args:
                db_list     (list)  --    list of databases to be dropped

            Raises:
                Exception:
                    if it fails to drop user database
        """
        for each_db in db_list:
            status = self.sybase_helper.is_system_database(each_db)
            if not status:
                db_drop_status = self.sybase_helper.drop_sybase_database(
                    each_db)
                if not db_drop_status:
                    raise Exception("Error in dropping the database :{0}".format(db_drop_status))

    def restore_to_disk_and_validation(self,
                                       destination_path,
                                       backup_job_ids,
                                       user_name,
                                       password,
                                       user_db,
                                       user_tables):
        """
        Performs restore to disk [Application free restore] and validates the restore

                Args:

                    destination_path            (str)   --  destination path for
                                                            application based restore


                    backup_job_ids              (list)  --  list of backup job IDs to
                                                            be used for disk restore

                    user_name                   (str)   --  impersonation user name
                                                            to restore to destination client

                    password                    (str)   --  impersonation user password

                    user_db                     (str)   --  user database to be
                                                            used for restore to disk

                    user_tables                 (list)  --  list of user created
                                                            tables during this test case run

                Returns:
                    (bool)                  -       status based to restore
                                                    to disk validation passed

                        True  -  if restore validation succeeds
                Raises:
                    Exception:
                        if failed to launch restore job

                        if unable to open input file

                        if database cannot be brought to online state

                        if restore validation fails

        """
        self.log.info("Restore to disk")
        instance = self.sybase_helper.instance
        destination_client = instance.client_name
        # saving database data before restore
        status, table_list_before = self.sybase_helper.get_table_list(user_db)
        self.log.info("Status of table list before restore : %s", status)
        table_contents_before = dict.fromkeys(user_tables, None)
        for table in user_tables:
            self.log.info("Content of table : %s in database : %s", table, user_db)
            status, table_contents_before[table] = self.sybase_helper.get_table_content(user_db,
                                                                                        table)

        self.log.info("Table List before drop : %s", table_list_before)
        for table in user_tables:
            drop_status = self.sybase_helper.drop_sybase_table(user_db, table)
            self.log.info("Drop status %s for table %s", drop_status, table)
        self.log.info("backup job ids : %s", backup_job_ids)
        restore_job = instance.restore_to_disk(destination_client,
                                               destination_path,
                                               backup_job_ids,
                                               user_name,
                                               password)
        self.log.info("Restore job id : %s", restore_job.job_id)
        if not restore_job.wait_for_completion():
            raise Exception("Failed to run Restore job with error: {0}".format(
                restore_job.delay_reason))
        destination_machine = machine.Machine(destination_client, self.sybase_helper.commcell)
        file_path = destination_machine.join_path(destination_path,
                                                  restore_job.job_id)
        for backup_job_id in backup_job_ids:
            self.log.info("For backup job ID :%s", backup_job_id)
            file_name = "{0}--{1}.sql".format(backup_job_id, user_db)
            remote_file = destination_machine.join_path(file_path, file_name)
            file_content = destination_machine.read_file(remote_file).strip()
            file_content = "{0}\n".format(file_content)
            temp_input_file_name = """rtd{0}.txt""".format(self.sybase_helper.thread_id)
            cmd_output = self.sybase_helper.execute_sybase_command(
                file_content, temp_input_file_name)

            # Checking if input file is valid for sybase command execution
            if (cmd_output.output).find("Unable to open input file") >= 0:
                time.sleep(20)
                cmd_output = self.sybase_helper.execute_sybase_command(
                    file_content, temp_input_file_name)
                if (cmd_output.output).find("Unable to open input file") >= 0:
                    raise Exception(
                        "Failed to open the input file given to"
                        " sybase ISQL command.Exiting")
            self.log.info("Load command output for job ID : %s is %s",
                          backup_job_id,
                          cmd_output.output)

        # Making the user database online
        db_status = self.sybase_helper.check_database_state(user_db)
        if not db_status:
            raise Exception("Could not bring the database online after restore and recovery")

        # Fetching table list and contents for validation
        status, table_list_after = self.sybase_helper.get_table_list(user_db)
        table_contents_after = dict.fromkeys(user_tables, None)
        for table in user_tables:
            status, table_contents_after[table] = self.sybase_helper.get_table_content(user_db,
                                                                                       table)

        database_content_status = self.table_validation(table_list_before,
                                                        table_list_after,
                                                        table_contents_before,
                                                        table_contents_after)

        if database_content_status:
            self.log.info("Restore happened successfully and validation passed")
            return True
        else:
            raise Exception("restore data validation failed")

    def directive_file(self, database_list):
        """
        Create directive file on client for ondemand backup with given database list

        Args:
            database_list       (list)      --  list of databases to be added
                                                in directive file

        Returns:
            (str)           -       returns string representing input file
                                    name with complete path

        Raises:
            Exception
                if it fails to copy file to remote machine

        """
        content = ""
        for i in database_list:
            content = "{0}{1}\n".format(content, i)
        self.log.info("Content of input file : %s", content)
        file_name = "dblist.txt"
        file_path = self.sybase_helper.machine_object.join_path(self.sybase_helper.remote_path,
                                                                file_name)
        local_filename = self.sybase_helper.controller_object.join_path(
            self.sybase_helper.common_dir_path, file_name)
        # Create local temp file and write database list on the controller to local file
        self.log.info(
            "Create local temp file and write the"
            " database list on the controller to local file")
        platform = self.sybase_helper.machine_object.os_info
        if platform.lower() == 'unix':
            fp = open(local_filename, 'w', newline='\n')
        else:
            fp = open(local_filename, 'w')
        fp.write(content)
        fp.close()

        # Copy the local file from controller to remote machine
        self.log.info("Copy the local file from controller to remote machine")
        copy_status = self.sybase_helper.machine_object.copy_from_local(
            local_filename, self.sybase_helper.remote_path)
        self.log.info("copy_status :%s", copy_status)
        if copy_status is False:
            raise Exception("Failed to copy file to remote machine.Exiting")
        self.log.info("Directive file created under : %s", file_path)
        return file_path

    def sybase_full_restore(self,
                            user_database_name,
                            user_table_list,
                            timevalue=None,
                            copy_precedence=0,
                            dr_restore_flag=False):
        """

        Performs Full Sybase server restore

        Args:
                user_database_name    (str)     --      database created during the test run

                user_table_list       (list)    --      list of user tables created

                timevalue             (str)     --      for pointintime based restore
                                                        format: YYYY-MM-DD HH:MM:SS
                                                        default : None

                copy_precedence       (int)     --      copy precedence of storage
                                                        policy
                                                        default: 0

                dr_restore_flag       (bool)    --      flag stating if this is
                                                        disaster recovery restore
                                                        default : False


        Returns:
                (bool)      -       returns True if restore
                                    succeeds and validation passed

        Raises:
            Exception

                if shutdown of sybase server fails

                if restore job fails

                if restore validation fails

        """
        database_status = False
        if timevalue:
            point_in_time = True
        else:
            point_in_time = False

        # Fetch data before full server restore for validation
        status, all_database_list_before_restore = self.sybase_helper.get_database_list()
        all_table_list_before_restore = self.get_all_database_tables()
        table_content_before = dict.fromkeys(user_table_list, None)
        for table in user_table_list:
            status, table_content_before[table] = self.sybase_helper.get_table_content(user_database_name,
                                                                                       table)

        # Drop all user databases before full server restore
        self.drop_user_databases(all_database_list_before_restore)

        # check if disaster recovery restore and rename the datafile directory
        if dr_restore_flag:
            self.log.info("Disaster Recovery Sybase Restore Selected")
            self.move_all_data_files(self.sybase_helper.remote_path)

        # Shutdown sybase server before full server restore
        self.sybase_helper.shutdown_sybase_server()
        self.log.info("Shutdown of sybase server is successful")

        # Full server restore initiation
        self.log.info("About to initiate full server restore")
        full_server_restore_job = self.sybase_helper.instance.restore_sybase_server(
            point_in_time=point_in_time,
            timevalue=timevalue,
            copy_precedence=copy_precedence)
        if not full_server_restore_job.wait_for_completion():
            raise Exception(
                "Failed to run Full Server Restore job with error: {0}".format(
                    full_server_restore_job.delay_reason))

        status, all_database_list_after_restore = self.sybase_helper.get_database_list()
        all_table_list_after_restore = self.get_all_database_tables()
        table_content_after = dict.fromkeys(user_table_list, None)
        for table in user_table_list:
            status, table_content_after[table] = self.sybase_helper.get_table_content(user_database_name,
                                                                                      table)

        if all_database_list_before_restore == all_database_list_after_restore:
            database_status = True
        # since its comparison of dict of list for table list of each database
        self.log.info("\n Dict of tables before restore : \n\n")
        self.log.info(all_table_list_before_restore)
        self.log.info("\n Dict of tables after restore : \n\n")
        self.log.info(all_table_list_after_restore)
        if self.comparing_dict_of_list(
                all_table_list_before_restore,
                all_table_list_after_restore):
            table_status = True
        table_content_status = self.comparing_dict_of_list(table_content_before, table_content_after)
        self.log.info("Database status : %s", database_status)
        self.log.info("Database List before : %s", all_database_list_before_restore)
        self.log.info("Database List after : %s", all_database_list_after_restore)
        self.log.info("Table List status after validation : %s", table_status)
        self.log.info("Table Content status after validation : %s", table_content_status)
        if database_status and table_status and table_content_status:
            return True
        else:
            raise Exception("Restore validation failed after full server restore")

    def single_database_restore(self,
                                database_name,
                                user_table_list,
                                expected_table_list=None,
                                destination_client=None,
                                destination_instance=None,
                                timevalue=None,
                                sybase_create_device=False,
                                rename_databases=False,
                                copy_precedence=0,
                                concurrent_flag=False,
                                snap_redirect=False,
                                redirect_path=None):
        """
        Performs single database restore with provided parameters

        Args:
                database_name           (str)     --     name of the database
                                                         to be restored with new name

                user_table_list         (list)    --     list of user tables created

                expected_table_list (list)        --     expected list of tables
                                                         for given user database
                                                         default : None

                destination_client      (str)     --     destination client for restore
                                                         default : None

                destination_instance    (str)     --     destination instance for restore
                                                         default : None

                timevalue               (str)     --     for pointintime based restore
                                                         format: YYYY-MM-DD HH:MM:SS
                                                         default : None

                sybase_create_device    (bool)    --     determines whether to create
                                                         device for database restore
                                                         default : False

                rename_databases        (bool)    --     determines whether
                                                         renamedatabase option chosen
                                                         default : False

                copy_precedence         (int)     --     copy precedence of storage
                                                         policy
                                                         default: 0

                concurrent_flag         (bool)    --     determines whether it is concurrent
                                                         backup based restore or not
                                                         default : False

                snap_redirect           (bool)    --     determines if its snap redirect
                                                         restore or not
                                                         default : False

                redirect_path           (str)    --      redirect path for snap redirect
                                                         restore
                                                         default : None


        Returns:
                (bool)      -       returns True if restore
                                    succeeds and validation passed

        Raises:
            Exception
                if restore job fails

                if restore validation fails

        """
        dev_option = None
        rename_flag = False
        create_instance_flag = False
        source_restore = False
        restore_status = False
        if destination_client is None and destination_instance is None:
            destination_client_object = self.sybase_helper.client
            destination_helper = self.sybase_helper
            source_restore = True
        elif destination_client is None and destination_instance is not None:
            destination_client_object = self.sybase_helper.client
            create_instance_flag = True
        elif destination_client is not None and destination_instance is None:
            destination_client_object = self.sybase_helper.commcell.clients.get(destination_client)
            destination_agent_object = destination_client_object.agents.get("sybase")
            destination_instance_object = destination_agent_object.instances.get(
                self.sybase_helper.instance.instance_name)
            destination_helper = SybaseHelper(self.sybase_helper.commcell,
                                              destination_instance_object,
                                              destination_client_object)
        else:
            destination_client_object = self.sybase_helper.commcell.clients.get(destination_client)
            create_instance_flag = True

        if create_instance_flag:
            destination_agent_object = destination_client_object.agents.get("sybase")
            destination_instance_object = destination_agent_object.instances.get(destination_instance)
            destination_helper = SybaseHelper(self.sybase_helper.commcell,
                                              destination_instance_object,
                                              destination_client_object)

        destination_helper.csdb = self.sybase_helper.csdb
        destination_helper.sybase_sa_userpassword = destination_helper.get_sybase_user_password()
        destination_machine_object = machine.Machine(destination_client_object)
        destination_cv_helper = SybaseCVHelper(destination_helper)

        if expected_table_list is None:
            status, table_list_before = self.sybase_helper.get_table_list(database_name)
        else:
            table_list_before = expected_table_list
        table_content_before = dict.fromkeys(user_table_list, None)
        for table in user_table_list:
            status, table_content_before[table] = self.sybase_helper.get_table_content(database_name,
                                                                                       table)

        if rename_databases and sybase_create_device:
            rename_flag = True
            device_list_source = self.sybase_helper.get_device_name(database_name)
            data_device_name = device_list_source[0]
            log_device_name = device_list_source[1]
            if source_restore:
                new_database_name = database_name
            else:
                new_database_name = "{0}_new".format(database_name)
            if snap_redirect:
                destination_device_path = redirect_path
                new_data_device_name = data_device_name
                new_log_device_name = log_device_name
            else:
                status, destination_device_path = destination_helper.get_device_path()
                new_data_device_name = "{0}_new".format(data_device_name)
                new_log_device_name = "{0}_new".format(log_device_name)

            data_file_name = "{0}_new.dat".format(data_device_name)
            new_data_device_path = destination_machine_object.join_path(destination_device_path,
                                                                        data_file_name)
            log_file_name = "{0}_new.dat".format(log_device_name)
            new_log_device_path = destination_machine_object.join_path(destination_device_path,
                                                                       log_file_name)

            dev_option = {
                database_name:
                    {
                        "datadevicename": data_device_name,
                        "newdatadevicename": new_data_device_name,
                        "newdatadevicepath": new_data_device_path,
                        "logdevicename": log_device_name,
                        "newlogdevicename": new_log_device_name,
                        "newlogdevicepath": new_log_device_path,
                        "newdatabasename": new_database_name
                    }
            }
            self.log.info("dev_option %s", dev_option)
            destination_database = new_database_name
        else:
            destination_database = database_name

        if source_restore and (rename_flag) and (not concurrent_flag):
            drop_status = self.sybase_helper.drop_sybase_database(database_name)
            self.log.info("Database Drop Status before restore: %s for database : %s", drop_status,
                          database_name)
        # Performing restore with given parameters
        restore_job = self.sybase_helper.instance.restore_database(
            destination_client=destination_client,
            destination_instance_name=destination_instance,
            database_list=[database_name],
            timevalue=timevalue,
            sybase_create_device=sybase_create_device,
            rename_databases=rename_databases,
            device_options=dev_option,
            copy_precedence=copy_precedence)
        if not restore_job.wait_for_completion():
            raise Exception(
                "Failed to run Restore job with error: {0}".format(restore_job.delay_reason))

        # data validation after restore
        self.log.info("Getting table details after restore")
        status, table_list_after = destination_helper.get_table_list(destination_database)
        table_content_after = dict.fromkeys(user_table_list, None)
        for table in user_table_list:
            status, table_content_after[table] = destination_helper.get_table_content(destination_database,
                                                                                      table)

        database_content_status = self.table_validation(table_list_before,
                                                        table_list_after,
                                                        table_content_before,
                                                        table_content_after)
        if rename_flag:
            self.log.info("Rename option chosen")
            device_list_destination = destination_helper.get_device_name(new_database_name)
            self.log.info("New Database Device List : %s", device_list_destination)
            status, database_list_after = destination_helper.get_database_list()
            if snap_redirect:
                self.log.info("Snap redirect validation")
                device_name_status = (device_list_source == device_list_destination)
                status, destination_data_device_path = destination_helper.get_device_path(device_list_destination[0])
                status, destination_log_device_path = destination_helper.get_device_path(device_list_destination[1])
                device_path_status = (destination_data_device_path == redirect_path) and (
                        destination_log_device_path == redirect_path)
                device_status = (device_name_status and device_path_status)
            else:
                device_status = (device_list_source != device_list_destination)
            database_status = (new_database_name in database_list_after)
            self.log.info("Device Validation Status: %s", device_status)
            if database_content_status and database_status and device_status:
                restore_status = True
            destination_cv_helper.sybase_cleanup_test_data(new_database_name)
        elif database_content_status:
            restore_status = True
        if restore_status:
            self.log.info("Restore validation succeeded")
            return True
        else:
            raise Exception("Restore data validation"
                            " failed for database :{0}".format(database_name))

    def table_validation(self,
                         table_list_before_restore,
                         table_list_after_restore,
                         table_content_before_restore,
                         table_content_after_restore):
        """
        Compares table list and Table content lists

        Args:
            table_list_before_restore       (list)      --  table list before restore

            table_list_after_restore        (list)      --  table list after restore

            table_content_before_restore    (dict)      --  dict of tables with its
                                                            contents before restore

            table_content_after_restore     (dict)      --  dict of tables with its
                                                            contents before restore


        Returns:

            (bool)      -   returns True if validation of table list and table
                            comparison passes

        Raises:
            Exception
                if table list and content validation fails

        """
        table_status = (table_list_before_restore == table_list_after_restore)
        self.log.info("Table Content dict of list Before restore : ")
        self.log.info(table_content_before_restore)
        self.log.info("Table Content dict of list After restore : ")
        self.log.info(table_content_after_restore)
        table_content_status = self.comparing_dict_of_list(
            table_content_before_restore, table_content_after_restore)
        self.log.info("Table List before : %s", table_list_before_restore)
        self.log.info("Table List after : %s", table_list_after_restore)
        self.log.info("Table List status after validation : %s", table_status)
        self.log.info("Table Content status after validation : %s", table_content_status)
        if table_status and table_content_status:
            return True
        else:
            raise Exception("Table and its content validation failed")

    def get_end_time_of_job(self, job):
        """
        Returns end time of job with additional one minute added to actual time

        Args:
            job     (object)        --  job class object

        Returns:

            (str)       -   return end time of given job with one minute added

        """
        job_end_time_epoch = job.summary["jobEndTime"]
        self.log.info("End Time of job before addition : %s", job_end_time_epoch)
        original = datetime.datetime.fromtimestamp(job_end_time_epoch)
        new = original + datetime.timedelta(minutes=1)
        job_end_time_epoch = time.mktime(new.timetuple())
        end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(job_end_time_epoch))
        self.log.info("End Time of job after addition : %s", end_time)
        return end_time

    def create_sybase_subclient(self, subclient_name, storage_policy, content):
        """
        Creates subclient with given content under given sybase instance

        Args:
            subclient_name  (str)  -- name of subclient to be created

            storage_policy  (str)  -- name of storage policy for subclient

            content         (list) -- list of sybase databases for content

        Returns:
            (obj)   -   subclient object created

        """
        if self.sybase_helper.instance.subclients.has_subclient(subclient_name):
            self.log.info("subclient with name:%s already exists.deleting", subclient_name)
            self.sybase_helper.instance.subclients.delete(subclient_name)
        subclient = self.sybase_helper.instance.subclients.add(subclient_name, storage_policy)
        subclient.content = content
        return subclient

    def move_all_data_files(self, temp_directory):
        """
        Moves all sybase datafiles current path to temporary directory

        Args:
            temp_directory      (str)   --  temporary directory path
                                            to store original datafiles

        Raises:
            Exception
                if source directory doesn't exists

        """
        get_status, source_path = self.sybase_helper.get_device_path()
        status = self.sybase_helper.machine_object.check_directory_exists(source_path)
        if status:
            self.log.info("current data path : %s", source_path)
            self.sybase_helper.machine_object.copy_folder(source_path, temp_directory)
            self.log.info("Datafile directory is copied to temp path."
                          "Delete all files inside source directory")
            self.sybase_helper.machine_object.remove_directory(source_path)
            self.sybase_helper.machine_object.create_directory(source_path, force_create=True)
        else:
            raise Exception("Source directory doesn't exists")
