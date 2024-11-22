# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Helper file to help with Oracle database specific operations

OracleHelper and OracleDMHelper are the classes defined in this file

OracleHelper: Helper class to perform Oracle operations

OracleHelper:
    __init__()                                  -- Constructor of the class

    __del__()                                   -- Destructor of the class

    _execute_ddl_dml()                          -- Executes DDL and DMLs including merge

    _execute_query()                            -- Executes the query and gives the result

    set_oracle_db_username()                    -- Sets oracle database username

    set_oracle_db_password()                    -- Sets oracle database password

    db_connect()                                -- Connects to the database

    db_execute()                                -- Executes DDLs, DMLs and Queries on the database

    alter_db_state()                            -- Alters the state of the database

    recover_standby()                           -- Recovers standby database by log shipping

    switch_logfile()                            -- Switches the logfile of the database.

    db_shutdown()                               -- Shuts down database

    db_startup()                                -- Starts up database

    db_create_tablespace()                      -- creates tablespace in the database

    db_alter_tablespace()                       -- used to make alterations to the tablespace

    db_create_user()                            --  creates database user

    db_create_table()                           -- creates tables and associates it with
                                                    a user and tablespace

    db_fetch_dbf_location()                     -- Fetched default location for datafiles

    check_instance_status()                     -- Checks and displays the instance properties

    validation()                                -- Validates the count of dfs, table records
                                                    after the restore

    create_sample_data()                        -- creates sample schema in the database

    db_create_sample_procedure()                -- creates a sample procedure for sample table

    db_drop_user()                              -- drops user

    fetch_rman_log()                            -- Fetches RMAN log for given
                                                   Job ID from oracle client

    actual_stream_allocation_from_rman()        -- Calculates channels allocated
                                                   in given RMAN log

    expected_stream_based_on_subclient()        -- Calculates expected channel count
                                                   based on subclient content

    stream_validation_for_backup()              -- Perform the stream validation
                                                   based on RMAN log for given backup

    create_subclient()                          -- Create new oracle subclient with
                                                   different oracle specific options

    launch_backup_wait_to_complete()            -- Launches backup on the subclient
                                                   and waits for it's completion.

    stream_validation()                         -- Perform full and incremental job
                                                   on given subclient and
                                                   validate streams used in
                                                   RMAN logs for both the jobs

    get_current_scn()                           -- Fetches teh current SCN value

    get_next_scn()                              -- Fetches the Next SCN value for given
                                                    oracle backup JOBID

    create_rman_restore_script()                -- Creates the RMAN script which can be used
                                                    to recover database after app free restore

    execute_rman_restore_script()               -- Executes the given RMAN script on the client

    get_replication_job()                       -- Fetches the replication job associated with
                                                    live sync operation from commserv database

    get_afileid()                               -- Gets afile id of a backup object for given job
                                                    id and file type

    run_sweep_job_using_regkey()                -- Sets SweepStartTime regkey and waits for the
                                                    sweep job to finish

    is_wallet_enabled()                         -- check and return the wallet_root parameter value

    encrypt_tablespace()                        -- encrypt tablespace using wallet

    get_encrypted_tablespaces()                   --  get list of tablespaces and encryption status

    get_tablespaces()                   --  get list of tablespaces

OracleDMHelper:

Class to perform operations involving oracle and commvault entity for data masking

    __init__()                          --  Constructor of the class

    fetch_one_column()                  --  Fetches single column from given table

    shuffling_validation()              --  Validates shuffling type oracle data masking algorithm
                                            by comparing given set of data before and after masking

    common_compare_validation()         --  Compares two list of
                                            items before and after masking

    fixed_string_validation()           --  Validates fixed string type oracle data
                                            masking algorithm with given set of data

    numeric_type_masking()              --  Perform numeric type
                                            oracle data masking and validates
                                            the data after masking

    char_varchar_type_masking()         --  Performs Character/varchar type masking
                                            and validate the data after masking

    drop_table()                        --  Delete temporary tables
                                            created for masking validation

    masking_data_cleanup()              --  Cleans up the  masking policy created
                                            during data masking testcase


    oracle_data_cleanup()               --  Cleans up the data created before running the backup

OracleRACHelper:
Class to interact with Oracle RAC

    __init__()                          --  Constructor of the class

    get_rac_node_details()              --  Fetches the details of one of the RAC nodes to connect to

    get_nodes()                         --  Fetches teh details of RAC nodes

    db_connect()                        --  Connects to one of the oracle RAC nodes

    check_instance_status()             --  Checks the database mode

    restart_database()                  -- restart the RAC database using srvctl utility

    make_cdb_encrypted()                -- enable wallet encryption by setting up wallet
