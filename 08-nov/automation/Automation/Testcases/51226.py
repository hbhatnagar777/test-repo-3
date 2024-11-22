# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  Initializes test case class object

    setup()                 --  Setup function for this testcase

    _run_restore()          --  Initiates the restore job for the specified subclient

    get_metadata()          --  method to collect database information

    clenaup_redirect_path() --  stops postgres server after redirect restore and
    cleansup redirected path

    get_info()              --  performs necessary operations before redirect
    restore and returns required information

    tear_down()             --  tear down function to delete automation generated data

    run()                   --  Main function for test case execution

"""
from AutomationUtils import constants
from AutomationUtils import machine
from AutomationUtils import database_helper
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database import dbhelper


class TestCase(CVTestCase):
    """Class for executing redirect restore of PostgreSQL iDA"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Redirect restore of PostgreSQL iDA"
        self.postgres_helper_object = None
        self.postgres_db_password = None
        self.pgsql_db_object = None
        self.backupset = None
        self.machine_object = None

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
        self.machine_object = machine.Machine(self.client)

    def _run_restore(
            self,
            destination_client=None,
            destination_instance=None,
            redirect_path=None,
            redirect_enabled=True):
        """Initiates the restore job for the specified backupset

        Args:

            destination_client          (str)       -- Name of the destination client

                default:    None

            destination_instance        (str)       -- Name of the destination instance

                default:    None

            redirect_path               (str)       -- redirect path for restore

                default:    None

            redirect_enabled            (bool)      -- redirect flag

                default:    True

        Returns:
            job                              -- Job object of the restore job

        Raises:
            Exception:
                if redirect path is not provided

                if unable to start the restore job

        """
        self.log.info("#####Starting Redirect Restore######")
        if redirect_path is None and redirect_enabled:
            raise Exception("Please provide a redirect path")
        if destination_client is None:
            destination_client = self.client.client_name
        if destination_instance is None:
            destination_instance = self.instance.instance_name
        self.log.debug("client_name = %s", self.client.client_name)
        self.log.debug("instance_name = %s", self.instance.instance_name)
        job = self.backupset.restore_postgres_server(
            ["/data"],
            destination_client,
            destination_instance,
            redirect_enabled=True,
            redirect_path=redirect_path)
        self.log.info(
            "Started %s Restore with Job ID: %s", self.backupset.backupset_name, job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore job with error: %s" % job.delay_reason
            )

        self.log.info("Successfully finished %s restore job", self.backupset.backupset_name)

        return job

    def get_metadata(
            self,
            pgsql_db_object=None,
            postgres_helper_object=None,
            client=None,
            instance=None):
        """ method to collect database information

            Args:
                pgsql_db_object          (obj)  --  postgres database object

                postgres_helper_object   (obj)  --  postgres helper object

                client                   (obj)  --  client object

                instance                 (obj)  --  instance object

            Returns:
                dict        --      meta data info of database

            Raises:
                Exception:
                    if unable to get the database list

        """
        if pgsql_db_object is None:
            pgsql_db_object = self.pgsql_db_object
        if postgres_helper_object is None:
            postgres_helper_object = self.postgres_helper_object
        if client is None:
            client = self.client
        if instance is None:
            instance = self.instance

        # Colecting Meta data after inc backup
        database_list = pgsql_db_object.get_db_list()
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
        return postgres_helper_object.generate_db_info(
            database_list,
            client.client_name,
            instance.postgres_server_port_number,
            instance.postgres_server_user_name,
            postgres_helper_object._postgres_db_password)

    def clenaup_redirect_path(
            self,
            bin_directory,
            data_directory,
            redirect_directory,
            machine_object,
            postgres_helper=None):
        """stops postgres server after redirect restore and cleansup redirected path

            Args:

                bin_directory       (str)   --  postgres bin directory path

                data_directory      (str)   --  postgres data directory path

                redirect_directory  (str)   --  postgres redirect directory path

                machine_object      (obj)   --  machine object associated with the client

                postgres_helper     (obj)   --  postgres helper object

                    default:    None

        """
        if postgres_helper is None:
            postgres_helper = self.postgres_helper_object
        self.log.info("Stopping restored server")
        postgres_helper.stop_postgres_server(
            bin_directory, data_directory)
        self.log.info("Cleaning up redirected path")
        machine_object.remove_directory(redirect_directory)
        self.log.info("Redirected directory is removed")

    def get_info(self, agent, instance_name, client, source_instance_version):
        """ performs necessary operations before redirect
        restore and returns required information

            Args:

                agent                   (obj)   --  agent object

                instance_name           (str)   --  name of the instance

                client                  (obj)   --  client object

                source_instance_version (str)   --  server version of source instance

            Returns:
            		(obj, str, str, obj, str)

                obj	-- instance object

                str	-- bin directory path

                str	-- server port number

                obj	-- postgres_helper object

                str	-- postgres database password

            Raises:
                Exception:

                    if source and Destination server versions are different

        """
        new_instance = agent.instances.get(instance_name)
        destination_instance_version = new_instance.postgres_version.strip()
        if source_instance_version[:3] != destination_instance_version[:3]:
            raise Exception(
                "Source and Destination server versions are different.######")
        pgsql_bin_dir_new = new_instance._properties['postGreSQLInstance']['BinaryDirectory']
        pgsql_server_port = new_instance._properties['postGreSQLInstance']['port']
        postgres_helper_object_new = pgsqlhelper.PostgresHelper(
            self.commcell, client, new_instance)
        postgres_db_password_new = postgres_helper_object_new._postgres_db_password

        return (
            new_instance,
            pgsql_bin_dir_new,
            pgsql_server_port,
            postgres_helper_object_new,
            postgres_db_password_new)


    def tear_down(self):
        """tear down function to delete automation generated data"""
        self.log.info("Deleting Automation Created databases")
        self.postgres_helper_object.cleanup_tc_db(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_db_password,
            "auto")

    def run(self):
        """Main function for test case execution"""

        try:
            pgsql_server_user_name = self.instance._properties[
                'postGreSQLInstance']['SAUser']['userName']
            pgsql_server_port = self.instance._properties['postGreSQLInstance']['port']

            pgsql_bin_dir = self.instance._properties['postGreSQLInstance']['BinaryDirectory']
            self.log.info("Bin Directory: %s", pgsql_bin_dir)
            self.log.info("Postgres server Port: %s", pgsql_server_port)

            pgsql_data_dir = self.postgres_helper_object.get_postgres_data_dir(
                pgsql_bin_dir, self.postgres_db_password, pgsql_server_port)
            self.log.info("Postgres data directory: %s", pgsql_data_dir)

            source_instance_version = self.instance.postgres_version.strip()
            db_helper_object = dbhelper.DbHelper(self.commcell)

            self.log.info("Generating Test Data")
            self.postgres_helper_object.generate_test_data(
                self.client.client_hostname,
                4,
                10,
                100,
                pgsql_server_port,
                pgsql_server_user_name,
                self.postgres_db_password,
                True,
                "auto")
            self.log.info("Test Data Generated successfully")

            ################### FS Backup Operation #################
            self.log.info(
                "#" * (10) + "  Running FSBased Full Backup  " + "#" * (10))
            self.backupset = self.instance.backupsets.get("fsbasedbackupset")
            subclient = self.backupset.subclients.get("default")

            db_helper_object.run_backup(subclient, "FULL")

            before_full_backup_db_list = self.get_metadata()

            ##stopping source postgres server before the restore
            self.postgres_helper_object.stop_postgres_server(pgsql_bin_dir, pgsql_data_dir)

            # Running FS Restore
            if "windows" in self.machine_object.os_info.lower():
                pgsql_data_dir = pgsql_data_dir.replace("/", "\\")
            redirect_to = "{0}_red".format(pgsql_data_dir)
            redirect_path = "{0}\u0015{1}".format(pgsql_data_dir, redirect_to)
            self._run_restore(
                redirect_path=redirect_path)

            self.pgsql_db_object.reconnect()
            after_restore_db_info = self.get_metadata()

            self.postgres_helper_object.validate_db_info(
                before_full_backup_db_list,
                after_restore_db_info)
            self.clenaup_redirect_path(
                pgsql_bin_dir, "{0}_red".format(pgsql_data_dir), redirect_to, self.machine_object)
            self.log.info("### Redirect restore to same instance completed ###")

            ###### Same client different instance redirect restore ########
            (
                new_instance,
                pgsql_bin_dir_new,
                pgsql_server_port,
                postgres_helper_object_new,
                postgres_db_password_new) = self.get_info(
                    self.agent,
                    self.tcinputs['AnotherInstanceOnSameMachine'],
                    self.client,
                    source_instance_version)

            self._run_restore(
                destination_instance=self.tcinputs['AnotherInstanceOnSameMachine'],
                redirect_path=redirect_path)

            pgsql_db_object_new = database_helper.PostgreSQL(
                self.client.client_hostname,
                new_instance.postgres_server_port_number,
                new_instance.postgres_server_user_name,
                postgres_db_password_new,
                "postgres")

            pgsql_data_dir_new = postgres_helper_object_new.get_postgres_data_dir(
                pgsql_bin_dir_new, postgres_db_password_new, pgsql_server_port)
            after_restore_db_info = self.get_metadata(
                pgsql_db_object_new, postgres_helper_object_new, instance=new_instance)

            self.postgres_helper_object.validate_db_info(
                before_full_backup_db_list,
                after_restore_db_info)
            self.clenaup_redirect_path(
                pgsql_bin_dir_new, pgsql_data_dir_new, redirect_to, self.machine_object)

            if "windows" in self.machine_object.os_info.lower():
                self._run_restore(redirect_enabled=False)
            else:
                self.log.info("Start the Source postgres Server.")
                self.postgres_helper_object.start_postgres_server(pgsql_bin_dir, pgsql_data_dir)
            self.log.info("### Redirect restore to different instance completed ###")

            ###### Different client redirect restore ########
            new_client = self.commcell.clients.get(self.tcinputs['DestinationClientName'])
            new_agent = new_client.agents.get('postgresql')
            (
                new_instance,
                pgsql_bin_dir_new,
                pgsql_server_port,
                postgres_helper_object_new,
                postgres_db_password_new) = self.get_info(
                    new_agent,
                    self.tcinputs['DestinationInstanceName'],
                    new_client,
                    source_instance_version)
            self.machine_object = machine.Machine(new_client)
            if "windows" in self.machine_object.os_info.lower():
                pgsql_data_dir = pgsql_data_dir.replace("/", "\\")
            redirect_to = self.machine_object.join_path(pgsql_bin_dir_new, "data_red")
            redirect_path = "{0}\u0015{1}".format(pgsql_data_dir, redirect_to)

            self._run_restore(
                destination_client=self.tcinputs['DestinationClientName'],
                destination_instance=self.tcinputs['DestinationInstanceName'],
                redirect_path=redirect_path)

            pgsql_db_object_new = database_helper.PostgreSQL(
                new_client.client_hostname,
                new_instance.postgres_server_port_number,
                new_instance.postgres_server_user_name,
                postgres_db_password_new,
                "postgres")

            pgsql_data_dir_new = postgres_helper_object_new.get_postgres_data_dir(
                pgsql_bin_dir_new, postgres_db_password_new, pgsql_server_port)
            after_restore_db_info = self.get_metadata(
                pgsql_db_object_new,
                postgres_helper_object_new,
                client=new_client,
                instance=new_instance)

            self.postgres_helper_object.validate_db_info(
                before_full_backup_db_list,
                after_restore_db_info)
            if "windows" in self.machine_object.os_info.lower():
                pgsql_data_dir = pgsql_data_dir.replace("\\", "/")
            self.clenaup_redirect_path(
                pgsql_bin_dir_new,
                pgsql_data_dir_new,
                redirect_to,
                self.machine_object,
                postgres_helper=postgres_helper_object_new)
            self.log.info("### Cross machine Redirect restore completed ###")

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
