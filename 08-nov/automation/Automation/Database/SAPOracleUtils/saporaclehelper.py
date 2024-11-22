# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""SAPOraclehelper file for performing SAP Oracle operations

SAPOracleHelper is the only class defined in this file

SAPOracleHelper: Helper class to perform SAP Oracle operations

SAPOracleHelper:
    __init__()                              --  initializes SAP Oracle helper object

    get_saporacle_db_connect_password()     --  gets the oracle connect password from cs db

    get_saporacle_home                     -- gets the oracle home path

    db_connect()                          --  Connect to Oracle db using cx_Oracle using
                                              SAPOracle class object

    find_tablespace()                       --  Connects to Oracle db and finds the
                                              the specified tablespace exists or not.

    find_tablename()                        --  Connects to Oracle db and finds the
                                              the specified table name exists or not.

    get_database_state()                    --  gets the database state from the database

    drop_tablespace()                       --  Connects to Oracle db and finds the
                                              the specified tablespace exists or not.
                                              if finds drops the tablespace.useful for
                                              validation after restore and also for data
                                              creation while running TC

    get_job_backupsize()                    --  Gets the backup size of the completed job status
                                                from jmbkpstats table totalUncompBytes
                                                is the application size
    get_job_databasephase_backupsize()      --  Gets the backup size of the completed job status
                                              from jmbkatmppstats table totalUncompBytes
                                              is the application size

    switch_logfile()                        --  Creates some archive logs

    get_datafile()                          --  gets the data file path for creating
                                              tablespaces from database

    create_test_tables()                    --  creates test tablespace and tables
                                              in the database
                                              
    get_archive_lsn()                       --  gets the archive log sequence ranges
                                                from the database

    test_tables_validation()              --  validates the test tables that were restored

    touch_files_onclient()                  --  keeps hook files on clients whick are
                                              useful for making job goes to pending
                                              at differemt phases for Sap oracle
                                              
    run_backup()                            -- Runs backup function
    
    run_restart_backup()                    -- suspendes and resumes backup job

    run_pending_backup()                    -- run make job go to pending function

    run_client_service_restart_backup()     -- run client restart function

    run_kill_process_backup()               -- kills client process for running backup job

    run_random_kill_process()               -- randomly kills running client process
    
    run_kill_process_backupcopy()           -- randomly kills client process for backupcopy job
    
    restart_backupcopy()                    -- restarts running backup copy job
    
    run_client_service_restart_backupcopy   -- restarts running backup copy client process

    thirdparty_cmd_backup_job               -- Runs commandline backup job and gets detailfilename

    cmd_execute_validate                    -- Runs commands on the remote machine and do validation

    remote_commands_path                    -- Creates the required directories/files on the remote/controller setup

    db_shutdown                             -- Runs database shutdown command

    rename_datafile                         -- Renames datafile

    db_mount                                -- Runs database mount command

    db_recover_open                         -- Runs database recover and open commands
    
    prepare_sap_cmd                         -- Prepares the sap command based on the os type

    fetch_brtools_log_validation            -- Gets the brtools log file and do brtools validation
    

