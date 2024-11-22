# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  Initializes test case class object

    setup()         --  Setup function for this testcase

    get_metadata()  --  method to collect database information

    validate_data() --  validates the data in source and destination

    run()           --  Main function for test case execution

"""
from AutomationUtils import constants
from AutomationUtils import database_helper
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """Class for executing PostgreSQL - Collect Object List during backup option test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "PostgreSQL - Collect Object List during backup option"
        self.postgres_helper_object = None
        self.postgres_db_password = None
        self.pgsql_db_object = None

    def setup(self):
        """setup function for this testcase"""

        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        self.postgres_db_password = self.postgres_helper_object.postgres_password
        self.pgsql_db_object = database_helper.PostgreSQL(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            "postgres")

    def get_metadata(self):
        """ method to collect database information

            Returns:
                dict        --      meta data info of database

            Raises:
                Exception:
                    if unable to get the database list

        """
        # Colecting Meta data after inc backup
        database_list = self.pgsql_db_object.get_db_list()
        if database_list is None:
            raise Exception(
                "Unable to get the database list."
            )
        # Get the subclient content Info before backup
        self.log.info(
            "Collect information of the subclient content")
        for database in ["postgres", "template0"]:
            if database in database_list:
                database_list.remove(database)
        return self.postgres_helper_object.generate_db_info(
            database_list,
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password)

    def validate_data(self, db_info_source, db_info_destination):
        """validates the data in source and destination

            Args:
                db_info_source        (dict)  --  database information of source

                db_info_destination   (dict)  --  database information of destination

            Raises:
                Exception:

                    if database information validation failed

        """

        self.log.info("Validating the database information collected before \
            Incremental Backup and after volume level Restore")
        if not self.postgres_helper_object.validate_db_info(
                db_info_source, db_info_destination):
            raise Exception(
                "Database information validation failed.!!!"
            )
        else:
            self.log.info(
                "###Database information validation passed successfully..!!###")

    def tear_down(self):
        """tear down function to delete automation generated data"""
        self.log.info("Deleting Automation Created databases")
        self.postgres_helper_object.cleanup_tc_db(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            "auto")
        self.log.info("Disabling collect object list")
        if self.subclient.collect_object_list:
            self.subclient.collect_object_list = False

    def run(self):
        """Main function for test case execution"""

        try:

            pgsql_server_user_name = self.instance._properties[
                'postGreSQLInstance']['SAUser']['userName']
            pgsql_server_port = self.instance._properties['postGreSQLInstance']['port']
            pgsql_server_hostname = self.client.client_hostname

            self.log.info("Enabling COLLECT OBJECT LIST in subclient property")
            if not self.subclient.collect_object_list:
                self.subclient.collect_object_list = True
            self.log.info("COLLECT OBJECT LIST is enabled")

            ################# DumpBased Backup/Restore Operations ########################
            self.log.info(
                "###  DumpBased Backup/Restore Operations  ###")
            db_prefix = "auto_full_dmp"
            self.log.info("Generating Test Data")
            self.postgres_helper_object.generate_test_data(
                pgsql_server_hostname,
                3,
                30,
                200,
                pgsql_server_port,
                pgsql_server_user_name,
                self.postgres_db_password,
                True,
                db_prefix)
            self.log.info("Test Data Generated successfully")

            db_list_before_backup = self.postgres_helper_object.get_subclient_database_list(
                self.subclient.subclient_name,
                self.backupset,
                self.pgsql_db_object.get_db_list())

            before_full_backup_db_list = self.get_metadata()

            ###################### Running Full Backup ##############################
            dbhelper_object = DbHelper(self._commcell)
            self.log.info(
                "###  Running Dumpbased Full Backup  ###")
            dbhelper_object.run_backup(self.subclient, "FULL")

            # appending "/" to dbnames for dumpbased restore
            for i in ["postgres", "template0"]:
                if i in db_list_before_backup:
                    db_list_before_backup.remove(i)
            db_list = ["/" + ele for ele in db_list_before_backup]

            ##################### Running Table level restore #########################
            self.log.info("######### Performing table level restore #########")
            self.log.info("Deleting a table from database")
            self.postgres_helper_object.drop_table(
                "testtab_1",
                pgsql_server_hostname,
                pgsql_server_port,
                pgsql_server_user_name,
                self.postgres_db_password,
                "auto_full_dmp_testdb_0")
            self.log.info("Deleting function from database")
            self.postgres_helper_object.drop_function(
                "test_function_1", database="auto_full_dmp_testdb_0")
            self.log.info("### starting table level restore ###")
            self.postgres_helper_object.run_restore(
                [
                    "/auto_full_dmp_testdb_0/public/testtab_1/",
                    "/auto_full_dmp_testdb_0/public/test_view_1/",
                    "/auto_full_dmp_testdb_0/public/test_function_1/"
                ],
                self.subclient, table_level_restore=True, is_dump_based=True)

            after_restore_db_info = self.get_metadata()

            self.validate_data(before_full_backup_db_list, after_restore_db_info)

            self.log.info("Deleting Automation Created databases")
            tc_name = "auto"
            self.postgres_helper_object.cleanup_tc_db(
                pgsql_server_hostname,
                pgsql_server_port,
                pgsql_server_user_name,
                self.postgres_db_password,
                tc_name)

            ####################### Running restore ########################
            self.log.info(
                "###  Running Dumpbased Restore  ###")
            self.log.info("Database list to restore:%s", db_list)
            self.postgres_helper_object.run_restore(db_list, self.subclient, is_dump_based=True)

            after_restore_db_info = self.get_metadata()
            self.validate_data(before_full_backup_db_list, after_restore_db_info)

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
