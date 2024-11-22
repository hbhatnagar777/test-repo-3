# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                    --  Initializes test case class object

    setup()                       --  setup function for this testcase

    _run_restore()                --  Initiates the restore job for the specified subclient

    collect_server_details()    --  Collects all the information about the postgres
    server and creates helper objects for given instance

    server_stop_restore_validate() -- Stops postgres server, cleans up data and wals dirs,
    runs restore and validation

    run()                         --  Main function for test case execution

"""
import time
from AutomationUtils import constants
from AutomationUtils import database_helper
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper


class TestCase(CVTestCase):
    """Class for executing PostgreSQL redirect restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Redirect restore Test of PostgreSQL"
        self.tcinputs = {
            'CrossInstance': None,
            'CrossMachineInstance': None,
            'CrossMachineClient': None,
            'TestDataSize': None
        }
        self.postgres_data_population_size = None
        self.num_of_databases = None
        self.num_of_tables = None
        self.num_of_rows = None
        self.ignoredb_list = []

    def setup(self):
        """setup function for this testcase"""
        self.ignoredb_list = ["postgres", "template0", "template1"]
        self.pgsql_instance_s2_name = self.tcinputs['CrossInstance']
        self.pgsql_instance_s3_name = self.tcinputs['CrossMachineInstance']
        self.pgsql_client2_name = self.tcinputs['CrossMachineClient']
        self.postgres_data_population_size = self.tcinputs['TestDataSize']
        self.num_of_databases = self.postgres_data_population_size[0]
        self.num_of_tables = self.postgres_data_population_size[1]
        self.num_of_rows = self.postgres_data_population_size[2]

    def _run_restore(self, subclient, db_list, client_name,
                     instance_name, redirect_option, redirect_path):
        """Initiates the restore job for the specified subclient

        Args:
            subclient            (Obj)       -- Subclient object for which restore needs to be run

            backup_type          (str)       -- Type of backup (FULL/INCREMENTAL)

            client_name          (str)       -- Name of the client which subclient belongs to

            instance_name        (str)       -- Name of the instance which subclient belongs to

            redirect_option      (Bool)      -- Indicates whether or not redirect is enabled

            redirect_path        (str)       -- redirect path to be used for restore

        Returns:
            job                  (obj)       -- Job object of the restore job

        Raises Exception:
            if unable to start the restore job

        """

        self.log.debug("db_list = %s", db_list)
        self.log.debug("client_name = %s", client_name)
        self.log.debug("instance_name = %s", instance_name)
        job = subclient.restore_postgres_server(
            db_list,
            client_name,
            instance_name,
            redirect_enabled=redirect_option,
            redirect_path=redirect_path)
        self.log.info("Started FSBased Backupset Restore with Job ID: %s",
                      job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore job with error: {0}".format(job.delay_reason)
            )

        self.log.info("Successfully finished FSBased BAckupset restore job")

        return job

    def collect_server_details(self, pgsql_client, pgsql_instance_name):
        """ Collects all the information about the postgres server
        and creates helper objects for given instance

        Args:
            pgsql_client        (obj)  -- client object of client where server exists

            pgsql_instance_name (str)  -- name of the postgresql instance

        returns:
            server_details   (dict)  -- details of given postgres server

        """
        pgsql_agent = pgsql_client.agents.get('postgresql')
        pgsql_instance = pgsql_agent.instances.get(pgsql_instance_name)
        pgsql_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, pgsql_client, pgsql_instance)
        pgsql_instance_properties = pgsql_instance._properties
        pgsql_server_user_name = pgsql_instance_properties[
            'postGreSQLInstance']['SAUser']['userName']
        pgsql_bin_dir = pgsql_instance_properties[
            'postGreSQLInstance']['BinaryDirectory']
        pgsql_server_password = pgsql_helper_object._postgres_db_password
        pgsql_server_port = pgsql_instance_properties['postGreSQLInstance']['port']
        pgsql_server_hostname = pgsql_client.client_hostname
        pgsql_db_object = database_helper.PostgreSQL(
            pgsql_server_hostname,
            pgsql_server_port,
            pgsql_server_user_name,
            pgsql_server_password,
            "postgres")
        pgsql_data_dir = pgsql_helper_object.get_postgres_data_dir(
            pgsql_bin_dir, pgsql_server_password, pgsql_server_port)

        server_details = {}
        server_details['pgsql_helper_object'] = pgsql_helper_object
        server_details['pgsql_db_object'] = pgsql_db_object
        server_details['pgsql_bin_dir'] = pgsql_bin_dir
        server_details['pgsql_data_dir'] = pgsql_data_dir
        server_details['pgsql_server_user_name'] = pgsql_server_user_name
        server_details['pgsql_server_password'] = pgsql_server_password
        server_details['pgsql_server_port'] = pgsql_server_port
        server_details['pgsql_server_hostname'] = pgsql_server_hostname

        return server_details

    def server_stop_restore_validate(self,
                                     pgsql_server_hostname, pgsql_server_port,
                                     pgsql_server_user_name, pgsql_server_password,
                                     pgsql_data_dir, pgsql_helper_object,
                                     client_name, instance_name,
                                     subclient, before_full_backup_db_list):
        """Stops postgres server, cleans up data and wal directories,
        runs restore and validation

        Args:
            pgsql_server_hostname(str)       -- hostname of postgres server

            pgsql_server_port    (str)       -- postgres server port number

            pgsql_server_user_name(str)      -- postgres server username

            pgsql_server_password(str)       -- postgres server password

            pgsql_data_dir       (str)       -- postgres data directory

            pgsql_helper_object  (obj)       -- postgresql helper object

            client_name          (str)       -- destination client name

            instance_name        (str)       -- destination instance name

            subclient            (Obj)       -- Subclient object for which restore needs to be run

            before_full_backup_db_list (list)-- meta data of server before backup

        Raises Exception:
            if unable to get database list
            if Data Validation fails

        """

        # stopping postgres server before the restore and clean up database directories
        pgsql_helper_object.cleanup_database_directories()

        # Running FS Restore
        db_list = ["/data"]
        redirect_source = "|%s" % pgsql_data_dir
        redirect_destination = "%s-autoredirect" % pgsql_data_dir
        redirect_path = "%s|#15!%s" % (redirect_source, redirect_destination)
        self.log.info("Redirect path being used for the restore: %s", redirect_destination)
        self._run_restore(
            subclient,
            db_list,
            client_name,
            instance_name,
            redirect_option=True,
            redirect_path=[redirect_path])

        # Collecting Meta data
        pgsql_db_object = database_helper.PostgreSQL(
            pgsql_server_hostname,
            pgsql_server_port,
            pgsql_server_user_name,
            pgsql_server_password,
            "postgres")
        after_backup_db_list = pgsql_db_object.get_db_list()
        if not after_backup_db_list:
            self.log.error(
                "Unable to get the database list")
            raise Exception("Unable to get the database list")
        self.log.info("Collect information of the subclient content after restore")
        for db_name in self.ignoredb_list:
            if db_name in after_backup_db_list:
                after_backup_db_list.remove(db_name)
        after_restore_db_info = pgsql_helper_object.generate_db_info(
            after_backup_db_list,
            pgsql_server_hostname,
            pgsql_server_port,
            pgsql_server_user_name,
            pgsql_server_password)

        # validation
        self.log.info(
            "Validating the database information collected before "
            "Full Backup and after Inplace Restore for DumpBasedBackupset")
        # validate subclient content information collected before backup and after restore
        return_code = pgsql_helper_object.validate_db_info(
            before_full_backup_db_list, after_restore_db_info)
        if not return_code:
            self.log.error(
                "Database information validation failed")
            raise Exception("Data validation failure")
        else:
            self.log.info("Database information validation passed successfully")

        time.sleep(10)
        self.log.info("sleeping for 10 seconds")

        self.log.info("Deleting Automation Created databases")
        tc_name = "auto"
        pgsql_helper_object.cleanup_tc_db(
            pgsql_server_hostname,
            pgsql_server_port,
            pgsql_server_user_name,
            pgsql_server_password,
            tc_name)

    def run(self):
        """Main function for test case execution"""
        try:
            pgsql_helper_object = pgsqlhelper.PostgresHelper(
                self.commcell, self.client, self.instance)

            subclient_list = []
            for i in self.instance.subclients.all_subclients:
                if i.startswith('dumpbased'):
                    subclient_list.append(i.split("\\")[1])

            # Collecting information of server 1
            pgsql_server_s1_details = self.collect_server_details(
                self.client,
                self.instance.instance_name)
            # Collecting information of server 2
            pgsql_server_s2_details = self.collect_server_details(
                self.client,
                self.pgsql_instance_s2_name)
            # Collecting information of server 3 (from client 2)
            pgsql_client2 = self.commcell.clients.get(self.pgsql_client2_name)
            pgsql_server_s3_details = self.collect_server_details(
                pgsql_client2,
                self.pgsql_instance_s3_name)
            ########################## FS Backup Operation #################

            backup_set = self.instance.backupsets.get("fsbasedbackupset")
            subclient = backup_set.subclients.get("default")

            # Data Population
            db_prefix = "auto_full_fs"
            pgsql_server_s1_details['pgsql_helper_object'].generate_test_data(
                pgsql_server_s1_details['pgsql_server_hostname'],
                self.num_of_databases,
                self.num_of_tables,
                self.num_of_rows,
                pgsql_server_s1_details['pgsql_server_port'],
                pgsql_server_s1_details['pgsql_server_user_name'],
                pgsql_server_s1_details['pgsql_server_password'],
                True,
                db_prefix)
            self.log.info("Test Data Generated successfully")

            # Collecting Meta data
            db_list_before_backup = pgsql_server_s1_details['pgsql_db_object'].get_db_list()
            if not db_list_before_backup:
                self.log.error(
                    "Unable to get the database list")
                raise Exception("Data validation failure")
            # Get the subclient content Info before backup
            self.log.info("Collect information of the subclient content before backup")
            for db_name in self.ignoredb_list:
                if db_name in db_list_before_backup:
                    db_list_before_backup.remove(db_name)
            before_full_backup_db_list = pgsql_server_s1_details[
                'pgsql_helper_object'].generate_db_info(
                    db_list_before_backup,
                    pgsql_server_s1_details['pgsql_server_hostname'],
                    pgsql_server_s1_details['pgsql_server_port'],
                    pgsql_server_s1_details['pgsql_server_user_name'],
                    pgsql_server_s1_details['pgsql_server_password'])

            # Running FS Based full backup
            self.log.info(
                "##### Running FSBased Full Backup  #####")
            job = subclient.backup("FULL")
            self.log.info("Started Full backup with Job ID: %s",
                          job.job_id)
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run Full backup job with error: %s",
                    job.delay_reason
                )
            self.log.info("Successfully finished Full backup job")

            time.sleep(10)
            self.log.info("Sleeping for 10 seconds")

            ########################## Inplace redirect restore to same instance #####
            self.log.info(
                "#####  Running Same Instance Redirect Restore  #####")

            self.server_stop_restore_validate(
                pgsql_server_s1_details['pgsql_server_hostname'],
                pgsql_server_s1_details['pgsql_server_port'],
                pgsql_server_s1_details['pgsql_server_user_name'],
                pgsql_server_s1_details['pgsql_server_password'],
                pgsql_server_s1_details['pgsql_data_dir'],
                pgsql_server_s1_details['pgsql_helper_object'],
                self.client.client_name,
                self.instance.instance_name,
                subclient,
                before_full_backup_db_list)

            ########################## Inplace redirect restore to different instance#
            self.log.info(
                "#####  Running Cross Instance Redirect Restore  #####")

            self.server_stop_restore_validate(
                pgsql_server_s2_details['pgsql_server_hostname'],
                pgsql_server_s2_details['pgsql_server_port'],
                pgsql_server_s2_details['pgsql_server_user_name'],
                pgsql_server_s1_details['pgsql_server_password'],
                pgsql_server_s2_details['pgsql_data_dir'],
                pgsql_server_s2_details['pgsql_helper_object'],
                self.client.client_name,
                self.pgsql_instance_s2_name,
                subclient,
                before_full_backup_db_list)

            ########################## Out of place redirect restore ##########################
            self.log.info(
                "##### Running Cross Machine Redirect Restore  #####")

            self.server_stop_restore_validate(
                pgsql_server_s3_details['pgsql_server_hostname'],
                pgsql_server_s3_details['pgsql_server_port'],
                pgsql_server_s3_details['pgsql_server_user_name'],
                pgsql_server_s3_details['pgsql_server_password'],
                pgsql_server_s3_details['pgsql_data_dir'],
                pgsql_server_s3_details['pgsql_helper_object'],
                pgsql_client2.client_name,
                self.pgsql_instance_s3_name,
                subclient,
                before_full_backup_db_list)

            ########################## Resetting the servers ##########################

            # stopping postgres server before the restore and clean up database directories
            pgsql_server_s3_details['pgsql_helper_object'].cleanup_database_directories()
            # Running FS Restore
            self.log.info(
                "#####  Running FSBased Restore for Instance 3 #####")
            db_list = ["/data"]
            self._run_restore(
                subclient,
                db_list,
                pgsql_client2.client_name,
                self.pgsql_instance_s3_name,
                redirect_option=False,
                redirect_path=None)

            # stopping postgres server before the restore and clean up database directories
            pgsql_server_s1_details['pgsql_helper_object'].cleanup_database_directories()
            # Running FS Restore
            self.log.info(
                "#####  Running FSBased Restore for Instance 1 #####")
            self._run_restore(
                subclient,
                db_list,
                self.client.client_name,
                self.instance.instance_name,
                redirect_option=False,
                redirect_path=None)

            # stopping postgres server before the restore and clean up database directories
            redirect_source = "|%s" % pgsql_server_s1_details['pgsql_data_dir']
            redirect_destination = pgsql_server_s2_details['pgsql_data_dir']
            redirect_path = "%s|#15!%s" % (redirect_source, redirect_destination)
            pgsql_server_s2_details['pgsql_helper_object'].cleanup_database_directories()
            # Running FS Restore
            self.log.info(
                "#####  Running FSBased Restore for Instance 2 #####")
            self._run_restore(
                subclient,
                db_list,
                self.client.client_name,
                self.pgsql_instance_s2_name,
                redirect_option=True,
                redirect_path=[redirect_path])

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
