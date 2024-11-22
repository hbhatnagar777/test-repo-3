#!/usr/bin/env python
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2016 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""SAPOraclehelper file for performing SAP Oracle operations

SAPOraclehelper is the only class defined in this file

SAPOraclehelper: Helper class to perform SAP Oracle operations

SAPOraclehelper:
    __init__()                            --  initializes SAP Oracle helper object

    get_saporacle_db_connectpassword()    --  gets the oracle connect password from cs db

    cleanup_test_data()                   --  cleanups the test data created by automation

    getdatafile()                         --  gets the data file path for creating
                                              tablespaces from database

    create_test_tables()                  --  creates test tablespace and tables
                                              in the database

    GetDatabaseState()                    --  gets the database state from the database

    createStopSqlFile()                   --  creates stop.sql needed for automation
                                                 test cases

    gracefulDBShutDown()                  --  creates shutdown.sql needed for automation
                                              test cases

    test_tables_validation()              --  validates the test tables that were restored
"""
import os
from random import randint
import time
from AutomationUtils import logger, constants
from AutomationUtils import database_helper
#from AutomationUtils.database_helper import SAPOracle
from AutomationUtils import cvhelper
from AutomationUtils import machine


class SAPOraclehelper(object):
    """Helper class to perform SAPOracle operations"""

    def __init__(self, test_case_obj):
        """Initializes SAPOraclehelper object"""

        self.log = logger.get_log()
        self._commcell = test_case_obj.commcell
        self.log.info("commcell name is "+self._commcell)
        self._csdb = database_helper.CommServDatabase(self._commcell)
        self._saporacle_client = test_case_obj.client
        self.log.info("Instance is "+self._saporacle_client)
        self._saporacle_instance = test_case_obj.instance
        self.log.info("saporacle Instance is "+self._saporacle_instance)
        self._connection = None
        self._cursor = None

    @property
    def saporacle_db_connectpassword(self):
        """Gets the sql connect password of the instance"""
        return self._saporacle_db_connectpassword


    def get_saporacle_db_connectpassword(self, saporacle_instanceid):
        """Gets the sql connect password of the instance"""
        try:
            log = logger.get_log()
            query = "Select attrVal from app_instanceprop where componentNameId = {0}\
            and attrName = 'SQL Connect Password'".format(str(saporacle_instanceid))
            log.info("Cs db query for getting sql connect password is "+query)
            self._csdb.execute(query)
            cur = self._csdb.fetch_one_row()
            if cur:
                password = cur[0]
                self._saporacle_db_connectpassword = cvhelper.format_string(self._commcell, password)
                return self._saporacle_db_connectpassword
            else:
                log.info("there is some issue while getting connect password from cs db")
                return None

        except Exception as exp:
            raise Exception("failed to get sqlplus connect password from cs db "+str(exp))

    def cleanup_test_data(self, _saporacle_db_user, _saporacle_db_connectpassword, \
                          _saporacle_db_connectstring, tablespace_name):
        """Cleans up the testdata from the previous cycle"""
        try:
            log = logger.get_log()
            self._db_connect = database_helper.SAPOracle(self._saporacle_db_user,
                                                         self._saporacle_db_connectpassword,
                                                         self._saporacle_db_connectstring)

            query = "select tablespace_name from dba_tablespaces"
            log.info("query running is "+query)
            response = self._db_connect.execute(query)
            log.info("tablespaces names we got is "+str(response))
            tablespaces = response.rows
            if str(tablespaces).find(tablespace_name) >= 0:
                log.info("query running is "+query)
                query = "drop tablespace " + tablespace_name + \
                    " including contents and datafiles"
                response = self._db_connect.execute(query)
                log.info("test data cleaned up sucessfully"+str(response))
                return 0
        except Exception as exp:
            raise Exception("Could not delete the test tables. "+ str(exp))

    def getdatafile(self, _saporacle_db_user, _saporacle_db_connectpassword, \
                    _saporacle_db_connectstring, toCreate):
        """gets the dtafilepath by connecting to oracle database"""
        try:
            log = logger.get_log()
            self._db_connect = database_helper.SAPOracle(self._saporacle_db_user,
                                                         self._saporacle_db_connectpassword,
                                                         self._saporacle_db_connectstring)

            query = "select name from v$datafile"
            log.info(query)
            response = self._db_connect.execute(query)
            row = response.rows
            log.info(row)
            firstrow = row[0]
            firstrow = str(firstrow).lstrip("('")
            log.info(firstrow)
            i = len(firstrow) -1
            log.info(i)
            while i >= 0:
                if firstrow[i] != "/" and firstrow[i] != "\\":
                    DFile = firstrow[0:i]
                    log.info("firstrow we got is"+str(DFile))
                else:
                    break
                i = i-1
                
            if toCreate == None:
                DFile = str(DFile)
                return DFile
            else:
                
                DFile = (str(DFile)+toCreate)
                log.info("Datafile path we got is "+str(DFile))
            return DFile
        except Exception as exp:
            raise Exception("Could not get datafile path. "+ str(exp))

    def create_test_tables(self, _saporacle_db_user, _saporacle_db_connectpassword, \
                           _saporacle_db_connectstring, DFile, tablespace_name, table_name,\
                           flagCreateTableSpace):
        """ Creates the test tablespace,tables in the source database
                Raises:
                    Exception:
                        if not able to create test tables
        """
        try:
            log = logger.get_log()
            self._db_connect = database_helper.SAPOracle(self._saporacle_db_user,
                                                         self._saporacle_db_connectpassword,
                                                         self._saporacle_db_connectstring)

            query = "select tablespace_name from dba_tablespaces"
            log.info("query running is "+query)
            response = self._db_connect.execute(query)
            log.info("tablespaces names we got is "+str(response))
            tablespaces = response.rows
            if str(tablespaces).find(tablespace_name) >= 0:
                log.info("query running is "+query)
                query = "drop tablespace " + tablespace_name + \
                " including contents and datafiles"
                self._db_connect.execute(query)
            log.info("query running is "+query)
            query = "create tablespace " + tablespace_name + " datafile '"+DFile + "' size 10M reuse"
            response = self._db_connect.execute(query)
            log.info(response)
            log.info("query running is "+query)
            query = "select table_name from dba_tables where tablespace_name = '" +tablespace_name +"'"
            response = self._db_connect.execute(query)
            tables = response.rows
            if str(tables).find(table_name) >= 0:
                query = "drop table " +table_name
                log.info(query)
                self._db_connect.execute(query)
            log.info("query running is "+query)
            query = "create table " + table_name + " (name varchar2(30), ID number)" +\
                                                     " tablespace " + tablespace_name

            response = self._db_connect.execute(query)
            log.info("create table response we got is"+str(response))
            for count in range(0, 1000):
                #log.info("query running is "+query)
                query = ("insert into " +table_name + " values('" + table_name+str(count)+ "'," \
                                                               +  str(count) + ")")
                response = self._db_connect.execute(query, commit=True)
            return 0
        except Exception as exp:
            raise Exception("failed to create tablespace and table. "+str(exp))

    def GetDatabaseState(self, _saporacle_db_user, _saporacle_db_connectpassword,\
                         _saporacle_db_connectstring):
        """connect to oracle database and gets the database status"""
        try:
            log = logger.get_log()
            log.info("initializing cursor object")
            (self._db_connect) = database_helper.SAPOracle(self._saporacle_db_user,\
                 self._saporacle_db_connectpassword, self._saporacle_db_connectstring)
            log.info(self._db_connect)

            query = "Select status from v$instance"
            log.info("running query is "+query)
            response = self._db_connect.execute(query)
            log.info("response we got is "+str(response))
            row = response.rows
            log.info(row[0])
            return row[0]
        except Exception as exp:
            raise Exception("failed to get database status. "+str(exp))

    def createStopSqlFile(self):
        """
        creates startup no script for oracle database
        """
        log = logger.get_log()
        try:
            #(CommonDirPath) = SAPOraclehelper.get_CommonDirPath()
            (CommonDirPath) = constants.TEMP_DIR
            log.info(CommonDirPath)
            fp = os.path.join(CommonDirPath, 'stop.sql')
            fp = open('stop.sql', 'w')
            fp.write('startup nomount;\n')
            fp.write('exit;\n')
            fp.close()
            log.info("Created stopsql file successfully")
            return(0, True)
        except Exception as exp:
            raise Exception("failed to createStopSqlFile . "+str(exp))

    def gracefulDBShutDown(self):
        """
        script to shutdown the oracle database
        """
        try:
            log = logger.get_log()
            (CommonDirPath) = constants.TEMP_DIR
            fd = os.path.join(CommonDirPath, 'DBShutDown.sql')
            fd = open('DBShutDown.sql', 'w')
            log.info(fd)
            fd.write('shutdown immediate;\n')
            log.info(fd)
            fd.write('exit;\n')
            fd.close()
            log.info("Created DBShutDown file successfully")
            return(0, True)
        except Exception as exp:
            raise Exception("failed to gracefulDBShutDown . "+str(exp))

    def test_tables_validation(self, _saporacle_db_user, _saporacle_db_connectpassword,
                               _saporacle_db_connectstring, \
                               tablespace_name, table_name):
        """ Validates the test tables that were created before the backup

                Raises:
                    Exception:
                        if the source tables and the restored tables do not match
        """
        try:
            self.table_count = 1000
            log = logger.get_log()
            self._db_connect = database_helper.SAPOracle(self._saporacle_db_user,
                                                         self._saporacle_db_connectpassword,
                                                         self._saporacle_db_connectstring)
            query = "select name from v$tablespace"
            log.info("query running is "+query)
            response = self._db_connect.execute(query)
            log.info("tablespaces names we got is "+str(response))
            tablespaces = response.rows
            if str(tablespaces).find(tablespace_name) >= 0:
                log.info("tablespace name exists.Restore tablespace is sucessfull")
            else:
                log.error("there is some issue with restoring tablespace")

            query = "Select table_name from dba_tables where table_name='{0}'"\
                                                        .format(table_name)
            response = self._db_connect.execute(query, commit=False)
            all_tables = response.rows
            if str(all_tables).find(table_name) >= 0:
                log.info("tablen name exists.Restore table is sucessfull")
            else:
                log.error("there is some issue with restoring table")
            query = "select  * from "+(table_name)+" order by "+(table_name)+".ID ASC"
            log.info(query)
            response = self._db_connect.execute(query)
            row_count_of_tables = response.rows
            log.info(row_count_of_tables)
            log.info(row_count_of_tables[0])
            if len(row_count_of_tables) == 0:
                raise Exception("Could not obtain the row count of all the tables in the schema")
            else:
                log.info(len(row_count_of_tables))
            if len(row_count_of_tables) != self.table_count:
                    raise Exception("The restored table does not contain all the rows")
            else:
                log.info(len(row_count_of_tables))
                return 0

        except Exception as exp:
            raise Exception("Failed to validate the source and restored test tables. " + str(exp))
