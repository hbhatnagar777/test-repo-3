# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Db2helper file for performing DB2 operations

DB2 is the only class defined in this file

DB2: Helper class to perform DB2 operations

DB2:
====
    __init__()                              -- initializes DB2 Helper object

    get_db2_password()                      -- Gets the db2 password of the instance

    modify_db2_instance_password            -- Changes the password of db2 instance at OS level

    get_db2_username()                      -- Gets the db2 username of the instance

    reconnect()                             -- reconnects to given database name

    run_backup()                            -- triggers backup job

    run_restore()                           -- Starts restore job

    get_datafile_location()                 -- retrieves tablespace datafile location

    prepare_data()                          -- create sample data in test tablespace

    rename_datafile()                        -- Cleaning up test data before restore

    create_tablespace()                     -- creates sample tablespace

    drop_tablespace()                       -- method to drop tablespace

    create_table2()                         -- creates sample data table in sample tablespace

    get_active_logfile()                    -- Fetches active logfile number by connecting
    to db2 database

    add_data_to_database()                  -- Adds some tablespaces and tables in the database

    remove_existing_logs_dir()              -- Removes the existing logs directory of database

    drop_database_on_client()               -- Drops the database from the client

    get_redirect_path()                     -- Fetches the redirect path of the given database

    backup_validation()                     -- validates backup image timestamp with db2
    history file

    container_path_validation               -- validates the container path

    restore_validation()                    -- validates restore job by checking if data restored
    is accessible or not

    log_backup_validation()                 -- validates db2 log backup by connecting
    to commserve database

    get_backup_time_stamp_and_streams()     -- records the db2 image time stamp and streams of
    given backup job id

    get_database_state()                    -- checks if database is in active state or backup
    pending state

    disconnect_applications()               -- disconnects all the database connections

    exec_immediate_method()                 -- executes given db2 command

    update_db2_database_configuration1()    -- updates db2 db configurations

    get_db2_version()                       -- returns db2 application version

    get_db2_information()                   -- gets database list, db2 home directory for the
    given db2 instance

    close_db2_connection()                  -- closes ibm_db db2 connection

    list_database_directory()               -- returns list of databases for the given db2 instance

    get_database_aliases_helper()           -- returns database alias names

    third_party_command_backup()            -- used to trigger command line backup job for database

    third_party_command_restore()           -- triggers command line restore job for database

    third_party_command_rollforward()       -- triggers command line rollforward for database

    third_party_command_recover()           -- triggers command line recover database

    db2_archive_log()                       -- uses command line to archive db2 logs

    third_party_command()                   -- method to execute third party commands

    db2_cold_backup()                       -- triggers cold backup

    restore_from_cold_backup()              -- triggers restore from cold backup

    compare_db2_versions()                  -- compare db2 version

    get_database_port()                     --  Get Database port for instance

    create_storage_group()                  --  Creates storage group

    drop_storage_group()                    --  Drops storage group

    is_index_v2_db2()                       -- Checks if client is Indexing V2

    get_database_encropts_csdb()            --  Get Database encryption options from CSDB

    get_database_encropts_client()          --  Get Database encryption options from Client

    run_sweep_job_using_regkey()            -- Adds SweepStartTime registry key to Db2Agent command line subclient
                                               properties

    csdb_object_to_execute()                -- Used to create a CSDB object with read and write permissions

    verify_one_min_rpo()                    -- Verifies if given backup job has one min rpo enabled

    get_chain_number()                      -- Fetches the chain number of DB used while initializing db2 helper

    get_mountpath()                         -- Fetches dump location of command line subclient logs in MA

    verify_logs_on_ma()                     -- Verifies if archived logs are available inside Dump location on MA

    verify_one_min_rpo_backupset_level()    -- Verifies if one min rpo is enabled from backupset properties in CSDB

    create_sweep_schedule_policy()          -- Creates sweep schedule policy to enable disk cache from GUI

    db2_load_copy()                         -- Generates load copy images of given db inside client

    get_mountpath_load_copy()               -- Returns the load copy dump location inside MA

    verify_load_copy_images_on_ma()         -- Verifies if load copies images generated are present inside MA or not

    gui_out_of_place_restore_same_instance()-- Runs GUI OOP Restore to same instance different DB

    gui_inplace_log_only_restore()          -- Method to run log only restore for all log files, log range and time
                                               based log only restore

    get_backupset_log_retrieve_path()       -- Method to get DB2 log retrieve path on client for the backupset
                                               used while initializing db2 helper

    verify_retrieve_logs_on_client()        -- Method to verify if the restored logs are available in DB2 retrieve path
                                               inside client

    delete_logs_from_retrieve_location()    -- Method to delete all log files present in retrieve location of backupset
                                               used for initializing db2 helper object

    verify_encryption_key()                 -- Method to Verify if the sweep job uses same encryption key for all
                                               archfiles backed up in a single sweep job

    rotate_encryption_key()                 -- Method to disable the encryption key related to encryption key id passed

    get_active_ma()                         -- Method to return the active ma used by command line subclient when having
                                               multiple ma's

