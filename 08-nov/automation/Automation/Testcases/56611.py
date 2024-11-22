
""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""

from time import sleep
import datetime
import random
from AutomationUtils import constants
from AutomationUtils.config import ConfigReader
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from AutomationUtils.constants import SnapShotEngineNames
from Application.SQL.sqlhelper import SQLHelper


class TestCase(CVTestCase):
    """Class for executing SNAP Recovery points and table level restores"""

    def __init__(self):
        """Initializes test case class objects"""
        super(TestCase, self).__init__()
        self.name = "SQL: Basic Acceptance - SNAP Recovery points and table level restores"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.MSSQL
        self.show_to_user = False
        self.sqldump_file1 = "restored_tables.txt"
        self.sqldump_file2 = "source_tables.txt"
        self.csdb_helper = None
        self.commserv_sql_user = None
        self.commserv_sql_password = None
        self.commserv_instance_name = None
        self.sqlhelper = None
        self.subclient = None
        self.basedbname = None
        self.db_name = None
        self.tcinputs = {
            "LibraryName": None,
            "MediaAgentName": None,
            "SnapEngineName": None,
            "SQLServerUser": None,
            "SQLServerPassword": None,
            "DirectoryPathOnLUN": None
        }

    def setup(self):
        """Setup function for the testcase

        Initializes database connections"""

        self.log.info("Initializing connection with CSDB")
        config = ConfigReader().get_config()
        self.commserv_sql_user = config.SQL.CS_Username
        self.commserv_sql_password = config.SQL.CS_Password
        self.commserv_instance_name = config.SQL.CS_InstanceName
        self.csdb_helper = MSSQL(
            self.commserv_instance_name,
            self.commserv_sql_user,
            self.commserv_sql_password,
            "CommServ",
            use_pyodbc=True
        )
        self.sqlhelper = SQLHelper(
            self,
            self.client.client_name,
            self.instance.instance_name,
            self.tcinputs['SQLServerUser'],
            self.tcinputs['SQLServerPassword']
        )

    def run(self):
        """Main function of this test case execution"""
        try:
            self.sqlhelper.sql_setup(
                noof_dbs=1,
                noof_tables_ffg=5,
                library_name=self.tcinputs['LibraryName'],
                media_agent=self.tcinputs['MediaAgentName'],
                db_path=self.tcinputs['DirectoryPathOnLUN'],
                snap_setup=True)

            self.basedbname = self.sqlhelper.dbname
            self.subclient = self.sqlhelper.subclient

            if not SnapShotEngineNames(self.tcinputs["SnapEngineName"]):
                self.log.info("Snap Engine Name [{0}] is invalid. Please enter correct Snap Engine Name"
                              .format(self.tcinputs["SnapEngineName"]))

            self.log.info('Enabling Intelli-Snap for the created subclient %s', self.subclient.name)
            self.subclient.enable_intelli_snap(self.tcinputs["SnapEngineName"])

            self.sqlhelper.dbinit.set_database_autoclose_property(self.basedbname+'1', "off")
            backup_jobid = self.sqlhelper.sql_backup('FULL')

            # check backup level for full backup job
            backuplevel = self.sqlhelper.dbvalidate.get_sql_backup_type(backup_jobid)
            if str(backuplevel) != "Full":
                raise Exception("Wrong backup level of the database detected in the job")
            else:
                self.log.info("Backup level confirmed: %s", str(backuplevel))

            db_list = []  # Stores the list of databases created by sql_setup()
            for i in range(1, self.sqlhelper.noof_dbs + 1):
                db_list.append(self.basedbname + str(i))

            # A db is selected at random to submit for recovery point creation
            self.db_name = random.choice(db_list)
            rp_id, rp_name = self.sqlhelper.sql_create_recovery_point(self.db_name, snap_setup=True)

            # Setting the expire time as 4 minutes
            expire_in = 4
            expire_time = datetime.datetime.now() + datetime.timedelta(minutes=expire_in)
            expire_time = int(datetime.datetime.timestamp(expire_time))
            self.sqlhelper.set_recovery_point_expire_time(
                rp_id,
                self.csdb_helper,
                expire_time)
            self.log.info('Updated the expiry time to %s minutes from now for RP id %s',
                          expire_in, rp_id)

            # Checking if the database created by recovery point is accessible
            if self.sqlhelper.dbinit.check_database(rp_name):
                self.log.info("Database created by recovery point is accessible")
            else:
                raise Exception(f"Database {rp_name} created by RP {rp_id} is not accessible")

            # Verify database is added to Do Not Backup subclient.
            dnb_subclient = self.sqlhelper.do_not_backup_subclient
            if rp_name in dnb_subclient.content:
                self.log.info('%s database found in DNB subclient.', rp_name)
            else:
                raise Exception(f"{rp_name} not found in DNB subclient")

            tables = []  # Stores the list of tables of the source db used for RP creation

            result = self.sqlhelper.dbvalidate.get_database_tables(self.db_name, True)
            for row in result:
                tables.append('[dbo].[' + row[0] + ']')

            tables_to_restore = random.sample(tables, random.randrange(1, len(tables)))

            # Starting table level restore
            self.log.info('Starting table level restore of tables %s', tables_to_restore)
            dest_db, restored_tables = self.sqlhelper.sql_table_level_restore(
                self.db_name,
                tables_to_restore,
                rp_name,
            )
            self.log.info('Restore of tables %s to db %s completed', restored_tables, dest_db)

            self.sqlhelper.dbvalidate.dump_tables_to_file(
                self.sqldump_file1,
                dest_db,
                restored_tables)

            self.sqlhelper.dbvalidate.dump_tables_to_file(
                self.sqldump_file2,
                self.db_name,
                tables_to_restore)

            if self.sqlhelper.dbvalidate.db_compare(self.sqldump_file1, self.sqldump_file2):
                self.log.info('Validation success')
            else:
                raise Exception("Validation of source tables and restored tables failed")

            # setting duration of sleep to 10 minutes
            sleep_time = 10
            self.log.info("Waiting until expiration time is met. Resume execution in %s minutes", sleep_time)
            sleep(sleep_time*60)

            if not self.sqlhelper.recovery_point_exists(rp_name):
                self.log.info('Recovery point %s removed', rp_name)
            else:
                raise Exception(f"Recovery point {rp_name} is not removed after expiration time")

            if not self.sqlhelper.dbinit.check_database(rp_name):
                self.log.info("Database created by recovery point is removed from SQL Server")
            else:
                raise Exception(f"Database {rp_name} created by RP is not removed from sql server")

            dnb_subclient.refresh()
            if rp_name not in dnb_subclient.content:
                self.log.info('%s database removed from DNB subclient.', rp_name)
            else:
                raise Exception(f"{rp_name} not removed from DNB subclient")

            self.log.info("*" * 10 + " TestCase %s successfully completed! " + "*" * 10, self.id)
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Test case execution failed with error : %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
        self.sqlhelper.sql_teardown()
