# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main helper file for performing SQL Server operations

SQLAutomation, SQLHelper, DBInit, DBValidate, ModifyDatabase are the only classes defined in this file

SQLAutomation: Helper class to initialize objects for SQLHelper

SQLHelper: Helper class to perform sql server operations

DBInit: Helper class to perform SQL Server initialization operations

DBValidate: Helper class to perform SQL Server validation operations

ModifyDatabase: Helper class to perform SQL Server modification operations

SQLAutomation:

    __init__()                      --  initializes SQL Automation Helper objects for SQLHelper

SQLHelper:

    __init__()                      --  initializes SQL Server helper object

    sql_setup()                     --  This function creates the sql setup environment by creating testcase directory,
    databases and subclient.

    create_subclient()              --  This function creates SQL subclient and assign necessary properties

    get_sql_backup_end_time()       --  This function gets the last backup finish time for a sql backup jobid

    get_file_list_restore()         --  This function constructs a list of SQL databases and their files for restore

    sql_restore()                   --  This function is the restore function for SQL restore operations

    do_not_backup_subclient         --  Returns the DO NOT BACKUP SUBCLIENT object

    sql_create_recovery_point()     --  This function creates recovery point and returns the recovery point id and name

    recovery_point_exists()         --  This function returns if the recovery exists or not

    set_recovery_point_expire_time()--  This function sets the recovery point expire time

    sql_table_level_restore()       --  This function is the table-level restore function for SQL

    sql_teardown()                  --  This function performs standard teardown for SQL Server automation

    sql_subclient_dump_path()       --  This function returns the SQL dump and sweep mount path of the subclient

    sql_subclient_dump_path_exists()--  This function returns if the SQL dump and sweep path exists on the media agent

    create_sql_automatic_schedule() --  This function creates an automatic schedule for the given subclient

    set_sweep_start_time()          --  This function sets the time to start the sweep operation

DBInit:

    __init__()                      --  initializes SQL Server helper object

    db_new_create()                 --  This function creates databases based on test case needs

    add_filegroup_and_file()        --  This function adds a file group to the database

    check_database()                --  This function checks if the database already exists

    drop_databases()                --  This function drops databases

    kill_db_connections()           --  This function kills database connections

    set_database_offline()          --  This function sets the database in offline state

    restart_sqlserver_services()    --  This function restarts SQL Server services

    rename_database()               --  This function renames the database by appending random characters

    change_recovery_model()         --  This function changes the recovery model of the database

    set_database_autoclose_property() -- This function is used to set the DB AUTO_CLOSE ON or OFF

DBValidate:

    __init__()                              --  initializes SQL Server helper object

    get_random_db_names_and_filegroups()    --  This function shuffles the database tables and returns some table names

    dump_db_to_file()                       --  This function writes the database tables to file

    dump_tables_to_file()                   --  This function writes the specified database tables to a file

    db_compare()                            --  This function compares two files

    is_db_online()                          --  This function checks to see if specified databases are online.

    get_sql_backup_type()                   --  This function returns the type of backup for a job

    db_path()                               --  This function returns the database file paths for a database

    get_access_states()                     --  This function returns list of access states for a database.

    get_tempdb_create_time()                --  This function returns the creation date/time of tempdb

    get_database_tables()                   --  This function returns a list of table names for the given database

    get_database_state()                    --  This function returns state of the given database

ModifyDatabase:

    __init__()                              --  initializes SQL Server helper object

    modify_db_for_inc()                     --  This function adds additional data to the target databases

    modify_db_for_diff()                    --  This function adds additional data to the target databases

