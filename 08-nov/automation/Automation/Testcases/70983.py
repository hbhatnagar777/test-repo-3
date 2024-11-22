# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Create subclient for dumpbased and verify master is used when standby is unavailable

TestCase:   Class for executing this test case

TestCase:

    __init__() -- initialize TestCase class

    setup() -- setup the requirements for the test case

    change_use_master_option(enable=True) -- enable or disable the "use master if standby unavailable" option.

    toggle_server(server, action='stop') -- change the status of the specified PostgreSQL server (start/stop/restart).

    toggle_standby(action='stop') -- start/stop/restart all standby server. (default:stop)

    dump_based_backup() -- perform a dump-based backup of the PostgreSQL databases.

    dump_based_restore(db_list) -- restore the specified list of PostgreSQL databases from a dump-based backup.

    generate_test_data() -- populate the master PostgreSQL database with random test data.

    gen_db_list() -- generate a list of databases in the master database

    add_db_group(plan_name) -- create a database group with the generated test data, associated with the specified plan.

    navigate_to_dump_backupset() -- navigate to the dump-based Backupset overview page in the web console.

    gen_db_map(when) -- generate a map of the PostgreSQL cluster's database metadata

    validate_restore() -- validate that the database metadata before backup and after restore matches.

    wait_for_job_completion(jobid) -- wait for the specified job to complete and return its state.

    delete_db_group() -- delete the database group created for automation.

    cleanup_master() -- clean up test data from the master PostgreSQL database.

    cleanup() -- clean up all test-generated resources.

    run() -- run function of this test case

    tear_down() -- tear down function of the test case



Input Example:
    "testCases":
        {
            "70983": {
                    "ClientName" : Postgres cluster client name
                    "plan_name" : plan for the new db group
                    }
        }