"""
import time
from AutomationUtils import logger, constants, idautils
from AutomationUtils import database_helper
from AutomationUtils.database_helper import get_csdb
from AutomationUtils import cvhelper
from AutomationUtils.machine import Machine
from AutomationUtils.interruption import Interruption

class SAPOracleHelper(object):
    """Helper class to perform SAPOracle operations"""
    CONN_SYSBACKUP = 'SYSBACKUP'
    CONN_SYSDBA = 'SYSDBA'
    CONN_DB_USER = 'DBUSER'
    SHUT_TRANSACTION = 'TRANSACTIONAL'
    SHUT_FINAL = 'FINAL'
    SHUT_ABORT = 'ABORT'
    SHUT_IMMEDIATE = 'IMMEDIATE'

    def __init__(self, commcell, client, instance):
        """Initializes SAPOraclehelper object
        Args:
            commcell    (obj)   -- commcell object to connect to

            instance    (obj)   -- instance object to connect to

        """
        
        self.log = logger.get_log()
        self.log.info('  Initializing SAPOracle Helper ...')
        self._commcell = commcell
        self._client = client
        self._instance = instance
        self._csdb = get_csdb()
        self._saporacle_client = self._client.client_name
        self.log.info("Client is " + self._saporacle_client)
        self._saporacle_clientid = self._client._get_client_id()
        self.log.info("Client is " + self._saporacle_clientid)
        self._jobresultsdir = self._client.job_results_directory
        self.log.info("Jobresults directlty is "+ self._jobresultsdir)
        self._client_hostname = self._client.client_hostname
        self.log.info("Client hostname  is "+ self._client_hostname)
        self._storage_policy_name1 = self._instance.log_sp
        self._saporacle_db_user = self._instance.saporacle_db_user
        self.log.info("Sap oracle db user name is " + self._saporacle_db_user)
        self._sys_password = None
        self._saporacle_db_connect_string = self._instance.saporacle_db_connectstring
        self.log.info("Sap oracle db connect string  is "+ self._saporacle_db_connect_string)
        self._sap_oracle_home = self._instance.oracle_home
        self.log.info("Sap oracle home  is " + self._sap_oracle_home)
        self._saporacle_instance = self._instance.instance_name
        self.log.info("Sap oracle instancename  is " + (self._saporacle_instance ))
        self._saporacle_instanceid = self._instance.saporacle_instanceid
        self.log.info("Sap oracle instance id  is " + str(self._saporacle_instanceid))
        self.ora_port = 1521
        self._saporadb = None
        self.storage_policy_name = self._commcell.storage_policies.get(self._storage_policy_name1)
        self._saporacle_sapsecurestore = self._instance.saporacle_sapsecurestore
        self._saporacle_osapp_user = self._instance.os_user
        self.log.info("Sap oracle application user name  is " + self._saporacle_osapp_user)
        self._machine_object = Machine(self._saporacle_client,self._commcell)
        self.controller_object = Machine()
        self._ostype = self._machine_object.os_info
        self._simpana_base_path = self._machine_object.get_registry_value(
            "Base", "dBASEHOME")
        self.log.info("commvault base path we got is " + self._simpana_base_path)
        self._saporacle_db_connect_password = self.get_saporacle_db_connect_password()
        self._commvault_instancename = self.get_commvault_instancename()
        self.log.info("Commvault Instance we got is " +str(self._commvault_instancename))
        self._sap_cmd = None

    @property
    def saporacle_db_connect_password(self):
        """Gets the sql connect password of the instance"""
        return self._saporacle_db_connect_password

    def get_saporacle_db_connect_password(self):
        """
        Gets the sql connect password of the instance
        Args:

            saporacle_instanceid   (str)         --  Gets the clientid from SAPOracle instance class
                                                          and passit using Testcase calling
        Raises:
                Exception:

                    if failed to get Oracle db connect password from Commserver database
        """
        
        try:

            query = "Select attrVal from app_instanceprop where componentNameId = {0}\
                and attrName = 'SQL Connect Password'".format(str(self._saporacle_instanceid))
            self.log.info("Cs db query for getting sql connect password is " + query)
            self._csdb.execute(query)
            cur = self._csdb.fetch_one_row()
            if cur:
                password = cur[0]
                self._saporacle_db_connect_password = cvhelper.format_string(self._commcell, \
                                                                            password)
                
                return self._saporacle_db_connect_password
                
            else:
                self.log.info("there is some issue while getting connect password from cs db")
                return None

        except Exception as exp:
            raise Exception("failed to get sqlplus connect password from cs db " + str(exp))

    def get_saporacle_home(self):
        """Gets the sap oracle home path of the instance
        Args:

            saporacle_instanceid   (str)         --  Gets the clientid from SAPOracle instance class
                                                          and passit using Testcase calling
        Raises:
                Exception:

                    if failed to get sap Oracle home path from Commserver database

        """
        try:

            query = "Select attrVal from app_instanceprop where componentNameId = {0}\
            and attrName = 'Oracle Home'".format(self._saporacle_instanceid)
            self.log.info("Cs db query for getting oracle home path is "+query)
            self._csdb.execute(query)
            cur = self._csdb.fetch_one_row()
            if cur:
                password = cur[0]
                self._saporacle_oracle_home = cvhelper.format_string(self._commcell,\
                                                                            password)
                self.log.info("oracle home we got is "+str(self._saporacle_oracle_home))
                return self._getsaporacle_home
                
            else:
                self.log.info("there is some issue while getting oracle home from cs db")
                return None

        except Exception as exp:
            raise Exception("failed to get oracle home from cs db "+str(exp))  

    def db_connect(self, mode=CONN_SYSDBA):
        """TODO: Doc String for db_connect"""
        self.log.info("Getting db connection object")
        self._saporadb = database_helper.SAPOracle(self._saporacle_db_user,\
                                         self._saporacle_db_connect_password, \
                                            self._saporacle_db_connect_string, \
                                       self._client_hostname, self.ora_port, mode=mode)
       
        self.log.info("Oracle connection object is" + str(self._saporadb))

    def find_tablespace(self, tablespace):
        """connects to oracledb and finds the tablespaces
        Args:

            tablespace   (str)         --  Specify tablespace name
                                             and passit using Testcase calling
        Raises:
                Exception:

                    Failed to find tablespace\nError
        """
        try:
            query = "select tablespace_name from dba_tablespaces"
            self.log.info("query running is "+query)
            response = self._saporadb.execute(query)
            self.log.info("tablespaces names we got is " + str(response.rows))
            tablespaces = response.rows
            if str(tablespaces).find(tablespace) >= 0:
                self.log.info("tablespace name exists: {0} tablespace ".\
                              format(tablespace))
                return 0
            else:
                return 1
        except Exception as excp:
            raise Exception('Failed to find tablespace\nError: {0}'.format(excp))

    def find_tablename(self, tablename):
        """connects to oracledb and finds the table name
         Args:

            tablename   (str)         --  Specify tablename and
                                            passit using Testcase calling
        Raises:
                Exception:

                    Failed to find tablename\nError
        """
        try:
            query = "Select table_name from dba_tables where table_name='{0}'"\
                                                        .format(tablename)
            self.log.info("query running is "+query)
            response = self._saporadb.execute(query)
            self.log.info("table names we got is "+ str(response.rows))
            tablespaces = response.rows
            if str(tablespaces).find(tablename) >= 0:
                self.log.info("table name exists: {0} tablename ".\
                              format(tablename))
                return 0
            else:
                return 1
        except Exception as excp:
            raise Exception('Failed to find tablename\nError: {0}'.format(excp))

    def get_database_state(self):
        """connects to oracledb and gets the database status

        """
        try:
            query = "Select status from v$instance"
            self.log.info("query running is "+query)
            response = self._saporadb.execute(query)
            self.log.info("response we got is "+str(response.rows))
            row = response.rows
            self.log.info("Db status we got is " + str(row[0][0]))
            return str(row[0][0])
        except Exception as excp:
            raise Exception("failed to get database status: {0} ".format(excp))

    def drop_tablespace(self, tablespace):
        """connects to oracledb and finds the tablespaces.
        if the tablespace specified exists drops the tablespace
        Args:

            tablespace   (str)         --  Specify tablespace name
                                             and passit using Testcase calling
        Raises:
                Exception:

                    Failed to drop tablespace\nError
        """
        try:
            status = self.find_tablespace(tablespace)
            if status == 0:
                self.log.info("tablespace exists we are going to drop tablespace ")
                query = "drop tablespace " + tablespace + \
                " including contents and datafiles"
                self.log.info("query running is "+query)
                response = self._saporadb.execute(query)
                return 0
            else:
                return 1

        except Exception as excp:
            raise Exception('Failed to drop tablespace\nError: {0}'.format(excp))


    def get_job_backupsize(self, jobid):
        """Gets the backup size of the completed job status
        from jmbkpstats table totalUncompBytes is the application size
        Args:

            jobid        (str)         --  Gets the jobid from job class
                                             and pass it using Testcase calling
        Raises:
                Exception:

                    if failed to get currentphase of the running job from Commserver database

        """
        try:
            query = "select sum(UncompBytes)/1024/1024  from JMBkpAtmptStats \
            where jobid={0} and phase=4".format(str(jobid))
            self.log.info("Cs db query for getting application size job is "+query)
            self._csdb.execute(query)
            cur = self._csdb.fetch_one_row()
            if cur:
                self.log.info("App size we got is " + cur[0])
                return cur[0]
            else:
                self.log.info("there is some issue while getting application size from cs db")
                return None

        except Exception as exp:
            raise Exception("failed to get currentphase of the running job from cs db " + str(exp))

    def get_job_databasephase_backupsize(self, jobid):
        """Gets the backup size of the completed job status
        from jmbkpstats table totalUncompBytes is the application size
        Args:

            jobid        (str)         --  Gets the jobid from job class
                                             and pass it using Testcase calling
        Raises:
                Exception:

                    if failed to get currentphase of the running job from Commserver database
        """
        try:
            query = "select sum(UncompBytes)/1024/1024  from JMBkpAtmptStats where jobid={0}\
            and phase=4 and status=1".format(str(jobid))
            self.log.info("Cs db query for getting application size for \
            database backup phase "+query)
            self._csdb.execute(query)
            cur = self._csdb.fetch_one_row()
            if cur:
                self.log.info("App size we got is" + cur[0])
                return cur[0]
            else:
                self.log.info("there is some issue while getting application size from cs db")
                return None

        except Exception as exp:
            raise Exception("failed to get for database backup phase job from cs db " + str(exp))

    def switch_logfile(self, lognumber):
        """Creates some archivelogs before backup.
        Args:

            lognumber(int)             -- Specify the number of logs to be created in
                                                          TC calling

        Raises:
                Exception:

                    if Could not delete the test tables
        """
        try:

            self.log.info("##generating archive logs starts here##")
            for count in range(0, int(lognumber)):
                query = ("alter system switch logfile")
                self.log.info("Command we are running is " + query)
                response = self._saporadb.execute(query)
                self.log.info("switch log file is sucessfull")
            return 0
        except Exception as exp:
            raise Exception("Could not delete the test tables. " + str(exp))

    def get_datafile(self, tocreate):
        """gets the dtafilepath by connecting to oracle database
        Args:

            tocreate               (str)            --  pass the tablespace Name.
                                                       If none datafile is not created

        Raises:
                Exception:

                    if failed to get datafile path
        """
        try:
            query = "select name from v$datafile"
            self.log.info(query)
            response = self._saporadb.execute(query)
            row = response.rows
            firstrow = row[0]
            firstrow = str(firstrow).lstrip("('")
            i = len(firstrow) -1
            while i >= 0:
                if firstrow[i] != "/" and firstrow[i] != "\\":
                    dbfile = firstrow[0:i]
                    self.log.info("firstrow we got is: {0} dbfile ".format(str(dbfile)))
                else:
                    break
                i = i-1

            if tocreate == None:
                dbfile = str(dbfile)
                return dbfile
            else:

                dbfile = (str(dbfile)+tocreate)
                self.log.info("Datafile path we got is:  {0} dbfile ".format(str(dbfile)))
            return dbfile
        except Exception as exp:
            raise Exception("Could not get datafile path: {0} dbfile ".format(str(exp)))

    def create_test_tables(self, dbfile, tablespace, tablename, flagcreatetableSpace):
        """ Creates the test tablespace,tables in the source database
        Args:

            dbfile                        (str)     -- Specify the Datafile path we got from
                                                         getdatafile function

            flagcreatetableSpace        (bool)    -- Takes True or False.
                                                        if True Tablespace will be created
                                                        if False Tablespace will not be created

        Raises:
                Exception:

                    if not able to create test tables

        """
        try:
            status = self.find_tablespace(tablespace)
            if status == 0:
                self.log.info("Tablespace name exists..so dropping tablespace")
                status = self.drop_tablespace(tablespace)
            query = "create tablespace " + tablespace + " datafile '"+\
            dbfile + "' size 10M reuse"
            self.log.info("query running is "+query)
            response = self._saporadb.execute(query)
            self.log.info("create tablespace response we got is " + str(response.rows))
            status = self.find_tablename(tablename)
            
            query = "create table " + tablename + " (name varchar2(30), ID number)" +\
                                                     " tablespace " + tablespace
            self.log.info("query running is "+query)
            response = self._saporadb.execute(query)
            self.log.info("create table response we got is "+ str(response.rows))
            for count in range(0, 1000):
                #log.info("query running is "+query)
                query = ("insert into " +tablename + " values('" + tablename+str(count)+ "'," \
                                                               +  str(count) + ")")
                response = self._saporadb.execute(query, commit=True)
            return 0
        except Exception as exp:
            raise Exception("failed to create tablespace and table: {0} exp ".format(str(exp)))
            

    def get_archive_lsn(self):
        """
    	This function -actually- gets the Log sequence number from the database
    	"""
        try:
            query = ("select TO_CHAR(SEQUENCE#) from (select SEQUENCE# from v$archived_log where  SEQUENCE# > 0 \
                     order by first_time desc) where rownum = 1")
            self.log.info("Query we are running is " + query)
            response = self._saporadb.execute(query)
            row = response.rows
            row1 = str(row[0]).rstrip("',)")
            row1 = row1.lstrip("('")
            self.log.info("archive lsn we got is " + str(row1))
            return str(row1)
        except Exception as exp:
            raise Exception("failed to Log sequence number from the database: {0} exp ".format(str(exp)))

    

    def test_tables_validation(self, tablespace, tablename):
        """ Validates the test tables that were created before the backup

        Args:
            tablespace_name         (str)     -- Tablespace name to be created specified in
                                                          TC calling

            tablename               (str)     -- Table name to be created specified in
                                                          TC calling
        Raises:
                Exception:

                    if Failed to validate the source and restored test tables
        """
        try:
            self.table_count = 1000
            status = self.find_tablespace(tablespace)
            if status == 0:
                self.log.info("tablespace name exists. Restore tablespace is sucessfull")
            else:
                self.log.error("there is some issue with restoring tablespace")
            status = self.find_tablename(tablename)
            if status == 0:
                self.log.info("tablen name exists. Restore table is sucessfull")
            else:
                self.log.error("there is some issue with restoring table")
            query = "select  * from "+ (tablename) + " order by " + (tablename) + ".ID ASC"
            self.log.info("Query response is " + query)
            response = self._saporadb.execute(query)
            row_count_of_tables = response.rows
            self.log.info("Table count response is " + str(row_count_of_tables))
            if len(row_count_of_tables) == 0:
                raise Exception("Could not obtain the row count of all the tables in the schema")
            else:
                self.log.info("Query response is " + str(row_count_of_tables))
            if len(row_count_of_tables) != self.table_count:
                raise Exception("The restored table does not contain all the rows")
            else:
                self.log.info("Row count response is " +str(row_count_of_tables))
                return 0

        except Exception as exp:
            raise Exception("Failed to validate the source and restored test tables: {0} exp ".\
                            format(str(exp)))

    def get_archfile_isvalid(self, jobid, filetype):
        """Gets the archfile is valid from Cs db
        Args:

            jobid       (str)           --  Gets the job id from jobclass
                                            pass it using TC calling

            filetype     (str)          --  Based on the archive type verifies
                                            cs db whether file is marked invalid or not
                                            Filetype 1 means data
                                            filetype 4 means log

        Raises:
                Exception:

                    if Failed to run query from cs db
        """

        try:
            query = "Select isvalid from archfile where jobid="+(str(jobid))+" \
            and isvalid=-1 and filetype="+filetype+""
            self.log.info("Cs db query for getting archivefile "+query)
            self._csdb.execute("Query response is " + query)
            cur = self._csdb.fetch_all_rows()
            if cur:
                cur1 = str(cur[0])
                self.log.info(cur1)
                if str(cur1) >= '-1':
                    self.log.info("Archive files are invalidated for the restarted job")
                    return 0
                else:
                    return -1
        except Exception as exp:
            raise Exception("failed to run query from cs db: {0} exp ".format(str(exp)))
            
    def run_backup(self, subclient, backup_type):
        """Starts backup job
        Args:

             subclient(str)     -- Specify the subclient object name where backups
                                             needs to be run
            backup_type(str)    --  specify the backup type needs to be run
                                   ex:FULL or INCREMENTAL
        Raises:
                Exception:

                    if failed to run backup

        """

        self.log.info("*" * 10 + " Starting Subclient {0} Backup "\
                 .format(backup_type) + "*" * 10)
        job = subclient.backup(backup_type)
        self.log.info("Started {0} backup with Job ID: {1}".\
                 format(backup_type, str(job.job_id)))

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}"\
                               .format(backup_type, job.delay_reason))
        self.log.info("Successfully finished {0} backup job".format(backup_type))
        return job
    
    def run_restart_backup(self, subclient, backup_type):
        """Starts backup job
         Args:

             subclient(str)     -- Specify the subclient object name where backups
                                             needs to be run
            backup_type(str)    --  specify the backup type needs to be run
                                   ex:FULL or INCREMENTAL
        Raises:
                Exception:

                    if failed to run backup
        """

        self.log.info("*" * 10 + " Starting Subclient {0} Backup "\
                 .format(backup_type) + "*" * 10)
        job = subclient.backup(backup_type)
        self.log.info("Started {0} backup with Job ID: {1}".\
                 format(backup_type, str(job.job_id)))
        self.interruption = Interruption(job.job_id, self._commcell)
        self.interruption.suspend_resume_job()
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}"\
                               .format(backup_type, job.delay_reason))
        self.log.info("Successfully finished {0} backup job".format(backup_type))
        return job
    
    def run_pending_backup(self, subclient, backup_type, machine, pathname,\
                           pathname1, pathname2, pathname3):
        """Starts backup job
         Args:

             subclient(str)     -- Specify the subclient object name where backups
                                             needs to be run
            backup_type(str)    --  specify the backup type needs to be run
                                   ex:FULL or INCREMENTAL
            machine(str)        -- specify the machine object
            pathname(str)      -- specify the name of saphookfile
            pathname1(str)      -- specify the name of saphookfile
            pathname2(str)      -- specify the name of saphookfile
            pathname3(str)      -- specify the name of saphookfile

        Raises:
                Exception:

                    if failed to run backup
        """

        self.log.info("*" * 10 + " Starting Subclient {0} Backup "\
                 .format(backup_type) + "*" * 10)
        job = subclient.backup(backup_type)
        self.log.info("Started {0} backup with Job ID: {1}".\
                 format(backup_type, str(job.job_id)))
        jobid = job.job_id
        job_status_flag = 1
        while job_status_flag:
            time.sleep(60)
            self.log.info("Job Status:%s", job.status)
            if(job.status.lower() == "pending" or
               "completed" in job.status.lower()):
                job_status_flag = 0
                if job.status.lower() == "pending":
                    self.log.info("Status of  {0} backup with Job ID: {1}")
                    machine.remove_directory(pathname)
                    self.log.info("hookfile failSAPDataBackupB4Intimate are deleted sucessfully")

        self.log.info(job.resume(True))
        self.log.info(job._wait_for_status("Running"))
        if job.status == "Running":
            recode = self.getarchfileisvalid(str(jobid), '1')
            if recode == 0:
                self.log.info("archivefiles are invalidated sucessfully in Cs db for restarted job")
        job_status_flag = 1
        while job_status_flag:
            time.sleep(60)
            self.log.info("Job Status:%s", job.status)
            if(job.status.lower() == "pending" or
               "completed" in job.status.lower()):
                job_status_flag = 0
                if job.status.lower() == "pending":
                    self.log.info("Status of  {0} backup with Job ID: {1}")
                    machine.remove_directory(pathname1)
                    self.log.info("hookfile failSAPDataConfigBackupB4Intimate are deleted sucessfully")

        self.log.info(job.resume(True))
        self.log.info(job._wait_for_status("Running"))
        self.log.info(job._wait_for_status("Running"))
        if job.status == "Running":
            recode = self.getarchfileisvalid(str(jobid), '1')
            if recode == 0:
                self.log.info("archivefiles are invalidated sucessfully in Cs db for restarted job")
        job_status_flag = 1
        while job_status_flag:
            time.sleep(60)
            self.log.info("Job Status:%s", job.status)
            if(job.status.lower() == "pending" or
               "completed" in job.status.lower()):
                job_status_flag = 0
                if job.status.lower() == "pending":
                    self.log.info("Status of  {0} backup with Job ID: {1}")
                    machine.remove_directory(pathname2)
                    self.log.info("hookfile failSAPLogBackupB4Intimate are deleted sucessfully")
        self.log.info(job.resume(True))
        self.log.info(job._wait_for_status("Running"))
        if job.status == "Running":
            recode = self.getarchfileisvalid(str(jobid), '4')
            if recode != '0':
                self.log.info("archivefiles are not invalidated sucessfully\
                in Cs db for restarted job")
        job_status_flag = 1
        while job_status_flag:
            time.sleep(60)
            self.log.info("Job Status:%s", job.status)
            if(job.status.lower() == "pending" or
               "completed" in job.status.lower()):
                job_status_flag = 0
                if job.status.lower() == "pending":
                    self.log.info("Status of  {0} backup with Job ID: {1}")
                    machine.remove_directory(pathname3)
                    self.log.info("hookfile failSAPLogConfigBackupB4Intimate are deleted sucessfully")
        self.log.info(job.resume(True))
        self.log.info(job._wait_for_status("Running"))
        if job.status == "Running":
            recode = self.getarchfileisvalid(str(jobid), '4')
            if recode != '0':
                self.log.info("archivefiles are not invalidated sucessfully\
                in Cs db for restarted job")

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}"\
                               .format(backup_type, job.delay_reason))
        self.log.info("Successfully finished {0} backup job".format(backup_type))
        return job
    
    def run_client_service_restart_backup(self, subclient, backup_type):
        """Starts backup job
         Args:

             subclient(str)         -- Specify the subclient object name where backups
                                             needs to be run
            backup_type(str)        --  specify the backup type needs to be run
                                       ex:FULL or INCREMENTAL
        Raises:
                Exception:

                    if failed to run backup
        """

        self.log.info("*" * 10 + " Starting Subclient {0} Backup "\
                 .format(backup_type) + "*" * 10)
        job = subclient.backup(backup_type)
        self.log.info("Started {0} backup with Job ID: {1}".\
                 format(backup_type, str(job.job_id)))
        self.interruption = Interruption(job.job_id, self._commcell)
        self.interruption.restart_client_services()
        self.interruption.wait_and_resume()

        self.log.info(job._wait_for_status("running"))
        if not job.wait_for_completion():
            raise Exception
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}"\
                               .format(backup_type, job.delay_reason))
        self.log.info("Successfully finished {0} backup job".format(backup_type))
        return job

    def run_kill_process_backup(self, subclient, backup_type, machine):
        """Starts backup job
         Args:

             subclient(str)         -- Specify the subclient object name where backups
                                             needs to be run
            backup_type(str)        --  specify the backup type needs to be run
                                       ex:FULL or INCREMENTAL

            machine(str)            -- specify the machine object

        Raises:
                Exception:

                    if failed to run backup
        """

        self.log.info("*" * 10 + " Starting Subclient {0} Backup "\
                 .format(backup_type) + "*" * 10)
        job = subclient.backup(backup_type)
        self.log.info("Started {0} backup with Job ID: {1}".\
                 format(backup_type, str(job.job_id)))
        time.sleep(40)
        self.log.info(job._wait_for_status("running"))
        machine.kill_process('ClSapAgent')
        self.log.info("ClSapAgent process is killed sucessfully")
        time.sleep(40)
        self.log.info(job.status)
        if job.status == "Pending":
            self.log.info("Status of  {0} backup with Job ID: {1}".\
                     format(backup_type, str(job.job_id)))
            self.log.info(job.resume(True))
            self.log.info(job._wait_for_status("Running"))
            if job.status == "Running":
                self.log.info("Status of  {0} backup with Job ID: {1}")

        self.log.info(job._wait_for_status("running"))
        if not job.wait_for_completion():
            raise Exception
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}"\
                               .format(backup_type, job.delay_reason))
        self.log.info("Successfully finished {0} backup job".format(backup_type))
        return job

    def run_random_kill_process(self, subclient, backup_type):
        """Starts backup job
         Args:

             subclient(str)         -- Specify the subclient object name where backups
                                             needs to be run
            backup_type(str)        --  specify the backup type needs to be run
                                       ex:FULL or INCREMENTAL

        Raises:
                Exception:

                    if failed to run backup
        """

        self.log.info("*" * 10 + " Starting Subclient {0} Backup "\
                 .format(backup_type) + "*" * 10)
        job = subclient.backup(backup_type)
        self.log.info("Started {0} backup with Job ID: {1}".\
                 format(backup_type, str(job.job_id)))
        time.sleep(30)
        self.interruption = Interruption(job.job_id, self._commcell)
        self.interruption.random_process_kill()
        self.interruption.wait_and_resume()

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}"\
                               .format(backup_type, job.delay_reason))
        self.log.info("Successfully finished {0} backup job".format(backup_type))
        return job
    
    def run_kill_process_backupcopy(self, subclient, snap_job_id):
        """Starts backup job
         Args:

           subclient(str)        -- specify the subclient name
                                       ex:default

           snap_job_id(int)      -- specify the snap backup jobid

        Raises:
                Exception:

                    if failed to run backup
        """

        self.log.info("*" * 10 + " Starting backup copy ""*" * 10)
        job = self.storage_policy_name.run_backup_copy()
        self.log.info("Backup copy workflow job id is : {0}".\
                 format(str(job.job_id)))
        time.sleep(30)
        backupcopyjob = idautils.get_backup_copy_job_id(self._commcell, subclient, snap_job_id)
        self.log.info(backupcopyjob)
        self.interruption = Interruption(job.job_id, self._commcell)
        self.interruption.random_process_kill()
        self.interruption.wait_and_resume()
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}"\
                               .format(str(job.job_id)), job.delay_reason)
        self.log.info("Successfully finished  backupcopy job {0} ".format(str(job.job_id)))
        return backupcopyjob

    def restart_backupcopy(self, subclient, snap_job_id):
        """Starts backup copy workflow job and gets the backupcopy job
         Args:

            subclient(str)        -- specify the subclient name
                                       ex:default

            snap_job_id(int)      -- specify the snap backup jobid

        Raises:
                Exception:

                    if failed to run backup copy job
        """

        self.log.info("*" * 10 + " Starting backup copy ""*" * 10)
        job = self.storage_policy_name.run_backup_copy()
        self.log.info("Backup copy workflow job id is : {0}".\
                 format(str(job.job_id)))
        time.sleep(30)
        backupcopyjob = idautils.get_backup_copy_job_id(self._commcell, subclient, snap_job_id)
        self.log.info(backupcopyjob)
        self.interruption = Interruption(backupcopyjob, self._commcell)
        self.interruption.suspend_resume_job()

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}"\
                               .format(str(job.job_id)), job.delay_reason)
        self.log.info("Successfully finished  backupcopy job {0} ".format(str(job.job_id)))
        return backupcopyjob

    def run_client_service_restart_backupcopy(self, subclient, snap_job_id):
        """Starts backup job
         Args:

            subclient(str)        -- specify the subclient name
                                       ex:default

            snap_job_id(int)      -- specify the snap backup jobid
        Raises:
                Exception:

                    if failed to run backupcopy
        """

        self.log.info("*" * 10 + " Starting Subclient {0} Backupcopy " "*" * 10)
        job = self.storage_policy_name.run_backup_copy()
        self.log.info("Started backup with Job ID: {0}".\
                 format(str(job.job_id)))
        time.sleep(30)
        backupcopyjob = idautils.get_backup_copy_job_id(self._commcell, subclient, snap_job_id)
        self.log.info(backupcopyjob)
        self.interruption = Interruption(backupcopyjob, self._commcell)
        self.interruption.restart_client_services()
        self.interruption.wait_and_resume()
        self.log.info(job._wait_for_status("running"))
        if not job.wait_for_completion():
            raise Exception
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}"\
                               .format(str(job.job_id)), job.delay_reason)
        self.log.info("Successfully finished  backupcopy job {0} ".format(str(job.job_id)))
        return backupcopyjob

    def thirdparty_cmd_backup_job(self, sap_cmd, temp_input_file_name, search_cmd):
        """Method to run cmd jobs on remote machine

            Args:
                sap_cmd                     (str)   --  rman command to be
                                                    executed on remote client


                temp_input_file_name    (str)   --  temporary input file to be created
                                                    on controller and copied to remote machine

                search_cmd               (str)  --  command to validate

            Returns:
                object type  -   object of output class for given command

            Raises:
                Exception:




                    If unable to copy file to remote machine
        """
        try:
            self._local_filename, remote_path = self.remote_commands_path(temp_input_file_name)
            self.log.info("Local file path we got is " + self._local_filename)
            file_path = open(self._local_filename, 'w', newline='\n')
            file_path.write('numstreams\n')
            file_path.write('2\n')
            file_path.write('CvClientName\n')
            file_path.write(self._saporacle_client + '\n')
            file_path.write('CvInstanceName\n')
            file_path.write(str(self._commvault_instancename) + '\n')
            file_path.write('SelectiveOnlineFull\n')
            file_path.write('1\n')
            file_path.close()

            self.log.info("File created and command is successfully written")
            copy_status = self._machine_object.copy_from_local(
                self._local_filename, remote_path)
            self.log.info("copy_status :%s", copy_status)
            if copy_status is False:
                raise Exception("Failed to copy file to remote machine.Exiting")
            remote_file = self._machine_object.join_path(remote_path,
                                                         temp_input_file_name)

            if self._machine_object.os_info == 'UNIX':
                cmd = ("chmod 777 " +remote_file)
                self._machine_object.execute(cmd)
                newsap_cmd = sap_cmd + ' -r ' + remote_file + '"'
                self.log.info("Sap command we are running is " +newsap_cmd)
                br_job = "False"
            else:
                br_job = "True"
                newsap_cmd = 'cmd.exe /c '+sap_cmd+' > c:\\temp\sapcmd.out"'
                self.log.info(newsap_cmd)
            sap_detail_file = self.cmd_execute_validate(newsap_cmd, search_cmd, detail_file=True, br_job=br_job)
            if sap_detail_file == None:
                self.log.error ("Some issue with getting detailfile " + str(sap_detail_file))
            else:
                self.log.info("SAP detailfile we got is " + str(sap_detail_file))
                return str(sap_detail_file)

        except Exception as excp:
            raise Exception(
            "Exception raised at thirdparty_command_backup_job: '{0}'".format(excp))

    def cmd_execute_validate(self, sap_cmd, search_cmd, detail_file=False, br_job=False):
        """Method to execute validate sap cmd jobs

            Args:

                search_cmd               (str)  -- user provided string will be validated

                sap_cmd                  (str)  -- command needs to be run

                detail_file              (bool) -- if true will get detailfilename

                br_job                   (bool) -- if true will pass the localfile name
                                            different for windows cmd jobs

            Returns:
                object type  -   object of output class for given command

            Raises:
                Exception:
                    If unable to copy file to remote machine
        """
        try:
            cmd_output = self._machine_object.execute_command(sap_cmd)
            self.log.info("Output of db shutdown script: %s",
                          cmd_output.formatted_output)
            from itertools import chain

            flat_list = list(chain.from_iterable(cmd_output.formatted_output))
            soutput = ' '.join(flat_list)

            self.log.info("Output of dboperations script 2: %s",
                          soutput)
            if br_job == True:
                self._local_filename = "c:\\temp\sapcmd.out"

            file_path = open(self._local_filename, 'w', newline='\n')
            file_path.write(soutput)
            file_path.close()

            fp = open(self._local_filename, 'r')
            i = 0
            search_pattern = []
            for ln in fp.readlines():
                if ln.find(search_cmd) >= 0:
                    search_pattern = ln
                    self.log.info("cmd job ran fine")
                    if detail_file == True:
                            if ln.find('End of database backup: ' or 'End of file restore: ') >= 0:
                                detail_file = ln
                                detail_file = detail_file.split(":")
                                detail_file = detail_file[1].split(" 202")
                                detail_file = detail_file[0]
                                self.log.info(
                                    "detailfile we got for third party command line brbackup job is " + str(detail_file))
                                return str(detail_file)

            self.log.info("Some issue with running cmd job")
            fp.close()
            self.log.info("Cleanup temp file on controller machine")
            return 0
        except Exception as excp:
            raise Exception(
            "Exception raised at cmd_execute_validate method: '{0}'".format(excp))

    def remote_commands_path(self, temp_input_file_name):
        """Method to create temporary directory on the remote machine

                        Args:
                            temp_input_file_name    (str)   --  temporary input file to be created
                                                                on controller and copied to remote machine

                        Returns:
                            object type  -   object of output class for given command

                        Raises:
                            Exception:
                                If unable to copy file to remote machine
        """
        try:
            temp_folder_name = "SAPOracleTemp"
            if self._machine_object.os_info == 'UNIX':
                self.log.info("Os type we got is " + self._ostype)
                cv_client_temp_path = self._machine_object.join_path(self._simpana_base_path, "Temp")
                remote_path = self._machine_object.join_path(cv_client_temp_path, temp_folder_name)
                self.log.info("Remote path we got on unix os is " + remote_path)
            else:
                self.log.info("Os type we got is " + self._ostype)
                remote_path = self._machine_object.join_path("c:\\temp", temp_folder_name)
            self._machine_object.clear_folder_content(temp_folder_name)
            self._machine_object.create_directory(remote_path, force_create=True)
            common_dir_path = self.controller_object.join_path(constants.TEMP_DIR, temp_folder_name)
            self.controller_object.clear_folder_content(temp_folder_name)
            self.controller_object.create_directory(common_dir_path, force_create=True)
            self._local_filename = self.controller_object.join_path(common_dir_path, temp_input_file_name)
            self.log.info("Local file  path we got on the setup is " + self._local_filename)
            return self._local_filename, remote_path

        except Exception as excp:
            raise Exception(
            "Exception raised at remote_commands_path method: '{0}'".format(excp))

    def db_shutdown(self, sap_cmd=None, temp_input_file_name="dbshutdown.sql"):
            """Method to run db shutdown commands on remote machine

                Args:
                    sap_cmd                     (str)   --  sql command to be
                                                        executed on remote client


                    temp_input_file_name    (str)   --  temporary input file to be created
                                                        on controller and copied to remote machine

                Returns:
                    object type  -   object of output class for given command

                Raises:
                    Exception:
                        If unable to copy file to remote machine
            """
            try:
                self._local_filename, remote_path = self.remote_commands_path(temp_input_file_name)
                self.log.info("Local file path we got is " + self._local_filename)
                file_path = open(self._local_filename, 'w', newline='\n')
                file_path.write('shutdown immediate;\n')
                file_path.write('exit;')
                file_path.close()
                self.log.info("File created and command is successfully written")
                copy_status = self._machine_object.copy_from_local(
                    self._local_filename, remote_path)
                self.log.info("copy_status :%s", copy_status)
                if copy_status is False:
                    raise Exception("Failed to copy file to remote machine.Exiting")
                remote_file = self._machine_object.join_path(remote_path,
                                                             temp_input_file_name)
                if sap_cmd is None:
                    self.prepare_sap_cmd()
                    sap_cmd = self._sap_cmd

                if self._machine_object.os_info == 'UNIX':
                    shut_cmd = sap_cmd + ' @' + remote_file + '"'
                else:
                    shut_cmd = 'cmd.exe /c ' + sap_cmd + ' @' + remote_file + '"'
                retCode = self.cmd_execute_validate( shut_cmd, 'ORACLE instance shut down.')
                if retCode == 0:
                    self.log.info("Db shutdown command executed correctly")
            except Exception as excp:
                raise Exception(
                    "Exception raised at db_shutdown: '{0}'".format(excp))
            
    def rename_datafile(self, db_file_path):
            """Method to rename datafiles before restore to be
               executed on remote machine

                Args:
                    db_file_path                     (str)   --  datafile path to rename

                Returns:
                    object type  -   object of output class for given command

                Raises:
                    Exception:
                        If unable to copy file to remote machine
            """
            try:

                if self._machine_object.os_info == 'UNIX':
                    newsap_cmd = 'mv ' + db_file_path + ' '+ db_file_path + '.org'
                    self.log.info("Command running is " + newsap_cmd)
                else:
                    newsap_cmd = 'cmd.exe /c rename' + db_file_path + ' ' + db_file_path + '.org'
                    self.log.info("Command running is " + newsap_cmd)
                cmd_output = self._machine_object.execute_command(newsap_cmd)
                self.log.info("Output of rename datafile script: %s",
                              cmd_output.formatted_output)
            except Exception as excp:
                raise Exception(
                    "Exception raised at rename_datafile: '{0}'".format(excp))

    def db_recover_open(self, sap_cmd, temp_input_file_name):
            """Method to run recover db commands on remote machine
                Args:
                    sap_cmd                     (str)   --  sql command to be
                                                        executed on remote client


                    temp_input_file_name    (str)   --  temporary input file to be created
                                                        on controller and copied to remote machine

                Returns:
                    object type  -   object of output class for given command

                Raises:
                    Exception:
                        If unable to copy file to remote machine
            """
            try:
                self._local_filename, remote_path = self.remote_commands_path(temp_input_file_name)
                self.log.info("Local file path we got is " + self._local_filename)
                file_path = open(self._local_filename, 'w', newline='\n')
                file_path.write('recover database;\n')
                file_path.write('alter database open;\n')
                file_path.write('exit;')
                file_path.close()
                self.log.info("File created and command is successfully written")
                copy_status = self._machine_object.copy_from_local(
                    self._local_filename, remote_path)
                self.log.info("copy_status :%s", copy_status)
                if copy_status is False:
                    raise Exception("Failed to copy file to remote machine.Exiting")
                remote_file = self._machine_object.join_path(remote_path,
                                                             temp_input_file_name)
                if self._machine_object.os_info == 'UNIX':
                    recover_cmd = sap_cmd + ' @' + remote_file + '"'
                else:
                    recover_cmd = 'cmd.exe /c ' + sap_cmd + ' @' + remote_file + '"'
                retCode = self.cmd_execute_validate(recover_cmd, 'Database opened: ')
                if retCode == 0:
                    self.log.info("Db recovered and open command executed correctly")
            except Exception as excp:
                raise Exception(
                    "Exception raised at db_recover_open: '{0}'".format(excp))

    def db_mount(self, sap_cmd, temp_input_file_name):
            """Method to database before restore
               and execute the same on remote machine

                Args:
                    sap_cmd                     (str)   --  sql command to be
                                                        executed on remote client


                    temp_input_file_name    (str)   --  temporary input file to be created
                                                        on controller and copied to remote machine

                Returns:
                    object type  -   object of output class for given command

                Raises:
                    Exception:




                        If unable to copy file to remote machine
            """
            try:

                self._local_filename, remote_path = self.remote_commands_path(temp_input_file_name)
                self.log.info("Local file path we got is " + self._local_filename)
                file_path = open(self._local_filename, 'w', newline='\n')
                file_path.write('startup mount;\n')
                file_path.write('exit;')
                file_path.close()
                self.log.info("File created and command is successfully written")
                copy_status = self._machine_object.copy_from_local(
                    self._local_filename, remote_path)
                self.log.info("copy_status :%s", copy_status)
                if copy_status is False:
                    raise Exception("Failed to copy file to remote machine.Exiting")
                remote_file = self._machine_object.join_path(remote_path,
                                                             temp_input_file_name)
                if self._machine_object.os_info == 'UNIX':
                    mount_cmd = sap_cmd + ' @' + remote_file + '"'
                else:
                    mount_cmd = 'cmd.exe /c ' + sap_cmd + ' @' + remote_file + '"'
                retCode = self.cmd_execute_validate(mount_cmd, 'Database mounted: ')
                if retCode == 0:
                    self.log.info("Db mount command executed correctly")
            except Exception as excp:
                raise Exception(
                    "Exception raised at db_mount: '{0}'".format(excp))

    def get_commvault_instancename(self):
        """
        Gets the commvault instance name from cs db
        """
        try:
            query = ("select APP_ClientProp.attrVal from APP_ClientProp "
				    "where APP_ClientProp.componentNameId = (select APP_Client.id from APP_Client "
				    "where APP_Client.name ='"+ self._saporacle_client+"' and APP_ClientProp.attrName = 'Galaxy Instance name')")
            self.log.info(query)
            self._csdb.execute(query)
            cur = self._csdb.fetch_one_row()
            self.log.info("Cs db instance number we got is " + str(cur))

            if str(cur):
                instance = str(cur).rstrip("']")
                self._commvault_instancename = instance.lstrip("['")
                self.log.info("Commvault instance name we got from from cs db is " + (self._commvault_instancename))
                return (self._commvault_instancename)
            else:
                raise Exception("Failed to get the commvault instance name from cs db")

        except Exception as excp:
                raise Exception(
                    "Exception raised at getting commvault instancename: '{0}'".format(excp))

    def prepare_sap_cmd(self):
        """ method to shutdown database

                    Returns:
                        returns return code

                    Raises:
                        Exception:
                                if unable to shutdown database

        """
        self.log.info("##DB shutdown #")
        if self._machine_object.os_info == 'UNIX':
            self.log.info("Os type we got is "+self._machine_object.os_info)
            self._sap_cmd = r'su - ' + self._saporacle_osapp_user + ' -c "sqlplus ' + \
                          self._saporacle_db_user + '/' + self._saporacle_db_connect_password + \
                          '@' + self._saporacle_db_connect_string + ' as sysdba '
        else:
            self.log.info("Os type we got is "+self._machine_object.os_info)
            self._sap_cmd = '"sqlplus ' + self._saporacle_db_user + \
                          '/' + self._saporacle_db_connect_password + '@' + \
                          self._saporacle_db_connect_string + ' as sysdba '

    def fetch_brtools_log_validation(self, job_id,  job_type, srchPattern):
        """
        Fetches brtools log for given Job ID from sap oracle client

            Args:
                job_id          (int)       --  job ID for which RMAN to be fetched

                job_type       (object)     --  specify job type as backup or restore

                srchPattern     (str)       --  pattern string to be searched in brtoolslog

            Returns:

                (int)                       --  returns 0 0r error code

            Raises:
                Exception

                    if search pattern is not found in brtools log file
        """
        try:
            if job_type.lower() in ["backup", "snap backup", "snap to tape"]:
                file_name = "backup.out"
            else:
                file_name = "restore.out"
            default_job_path = self._machine_object.join_path("CV_JobResults", "2", "0")
            common_path = self._machine_object.join_path(default_job_path, job_id)

            if self._machine_object.os_info == 'UNIX':
                command = ("sed -n \"/%s/p\" %s") % (srchPattern, (self._machine_object.join_path(self._jobresultsdir,
                                                                                        common_path, file_name)))
                self.log.info("Command running on unix is "+ command)
            else:
                command = ("(Select-String -Path \"%s\" -Pattern \"%s\")") % \
                          (self._machine_object.join_path(self._jobresultsdir, common_path, file_name), srchPattern)
                self.log.info("Command running is:%s",command)
            output = self._machine_object.execute_command(command).formatted_output
            self.log.info("Output of brtools log script: %s",output)
            if output != '':
                self.log.info("Output of brtools log script correct is: %s",output)
                return 0
            return 1

        except Exception as excp:
                raise Exception(
                    "Exception raised at getting brtoolslog and validation".format(excp))
        