"""
import os
import time
import math
import random
import filecmp
import threading
from datetime import datetime
from cvpysdk.schedules import Schedules
from cvpysdk.subclients.sqlsubclient import SQLServerSubclient
from cvpysdk.policies.storage_policies import StoragePolicy
from . import sqlconstants
from AutomationUtils import constants
from AutomationUtils import database_helper
from AutomationUtils.machine import Machine
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instances import SQLInstance
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.db_instance_details import MSSQLInstanceDetails

global_lock = threading.Lock()


class SQLAutomation(object):
    """Helper class to initialize SQL Helper objects

    Args:
        _sqlclient (str): Name of the client
        _sqlinstance (str): Name of the SQL instance
        _sqluser (str): SQL user name
        _sqlpass (str): SQL password
        _tcobject (:obj:'CVTestCase'): test case object
        _app_aware (bool): True if it is a appaware backup
        _command_centre(Bool): True, if automation is for command centre
        _machine_user (str): Username of the machine to connect to( only applicable if machine is not a CV client)
        _machine_pass (str): Password for the above user
        _instance_exists (bool): True if client/instance already exists in Commcell

    """

    def __init__(self, _tcobject, _sqlclient, _sqlinstance, _sqluser, _sqlpass, _media_agent=None,
                 _app_aware=False, _command_centre=False, _machine_user=None, _machine_pass=None,
                 _instance_exists=True):
        self.log = _tcobject.log
        self.sqlClient = _sqlclient
        self.sqlInstance = _sqlinstance
        self.sqlUser = _sqluser
        self.sqlPass = _sqlpass
        self.tcobject = _tcobject
        self.csdb = database_helper.get_csdb()
        self.command_centre = _command_centre
        self.azure_sql = sqlconstants.SQL_AZ_INS_SUFFIX in _sqlinstance
        self.instance_exists = _instance_exists
        if _app_aware:
            self.instance_exists = False
            self.sqlmachine = Machine(machine_name=_sqlclient,
                                      username=_machine_user,
                                      password=_machine_pass)
        elif self.instance_exists:
            if self.azure_sql:
                access_node = \
                    _tcobject.agent.properties['sql61Prop']['proxies']['memberServers'][0]['client']['clientName']
                if _tcobject.instance.mssql_instance_prop['proxies'].get('memberServers') is not None:
                    access_node = \
                        _tcobject.instance.mssql_instance_prop['proxies']['memberServers'][0]['client']['clientName']
                self.sqlmachine = Machine(access_node, _tcobject.commcell)
            else:
                self.sqlmachine = Machine(_tcobject.client)
        self.localmachine = Machine()


class SQLHelper(object):
    """Helper class to perform SQL Server operations"""

    global global_lock

    def __init__(self, _tcobject, _sqlclient, _sqlinstance, _sqluser, _sqlpass, **kwargs):
        """Initializes SQLHelper object

        Args:
            _tcobject (:obj:'CVTestCase'): test case object
            _sqlclient (str): Name of the client
            _sqlinstance (str): Name of the SQL instance
            _sqluser (str): SQL user name
            _sqlpass (str): SQL password

        Keyword Args:
            _media_agent (str): Name of media agent to use in configuration
            _app_aware (bool): True if it is a appaware backup
            _command_centre(Bool): True, if automation is for command centre
            _machine_user (str): Username of the machine to connect to (only applicable if machine is not a CV client)
            _machine_pass (str): Password for the above user
            _instance_exists (bool): True if client/instance already exists in Commcell

        """

        self.sqlautomation = SQLAutomation(_tcobject, _sqlclient, _sqlinstance, _sqluser, _sqlpass, **kwargs)
        self.dbinit = DBInit(self.sqlautomation)
        self.dbvalidate = DBValidate(self.sqlautomation)
        self.modifydatabase = ModifyDatabase(self.sqlautomation)

        self.log = self.sqlautomation.log
        self.csdb = self.sqlautomation.csdb
        self.tcobject = self.sqlautomation.tcobject
        self.command_centre = self.sqlautomation.command_centre
        self.azure_sql = self.sqlautomation.azure_sql
        self.instance_exists = self.sqlautomation.instance_exists

        self.dbname = None
        self.subclient = None
        self.subcontent = None
        self.tcdir = None
        self.tctime = None
        self.noof_dbs = None
        self.noof_ffg_db = None
        self.noof_files_ffg = None
        self.noof_tables_ffg = None
        self.noof_rows_table = None
        self.storagepolicy = None
        self.snap_setup = False

        if '_media_agent' in kwargs:
            _media_agent = kwargs.get('_media_agent')
            if _media_agent is not None:
                self.ma_machine = Machine(_media_agent, self.tcobject.commcell)

    def sql_setup(
            self,
            storagepolicy=None,
            noof_dbs=5,
            noof_ffg_db=3,
            noof_files_ffg=4,
            noof_tables_ffg=10,
            noof_rows_table=50,
            db_path=None,
            snap_setup=False,
            library_name=None,
            media_agent=None
            ):
        """This function creates the sql setup environment by creating testcase directory, databases and subclient.

        Args:
            storagepolicy (str): Name of storage policy to assign to subclient

            noof_dbs (int): Number of databases to create

            noof_ffg_db (int): Number of file groups per database to create

            noof_files_ffg (int): Number of files per file groups to create

            noof_tables_ffg (int): Number of tables per file groups to create

            noof_rows_table (int): Number of rows per table to create

            db_path (str): Directory path where to create databases. Default location is SQL Server default data path

            snap_setup (bool): Boolean whether this setup is for a snap setup or not

            library_name (str): Name of library to use for storage policy creation

            media_agent (str): Name of media agent to use for storage policy creation

        """
        sqlmachine = self.sqlautomation.sqlmachine
        localmachine = self.sqlautomation.localmachine
        tc_id = self.sqlautomation.tcobject.id

        if self.instance_exists:
            logdir = sqlmachine.client_object.log_directory
        else:  # setups with no client/instance configured, get log dir of controller. CV may not be on sqlmachine.
            logdir = self.tcobject.log_dir

        try:
            # set storage policy name if not given
            if not self.command_centre:  # We dont need this in CC, because there we have plans
                time1 = (datetime.now()).strftime("%H:%M:%S")
                sptime = time1.replace(":", "")
                subclientname = "Subclient{0}_{1}".format(tc_id, time1)
                if storagepolicy is None and self.instance_exists:
                    if library_name is not None and media_agent is not None:
                        storagepolicy = "SQLSP_{0}_{1}".format(tc_id, sptime)
                    elif not snap_setup:
                        storagepolicy = self.tcobject.instance.subclients.get(
                            self.tcobject.instance.subclients.default_subclient).storage_policy
                        if storagepolicy is None:
                            raise Exception("Failed to retrieve storage policy from default subclient. "
                                            "Please assign one and resubmit automation run.")
                    else:
                        raise Exception("Please provide valid storage policy or library and media agent.")

            # generate a random database name
            ransum = ""
            for i in range(1, 7):
                ransum = ransum + random.choice("abcdefghijklmnopqrstuvwxyz")
            dbname = ransum

            # build temporary testcase logging directory and create it
            tcdir = logdir + "/" + tc_id + '-' + ransum

            # create logging directory on local machine since sqlmachine is remote
            if not sqlmachine.is_local_machine:
                sqlmachine.create_directory(tcdir)
                localmachine.create_directory(
                    os.path.join(self.sqlautomation.tcobject.log_dir, os.path.basename(os.path.normpath(tcdir)))
                )
            else:
                tcdir = os.path.join(self.sqlautomation.tcobject.log_dir, os.path.basename(os.path.normpath(tcdir)))
                sqlmachine.create_directory(tcdir)

            # SQL linux require that the destination path of the databases is owned by mssql user.
            if sqlmachine.os_info.lower() == "unix":
                if not sqlmachine.change_folder_owner("mssql", tcdir):
                    raise Exception("Failed to change directory owner. ")

            # build list for subclient content
            subcontent = []
            for i in range(1, noof_dbs + 1):
                db = dbname + repr(i)
                subcontent.append(db)

            # perform database check if exists, if so, drop it first.
            if self.dbinit.check_database(dbname):
                if not self.dbinit.drop_databases(dbname):
                    raise Exception("Unable to drop the database")

            # create databases
            self.log.info("*" * 10 + " Creating database [{0}] ".format(dbname) + "*" * 10)
            if not self.dbinit.db_new_create(dbname, noof_dbs, noof_ffg_db,
                                             noof_files_ffg, noof_tables_ffg, noof_rows_table, dbpath=db_path):
                raise Exception("Failed to create databases.")

            if not self.command_centre:  # No need this block for Command Centre
                # if this is snap setup then create storage policy and snap copy
                if snap_setup:
                    sp_snap_copy = "SQLSnap_Copy_{0}".format(tc_id)
                    if not self.sqlautomation.tcobject.commcell.storage_policies.has_policy(storagepolicy):
                        storagepolicyname = self.sqlautomation.tcobject.commcell.storage_policies.add(
                            storagepolicy,
                            library_name,
                            media_agent,
                            number_of_streams=10
                        )
                    else:
                        storagepolicyname = self.sqlautomation.tcobject.commcell.storage_policies.get(storagepolicy)
                    storagepolicyname.create_secondary_copy(sp_snap_copy, library_name, media_agent, snap_copy=True)
                    schedules_obj = Schedules(self.sqlautomation.tcobject.commcell)
                    if schedules_obj.has_schedule(constants.SNAP_COPY_SCHEDULE_NAME.format(storagepolicy)):
                        schedules_obj.delete(constants.SNAP_COPY_SCHEDULE_NAME.format(storagepolicy))

                elif library_name is not None and media_agent is not None:
                    if not self.sqlautomation.tcobject.commcell.storage_policies.has_policy(storagepolicy):
                        self.sqlautomation.tcobject.commcell.storage_policies.add(
                            storagepolicy,
                            library_name,
                            media_agent
                        )

                if self.instance_exists:
                    # create subclient
                    self.log.info("*" * 10 + " Creating subclient [{0}] ".format(subclientname) + "*" * 10)
                    if not self.create_subclient(subclientname, subcontent, storagepolicy):
                        self.subclient = self.sqlautomation.tcobject.instance.subclients.get(subclientname)
                        raise Exception("Failed to create subclient.")
                    else:
                        self.subclient = self.sqlautomation.tcobject.instance.subclients.get(subclientname)

            if not self.command_centre:
                self.tctime = time1
                self.storagepolicy = storagepolicy
            self.dbname = dbname
            self.subcontent = subcontent
            self.tcdir = tcdir
            self.noof_dbs = noof_dbs
            self.noof_ffg_db = noof_ffg_db
            self.noof_files_ffg = noof_files_ffg
            self.noof_tables_ffg = noof_tables_ffg
            self.noof_rows_table = noof_rows_table
            self.snap_setup = snap_setup

        except Exception as excp:
            self.log.exception("Exception raised in sql_setup()\nError: '{0}'".format(excp))
            raise

    def create_subclient(self, subclientname, subcontent, storagepolicy,
                         subclient_type=sqlconstants.SUBCLIENT_DATABASE):
        """This function makes the necessary calls and assignments to create a SQL subclient.

        Args:
            subclientname (str): Name of subclient to be created
            subcontent (list): Content to add to subclient
            storagepolicy (str): Storage policy to assign to subclient
            subclient_type (str, Optional): Type of sql subclient to create: DATABASE or FILE_FILEGROUP.

        Returns:
            bool: True for success, else False

        """
        log = self.log

        try:
            self.tcobject.instance.subclients.add(subclientname, storagepolicy, subclient_type=subclient_type)
            subclient = self.tcobject.instance.subclients.get(subclientname)
            subclient.content = subcontent
            subclient.log_backup_storage_policy = storagepolicy

            # combine subclient mssql properties with updated values in the request json
            request_json = sqlconstants.SQL_SUBCLIENT_PROP_DICT
            request_json.update(subclient.mssql_subclient_prop)

            # set the subclient mssql properties to the subclient
            subclient_prop = ["_mssql_subclient_prop", request_json]
            subclient.mssql_subclient_prop = subclient_prop

            request_json = sqlconstants.SQL_SUBCLIENT_STORAGE_DICT

            subclient.mssql_subclient_prop = ["_commonProperties['storageDevice']", request_json]
            return True

        except Exception as excp:
            log.exception("Exception raised in create_subclient()\nError: '{0}'".format(excp))
            return False

    def get_sql_backup_end_time(self, jobid, timeformat="datestringformat"):
        """This function gets the last backup finish time for a sql backup jobid

        Args:
            jobid (str): Job id that we are checking end time of
            timeformat (str): Time format either unixformat or datestringformat

        Returns:
            str: sql backup end time for entire job

        """
        log = self.log
        try:
            epochtime = None
            log.info("Get getSqlBackupFinishTime for a given backup job [" + jobid + "]")
            query = "select max(backup_finish_Date) from sqlDbBackupInfo where jobid = '" + jobid + "'"
            self.csdb.execute(query)
            cur = self.csdb.fetch_all_rows()

            for row in cur:
                log.info(row)
                epochtime = int(row[0])

            if timeformat == "unixformat":
                return str(epochtime)

            log.info("Converting EpochSeconds: '{0}' to YYYY/MM/DD HH:MM:SS Format".format(str(epochtime)))
            datetimeobj = datetime.fromtimestamp(epochtime)
            endtime = datetimeobj.strftime("%Y/%m/%d %H:%M:%S")
            return endtime

        except Exception as excp:
            raise Exception("Exception raised in getSqlBackupFinishTime()\nError: '{0}'".format(excp))

    def get_file_list_restore(self, database_list, restore_path=None, filerename=False):
        """This function compiles the file list needed for performing out of place restores

        Args:
            database_list (list): List of dicts of original database names and names to be restored
            restore_path (str, Optional): Path of where to restore databases to
            filerename (bool, Optional): If True the files names will be prefixed with newName_, if False then the file
            names will remain the same as they were on the source.

        Returns:
            list: List of paths for all database files

        """
        dbvalidate = self.dbvalidate
        try:
            ransum = ""
            restore_path_list = []

            for i in range(1, 5):
                ransum = ransum + random.choice("abcdefghijklmnopqrstuvwxyz")

            unix_os = True if self.sqlautomation.sqlmachine.os_info == "UNIX" else False
            for db_dict in database_list:
                for database in db_dict:
                    db = db_dict[database][sqlconstants.DATABASE_ORIG_NAME]
                    dbrename = db_dict[database][sqlconstants.DATABASE_NEW_NAME]
                    listfg, listdb = dbvalidate.db_path(db)

                    p = 0
                    filepath = '/' if unix_os else '\\'
                    for i in listdb:
                        j = listfg[p]
                        file_name = listdb[p].split(filepath)[-1]
                        orig_path, _orig_file = os.path.split(i)

                        if restore_path is None:  # If restore path not passed in take path of original
                            restore_path = orig_path

                        if not filerename:  # If file rename is false keep the original file names
                            restore_path_list.append(sqlconstants.VDI_RESTORE_FORMAT.format(
                                db, dbrename, j, os.path.join(restore_path, file_name), i))
                        else:  # use new file names
                            file_name, file_ext = os.path.splitext(os.path.basename(i))
                            new_file = file_name + "_" + ransum + file_ext
                            restore_path_list.append(sqlconstants.VDI_RESTORE_FORMAT.format(
                                db, dbrename, j, os.path.join(restore_path, new_file), i))
                        p += 1
            return restore_path_list

        except Exception as excp:
            raise Exception("Exception raised in get_file_list_restore()\nError: '{0}'".format(excp))

    def sql_backup(self, backup_type, backup_options=None):
        """This function initiates a backup job, waits for completion, and validates the number of databases backed up

        Args:
            backup_type (str): Type of backup to run: Full, Differential, Transaction_Log
            backup_options (list, optional): List of options to be enabled for the backup operation

        Returns:
            str: Job id of backup job

        """

        if backup_options is None:
            backup_options = []
        log = self.log

        try:
            log.info("*" * 10 + " Starting Subclient {0} Backup ".format(backup_type) + "*" * 10)
            job = self.tcobject.subclient.backup(backup_type, data_options=backup_options)
            log.info("Started {0} backup with Job ID: {1}".format(backup_type, str(job.job_id)))
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run {0} backup job with error: {1}".format(
                        backup_type, job.delay_reason
                    )
                )
            if job.status == 'Completed':
                log.info("Successfully finished {0} backup job".format(backup_type))
            else:
                raise Exception("Backup job {0} did not complete successfully".format(job.job_id))

            j_details = job.details
            if int(j_details['jobDetail']['detailInfo']['numOfObjects']) != \
                    len(self.tcobject.subclient.content):
                raise Exception("Failed to backup all databases in subclient")

            return job.job_id

        except Exception as excp:
            raise Exception("Exception raised in sql_backup()\nError: '{0}'".format(excp))

    def sql_restore(self, content, timeout=30, job_delay_reason=None, restore_count=0, return_job_id=False, **kwargs):
        """This function makes the necessary calls and assignments to perform a SQL restore.

        Args:
            content (list): Content to restore
            timeout (int, optional): Timeout value to wait for job completion
            job_delay_reason (str, optional): Job delay reason
            restore_count (int, optional): Expected database objects as success
            return_job_id (bool, optional): Boolean value on whether to return the job id

        Keyword Args:
            restore_path (str): Path to restore databases to, inplace restore if not specified
            drop_connections_to_databse (bool): Drop connections to database
            overwrite (bool): Overwrite on restore
            to_time (str): Restore to time
            sql_restore_type (str): Type of sql restore (database restore, step restore, recovery only)
            sql_recover_type (str): Type of sql recovery (recover, no recovery, stand by)
            undo_path (str): File path for undo path for sql server standby restores.
            restricted_user (bool): Restore database in restricted user mode
            hardware_revert (bool): True, to do hardware revert for snap restores

        Returns:
            bool: True for success, else False

        """
        log = self.log

        try:

            for database in content:
                if self.dbinit.check_database(database):
                    self.dbinit.kill_db_connections(database, 1, False)

            job = self.tcobject.instance.restore(content, **kwargs)
            log.info("Started restore job with job id: " + str(job.job_id))
            if not job.wait_for_completion(timeout):
                if job_delay_reason is not None:
                    if job.delay_reason.lower().count(job_delay_reason) == 0:
                        raise Exception("Restore did not complete with expected reason.")
                    log.info("Restore completed with expected reason.")
                    if return_job_id:
                        return job.job_id
                    return True
                raise Exception("Restore job failed for unexpected reasons. Check log files.")
            if job_delay_reason is None:
                j_details = job.details
                if restore_count == 0:
                    restore_count = int(len(content))
                if j_details['jobDetail']['detailInfo']['numOfObjects'] != restore_count:
                    raise Exception("Failed to restore all databases")
                log.info("Successfully finished restore job.")
                if return_job_id:
                    return job.job_id
                return True

            raise Exception("Restore job failed for unexpected reasons. Check log files.")

        except Exception as excp:
            raise Exception("Exception raised in sql_restore()\nError: '{0}'".format(excp))

    def run_backup_copy(self, storage_policy=None):
        """Runs the backup copy for the specified storage policy"""
        if storage_policy:
            sp_obj = StoragePolicy(self.tcobject.commcell, storage_policy)
        else:
            sp_obj = StoragePolicy(self.tcobject.commcell, self.storagepolicy)

        self.log.info(f"Starting backup copy for storage policy {sp_obj}")
        job = sp_obj.run_backup_copy()
        self.log.info(f"Backup copy workflow started with job id {job.job_id}")

        if not job.wait_for_completion():
            raise Exception(f"Backup copy job {job.job_id} failed. Check log files")
        if job.status != 'Completed':
            raise Exception(f"Backup copy job {job.job_id} completed with errors. Check log files")
        self.log.info(f"Successfully finished backup copy workflow job {job.job_id}")

    def recovery_point_exists(self, dbname):
        """
        checks if the recovery point exists with the given name

        Args:

            dbname (str): name to the recovery point db

        returns:
            (bool) : True if it exists, else False

        """
        _count, all_recovery_points = self.tcobject.instance.get_recovery_points()
        # no recovery points exists
        if all_recovery_points is None:
            return False
        for recoverypoint in all_recovery_points:
            if dbname in recoverypoint["mountPath"]:
                return True
        return False

    @property
    def do_not_backup_subclient(self):
        """
        returns the properties of the Do Not Backup Subclient properties

        :returns

            object (Subclient) -- returns the do not backup subclient object

        """
        client_id = self.tcobject.client.client_id
        instance_id = self.tcobject.instance.instance_id
        querry = "select id from App_Application where clientId=" + client_id + \
                 " and instance=" + instance_id + " and appTypeId=81 and subclientName='Do Not Backup'"

        self.csdb.execute(querry)
        cur = self.csdb.fetch_all_rows()
        subclient_id = int(cur[0][0])
        backupset = self.tcobject.instance.backupsets.get('defaultBackupSet')
        do_not_backup = SQLServerSubclient(backupset, "Do Not Backup", subclient_id)
        return do_not_backup

    def sql_create_recovery_point(
            self,
            db_name,
            new_db_name=None,
            destination_instance=None,
            expire_days=1,
            snap_setup=False
    ):
        """This function makes the necessary calls to create a recovery point

        Args:
            db_name (str) : Name of database from which recovery point is to be created

            new_db_name (str) : Name of the newly created database database. Default = None

            destination_instance (str) : Destination server(instance) name. Default = None

            expire_days (int) : Time(days) for which the database will be available. Default = 1

            snap_setup (bool) : Make it true if RP is for a snap setup

        Returns:
            rp_id : id to uniquely access the recovery point, if job is success

            rp_name : name of the database created, if job is success
        """
        log = self.log
        try:
            job, rp_id, rp_name = self.tcobject.instance.create_recovery_point(
                database_name=db_name,
                new_database_name=new_db_name,
                destination_instance=destination_instance,
                expire_days=expire_days,
                snap=snap_setup
            )
            log.info(f"Submitted recovery point creation job with job id {job.job_id} for database {db_name}")
            if not job.wait_for_completion():
                raise Exception(f"Recovery point creation failed.Check logs for details")
            else:
                log.info(f"Created recovery point with name {rp_name} and recovery point id {rp_id}")
                return rp_id, rp_name

        except Exception as exp:
            raise Exception(f"Exception raised in sql_create_recovery_point().\n Error : {exp}")

    @staticmethod
    def set_recovery_point_expire_time(recovery_point_id, sql_con, expire_time):
        """changes the expire time of the recovery point to present time + requested time

            Args:
                recovery_point_id (int) : id of the recovery point

                sql_con (db_handler) : sql con to the csdb sa user

                expire_time (timestamp) : expire time in unix time format

            returns:
                    None

            raise Exception:
                if input are not valid

                unable to change the expire time
        """
        if not isinstance(sql_con, database_helper.MSSQL):
            raise Exception("invalid sql connection")

        if not isinstance(recovery_point_id, int):
            raise Exception("Data type of inputs is not valid")

        now = int(datetime.timestamp(datetime.now()))
        if expire_time < now:
            raise Exception("invalid Expire Time")

        sql_con.execute("update App_LiveBrowseRecoveryPoints"
                        " set expireTime={0} where id={1};".format(expire_time, recovery_point_id))
        result = sql_con.execute("select expireTime from App_LiveBrowseRecoveryPoints"
                                 " where id={0};".format(recovery_point_id))
        if result.rows[0].expireTime != expire_time:
            raise Exception("unable to change expire time"
                            " to {0} for recoveryPointId={1}".format(expire_time, recovery_point_id))

    def sql_table_level_restore(self,
                                src_db_name,
                                tables_to_restore,
                                rp_name,
                                destination_db_name=None,
                                include_child_tables=True,
                                include_parent_tables=False):

        """This function makes the necessary calls to start a table level restore
        Args:

            src_db_name(str) : Name of the source database

            tables_to_restore(list) : List of tables to restore

            rp_name(str) : Name of corresponding recovery point

            destination_db_name(str) : Destination database name

            include_child_tables(bool) : Includes all child tables in restore. Default value is true

            include_parent_tables(bool) : Includes all parent tables in restore. Default value is false

        Returns:
            List of restored tables
        """
        log = self.log
        try:
            if destination_db_name is None:
                timestamp = (datetime.now()).strftime("%H:%M:%S")
                timestamp = timestamp.replace(":", "")
                destination_db_name = src_db_name + '_Table_Restore_' + timestamp
                status = self.dbinit.db_new_create(
                    dbname=destination_db_name,
                    noofdbs=1,
                    nooffilegroupsdb=0,
                    nooffilesfilegroup=0,
                    nooftablesfilegroup=0,
                    noofrowstable=0)
                if status:
                    # '1' is appended here, because dbs are created by db_new_create() in that format
                    destination_db_name = destination_db_name + '1'
                    log.info(f"Database created with name {destination_db_name}")
                else:
                    raise Exception(f"Destination database creation failed")
            else:
                if not self.dbinit.check_database(destination_db_name):
                    raise Exception(f"Database {destination_db_name} not found")

            compare_time = datetime.now()
            job = self.tcobject.instance.table_level_restore(
                src_db_name,
                tables_to_restore,
                destination_db_name,
                rp_name,
                include_child_tables,
                include_parent_tables
            )
            restored_tables = []
            log.info(f"Submitted table level restore job with job id {job.job_id}")
            if not job.wait_for_completion():
                raise Exception(f"Table level restore failed.Check logs for details")
            else:
                log.info(f"Table level restore job with job id {job.job_id} completed")
                tables_restored = self.dbvalidate.get_database_tables(destination_db_name, True)
                src_db_tables = self.dbvalidate.get_database_tables(src_db_name)
                for row in tables_restored:
                    table = row[0]
                    if row[1] > compare_time:
                        if table in src_db_tables:
                            restored_tables.append('[dbo].[' + table + ']')
                        else:
                            raise Exception(f"Restored table {table} not found in source database {src_db_name}")
                return destination_db_name, restored_tables
        except Exception as exp:
            raise Exception(f"Exception raised in sql_table_level_restore().\n Error : {exp}")

    def sql_teardown(self, cleanup_dumpsweep=False, delete_instance=False):
        """
        This function performs standard teardown for SQL Server automation on the basic created items from sql_setup.

        Args:

            cleanup_dumpsweep(bool/Optional) :   Boolean value on whether to clean up a dump/sweep setup during teardown
            Default is False

            delete_instance(bool/Optional)   :   Boolean value on whether to delete the instance during teardown
            Default is False

        """
        log = self.log
        sqlmachine = self.sqlautomation.sqlmachine
        localmachine = self.sqlautomation.localmachine

        try:
            # drop databases
            if not self.dbinit.drop_databases(self.dbname):
                log.error("Unable to drop the dataBase")
            # delete directories
            tcdir_local_list = localmachine.get_folders_in_path(self.tcobject.log_dir)
            for tcdir_local in tcdir_local_list:
                if self.tcobject.id in tcdir_local:
                    localmachine.remove_directory(tcdir_local)
            if not sqlmachine.is_local_machine and self.instance_exists:
                # Remote SQL machine, get directories and remove them
                tcdir_remote_list = sqlmachine.get_folders_in_path(sqlmachine.client_object.log_directory)
                for tcdir_remote in tcdir_remote_list:
                    if self.tcobject.id in tcdir_remote:
                        sqlmachine.remove_directory(tcdir_remote)

            if cleanup_dumpsweep:
                self.ma_machine.remove_registry("MSSQLAgent", "SweepStartTime")
                if self.ma_machine.os_info.lower() == "windows":
                    self.ma_machine.execute_command("fltmc unload CVDLP")
                    self.ma_machine.remove_directory(self.sql_subclient_dump_path(self.subclient))
                    self.ma_machine.execute_command("fltmc load CVDLP")
                else:
                    self.ma_machine.remove_directory(self.sql_subclient_dump_path(self.subclient))

            if delete_instance:
                if self.sqlautomation.sqlInstance in list(self.tcobject.agent.instances.all_instances.keys()):
                    try:
                        log.info("Deleting instance [{0}]".format(self.sqlautomation.sqlInstance))
                        self.tcobject.agent.instances.delete(self.sqlautomation.sqlInstance)
                    except Exception:
                        log.exception("Instance [{0}] failed to be removed.".format(self.sqlautomation.sqlInstance))
            elif self.instance_exists:
                # clean up all subclients including orphans
                for subclient in list(self.tcobject.instance.subclients.all_subclients.keys()):
                    if subclient.startswith("subclient{0}_".format(self.sqlautomation.tcobject.id)):
                        try:
                            log.info("Deleting subclient [{0}]".format(subclient))
                            self.tcobject.instance.subclients.delete(subclient)
                        except Exception:
                            log.exception("Subclient [{0}] failed to be removed.".format(subclient))
                            continue
            if not self.command_centre:
                # delete storage policy and any possible orphaned storage policies
                for storage_policy in list(self.tcobject.commcell.storage_policies.all_storage_policies.keys()):
                    if storage_policy.startswith("sqlsp_{0}".format(self.tcobject.id)):
                        try:
                            log.info("Deleting storage policy [{0}]".format(storage_policy))
                            self.tcobject.commcell.storage_policies.delete(storage_policy)
                        except Exception:
                            log.exception("Storage policy [{0}] failed to be removed.".format(self.storagepolicy))
                            continue
        except Exception as excp:
            raise Exception("Exception raised in sql_teardown()\nError: '{0}'".format(excp))

    def sql_subclient_dump_path(self, subclient_obj):
        """
        Returns the SQL dump and sweep mount path of the subclient.

        Args:
            subclient_obj(object) : Instance of the subclient class

        returns:
            (str) : SQL subclient dump and sweep mount path

        """
        try:
            # query to retrieve mount path for dump/sweep for given subclient
            mount_path_query = "SELECT CONCAT(MDC.Folder, '/', MP.MountPathName) " \
                               "FROM APP_SubclientToMountpathMapping ASM " \
                               "JOIN MMMountPath MP ON MP.MediaSideId = ASM.mountPathId " \
                               "JOIN MMMountPathToStorageDevice MPS ON MPS.MountPathId = MP.MountPathId " \
                               "JOIN MMDeviceController MDC ON MDC.DeviceId = MPS.DeviceId " \
                               "WHERE ASM.subClientId = {0}".format(subclient_obj.subclient_id)

            self.csdb.execute(mount_path_query)
            cur = self.csdb.fetch_all_rows()
            mount_path = str(cur[0][0])
            sql_dump_sweep_filepath = mount_path + "/CV_MAGNETIC/CV_APP_DUMPS/" + subclient_obj.subclient_guid

            return sql_dump_sweep_filepath
        except Exception as excp:
            raise Exception("Exception raised in sql_subclient_dump_path()\nError: '{0}'".format(excp))

    def sql_subclient_dump_path_exists(self, sql_dump_filepath):
        """
        This function checks if the SQL dump and sweep path on the media agent exists.

        Args:

            sql_dump_filepath(str) : File path on the library where the SQL dumps are stored.

        Returns:
            bool: True for exists, else False

        """
        try:
            # check the dump/sweep location exists but give it a minute otherwise fail
            retry = 4
            dump_dir_exists = False
            while retry > 0:
                if not self.ma_machine.check_directory_exists(sql_dump_filepath):
                    time.sleep(30)
                else:
                    dump_dir_exists = True
                    break
                retry -= 1

            return True if dump_dir_exists else False

        except Exception as excp:
            raise Exception("Exception raised in sql_subclient_dump_path_exists()\nError: '{0}'".format(excp))

    def create_sql_automatic_schedule(
            self,
            subclient,
            min_interval_minutes=1,
            max_interval_minutes=2,
            use_dump_sweep=False
    ):
        """This function creates an automatic schedule for the given subclient
        Args:

            subclient(object) : Instance of the subclient class to create schedule for

            min_interval_minutes(int) : Minimum minutes for automatic schedule

            max_interval_minutes(int) : Maximum minutes for automatic schedule

            use_dump_sweep(bool) : Boolean value whether to enable dump and sweep for schedule

        Returns:
            object - instance of the schedule class for this schedule
        """
        from Server.Scheduler.schedulerhelper import ScheduleCreationHelper
        schedule_helper = ScheduleCreationHelper(self.tcobject.commcell)
        try:
            # dict for automatic schedule pattern
            schedule_pattern_dict = {
                "freq_type": "automatic",
                "max_interval_hours": 0,
                "sweep_start_time": 3600,
                "use_storage_space_ma": use_dump_sweep,
                "min_interval_minutes": min_interval_minutes,
                "max_interval_minutes": max_interval_minutes
            }

            schedule_helper.create_schedule(
                "subclient_backup",
                backup_type="transaction_log",
                schedule_pattern=schedule_pattern_dict,
                wait=False,
                subclient=subclient
            )
        except Exception as excp:
            raise Exception("Exception raised in create_sql_osc_schedule()\nError: '{0}'".format(excp))

    def set_sweep_start_time(self, sweep_start_time):
        """This function sets the time to start the sweep operation
        Args:

            sweep_start_time(str) : Time to initiate the sweep operation. Format: HH:MM

        """
        try:
            if self.ma_machine.check_registry_exists("MSSQLAgent", "SweepStartTime"):
                self.ma_machine.update_registry("MSSQLAgent", "SweepStartTime", sweep_start_time, "String")
            else:
                self.ma_machine.create_registry("MSSQLAgent", "SweepStartTime", sweep_start_time)

        except Exception as excp:
            raise Exception("Exception raised in set_sweep_start_time()\nError: '{0}'".format(excp))


class DBInit(object):
    """Helper class to perform SQL Server initialization operations"""

    global global_lock

    def __init__(self, _sqlautomation):
        """Initializes SQLHelper object

        Args:
            _sqlautomation (:obj: 'SQLAutomation'): Instance of SQLAutomation

        """

        self.sqlhelper = _sqlautomation
        self.log = self.sqlhelper.log
        self._unix_os = True if self.sqlhelper.sqlmachine.os_info == "UNIX" else False

    def db_new_create(self, dbname, noofdbs, nooffilegroupsdb, nooffilesfilegroup, nooftablesfilegroup,
                      noofrowstable, size=0, dbpath=None, recoverymodel="FULL"):
        """This function creates as many databases with as many tables specified

            The databases will be created with the names "databasename+dbnumber" with
            "tab+dbnumber+filegroupnumber+tablenumber+rownumber","tabm+dbnumber+tablenumber+rownumber"

            This creates as many no of dbs, filegroups, tables for each file group the user requested.

        Args:
            dbname (str): Database name
            noofdbs (int): Number of databases to be created
            nooffilegroupsdb (int): Number of file groups for each database
            nooffilesfilegroup (int): Number of files for each file group
            nooftablesfilegroup (int): Number of table for each file group
            noofrowstable (int): Number of rows for each table
            size (int, optional): Database size will be limited to optional size of 1MB if passed.
                                    Default is 0 which will default to native SQL Server size.
            dbpath (str, optional): Path where to create databases. Default is SQL Server native location.
            recoverymodel (str, optional): Create database with specific recovery model. Default is FULL.

        Returns:
            bool: True for success, else False

        """
        log = self.sqlhelper.log
        sqlcon = None
        try:
            if not self.sqlhelper.azure_sql:
                with global_lock:
                    sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                                   self.sqlhelper.sqlPass, "master", use_pyodbc=True,
                                                   unix_os=self._unix_os)
                cur = sqlcon.execute("SELECT name FROM sys.databases")
                for row in cur.rows:
                    log.info("[{0}]".format(row.name))
                query = "SELECT SUBSTRING(physical_name, 1, CHARINDEX(N'master.mdf', LOWER(physical_name)) - 1) " \
                        "DataFileLocation FROM master.sys.master_files WHERE database_id = 1 AND FILE_ID = 1"
                cur = sqlcon.execute(query)
                dbcreationpath = dbpath
                filepath = '\\' if not self._unix_os else '/'
                for row in cur.rows:
                    if dbpath is None:
                        dbcreationpath = row.DataFileLocation
                    log.info("Data Files Creation Path: [{0}]".format(dbcreationpath))
                # creating the tables for each db on ndf
                for i in range(1, noofdbs + 1):
                    dbname1 = dbname + str(i)
                    if dbpath is None:
                        sqlcon.execute("CREATE DATABASE [{0}]".format(dbname1))
                        time.sleep(2)
                        sqlcon.execute("ALTER DATABASE [{0}] SET AUTO_CLOSE OFF WITH NO_WAIT;".format(dbname1))
                    else:
                        dbpathname = dbcreationpath + filepath + dbname1
                        sqlcon.execute(
                            "CREATE DATABASE [" + dbname1 + "] ON PRIMARY(NAME = N'" + dbname1 + "', FILENAME = N'" +
                            dbpathname + ".mdf') LOG ON (NAME = N'" + dbname1 + "_log', FILENAME = N'" +
                            dbpathname + "_log.ldf')")

                    sqlcon.execute("ALTER DATABASE [{0}] SET RECOVERY {1}".format(dbname1, recoverymodel))
                    log.info("Database [{0}] is created.".format(dbname1))
                    for j in range(1, nooffilegroupsdb + 1):
                        file_group1 = "File_group" + str(i) + str(j)
                        sqlcon.execute("ALTER DATABASE [{0}] ADD FILEGROUP [{1}]".format(dbname1, file_group1))
                        log.info("File group [{0}] is created".format(file_group1))

                        for k in range(1, nooffilesfilegroup + 1):
                            filename1 = dbname + str(i) + str(j) + str(k)
                            path1 = dbname + str(i) + str(j) + str(k) + ".ndf"
                            if dbpath is None:
                                logdirpath = dbcreationpath + path1
                            else:
                                logdirpath = dbcreationpath + filepath + path1
                            if size == 1:
                                sqlcon.execute(
                                    "ALTER DATABASE [" + dbname1 + "] ADD FILE(NAME = N'" +
                                    filename1 + "', FILENAME = N'" + logdirpath +
                                    "' , SIZE = 1, MAXSIZE = 2MB, FILEGROWTH = 10%) TO FILEGROUP "
                                    "[" + file_group1 + "]"
                                )
                            else:
                                sqlcon.execute(
                                    "ALTER DATABASE [" + dbname1 + "] ADD FILE(NAME = N'" +
                                    filename1 + "', FILENAME = N'" + logdirpath +
                                    "' , SIZE = 10, MAXSIZE = 20MB, FILEGROWTH = 10%) TO FILEGROUP "
                                    "[" + file_group1 + "]"
                                )
                            log.info("File [{0}] is created under file group [{1}]".format(filename1, file_group1))

                        for l in range(1, nooftablesfilegroup + 1):
                            sqlcon.execute("use [{0}]".format(dbname1))
                            tab1 = "tab" + str(i) + str(j) + str(l)

                            sqlcon.execute(
                                "create table [dbo].[" + tab1 + "](a bigint,c bit,d char(8),"
                                "e date,f datetime,g datetime2(7),i decimal(18,0),j float,o int,p money,q nchar(10),"
                                "r ntext,s numeric(18,0),t nvarchar(50),u nvarchar(MAX),v real,w smalldatetime,x "
                                "smallint,y smallmoney,z text,aa time(7),bb tinyint,cc uniqueidentifier,ff varchar(50),"
                                "gg varchar(MAX)) ON " + file_group1)

                            for z in range(1, noofrowstable + 1):
                                query = "INSERT INTO [" + dbname1 + "].[dbo].[" + tab1 + "] VALUES " \
                                        "( 123456789,'True','dvsdv','2009-11-19','2009-11-19 11:01:30.000'," \
                                        "'2009-02-12 12:30:15.1234567',686868,66.666869,32,$30000,'comm'," \
                                        "'cvcvcvcvcvcvc',686868,'commvault','" + str(i) + str(j) + str(l) + str(z) + \
                                        "',56.56565,'2009-01-01 03:50:00',1,$1000,'comm','12:30:15.1234567',0," \
                                        "'6F9619FF-8B86-D011-B42D-00C04FC964FF','commvault','cvcvcvcvcvcvcvc')"
                                sqlcon.execute(query)

                # creating the tables for each db on mdf
                for i in range(1, noofdbs + 1):
                    dbname1 = dbname + str(i)
                    for l in range(1, nooftablesfilegroup + 1):
                        sqlcon.execute("use [{0}]".format(dbname1))
                        tab1 = "tabm" + str(i) + str(l)
                        sqlcon.execute(
                            "create table [dbo].[" + tab1 + "](a bigint,c bit,d char(8),e date,f datetime,"
                            "g datetime2(7),i decimal(18,0),j float,o int,p money,q nchar(10),r ntext,s numeric(18,0),"
                            "t nvarchar(50),u nvarchar(MAX),v real,w smalldatetime,x smallint,y smallmoney,z text,"
                            "aa time(7),bb tinyint,cc uniqueidentifier,ff varchar(50),gg varchar(MAX))")

                        for z in range(1, noofrowstable + 1):
                            query = "INSERT INTO [" + dbname1 + "].[dbo].[" + tab1 + "] VALUES " \
                                "( 123456789,'True','dvsdv','2009-11-19','2009-11-19 11:01:30.000'," \
                                "'2009-02-12 12:30:15.1234567',686868,66.666869,32,$30000,'comm','cvcvcvcvcvcvc'," \
                                "686868,'commvault','" + str(i) + str(l) + str(z) + "',56.56565,'2009-01-01 " \
                                "03:50:00',1,$1000,'comm','12:30:15.1234567',0,'6F9619FF-8B86-D011-B42D-00C04FC964FF'" \
                                ",'commvault','cvcvcvcvcvcvcvc')"
                            sqlcon.execute(query)
                return True
            else:
                with global_lock:
                    sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                                   self.sqlhelper.sqlPass, "master", use_pyodbc=True,
                                                   unix_os=self._unix_os)
                cur = sqlcon.execute("SELECT name FROM sys.databases")
                for row in cur.rows:
                    log.info("[{0}]".format(row.name))
                # creating the databases for each db
                for i in range(1, int(noofdbs) + 1):
                    dbname1 = dbname + str(i)
                    sqlcon.execute("CREATE DATABASE [%s]" % dbname1)
                    sqlcon.execute("ALTER DATABASE [%s] SET COMPATIBILITY_LEVEL = 120" % dbname1)
                # creating the tables for each db on mdf
                for i in range(1, int(noofdbs) + 1):
                    dbname1 = dbname + str(i)
                    sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                                   self.sqlhelper.sqlPass, dbname1, use_pyodbc=True,
                                                   unix_os=self._unix_os)
                    for l in range(1, int(nooftablesfilegroup) + 1):
                        tab1 = "tab" + str(i) + str(l)
                        sqlcon.execute(
                            "CREATE TABLE [dbo].[" + tab1 + "](a bigint,c bit,d char(8),e date,f datetime,"
                            "g datetime2(7),i decimal(18,0),j float,o int,p money,q nchar(10),r ntext,s numeric(18,0),"
                            "t nvarchar(50),u nvarchar(MAX),v real,w smalldatetime,x smallint,y smallmoney,z text,"
                            "aa time(7),bb tinyint,cc uniqueidentifier,ff varchar(50),gg varchar(MAX))"
                        )
                        for z in range(1, int(noofrowstable) + 1):
                            query = "INSERT INTO [dbo].[" + tab1 + "] VALUES ( 123456789,'True','dvsdv','2009-11-19'," \
                                    "'2009-11-19 11:01:30.000','2009-02-12 12:30:15.1234567',686868,66.666869,32," \
                                    "$30000,'comm','cvcvcvcvcvcvc',686868,'commvault','" + str(i) + str(l) + str(z) + \
                                    "',56.56565,'2009-01-01 03:50:00',1,$1000,'comm','12:30:15.1234567',0," \
                                    "'6F9619FF-8B86-D011-B42D-00C04FC964FF','commvault','cvcvcvcvcvcvcvc')"
                            sqlcon.execute(query)
                return True

        except Exception as excp:
            raise Exception("Exception raised in db_new_create()\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def add_filegroup_and_file(self, dbname, filegroupname, filename, logdir):
        """This function adds the file group to database.

        Args:
            dbname (str) : Database name to add filegroup to
            filegroupname (str) : Name of filegroup to add
            filename (str) : Name of file for filegroup
            logdir (str) : Directory of testcase temp file logging

        Returns:
            bool: True for success, else False

        """

        sqlcon = None
        try:
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True,
                                               unix_os=self._unix_os)

            tclogdir = os.path.join(logdir, filename)

            sqlcon.execute("ALTER DATABASE [{0}] ADD FILEGROUP [{1}]".format(dbname, filegroupname))
            sqlcon.execute("ALTER DATABASE [{0}] ADD FILE(NAME = N'{1}', FILENAME = N'{2}', SIZE = 20, "
                           "MAXSIZE = 30MB, FILEGROWTH = 10%) TO FILEGROUP [{3}]"
                           .format(dbname, filename, tclogdir, filegroupname))
            return True

        except Exception as excp:
            raise Exception("Exception raised in add_filegroup_and_file()\nError: {0}".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def check_database(self, databasename):
        """This function checks for the dataBase.

        Args:
            databasename (str) : Database name

        Returns:
            bool: True for exists, else False

        """
        log = self.sqlhelper.log
        sqlcon = None
        try:
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True,
                                               unix_os=self._unix_os)

            cur = sqlcon.execute("SELECT name FROM sys.databases")
            for row in cur.rows:
                if databasename in row.name:
                    log.info("Database {0} exists".format(databasename))
                    return True
            log.info("Database {0} does not exist.".format(databasename))
            return False

        except Exception as excp:
            raise Exception("Exception raised in check_database\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def drop_databases(self, databasename, useexistingdb=True):
        """This function drops the database for the given test case.

        Args:
            databasename (str) : Database name
            useexistingdb (bool, optional) : Drop all databases with names that contain provided databasename

        Returns:
            bool: True for success, else False

        """
        log = self.sqlhelper.log
        sqlcon = None
        try:
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True,
                                               unix_os=self._unix_os)

            # This code block is to handle specific provided database name only.
            if not useexistingdb:
                cur = sqlcon.execute("SELECT name FROM sys.databases where name = '{0}'".format(databasename))
                if databasename == cur.rows[0].name:
                    if not self.kill_db_connections(databasename, 1, useexistingdb):
                        log.error("Unable to kill database connection.")
                        return False
                    sqlcon.execute("drop database [{0}]".format(databasename))
                    log.info("{0} is dropped from {1} ".format(databasename, self.sqlhelper.sqlInstance))
                    return True
                return False
            # This code block is to handle all databases that contain the provided database name.
            cur = sqlcon.execute("SELECT name FROM sys.databases")
            for row in cur.rows:
                if databasename in row.name:
                    db = row.name

                    if not self.kill_db_connections(db, 1, useexistingdb=False):
                        log.error("Unable to kill database connection.")
                    try:
                        sqlcon.execute("drop database [{0}]".format(db))
                        log.info("{0} is dropped from {1} ".format(db, self.sqlhelper.sqlInstance))
                    except Exception as excp:
                        log.error("Failed to drop database.\nError: '{0}'".format(excp))
                        continue
            return True

        except Exception as excp:
            log.exception("Exception raised in drop_databases()\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def kill_db_connections(self, databasename, noofdbs, useexistingdb):
        """This function kills the list of open connections to the given DataBase

        Args:
            databasename (str) : Database name
            noofdbs (int) : Number of databases to be dropped
            useexistingdb (bool) : Kill connections for all databases that begin with databasename

        Returns:
            bool: True for success, else False

        """
        try:
            sqlmachine = self.sqlhelper.sqlmachine
            sqlinstance = self.sqlhelper.sqlInstance

            if useexistingdb:
                dbflag = 0
            else:
                dbflag = 1

            path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                'SQL', 'Scripts', 'KillDBConnections.sql')

            cmd = "sqlcmd -i \"" + str(path) + "\" -v databasename =\"" + databasename + "\" " \
                "dbcount =\"" + str(noofdbs) + "\" dbflag =\"" + str(dbflag) + "\" -U " + \
                  self.sqlhelper.sqlUser + " -P " + self.sqlhelper.sqlPass + " -S \"" + sqlinstance + "\""

            sqlmachine.execute_command(cmd)
            return True

        except Exception as excp:
            raise Exception("Exception raised in kill_db_connections()\nError: '{0}'".format(excp))

    def set_database_autoclose_property(self, databasename, value="ON"):
        """This function sets the database autoclose property on or off

        Args:
            databasename (str)  : Database name

            value   (str): sets the auto close property to on or off

        Returns:
            bool: True for success, else False

        """
        sqlcon = None
        value = value.lower()
        if value not in ["on", "off"]:
            raise Exception("invalid value specified: {0}".format(value))
        try:
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True,
                                               unix_os=self._unix_os)

            sqlcon.execute("ALTER DATABASE [{0}] SET AUTO_CLOSE {1} WITH NO_WAIT;".format(databasename, value))
            self.log.info("AUTO_CLOSE is {0} for database {1}".format(value, databasename))
            return True

        except Exception as excp:
            raise Exception("Exception raised in set_database_sutoclose_property()\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def set_database_offline(self, databasename):
        """This function sets the database to offline.

        Args:
            databasename (str) : Database name

        Returns:
            bool: True for success, else False

        """
        log = self.sqlhelper.log
        sqlcon = None

        try:
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True,
                                               unix_os=self._unix_os)

            sqlcon.execute("ALTER DATABASE [{0}] SET OFFLINE WITH ROLLBACK IMMEDIATE".format(databasename))
            log.info("{0} database is offline".format(databasename))
            return True

        except Exception as excp:
            raise Exception("Exception raised in set_database_offline()\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def restart_sqlserver_services(self, action=1):
        """This function restarts the services of sql server

        Args:
            action (int, optional): 1 = Restart Services (default)
                                    2 = Stop Services
                                    3 = Start Services

        Returns:
            bool: True for success, else False

        """
        log = self.sqlhelper.log
        sqlmachine = self.sqlhelper.sqlautomation.sqlmachine
        sqlinstance = self.sqlhelper.sqlInstance

        try:
            # STOP SERVICES
            if action in (1, 2):
                log.info("Stopping the SQL Server Services")
                sqlmachine.execute_command("net stop \"SQL Server Agent ({0})\"".format(sqlinstance))
                # command output is an object.. need to parse output message on success or failure.
                log.info("Sleep for 30 seconds while stopping SQL Server Agent")
                time.sleep(30)
                sqlmachine.execute_command("net stop \"SQL Server ({0})\"".format(sqlinstance))
                # command output is an object.. need to parse output message on success or failure.
                log.info("Sleep for 30 seconds while services are stopping.")
                time.sleep(30)

            # START SERVICES
            if action in (1, 3):
                log.info("Starting the SQL Server services")
                sqlmachine.execute_command("net action \"SQL Server ({0})\"".format(sqlinstance))
                # command output is an object.. need to parse output message on success or failure.
                log.info("Sleep for 30 seconds while services are starting.")
                time.sleep(30)
                return True

            return True
        except Exception as excp:
            raise Exception("Exception raised in restart_sqlserver_services()\nError: {0}".format(excp))

    def rename_database(self, databasename):
        """This function renames the database by appending some random characters
        On success returns (renamed database, True) else (1, False)

        Args:
            databasename (str): Database name

        Returns:
            str: database name
            bool: True for success, else False

        """
        sqlcon = None

        try:
            ransum = ""

            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True,
                                               unix_os=self._unix_os)
            for _ in range(1, 7):
                ransum = ransum + random.choice("abcdefghijklmnopqrstuvwxyz")

            database_rename = databasename + "_" + ransum
            sqlcon.execute("ALTER DATABASE [{0}] MODIFY NAME = [{1}]".format(databasename, database_rename))

            return database_rename, True
        except Exception as excp:
            raise Exception("Exception raised in rename_database()\nError: {0}".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def change_recovery_model(self, databasename, noofdbs, recoverymodel):
        """This function changes the recovery model for specified databases.

        Args:
            databasename (str): Database name
            noofdbs (int): Number of DBs to change recovery model
            recoverymodel (str): Recovery model to set database to

        Returns:
            bool: True for success, else False

        """
        sqlcon = None

        try:
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True,
                                               unix_os=self._unix_os)

            for i in range(1, noofdbs + 1):
                sqlcon.execute("ALTER DATABASE [{0}{1}] SET RECOVERY {2}".format(databasename, i, recoverymodel))

            return True

        except Exception as excp:
            raise Exception("Exception raised  in change_recovery_model()\nError: {0}".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()


class DBValidate(object):
    """Helper class to perform SQL Server validation operations"""

    global global_lock

    def __init__(self, _sqlautomation):
        """Initializes DBValidate object

        Args:
            _sqlautomation (:obj:'SQLAutomation'): Instance of SQLAutomation

        """

        self.sqlhelper = _sqlautomation

    def db_compare(self, sqldump_file1, sqldump_file2):
        """This function compares sql database dump files.

        Args:
            sqldump_file1 (str): File to be compared to file2
            sqldump_file2 (str): File to be compared to file1

        Returns:
            bool: True for success, False otherwise.

        """
        log = self.sqlhelper.log

        try:

            sqldump_file1 = os.path.basename(sqldump_file1)
            sqldump_file2 = os.path.basename(sqldump_file2)

            if filecmp.cmp(
                    os.path.abspath(
                        os.path.join(
                            self.sqlhelper.tcobject.log_dir,
                            os.path.basename(os.path.normpath(self.sqlhelper.tcobject.sqlhelper.tcdir)),
                            sqldump_file1
                        )
                    ),
                    os.path.abspath(
                        os.path.join(
                            self.sqlhelper.tcobject.log_dir,
                            os.path.basename(os.path.normpath(self.sqlhelper.tcobject.sqlhelper.tcdir)),
                            sqldump_file2
                        )
                    )
            ):
                log.info("Files {0} and {1} are identical".format(sqldump_file1, sqldump_file2))
                return True
            log.error("Files {0} and {1} differ!".format(sqldump_file1, sqldump_file2))
            return False

        except Exception as excp:
            raise Exception("Exception raised in db_compare()\nError: '{0}'".format(excp))

    @staticmethod
    def get_random_dbnames_and_filegroups(randomization, noofdbs, nooffilegroupsdb, nooftablesfilegroup):
        """This function shuffles the database tables and returns some table names

        Args:
            randomization (int): Randomization 0 to 100
            noofdbs (int): Number of databases
            nooffilegroupsdb (int): Number of file groups for each database
            nooftablesfilegroup (int): Number of file for each file group

        Returns:
            bool: True if success, False otherwise
            list: database numbers
            list: file group numbers
            list: table numbers

        """
        try:
            list1 = []
            list2 = []
            list3 = []
            for i in range(1, noofdbs + 1):
                list1.append(i)
            for i in range(1, nooffilegroupsdb + 1):
                list2.append(i)
            for i in range(1, nooftablesfilegroup + 1):
                list3.append(i)
            r = randomization
            random.shuffle(list1)
            random.shuffle(list2)
            random.shuffle(list3)
            i = int(math.ceil((float(r) / float(100)) * noofdbs))
            l = []
            m = []
            n = []
            a = 0
            for _ in range(1, i + 1):
                l.append(list1[a])
                a = a + 1
            i = int(math.ceil((float(r) / float(100)) * nooffilegroupsdb))
            a = 0
            for _ in range(1, i + 1):
                m.append(list2[a])
                a = a + 1
            i = int(math.ceil((float(r) / float(100)) * nooftablesfilegroup))
            a = 0
            for _ in range(1, i + 1):
                n.append(list3[a])
                a = a + 1
            return True, l, m, n

        except Exception as excp:
            raise Exception("Exception raised in get_random_dbnames_and_filegroups()\nError: '{0}'".format(excp))

    def dump_db_to_file(self, fname, databasename, l, m, n, incbackuptype, p=1, use_same_db_name=False):
        """This function writes the database tables to file

        Args:
            fname (str): File name
            databasename (str): Database name
            l (list): List contains the table data
            m (list): List contains the file group data
            n (list): List contains the no.of records in table
            incbackuptype (str): Is "incremental" or "differential" or other
            p (int, Optional): Number we put in the table name so runs don't
                conflict with previous runs of this function.  Default of 1.
            use_same_db_name   (bool): if True doesn't append the numbers at the end of the databasename

        Returns:
            bool: True for Success else False

        """
        log = self.sqlhelper.log
        sqlcon = None

        try:
            fname = os.path.abspath(
                os.path.join(
                    self.sqlhelper.tcobject.log_dir,
                    os.path.basename(os.path.normpath(self.sqlhelper.tcobject.sqlhelper.tcdir)),
                    os.path.basename(fname)
                )
            )

            log.info("Writing the data to file: [{0}]".format(fname))
            filehandle = open(fname, 'w')
            if not self.sqlhelper.azure_sql:
                with global_lock:
                    sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                                   self.sqlhelper.sqlPass, "master", use_pyodbc=True)
            for val1 in l:
                if use_same_db_name:
                    db = databasename
                else:
                    db = databasename + str(val1)
                if not self.sqlhelper.azure_sql:
                    sqlcon.execute("use [{0}]".format(db))
                else:
                    with global_lock:
                        sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                                       self.sqlhelper.sqlPass, db, use_pyodbc=True)
                for val2 in m:
                    for val3 in n:
                        dbn = str("tab") + str(val1) + str(val2) + str(val3)
                        if self.sqlhelper.azure_sql:
                            dbn = str("tab") + str(val1) + str(val3)
                        cur1 = sqlcon.execute("select * from " + str(dbn))
                        for r in cur1.rows:
                            filehandle.write(str(r) + '\n')
            for val1 in l:
                if use_same_db_name:
                    db = databasename
                else:
                    db = databasename + str(val1)
                if not self.sqlhelper.azure_sql:
                    sqlcon.execute("use [{0}]".format(db))
                else:
                    with global_lock:
                        sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                                       self.sqlhelper.sqlPass, db, use_pyodbc=True)
                if not self.sqlhelper.azure_sql:
                    for val3 in n:
                        dbn = str("tabm") + str(val1) + str(val3)
                        cur3 = sqlcon.execute("select * from " + str(dbn))
                        for r in cur3.rows:
                            filehandle.write(str(r) + '\n')

            if incbackuptype == "INCREMENTAL":
                for i in l:
                    if use_same_db_name:
                        db = databasename
                    else:
                        db = databasename + str(i)
                    if not self.sqlhelper.azure_sql:
                        sqlcon.execute("use [{0}]".format(db))
                    else:
                        with global_lock:
                            sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                                           self.sqlhelper.sqlPass, db, use_pyodbc=True)
                    for j in m:
                        cur4 = sqlcon.execute("select * from [tab_inc{0}{1}{2}_ndf]".format(i, j, p))
                        for r in cur4.rows:
                            filehandle.write(str(r) + '\n')
                        cur5 = sqlcon.execute("select * from [tab_inc{0}{1}{2}_mdf]".format(i, j, p))
                        for r in cur5.rows:
                            filehandle.write(str(r) + '\n')

            if incbackuptype == "DIFFERENTIAL":
                for i in l:
                    if use_same_db_name:
                        db = databasename
                    else:
                        db = databasename + str(i)
                    if not self.sqlhelper.azure_sql:
                        sqlcon.execute("use [{0}]".format(db))
                    else:
                        with global_lock:
                            sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                                           self.sqlhelper.sqlPass, db, use_pyodbc=True)
                    for j in m:
                        cur4 = sqlcon.execute("select * from [tab_diff{0}{1}{2}_ndf]".format(i, j, p))
                        for r in cur4.rows:
                            filehandle.write(str(r) + '\n')
                        cur5 = sqlcon.execute("select * from [tab_diff{0}{1}{2}_mdf]".format(i, j, p))
                        for r in cur5.rows:
                            filehandle.write(str(r) + '\n')

            log.info("Successfully wrote data to file [{0}] ".format(fname))
            return True

        except Exception as excp:
            raise Exception("Exception raised in dump_db_to_file()\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def dump_tables_to_file(self, file_name, database_name, tables):
        """This function writes the specified database tables to file

           Args:
               file_name (str): File name
               database_name (str): Database name
               tables (list): The list of tables to write to file

           Returns:
               bool: True for Success else False

        """
        log = self.sqlhelper.log
        sqlcon = None

        try:
            file_name = os.path.abspath(
                os.path.join(
                    self.sqlhelper.tcobject.log_dir,
                    os.path.basename(os.path.normpath(self.sqlhelper.tcobject.sqlhelper.tcdir)),
                    os.path.basename(file_name)
                )
            )

            log.info("Writing the data to file: [{0}]".format(file_name))
            filehandle = open(file_name, 'w')
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True)
                if not self.sqlhelper.azure_sql:
                    sqlcon.execute(f"use [{database_name}]")
                else:
                    with global_lock:
                        sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                                       self.sqlhelper.sqlPass, database_name, use_pyodbc=True)
                for table in tables:
                    if table.startswith('[dbo].'):
                        table = table[7:-1]
                    column_names = []
                    # get list of all columns in the table
                    cur = sqlcon.execute(
                        f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = N'{table}'"
                    )

                    # store these columns in a list
                    for row in cur.rows:
                        column_names.append(row.COLUMN_NAME)

                    # begin building query to order select by all columns
                    if column_names:
                        select_query = f"select * from [{table}] order by "

                        # for each column, cast the column type to avoid types which aren't orderable
                        for column in column_names:
                            select_query += f"cast([{column}] as nvarchar(max)),"
                        select_query = select_query[:-1] + " asc"

                        cur = sqlcon.execute(select_query)
                        for row in cur.rows:
                            filehandle.write(str(row) + '\n')
        except Exception as exp:
            raise Exception("Exception raised in dump_tables_to_file()\nError: '{0}'".format(exp))
        finally:
            if sqlcon is not None:
                filehandle.close()
                sqlcon.close()

    def is_db_online(self, dbname, noofdbs=None, useexistingdb=True):
        """This function checks if the databases are online

        Args:
            dbname (str): Database name
            noofdbs (int, Optional): Number of databases being checked.  Only needed if useexistingdb is True.
            useexistingdb (bool, Optional): If True assume passed in dbname is base name and loop through for noofdbs,
            if False then take the passed in dbname as the actual database name

        Returns:
             bool: True for Success else False

        """
        log = self.sqlhelper.log
        sqlcon = None
        try:
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True)

            # This code block is for a specific provided database name
            if not useexistingdb:
                db = dbname
                query = "SELECT name FROM sys.databases where state_desc='online' and name = '{0}'".format(db)
                cur = sqlcon.execute(query)

                if cur.rows:
                    if cur.rows[0].name == db:
                        log.info("Database [{0}] is ONLINE on [{1}]".format(db, self.sqlhelper.sqlInstance))
                        return True
                    log.error("ERROR - Database [{0}] is NOT ONLINE on [{1}]"
                              .format(db, self.sqlhelper.sqlInstance))
                    return False
                log.error("Database [{0}] is NOT ONLINE on [{1}]".format(db, self.sqlhelper.sqlInstance))
                return False
            # This code block is to iterate through noofdbs and append num to provided database name
            if useexistingdb and noofdbs is not None:
                dbcount = 0
                for d in range(1, noofdbs + 1):
                    db = dbname + str(d)
                    query = "SELECT name FROM sys.databases where state_desc='online' and name = '{0}'".format(db)
                    cur = sqlcon.execute(query)
                    if cur.rows:
                        if cur.rows[0].name == db:
                            log.info("Database [{0}] is ONLINE on [{1}]".format(db, self.sqlhelper.sqlInstance))
                            dbcount += 1
                        else:
                            log.error("ERROR - Database [{0}] is NOT ONLINE on [{1}]"
                                      .format(db, self.sqlhelper.sqlInstance))

                if not dbcount == noofdbs:
                    log.info("Not all databases are ONLINE on [{0}] ".format(self.sqlhelper.sqlInstance))
                    return False
                log.info("All databases are ONLINE on [{0}]".format(self.sqlhelper.sqlInstance))
                return True

            log.error("Provide number of databases to check for base name [{0}] when using useexistingdb flag"
                      .format(dbname))
            return False

        except Exception as excp:
            raise Exception("Exception raised in is_db_online()\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def get_sql_backup_type(self, jobid, multidb=False):
        """This function checks the backup type in CS database based on the specific job id.

        Args:
            jobid (str): Job id of the backup we want to get the level of
            multidb (bool): True if you want to check multiple distinct backup levels

        Returns:
             str: The type of job.  "Full", "Transaction Log" or "Differential"

        """
        log = self.sqlhelper.log

        try:
            log.info("Getting backup type for backup jobid [{0}]".format(jobid))
            query = "select distinct type, is_copy from sqlDbBackupInfo where jobId = '{0}'".format(jobid)
            self.sqlhelper.csdb.execute(query)
            cur = self.sqlhelper.csdb.fetch_all_rows()

            ''' If there are multiple databases in the job and the backup
                level of each database is different then multiple rows will
                be returned from the query.
            '''
            backuptype = None
            copy_only = False
            if not multidb:  # return a single type
                for row in cur:
                    backuptype = str(row[0])
                    copy_only = True if int(row[1]) == 1 else False

                if len(cur) != 1:
                    log.exception("Back up type is more than one : '{0}'".format(str(cur)))

                if backuptype == "D":
                    if copy_only:
                        return "Full(Copy-Only)"
                    return "Full"
                if backuptype == "L":
                    return "Transaction Log"
                if backuptype == "I":
                    return "Differential"
                return str(backuptype)
            # return all of the backup types
            if len(cur) == 1:
                log.info("Back up type is only 1 : " + str(cur))
                return str(cur)
            log.info("Back up type is more than 1: " + str(cur))
            return str(cur)

        except Exception as excp:
            raise Exception("Exception raised in get_sql_backup_type()\nError: '{0}'".format(excp))

    def db_path(self, dbname):
        """This function returns the path of the database files (mdf, ldf, ndf).

        Args:
            dbname (str): Database name

        Returns:
            list: Database file name
            list: Database file path

        """

        sqlcon = None
        try:
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True)

            list1 = []
            list2 = []

            if not self.sqlhelper.azure_sql:
                sqlcon.execute("use [{0}]".format(dbname))
            else:
                with global_lock:
                    sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                                   self.sqlhelper.sqlPass, dbname, use_pyodbc=True)

            cur = sqlcon.execute("select name,filename from sysfiles")
            for row in cur.rows:
                list1.append(row.name)
                list2.append(row.filename)
            return list1, list2

        except Exception as excp:
            raise Exception("Exception raised in db_path()\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def get_access_states(self, dbname, noofdbs):
        """This function returns a list of database access states

        Args:
            dbname (str): Database base name
            noofdbs (int): number of databases being worked on.

        Returns:
            list: database access types for each database

        """
        log = self.sqlhelper.log
        sqlcon = None
        try:
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True)

            accesslist = []
            for d in range(1, noofdbs + 1):
                db = dbname + str(d)
                query = "SELECT name,user_access_desc FROM sys.databases where name = '{0}'".format(db)
                cur = sqlcon.execute(query)
                if cur.rows:
                    if cur.rows[0].name == db:
                        log.info("Database state for database - {0} is {1}".format(db, cur.rows[0].user_access_desc))
                        accesslist.append(cur.rows[0])
                    else:
                        log.error("ERROR - could not determine access state for database: {0}".format(db))
                        raise Exception("could not determine access state for database\nDatabase: '{0}'".format(db))

            return accesslist

        except Exception as excp:
            raise Exception("Exception raised in get_access_states()\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def get_tempdb_create_time(self):
        """This function returns the creation time of the tempdb for the instance

        Returns:
            str: timestamp of the tempdb creation time.  If no timestamp found in master then returns False.

        """
        log = self.sqlhelper.log
        sqlcon = None
        try:
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True)

            query = "SELECT CONVERT(VARCHAR(30),create_date,109) as timestamp from sys.databases where database_id=2"
            cur = sqlcon.execute(query)
            if cur.rows:
                log.info("TEMPDB: " + str(cur.rows[0].timestamp))
                return str(cur.rows[0].timestamp)

            return False

        except Exception as excp:
            raise Exception("Exception raised in get_tempdb_create_time()\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def get_database_tables(self, database_name, table_create_time=False):
        """This function returns a list of table names for the given database

        Args:
            database_name (str): Database name

            table_create_time (bool): If True, function returns creation time of table along with list of tables

        Returns:
            list: List of table names for given database

        """
        sqlcon = None
        try:
            database_table_list = []
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True)

            sqlcon.execute("USE [{0}]".format(database_name))
            if table_create_time:
                query = "SELECT name, create_date FROM sys.tables"
                cur = sqlcon.execute(query)
                return cur.rows

            query = "SELECT name FROM sys.tables order by create_date desc"
            cur = sqlcon.execute(query)
            for row in cur.rows:
                database_table_list.append(row.name)

            return database_table_list
        except Exception as excp:
            raise Exception("Exception raised in get_database_tables()\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def get_database_state(self, database_name):
        """This function returns state of the given database

        Args:
            database_name (str): Database name

        Returns:
            str: State of the database

        """
        sqlcon = None
        try:
            database_state = None
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True)
            query = "SELECT name,state_desc FROM sys.databases where name = '{0}'".format(database_name)
            cur = sqlcon.execute(query)
            if cur.rows:
                database_state = cur.rows[0].state_desc
                self.sqlhelper.log.info("Database [{0}] is in [{1}] state on [{2}]"
                                        .format(database_name, database_state, self.sqlhelper.sqlInstance))
            return str(database_state)

        except Exception as excp:
            raise Exception("Exception raised in get_database_tables()\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def is_db_standby(self, database_name):
        """This function returns whether database is in Standby state

        Args:
            database_name (str): Database name

        Returns:
            bool: True if database is in standby or False if not

        """
        sqlcon = None
        try:
            database_state = None
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True)
            query = "SELECT name, is_in_standby FROM sys.databases where name = '{0}'".format(database_name)
            cur = sqlcon.execute(query)
            if cur.rows:
                database_state = cur.rows[0].is_in_standby
            return True if database_state == 1 else False

        except Exception as excp:
            raise Exception("Exception raised in is_db_standby()\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()


class ModifyDatabase(object):
    """Helper class to perform SQL Server modification operations"""

    global global_lock

    def __init__(self, _sqlautomation):
        """Initializes ModifyDatabase object

        Args:
            _sqlautomation (:obj:'SQLAutomation'): Instance of SQLAutomation

        """
        self.sqlhelper = _sqlautomation

    def modify_db_for_inc(self, dbname, l, m, n, p=1):
        """This function adds additional data to specified databases before log backups

        Args:
            dbname (str): Base database name to modify
            l (list): List contains the table data
            m (list): List contains the file group data
            n (list): List contains the no.of records in table
            p (list, Optional): If calling multiple times in a test case this number needs to be incremented
                                for each call to avoid name conflicts. Default is 1.

        Returns:
            bool: True for success, else False

        """

        sqlcon = None
        try:
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True)

            # TRUNCATE TABLE CODE BLOCK
            sqlcon.execute("BEGIN TRANSACTION")
            for i in l:
                db = dbname + str(i)
                sqlcon.execute("use [{0}] ".format(db))
                for j in m:
                    for k in n:
                        tab1 = "tab" + str(i) + str(j) + str(k)
                        tab2 = "tabm" + str(i) + str(k)
                        sqlcon.execute("truncate table " + tab1)
                        sqlcon.execute("truncate table " + tab2)

            # CREATE TABLE CODE BLOCK

            for i in l:
                db = dbname + str(i)
                sqlcon.execute("use [{0}] ".format(db))
                for j in m:
                    file_group1 = "file_group" + str(i) + str(j)
                    sqlcon.execute("use [{0}]".format(db))
                    sqlcon.execute("create table [tab_inc{0}{1}{2}_ndf](fname nvarchar(15),lname nvarchar(15)) on {3}"
                                   .format(i, j, p, file_group1))
                    sqlcon.execute("create table [tab_inc{0}{1}{2}_mdf](fname nvarchar(15),lname nvarchar(15))"
                                   .format(i, j, p))

            # INSERT CODE BLOCK

            for i in l:
                db = dbname + str(i)
                sqlcon.execute("use [{0}] ".format(db))
                for j in m:
                    sqlcon.execute("insert into [tab_inc{0}{1}{2}_mdf] values(N'inc1',N'commvault1 ')".format(i, j, p))
                    sqlcon.execute("insert into [tab_inc{0}{1}{2}_ndf] values(N'inc2',N'commvault2')".format(i, j, p))

            # UPDATE CODE BLOCK

            for i in l:
                db = dbname + str(i)
                sqlcon.execute("use [{0}] ".format(db))
                for j in m:
                    sqlcon.execute("update [tab_inc{0}{1}{2}_mdf] set fname=N'Incremental1' where fname=N'inc1'"
                                   .format(i, j, p))
                    sqlcon.execute("update [tab_inc{0}{1}{2}_ndf] set lname=N'cvcvcv2' where lname=N'commvault2'"
                                   .format(i, j, p))

            sqlcon.execute("COMMIT TRANSACTION")

            return True

        except Exception as excp:
            raise Exception("Exception raised in modify_db_for_inc()\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def modify_db_for_diff(self, dbname, l, m, n, p=1):
        """This function adds additional data to specified databases before differential backups

        Args:
            dbname (str): Base database name to modify
            l (list): List contains the table data
            m (list): List contains the file group data
            n (list): List contains the number of records in table
            p (list, Optional): If calling multiple times in a test case this number needs to be incremented
                                for each call to avoid name conflicts. Default is 1.
        Returns:
            bool: True for success, else False

        """

        sqlcon = None
        try:
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True)

            # TRUNCATE TABLE CODE BLOCK
            sqlcon.execute("BEGIN TRANSACTION")
            for i in l:
                db = dbname + str(i)
                sqlcon.execute("use [{0}] ".format(db))
                for j in m:
                    for k in n:
                        tab1 = "tab" + str(i) + str(j) + str(k)
                        tab2 = "tabm" + str(i) + str(k)

                        sqlcon.execute("truncate table " + tab1)
                        sqlcon.execute("truncate table " + tab2)

            # CREATE TABLE CODE BLOCK
            for i in l:
                db = dbname + str(i)
                sqlcon.execute("use [{0}] ".format(db))
                for j in m:
                    file_group1 = "file_group" + str(i) + str(j)
                    sqlcon.execute("use [{0}]".format(db))
                    sqlcon.execute("create table [tab_diff{0}{1}{2}_ndf](fname nvarchar(15),lname nvarchar(15)) on {3}"
                                   .format(i, j, p, file_group1))
                    sqlcon.execute("create table [tab_diff{0}{1}{2}_mdf](fname nvarchar(15),lname nvarchar(15))"
                                   .format(i, j, p))

            # INSERT CODE BLOCK

            for i in l:
                db = dbname + str(i)
                sqlcon.execute("use [{0}] ".format(db))
                for j in m:
                    sqlcon.execute(
                        "insert into [tab_diff{0}{1}{2}_mdf] values(N'diff1',N'commvault1')".format(i, j, p)
                    )
                    sqlcon.execute(
                        "insert into [tab_diff{0}{1}{2}_ndf] values(N'diff2',N'commvault2')".format(i, j, p)
                    )

            # UPDATE CODE BLOCK

            for i in l:
                db = dbname + str(i)
                sqlcon.execute("use [{0}] ".format(db))
                for j in m:
                    sqlcon.execute("update [tab_diff{0}{1}{2}_mdf] set fname=N'Differential1' where fname=N'diff1'"
                                   .format(i, j, p))
                    sqlcon.execute("update [tab_diff{0}{1}{2}_ndf] set lname=N'cvcvcv2' where lname=N'commvault2'"
                                   .format(i, j, p))

            sqlcon.execute("COMMIT TRANSACTION")

            return True

        except Exception as excp:
            raise Exception("Exception raised in modify_db_for_diff()\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def create_table(self, database_name, table_name):
        """This function creates a table on a given database

        Args:
            database_name (str): Name of database to create table on
            table_name (str): Name of new table to be created

        """
        sqlcon = None
        try:
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True)

            sqlcon.execute("USE [{0}] ".format(database_name))
            sqlcon.execute("CREATE TABLE [{0}] (fname nvarchar(15),lname nvarchar(15))".format(table_name))
            self.sqlhelper.log.info("Table [{0}] created successfully on database [{1}]".format(table_name,
                                                                                                database_name))

        except Exception as excp:
            raise Exception("Exception raised in create_table()\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()

    def drop_table(self, database_name, table_name):
        """This function drops a table on a given database

        Args:
            database_name (str): Name of database containing table to drop
            table_name (str): Name of table to be dropped

        """
        sqlcon = None
        try:
            with global_lock:
                sqlcon = database_helper.MSSQL(self.sqlhelper.sqlInstance, self.sqlhelper.sqlUser,
                                               self.sqlhelper.sqlPass, "master", use_pyodbc=True)

            sqlcon.execute("USE [{0}] ".format(database_name))
            sqlcon.execute("DROP TABLE [{0}]".format(table_name))
            self.sqlhelper.log.info("Table [{0}] dropped successfully on database [{1}]".format(table_name,
                                                                                                database_name))

        except Exception as excp:
            raise Exception("Exception raised in create_table()\nError: '{0}'".format(excp))
        finally:
            if sqlcon is not None:
                sqlcon.close()
