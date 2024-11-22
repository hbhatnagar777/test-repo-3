# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing sap hana operations

HANAHelper is the only class defined in this file

HANAHelper: Helper class to perform sap hana operations

HANAHelper:
    __init__()                      --  initializes sap hana helper object

    backup_prefix()                 --  sets the back up prefix to be used during backup

    _get_db_connection              --  HANA DB connections

    get_hana_server_details()       --  gets the SAP HANA server details like the hostname of the
                                            HANA server, port

    hana_backup()                   --  runs the sap hana backup with the given backup type

    hana_restore()                  --  runs the given SAP HANA restore

    cleanup_test_data()             --  cleans up the test data created during automation

    get_metadata()                  --  method to collect database information like tables and rows count

    create_test_tables()            --  creates test tables in the schema of the database user provided

    validate_db_info()              --  validates the data on source and destination DB

    test_tables_validation()        --  validates the test tables that were restored

    run_hdbsql_command()            --  run backup and restore operation from hdbsql comamnd line
"""

import datetime
import time
from random import randint
from pytz import timezone
from AutomationUtils import cvhelper, logger, database_helper, machine
from AutomationUtils.database_helper import SAPHANA


class HANAHelper:
    """Helper class to perform sap hana operations"""

    def __init__(self, testcase=None, commcell=None, client_name=None, instance_name=None, backupset_name=None,
                 subclient_name=None):
        """
        Initializes hanahelper object

        Args:
            testcase    (object):   Object of the testcase class to get all the details
                default = None
            commcell    (object):   Object of the commcell
                default = None
            Client_name (str):      HANA client name
                default = None
            instance_name (str):    HANA instance name
                default = None
            backupset_name (str):   Hana backup set name
                default = None
            subclient_name (str):   HANA subclient name

        """
        if testcase:
            self.log = testcase.log
            self.commcell = testcase.commcell
            self.csdb = testcase.csdb
            self.hana_client = testcase.client.client_name
            self.hana_instance = testcase.instance
            self.hana_subclient = testcase.subclient
        else:
            self.log = logger.get_log()
            self.commcell = commcell
            self.csdb = database_helper.get_csdb()
            self.hana_client = client_name
            self.client = commcell.clients.get(client_name)
            self.hana_instance = self.client.agents.get('SAP HANA').instances.get(instance_name)
            self.hana_subclient = self.hana_instance.backupsets.get(backupset_name).subclients.get(subclient_name)

        self.hana_backupset = self.hana_subclient._backupset_object
        if self.hana_backupset:
            self.backupset_name = self.hana_backupset.backupset_name
        else:
            self.backupset_name = "default"

        self.hana_server = self.hana_instance.db_instance_client['clientName']
        self.hana_server_hostname = None
        self._hana_port = None
        self._hana_tenant_port = None
        self._hana_db_user_name = self.hana_instance.instance_db_username
        self._hana_os_sap_user = None
        self._hana_db_password = None
        self._hdbsql_path = None
        self._total_tables = 5
        self._total_rows = 5
        self._table_number = 1
        self._test_data = "SAP HANA test automation:SAP HANA test automation:SAP HANA test \
        automation:SAP HANA test automation:SAP HANA test automation:SAP HANA test automation:\
        SAP HANA test automation:SAP HANA test automation: SAP HANA test automation:"

        self._connection = None
        self._cursor = None
        self._backup_prefix = None
        self.last_backup_backint = None
        self._job_start = None
        self.get_hana_server_details()
        self._db_connect = None

        self.restore_data_prefix = None
        self.incremental_job_time = None

        self.cleanup_test_data()
        self.cleanup_test_data(tenant_connection=True)

    @property
    def backup_prefix(self):
        """ getter for the backup prefix
		    Returns:
			    (str)	:	Returns backup prefix
		"""
        return self._backup_prefix

    @backup_prefix.setter
    def backup_prefix(self, value):
        """ Setter for the backup prefix
	        Args:
			    value	(str)	: backup prefix of job
		"""
        self._backup_prefix = str(value)

    def _get_db_connection(self, tenant_connection=False):
        """ method to get the database connection

            Args:
                tenant_connection  (boolean) : HANA DB connection, True will connect to tenant DB,
                                                                        False will connect to SYSTEMDB'
                    default : False

        """
        port = self._hana_port
        if tenant_connection:
            port = self._hana_tenant_port
        self._db_connect = SAPHANA(
            self.hana_server_hostname,
            port,
            self._hana_db_user_name,
            self._hana_db_password)

    def get_hana_server_details(self):
        """ Gets the SAP HANA server details like hostname, password and port

        Raises:
            Exception:
                if the hostname of the HANA server could not be obtained or
                if the password for the HANA instance could not be obtained or
                if there is an issue with getting the port
        """
        try:
            # Gets the SAP HANA server client's hostname
            query = f"select net_hostname from App_Client where id ={self.hana_instance.db_instance_client['clientId']}"
            self.csdb.execute(query)
            cur = self.csdb.fetch_one_row()
            if cur:
                self.hana_server_hostname = cur[0]
            else:
                raise Exception("Failed to get the HANA server host name from database")

            # Gets the password of the SAP HANA server
            query = f"Select attrVal from app_instanceprop where componentNameId = {self.hana_instance.instance_id} and \
                        attrName = 'DB User Password'"

            self.csdb.execute(query)
            cur = self.csdb.fetch_one_row()
            if cur:
                password = cur[0]
                self._hana_db_password = cvhelper.format_string(self.commcell, password)
            else:
                raise Exception("Failed to get the HANA client name from database")

            # Gets the port number to connect to the SAP HANA server
            instance_id = self.hana_instance.instance_number
            self._hana_port = int(f"3{instance_id}13")
            self._hana_tenant_port = int(f"3{instance_id}15")

            # Gets the hdbsql path of the SAP HANA server
            query = f"Select attrVal from app_instanceprop where componentNameId = {self.hana_instance.instance_id} and \
                                    attrName = 'HDB SQL Location Directory'"

            self.csdb.execute(query)
            cur = self.csdb.fetch_one_row()
            if cur:
                self._hdbsql_path = cur[0]
            else:
                raise Exception("Failed to get the hdsql path from database")

        except Exception as exp:
            raise Exception(str(exp)) from exp

    def hana_backup(self, backup_type):
        """
        Submits a SAP HANA backup for the subclient with the given backup type

        Args:
            backup_type (str):  the type of backup to be submitted

        Raises:
            Exception:
                if there is an error while submitting SAP HANA backup

        """
        try:
            self.log.info(" Starting Subclient %s Backup ", backup_type)
            backup_job = self.hana_subclient.backup(backup_type, self.backup_prefix)
            self.log.info("Started %s backup with Job ID: %s", backup_type, backup_job.job_id)
            if not backup_job.wait_for_completion():
                raise Exception(
                    f"Failed to run {backup_type} backup job with error: {backup_job.delay_reason}"
                    )
            if backup_type.lower() == "full":
                if self.backup_prefix:
                    self.restore_data_prefix = "f{backup_job.job_id}_{self.backup_prefix}"
                else:
                    self.restore_data_prefix = f"{backup_job.job_id}_COMPLETE_DATA_BACKUP"
            elif backup_type.lower() == "incremental":
                self.incremental_job_time = str(backup_job.end_time)
                self.log.info("Incremental End time -- %s", self.incremental_job_time)
                time_stamp = datetime.datetime.strptime(self.incremental_job_time,
                                                        '%Y-%m-%d %H:%M:%S')
                time_stamp = time_stamp.replace(tzinfo=timezone('UTC'))
                time_stamp = str(int(time_stamp.timestamp()))
                self.log.info("Incremental timestamp -- %s", time_stamp)
                self.incremental_job_time = time_stamp
        except Exception as exp:
            raise Exception(f"Exception occurred while trying to run hana backup. {str(exp)}") from exp

    def hana_restore(self, point_in_time=False, data_only=False):
        """
        Submits a SAP HANA restore of the given type

        Args:
            point_in_time   (bool): if the restore has to be point in time
				default: False

            data_only       (bool): if the restore has to be recover data only
				default: False

        Raises:
            Exception:
                if there is an error while submitting a restore

        """
        try:
            self.log.info("***** Starting Subclient Restore *****")
            if all([point_in_time, data_only]):
                raise Exception("Both point in time and data only restores are selected "
                                "for a single restore")

            if not point_in_time and not data_only:
                self.log.info("Starting a current time restore")
                restore_job = self.hana_instance.restore(pseudo_client=self.hana_client.lower(),
                                                         instance=self.hana_instance.instance_name,
                                                         backupset_name=self.backupset_name,
                                                         ignore_delta_backups=False,
                                                         check_access=True)
                self.log.info("Current time restore job started. Job ID is %s", restore_job.job_id)
                if not restore_job.wait_for_completion():
                    raise Exception("Failed to run current time restore job with error: " + str(
                        restore_job.delay_reason))

                self.test_tables_validation()
            elif point_in_time:
                restore_job = self.hana_instance.restore(pseudo_client=self.hana_client.lower(),
                                                         instance=self.hana_instance.instance_name,
                                                         backupset_name=self.backupset_name,
                                                         point_in_time=self.incremental_job_time,
                                                         check_access=True,
                                                         ignore_delta_backups=False)
                self.log.info("Point in time restore job started. Job ID is %s",
                              restore_job.job_id)
                if not restore_job.wait_for_completion():
                    raise Exception("Failed to run point in time restore job with error: " + str(
                        restore_job.delay_reason))

                self.test_tables_validation(point_in_time=True)
            elif data_only:
                self.log.info("Starting a recover data only restore")
                restore_job = self.hana_instance.restore(pseudo_client=self.hana_client.lower(),
                                                         instance=self.hana_instance.instance_name,
                                                         backupset_name=self.backupset_name,
                                                         backup_prefix=self.restore_data_prefix,
                                                         check_access=True)
                self.log.info("Recover data only restore job started. Job ID is %s",
                              restore_job.job_id)
                if not restore_job.wait_for_completion():
                    raise Exception("Failed to run recover data only restore job with "
                                    "error: " + str(restore_job.delay_reason))

                self.test_tables_validation(recover_data=True)
            self.log.info("Successfully validated restored content")
        except Exception as exp:
            raise Exception(f"Sap Hana restore or validation failed. {str(exp)}") from exp

    def cleanup_test_data(self, tenant_connection=False):
        """
        Cleans up the testdata from the previous cycle

        Args:
            tenant_connection    (boolean) : boolean value to specify tenant db connection. True will connect
                                                            to tenant DB, False will connect to SYSTEMDB
                default = False


        Raises:
            Exception:
                if the testdata could not be cleaned up properly
                or if connection could not be established to the HANA client

        """
        try:
            self._get_db_connection(tenant_connection=tenant_connection)

            query = f"Select TABLE_NAME from Tables where SCHEMA_NAME='{self._hana_db_user_name}' and TABLE_NAME like\
            'AUTOMATIONTABLE%'"
            response = self._db_connect.execute(query, commit=False)

            all_tables = response.rows

            if all_tables:
                for table in all_tables:
                    query = f"Drop table {self._hana_db_user_name}.{str(table[0])} CASCADE;"
                    self._db_connect.execute(query)
        except Exception as exp:
            raise Exception("Could not delete the test tables " + str(exp)) from exp

    def get_meta_data(self, _tenant_connection=False):
        """
        Get the list of tables & rows available in the Database

        Args:
                _tenant_connection    (boolean) : boolean value to specify tenant db connection. True will connect
                                                            to tenant DB, False will connect to SYSTEMDB
                        default = False
            Returns:
                Dict (dict) : Tables and Rows in Database
                    example : {'AUTOMATIONTABLE_1631194539_0': 5, 'AUTOMATIONTABLE_1631194539_1': 5}
            Raises:
                Exception:
                if unable to get table & rows in db
        """
        meta_data = {}
        try:

            self._get_db_connection(tenant_connection=_tenant_connection)

            query = f"SELECT TABLE_NAME FROM SYS.M_TABLES WHERE SCHEMA_NAME='{self._hana_db_user_name}'"
            list_tables = self._db_connect.execute(query, commit=False)
            list_tables = [element[0] for element in list_tables.rows]

            for table in list_tables:
                query_1 = f"select count(*) from system.{table}"
                row_count = self._db_connect.execute(query_1, commit=False).rows[0][0]
                meta_data[table] = row_count

            return meta_data

        except Exception as exp:
            raise Exception(f"Exception {str(exp)} in get_meta_data") from exp

    def create_test_tables(self, table_count=5, tenant_connection=False, backup_type="FULL"):
        """
        Creates the test tables in the source database

        Args:
            table_count (int) : no. of tables need to create
                default = 5
            tenant_connection  (boolean) : boolean value to specify tenant db connection. True will connect
                                                            to tenant DB, False will connect to SYSTEMDB
                default = False
            backup_type  (str) : Pre-fix of table name for each backup_type
                example : For FULL backup table name like "AUTOMATIONTABLE_1631194539_0"
                          For INCR backup table name like "AUTOMATIONTABLE_INCR_1631194539_0"
                          For DIFF backup table sname like "AUTOMATIONTABLE_DIFF_1631194539_0"
                default = "FULL"

        Raises:
            Exception:
                if not able to create test tables
        """
        try:
            self._get_db_connection(tenant_connection=tenant_connection)

            time_stamp = int(time.time())
            for table_num in range(0, table_count):
                if backup_type == "FULL":
                    table_name = f"AutomationTable_{time_stamp}_{table_num}"
                elif backup_type == "INCR":
                    table_name = f"AutomationTable_INC_{time_stamp}_{table_num}"
                elif backup_type == "DIFF":
                    table_name = f"AutomationTable_DIFF_{time_stamp}_{table_num}"

                query = f"create table {self._hana_db_user_name}.{table_name} (Id int,String1 varchar(256)," \
                        f"String2 varchar(256),String3 \
                            varchar(256),String4 varchar(256),String5 varchar(256),String6 varchar(256),String7 \
                            varchar(256),String8 varchar(256),String9 varchar(256),String10 varchar(256)); \
                            "
                self._db_connect.execute(query)

                query = f"Insert into {self._hana_db_user_name}.{table_name} values('1','{self._test_data}'," \
                        f"'{self._test_data}','{self._test_data}','{self._test_data}','{self._test_data}'," \
                        f"'{self._test_data}','{self._test_data}','{self._test_data}','{self._test_data}'," \
                        f"'{self._test_data}');"
                self._db_connect.execute(query)

                for row in range(2, self._total_rows + 1):
                    query = f"Insert into {self._hana_db_user_name}.{table_name} " \
                            f"(Id,String1,String2,String3,String4,String5,\
                     String6,String7,String8,String9,String10) select {str(row)},String1,String2,String3,\
                     String4,String5,String6,String7,String8,String9,String10 from " \
                            f"{self._hana_db_user_name}.{table_name} where Id=1"
                    self._db_connect.execute(query)
                self._table_number += 1

        except Exception as exp:
            raise Exception(str(exp)) from exp

    def validate_db_info(self, db_map_1, db_map_2):
        """
        Takes two metadata Information Maps and verifies if both have same info

              Args:
                  db_map_1        (dict)  : Metadata before restore
                  db_map_2        (dict)  : Metadata after restore

             Raises:
                Exception:
                   if validation fails
        """
        self.log.info("## Validating the tables and rows information after restore ##")
        if db_map_1 != db_map_2:
            raise Exception(
                "#### Database validation failed!! ####"
            )
        self.log.info("#### All the Tables and rows restored correctly Database validation PASS..!! ####")

    def test_tables_validation(self, point_in_time=False, recover_data=False):
        """
        Validates the test tables that were created before the backup

        Args:
            point_in_time   (boolean):  True / False based on the restore job to be
                                        validated is Point In Time Restore or not

                default:    False

            recover_data    (boolean):  True / False based on the restore job to be
                                        validated is Recover Data only restore or not

                default:    False

        Raises:
			Exception:
				if database connection fails
				if not table is restored by the job
                if the number of source tables and the restored tables do not match
                if the number of table is greater than the number of source table
				if we are unable to get row count for a table
				if the row count doesn't match
				if the values in table doesn't match
				if restore validation fails

        """
        try:
            try:
                self._db_connect = SAPHANA(self.hana_server_hostname,
                                           self._hana_port,
                                           self._hana_db_user_name,
                                           self._hana_db_password)
            except Exception:
                self._hana_port = f"3{self.hana_instance.instance_number}13"
                self._db_connect = SAPHANA(self.hana_server_hostname,
                                           self._hana_port,
                                           self._hana_db_user_name,
                                           self._hana_db_password)

            query = f"Select TABLE_NAME from TABLES where SCHEMA_NAME='{self._hana_db_user_name}'"
            response = self._db_connect.execute(query, commit=False)

            all_tables = response.rows
            if not all_tables:
                raise Exception("There are no restored tables in the restored database.")

            restored_tables = []
            for table in all_tables:
                restored_tables.append(str(table[0]))

            if point_in_time:
                source_table_count = (self._total_tables/3)*2
            else:
                if recover_data:
                    source_table_count = self._total_tables / 3
                else:
                    source_table_count = self._total_tables
            print(source_table_count)

            restored_table_count = 0
            prefixed_tables = []
            restored_table_number = []
            for table_name in restored_tables:
                if "AUTOMATIONTABLE" in table_name:
                    restored_table_count += 1
                    prefixed_tables.append(table_name)
                    restored_table_number.append(int(table_name.split("AUTOMATIONTABLE")
                                                     [-1].strip()))

            if not restored_table_count == source_table_count:
                raise Exception("The number of restored tables does not match the number of "
                                "source tables.")

            if any(table_number > source_table_count for table_number in restored_table_number):
                raise Exception("The restored table names do not match with the source"
                                "table names")

            query = f"SELECT \"RECORD_COUNT\" FROM \"SYS\".\"M_TABLES\" WHERE SCHEMA_NAME='{self._hana_db_user_name}';\
            "
            response = self._db_connect.execute(query, commit=False)

            row_count_of_tables = response.rows
            if not row_count_of_tables:
                raise Exception("Could not obtain the row count of all the tables in the schema")

            for each_tables_row in row_count_of_tables:
                if int(each_tables_row[0]) != self._total_rows:
                    raise Exception("The restored table does not contain all the rows")

            random_table_number = [randint(1, (self._total_tables/3)+1) for table in range(0, 6)]
            random_rows = [randint(1, (self._total_rows/3)+1) for rows in range(0, 5)]
            for table in random_table_number:
                query = f"Select String3 from {self._hana_db_user_name}.{'AUTOMATIONTABLE'+str(table)} " \
                        f"where id in {tuple(random_rows)}"
                response = self._db_connect.execute(query, commit=False)
                table_values = response.rows
                for values in table_values:
                    if str(values[0]) != self._test_data:
                        raise Exception("Test data does not match the cell in the table")

        except Exception as exp:
            raise Exception("Failed to validate the source and restored test tables " + exp) from exp

    def run_hdbsql_command(self, operation, database, source_database=None, backup_type='full', pit=None,
                           destination_database=None, using_backint=None):
        """
        Method to run hdbsql commands
        Args:
            operation (str) : operation to run (backup/restore)
            database (str)  : database to run operation on
            source_database (str)  : name of source database (in case of restore operation)
            backup_type (str)  : backup type (full/diff/inc) [default - full]
            pit (str) : to set point in time for restores [format - %Y-%m-%d %H:%M:%S]
            destination_database (str) : destination database for restore operation
            using_backint (str) : backint value for restore opeation
        """
        command = ''
        conn = (f'su - {self.hana_instance.instance_name}adm -c '
                f'"/{self._hdbsql_path}/hdbsql -i {self.hana_instance.instance_number} -d SYSTEMDB '
                f'-u {self._hana_db_user_name} -p \'{self._hana_db_password}\' ')
        if operation == 'backup':
            backup_op = ''
            if backup_type == 'incr':
                backup_op = 'INCREMENTAL '
            elif backup_type == 'diff':
                backup_op = 'DIFFERENTIAL '
            backint = f"'{database}_AUTOMATION_{backup_type.upper()}_{datetime.datetime.now()}'"
            command = conn + (f'\\\"backup data {backup_op}for {database} using backint '
                              f'({backint})\\\"')
            self.log.info(f"Running command {command}")
            self.last_backup_backint = backint
            self.log.info(f"backup with backint {backint}")
        elif operation == 'restore':
            if using_backint is not None:
                command = conn + (f'RECOVER DATA FOR {destination_database} USING SOURCE {database}@{source_database} '
                                  f'USING BACKING {using_backint} CLEAR LOG \\\" --wait --timeout=600')
            else:
                if not pit:
                    pit = datetime.datetime.now()
                command = conn + (f'\\\"RECOVER DATABASE FOR {destination_database} UNTIL '
                                  f"'{pit}' CLEAR LOG USING SOURCE {database}@{source_database} "
                                  f'CHECK ACCESS\\\" --wait --timeout=600"')
            self.log.info(f"Running command {command}")

        client_name = self.client.client_name.replace(f"_{source_database}", '')
        self.log.info(f'creating machine object for client {client_name}')
        machine_object = machine.Machine(self.commcell.clients.get(client_name), self.commcell)
        self._job_start = int(time.time())
        machine_object.execute_command(command)

