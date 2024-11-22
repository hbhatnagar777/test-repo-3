# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  Initializes test case class object

    setup()             --  Setup function for this testcase

    tear_down()         --  tear down method for this testcase

    perform_install()   --  Method to perform push install

    check_permissions() --  Method to check if permission of CV directories are properly set

    setup_instance()    --  Method to setup postgres instance

    run_backup_restore()--  Method to run backup and restore

    run()               --  Main function for test case execution

Example Input:

    "62779":
            {
                    "postgresUser": "postgres",
                    "postgresPassword": "",
                    "postgresPort": "5432",
                    "storagePolicy": "CS_POLICY",
                    "postgresBinaryDirectory": "/usr/lib/postgresql/14/bin",
                    "postgresLibraryDirectory": "/usr/lib/postgresql/14/lib",
                    "postgresLogDirectory": "/archivelogspg"
            }

"""
from Install.install_helper import InstallHelper
from AutomationUtils.machine import Machine
from AutomationUtils import config, constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database import dbhelper


class TestCase(CVTestCase):
    """Class for executing PGSQL push install without DB group"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()

        self.name = "PGSQL push install without DB group"
        self.postgres_helper_object = None
        self.postgres_db_password = None
        self.pgsql_db_object = None
        self.install_helper = None
        self.machine_object = None
        self.client_hostname = None
        self.install_success_flag = False
        self.client = None
        self.config_json = config.get_config()
        self.tcinputs = {
            'postgresUser': None,
            'postgresPassword': None,
            'postgresPort': None,
            'storagePolicy': None,
            'postgresBinaryDirectory': None,
            'postgresLibraryDirectory': None,
            'postgresLogDirectory': None
        }
        self.subclient = None
        self.instance_object = None
        self.dbhelper_object = None


    def setup(self):
        """ setup function for this testcase """
        self.dbhelper_object = dbhelper.DbHelper(self.commcell)
        username = self.config_json.Install.unix_client.machine_username
        password = self.config_json.Install.unix_client.machine_password
        self.client_hostname = self.config_json.Install.unix_client.machine_host
        if username == '' or password == '' or self.client_hostname == '':
            raise Exception('Please provide hostname/username/Password in config.json(Install.unix_client)')
        self.machine_object = Machine(self.client_hostname, self.commcell, username, password)
        self.install_helper = InstallHelper(self.commcell, self.machine_object)

    def tear_down(self):
        """ Tear down function to uninstall the client """
        if self.install_success_flag:
            self.install_helper.uninstall_client(True)

    def perform_install(self):
        """ Method to perform push install """
        self.dbhelper_object.install_db_agent(
            'POSTGRESQL', self.machine_object, self.tcinputs['storagePolicy'])
        self.install_helper.commcell.clients.refresh()
        self.install_success_flag = True
        self.commcell.clients.refresh()

    def check_permissions(self):
        """ Method to check if permission of CV directories are properly set """
        self.client = self.commcell.clients.get(self.client_hostname)
        self.dbhelper_object.check_permissions_after_install(self.client, "postgres")

    def setup_instance(self):
        """ Method to setup postgres instance """
        agent = self.client.agents.get('postgresql')
        instances = agent.instances.all_instances
        self.log.info("Checking if instance is auto-discovered")
        auto_discovery = False
        for instance_name in instances:
            if self.tcinputs['postgresPort'] in instance_name:
                auto_discovery = True
        if auto_discovery:
            self.instance_object = agent.instances.get(f"{self.client.client_name}_{self.tcinputs['postgresPort']}")
            self.instance_object.change_sa_password('postgres')
        else:
            agent.instances.add_postgresql_instance(
                f"{self.client.client_name}_{self.tcinputs['postgresPort']}",
                storage_policy=self.tcinputs['storagePolicy'],
                port=self.tcinputs['postgresPort'],
                postgres_user_name=self.tcinputs['postgresUser'],
                postgres_password=self.tcinputs['postgresPassword'],
                binary_directory=self.tcinputs['postgresBinaryDirectory'],
                lib_director=self.tcinputs['postgresLibraryDirectory'],
                archive_log_directory=self.tcinputs['postgresLogDirectory'])
            agent.instances.refresh()
            self.instance_object = agent.instances.get(f"{self.client.client_name}_{self.tcinputs['postgresPort']}")
        self.instance_object.log_storage_policy = self.tcinputs['storagePolicy']
        backupset = self.instance_object.backupsets.get('fsbasedbackupset')
        self.subclient = backupset.subclients.get('default')
        self.subclient.storage_policy = self.tcinputs['storagePolicy']
        self.subclient.refresh()

    def run_backup_restore(self):
        """ Method to run backup and restore """
        self.dbhelper_object.run_backup(self.subclient, "FULL")

        postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance_object)
        postgres_helper_object.cleanup_database_directories()
        job = self.subclient.restore_postgres_server(
            ["/data"], self.client.client_name, self.instance_object.instance_name)
        self.log.info(
            "Started Restore with Job ID: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore job with error: %s" % job.delay_reason
            )

        self.log.info("Successfully finished restore job")

    def run(self):
        """ Main function for test case execution """

        try:
            self.perform_install()
            self.check_permissions()
            self.setup_instance()
            self.run_backup_restore()

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