"""

import time
import ibm_db
from AutomationUtils import logger
from AutomationUtils import database_helper
from Database.dbhelper import DbHelper
from AutomationUtils import cvhelper
from AutomationUtils.database_helper import Db2
from AutomationUtils import machine
from datetime import datetime, timedelta
from AutomationUtils.config import get_config
from AutomationUtils.database_helper import MSSQL
from datetime import date


class DB2(object):
    """Helper class to perform DB2 operations"""

    def __init__(self, commcell, client, instance, backupset, port=None):
        """Initializes DB2helper object

            Args:
                commcell             (obj)  --  Commcell object

                client               (obj)  --  Client object

                instance             (obj)  --  db2 instance object

                backupset            (obj)  --  backupset object

                port                 (int)  --  db2 database port
                    default -- None
        """
        self.is_pseudo_client = False
        self.log = logger.get_log()
        self.log.info('  Initializing db2 Helper ...')
        self.commcell = commcell
        self.client = client
        self.instance = instance
        self.backupset = backupset
        self._database = self.backupset.backupset_name
        self._hostname = self.client.client_hostname
        self._csdb = database_helper.get_csdb()
        self._protocol = "TCPIP"
        self._db_user = None
        self.get_db2_username()
        self._db_password = None
        self.get_db2_password()
        self.log.info(" db2 user name is %s", self._db_user)
        self._db2_home_path = self.instance.home_directory
        self.machine_object = machine.Machine(self.client)
        self.machine_db2object = machine.Machine(
            machine_name=self.client.client_name,
            username=self._db_user,
            password=self._db_password)
        self._port = str(port) if port else self.get_database_port()
        if self._db_password != "":
            self.db2 = Db2(
                self._database,
                self._hostname,
                self._port,
                self._protocol,
                self._db_user,
                self._db_password)
            self._connection = self.db2._connection
        self.platform = self.machine_object.os_info
        self.db2_profile = ""
        self.simpana_instance = self.client.instance
        self.simpana_base_path = self.machine_object.get_registry_value(
            "Base", "dBASEHOME")
        if self.platform.upper() == 'WINDOWS':
            self.db2cmd = " set-item -path env:DB2CLP -value **$$** ; set-item -path env:DB2INSTANCE -value \"%s\" ;" \
                          "db2 -o  " % self.instance.name
            self.load_path = r"{0}\Db2Sbt.dll".format(self.simpana_base_path)
        else:
            self.db2cmd = ""
            self.load_path = "{0}/libDb2Sbt.so".format(self.simpana_base_path)
        self.get_db2_information()

    def get_db2_password(self):
        """Gets the db2 password of the instance

                Raises:
                    Exception:
                        if failed to get the db password of the instance """
        query = f"select password from app_credentials where credentialName='{self.instance.properties['credentialEntity']['credentialName']}'"
        self._csdb.execute(query)
        cur = self._csdb.fetch_one_row()
        if cur:
            self._db_password = cvhelper.format_string(
                self.commcell, cur[0])
            self.log.info("Password for db2 database is fetched Successfully")
        else:
            raise Exception("Failed to get the db2 database password")

    def modify_db2_instance_password(self, new_password):
        """ Modify db2 instance password"""
        try:
            if "windows" in self.client.os_info.lower():
                db_user = self._db_user.split("\\")[1]
                command = f"net user {db_user} {new_password}"
            else:
                command = f"echo '{self._db_user}:{new_password}' | chpasswd"
            self.machine_object.execute(command)
        except Exception as excp:
            raise Exception("Exception in modifying instance password: {0}".format(excp))

    def get_db2_username(self):
        """Gets the db2 username of the instance
                        Raises:
                            Exception:
                                if failed to get the db username of the instance """
        query = f"select userName from app_credentials where credentialName='{self.instance.properties['credentialEntity']['credentialName']}'"
        self._csdb.execute(query)
        cur = self._csdb.fetch_one_row()
        if cur:
            self._db_user = cur[0]
            self.log.info("Username for db2 database is fetched Successfully")
        else:
            raise Exception("Failed to get the db2 database username")

    def reconnect(self):
        """
        Reconnects to the db2 database

        Raises:
            Exception:
                if connection to db fails

        """
        try:
            self.db2._connect()
            self._connection = self.db2._connection
            self.log.info("Reconnecting to db2 database")
        except Exception as excp:
            raise Exception("Exception in reconnect: {0}".format(excp))

    def run_backup(self, subclient, backup_type, **kwargs):
        """Starts backup job

        Args:

            subclient   (obj)       --  Specify the subclient object name where backups
                                             needs to be run
            backup_type (str)       --  specify the backup type needs to be run say
                                        FULL or INCREMENTAL or DIFFERENTIAL

            create_backup_copy_immediately  (bool)  --  Run backup copy with the job
                default: False

            backup_copy_type                        (int)   --  backup copy job to be launched
                                                                based on below two options
             default : 2,
             possible values :
                        1 (USING_STORAGE_POLICY_RULE),
                        2( USING_LATEST_CYCLE)
        Returns:
                        (obj)       --  job object will be returned
        Raises:
                Exception:

                    if failed to run backup

        """
        self.log.info("Starting subclient %s Backup ", backup_type)
        create_backup_copy_immediately = kwargs.get("create_backup_copy_immediately")
        if create_backup_copy_immediately:
            job = subclient.db2_backup(backup_level=backup_type,
                                       **kwargs)
        else:
            job = subclient.backup(backup_level=backup_type)
        self.log.info("Started: backup with Job ID: %s job_id ",
                      job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run: {0} backup_type backup job with error: {1} delay_reason ".
                format(backup_type, job.delay_reason))
        self.log.info("Successfully finished backup_type %s backup_type ",
                      backup_type)

        return job

    def run_restore(self, backupset, recover_db=True, restore_data=True, copy_precedence=None,
                    roll_forward=True, restore_logs=True):
        """Starts restore job
        Args:

            backupset       (Backupset)     --  Backupset object

            recover_db      (bool)    -- boolean value to specify if db needs to be recovered

                    default: True

            restore_data            (bool)  -- Restore data or not
                    default: True

            copy_precedence         (int)   -- Copy precedence to perform restore from
                default : None

            roll_forward (bool)  -   Rollforward database or not
                default: True

            restore_logs (bool)  -   Restore the logs or not
                default: True

        Returns:
            (obj)   --  job object

        Raises:
                Exception:

                    if failed to run restore

        """
        if not copy_precedence:
            copy_precedence = None
        job = backupset.restore_entire_database(
            recover_db=recover_db, restore_incremental=recover_db,
            restore_data=restore_data, copy_precedence=copy_precedence,
            roll_forward=roll_forward, restore_logs=restore_logs)
        self.log.info(
            "Started: FULL restore with Job ID: %s", job.job_id)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run: {0} restore job with error: {1} delay_reason ".
                format(job.job_id, job.delay_reason))
        self.log.info("Successfully finished restore ")

        return job

    def get_datafile_location(self):
        """
        Retrieves datafile location.

        Returns:
            (str)       --      tablespace location.

        Raises:
            Exception: if tablespace is not found

        """
        try:
            cmd = "select path from sysibmadm.dbpaths where type = 'DBPATH'"
            self.log.info(cmd)
            try:
                stmt = ibm_db.exec_immediate(self._connection, cmd)
            except Exception as excp:
                raise Exception(
                    "Failed to get datafile with error: {0}".format(excp))
            datafile_location = ibm_db.fetch_assoc(stmt)
            self.log.info(datafile_location)
            for value in datafile_location.values():
                val = value
                self.log.info("Data file Location is: %s", value)
            return val
        except Exception as excp:
            raise Exception(
                "Exception in get_datafile_location: {0}".format(excp))

    def prepare_data(self, table_name):
        """
        Method for getting table content,tablespace list and count.

        Args:

             table_name  (str) - name of the table

        Returns:
            table_content       (str) - table contents like number of rows
            tablespaces_list    (list) - list of tablespaces
            tablespace_count    (int) - number of tablespaces

        Raises:
              Exception:
                If unable to retrieve any of these information

        """
        try:
            table_content = self.db2.get_table_content(table_name)
            (tablespaces_list, tablespace_count) = self.db2.get_tablespaces()
            return table_content, tablespaces_list, tablespace_count

        except Exception as excp:
            raise Exception("Exception in prepare_data : {0}".format(excp))

    def rename_datafile(self, tablespace_name):
        """
        Cleaning up test data before restore

        Args:
            tablespace_name -- name of the tablespace
        """
        datafile = self.get_datafile_location()
        self.log.info("Cleaning up test data before restore ")
        if "{0}{1}_Full.dbf".format(datafile, tablespace_name):
            self.machine_object.rename_file_or_folder(
                "{0}{1}_Full.dbf".format(
                    datafile, tablespace_name),
                "{0}{1}_Full.dbf.ORG".format(datafile, tablespace_name))

    def create_tablespace(self, datafile, tblspace_name,
                          flag_create_tablespace):
        """
        Method to create tablespace

        Args:
            datafile (str)                  -- datafile location where tablespace can
            hold the physical file

            tblspace_name (str)             -- name of the tablespace

            flag_create_tablespace (bool)   -- flag to create tablespace or not

        Returns:

            (bool)      -   method return false if drop tablespace fails
            (bool)      -   tablespace creation fails


        """
        if flag_create_tablespace:
            cmd = "select tbsp_name from sysibmadm.tbsp_utilization where tbsp_name = '{0}'".format(
                tblspace_name)
            stmt = ibm_db.exec_immediate(self._connection, cmd)
            tablespaces = ibm_db.fetch_assoc(stmt)
            if tablespaces:
                tablespaces = str(tablespaces.items())
                self.log.info("tablespace exists : %s", tablespaces)
                cmd = "drop tablespace {0}".format(tblspace_name)
                output = ibm_db.exec_immediate(self._connection, cmd)
                if output:
                    self.log.info("tablespace dropped successfully")
                else:
                    self.log.info("tablespace not dropped successfully")
                    return False

            datafile1 = "{0}{1}_Full.dbf".format(datafile, tblspace_name)

            cmd = (
                "CREATE TABLESPACE {0} MANAGED BY DATABASE "
                "USING (FILE '{1}' 100M ) AUTORESIZE NO ".format(tblspace_name, datafile1))

            output = ibm_db.exec_immediate(self._connection, cmd)
            if output:
                self.log.info("Created tablespace successfully")
            else:
                self.log.info(
                    "tablespace is not created successfully :%s", output)
        return False

    def drop_tablespace(self, tblspace_name):
        """
        Method to drop tablespace

        Args:

            tblspace_name (str)             -- name of the tablespace

        Returns:

            (bool)      -   method return false if drop tablespace fails

        """

        cmd = "select tbsp_name from sysibmadm.tbsp_utilization where tbsp_name = '{0}'".format(
            tblspace_name)
        stmt = ibm_db.exec_immediate(self._connection, cmd)
        tablespaces = ibm_db.fetch_assoc(stmt)
        if tablespaces:
            tablespaces = str(tablespaces.items())
            self.log.info("tablespace exists : %s", tablespaces)
            cmd = "drop tablespace {0}".format(tblspace_name)
            output = ibm_db.exec_immediate(self._connection, cmd)
            if output:
                self.log.info("tablespace dropped successfully")
                return True
            self.log.info("tablespace not dropped successfully")
            return False
        else:
            self.log.info("Tablespace doesn't exists")
            return True

    def create_table2(self, datafile, tablespace_name,
                      table_name, flag_create_tablespace):
        """ creates table in the given tablespace

            Args:

                datafile                (str)       -- datafile location

                tablespace_name         (str)       -- name of the tablespace

                table_name              (str)       -- name of the table

                flag_create_tablespace  (bool)      -- set flag to create or not the tablespace

            Returns:

                (bool)  - returns false if table creation fails

        """
        self.create_tablespace(
            datafile, tablespace_name, flag_create_tablespace)

        cmd = "create table {0} (name varchar(30), ID decimal) in {1} ".format(
            table_name, tablespace_name)

        output = ibm_db.exec_immediate(self._connection, cmd)
        if output:
            self.log.info(
                "Created table successfully with table name %s ",
                table_name)
        else:
            self.log.info("table is not created successfully")
            return False

        cmd = "insert into {0} values('commvault', 1)".format(table_name)
        for _ in range(1, 10):
            output = ibm_db.exec_immediate(self._connection, cmd)

        self.log.info("Inserted rows into table successfully")
        return True

    def get_active_logfile(self):
        """
        Fetches active logfile number by connecting to db2 database

        Raises:
            Exception:
                If unable to retrieve active log file number from db2 database

        """
        try:
            cmd = (
                "select MEMBER, CURRENT_ACTIVE_LOG from "
                "table(mon_get_transaction_log(-1)) as t order by member asc")
            self.log.info(cmd)
            stmt = ibm_db.exec_immediate(self._connection, cmd)
            output = ibm_db.fetch_tuple(stmt)
            self.log.info(output)
            return output
        except Exception as excp:
            raise Exception(
                "exception in get_active_logfile: {0}".format(excp))

    def add_data_to_database(self, tablespace_name, table_name, database_name):
        """Adds tablespace , table to given database such that backup and restore can be validated"""
        try:
            datafile = self.get_datafile_location()
            self.log.info(
                f"creating the tablespace {tablespace_name} inside database {database_name}")
            self.log.info(
                f"creating the table {table_name + '_FULL'} inside tablespace {tablespace_name}")
            self.create_table2(datafile, tablespace_name, table_name + '_FULL', True)
            self.log.info("Getting require parameters to validate backup and restore")
            (tblcount_full, tablespace_list, tablespace_count) = self.prepare_data(
                table_name + '_FULL')
            self.log.info(f"Rows count in the created table are {tblcount_full}")
            self.log.info(f"Tablespace list in the given database is {tablespace_list}")
            self.log.info(f"Tablespace count in the given database is {tablespace_count}")
            return tblcount_full, tablespace_list
        except Exception as _:
            raise Exception(f"Failed to add data into the database {database_name}")

    def remove_existing_logs_dir(self, instance_name, dest_db):
        """
        Removes existing logs staging directory for destination database
        """

        path_sep = "\\" if "windows" in self.client.os_info.lower() else "/"

        archive_path = self.machine_object.get_registry_value(commvault_key="Db2Agent",
                                                              value="sDB2_ARCHIVE_PATH").strip()
        audit_error_path = self.machine_object.get_registry_value(commvault_key="Db2Agent",
                                                                  value="sDB2_AUDIT_ERROR_PATH").strip()
        retrieve_path = self.machine_object.get_registry_value(commvault_key="Db2Agent",
                                                               value="sDB2_RETRIEVE_PATH").strip()
        retrieve_path = f"{retrieve_path}{path_sep}retrievePath"

        self.log.info("Archive Path: %s", archive_path)
        self.log.info("Audit Path: %s", audit_error_path)
        self.log.info("Retrieve Path: %s", retrieve_path)

        self.delete_database_directory(path=f"{archive_path}{path_sep}{instance_name}{path_sep}",
                                       database_name=dest_db)
        self.delete_database_directory(path=f"{retrieve_path}{path_sep}{instance_name}{path_sep}",
                                       database_name=dest_db)

        if "windows" in self.client.os_info.lower():
            cmd = "Get-ChildItem -Path %s -Include * -Recurse | foreach { $_.Delete()}" % audit_error_path
        else:
            if len(audit_error_path):
                cmd = f"rm -rf {audit_error_path}/*"
        self.log.info("Removing audit error files: %s", cmd)
        self.machine_object.execute_command(command=cmd)

    def delete_database_directory(self, path, database_name):
        """
        Deletes existing database directory
        Args:
            path (str)  -- Base path of database
            database_name (str) -- Database name to delete path for
        """
        self.log.info("Deleting file %s", f"{path}{database_name}")
        try:
            self.machine_object.remove_directory(directory_name=f"{path}{database_name}")
        except Exception as _:
            pass

    def drop_database_on_client(self, database_name):
        """
        Drops database on client
        Args:
            database_name (str) -- Name of database to drop
        """
        db2_base = ""
        if "windows" in self.machine_object.os_info.lower():
            db2_base = " set-item -path env:DB2CLP -value **$$** ; "

        database_cmd = f"{db2_base} db2 force application all"
        self.log.info("Disconnecting database %s from all connections using command: %s", database_name, database_cmd)
        output = self.machine_object.execute_command(command=database_cmd)
        self.log.info(output.output)

        database_cmd = f"{db2_base} db2 deactivate db {database_name}"
        self.log.info("Deactivating database %s on client using command: %s", database_name, database_cmd)
        output = self.machine_object.execute_command(command=database_cmd)
        self.log.info(output.output)

        if "SQL1031N" in output.output:
            database_cmd = f"{db2_base} db2 uncatalog database {database_name}"
            self.log.info("Uncataloging database %s on client using command: %s", database_name, database_cmd)
            output = self.machine_object.execute_command(command=database_cmd)
            self.log.info(output.output)

        database_cmd = f"{db2_base} db2 drop db {database_name}"
        self.log.info("Dropping database %s on client using command: %s", database_name, database_cmd)
        output = self.machine_object.execute_command(command=database_cmd)
        self.log.info(output.output)

    def get_redirect_path(self, database_name):
        """
        Get Redirect Path
        """
        db2_base = ""
        index = 9
        if "windows" in self.machine_object.os_info.lower():
            db2_base = " set-item -path env:DB2CLP -value **$$** ; "
            index = 1

        get_redirect_path = f"{db2_base} db2 connect to {database_name}; db2 \"SELECT DBPARTITIONNUM," \
                            f" TYPE, PATH FROM TABLE(ADMIN_LIST_DB_PATHS()) AS FILES where type='DB_STORAGE_PATH'\""
        output = self.machine_db2object.execute_command(command=get_redirect_path).formatted_output
        self.log.info("Redirect path for the instance:%s", output[index][2])
        return output[index][2]

    def backup_validation(self, operation_type,
                          tablespaces_count, backup_time_stamp):
        """
        Validates if backup job is successful

        Args:

            operation_type      (str)   -- type backup job like full/incremental/delta

            tablespaces_count   (int)   -- tablespace count

            backup_time_stamp   (str)   -- backup image timestamp

        Raises:

            Exception:
                If job type ran is not correct.
                If there is a mismatch in number of tablespaces backedup.
                If tablespace backup is not successfull.

        """
        try:
            cmd = (
                "select operationtype, TBSPNAMES from sysibmadm.db_history "
                "where start_time =  '{0}' and "
                "operationtype in('F','N','I','O','D','E')".format(backup_time_stamp))
            self.log.info(cmd)
            stmt = ibm_db.exec_immediate(self._connection, cmd)
            output = ibm_db.fetch_tuple(stmt)
            self.log.info(output)
            tble_line = output[1]
            self.log.info("table spaces backed up: '%s'", tble_line)
            self.log.info(
                "total table spaces: '%s'", tablespaces_count)
            if str(output[0]) == operation_type:
                self.log.info(
                    "Correct backup type job ran  F - Offline   N - Online   I - "
                    "Incremental offline  O - Incremental online D - Delta offline "
                    "E - Delta online  Actual job type :%s , Ran job type: %s",
                    operation_type,
                    output[0])

            else:
                raise Exception("Correct backup type job is not ran. Actual job type:{0} Ran "
                                "Job Type: {1}".format(operation_type, output[0]))
            for db_tablespace in tablespaces_count:
                if str(tble_line).find(db_tablespace) >= 0:
                    self.log.info(
                        "Table space backed up successfully : '%s'", db_tablespace)
                else:
                    raise Exception(
                        "Table space was not able to back up successfully : '{0}'".format(
                            db_tablespace))
                self.log.info(
                    " All Table space backed up successfully : '%s'", db_tablespace)

        except Exception as excp:
            raise Exception("exception in backup_validation: {0}".format(excp))

    def restore_validation(
            self,
            table_space,
            table_name,
            tablecount_full=None,
            tablecount_incr=None,
            tablecount_delta=None,
            storage_grps=None):
        """
        After restore it will check whether table space is accessible
        and checks the restore table data with original table data

        Args:

            table_space         (str)   --  name of the tablespace
            table_name          (str)   --  table name

            tablecount_full     (int)   --  number of rows in table during full backup
                default:    None

            tablecount_incr     (int)   --  number of rows in table during incremental backup
                default:    None

            tablecount_delta    (int)   --  number of rows in table during delta backup
                default:    None

            storage_grps         (list)   --  list of names of the storage groups
                default:    None

        Raises:

            Exception:
                if any table or tablespace is not restored successfully

        """
        try:
            cmd = "SELECT SERVICE_LEVEL FROM TABLE(SYSPROC.ENV_GET_INST_INFO())"
            self.log.info(cmd)
            stmt = ibm_db.exec_immediate(self._connection, cmd)
            output = ibm_db.fetch_assoc(stmt)
            self.log.info(output)

            self.log.info("DB2 version: %s", output['SERVICE_LEVEL'])
            if str(output['SERVICE_LEVEL']).find("v9.") >= 0:
                cmd = ("select ACCESSIBLE from  table(sysproc.snapshot_container('{0}',0)) tbl "
                       "where TABLESPACE_NAME = '{1}'".format(self._database, table_space))
                self.log.info(cmd)
            else:
                cmd = ("select ACCESSIBLE from  table(sysproc.SNAP_GET_CONTAINER_V91('{0}',0)) tbl"
                       " where TBSP_NAME = '{1}'".format(self._database, table_space))

                self.log.info(cmd)

            stmt = ibm_db.exec_immediate(self._connection, cmd)
            output = ibm_db.fetch_assoc(stmt)
            self.log.info(output)

            self.log.info("Accessible value %s", output['ACCESSIBLE'])
            if output['ACCESSIBLE'] == 0:
                self.log.info("Data is not restored")

            output = self.db2.get_table_content("{0}_FULL".format(table_name))
            self.log.info(f"Output of {table_name}_FULL is {output}")

            if output != tablecount_full:
                output = self.db2.get_table_content(
                    "{0}_PARTIAL".format(table_name))
                self.log.info(output)
                if output != tablecount_full:
                    self.log.info(
                        "table %s_FULL or %s_PARTIAL is not restored correctly",
                        table_name, table_name)

            if tablecount_incr is not None:
                output = self.db2.get_table_content(
                    "{0}_INCR".format(table_name))
                self.log.info(output)
                if output != tablecount_incr:
                    self.log.info(
                        "table : %s_INCR is not restored correctly", table_name)

            if tablecount_delta is not None:
                output = self.db2.get_table_content(
                    "{0}_DELTA".format(table_name))
                self.log.info(output)
                if output != tablecount_delta:
                    self.log.info(
                        "table %s_DELTA is not restored correctly", table_name)

                self.log.info(
                    "All tables are restored correctly from "
                    "all backup images(full, incremental, delta)")

            if storage_grps:
                for storage_grp in storage_grps:
                    cmd = f"select SGNAME from syscat.stogroups where SGNAME = '{storage_grp}'"
                    stmt = ibm_db.exec_immediate(self._connection, cmd)
                    stogrp = ibm_db.fetch_assoc(stmt)
                    if stogrp:
                        stogrp = str(stogrp.items())
                        self.log.info("Storage Group exists : %s", stogrp)
                    else:
                        self.log.info("Storage Group %s is not restored correctly", stogrp)

        except Exception as excp:
            self.log.exception(
                "Exception while Running restore_validation function %s", excp)

    def container_path_validation(self, tbsp_name, path):
        cmd = ('db2 "SELECT varchar(container_name,70) as container_name, varchar(tbsp_name,'
               '20) as tbsp_name, pool_read_time FROM TABLE(MON_GET_CONTAINER(\'\',-2)) where TBSP_NAME = \'{0}\'  '
               'ORDER BY pool_read_time DESC"').format(tbsp_name)
        self.machine_db2object.execute_command(f"db2 connect to {self._database}")
        cmd_output = self.machine_db2object.execute_command(cmd)
        container_path = cmd_output.formatted_output[2][0]
        self.log.info(f"Expected Path: {path}")
        self.log.info(f"Actual Path: {container_path}")
        if container_path == path:
            return True
        raise Exception("Container path validation failed")

    def restore_table_validation(
            self,
            tables_info):
        """
        After restore it will check whether table is restored
        and checks the restore table data with original table data

        Args:

            tables_info         (dict)   --  dictionary of tables and data
                Example: {"TableTest": (Value1, Value2, Value3)}

        Raises:

            Exception:
                if any table is not restored successfully

        """
        try:
            for table_name, content in tables_info.items():
                output = self.db2.get_table_content("{0}".format(table_name))
                self.log.info("[Expected Data]: %s", content)
                self.log.info("[Actual Data]: %s", output)
                if output != content:
                    self.log.info("Table %s is not restored correctly", table_name)

        except Exception as excp:
            self.log.exception(
                "Exception while Running restore_validation function %s", excp)

    def log_backup_validation(self, jobid):
        """
        Validates db2 log backup by connecting to commserve database

        Args:

            jobid(str)  -- jobid of db2 log backup

        Returns:

            bool -- returns boolean based on the fileType output

        Raises:
            Exception:
                If unable to retrieve fileType value from csdb

        """
        try:
            self.log.info(
                "Get fileType from archFile table for a given backup job : %s", jobid)
            query = (
                "select fileType from archFile where archFile.jobId = {0} "
                "and commCellId = '2'".format(jobid))
            self.log.info(query)
            self._csdb.execute(query)
            file_type = self._csdb.fetch_all_rows()
            self.log.info("fileType for log backup is %s", file_type)
            if str(file_type).find("4"):
                return True
            else:
                raise Exception("log backup validation failed")
        except Exception as excp:
            raise Exception(
                "Exception raised in get_backup_time_stamp_and_streams()"
                "\nError: '{0}'".format(excp))

    def get_backup_time_stamp_and_streams(self, jobid):
        """
        Gets Backup Time Stamp for a given backup job

        Args:

            jobid (str) -- jobid of db2 backup

        Returns:

              str - backup image timestamp and number of streams used for that backup

        Raises:
              Exception:
                if unable to get values from archfile table of csdb

        """
        try:
            self.log.info(
                "Get Backup Time Stamp for a given backup job : %s", jobid)
            query = (
                "select archFile.name from archFile where archFile.jobId = {0} "
                "and commCellId = '2'".format(jobid))
            self.log.info(query)
            self._csdb.execute(query)
            backup_time_stamp = self._csdb.fetch_all_rows()
            self.log.info("backuptimestamp %s", backup_time_stamp)
            backup_time_stamp0 = str(backup_time_stamp[0][0]).rsplit("_", 2)
            i = 1
            flag = 0
            for i in range(1, len(backup_time_stamp)):
                if str(backup_time_stamp[i][0]).find(
                        backup_time_stamp0[1]) < 0:
                    flag = 1
                    break

            if int(flag) != 1 and i == (len(backup_time_stamp) - 1):
                backup_time_stamp = str(backup_time_stamp[i][0]).rsplit("_", 2)
            else:
                backup_time_stamp = str(
                    backup_time_stamp[i - 1][0]).rsplit("_", 2)
            self.log.info(
                "backuptimestamp: %s , streams: %s",
                backup_time_stamp[1],
                backup_time_stamp[2])

            return (backup_time_stamp[1], backup_time_stamp[2])
        except Exception as excp:
            raise Exception(
                "Exception raised in get_backup_time_stamp_and_streams()"
                "\nError: '{0}'".format(excp))

    def get_database_state(self):
        """
        Checks whether database is in active state

        Raises:
            Exception:
                if unable to get database state

        """

        try:
            cmd = "CALL SYSPROC.ADMIN_CMD('connect to {0}')".format(
                self._database)
            self.log.info(cmd)
            stmt = ibm_db.exec_immediate(self._connection, cmd)
            output = ibm_db.fetch_assoc(stmt)
            self.log.info(output)
            if str(output).find("Database Connection Information") >= 0:
                self.log.info(
                    "Database: %s is in active state. ",
                    self._database)
            if str(output).upper().find("BACKUP PENDING") >= 0:
                cmd = "{0} backup database {1}".format(
                    self.db2, self._database)
                output = ibm_db.exec_immediate(self._connection, cmd)
                if str(output).find("Backup successful") >= 0:
                    self.log.info(
                        "first time backup after database creation is successful :%s", output)
                else:
                    self.log.info(
                        "first time backup after database creation is not successful :%s", output)
            else:
                self.log.info(
                    "Database is not active state. Please check database :%s",
                    self._database)
        except Exception as excp:
            self.log.exception(
                "Exception raised at get_database_state '%s'", excp)

    def disconnect_applications(self, database=None):
        """
        It will disconnect all applications of DB2 so that offline restore will work

        Args:

            database (str)  -- database name
        Returns:
                    (bool)  --  Returns true if command executes successfully
        Raises:
            Exception:
                If deactivate database command fails

        """
        if not database:
            database = self._database
        cmd = "{0} force applications all".format(self.db2cmd)
        self.log.info(cmd)
        cmd_output = self.machine_db2object.execute_command(cmd)
        output = cmd_output.formatted_output
        self.log.info("output: %s", output)

        cmd1 = "{0} deactivate database {1}".format(self.db2cmd, database)
        self.log.info(cmd1)
        cmd1_output = self.machine_db2object.execute_command(cmd1)
        output = cmd1_output.formatted_output
        self.log.info("%s", output)

        cmd2 = "{0} terminate".format(self.db2cmd)
        self.log.info(cmd2)
        cmd2_output = self.machine_db2object.execute_command(cmd2)
        output = cmd2_output.formatted_output
        self.log.info("%s", output)

    def exec_immediate_method(self, cmd):
        """
        Execute the given command using exec_immediate in ibm_db

        Args:

            cmd (str) -- db2 command that need to be executed

        """

        stmt = ibm_db.exec_immediate(self._connection, cmd)

        self.log.info(stmt)
        output = ibm_db.stmt_error(stmt)
        self.log.info(output)

    def update_db2_database_configuration1(self, cold_backup_path=None):
        """
        updates DB2 db configurations LOGARCHMETH1, LOGARCHOPT1, VENDOROPT, TRACKMOD parameters

        Args:
            cold_backup_path (str) -- Cold Backup Path

        Returns:
            (bool)  --  returns true or false based on success or failure of update cfg command

        Raises:
            Exception:
                If  db update cfg command fails.

        """
        self.log.info(self)
        try:
            client_name = self.client.client_name
            base_path = self.simpana_base_path

            if self.platform.lower() == "windows":

                cmd = ("CALL SYSPROC.ADMIN_CMD( 'update db cfg for  {0} using LOGARCHMETH1 "
                       "''VENDOR:{1}\DB2Sbt.dll''')".format(self._database, base_path))
                self.log.info("Set LOGRETAIN ON :%s", cmd)
                self.exec_immediate_method(cmd)

            else:

                cmd = (
                    "CALL SYSPROC.ADMIN_CMD( 'update db cfg for {0} using LOGARCHMETH1 "
                    "''VENDOR:{1}/libDb2Sbt.so''')".format(
                        self._database, self.simpana_base_path))
                self.log.info("Set LOGARCHMETH1 to CV %s", cmd)
                self.exec_immediate_method(cmd)

            cmd = (
                "CALL SYSPROC.ADMIN_CMD('update db cfg for {0} using LOGARCHOPT1 ''"
                "CvClientName={1},CvInstanceName={2}''')".format(
                    self._database,
                    client_name,
                    self.simpana_instance))
            self.log.info("Set LOGARCHOPT1 options %s", cmd)
            self.exec_immediate_method(cmd)

            cmd = (
                "CALL SYSPROC.ADMIN_CMD('update db cfg for {0} using VENDOROPT ''CvClientName={1},"
                "CvInstanceName={2}''')".format(
                    self._database,
                    client_name,
                    self.simpana_instance))
            self.log.info("Set VENDOROPT options %s", cmd)
            self.exec_immediate_method(cmd)

            cmd = "CALL SYSPROC.ADMIN_CMD( 'update db cfg for {0} using LOGARCHMETH2 OFF')".format(
                self._database)
            self.log.info("Set LOGARCHMETH2 OFF :%s", cmd)
            self.exec_immediate_method(cmd)

            cmd = "CALL SYSPROC.ADMIN_CMD( 'update db cfg for {0} using TRACKMOD ON')".format(
                self._database)
            self.log.info("Set TRACKMOD ON %s", cmd)
            self.exec_immediate_method(cmd)

            cmd = "{0} connect reset".format(self.db2cmd)
            self.log.info(cmd)
            cmd_output = self.machine_object.execute_command(cmd)
            output = cmd_output.formatted_output
            self.log.info("output: %s", output)

            retcode = self.disconnect_applications(self._database)

            if cold_backup_path:
                self.db2_cold_backup(cold_backup_path=cold_backup_path,
                                     db_name=self._database)
            self.reconnect()
            if retcode != 0:
                return False

            return True

        except Exception as excp:
            raise Exception(
                "Exception raised at update_db2_database_configuration:  '{0}'".format(excp))

    def get_db2_version(self):
        """
        Returns the DB2 application version level

        Raises:
            Exception:
                if unable to get db2 version

        """
        try:
            cmd = "SELECT SERVICE_LEVEL FROM TABLE(SYSPROC.ENV_GET_INST_INFO())"
            self.log.info(cmd)
            stmt = ibm_db.exec_immediate(self._connection, cmd)
            output = ibm_db.fetch_assoc(stmt)

            self.log.info("DB2 version: %s", (output['SERVICE_LEVEL']))
            return output['SERVICE_LEVEL']
        except Exception as excp:
            raise Exception(
                "Exception raised at get_db2_version :  '{0}'".format(excp))

    def close_db2_connection(self):
        """
        Closes db2 ibm_db connection

        Raises:
            Exception:
                if unable to close db2 connection

        """
        try:
            self.log.info("closing db2 ibm_db connection")
            ibm_db.close(self._connection)
        except Exception as excp:
            raise Exception(
                "Exception raised at close_db2_connection :  '{0}'".format(excp))

    def get_db2_information(self):
        """
        gets information about db2home, db2 databases, simpana instance name, simpana base path

        Raises:
            Exception:
                if unable to get db2 information

        """

        try:
            self.log.info("Instance name is : %s", self.simpana_instance)

            self.log.info("Simpana Base Path : %s", self.simpana_base_path)
            db2_home_path = self._db2_home_path
            self.log.info("DB2 Home Path : %s", db2_home_path)
            if self.platform.lower() != "windows":
                self.db2_profile = "{0}/sqllib/db2profile".format(
                    db2_home_path)
                self.db2cmd = "{0};db2".format(self.db2_profile)

            db2_database_list = self.list_database_directory()
            self.log.info("DB2 Database List is : %s", db2_database_list)

            return db2_home_path, db2_database_list, self.simpana_instance, self.simpana_base_path
        except Exception as excp:
            raise Exception(
                "Exception raised at get_db2_information:  '{0}'".format(excp))

    def list_database_directory(self):
        """
        method to list all database directories

        Returns: (list) - list of database aliases

        """
        cmd = f"{self.db2cmd} list database directory"
        self.log.info(cmd)
        cmd_output = self.machine_db2object.execute_command(cmd)
        output = cmd_output.formatted_output
        self.log.info("%s", output)
        return output

    def get_database_aliases_helper(self, alias_helper):
        """
        Helper method that retrieves a list of the database aliases from the database directory
        Args:
            alias_helper    (str)   -- database name need to ba passed

        Returns:

            (list) - List of databases

        """
        database_list = []
        list_db = alias_helper.split()
        count = 0

        while True:
            if len(list_db) > count:
                if list_db[count].lower() == 'alias':
                    alias = list_db[count + 2]
                    database_list.append(alias)
                    count = count + 1
                else:
                    count = count + 1
            else:
                break
        self.log.info(database_list)

        return database_list

    def third_party_command_backup(self, db_name, backup_type):
        """
        Uses command line to submit backup job on database.

        Args:

            db_name        (str)   -- database name

            backup_type    (str)   -- backup job type like FULL, INCREMENTAL , DELTA

        Returns:

            str - backup image timestamp

        Raises:
            Exception:
                if incorrect backup type is given or if any issue in running the backup job

        """
        try:
            self.log.info(self.load_path)

            if backup_type.upper() == "FULL":
                cmd = "{0} backup db {1} online load \"'{2}'\"".format(
                    self.db2cmd, db_name, self.load_path)
            elif backup_type.upper() == "DELTA":
                cmd = "{0} backup db {1} online incremental delta load \"'{2}'\"".format(
                    self.db2cmd, db_name, self.load_path)
            elif backup_type.upper() == "INCREMENTAL":
                cmd = "{0} backup db {1} online incremental load \"'{2}'\"".format(
                    self.db2cmd, db_name, self.load_path)
            else:
                raise Exception("Incorrect backup type entered")

            output = self.third_party_command(cmd)

            output = output.replace(" ", "")
            output = output.replace("\n", "")
            output = output.split(":")
            backup_time_stamp1 = output[1]

            return backup_time_stamp1.strip()
        except Exception as excp:
            raise Exception(
                "Exception raised at third_party_command_backup: '{0}'".format(excp))

    def third_party_command_restore(
            self, db_name, backup_time, version, restore_cycle=False):
        """
        Uses command line to submit restore job on database

        Args:

            db_name         (str)       -- database name

            backup_time     (str)       -- backup image timestamp

            version         (Str)       -- db2 application version

            restore_cycle   (bool)      -- whether to restore entire cycle of backup images or not
                    default: False

        Raises:

            Exception:
                if any issue occurs in triggering the cli restore

        """
        try:
            is_greater = self.compare_db2_versions(version)
            if is_greater:
                self.log.info(self.load_path)
                if restore_cycle:
                    cmd = (
                        "{0} restore db {1} incremental automatic load \"'{2}'\" open 2 sessions "
                        "taken at {3} without prompting".format(
                            self.db2cmd,
                            db_name,
                            self.load_path,
                            backup_time))
                else:
                    cmd = (
                        "{0} restore db {1} load \"'{2}'\" open 2 sessions taken at {3} without "
                        "prompting".format(
                            self.db2cmd,
                            db_name,
                            self.load_path,
                            backup_time))
                output = self.third_party_command(cmd)
            else:
                if restore_cycle:
                    cmd = (
                        "{0} restore db {1} incremental automatic load \"'{2}'\" taken at {3} "
                        "without prompting".format(
                            self.db2cmd,
                            db_name,
                            self.load_path,
                            backup_time))
                else:
                    cmd = ("{0} restore db {1} load \"'{2}'\" taken at {3} without "
                           "prompting".format(self.db2cmd, db_name, self.load_path, backup_time))
                output = self.third_party_command(cmd)

            if str(output).find("'Restore', 'is', 'successful") or str(
                    output).find("Restore is successful") >= 0:
                self.log.info("CLI restore is successful :%s", output)
            else:
                raise Exception(
                    "CLI restore is not successful :{0}".format(output))

            self.third_party_command_rollforward(db_name)
        except Exception as excp:
            raise Exception(
                "Exception raised at third_party_command_restore: '{0}'".format(excp))

    def third_party_command_rollforward(self, db_name):
        """
        Uses command line to Rollforward database

        Args:
            db_name (str) -- database name

        Raises:
            Exception:
                if commandline rollforward fails

        """
        try:
            cmd = "{0} rollforward db {1} to end of logs and complete".format(
                self.db2cmd, db_name)
            output = self.third_party_command(cmd)
            if str(output).find("'not', 'pending'") or str(
                    output).find("not pending") >= 0:
                self.log.info("Rollforward was successfull: %s", output)
            else:
                raise Exception(
                    "Rollforward is not successfull: {0}".format(output))
        except Exception as excp:
            raise Exception(
                "Exception raised at third_party_command_rollover: '{0}'".format(excp))

    def third_party_command_recover(self, db_name):
        """
        Uses command line to recover database.

        Args:
            db_name (str) -- database name

        Raises:
            Exception:
                If command line recover fails

        """
        try:
            self.log.info(self.load_path)
            cmd = "{0} recover database {1}".format(self.db2cmd, db_name)
            output = self.third_party_command(cmd)
            self.log.info("%s", output)
            if str(output).find("DB20000I") >= 0:
                self.log.info("Recover was successful: %s", output)
            else:
                raise Exception(
                    "Recover is not successful: {0}".format(output))

        except Exception as excp:
            raise Exception(
                "Exception raised at third_party_command_recover: '{0}'".format(excp))

    def db2_archive_log(self, db_name, archive_number_of_times):
        """
        Uses command line to archive db2 logs.

        Args:
            db_name (str) -- database name
            archive_number_of_times (int)   -- log archival count

        Raises:
            Exception:
                If command line archive log fails

        """
        try:
            count = 1
            while count <= archive_number_of_times:
                archive_cmd = "{0} archive log for db {1}".format(
                    self.db2cmd, db_name)
                self.third_party_command(archive_cmd)
                count += 1

        except Exception as excp:
            raise Exception(
                "Exception raised at third_party_command_recover: '{0}'".format(excp))

    def third_party_command(self, cmd):
        """
        Module to execute third party commands

        Args:
            cmd (str) -- db2 application command

        Returns:
            str -- output of the command that is executed in db2 cli interface

        Raises:
            Exception:
              if third party command fails to execute

        """
        try:
            self.log.info(cmd)
            if self.platform == 'WINDOWS':
                cmd_output = self.machine_object.execute_command(cmd)
            else:
                cmd_output = self.machine_db2object.execute_command(cmd)
            self.log.info(cmd_output)
            output = cmd_output.output
            self.log.info(output)
            return output
        except Exception as excp:
            raise Exception(
                "Exception raised at third_party_command: '{0}'".format(excp))

    def db2_cold_backup(self, cold_backup_path, db_name):
        """
        Takes DB2 cold backup

        Args:
            cold_backup_path (str) -- path on disk to backup db2 database

            db_name (str) -- database name

        Returns:
            str     -- cold backup image timestamp
            bool    -- true if cold backup is already taken

        Raises:
            Exception:
                if any issue occurs with cold backup

        """
        try:

            self.log.info("Check if backup is already exists")

            if self.platform.upper() != 'WINDOWS':
                cmd = "touch {0} timestamp.txt".format(cold_backup_path)
                self.log.info(cmd)
                cmd_output = self.machine_object.execute_command(cmd)
                self.log.info(cmd_output)
                output = cmd_output.formatted_output
                self.log.info(output)

                if str(output).find("Backup successful") >= 0:
                    self.log.info("Cold backup is already taken")
                    return True

            self.disconnect_applications(self._database)
            cmd = "{0} \"backup database {2} to '{1}'\" ".format(
                self.db2cmd, cold_backup_path, db_name)
            self.log.info(cmd)
            cmd_output = self.machine_object.execute_command(cmd)
            self.log.info(cmd_output)
            output = cmd_output.formatted_output
            self.log.info(output)
            output = self.third_party_command(cmd)

            if str(output).find("Backup successful") >= 0:
                self.log.info("Cold backup was successful")
            else:
                raise Exception("Cold backup was not successful. Please check")

            output = output.replace(" ", "")
            output = output.replace("\n", "")
            output = output.split(":")
            backup_time_stamp1 = output[1]

            return backup_time_stamp1
        except Exception as excp:
            raise Exception(
                "Exception raised at db2_cold_backup : '{0}'".format(excp))

    def restore_from_cold_backup(self, cold_backup_path, backup_time_stamp):
        """
        If database is down, restores from cold backup

        Args:
            cold_backup_path    (str)   -- disk path where cold backup image exists
            backup_time_stamp   (str)   -- backup image timestamp

        Raises:
            Exception :
                If any issue occurs while running restore from cold backup
                If restore command fails
        """
        self.log.info(
            "if any incremental restore is in progress abort that restore")
        cmd = "{0} restore db {1} incremental abort ".format(
            self.db2cmd, self._database)
        self.log.info(cmd)
        cmd_output = self.machine_object.execute_command(cmd)
        self.log.info(cmd_output)
        output = cmd_output.formatted_output
        self.log.info(output)
        self.log.info("Restoring from cold backup")
        cmd = ("{0} restore db {1} from '{2}' taken at  {3} without rolling forward without "
               "prompting ".format(self.db2cmd, self._database, cold_backup_path, backup_time_stamp))
        self.log.info(cmd)
        cmd_output = self.machine_object.execute_command(cmd)
        self.log.info(cmd_output)
        output = cmd_output.formatted_output
        self.log.info(output)

        if str(output).find("Restore is successful") >= 0:
            self.log.info("Restore from Cold backup is successful")
        else:
            raise Exception(
                "Restore from Cold backup is not successful. Please check")

    def compare_db2_versions(self, vers1):
        """
        Helper method that compares versions

        Args:
            vers1 (str) -- db2 application version for the given db2 instance

        Returns:

              (bool)    --  be returns if db2 version is less than 10.5.0.8

        """
        vers1 = vers1[5:]
        vers1 = vers1.split(".")
        vers1 = int(vers1[0] + vers1[1] + vers1[2] + vers1[3])
        vers2 = "10.5.0.8"
        vers2 = vers2.split(".")
        vers2 = int(vers2[0] + vers2[1] + vers2[2] + vers2[3])

        if vers2 <= vers1:
            self.log.info(
                "----------db2 version is greater than or equal to v10.5fp8------------")
            return True
        return False

    def create_database(self, db_name):
        """
        It will create database with given name and takes a base backup.

        Args:
            db_name (str) -- database name

        Raises:
            Exception:
                If issue occurs while creating database
                If disk backup after database creation fails
                If any other issue occurs in try block

        """
        try:
            cmd = (
                "{0} create database {1} automatic storage yes alias {1} using codeset "
                "utf-8 territory us collate using identity pagesize 4 K".format(
                    self.db2cmd, db_name))
            self.log.info(cmd)
            cmd_output = self.machine_object.execute_command(cmd)
            self.log.info(cmd_output)
            output = cmd_output.formatted_output
            self.log.info(output)

            self.log.info(output)
            if str(output).find("DB20000I") >= 0:
                self.log.info("Database Created %s", db_name)
                cmd = "{0} backup database {1}".format(self.db2cmd, db_name)
                cmd_output = self.machine_object.execute_command(cmd)
                self.log.info(cmd_output)
                output = cmd_output.formatted_output
                self.log.info(output)

                if str(output).find("Backup successful") >= 0:
                    self.log.info(
                        "first time backup after database creation is successful: %s",
                        output)

                else:
                    raise Exception(
                        "first time backup after database creation is not successful :{0}".format(
                            output))

            else:
                raise Exception("Database is not created {0}".format(db_name))

        except Exception as excp:
            raise Exception(
                "Exception raised at create_database  : '{0}'".format(excp))

    def get_database_port(self):
        """ Get Database Port """
        if not self.is_pseudo_client and "windows" in self.machine_object.os_info.lower():
            service_filepath = "C:\\Windows\\System32\\drivers\\etc\\services"
            get_svce_cmd = 'set-item -path env:DB2CLP -value **$$** ; set-item -path env:DB2INSTANCE -value "%s"; ' \
                           'db2 -o get dbm cfg|Select-String "\(SVCENAME\)"' % self.instance.name
            cmd_output = self.machine_object.execute_command(command=get_svce_cmd).output.strip()
        else:
            service_filepath = "/etc/services"
            get_svce_cmd = "db2 get dbm cfg | grep -i '(SVCENAME)'"
            cmd_output = self.machine_db2object.execute_command(command=get_svce_cmd).output.strip()

        self.log.info("SVCENAME CMD output: %s", cmd_output)
        instance_port_service_name = cmd_output.split("=")[-1].strip()
        self.log.info("SVCENAME: %s", instance_port_service_name)
        port = None
        if instance_port_service_name.isnumeric():
            port = instance_port_service_name
        else:
            instance_ports = self.machine_object.find_lines_in_file(file_path=service_filepath,
                                                                    words=[instance_port_service_name])
            for instances in instance_ports:
                if '\t' in instances:
                    instance_port = instances.split('\t')
                else:
                    instance_port = instances.split()
                if instance_port[0] == instance_port_service_name:
                    port = instance_port[1].split('/')[0]
                    break

        if not port:
            raise Exception("Port Number not found for instance: %s" % self.instance.name)
        self.log.info("Port Number for instance %s : %s" % (self.instance.name, port))
        return port

    def create_storage_group(self, storage_group_name, path, flag_recreate_storage_group):
        """
        Method to create Storage Group

        Args:
            storage_group_name (str)             -- name of the storage group

            path (str)                          -- Path to create storage group on

            flag_recreate_storage_group (bool)  -- flag to recreate storage group or not

        Returns:

            (bool)      -   method return false if drop tablespace fails
        """
        cmd = f"select SGNAME from syscat.stogroups where SGNAME = '{storage_group_name}'"
        stmt = ibm_db.exec_immediate(self._connection, cmd)
        stogrp = ibm_db.fetch_assoc(stmt)
        if stogrp:
            stogrp = str(stogrp.items())
            self.log.info("Storage Group exists : %s", stogrp)
            if flag_recreate_storage_group:
                if not self.drop_storage_group(stogroup_name=storage_group_name):
                    return False
            else:
                return False

        cmd = f"create stogroup {storage_group_name} on '{path}'"
        self.log.info("Creating storage policy %s on path: %s", storage_group_name, path)
        output = ibm_db.exec_immediate(self._connection, cmd)
        if output:
            self.log.info("Created Storage Group successfully")
        else:
            self.log.info("Storage Group is not created successfully :%s", output)
            return False
        return True

    def drop_storage_group(self, stogroup_name):
        """
        Drop storage group
        Args:
            stogroup_name (str)             -- name of the storage group

        Returns:
            (bool)      -   method return false if drop storage group fails
        """
        cmd = f"drop STOGROUP {stogroup_name}"
        output = ibm_db.exec_immediate(self._connection, cmd)
        if output:
            self.log.info("Storage Group dropped successfully")
            return True
        else:
            self.log.info("Storage Group not dropped successfully")
            return False

    def is_index_v2_db2(self):
        """Returns True if DB2 index version is V2.
            Returns:
                Returns true if indexing is V2 for DB2.
                Else returns False

            Raises:
                Exception:
                    if failed to get the DB2 indexing version

        """
        indexing = "IndexingV2_DB2_DPF" if self.is_pseudo_client else "IndexingV2_DB2"
        query = f"select attrVal from APP_ClientProp where [componentNameId] in " \
                f"(select id from APP_Client where name='{self.client.client_name}') and attrName like '{indexing}'"
        self._csdb.execute(query)
        cur = self._csdb.fetch_one_row()
        if cur:
            index_v2 = cur[0]
            return index_v2 == "1"
        else:
            raise Exception(
                "Failed to get the Postgres Index version")

    @property
    def instance_port(self):
        return self._port

    def run_db2_config_script(self, cold_backup_path=None):
        """
        updates DB2 MultiNode db configurations LOGARCHMETH1, LOGARCHOPT1, VENDOROPT, TRACKMOD parameters

        Args:
            cold_backup_path    (str)   --  Cold Backup Path
                default: None
        Returns:
            (bool)  --  returns true or false based on success or failure of update cfg command

        Raises:
            Exception:
                If  db update cfg command fails.

        """
        self.log.info(self)
        try:
            if "windows" in self.client.os_info.lower():
                path_sep = "\\"
                db2_config_name = "Base\\Db2_config.ps1"
                instance_set = "set-item -path env:DB2INSTANCE -value \"%s\" ;" % self.instance.name
            else:
                path_sep = "/"
                db2_config_name = "iDataAgent/Db2_config.sh"
                instance_set = ""

            if self.is_pseudo_client:
                install_directory = self.machine_object.get_registry_value('Base', 'dGALAXYHOME')
                db2_config_path = f"{install_directory}{path_sep}{db2_config_name}"
                script_run_command = f". {db2_config_path} -d {self._database} -i {self.simpana_instance}"
                script_run_command = f"{script_run_command} -c {self._pseudo_client_name}"
            else:
                db2_config_path = f"{self.client.install_directory}{path_sep}{db2_config_name}"
                script_run_command = f"{instance_set} . {db2_config_path} -d {self._database} -i {self.simpana_instance}"
            self.log.info("Running DB2_config Script Command: %s", script_run_command)

            output = self.machine_db2object.execute_command(command=script_run_command)
            self.log.info("Output: %s", output.output)

            retcode = self.disconnect_applications(self._database)

            if cold_backup_path:
                self.db2_cold_backup(cold_backup_path=cold_backup_path,
                                     db_name=self._database)
            self.reconnect()
            if retcode != 0:
                return False

            return True

        except Exception as excp:
            raise Exception(
                "Exception raised at update_db2_database_configuration:  '{0}'".format(excp))

    def get_database_encropts_csdb(self):
        """Returns DB2 Encryption Options from CSDB.
            Returns:
                Returns dictionary with 2 keys:
                    DB2 Encryption Library
                    DB2 Encryption Options

            Raises:
                Exception:
                    if failed to get the DB2 Encryption Properties

        """
        query = f"select attrVal from APP_BackupSetProp where [componentNameId]={self.backupset._backupset_id} and attrName='DB2 Encryption Library'"
        self._csdb.execute(query)
        cur1 = self._csdb.fetch_one_row()

        query = f"select attrVal from APP_BackupSetProp where [componentNameId]={self.backupset._backupset_id} and attrName='DB2 Encryption Options'"
        self._csdb.execute(query)
        cur2 = self._csdb.fetch_one_row()
        if cur1 and cur2:
            encrlib = cur1[0]
            encropts = cur2[0]
            return {
                "DB2 Encryption Library": encrlib,
                "DB2 Encryption Options": encropts
            }
        else:
            raise Exception(
                "Failed to get the DB2 Encryption Values")

    def get_database_encropts_client(self):
        """Returns DB2 Encryption Options from client.
            Returns:
                Returns dictionary with 2 keys:
                    DB2 Encryption Library
                    DB2 Encryption Options

            Raises:
                Exception:
                    if failed to get the DB2 Encryption Properties

        """
        query = f"db2 get db cfg for {self._database} | grep -i 'Encryption Library for Backup'"
        encrlib = self.machine_db2object.execute_command(command=query).output
        encrlib = encrlib[encrlib.index('=') + 1:].strip()

        query = f"db2 get db cfg for {self._database} | grep -i 'Encryption Options for Backup'"
        encropts = self.machine_db2object.execute_command(command=query).output
        encropts = encropts[encropts.index('=') + 1:].strip()
        if encropts and encrlib:
            return {
                "DB2 Encryption Library": encrlib,
                "DB2 Encryption Options": encropts
            }
        else:
            raise Exception("Failed to get the DB2 Encryption Options")

    def run_sweep_job_using_regkey(self, media_agent=None):
        """ Sets SweepStartTime regkey and waits for the sweep job to finish

            Args:
                media_agent(str)   -- Name of the media agent where logs are dumped
        """
        cli_subclient = self.instance.backupsets.get(self.backupset.backupset_name).subclients.get('(command line)')
        self.log.info(f"Command line subclient id is {cli_subclient.subclient_id}")
        after_two_mins = datetime.now() + timedelta(minutes=2)
        hours = int(after_two_mins.hour)
        mins = int(after_two_mins.minute)
        time_stamp = int(time.time())
        if media_agent:
            self.log.info("Setting SweepStartTime registry key on MA")
            media_agent_client_obj = self.commcell.clients.get(media_agent)
            media_agent_client_obj.add_additional_setting(
                f"Db2Agent/Sweep/{cli_subclient.subclient_id}",
                "SweepStartTime",
                "STRING",
                f"{hours}:{mins}")
        else:
            self.log.info("Setting SweepStartTime registry Key on CS")
            self.commcell.add_additional_setting(
                f"Db2Agent/Sweep/{cli_subclient.subclient_id}",
                "SweepStartTime",
                "STRING",
                f"{hours}:{mins}")
        try:
            self.log.info("Sleeping for 3 mins before checking sweep job")
            time.sleep(180)
            count = 15
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
                raise Exception("Sweep job did not trigger is 15 mins")
            self.log.info("Sweep job:%s", job_obj.job_id)
            return job_obj.job_id
        except Exception as exp:
            self.log.error("Unable to trigger sweep job")
            raise Exception(exp)
        finally:
            if media_agent:
                self.log.info("Deleting SweepStartTime registry Key from MA")
                media_agent_client_obj.delete_additional_setting(
                    f"Db2Agent/Sweep/{cli_subclient.subclient_id}",
                    "SweepStartTime")
            else:
                self.log.info("Deleting SweepStartTime registry Key from CS")
                self.commcell.delete_additional_setting(
                    f"Db2Agent/Sweep/{cli_subclient.subclient_id}",
                    "SweepStartTime")
            self.log.info(
                "SweepStartTime registry key is deleted Successfully")

    def csdb_object_to_execute(self):
        """ This function creates csdb object using mssql class with read and write access permissions

            Returns:
                CSDB Object with write and execute permissions

            Raises:
            Exception :
                If CSDB credentials are missing in config.json or
                when Invalid credentials are provided to connect to CSDB

        """
        csdb_username = get_config().SQL.Username
        csdb_password = get_config().SQL.Password
        server_name = f"{self.commcell.commserv_hostname}\commvault"
        self.log.info(f"csdb user name is {csdb_username}, csdb server is {server_name}")
        try:
            if server_name and csdb_password and csdb_username:
                csdb = MSSQL(server_name, csdb_username, csdb_password, "CommServ")
                return csdb
            else:
                raise Exception("Missing or incorrect credentials to connect to csdb")
        except Exception as exception:
            self.log.error("Unable to establish connection with csdb")
            raise Exception(exception)

    def verify_one_min_rpo(self, job_id):
        """ Method to verify if One min rpo is enabled on client or not based on backup job ran

            Args :
                job_id (int) -- Backup job id

            Returns :
                Boolean - True if given Backup job backed up only files

            Raises :
            Exception :
                If one min rpo is not enabled (Backup job backed up logs)

        """
        try:
            query = """select fileType from archFile where jobID = {0} and fileType != 1""".format(job_id)
            self.log.info(f"Running {query} in CSDB")
            self._csdb.execute(query)
            cur = self._csdb.fetch_all_rows()
            self.log.info("RESULT of query: {0}".format(cur))
            self.log.info(cur[0], len(cur[0]))
            if len(cur[0]) > 1:
                self.log.info(f"One min rpo is not working as CSDB returned the filetypes {cur}")
                raise Exception(
                    "Test case Failed as ONE MIN RPO is not working Backup job has invalid filetype")
            else:
                self.log.info("Successfully verified one min rpo and it is enabled")
                return True
        except Exception as exception:
            self.log.info("Failed to verify the status of one min rpo")
            raise Exception(exception)

    def get_chain_number(self):
        """ Method return the chain number of given DB

            Returns :
                Int -- Chain number

            Raises :
            Exception :
                If unable to fetch the chain number of given DB

         """
        try:
            self.reconnect()
            query = """db2 activate database {0}""".format(self.backupset.backupset_name)
            self.log.info(f"executing query {query}")
            output = self.third_party_command(query)
            self.log.info(f"Output of the {query} is {output}")
            query = """db2pd -log -db {0}""".format(self.backupset.backupset_name)
            self.log.info(f"executing query {query}")
            output = self.third_party_command(query)
            self.log.info(f"Output of the {query} is {output}")
            # Code to extract log chain id from output
            output = output.split("\n")
            i = 0
            for x in output:
                if "Log Chain ID" in x:
                    break
                i += 1
            chain_number = output[i].split()[-1]
            return chain_number
        except Exception as exception:
            self.log.info("Failed to get the chain directory number")
            raise Exception(exception)

    def get_mountpath(self):
        """ Method to get the dump location of logs of given database while creating db2helper

            Returns:
                Str -- Dump location of logs inside media agent

            Raises:
            Exception :
                If unable to fetch mount path from CSDB or unable to get chain id of database

        """
        try:
            chain_id = self.get_chain_number()
            csdb = self.csdb_object_to_execute()
            command_line_sub_client = self.backupset.subclients.get("(command line)")
            subclient_id = command_line_sub_client.subclient_id
            backupset_id = self.backupset.backupset_id
            query = """EXEC ArchGetSubclientMountpathList {0}, 3, 0, 0""".format(subclient_id)
            self.log.info(f"Executing the query '{query}' in csdb")
            output = csdb.execute(query)
            self.log.info(f"output of the query '{query}' is {output.rows}")
            # Extracting mountpath from output
            mount_path_csdb = output.rows[0][1].split("|")[1].strip()
            self.log.info(f"Mountpath from csdb is {mount_path_csdb}")
            query = """select GUID from APP_BackupSetName where id = {0}""".format(backupset_id)
            self.log.info(f"Executing the query '{query}' in csdb")
            self._csdb.execute(query)
            output = self._csdb.fetch_all_rows()
            self.log.info(f"output of the query '{query}' is {output}")
            backupset_guid = output[0][-1]
            self.log.info(f"Backupset guid is {backupset_guid}")
            chain_file = 'C' + '0' * (7 - len(chain_id)) + chain_id
            dump_location = mount_path_csdb + "/CV_APP_DUMPS/" + backupset_guid + "/DB2LOGS/NODE0000/" + chain_file
            self.log.info(f"Dump location of archived logs on ma is {dump_location}")
            return dump_location
        except Exception as exception:
            self.log.info("Failed to get the mount path for logs in ma")
            raise Exception(exception)

    def verify_logs_on_ma(self, active_log_number, ma_obj):
        """ Method to verify if given active log number is present inside the mount path location inside given media
            agent object

            Args :
                ma_obj (media agent object) -- Media agent machine object on which logs are dumped
                active_log_number (int) -- Active log number of db
            Returns :
                Boolean -- True if dumped logs are available inside media agent

            Raises:
            Exception:
                If unable to get active log number
                If mount path is not available on media agent
                If dumped logs are not present inside the media agent mount path location

         """
        try:
            self.reconnect()
            mount_path = self.get_mountpath()
            self.log.info(f"{active_log_number},{mount_path}")
            chain_file = mount_path.split("/")[-1]
            self.log.info(f"{chain_file}")
            log_file = 'S' + '0' * (7 - len(str(active_log_number))) + str(active_log_number) + '.LOG'
            self.log.info(f"{log_file}")
            file_name = self.instance.instance_name.upper() + '_' + self.backupset.backupset_name.upper() + '_NODE0000_' + chain_file + '_' + log_file
            self.log.info(f"Log file to be checked in MA is {file_name}")
            log_file_path = mount_path + "/" + file_name
            self.log.info(f"{log_file_path}")
            if ma_obj.check_directory_exists(mount_path):
                self.log.info("Mount path is available on MA")
                if not ma_obj.check_file_exists(log_file_path):
                    raise Exception("The Archived log files are not available on MA")
                else:
                    self.log.info("Archived logs are available in dump location on MA")
                    return True
            else:
                raise Exception("Given mount path is not available on MA")
        except Exception as exception:
            self.log.info("Failed to verify the existence of logs inside ma")
            raise Exception(exception)

    def create_sweep_schedule_policy(self, name="db2_sweep_schedule", association=None, sweep_time=8):
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
                                    "appName": "DB2"
                                }]

            sweep_time  (int)   --  Frequency of sweep job (within 1 to 24)
                default: 1

        """
        if self.commcell.schedule_policies.has_policy('db2_sweep_schedule'):
            self.log.info("Deleting the automation created sweep schedule policy")
            self.commcell.schedule_policies.delete('db2_sweep_schedule')
        pattern = [{'name': 'Dummy_name',
                    'pattern': {"freq_type": 'automatic',
                                "use_storage_space_ma": True,
                                "sweep_start_time": sweep_time * 3600
                                }}]
        types = [{"appGroupName": "DB2"}]
        if not association:
            association = [{
                "clientName": self.client.client_name,
                "instanceName": self.instance.instance_name,
                "appName": "DB2"
            }]
        self.commcell.schedule_policies.add(
            name=name, policy_type='Data Protection',
            associations=association, schedules=pattern, agent_type=types)

    def verify_one_min_rpo_backupset_level(self):
        """ Method to verify if One min rpo is enabled on client or not at backupset level

            Returns :
                Boolean - True if Dump Sweep Schedule property is set at Backupset level


        """
        query = """select attrVal from APP_BackupSetProp where componentNameId = {0} and 
                    attrName = 'Dump Sweep Schedule'""".format(self.backupset.backupset_id)
        self.log.info(f"Running {query} in CSDB")
        self._csdb.execute(query)
        cur = self._csdb.fetch_all_rows()
        self.log.info("RESULT of query: {0}".format(cur))
        self.log.info(cur[0], len(cur[0]))
        if cur[0][0] != '1':
            self.log.info(f"One min rpo is not working as CSDB returned {cur}")
            return False
        else:
            self.log.info("Successfully verified one min rpo and it is enabled")
            return True

    def db2_load_copy(self, datafile, tablespace_name, table_name, db_name, count, return_output=False):
        """
                Uses command line to generate db2 load copy.

                Args:
                    datafile(str)                   -- datafile location

                    tablespace_name(str)            -- name of the tablespace

                    table_name(str)                 -- name of the table

                    db_name (str)                   -- database name

                    count (int)                     -- db2 load copy count

                    return_output(bool)             -- True/False to return output of load copy commands

                        default : False

                Returns:
                    list  -- Output of load copy commands

                Raises:
                    Exception:
                        If command line load copy generation fails

                """
        try:
            boolean = self.drop_tablespace(tablespace_name)
            if not boolean:
                self.log.info("Tablespace given to generate load copy image already exists and unable to drop it")
                raise Exception("unable to drop the tablespace {0}".format(tablespace_name))
            output = []
            if self.platform.upper() == 'WINDOWS':
                set_schema_command = "SET SCHEMA=SYSTEM"
                ibm_db.exec_immediate(self._connection, set_schema_command)
            self.log.info(f"Creating the tablespace {tablespace_name} and table {table_name} inside db {db_name}")
            self.create_table2(datafile, tablespace_name, table_name, True)
            loop_count = 1
            base_path = self.simpana_base_path
            self.log.info(f"Commvault's base path is {base_path}")
            if self.platform.upper() == 'WINDOWS':
                path = base_path + "\Db2Sbt.dll"
                env_cmd = f"set-item -path env:DB2CLP -value **$$** ; set-item -path env:DB2INSTANCE -value \"{self.instance.name}\" ;"
            else:
                path = base_path + "/libDb2Sbt.so"
                env_cmd = ""
            self.log.info(f"Commvault's DB2 library path is {path}")
            if self.platform.upper() == 'WINDOWS':
                grant_admin = "GRANT DBADM ON DATABASE TO SYSTEM;"
                ibm_db.exec_immediate(self._connection, grant_admin)
            load_cmd = env_cmd + """
            db2 connect to {0};
            db2 "DECLARE EMPCURS12 CURSOR FOR SELECT * from {1}";
            db2 -v "drop table ttable1copy";
            db2 -v "create table ttable1copy like {1}";
            db2 -v "LOAD FROM EMPCURS12 of cursor replace into ttable1copy statistics use profile copy yes load '{2}'";
            """.format(db_name, table_name, path)
            self.log.info(f"This Command will be executed in client machine {load_cmd} for {count} times")
            while loop_count <= count:
                temp = self.third_party_command(load_cmd)
                output.append(temp)
                loop_count += 1
            self.log.info(f"Output of load copy commands executed is {output}")
            if return_output:
                return output

        except Exception as exception:
            raise Exception(
                "Exception raised at third_party_command: '{0}'".format(exception))

    def get_mountpath_load_copy(self):
        """ Method to get the dump location of load copy of given database

            Returns:
                Str -- Dump location of load copy images inside media agent

            Raises:
            Exception :
                If unable to fetch mount path from CSDB

        """
        try:
            csdb = self.csdb_object_to_execute()
            command_line_sub_client = self.backupset.subclients.get("(command line)")
            subclient_id = command_line_sub_client.subclient_id
            backupset_id = self.backupset.backupset_id
            query = """EXEC ArchGetSubclientMountpathList {0}, 3, 0, 0""".format(subclient_id)
            self.log.info(f"Executing the query '{query}' in csdb")
            output = csdb.execute(query)
            self.log.info(f"output of the query '{query}' is {output.rows}")
            # Extracting mountpath from output
            mount_path_csdb = output.rows[0][1].split("|")[1].strip()
            self.log.info(f"Mountpath from csdb is {mount_path_csdb}")
            query = """select GUID from APP_BackupSetName where id = {0}""".format(backupset_id)
            self.log.info(f"Executing the query '{query}' in csdb")
            self._csdb.execute(query)
            output = self._csdb.fetch_all_rows()
            self.log.info(f"output of the query '{query}' is {output}")
            backupset_guid = output[0][-1]
            self.log.info(f"Backupset guid is {backupset_guid}")
            dump_location = mount_path_csdb + "/CV_APP_DUMPS/" + backupset_guid + "/DB2LOAD/"
            self.log.info(f"Dump location of load copy on ma is {dump_location}")
            return dump_location
        except Exception as exception:
            self.log.info("Failed to get the mount path for load copy in ma")
            raise Exception(exception)

    def verify_load_copy_images_on_ma(self, ma_obj, output):
        """ Method to verify if load copy images are present inside the mount path location inside given media
                    agent object

                    Args :
                        ma_obj (media agent object) -- Media agent machine object on which load copy images are dumped
                        output (list) -- Output of load copy commands from db2_load_copy method
                    Returns :
                        Boolean -- True if dumped load copy images are available inside media agent

                    Raises:
                    Exception:
                        If unable to get load copy mount path inside MA
                        If mount path is not available on media agent
                        If load copy images are not present inside the media agent mount path location

                 """
        try:
            mountpath = self.get_mountpath_load_copy()
            todays_date = date.today().strftime("%Y%m%d")
            timestamps_from_output = []
            folder_names = []
            file_names = []

            for x in output:
                temp = x
                temp = temp.split("\n")
                temp_n = []
                for z in temp:
                    if len(z.strip()) > 0:
                        temp_n.append(z.strip())
                self.log.info("Extracting timestamps to get directory paths of load copy images inside MA")
                for i, y in enumerate(temp_n):
                    if 'The utility has finished the "LOAD" phase at time' in y:
                        temp1 = temp_n[i + 1].split(".")
                        temp1[1] = temp1[1][:-1]
                        secs = f"0.{temp1[1]}"
                        secs = float(secs)
                        temp2 = temp1[0].split(":")
                        temp2[2] = str(int(temp2[2]) + round(secs))
                        if len(temp2[2]) < 2:
                            temp2[2] = "0" * (2 - len(temp2[2])) + temp2[2]
                        timestamps_from_output.append(''.join(temp2).strip())
                        break

            self.log.info(f"Time stamps from output generated is {timestamps_from_output}")

            self.log.info("Generating load copy file names to check inside MA")
            for x in timestamps_from_output:
                folder_name = "NODE0000_" + todays_date + x + "_1"
                folder_names.append(folder_name)
                file_name = self.instance.instance_name.upper() + "_" + self.backupset.backupset_name.upper() + "_" + folder_name
                file_names.append(file_name)
                self.log.info(f"{file_name} is present in folder {folder_name}")

            self.log.info(f"File names of load copy images is {file_names}")
            self.log.info(f"Folder names of load copy images is {folder_names}")
            self.log.info("Checking for load copy images inside MA")
            count = 0
            for i, x in enumerate(folder_names):

                if (ma_obj.check_directory_exists(mountpath + '/' + x) and ma_obj.check_file_exists(
                        mountpath + '/' + x + '/' + file_names[i])):
                    count += 1
                    break

            if count == 0:
                raise Exception("Load copy images are not present inside the MA")

            self.log.info("load copy images generated are present inside MA")
            return True

        except Exception as exception:
            self.log.info("Failed to verify the existence of load copy images inside ma")
            raise Exception(exception)

    def gui_out_of_place_restore_same_instance(self, dest_db_name, restore_incremental=False, roll_forward=True):
        """ Method to Run DB2 GUI Out Of Place Restore to same instance different DB

        Args :

            dest_db_name (str) : Name of the destination database

            restore_incremental (bool) : True if restore should happen incrementally till end of all backup images on top of a base image

            roll_forward (bool) : False if restored db should be in roll forward pending state else True

        Returns :

            job (obj) -- Restore job object

        Raises :
            Exception :
                If failed to trigger restore job

        """
        redirect_storage_group = {'IBMSTOGROUP': self.instance.home_directory}
        job = self.backupset.restore_out_of_place(dest_client_name=self.client.client_name,
                                                  dest_instance_name=self.instance.instance_name,
                                                  dest_backupset_name=dest_db_name,
                                                  target_path=self.instance.home_directory,
                                                  redirect_enabled=True,
                                                  redirect_storage_group_path=redirect_storage_group,
                                                  roll_forward=roll_forward,
                                                  restore_incremental=restore_incremental)
        self.log.info("Started:FULL Out Of Place Restore JOB to same instance different DB with JOB ID: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run: {0} restore job with error: {1} delay_reason ".
                format(job.job_id, job.delay_reason))
        self.log.info("Successfully finished restore ")

        return job

    def gui_inplace_log_only_restore(self, roll_forward=False, archiveLogLSN=False, startLSN=False, endLSN=False,
                                     startLSNNum=1, endLSNNum=1, archiveLogTime=False, logTimeStart=False,
                                     logTimeEnd=False, fromTimeValue=None, toTimeValue=None):
        """ Method to Run DB2 GUI Out Of Place Restore to same instance different DB

        Args:

            roll_forward (bool) -- False if restored db should be in roll forward pending state else True

                default : False

            archiveLogLSN (bool) -- True if log range restore needs to be done else False

                default : False

            startLSN (bool) -- True when log range restore needs to be done and start log number needs to be specified

                default : False

            endLSN (bool)   -- True when log range restore needs to be done and end log number needs to be specified

                default : False

            startLSNNum (int) -- Starting log number when archiveLogLsn and startLsn are true

                default : 1

            endLSNNum (int) -- ending log number when archiveLogLsn and startLsn are true

                default : 1

            archiveLogTime (bool)   -- True if time based log restore needs to be done else False

                default : False

            logTimeStart (bool)    -- True if start time of log time restore needs to be given

                default : False

            logTimeEnd (bool)   -- True if end time of log time restore needs to be given

                default : False

            fromTimeValue (str)--Timestamp in the form of YY-MM-DD HH:MM:SS for start log time when logTimeStart is True

                default : None

            toTimeValue (str)--Timestamp in the form of YY-MM-DD HH:MM:SS for end log time when logTimeEnd is True

                default : None

        Returns :

            job (obj) -- Job object of log restore job triggered

        Raises :
            Exception :
                If unable to trigger the log only restore job with specified parameters


        """

        job = self.backupset.restore_entire_database(dest_client_name=self.client.client_name,
                                                     dest_instance_name=self.instance.instance_name,
                                                     dest_backupset_name=self.backupset.backupset_name,
                                                     target_path=self.instance.home_directory,
                                                     roll_forward=roll_forward,
                                                     startLSNNum=startLSNNum,
                                                     endLSNNum=endLSNNum,
                                                     archiveLogLSN=archiveLogLSN,
                                                     startLSN=startLSN,
                                                     endLSN=endLSN,
                                                     archiveLogTime=archiveLogTime,
                                                     logTimeStart=logTimeStart,
                                                     logTimeEnd=logTimeEnd,
                                                     fromTimeValue=fromTimeValue,
                                                     toTimeValue=toTimeValue,
                                                     redirect_enabled=False,
                                                     restore_incremental=False,
                                                     recover_db=False,
                                                     restore_data=False,
                                                     restore_logs=True)
        self.log.info("Started:Inplace LOG Only Restore JOB with JOB ID: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run: {0} restore job with error: {1} delay_reason ".
                format(job.job_id, job.delay_reason))
        self.log.info("Successfully finished restore ")

        return job

    def get_backupset_log_retrieve_path(self):
        """ Method to get the log file restore location of backupset configured with db2 helper inside client

        Returns :

                retrieve_location(str) : DB2 log retrieve path of given backupset

        Raises :
            Exception :

                If unable to get the log retrieve path of given backupset inside client

        """
        try:
            chain_id = self.get_chain_number()
            self.log.info(f"Current chain id of given backupset {chain_id}")
            chain_file = 'C' + '0' * (7 - len(chain_id)) + chain_id
            self.log.info(f"Current Restore chain file of given backup set is {chain_file}")
            db2_retrieve_path = self.machine_object.get_registry_value("Db2Agent", "sDB2_RETRIEVE_PATH")
            self.log.info(f"DB2 Log retrieve location of given client is {db2_retrieve_path}")
            retrieve_location = self.machine_object.join_path(db2_retrieve_path, "retrievePath", self.instance.instance_name, self.backupset.backupset_name.upper(), "NODE0000", chain_file)
            self.log.info(f"Log Retrieve location of given backupset inside client is {retrieve_location}")
            return retrieve_location
        except Exception as exception:
            self.log.info("Failed to get the log retrieve location of the backupset")
            raise Exception(exception)

    def verify_retrieve_logs_on_client(self, active_log_number, chain_id=None):
        """ Method to Verify if the logs retrieved for a db is present in db2 retrieve location before roll forward

         Args:
            active_log_number   (int)   --  Log number to verify lof file in db2 log retrieve path of backupset

            chain_id (int) -- Chain ID of the active log file to check in retrieve path

        Returns
            boolean  --  If given log file is present in db2 retrieve path of backupset

        Raises:
            Exception:
                If Retrieve logs or retrieve location is not present inside client or unable to verify logs inside client

         """
        try:
            retrieve_location = self.get_backupset_log_retrieve_path()
            log_file = 'S' + '0' * (7 - len(str(active_log_number))) + str(active_log_number) + '.LOG'
            if chain_id:
                chain_id = str(chain_id)
                chain_file = 'C' + '0' * (7 - len(chain_id)) + chain_id
                retrieve_location = retrieve_location[:-8]+chain_file
            log_file_path = self.machine_object.join_path(retrieve_location, log_file)
            if self.machine_object.check_directory_exists(retrieve_location):
                self.log.info(" Retrieve location is available on Client")
                if not self.machine_object.check_file_exists(log_file_path):
                    raise Exception("The Retrieved log files are not available on client")
                else:
                    self.log.info("Retrieved logs are available in Retrieve location on client")
                    return True
            else:
                raise Exception("Given Retrieve location is not available on client")
        except Exception as exception:
            self.log.info("Failed to verify the existence of logs inside client")
            raise Exception(exception)

    def delete_logs_from_retrieve_location(self):
        """
        Method to delete the logs from log retrieve location inside client for backupset
        used while initializing db2 helper

         Raises:
                Exception:
                    if failed to delete logs from log retrieve location of backupset
        """
        try:
            self.log.info("Trying to delete restored logs in db2 log retrieve path inside client")
            log_retrieve_location = self.get_backupset_log_retrieve_path()
            self.machine_object.clear_folder_content(log_retrieve_location)
            self.log.info("Successfully deleted the restored logs from log retrieve path")
        except Exception as exception:
            self.log.info("Failed to delete the logs from log retrieve path")
            raise Exception(exception)

    def verify_encryption_key(self, jobid, storage_policy):

        """
        Method to Verify if the sweep job uses an encryption key

        Args:
            jobid   (str)   --  ID of the sweep job

            storage_policy (str) -- Name of the storage policy used by sweep job

        Returns
            String  --  Encryption key ID if encryption key is used in sweep job

        Raises:
            Exception:
                If Encryption key is not used or same sweep job uses multiple encryption keys

        """

        try:
            # Code to get storage policy copy id
            query = """select * from archgroup where name = '{0}'""".format(storage_policy)
            self.log.info(f"Executing the query '{query}' in csdb")
            self._csdb.execute(query)
            output = self._csdb.fetch_all_rows()
            self.log.info(f"output of the query '{query}' is {output}")
            storage_policy_copy_id = output[0][1]
            self.log.info(f"Storage policy id is {output[0][0]}")
            self.log.info(f"Storage policy default copy id is {storage_policy_copy_id}")

            # code to get arch file id's backed up during sweep job
            query = """select * from archFile where jobId = {0}""".format(jobid)
            self.log.info(f"Executing the query '{query}' in csdb")
            self._csdb.execute(query)
            output = self._csdb.fetch_all_rows()
            self.log.info(f"output of the query '{query}' is {output}")
            arch_file_ids = []
            for x in output:
                if x[1] != 'IdxLogs_V1':
                    arch_file_ids.append(x[0])

            if len(arch_file_ids) == 0:
                raise Exception("No arch files are backed up during the sweep job")
            self.log.info(f"Arch File ID's backed up during the sweep job {jobid} is {arch_file_ids}")

            # code to get encryption keys used by arch files backed up during sweep job
            self.log.info("Verifying encryption key for arch files generated")

            csdb = self.csdb_object_to_execute()
            enc_key_public = None
            enc_key_private = None
            enc_key_id = None
            for x in arch_file_ids:
                # Extracting encryption keys used from output
                query = """EXEC ArchFileEncryptionInfo {0}, 2, {1}, 0""".format(x, storage_policy_copy_id)
                self.log.info(f"Executing the query '{query}' in csdb")
                output = csdb.execute(query)
                self.log.info(f"output of the query '{query}' is {output.rows}")
                if not enc_key_public and not enc_key_private:
                    enc_key_public = output.rows[-1][16]
                    enc_key_private = output.rows[-1][21]
                    enc_key_id = output.rows[-1][27]
                    self.log.info(
                        f"Encryption keys used by the sweep job is Public key = {enc_key_public} , "
                        f"Private key = {enc_key_private}")
                elif enc_key_public != output.rows[-1][16] or enc_key_private != output.rows[-1][21] or enc_key_id != output.rows[-1][27] or enc_key_public == '' or enc_key_private == '':
                    self.log.info(
                        "Failed to verify the encryption key as different encryption keys are being used in same"
                        " sweep job (or) encryption keys are not getting generated ")
                    raise Exception("Failed to verify the encryption key as different encryption keys are being "
                                    "used in same sweep job")
            return enc_key_id
        except Exception as exception:
            self.log.info("Failed to verify encryption keys")
            raise Exception(exception)

    def rotate_encryption_key(self, enc_key_id):
        """
            Method to disable the encryption key related to encryption key id passed

            Args:
                enc_key_id   (str)   --  ID of the encryption ket to disable

            Raises:
                Exception:
                    If failed to disable the encryption key id passed

        """
        try:
            self.log.info("Rotating the encryption key")
            self.log.info(f"Disabling the encryption key with ID {enc_key_id}")
            query = """update ArchEncKeys set isActive = 0 where encKeyId = {0}""".format(enc_key_id)
            csdb = self.csdb_object_to_execute()
            self.log.info(f"Executing the query '{query}' in csdb")
            output = csdb.execute(query)
            self.log.info(f"output of the query '{query}' is {output.rows}")
        except Exception as exception:
            self.log.info("Failed to rotate the encryption key")
            raise Exception(exception)

    def get_active_ma(self):
        """

        Method to return the active ma used by command line subclient when having multiple ma's

        Returns
            String  --  Name of the active MA that is currently being used

        """
        try:
            csdb = self.csdb_object_to_execute()
            command_line_sub_client = self.backupset.subclients.get("(command line)")
            subclient_id = command_line_sub_client.subclient_id
            query = """EXEC ArchGetSubclientMountpathList {0}, 3, 0, 0""".format(subclient_id)
            self.log.info(f"Executing the query '{query}' in csdb")
            output = csdb.execute(query)
            self.log.info(f"output of the query '{query}' is {output.rows}")
            active_ma = None
            for x in output.rows:
                if x[3] == 0:
                    active_ma = x[5].split('*')[0]
                    break
            if active_ma is None:
                raise Exception(
                    "There is not active MA for the given subclient please check the Storage policy and if it is "
                    "properly associated to the given backupset and subclient")
            return active_ma
        except Exception as exception:
            self.log.info("Failed to get the active MA for the given backupset")
            raise Exception(exception)

    def get_rollforward_status(self, db_name):
        """
        Method to get the rollforward status of the database
        Args:
            db_name (str) -- Name of the database
        Returns:
            str -- Rollforward status of the database
        Raises:
            Exception: If there is an error executing the command.
        """
        try:
            self.disconnect_applications(db_name)
            output = self.machine_db2object.execute_command(f"db2 rollforward db {db_name} | grep -i 'Rollforward status'").formatted_output
            self.reconnect()
            if output == '':
                raise Exception("Command didn't return any valid output")
            self.log.info(f"Output returned: {output}")
            return output
        except Exception as e:
            self.log.error(f"Error getting rollforward status for database {db_name}: {str(e)}")
            raise Exception(e)