"""

import random
from cvpysdk.job import Job
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import database_helper, machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure, CVWebAutomationException
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import PostgreSQLClusterInstanceDetails
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Databases.subclient import PostgreSQLSubclient
from Web.AdminConsole.Databases.backupset import PostgreSQLBackupset
from Database.PostgreSQL.PostgresUtils import pgsqlhelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """
        Initializes test case class object
        """
        super().__init__()
        self.name = "Create subclient for dumpbased and verify master is used when standby is unavailable"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_instance = None
        self.db_instance_details = None
        self.pg_cluster_object = None
        self.pg_cluster_instance = None
        self.tcinputs = {
            "ClientName": None,
            "plan_name": None
        }
        self.database_list = None
        self.cluster_nodes = None
        self.cluster_data = None
        self.master_node = None
        self.master_db_object = None
        self.cluster_instance = None
        self.cluster_subclient = None
        self.cluster_pg_objects = {}
        self.cluster_backupset = None
        self.db_group_page = None
        self.db_map_after_restore = None
        self.db_map_before_backup = None
        self.full_backup = None
        self.jobs = dict()

    def setup(self):
        """
        Method to setup test variables
        """
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(username=self.inputJSONnode['commcell']["commcellUsername"],
                                 password=self.inputJSONnode['commcell']["commcellPassword"])
        self.navigator = self.admin_console.navigator
        self.pg_cluster_instance = self.client.agents.get('postgresql').instances.get(self.tcinputs['ClientName'])
        self.pg_cluster_object = pgsqlhelper.PostgresCusterHelper(self.commcell, self.client, self.pg_cluster_instance)
        self.db_instance_details = PostgreSQLClusterInstanceDetails(self.admin_console)
        self.cluster_backupset = PostgreSQLBackupset(self.admin_console)
        self.db_group_page = PostgreSQLSubclient(self.admin_console)
        self.cluster_nodes = self.pg_cluster_object.nodes
        self.cluster_data = self.pg_cluster_object.node_data
        master_node = self.pg_cluster_object.master_node
        for cluster_node in self.cluster_nodes.values():
            self.log.debug(f'generating postgres helper objects for {cluster_node}')
            con_info = {
                'client_name': cluster_node,
                'instance_name': 'dummy',
                'port': self.cluster_data[cluster_node]['port'],
                'hostname': self.commcell.clients.get(cluster_node).client_hostname,
                'user_name': self.cluster_data[cluster_node]['sa_user'],
                'password': self.cluster_data[cluster_node]['sa_password'],
                'bin_directory': self.cluster_data[cluster_node]['binary_file_path']
            }
            self.cluster_pg_objects[cluster_node] = pgsqlhelper.PostgresHelper(self.commcell, connection_info=con_info)
            self.log.debug('pghelper object generation successful')
        self.master_node = self.cluster_pg_objects[master_node]
        self.master_db_object = database_helper.PostgreSQL(
            self.master_node.postgres_server_url,
            self.master_node.postgres_port,
            self.master_node.postgres_db_user_name,
            self.master_node.postgres_password,
            "postgres")
        self.full_backup = RBackup.BackupType.FULL

    @test_step
    def change_use_master_option(self, enable=True):
        """
        Function to update "use master if standby unavailable"
        Args:
            enable (bool) : bool value to set the function
        """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['ClientName'], self.tcinputs['ClientName'])
        if enable:
            self.db_instance_details.toggle_master_if_standby_unavailable()
        else:
            self.db_instance_details.toggle_master_if_standby_unavailable(enable=False)

    def toggle_server(self, server, action='stop'):
        """
        Changes server status
        Args:
            server : name of the server
            action : start/stop/restart the server (default:stop)
        """
        node, name = None, None
        for val in self.cluster_nodes.values():
            if server == val:
                name = val
                node = self.cluster_pg_objects[val]
                break
        bin_dir, data_dir = self.cluster_data[name]["binary_file_path"], self.cluster_data[name]['data_dir']
        if action == 'stop':
            node.stop_postgres_server(bin_dir, data_dir)
        elif action == 'start':
            node.start_postgres_server(bin_dir, data_dir)
        else:
            node.stop_postgres_server(bin_dir, data_dir)
            node.start_postgres_server(bin_dir, data_dir)

    @test_step
    def toggle_standby(self, action='stop'):
        """foc"""
        for node_key, node in self.cluster_nodes.items():
            if node_key == '0':
                continue
            self.toggle_server(server=node, action=action)

    @test_step
    def backup_validation(self):
        """aa"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['ClientName'], self.tcinputs['ClientName'])

        if self.db_instance_details.master_if_standby_unavailable == 'False':
            self.log.info("Checking if backup failed because of no standby available")
            if not self.cluster_pg_objects[self.cluster_nodes['1']].get_postgres_status(
                    self.cluster_data[self.cluster_nodes['1']]["binary_file_path"],
                    self.cluster_data[self.cluster_nodes['1']]["data_dir"]):
                if self.wait_for_job_completion(self.jobs['dump_backup']):
                    self.log.error("backup happened from master when use master option disabled")
                    raise CVTestStepFailure("BACKUP NOT FAILED")
        else:
            self.log.info("Checking if data backup occurred on master.")
            node = self.commcell.clients.get(self.pg_cluster_object.master_node)
            log_path = node.log_directory
            lin_machine_object = machine.Machine(
                node, self._commcell)
            log_path = lin_machine_object.join_path(log_path, 'PostGresBackupParent.log')
            command = f"cat {log_path} | grep {self.jobs['dump_backup']} | grep 'This is backup from Master.'"
            output = lin_machine_object.execute_command(command)
            if output.exception_message == '':
                self.log.error("Error executing command on client machine: %s", output.exception_message)
                raise Exception("Unable to run the command on client machine")
            self.log.info(f"Data backup found on standby for job id {self.jobs['dump_backup']}")

    @test_step
    def dump_based_backup(self):
        """
        Helper function for dump based backups
        """
        self.navigate_to_dump_backupset()
        self.log.info("#" * 10 + "  DumpBased Backup Operations  " + "#" * 10)
        self.log.info("Running DumpBased Backup.")
        self.db_instance_details.click_on_entity('automation_test')
        self.jobs['dump_backup'] = self.db_group_page.backup(backup_type=self.full_backup)
        self.wait_for_job_completion(self.jobs['dump_backup'])
        self.log.info("Dumpbased backup compeleted successfully.")

    @test_step
    def dump_based_restore(self, db_list):
        """
         Helper function for Dump based restores
            Args:
                db_list: list of databses created to restore
        """
        self.navigate_to_dump_backupset()
        self.log.info("#" * 10 + "  Running DumpBasedBackupSet Restore  " + "#" * 10)
        self.cluster_backupset.access_restore()
        restore_panel = self.cluster_backupset.restore_folders(
            database_type=DBInstances.Types.POSTGRES, items_to_restore=db_list)
        self.jobs['dump_restore'] = restore_panel.in_place_restore()
        self.wait_for_job_completion(self.jobs['dump_restore'])
        self.log.info("Dumpbased restore compeleted successfully.")

    @test_step
    def generate_test_data(self):
        """ Generates test data for backup and restore """
        self.log.info("Populating master with random data.")
        db_prefix = "auto_full_dmp"
        self.log.info("Generating Test Data")
        self.master_node.generate_test_data(
            self.master_node.postgres_server_url,
            random.randint(3, 10),
            random.randint(3, 10),
            random.randint(3, 10),
            self.master_node.postgres_port,
            self.master_node.postgres_db_user_name,
            self.master_node.postgres_password,
            True,
            db_prefix)
        self.log.info("Successfully generated Test Data.")

    @test_step
    def gen_db_list(self):
        """
        Generates a list of databases containing 'auto_full_dmp' in their name from the master database.
        """
        self.log.info("Generating list of databases containing 'auto_full_dmp'.")
        self.database_list = []
        db_list = self.master_db_object.get_db_list()
        for database in db_list:
            if 'auto_full_dmp' in database:
                self.database_list.append(database)
        self.log.info(f"Master database list populated: {self.database_list}")

    @test_step
    def add_db_group(self, plan_name):
        """
        Creates a database group consisting of generated Test data( similar to a sub client )
            Args:
            plan_name       (str):      Name of the plan to associate to subclient
        """
        self.navigate_to_dump_backupset()
        self.cluster_backupset.add_subclient("automation_test", 2, True, plan_name, self.database_list)
        self.admin_console.wait_for_completion()

    @test_step
    def navigate_to_dump_backupset(self):
        """
        Navigates to the dumpbased Backupset overview page
        """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['ClientName'], self.tcinputs['ClientName'])
        self.cluster_instance = self.client.agents.get('postgresql').instances.get(self.tcinputs['ClientName'])
        self.cluster_subclient = self.cluster_instance.backupsets.get('dumpbasedbackupset')
        self.db_instance_details.click_on_entity('DumpBasedBackupSet')

    @test_step
    def validate_restore(self):
        """
        Validates that the database metadata before backup and after restore matches.
        """
        self.log.info("Validating DB info before backup and after restore.")
        if not self.master_node.validate_db_info(self.db_map_before_backup, self.db_map_after_restore):
            self.log.error('Database info validation failed: metadata before backup and after restore do not match.')
            raise CVTestStepFailure('Database info before backup and after restore do not match.')
        self.log.info("Database info validated successfully: metadata matches before backup and after restore.")

    @test_step
    def wait_for_job_completion(self, jobid):
        """
        Waits for completion of job and gets the object once job completes
        Args:
            jobid   (str): Jobid
        Returns:
            job state (bool)
        """
        job = Job(self.commcell, jobid)
        job_state = job.wait_for_completion()
        self.log.info("Job state: [" + str(job_state) + "]")
        self.log.info("finished %s job", jobid)
        return job_state

    @test_step
    def delete_db_group(self):
        """
        Deletes the DB Group made for automation
        """
        self.navigate_to_dump_backupset()
        self.db_instance_details.click_on_entity('automation_test')
        self.db_group_page.delete_subclient()

    @test_step
    def cleanup_master(self):
        """
        Cleans up test data from the master database.
        """
        self.log.info("Cleaning up test data from master database.")
        self.master_node.cleanup_test_data(self.database_list)
        self.log.info("Test data cleanup complete.")

    @test_step
    def cleanup(self):
        """Method to clean up test generated resources"""
        self.toggle_standby(action='start')
        self.cleanup_master()
        self.delete_db_group()

    def run(self):
        """Run function of this test case"""
        try:
            self.change_use_master_option(enable=False)
            self.generate_test_data()
            self.gen_db_list()
            self.add_db_group(self.tcinputs['plan_name'])
            self.dump_based_backup()
            self.toggle_standby()
            self.dump_based_backup()
            self.backup_validation()
            self.change_use_master_option(enable=True)
            self.gen_db_list()
            self.db_map_before_backup = self.master_node.get_metadata()
            self.dump_based_backup()
            self.backup_validation()
            self.dump_based_restore(self.database_list)
            self.db_map_after_restore = self.master_node.get_metadata()
            self.validate_restore()

        except Exception as e:
            self.log.error(f'An error occurred during execution: {e}')
            raise CVWebAutomationException

        finally:
            self.cleanup()

    def tear_down(self):
        """Tear Down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