"""
import random
import string
from time import sleep
import time
import oracledb
from AutomationUtils import logger
from AutomationUtils import machine
from AutomationUtils import constants
from AutomationUtils.database_helper import get_csdb
from AutomationUtils import cvhelper
from AutomationUtils import database_helper
from AutomationUtils.idautils import CommonUtils
from Database.dbhelper import DbHelper


class OracleHelper:
    """
        Class to work on oracle databases
    """
    CONN_SYSBACKUP = 'SYSBACKUP'
    CONN_SYSDBA = 'SYSDBA'
    CONN_DB_USER = 'DBUSER'
    SHUT_TRANSACTION = 'TRANSACTIONAL'
    SHUT_FINAL = 'FINAL'
    SHUT_ABORT = 'ABORT'
    SHUT_IMMEDIATE = 'IMMEDIATE'

    def __init__(self, commcell, db_host, instance, sys_user=None, sys_password=None):
        """Initializes an Oracle Helper Instance

        Args:
            commcell    (obj)   -- commcell object to connect to
            instance    (obj)   -- instance object to connect to
            db_host     (obj)   -- client object to connect to
            sys_user    (str)   -- sys username
            sys_password(str)   -- sys password

        """
        self.log = logger.get_log()
        self.log.info('  Initializing Oracle Helper ...')
        # Commented as these are not required by any methods as of now
        self.commcell = commcell
        self.client = db_host
        # self.agent = agent
        self.instance = instance
        self.csdb = get_csdb()
        self.ora_host_name = db_host
        self.ora_instance = instance.instance_name
        # Service name defaults to instance name
        self.ora_service_name = instance.instance_name
        self.ora_port = 1521
        self.ora_sys_user = sys_user or self.set_oracle_db_username()
        self.ora_sys_password = sys_password or self.set_oracle_db_password()
        self.ora_version = None
        # Instantiate instance variables to hold oracle database object
        self.dns_tns = None
        self.oradb = None
        self.connection = None
        self.controller_object = machine.Machine()
        self.oracle_home = self.instance.oracle_home
        self.base_directory = None
        self.ora_machine_object = None
        self.oracle_helper = None
        self.rds = False

    def get_current_scn(self):
        """Method to return the current SCN
            Returns:
                str     -   string representing the next SCN value of the given backup job id

            Raises:
                Exception:

                    if unable to execute the query to get the SCN

            """
        return self.oradb.get_current_scn()

    def get_next_scn(self, job_id):
        """Method to return the Next SCN for the given oracle backup job

            Args:
                job_id                    (str)   --  the job_id of the Oracle backup job

            Returns:
                str     -   string representing the next SCN value of the given backup job id

            Raises:
                Exception:

                    if unable to execute the query to get the next SCN

            """
        try:
            query = f'select nextSCN from CommCellOracleBackupInfo with (nolock) where jobId={job_id}'

            self.csdb.execute(query)
            cur = self.csdb.fetch_one_row()
            if cur:
                return cur[0]

            raise Exception("Failed to get the Next SCN value for the given jobid")
        except Exception as exp:
            self.log.exception('Failed to get the Next SCN value for the given jobid')
            raise Exception(str(exp))

    def create_rman_restore_script(self, recover_scn, job_id):
        """Method to generate the RMAN script to recover the database after app free restore

                Args:
                    recover_scn    (str)   --  The SCN until which Oracle database needs to be
                                                recovered after app free restore

                    job_id    (str)   --       The jobid of the app free restore job


                Returns:
                    str   --     The RMAN command that is generated using
                                 the provided staging path and SCN
        """
        self.log.info("Creating RMAN restore script")
        staging_path = self.ora_machine_object.join_path(self.base_directory,
                                                         self.ora_machine_object.join_path(
                                                             "Temp", "OracleTemp"))
        libobk_file_path = self.ora_machine_object.join_path(self.base_directory, "libobk.so")
        startup_mount_cmd = "  shutdown immediate;  startup mount;  "
        restore_cmd = f'restore database until scn {recover_scn} ; '
        recover_cmd = f'recover database until scn {recover_scn} ; '
        open_database_cmd = " sql \"alter database open resetlogs\"; "
        exit_cmd = " }  exit ; "
        backup_dir_path = self.ora_machine_object.join_path(staging_path, job_id)

        if self.ora_machine_object.os_info == 'WINDOWS':
            allocate_cmd = (f"  run {{  allocate channel ch1 device type 'sbt_tape' "
                            f"PARMS= \"ENV=(CV_media=FILE, BACKUP_DIR={backup_dir_path})\";")

        else:
            allocate_cmd = (f"  run {{  allocate channel ch1 device type 'sbt_tape' "
                            f"PARMS= \"SBT_LIBRARY={libobk_file_path},"
                            f"ENV=(CV_media=FILE, BACKUP_DIR={backup_dir_path})\"; ")

        final_cmd = (f"{startup_mount_cmd}{allocate_cmd}{restore_cmd}"
                     f"{recover_cmd}{open_database_cmd}{exit_cmd}")
        self.log.info("Generated command is:%s", final_cmd)
        return final_cmd

    def execute_rman_restore_script(self, cmd, temp_input_file_name):
        """Method to create temp file with RMAN command
           and execute the same on remote machine

            Args:
                cmd                     (str)   --  rman command to be
                                                    executed on remote client


                temp_input_file_name    (str)   --  temporary input file to be created
                                                    on controller and copied to remote machine

            Returns:
                object type  -   object of output class for given command

            Raises:
                Exception:

                    If unable to copy file to remote machine
        """
        cv_client_temp_path = self.ora_machine_object.join_path(self.base_directory, "Temp")
        temp_folder_name = "OracleTemp"
        remote_path = self.ora_machine_object.join_path(cv_client_temp_path, temp_folder_name)
        self.ora_machine_object.create_directory(remote_path)

        # Create local temp file and write the the command on the controller to local file
        self.log.info(
            "Create local temp file and write the"
            "command on the controller to local file")

        common_dir_path = self.controller_object.join_path(constants.TEMP_DIR, temp_folder_name)
        self.controller_object.create_directory(
            common_dir_path)
        local_filename = self.controller_object.join_path(common_dir_path, temp_input_file_name)
        self.log.info("Oracle/RMAN Command : %s", cmd)

        if self.ora_machine_object.os_info == 'UNIX':
            file_path = open(local_filename, 'w', newline='\n')
        else:
            file_path = open(local_filename, 'w')
        if cmd is not None:
            file_path.write(cmd)
        else:
            cmd = "exit\n"
            file_path.write(cmd)
        file_path.close()

        self.log.info("File created and command is successfully written")
        # Copy the local file from controller to remote machine
        self.log.info("Copy the local file from controller to remote machine")
        copy_status = self.ora_machine_object.copy_from_local(
            local_filename, remote_path)
        self.log.info("copy_status :%s", copy_status)
        if copy_status is False:
            raise Exception("Failed to copy file to remote machine.Exiting")

        # Execute the RMAN command on remote machine using copied temp file
        remote_file = self.ora_machine_object.join_path(remote_path,
                                                        temp_input_file_name)

        # Create the shell script to invoke RMAN to run the database recover script

        data = {
            'oracle_home': self.oracle_home,
            'oracle_sid': self.ora_instance,
            'remote_file': remote_file
        }

        self.log.info("Run the shell script to recover database on oracle client")
        cmd_output = self.ora_machine_object.execute_script(constants.UNIX_ORACLE_RMAN_RECOVER,
                                                            data)
        self.log.info("Output of Oracle RMAN database recovery script: %s",
                      cmd_output.formatted_output)

        # Cleanup temp file on controller and on remote machine

        self.log.info("Cleanup temp file on controller machine")
        self.controller_object.delete_file(local_filename)
        return cmd_output

    def set_oracle_db_username(self):
        """Gets the db username of the instance from commcell database

            Returns:
                Oracle database username

            Raises:
                Exception:
                    if failed to get the db username of the instance

        """
        try:
            query = ("Select attrVal from app_instanceprop where componentNameId = {0} and"
                     " attrName = 'SQL Connect'".format(self.instance.instance_id))

            self.csdb.execute(query)
            cur = self.csdb.fetch_one_row()
            if cur:
                return cur[0]

            raise Exception("Failed to get the Oracle client name from database")
        except Exception as exp:
            self.log.exception('Failed to get sys user name for the database')
            raise Exception(str(exp))

    def set_oracle_db_password(self):
        """Gets the db password of the instance from the commcell database

            Returns:
                Oracle database password

            Raises:
                Exception:
                    -- if failed to get the db password of the instance

        """
        try:
            query = ("Select attrVal from app_instanceprop where componentNameId = {0} and"
                     " attrName = 'SQL Connect Password'".format(self.instance.instance_id))

            self.csdb.execute(query)
            cur = self.csdb.fetch_one_row()
            if cur:
                password = cur[0]
                return cvhelper.format_string(self.commcell, password)

            raise Exception("Failed to get the Oracle client name from database")
        except Exception as exp:
            self.log.exception('Failed to set oracle sys user password')
            raise Exception(str(exp))

    def db_connect(self, mode=CONN_SYSDBA, host_name=None, ora_instance=None, rds=False):
        """
        Establishes a connection to the database

            Args:
                mode (str/enum) -- DBA role connection
                host_name (str) -- IP of the oracle client
                ora_instance (str) -- Oracle instance name
                rds (bool) -- True if the database is RDS

        """
        self.rds = rds
        self.oradb = database_helper.Oracle(
            self.client,
            ora_instance if ora_instance else self.ora_instance,
            self.ora_sys_password,
            self.ora_sys_user,
            self.ora_port,
            self.ora_service_name,
            mode=mode,
            host_name=host_name,
            rds=rds)

    def create_sample_data(self, tablespace_name, table_limit=1, num_of_files=1, row_limit=10, stored_procedure=False):
        """
        Creates sample data in the database

            Args:
                tablespace_name -- tablespace name
                table_limit     -- number of tables to be created
                row_limit       -- number of rows to be created
                stored_procedure (bool) -- True if stored procedure is to be created

        """
        user = "{0}_user".format(tablespace_name.lower())
        table_prefix = "CV_TABLE_"

        data_file_location = "" if self.rds else self.db_fetch_dbf_location()

        # create a sample tablespace
        self.db_create_tablespace(
            tablespace_name, data_file_location, num_of_files)

        # create a sample user/schema
        self.db_create_user(user, tablespace_name)

        # create table and populate with records
        self.db_create_table(
            tablespace_name, table_prefix, user, table_limit, row_limit)

        # create a stored procedure in the new schema
        if stored_procedure:
            self.db_create_sample_procedure(user, f"{table_prefix}_01")

    def db_create_sample_procedure(self, user, table):
        """
        Creates a Sample Procedure in user's schema
            Args:
                user    (str):  User associated to procedure to be created

                table   (str):  Table_name used in sample procedure

            Raises:
                Exception:
                    -- If procedure is invalid and cannot be created.
        """
        try:
            cmd = f"CREATE or REPLACE PROCEDURE {user}.{user}_procedure \n(id IN NUMBER, name in VARCHAR2) " \
                  f"\nis \nbegin \ninsert into {user}.{table} values(id,name); \nend;"
            self.oradb.execute(cmd)
        except Exception as str_err:
            self.log.exception('Unable to create procedure %s', str_err)
            raise

    def db_drop_user(self, user):
        """
        Drops the user
            Args:
                user    (str): User to be dropped

        """
        self.oradb.drop_user(user)

    def db_fetch_dbf_location(self):
        """
        Fetches default Oracle DBF location

        Returns:
                (str)     --  The default path to the database files
        """
        return self.oradb.fetch_dbf_location()

    def db_execute(self, query, data=None, commit=False):
        """
        Execute DDL/DML/DCL in the database

            Args:
                commit  (str)   -- whether this query should be committed

                data    (List/Tuple/dict)   --  input to the query, default value is None

                query   (str)   --  string representing the DDL/DML/DCL to be executed

            Returns:
                (object) -- Executed query result

        """
        dbresponse = self.oradb.execute(query, data, commit)
        return dbresponse.rows

    def alter_db_state(self, state):
        """
        Changes the state of the database

            Args:
                state  (str)  -- State of the database you want to change the database to
                 accepted values: open, close, mount, dismount, open read only

        """
        states = ['open', 'close', 'mount', 'dismount', 'open read only']
        if state in states:
            self.db_execute(query=f'alter database {state}')
        self.log.info('Database altered')

    def recover_standby(self, apply=True):
        """
        Recovers managed Standy database by starting log shipping or cancels it.

            Args:
                apply (bool)  -- True if log shipping needs to be enabled and cancels log shipping when false
                    default: True

        """

        if apply:
            self.db_execute(query="alter database recover managed standby database disconnect from session")
            self.log.info("Database altered, Managed Standby Recovery active")
        else:
            self.db_execute(query="alter database recover managed standby database cancel")
            self.log.info("Managed Standby recovery cancelled")

    def switch_logfile(self):
        """
        Switches the logfile for the database.

        """

        self.db_execute(query='alter system switch logfile')
        self.log.info("Log switched.")

    def db_connect_to_pdb(self, pdb_name):
        """
        Sets container to connect to the pdb Database
            Args:
                pdb_name  (str)  -- Name of the pluggable database to connect to
        """
        self.db_connect()
        self.db_execute(query="alter pluggable database all open")
        self.db_execute(query=f"alter session set container={pdb_name}")
        self.log.info("Session Altered, switched to %s ", pdb_name)

    def db_drop_pdb(self, pdb_name):
        """
        Drops (Deletes) the given pdb name including the datafiles
            Args:
                pdb_name  (str)  -- Name of the pluggable database to connect to
        """
        self.log.info("Dropping pluggable database %s", pdb_name)
        self.db_connect()
        self.db_execute(query=f"alter pluggable database all open")
        self.db_execute(query=f"alter pluggable database {pdb_name} close")
        self.db_execute(query=f"drop pluggable database {pdb_name} including datafiles")
        self.log.info("Pluggable database %s dropped", pdb_name)

    def get_db_status(self):
        """
        Returns get database status

            Returns:
                (str)       -- string of database status

        """

        query = "select open_mode from v$database"
        con = self.oradb.connection
        self.log.info("type of con in get db status : %s", con)
        cur = con.cursor()
        cur.execute(query)
        result = cur.fetchall()
        db_status = result[0][0]
        return db_status

    def check_instance_status(self, standby=False):
        """
        Checks for the database status.
            Args:
                standby     (bool)  -- True if instance status is being checked for standby
                    default: False
            Raises:
                Exception:
                    ValueError   -- If the database state is invalid

        """
        db_status = self.get_db_status()
        self.log.info('DB DBID: %s', self.instance.dbid)
        self.log.info('DB Status: %s', db_status)
        self.log.info('DB Version: %s', self.ora_version)

        if db_status.strip().upper() != 'READ WRITE':
            if standby==True and db_status.strip().upper() != 'READ ONLY':
                self.log.exception('Database status is invalid: %s', db_status)
                raise ValueError('Invalid database status: {0}'.format(db_status))

    def db_shutdown(self, mode):
        """Shut down the database

            Args:
                mode    (str)   -- Mode of shutdown to be given to the database
                    SHUT_TRANSACTION    : shutdown using TRANSACTIONAL

                    SHUT_FINAL          : shutdown using FINAL

                    SHUT_ABORT          : shutdown using ABORT

                    SHUT_IMMEDIATE      : shutdown using IMMEDIATE

            Raises:
                ValueError:
                    -- If the database connection wasn't established

                    -- If the mode for shutdown is invalid
                DatabaseError:
                    -- Exception in shutting the database down

        """
        if self.connection is None:
            self.log.exception(
                '  Connection to database has not been established')
            raise ValueError(
                'Database connection not established for shutdown')
        try:
            if mode == 'TRANSACTIONAL':
                self.connection.shutdown(
                    mode=oracledb.DBSHUTDOWN_TRANSACTIONAL)
            elif mode == 'FINAL':
                self.connection.shutdown(mode=oracledb.DBSHUTDOWN_FINAL)
            elif mode == 'ABORT':
                self.connection.shutdown(mode=oracledb.DBSHUTDOWN_ABORT)
            elif mode == 'IMMEDIATE':
                self.connection.shutdown(mode=oracledb.DBSHUTDOWN_IMMEDIATE)
            else:
                raise ValueError('Unrecognized mode for shutdown detected: {0}'
                                 .format(mode))
        except oracledb.DatabaseError as str_err:
            self.log.exception('Error shutting The DB %s down: %s', self.ora_instance, str_err)
            raise
        except ValueError as str_err:
            message = 'Unrecognized value {0} for shutting down the database: {1}'.format(
                mode, str_err)
            self.log.exception(message)
            raise

    def db_startup(self, mode=None):
        """
        Start up the database.

            Args:
                mode    (str)  -- The mode to startup the database
                    Values: 'MOUNT', 'OPEN'

            Raises:
                Exception:
                    DatabaseError   -- If the remote connection is rejected

        """
        self.dns_tns = oracledb.makedsn(
            self.ora_host_name, self.ora_port, self.ora_instance)
        try:
            self.connection = oracledb.Connection(self.ora_sys_user,
                                                   self.ora_sys_password, self.dns_tns,
                                                   mode=oracledb.SYSDBA | oracledb.PRELIM_AUTH)
            self.connection.startup()
            if mode:
                self.connection = oracledb.connect(mode=oracledb.SYSDBA)
                if mode == 'MOUNT':
                    cursor = self.connection.cursor()
                    cursor.execute("alter database mount")
                elif mode == 'OPEN':
                    cursor = self.connection.cursor()
                    cursor.execute("alter database mount")
                    cursor.execute("alter database open")

        except oracledb.DatabaseError as str_err:
            message = 'Startup is not supported for remote database connections: {0}'.format(
                str_err)
            self.log.exception(message)
            raise

    def db_create_tablespace(self, tablespace_name, location, num_files):
        """
        Create a tablespace with the a specified number of datafiles

            Args:
                tablespace_name (str)   --    Name given to the newly created tablespace

                location    (str)   --  The datafiles path associated with the tablespace

                num_files   (int)   --  No.of. files tablespace should have at the time of creation

        """

        self.oradb.create_tablespace(tablespace_name, location, num_files)

    def db_alter_tablespace(self, tablespace_name, location, num_files):
        """
        Alter the tablespace by adding additional number of files

            Args:
                tablespace_name (str)   --    Name given to the newly created tablespace

                location    (str)   --  The datafiles path associated with the tablespace

                num_files   (int)   --  No.of. files to be added to the tablespace

        """

        self.oradb.alter_tablespace(tablespace_name, location, num_files)

    def db_create_user(self, user, default_tablespace):
        """
        Create a database user which a defualt tablespace mapping

            Args:
                user    (str)   --  The name of the newly create user/schema

                default_tablespace  (str)   --  The tablespace associated with the user

        """

        self.oradb.create_user(user, default_tablespace)

    def db_create_table(self, tablespace_name, table_prefix, user, number, row_limit=10):
        """
        Create a table and mapped to a tablespace and user

            Args:
                tablespace_name (str)   --  The tablespace associated with the tables

                table_prefix    (str)   --  The prefix associated with the tables
                    Sample: CV_TABLE

                user    (str)   --  The user/schema associated with the tablespace

                number  (int)   --  The number of tables to be created

                row_limit   (int)   --  The number of rows to be populated in each table

        """

        self.oradb.create_table(tablespace_name, table_prefix, user, number, row_limit)

    def db_drop_table(self, user, table):
        """
        Drops a table

            Args:
                user (str) -- The user/schema associated with the tablespace

                table(str) -- The table to be dropped

        """
        self.oradb.drop_table(user, table)

    def db_populate_table(self, tblpref, user=None, number=1):
        """
        Populates data in a table. Appends 10 records every time this  method is called

            Args:
                tblpref (str)   --  The prefix used at the time of creating tables

                user (str)  --  The user who has access to the tablespace and tables

                number (str)    --  Appended to tablepref to get the tablename to be populated

        """
        self.oradb.populate_table(tblpref, user, number)

    def db_tablespace_validate(self, tablespace_name):
        """
        Returns count of datafiles associated with a particular tablespace.

            Args:

                tablespace_name (str) -- The name of the tablespace we want to validate

            Returns:
                (str,int) -- tablespace name and the count of the datafiles in the tablespace

        """

        return self.oradb.tablespace_validate(tablespace_name)

    def db_table_validate(self, user, tablename):
        """
       Returns the records in a particular table.

            Args:
                user (str) -- The user assocaited with the table

                tablename (str) -- The table we want to validate

            Returns:
                (int)     --  The number of records in the table

        """
        return self.oradb.table_validate(user, tablename)

    def validation(
            self,
            tablespace_name,
            num_of_files,
            table,
            records,
            table_count=None,
            host_name=None,
            standby=False):
        """Method validates the tablespace , datafiles and table content

        Args:
            tablespace_name         (str)   --  Tablespace name to be validated

            num_of_files            (int)   --  expected number of datafiles

            table                   (str)   --  name of the table to be validated for records/
                                                table prefix if table_count input is given

            records                 (int)   --  expected rows in the table

            table_count             (int)   --  number of tables to validate

            host_name               (str)   --  IP of the machine

            standby                 (bool)  --  True if vaidation is for standby node
                default: False

        Raise:
            ValueError -- if datatabase status/ TS/ DF is invalid

        """
        self.log.info("****** Validation Start *****")
        self.db_connect(OracleHelper.CONN_SYSDBA, host_name=host_name)
        self.check_instance_status(standby)
        (tbs, datafiles) = self.db_tablespace_validate(tablespace_name)
        if tablespace_name == tbs and (self.rds or num_of_files + 1 == datafiles):
            self.log.info("Tablespace and datafiles validation successful")
        else:
            raise ValueError('Tablespace not found')

        user = "{0}_user".format(tablespace_name.lower())
        if table_count:
            for i in range(1, table_count+1):
                table_name = table+'{:02}'.format(i)
                rec = self.db_table_validate(user, table_name)
                if records == rec:
                    self.log.info("Table %s records validation successful", table_name)
                else:
                    raise ValueError("Table %s records not matching", table_name)
        else:
            rec = self.db_table_validate(user, table)
            if records == rec:
                self.log.info("Table %s records validation successful", table)
            else:
                raise ValueError("Table %s records not matching", table)
            self.log.info("****** Validation complete *****")

    def fetch_rman_log(self, job_id, client_object, job_type):
        """
        Fetches RMAN log for given Job ID from oracle client

            Args:
                job_id              (int)       --  job ID for which RMAN to be fetched

                client_object       (object)    --  Client object to fetch RMAN log from

                job_type            (str)       --  type to determine output file name on client

            Returns:

                (str)      --  string of RMAN log content

            Raises:
                Exception
                    if job type does not fall under available oracle job types

                    if no file exists at the given path for RMAN log

                    if failed to get the contents of the file
        """
        base_oracle_job_types = constants.OracleJobType
        if base_oracle_job_types(job_type.lower()) not in base_oracle_job_types:
            raise Exception(
                "Job Type sent does not fall under available"
                "oracle job types.check the spelling")
        if job_type.lower() in ["backup", "snap backup", "snap to tape"]:
            file_name = "backup.out"
        else:
            file_name = "restore.out"
        client_machine_object = machine.Machine(client_object)
        default_job_path = client_machine_object.join_path("CV_JobResults", "2", "0")
        common_path = client_machine_object.join_path(default_job_path, job_id)
        remote_file_path = client_machine_object.join_path(client_object.job_results_directory,
                                                           common_path, file_name)
        self.log.info("Log File Path to fetch RMAN Log : %s", remote_file_path)
        rman_log_content = client_machine_object.read_file(remote_file_path)

        return rman_log_content

    def actual_stream_allocation_from_rman(self, rman_log, subclient):
        """
        Calculates channels allocated in given RMAN log

            Args:
                rman_log        (str)       --  string containing RMAN log

                subclient       (object)    --  subclient object

            Returns:
                    (int, int)

                (int)   --  actual data channel count

                (int)   --  actual log channel count
        """
        self.log.info("Actual Stream Allocation check : %s", self.instance.instance_name)
        data_script = []
        log_script = []
        rman_split = rman_log.lower().replace("\n", "").split("rman script:")

        if (subclient.data and subclient.backup_archive_log) or (subclient.selective_online_full):
            data_part = rman_split[1]
            log_part = rman_split[2]
            # need to split data script and data output
            data_split = data_part.split("rman log:")
            data_script = data_split[0]
            # need to split log script and log output
            log_split = log_part.split("rman log:")
            log_script = log_split[0]
        elif subclient.backup_archive_log and subclient.data is False:
            log_part = rman_split[1]
            log_split = log_part.split("rman log:")
            log_script = log_split[0]
        elif subclient.data and subclient.backup_archive_log is False:
            data_part = rman_split[1]
            data_split = data_part.split("rman log:")
            data_script = data_split[0]

        # lets get the count of allocate channel statements
        data_count = data_script.count("allocate channel")
        log_count = log_script.count("allocate channel")

        return data_count, log_count

    def expected_stream_based_on_subclient(self, subclient, backup_level):
        """
        Calculates expected channel count based on subclient content

            Args:
                subclient       (object)        --  subclient object

                backup_level       (str)        --  backup  level [full|incremental|online full]

            Returns:
                    (int, int)

                (int)   --  actual data channel count

                (int)   --  actual log channel count

        """
        oracle_properties = subclient._oracle_subclient_properties
        data_status = oracle_properties.get("data")
        log_status = oracle_properties.get("backupArchiveLog")
        data_stream_count = oracle_properties.get("dataThresholdStreams", 1)
        log_stream_count = oracle_properties.get("logThresholdStreams", 1)
        selective_online_status = oracle_properties.get("selectiveOnlineFull", False)

        if data_status and log_status and selective_online_status is False:
            self.log.info("Subclient %s has both data and log selected", subclient.subclient_name)
            data_final_stream = data_stream_count
            log_final_stream = log_stream_count
        elif data_status and log_status is False:
            self.log.info("Subclient %s has only data selected", subclient.subclient_name)
            data_final_stream = data_stream_count
            log_final_stream = 0
        elif data_status is False and log_status:
            self.log.info("Subclient %s has only log selected", subclient.subclient_name)
            data_final_stream = 0
            log_final_stream = log_stream_count
        elif selective_online_status and data_status:
            self.log.info("Subclient %s has selective online option", subclient.subclient_name)
            if (data_stream_count < log_stream_count) and (backup_level == 'online full'):
                data_final_stream = data_stream_count
                log_final_stream = data_stream_count
            else:
                data_final_stream = data_stream_count
                log_final_stream = log_stream_count

        return data_final_stream, log_final_stream

    def stream_validation_for_backup(self, client, subclient, job_id):
        """
        Perform the stream validation based on RMAN log for given backup

            Args:
                client                  (object)    --  object of client class

                subclient               (object)    --  object of subclient  class

                job_id                  (int)       --  job ID

            Returns:
                (bool)                              --  Boolean status for Stream count

                    True  : When stream count and allocate statement count match

            Raises:
                Exception
                    if given job is snap backup

                    if given subclient has FS based backup copy
                    and job is backup copy job

                    if stream validation fails
        """
        # This stream validation is only applicable for
        # regular backup, backup copy jobs and not for snap job
        job_object = self.commcell.job_controller.get(job_id=job_id)
        if job_object.job_type.lower() == 'snap backup':
            raise Exception("This stream validation is not applicable for snap backup jobs")
        elif job_object.job_type.lower() == 'snap to tape':
            if subclient._oracle_subclient_properties['backupCopyInterface'].lower() != "rman":
                self.log.info("No RMAN log for FS based backup copy."
                              "so no stream validation possible")
                raise Exception("This stream validation is not applicable FS based backup copy")
        # fetch RMAN log for given Job ID
        rman_log = self.fetch_rman_log(job_id, client_object=client,
                                       job_type=job_object.job_type.lower())
        expected_data_count, expected_log_count = self.expected_stream_based_on_subclient(
            subclient,
            job_object.backup_level.lower())
        actual_data_count, actual_log_count = self.actual_stream_allocation_from_rman(rman_log,
                                                                                      subclient)
        data_status = (expected_data_count == actual_data_count)
        log_status = (expected_log_count == actual_log_count)
        self.log.info("Subclient : %s", subclient.subclient_name)
        self.log.info("Expected Data Stream Count : %d"
                      "\nActual data Stream Count : %d", expected_data_count,
                      actual_data_count)
        self.log.info("Expected Log Stream Count : %d"
                      "\nActual Log Stream Count : %d", expected_log_count,
                      actual_log_count)

        if data_status and log_status:
            self.log.info("Stream validation succeeded for job : %s", job_id)
            return True
        raise Exception("Stream validation for Job ID : {0} failed".format(job_id))

    def create_subclient(self,
                         subclient_name,
                         storage_policy,
                         snap_engine=None,
                         data_stream=2,
                         data=True,
                         log=False,
                         selective_online=False, backupcopy_interface=0, delete_existing=False):
        """
                Create new oracle subclient or uses if it already exists

                    Args:
                        subclient_name      (str)   --  subclient name

                        storage_policy      (str)   --  storage policy name

                        snap_engine         (str)   --  snap engine name
                                                        default : None

                        data_stream         (int)   --  data stream count
                                                        default : 2

                        data                (bool)  --  whether to enable data or not
                                                        default : True

                        log                 (bool)  --  whether to enable log or not
                                                        default : False

                        selective_online    (bool)  --  enable/disable selective online
                                                        default : False

                        backupcopy_interface (bool) --  type of the interface for backupcopy
                                                        default : 0

                        delete_existing      (bool) --  Deletes the existing subclient if set
                                                        deafult: False

                    Returns:
                        (object)        -- object of subclient class
                """

        if delete_existing:
            try:
                self.log.info("Delete if already the subclient exists with that name")
                self.instance.subclients.delete(subclient_name)
                self.log.info("Recreating the subclient after delete")
                subclient = self.instance.subclients.add(subclient_name, storage_policy)
            except Exception as error:
                self.log.info("delete subclient before creation failed with error : %s", error)
        else:
            if not self.instance.subclients.has_subclient(subclient_name):
                self.log.info(' STEP: Creating Subclient')
                subclient = self.instance.subclients.add(subclient_name, storage_policy)
            else:
                self.log.info("Subclient named %s exists - reusing", subclient_name)
                subclient = self.instance.subclients.get(subclient_name)
        subclient.archive_files_per_bfs = 32
        subclient.data_stream = data_stream
        if data and log is False and selective_online is False:
            subclient.backup_archive_log = False
        elif selective_online:
            subclient.data = False
            subclient.backup_archive_log = False
            subclient.selective_online_full = True
            subclient.data = True
            subclient.backup_archive_log = True

        if snap_engine is not None:
            if not self.client.is_intelli_snap_enabled:
                self.client.enable_intelli_snap()
                self.log.info("Intellisnap is enabled on the client")
            subclient.set_prop_for_orcle_subclient(storage_policy, snap_engine)

            if backupcopy_interface == 0:
                subclient.set_backupcopy_interface('FILESYSTEM')
            elif backupcopy_interface == 1:
                subclient.set_backupcopy_interface('RMAN')
            elif backupcopy_interface == 2:
                if not subclient.is_trueup_enabled:
                    self.log.info("Subclient doesnt have true up enabled, enabling now")
                    subclient.enable_trueup()
                subclient.set_backupcopy_interface('VOLUME')

        subclient.refresh()
        return subclient

    def launch_backup_wait_to_complete(self, subclient, backup_type=r"full"):
        """ Launches a backup job on the specified subclient and waits for it to complete

            Args:
                subclient           (obj)   --  subclient object where the backup isto be triggered.

                backup_level        (str)   --  Level of backup. Can be full or incremental
                                                default: full

        """
        job = subclient.backup(backup_type)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run FULL snap backup job with error: {0}".format(
                    job.delay_reason))
        self.log.info(
            " STEP 1: Full backup JOB ID: %s",
            job.job_id)
        sleep(5)

    def stream_validation(self, client, subclient):
        """
        Perform full and incremental job on given subclient and
        validate streams used in RMAN logs for both the jobs

            Args:
                client          (object)    --  object of client

                subclient       (object)    --  object of subclient

            Returns:
                bool                        --  Validation check for two jobs

                    True   : When stream validation passes for full and incremental job

            Raises:
                Exception
                    if failed to run full job

                    if failed to run incremental job

                    if Stream validation fails


        """
        self.log.info("Stream Validation For Subclient : %s", subclient.subclient_name)
        subclient.refresh()
        # launch full backup job
        full_job = subclient.backup(backup_level="full")
        if not full_job.wait_for_completion():
            raise Exception("Failed to run Full backup job with error: {0}".format(
                full_job.delay_reason))

        # stream validation for full job
        full_status = self.stream_validation_for_backup(client,
                                                        subclient,
                                                        full_job.job_id)
        self.log.info("Full job validation status : %s", full_status)

        # launch incremental backup job
        incremental_job = subclient.backup(backup_level="incremental")
        if not incremental_job.wait_for_completion():
            raise Exception("Failed to run Incremental backup job with error: {0}".format(
                incremental_job.delay_reason))

        # stream validation for full job
        incremental_status = self.stream_validation_for_backup(client,
                                                               subclient,
                                                               incremental_job.job_id)
        self.log.info("Incremental job validation status : %s", incremental_status)

        if full_status and incremental_status:
            self.log.info("For subclient %s , both full and incremental validation passed",
                          subclient.subclient_name)
            return True
        raise Exception("Stream validation failed for {0} subclient".format(
            subclient.subclient_name))

    def get_replication_job(self, backup_job):
        """ method to fetch the replication job associated with
        live sync operation from commserv database

            Args:
                backup_job     (obj)    -- backup job object

            Returns:
                (obj)    --     returns replication job object started
                                by the backup job

            Raises:
                Exception
                    if unable to get replication job ID

        """
        src_instance_id = self.instance.instance_id
        self.log.info("Waiting for 30 seconds to get the replication"
                      " jobid associated with source instance:%s", src_instance_id)
        sleep(30)
        query = (
            "select jobId from RunningRestores where instanceID={0} and "
            "jobStartTime>={1} and opType=105 "
            "order by jobId DESC".format(src_instance_id, backup_job.summary['jobEndTime']))
        self.log.info("Query that is being run on csdb:%s", query)
        count = 0
        while True:
            count += 1
            self.csdb.execute(query)
            cur = self.csdb.fetch_one_row()
            self.log.info("Replication jobid:%s", cur)
            self.log.info("Replication jobid as passed to job controller:%s", cur[0].strip())
            if cur:
                if cur[0] != '':
                    return self.commcell.job_controller.get(cur[0].strip())
                else:
                    if count >= 60:
                        raise Exception("Failed to get the replication Job ID")
                    self.log.info("Sleeping for 30 seconds as replication job is not complete yet")
                    sleep(30)
            else:
                raise Exception(
                    "Failed to get the replication Job ID")

    def oracle_data_cleanup(self, tablespace, tables=None, user=None):
        """
        Cleans up the data created before running the backup
            Args:
                    tablespace      (str)  -- Tablespace name which has to be dropped

                    tables          (list) -- The table to be dropped
                        default:    None

                    user            (str)  -- User of the tablespace
        """
        self.log.info("Dropping the table(s)")
        user = user or self.ora_sys_user
        if tables:
            for table in tables:
                self.oradb.drop_table(user, table)
        self.log.info("Dropping the tablespace")
        self.oradb.drop_tablespace(tablespace)

    def backup_validation(self, jobid, backup_type):
        """
        Validates backup level of job triggered
            Args:
                    jobid           (str)                   --     jobid which needs to be
                                                                   validated on backup completion

                    backup_type     (str):                  --     expected backup type from
                                                                   calling method
                                                                   eg: "Online Full"/
                                                                   "Offline Full"/"Incremental" etc
        """
        common_utils = CommonUtils(self.commcell)
        return common_utils.backup_validation(jobid, backup_type)

    def get_afileid(self, job_id, file_type):
        """Gets afile id of a backup object for given job id and file type
                Args:
                    job_id (int)  -- Backup Job ID to fetch afile ids of the job
                    file_type (int) -- File type
                Returns:
                    afileid (int) -- id for first record from archfile table
                                     for a given job and file type
                Raises:
                    Exception:
                        If no archfile id is retrieved for given job id and file type
        """
        query = "select id from archfile with (nolock) where jobid={0} and fileType={1}".format(
            job_id, file_type)
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
        if cur:
            cur.reverse()
            afileid = cur[len(cur)-1][0]
            return int(afileid)
        raise Exception("Failed to get the arch file ID from cs db")

    def is_log_backup_to_disk_enabled(self):
        """ Method to check if log backup to disk feature is enabled
        for instance or not

        Returns: True if log backup to disk is enabled. False Otherwise

        """
        query = "select * from APP_InstanceProp with (nolock) where componentNameId=" \
                f"{self.instance.instance_id} and attrName='Dump Sweep Schedule' and modified=0"
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
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
        cli_subclient = self.instance.subclients.get('(command line)')
        hours = time.strftime('%H')
        mins = int(time.strftime('%M')) + 2
        time_stamp = int(time.time())
        if media_agent:
            self.log.info("Setting SweepStartTime registry key on MA")
            media_agent_client_obj = self.commcell.clients.get(media_agent)
            media_agent_client_obj.add_additional_setting(
                f"OracleAgent/Sweep/{cli_subclient.subclient_id}",
                "SweepStartTime",
                "STRING",
                f"{hours}:{mins}")
        else:
            self.log.info("Setting SweepStartTime registry Key on CS")
            self.commcell.add_additional_setting(
                f"OracleAgent/Sweep/{cli_subclient.subclient_id}",
                "SweepStartTime",
                "STRING",
                f"{hours}:{mins}")
        try:
            self.log.info("Sleeping for 3 mins before checking sweep job")
            time.sleep(180)
            count = 10
            dbhelper = DbHelper(self.commcell)
            while count:
                count -= 1
                last_job = dbhelper._get_last_job_of_subclient(cli_subclient)
                if last_job:
                    self.log.info("Checking if the job ID:%s is sweep job", last_job)
                    job_obj = self.commcell.job_controller.get(last_job)
                    if "(command line)" in job_obj.subclient_name.lower() and \
                            job_obj.job_type.lower() in "backup" and \
                            job_obj.start_timestamp > time_stamp:
                        break
                self.log.info("Sleeping for 1 minute")
                time.sleep(60)
            if not count:
                raise Exception("Sweep job did not trigger is 10 mins")
            self.log.info("Sweep job:%s", job_obj.job_id)
        except Exception as exp:
            self.log.error("Unable to trigger sweep job")
            raise Exception(exp)
        finally:
            if media_agent:
                self.log.info("Deleting SweepStartTime registry Key from MA")
                media_agent_client_obj.delete_additional_setting(
                    f"OracleAgent/Sweep/{cli_subclient.subclient_id}",
                    "SweepStartTime")
            else:
                self.log.info("Deleting SweepStartTime registry Key from CS")
                self.commcell.delete_additional_setting(
                    f"OracleAgent/Sweep/{cli_subclient.subclient_id}",
                    "SweepStartTime")
            self.log.info(
                "SweepStartTime registry key is deleted Successfully")

    def is_wallet_enabled(self):
        """ Checks if the wallet_root parameter is set"""
        res = self.db_execute(query="select value from v$parameter where name='wallet_root'")
        if res and res[0]:
            return res[0][0]
        return False

    def encrypt_tablespace(self, tablespace_name):
        """ Method to encrypt tablespaces
        Args:rypted tablespace
            tablespace_name (str)   : Name of the tablespace to encrypt
        Returns:
            Name of the enc
        """
        self.db_execute(query=f"alter tablespace {tablespace_name} encryption online encrypt")
        return tablespace_name

    def get_encrypted_tablespaces(self):
        """ Method to get list  of encrypted tablespaces in cdb"""
        res = self.db_execute(query=f"select tablespace_name, encrypted from cdb_tablespaces")
        result = dict()
        for tablespace in res:
            if tablespace[1] == "YES":
                result[tablespace[0]] = True
            else:
                result[tablespace[0]] = False
        return result
    
    def get_tablespaces(self):
        """ Method to get list  of tablespaces in cdb"""
        res = self.db_execute(query=f"select tablespace_name from cdb_tablespaces")
        result = dict()
        for tablespace in res:
            result[tablespace[0]] = "exists"
        list(result.keys())
        return list(result.keys())


class OracleDMHelper:
    """Class to perform operations involving oracle and commvault entity for data masking"""

    def __init__(self, oracle_helper):
        self.oracle_helper = oracle_helper
        self.log = logger.get_log()
        self.test_tables = []
        self.test_policies = []
        self.connection_object = self.oracle_helper.oradb.connection

    def fetch_one_column(self, conn, table_name, column_name):
        """
        Fetches single column from given table

            Args:

                conn        (object)                          --  cx_oracle connection
                                                                  database connection object

                table_name  (str)                             --  table name whose data
                                                                  to be fetched

                column_name  (str)                            --  column name to be retrieved

            Returns:
                list        --      content of given column
        """
        sql = "select {0} from {1}".format(column_name, table_name)
        self.log.info(sql)
        cur = conn.cursor()
        cur.execute(sql)
        data = cur.fetchall()
        content = []
        for i in data:
            tuple_value = i[0]
            content.append(tuple_value)
        cur.close()
        return content

    def shuffling_validation(self, list_before, list_after):
        """
        Validates shuffling type oracle data masking algorithm
        by comparing  given set of data before and after masking

            Args:
                list_before     (list)     -- list of column values before masking

                list_after      (list)     -- list of column values after masking

            Returns:
                (bool)                     --  returns comparison results

                    True    :   When both lists matches based on shuffling validation

                    False   :   When two lists does not match based on shuffling validation
        """
        shuffling_status = False
        equality_status = True
        count = 0
        if len(list_after) == len(list_before):
            for i, j in zip(list_before, list_after):
                if j in list_before:
                    self.log.info(
                        "New value %s is in old list %s", j, list_before)
                    if i != j:
                        self.log.info(
                            "List before value : %s and list after value : %s", i, j)
                        count = count + 1
                else:
                    self.log.info(
                        "Shuffling not applied as new value in list is not existing in old list.")
                    equality_status = False
                    break
            if (count != 0) and (equality_status is True):
                shuffling_status = True
                self.log.info("Shuffling has happened")
        else:
            self.log.info("List length differs before and after masking")
        return shuffling_status

    def common_compare_validation(self, list_before, list_after):
        """
        Compares two list of items before and after masking

            Args:
                list_before     (list)     -- list of column values before masking

                list_after      (list)     -- list of column values after masking

            Returns:

                (bool)                     --  returns validation results

                    True    :   When both lists matches based on compare validation

                    False   :   When two lists does not match based on compare validation
        """
        status = False
        count = 0
        for i, j in zip(list_before, list_after):
            if i != j:
                self.log.info(
                    "List before value : %s and list after value : %s", i, j)
                count = count + 1
        if count == 10:
            status = True
        return status

    def fixed_string_validation(self, fixed_string, list_after):
        """
        Validates fixed string type oracle data
        masking algorithm with given set of data

            Args:

                fixed_string        (str)  -- string used for masking the columns

                list_after          (list) -- list of column values after masking

            Returns:

                (bool)                     --  returns comparison results

                    True    :   When both lists matches based on Fixed string validation

                    False   :   When two lists does not match based on Fixed string validation
        """
        status = False
        count = 0
        for i in list_after:
            if str(i) == fixed_string:
                count = count + 1
            else:
                break
        if count == 10:
            status = True
            self.log.info("Fixed String Algorithm validation succeeded")
        return status

    def numeric_type_masking(self, policy_name, schema_name):
        """
        Perform numeric type oracle data masking and validates
        the data after masking

            Args:

                policy_name     (str)            -- string of data masking policy

                schema_name     (str)            -- name of schema under which
                                                    test tables can be created
            Returns:

                (bool)                     --  returns cnumneric masking validation results

                    True    :   When numeric validation succeeds

                    False   :   When numeric validation fails

            Raises:
                Exception
                    if failed to create data masking policy

                    if failed to run data masking job
        """
        test_status = False
        number_test_table_name = "masking_number"
        self.test_policies.append(policy_name)

        ### create table with number type columns in instance ###
        tbl_name = "{0}.{1}".format(schema_name, number_test_table_name)
        self.test_tables.append(number_test_table_name)
        self.oracle_helper.db_drop_table(user="hr", table=number_test_table_name)
        cursor_object = self.connection_object.cursor()
        sql_query = ("create table {0}(n1 number(30), n2 number(30),"
                     " n3 number(30), n4 number(30))".format(tbl_name))
        try:
            cursor_object.execute(sql_query)
            cursor_object.execute("commit")
        except oracledb.DatabaseError as db_error:
            self.log.error("Ignoring error : %s", db_error)

        cursor_object.close()

        ### insert random data to populated table ###
        cursor_object = self.connection_object.cursor()
        sql1 = ("insert into {0}(n1, n2, n3, n4) select"
                " TRUNC(DBMS_RANDOM.VALUE (1000, 500000), 2),"
                " TRUNC(DBMS_RANDOM.VALUE (1000, 500000), 2),"
                " TRUNC(DBMS_RANDOM.VALUE (1000, 500000), 2),"
                " TRUNC(DBMS_RANDOM.VALUE (1000, 500000), 2)".format(tbl_name))
        sql2 = " from dual CONNECT BY LEVEL < 11"
        sql_query = sql1 + sql2
        cursor_object.execute(sql_query)
        cursor_object.execute("commit")
        cursor_object.close()

        ### fetch table data into temp variables for validation ###
        n1_before = self.fetch_one_column(
            self.connection_object, tbl_name, "n1")
        n2_before = self.fetch_one_column(
            self.connection_object, tbl_name, "n2")
        n3_before = self.fetch_one_column(
            self.connection_object, tbl_name, "n3")
        n4_before = self.fetch_one_column(
            self.connection_object, tbl_name, "n4")

        self.log.info("n1_before: %s", n1_before)
        self.log.info("n2_before: %s", n2_before)
        self.log.info("n3_before: %s", n3_before)
        self.log.info("n4_before: %s", n4_before)

        ### Configure data masking policy ####
        dm_table_name = tbl_name.upper()
        table_list_of_dict = [
            {
                "name": dm_table_name,
                "columns": [{"name": "N1", "type": 0},
                            {"name": "N2", "type": 2, "arguments": ["1000", "2000"]},
                            {"name": "N3", "type": 3, "arguments": ["50"]},
                            {"name": "N4", "type": 1}
                            ]
            }
        ]
        instance = self.oracle_helper.instance
        try:
            policy_deletion_status = instance.delete_data_masking_policy(
                policy_name)
            self.log.info("Policy deletion status : %s", policy_deletion_status)
        except Exception as delete_policy:
            self.log.info("Given data masking policy is not existing : %s", delete_policy)

        policy_creation_status = instance.configure_data_masking_policy(
            policy_name, table_list_of_dict)
        if policy_creation_status:
            self.log.info(
                "Policy : %s created successfully", policy_name)
        else:
            raise Exception("Failed to create data masking policy")

        ### Run data masking job on this instance ###
        dm_job = instance.standalone_data_masking(
            policy_name)

        self.log.info(
            "Data Masking Job : %s is launched ", dm_job.job_id)
        if not dm_job.wait_for_completion():
            raise Exception(
                "Failed to data masking job with error: {0}".format(dm_job.delay_reason))

        self.log.info("Data Masking job Completed. Now we need to validate the masked data")

        ### fetch table data into temp variables for validation ###
        n1_after = self.fetch_one_column(
            self.connection_object, tbl_name, "n1")
        n2_after = self.fetch_one_column(
            self.connection_object, tbl_name, "n2")
        n3_after = self.fetch_one_column(
            self.connection_object, tbl_name, "n3")
        n4_after = self.fetch_one_column(
            self.connection_object, tbl_name, "n4")

        self.log.info("n1_after: %s", n1_after)
        self.log.info("n2_after: %s", n2_after)
        self.log.info("n3_before: %s", n3_after)
        self.log.info("n4_before: %s", n4_after)

        ### Shuffling Algorithm Validation ###
        self.log.info("Shuffling Algorithm Validation")
        shuffling_status = self.shuffling_validation(n1_before, n1_after)

        ### Numeric Range validation ###
        self.log.info("Numeric Range Algorithm Validation")
        numeric_range_status = False
        min_value = 1000
        max_value = 2000
        count = 0
        for i, j in zip(n2_before, n2_after):
            if (i != j) and (j >= min_value) and (j <= max_value):
                log_message = "{0} not equal to {1} and {1} is within range {2}:{3}".format(
                    i, j, min_value, max_value)
                self.log.info(log_message)
                count = count + 1
        if count == 10:
            self.log.info(
                "Numeric Range masking applied successfully to the column")
            numeric_range_status = True

        ### Numeric Variance validation ###
        self.log.info("Numeric Variance Algorithm Validation")
        numeric_variance_status = self.common_compare_validation(
            n3_before, n3_after)

        ### Format preserving encryption validation ###
        self.log.info("FPE Algorithm Validation")
        fpe_status = self.common_compare_validation(n4_before, n4_after)
        if fpe_status is True:
            self.log.info("FPE validation succeeded")

        if shuffling_status and numeric_range_status and numeric_variance_status and fpe_status:
            self.log.info(
                "All types of number masking  algorithm validation succeeded")
            test_status = True

        self.log.info("delete data masking policy :%s ", policy_name)

        return test_status

    def char_varchar_type_masking(self, column_type, policy_name, schema_name):
        """
        Performs Character/varchar type masking and validate the data after masking

            Args:
                column_type     (int)            -- integer representing masking is
                                                    for char type (1) or varchar type (2)


                policy_name     (str)            -- string of data masking policy

                schema_name     (str)            -- name of schema under
                                                    which test tables can be created
            Returns:

                    bool                         -- status of numeric type masking validation

                        True : when numeric masking validation succeeds

                        False : when numeric masking validation Fails

            Raises:
                Exception
                    if failed to create data masking policy

                    if failed to run data masking job
        """
        test_status = False
        fixed_string = ''.join(random.choice(
            string.ascii_lowercase) for i in range(20))
        if column_type == 1:
            test_table_name = "character_masking"
            column_name_prefix = "c"
        else:
            test_table_name = "varchar_masking"
            column_name_prefix = "v"
        self.test_policies.append(policy_name)

        ### create table with char/varchar type columns in instance ###
        cursor_object = self.connection_object.cursor()
        tbl_name = "{0}.{1}".format(schema_name, test_table_name)
        self.test_tables.append(test_table_name)
        self.oracle_helper.db_drop_table(user="hr", table=test_table_name)
        if column_type == 1:
            sql_query = """create table {0}(c1 char(20), c2 char(20), c3 char(20))""".format(
                tbl_name)
        else:
            sql_query = ("create table {0}(v1 varchar(100),"
                         " v2 varchar(100), v3 varchar(100))".format(tbl_name))
        try:
            cursor_object.execute(sql_query)
            cursor_object.execute("commit")
        except oracledb.DatabaseError as db_error:
            self.log.error("Ignoring error : %s", db_error)

        cursor_object.close()

        ### insert random data to populated table ###
        cursor_object = self.connection_object.cursor()
        if column_type == 1:
            sql1 = ("insert into {0}(c1, c2, c3) select  dbms_random.string('U', 20),"
                    " dbms_random.string('U', 20),"
                    " dbms_random.string('U', 20)".format(tbl_name))
        else:
            sql1 = ("insert into {0}(v1, v2, v3) select  dbms_random.string('X', 30),"
                    " dbms_random.string('X', 10),"
                    " dbms_random.string('X', 30)".format(tbl_name))

        sql2 = """  from dual CONNECT BY LEVEL < 11"""
        sql_query = "{0}{1}".format(sql1, sql2)
        cursor_object.execute(sql_query)
        cursor_object.execute("commit")
        cursor_object.close()

        ### fetch table data into temp variables for validation ###
        l1_before = self.fetch_one_column(
            self.connection_object, tbl_name, column_name_prefix + "1")
        l2_before = self.fetch_one_column(
            self.connection_object, tbl_name, column_name_prefix + "2")
        l3_before = self.fetch_one_column(
            self.connection_object, tbl_name, column_name_prefix + "3")

        self.log.info("l1_before :%s", l1_before)
        self.log.info("l2_before :%s", l2_before)
        self.log.info("l3_before :%s", l3_before)

        ### Configure data masking policy ####
        dm_table_name = tbl_name.upper()
        if column_type == 1:
            table_list_of_dict = [
                {
                    "name": dm_table_name,
                    "columns": [{"name": "C1", "type": 0},
                                {"name": "C2", "type": 1},
                                {"name": "C3", "type": 4, "arguments": [fixed_string]}]
                }
            ]
        else:
            table_list_of_dict = [
                {
                    "name": dm_table_name,
                    "columns": [{"name": "V1", "type": 0},
                                {"name": "V2", "type": 1},
                                {"name": "V3", "type": 4, "arguments": [fixed_string]}]
                }
            ]
        instance = self.oracle_helper.instance
        try:
            policy_deletion_status = instance.delete_data_masking_policy(
                policy_name)
            self.log.info("Policy deletion status : %s", policy_deletion_status)
        except Exception as delete_policy:
            self.log.info("Given data masking policy is not existing : %s", delete_policy)
            raise

        policy_creation_status = instance.configure_data_masking_policy(
            policy_name, table_list_of_dict)
        if policy_creation_status:
            self.log.info(
                "Policy : %s created successfully", policy_name)
        else:
            raise Exception("Failed to create data masking policy")

        ### Run data masking job on this instance ###
        dm_job = instance.standalone_data_masking(
            policy_name)

        self.log.info(
            "Data Masking Job : %s is launched ", dm_job.job_id)
        if not dm_job.wait_for_completion():
            raise Exception(
                "Failed to data masking job with error: {0}".format(dm_job.delay_reason))

        self.log.info("Data Masking job Completed. Now we need to validate the masked data")

        ### fetch table data into temp variables for validation ###
        l1_after = self.fetch_one_column(
            self.connection_object, tbl_name, column_name_prefix + "1")
        l2_after = self.fetch_one_column(
            self.connection_object, tbl_name, column_name_prefix + "2")
        l3_after = self.fetch_one_column(
            self.connection_object, tbl_name, column_name_prefix + "3")

        self.log.info("l1_after :%s", l1_after)
        self.log.info("l2_after :%s", l2_after)
        self.log.info("l3_after :%s", l3_after)

        ### Shuffling Algorithm Validation ###
        self.log.info("Shuffling Algorithm Validation")
        shuffling_status = self.shuffling_validation(l1_before, l1_after)

        ### Format preserving encryption validation ###
        self.log.info("FPE Algorithm Validation")
        fpe_status = self.common_compare_validation(l2_before, l2_after)
        if fpe_status is True:
            self.log.info("FPE validation succeeded")

        ### Fixed String validation ###
        self.log.info("Fixed String Algorithm Validation")
        fixed_string_status = self.fixed_string_validation(
            fixed_string, l3_after)

        if shuffling_status and fpe_status and fixed_string_status:
            self.log.info(
                "All algorithms of char/varchar type masking succeeded")
            test_status = True
        return test_status

    def masking_data_cleanup(self):
        """
        Cleans up the  masking policy created
        during data masking testcase
        """
        self.log.info("Table drops")
        table_list = self.test_tables
        for i in table_list:
            self.oracle_helper.db_drop_table(user="hr", table=i)
        self.connection_object.close()
        self.log.info("Policy deletion")
        policy_list = self.test_policies
        for i in policy_list:
            status = self.oracle_helper.instance.delete_data_masking_policy(i)
            if status is True:
                self.log.info("Policy %s deleted successfully", i)


class OracleRACHelper(OracleHelper):
    """
        Class to work on oracle RAC databases
    """
    def __init__(self, commcell, db_host, instance,admin_user_commcell=None):
        """Initializes an Oracle RAC Helper Instance

        Args:
            commcell    (obj)   -- commcell object to connect to
            instance    (obj)   -- instance object to connect to
            db_host     (obj)   -- client object to connect to
            admin_user_commcell  (bool)  -- Commcell object using admin credentials
                                   default = None
        """
        self.log = logger.get_log()
        self.log.info('  Initializing Oracle RAC Helper ...')
        # Commented as these are not required by any methods as of now
        self.commcell = commcell
        self.client = db_host
        self.instance = instance
        self.csdb = get_csdb()
        self.ora_instance = instance.instance_name
        # Service name defaults to instance name
        self.ora_port = 1521
        self.ora_version = None
        self.admin_user_commcell = None
        if admin_user_commcell:
            self.admin_user_commcell = admin_user_commcell
        # Node details to connect to the RAC setup for creating test data
        self.node_details = self.get_rac_node_details()
        self.node_client = self.get_node_client_object()
        # Instantiate instance variables to hold oracle database object
        self.dns_tns = None
        self.oradb = None
        self.connection = None
        self.ora_sys_user = self.node_details['oraUser']
        self.rds = False

    def get_rac_node_details(self):
        """Fetches the details of one of the RAC nodes to connect to"""
        try:
            query = (
                "Select Top 1 O.name, O.oracleHome, O.InstanceOraUser, O.InstanceOraPasswd, O.clientId, C.net_hostname "
                "from APP_OracleRacInstance O INNER JOIN APP_Client C WITH (NOLOCK) ON O.clientId = C.id where O.instaceId in "
                "(Select DISTINCT A.instance from APP_Application A WITH (NOLOCK) where A.clientId = {0}) AND O.instaceId in "
                "(Select I.id from APP_InstanceName I WITH (NOLOCK) where I.name = '{1}') AND O.InstanceOraUser <> '/';".format(
                    self.client.client_id, self.ora_instance))

            self.csdb.execute(query)
            cur = self.csdb.fetch_all_rows()
            commcell_obj=self.commcell
            if self.admin_user_commcell:
                commcell_obj=self.admin_user_commcell
            if cur:
                return {
                    'name': cur[0][0],
                    'oraHome': cur[0][1],
                    'oraUser': cur[0][2],
                    'oraPasswd': cvhelper.format_string(commcell_obj, cur[0][3]),
                    'clientId': cur[0][4],
                    'hostname': cur[0][5]
                }
            raise Exception("Failed to get the Oracle RAC node details from database")
        except Exception as exp:
            self.log.exception('Failed to set Oracle node details')
            raise Exception(str(exp))

    def get_node_client_object(self):
        """
        Returns the CvPySDK client object of one of the RAC nodes
        """
        return self.commcell.clients.get(self.node_details['hostname'])

    def get_nodes(self):
        """
        Returns client names of nodes of RAC instance
        """
        try:
            query = (
                "SELECT distinct C.id, C.name FROM APP_Client C INNER JOIN APP_OracleRacInstance O"
                " ON C.id = O.clientId INNER JOIN APP_Application A ON A.instance = O.instaceId AND"
                " A.clientId = {0} AND A.appTypeId = 80 INNER JOIN APP_InstanceName I ON"
                " A.instance = I.id AND I.name = '{1}'".format(self.client.client_id, self.ora_instance))

            self.csdb.execute(query)
            cur = self.csdb.fetch_all_rows()

            if cur:
                return {node[1]: int(node[0]) for node in cur}
            raise Exception("Failed to get the Oracle RAC node details from database")
        except Exception as exp:
            self.log.exception('Failed to set Oracle node details')
            raise Exception(str(exp))

    def db_connect(self, mode=OracleHelper.CONN_SYSDBA):
        """
        Connects to the database by using node details
        Args:
            mode    (obj)   -- SQLPlus Connection Mode like CONN_SYSDBA for connecting as sysdba
        """

        self.oradb = database_helper.Oracle(
            self.node_client,
            self.node_details['name'],
            self.node_details['oraPasswd'],
            self.node_details['oraUser'],
            self.ora_port,
            self.node_details['name'],
            mode)

    def check_instance_status(self):
        """
        Checks for the database status.
            Raises:
                Exception:
                    ValueError   -- If the database state is invalid

        """
        db_status = self.get_db_status()
        self.log.info('DB Instance: %s', self.instance.name.upper())
        self.log.info('DB Status: %s', db_status)
        self.log.info('DB Version: %s', self.instance.properties['version'])

        if db_status.strip().upper() != 'READ WRITE':
            self.log.exception('Database status is invalid: %s', db_status)
            raise ValueError('Invalid database status: {0}'.format(db_status))

    def restart_database(self, machine_obj, unique_name, startup_option='open'):
        """ Method to restart the database using srvctl utility
        Args:
            machine_obj (obj)   --  Machine class object for client node
            unique_name (str)   --  DB unique name
            startup_option(str) --  start up mode open/mount/no mount
                Default:    "open"
        """
        data = {'db_unique_name': unique_name, 'startup_option': startup_option}
        machine_obj.execute_script(constants.UNIX_ORACLE_RESTART_DB, data)

    def make_cdb_encrypted(self, unique_name, wallet_dir, machine_obj):
        """ Method to encrypt database using the makeCDBEncrypted.sh script
        Args:
            unique_name (str):  db unique name
            wallet_dir  (str):  directory to set up wallet
            machine_obj (obj):  machine object for client node
        """
        tde_dir = machine_obj.join_path(wallet_dir, 'tde')
        machine_obj.create_directory(tde_dir)
        self.db_connect()
        self.db_execute(query=f"alter system set WALLET_ROOT='${wallet_dir}' scope=spfile")
        self.restart_database(machine_obj, unique_name, 'nomount')
        self.db_connect()
        self.db_execute(query=f'ALTER SYSTEM SET TDE_CONFIGURATION = "KEYSTORE_CONFIGURATION=FILE" scope = spfile')
        self.restart_database(machine_obj, unique_name)
        self.db_connect()
        wallet_password = 'test'
        self.db_execute(query=f"administer key management create keystore '{tde_dir}' identified by {wallet_password}")
        self.db_execute(query=f'administer key management set keystore open identified by {wallet_password}')
        self.db_execute(query=f'administer key management set key identified by {wallet_password} with backup')
        self.db_execute(query=f"administer key management create auto_login keystore from keystore '{tde_dir}' identified by {wallet_password}")
        self.restart_database(machine_obj, unique_name)


    def validation(
            self,
            tablespace_name,
            num_of_files,
            table,
            records,
            table_count=None,
            host_name=None,
            standby=False):
        """Method validates the tablespace , datafiles and table content for Oracle RAC

        Args:
            tablespace_name         (str)   --  Tablespace name to be validated

            num_of_files            (int)   --  expected number of datafiles

            table                   (str)   --  name of the table to be validated for records/
                                                table prefix if table_count input is given

            records                 (int)   --  expected rows in the table

            table_count             (int)   --  number of tables to validate

            host_name               (str)   --  IP of the machine

            standby                 (bool)  --  True if vaidation is for standby node
                default: False

        Raise:
            ValueError -- if datatabase status/ TS/ DF is invalid

        """
        self.log.info("****** Validation Start *****")
        self.db_connect(OracleHelper.CONN_SYSDBA)
        self.check_instance_status()
        (tbs, datafiles) = self.db_tablespace_validate(tablespace_name)
        if tablespace_name == tbs and (num_of_files + 1 == datafiles):
            self.log.info("Tablespace and datafiles validation successful")
        else:
            raise ValueError('Tablespace not found')

        user = "{0}_user".format(tablespace_name.lower())
        if table_count:
            for i in range(1, table_count+1):
                table_name = table+'{:02}'.format(i)
                rec = self.db_table_validate(user, table_name)
                if records == rec:
                    self.log.info("Table %s records validation successful", table_name)
                else:
                    raise ValueError("Table %s records not matching", table_name)
        else:
            rec = self.db_table_validate(user, table)
            if records == rec:
                self.log.info("Table %s records validation successful", table)
            else:
                raise ValueError("Table %s records not matching", table)
            self.log.info("****** Validation complete *****")
            
    def get_tablespaces(self):
        """ Method to get list  of tablespaces in cdb"""
        res = self.db_execute(query=f"select tablespace_name from cdb_tablespaces")
        result = dict()
        for tablespace in res:
            result[tablespace[0]] = "exists"
        list(result.keys())
        return list(result.keys())


