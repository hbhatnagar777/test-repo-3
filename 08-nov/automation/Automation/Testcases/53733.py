# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()         --  Initializes test case class object

    setup()            --  setup function for this testcase

    teardown()         --  Teardown function for this testcase

    _run_backup()      --  Initiates the backup job for the specified subclient

    _run_restore()     --  Initiates the restore job for the specified subclient


    validate_db_info() --  Compares the meta data collected before backup and restore
    and validates if the data is same

    run()              --  Main function for test case execution

"""
import time
from AutomationUtils import constants
from AutomationUtils import database_helper
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of PostgreSQL backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Basic Acceptance Test of PostgreSQL backup and restore"
        self.tcinputs = {
            'TestDataSize': []
        }
        self.pgsql_helper_object = None
        self.backup_set = None
        self.pgsql_server_password = None
        self.instance_properties = None
        self.pgsql_server_port = None
        self.pgsql_server_hostname = None
        self.pgsql_server_user_name = None

    def setup(self):
        """setup function for this testcase"""
        self.pgsql_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        self.pgsql_server_password = self.pgsql_helper_object._postgres_db_password
        self.instance_properties = self.instance._properties
        self.pgsql_server_port = self.instance_properties.get(
            'postGreSQLInstance', {}).get('port', None)
        self.pgsql_server_hostname = self.client.client_hostname
        self.pgsql_server_user_name = self.instance_properties.get(
            'postGreSQLInstance', {}).get('SAUser').get('userName')

    def teardown(self):
        """Teardown function for this testcase"""
        self.log.info("Deleting Automation Created databases")
        self.pgsql_helper_object.cleanup_tc_db(
            self.pgsql_server_hostname,
            self.pgsql_server_port,
            self.pgsql_server_user_name,
            self.pgsql_server_password,
            "auto")

    def _run_backup(self, subclient, backup_type):
        """Initiates the backup job for the specified subclient

        Args:
            subclient            (obj)       -- Subclient object for which backup needs to be run

            backup_type          (str)       -- Type of backup (FULL/INCREMENTAL)

        Returns:
            job                  (obj)       -- Job object of the backup job

        Raises Exception:
            if unable to start the backup job

        """

        job = subclient.backup(backup_type)
        self.log.info("Started %s backup with Job ID: %s",
                      backup_type, job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run %s backup job with error: %s" % (
                    backup_type,
                    job.delay_reason)
            )
        self.log.info("Successfully finished %s backup job", backup_type)

        return job

    def _run_restore(self, subclient, db_list):
        """Initiates the restore job for the specified subclient

        Args:
            subclient            (obj)       -- Subclient object for which restore needs to be run

            db_list              (list)      -- List of databases to be restored

        Returns:
            job                  (obj)             -- Job object of the restore job

        Raises Exception:
            if unable to start the backup job

        """

        self.log.debug("db_list = %s", db_list)
        job = subclient.restore_postgres_server(
            db_list, self.client.client_name, self.instance.instance_name)
        self.log.info("Started %s Restore with Job ID: %s",
                      self.backup_set.backupset_name, job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore job with error: %s" % job.delay_reason
            )

        self.log.info("Successfully finished %s restore job", self.backup_set.backupset_name)
        return job

    def validate_db_info(self, data_before_backup, data_after_restore):
        """ Compares the meta data collected before backup and restore
            and validates if the data is same

        Args:
            data_before_backup    (dict)  -- metadata collected before the backup

            data_after_restore    (dict)  -- metadata collected after the restore
        """

        return_code = self.pgsql_helper_object.validate_db_info(
            data_before_backup, data_after_restore)
        if not return_code:
            self.log.error(
                "Database information validation failed")
            raise Exception("Data validation failure")
        else:
            self.log.info("Database information validation passed successfully")

    def run(self):
        """Main function for test case execution

        Raises Exception:
            if data validation fails
            if the subclient given for automation does not exist
            if databases are not accessible from the server

        """
        try:
            self.log.info("Started executing %s testcase", self.id)

            subclient_list = []
            for i in self.instance.subclients.all_subclients:
                if i.startswith('dumpbased'):
                    subclient_list.append(i.split("\\")[1])
            self.log.debug("List of subclients configured for dumpbased"
                           "backupset: %s", subclient_list)
            ignoredb_list = ["postgres", "template0"]
            test_data_size = self.tcinputs['TestDataSize']
            num_of_databases = test_data_size[0]
            num_of_tables = test_data_size[1]
            num_of_rows = test_data_size[2]
            pgsql_db_object = database_helper.PostgreSQL(
                self.pgsql_server_hostname,
                self.pgsql_server_port,
                self.pgsql_server_user_name,
                self.pgsql_server_password,
                "postgres")

            pgsql_bin_dir = self.instance_properties['postGreSQLInstance']['BinaryDirectory']
            self.log.info("Bin Directory: %s", pgsql_bin_dir)
            self.log.info("Postgres server Port: %s", self.pgsql_server_port)
            self.log.info("postgres server password: %s", self.pgsql_server_password)

            pgsql_data_dir = self.pgsql_helper_object.get_postgres_data_dir(
                pgsql_bin_dir, self.pgsql_server_password, self.pgsql_server_port)
            self.log.info(pgsql_data_dir)

            pgsql_db_object.drop_tablespace(
                tablespace="auto1")
            self.log.info("Generating Test Data")
            tablespace_location = self.pgsql_helper_object.create_path_for_tablespace(
                pgsql_data_dir)

            ################# DumpBased Backup/Restore Operations ########################
            self.log.info(
                "#####  DumpBased Backup/Restore Operations  #####")
            self.backup_set = self.instance.backupsets.get("dumpbasedbackupset")
            subclient_dict = (self.backup_set.subclients._subclients)
            subclient = self.backup_set.subclients.get("default")
            subclient_list = [subclient_dict.keys()]

            pgsql_db_object.create_tablespace(
                tablespace="auto1",
                location=tablespace_location)
            self.log.info("Generating Test Data")
            self.pgsql_helper_object.generate_test_data(
                self.pgsql_server_hostname,
                num_of_databases,
                num_of_tables,
                num_of_rows,
                self.pgsql_server_port,
                self.pgsql_server_user_name,
                self.pgsql_server_password,
                True,
                database_prefix="auto_full_dmp",
                tablespace="auto1")
            self.log.info("Test Data Generated successfully")

            db_list_before_backup = None
            # Get Subclient content
            # check if subclient exists or not if not default subclient
            self.log.info("Collecting DB List")
            if subclient.subclient_name.lower() == "default":
                db_list_before_backup = pgsql_db_object.get_db_list()
                if not db_list_before_backup:
                    self.self.log.error(
                        "Unable to get the database list")
                    raise Exception("Data validation failure")
                # Get list of all the subclients content and exclude them from total list
                # of Databases
                all_other_sub_clients_contents = []
                for sbclnt in subclient_list:
                    if sbclnt.lower() != self.backup_set.subclients.default_subclient.lower():
                        self.log.info("Subclient name is not default subclient")
                        sub_client_new = self.backup_set.subclients.get(sbclnt)
                        subc_content_db_list = None
                        subc_content_db_list = sub_client_new.content
                        sub_client_db_list = []
                        for contents in subc_content_db_list:
                            sub_client_db_list.append(
                                contents['postgreSQLContent']['databaseName'])
                        self.log.info(
                            "Database list of %s Subclient is %s", sbclnt, sub_client_db_list)
                        for database in sub_client_db_list:
                            all_other_sub_clients_contents.append(
                                database.lstrip("/"))
                for db_name in all_other_sub_clients_contents:
                    if db_name in db_list_before_backup:
                        db_list_before_backup.remove(db_name)
            else:
                if self.subclient.subclient_name not in subclient_list:
                    raise Exception(
                        "{0} SubClient Does't exist".format(
                            self.subclient.subclient_name))

                sub_client_content = self.subclient.content
                db_list = []
                for i in sub_client_content:
                    db_list.append(
                        sub_client_content[i]['postgreSQLContent']['databaseName'])

                db_list_before_backup = db_list
                self.log.info("Subclient Contents: %s", db_list)
                db_list_before_backup = self.pgsql_helper_object.strip_slash_char(
                    db_list_before_backup)

            # Get the subclient content Info before backup
            self.log.info("Collect information of the subclient content before backup")
            for i in ignoredb_list:
                if i in db_list_before_backup:
                    db_list_before_backup.remove(i)

            # collecting Meta data
            before_full_backup_db_info = self.pgsql_helper_object.generate_db_info(
                db_list_before_backup,
                self.pgsql_server_hostname,
                self.pgsql_server_port,
                self.pgsql_server_user_name,
                self.pgsql_server_password)

            ###################### Running Full Backup ##############################
            self.log.info(
                "#####  Running Dumpbased Full Backup  #####")
            self._run_backup(subclient, "FULL")

            # appending "/" to dbnames for dumpbased restore
            db_list = ["/" + ele for ele in db_list_before_backup]
            time.sleep(10)
            self.log.info("Sleeping for 10 seconds")

            self.log.info("Deleting Automation Created databases")
            self.pgsql_helper_object.cleanup_tc_db(
                self.pgsql_server_hostname,
                self.pgsql_server_port,
                self.pgsql_server_user_name,
                self.pgsql_server_password,
                "auto")

            # ###################### Running restore ###################################
            self.log.info(
                "#####  Running Dumpbased Restore #####")
            self._run_restore(
                subclient, db_list)
            after_backup_db_list = pgsql_db_object.get_db_list()
            if not after_backup_db_list:
                self.log.error(
                    "Unable to get the database list")
                raise Exception("Unable to get the database list")

            # Get subclient content info after restore
            self.log.info("Collect information of the subclient content after restore")
            for i in ignoredb_list:
                if i in after_backup_db_list:
                    after_backup_db_list.remove(i)
            after_restore_db_info = self.pgsql_helper_object.generate_db_info(
                after_backup_db_list,
                self.pgsql_server_hostname,
                self.pgsql_server_port,
                self.pgsql_server_user_name,
                self.pgsql_server_password)

            # validation
            self.log.info(
                "Validating the database information collected before Full Backup \
                 and after Inplace Restore for DumpBasedBackupset")
            # validate subclient content information collected before backup and after restore
            self.validate_db_info(
                before_full_backup_db_info, after_restore_db_info)

            # ########################## FS Backup/Restore Operation #################

            # Running FS Backup FULL
            self.log.info(
                "#####  Running FSBased Full Backup  #####")
            self.backup_set = self.instance.backupsets.get("fsbasedbackupset")
            subclient_dict = (self.backup_set.subclients._get_subclients())
            subclient = self.backup_set.subclients.get("default")
            subclient_list = list(subclient_dict.keys())

            self._run_backup(subclient, "FULL")

            # Modifications to DB before incremental
            self.pgsql_helper_object.generate_test_data(
                self.pgsql_server_hostname,
                num_of_databases,
                num_of_tables,
                num_of_rows,
                self.pgsql_server_port,
                self.pgsql_server_user_name,
                self.pgsql_server_password,
                True,
                database_prefix="auto_incr_fs",
                tablespace="auto1")
            self.log.info("Test Data Generated successfully")

            # collecting Meta data
            db_list_before_backup = pgsql_db_object.get_db_list()
            if not db_list_before_backup:
                self.log.error(
                    "Unable to get the database list")
                raise Exception("Unable to get the database list")
            # Get the subclient content Info before backup
            self.log.info("Collect information of the subclient content before backup")
            for i in ignoredb_list:
                if i in db_list_before_backup:
                    db_list_before_backup.remove(i)

            before_full_backup_db_info = self.pgsql_helper_object.generate_db_info(
                db_list_before_backup,
                self.pgsql_server_hostname,
                self.pgsql_server_port,
                self.pgsql_server_user_name,
                self.pgsql_server_password)

            # Running FS Backup Log
            self.log.info(
                "#####  Running FSBased Incremental Backup  #####")
            self._run_backup(subclient, "INCREMENTAL")

            time.sleep(10)
            self.log.info("Sleeping for 10 seconds")

            # deleting data and stopping postgres server before the restore
            self.pgsql_helper_object.cleanup_database_directories(tablespace_location)

            # Running FS Restore
            self.log.info(
                "#####  Running FSBased Restore  #####")
            db_list = ["/data"]
            self._run_restore(
                subclient, db_list)

            db_list = ["/" + ele for ele in db_list_before_backup]

            # collecting Meta data
            del pgsql_db_object
            pgsql_db_object = database_helper.PostgreSQL(
                self.pgsql_server_hostname,
                self.pgsql_server_port,
                self.pgsql_server_user_name,
                self.pgsql_server_password,
                "postgres")
            after_backup_db_list = pgsql_db_object.get_db_list()
            if not after_backup_db_list:
                self.log.error(
                    "Unable to get the database list")
                raise Exception("Unable to get the database list")
            self.log.info("Collect information of the subclient content after restore")
            for i in ignoredb_list:
                if i in after_backup_db_list:
                    after_backup_db_list.remove(i)

            after_restore_db_info = self.pgsql_helper_object.generate_db_info(
                after_backup_db_list,
                self.pgsql_server_hostname,
                self.pgsql_server_port,
                self.pgsql_server_user_name,
                self.pgsql_server_password)

            # validation
            self.log.info(
                "Validating the database information collected before \
                Full Backup and after Inplace Restore for DumpBasedBackupset")
            # validate subclient content information collected before backup and after restore
            self.validate_db_info(
                before_full_backup_db_info, after_restore_db_info)

            time.sleep(10)
            self.log.info("sleeping for 10 seconds")

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
