# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  Initializes test case class object

    setup()         --  Setup function for this testcase

    teardown()      --  Cleans up testdata

    run()           --  Main function for test case execution

"""
import time
from AutomationUtils import constants
from AutomationUtils import database_helper
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database.config_cloud_db import ConfigCloudDb


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance test of Amazon RDS PostgreSQL backup and Restore test case
    Example for testcase inputs:
    "56192": {
        "client_name": "client name",

        "agent_name": "PostgreSQL",

        "instance_name": "pgsqldb2[eastus]",

        "access_node": "proxyvm",

        "cloud_type":"Amazon",

        "cloud_options": {

            "accessKey": "accesskey",
            
            "secretkey": "secretkey"

        },

        "database_options": {

                "storage_policy":"storage policy",

                "port":"pgsqldb2.postgres.database.amazon.com:5432",

                "postgres_user_name":"postgres user",

                "postgres_password":"password",

                "version":"postgres version"

            }

        }

    Example if client/agent/instance already exists:
    "56192": {
        "ClientName": "cloud client name",

        "AgentName": "PostgreSQL",

        InstanceName": "pgsqldb2 [eastus]",

        "BackupsetName": "DumpBasedBackupSet",

        "SubclientName": "default",

    }
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Basic Acceptance Test of Amazon RDS PostgreSQL backup and restore"
        self.postgres_helper_object = None
        self.pgsql_db_object = None
        self.config_cloud_db_object = None

    def setup(self):
        """setup function for this testcase"""
        if self._client is None:
            self.config_cloud_db_object = ConfigCloudDb(self.commcell, self.tcinputs)
        elif self._instance is None:
            self.config_cloud_db_object = ConfigCloudDb(self.commcell, self.tcinputs, self.client)
        else:
            self.config_cloud_db_object = ConfigCloudDb(self.commcell, self.tcinputs, self.client, self.instance)
        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.config_cloud_db_object.client, self.config_cloud_db_object.instance)
        self.pgsql_db_object = database_helper.PostgreSQL(
            self.postgres_helper_object.postgres_server_url,
            self.postgres_helper_object.postgres_port,
            self.postgres_helper_object.postgres_db_user_name,
            self.postgres_helper_object.postgres_password,
            "postgres")
        self.postgres_helper_object.pgsql_db_object = self.pgsql_db_object

    def tear_down(self):
        """tear down function to delete automation generated data"""
        self.log.info("Deleting Automation Created databases")
        self.postgres_helper_object.cleanup_tc_db(
            self.postgres_helper_object.postgres_server_url,
            self.postgres_helper_object.postgres_port,
            self.postgres_helper_object.postgres_db_user_name,
            self.postgres_helper_object.postgres_password,
            "auto")

    def run(self):
        """Main function for test case execution"""
        try:
            postgres_data_population_size = self.tcinputs.get('TestDataSize', [2, 10, 10])
            num_of_databases = postgres_data_population_size[0]
            num_of_tables = postgres_data_population_size[1]
            num_of_rows = postgres_data_population_size[2]

            ################# DumpBased Backup/Restore Operations ########################
            self.log.info(
                "#" * 10 + "  DumpBased Backup/Restore Operations  " + "#" * 10)
            backupset = self.config_cloud_db_object.instance.backupsets.get("dumpbasedbackupset")
            subclient_dict = backupset.subclients._subclients
            subclient = backupset.subclients.get("default")
            subclient_list = list(subclient_dict.keys())

            db_prefix = "auto_full_dmp"
            self.log.info("Generating Test Data")
            self.postgres_helper_object.generate_test_data(
                self.postgres_helper_object.postgres_server_url,
                num_of_databases,
                num_of_tables,
                num_of_rows,
                self.postgres_helper_object.postgres_port,
                self.postgres_helper_object.postgres_db_user_name,
                self.postgres_helper_object.postgres_password,
                True,
                db_prefix)
            self.log.info("Test Data Generated successfully")

            # Get Subclient content
            # check if subclient exists or not if not default subclient
            self.log.info("Collecting DB List")
            db_list_before_backup = self.pgsql_db_object.get_db_list()
            if db_list_before_backup is None:
                raise Exception("Unable to get the database list. Cleaning up test data.")
            # Get list of all the subclients content and exclude them from total list
            # of Databases
            self.log.debug(db_list_before_backup)
            all_other_sub_clients_contents = list()
            for sub_client in subclient_list:
                if sub_client.lower() != backupset.subclients.default_subclient.lower():
                    self.log.info("Subclient name is not default subclient")
                    self.log.debug(sub_client)
                    sub_client_new = backupset.subclients.get(sub_client)
                    self.log.debug(sub_client_new.content)
                    subc_content_db_list = sub_client_new.content
                    self.log.debug(subc_content_db_list)
                    sub_client_db_list = []
                    for contents in subc_content_db_list:
                        sub_client_db_list.append(contents)
                    self.log.info(
                        "Database list of %s Subclient is %s", sub_client, sub_client_db_list)
                    for database in sub_client_db_list:
                        all_other_sub_clients_contents.append(
                            database.lstrip("/"))
            for db_name in all_other_sub_clients_contents:
                if db_name in db_list_before_backup:
                    db_list_before_backup.remove(db_name)

            before_full_backup_db_list = self.postgres_helper_object.get_metadata()

            ###################### Running Full Backup ##############################
            self.log.info(
                "#" * 10 + "  Running Dumpbased Full Backup  " + "#" * 10)
            self.postgres_helper_object.run_backup(subclient, "FULL")

            # appending "/" to dbnames for dumpbased restore
            for i in ["postgres", "template0", "rdsadmin"]:
                if i in db_list_before_backup:
                    db_list_before_backup.remove(i)
            db_list = ["/" + ele for ele in db_list_before_backup]
            time.sleep(10)
            self.log.info("Sleeping for 10 seconds")

            ##################### Running Table level restore #########################
            self.log.info("######### Performing table level restore #########")
            self.log.info("Deleting a table from database")
            self.postgres_helper_object.drop_table(
                "testtab_1",
                self.postgres_helper_object.postgres_server_url,
                self.postgres_helper_object.postgres_port,
                self.postgres_helper_object.postgres_db_user_name,
                self.postgres_helper_object.postgres_password,
                "auto_full_dmp_testdb_0")
            self.log.info("Deleting function from database")
            self.postgres_helper_object.drop_function(
                "test_function_1", database="auto_full_dmp_testdb_0")
            self.log.info("### starting table level restore ###")
            self.postgres_helper_object.run_restore(
                [
                    "/auto_full_dmp_testdb_0/public/testtab_1/",
                    "/auto_full_dmp_testdb_0/public/test_view_1/",
                    "/auto_full_dmp_testdb_0/public/test_function_1/"],
                subclient,
                is_dump_based=True,
                table_level_restore=True)

            after_restore_db_info = self.postgres_helper_object.get_metadata()

            self.postgres_helper_object.validate_db_info(
                before_full_backup_db_list, after_restore_db_info)

            self.log.info("Deleting Automation Created databases")
            tc_name = "auto"
            self.postgres_helper_object.cleanup_tc_db(
                self.postgres_helper_object.postgres_server_url,
                self.postgres_helper_object.postgres_port,
                self.postgres_helper_object.postgres_db_user_name,
                self.postgres_helper_object.postgres_password,
                tc_name)

            ####################### Running restore ###################################
            self.log.info(
                "#" * 10 + "  Running Dumpbased Restore  " + "#" * 10)
            self.log.info("Database list to restore:%s", db_list)
            self.postgres_helper_object.run_restore(
                db_list, subclient, is_dump_based=True)

            after_restore_db_info = self.postgres_helper_object.get_metadata()
            self.postgres_helper_object.validate_db_info(
                before_full_backup_db_list, after_restore_db_info)

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
