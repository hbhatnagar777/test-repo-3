# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""ACC test case for postgresql cluster EDB Failover Manager

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    add_instance() -- Add new PostgreSQL Cluster instance

    edit_instance() -- Edit DB instance by adding a new node

    fs_backup(backup_type) -- Helper function for fs based backups

    backup_validation() -- Validates the backup process for a PostgreSQL Cluster instance

    fs_restore(restore_to_entire_cluster, restore_node=None) -- Helper function for fs based restores

    wait_for_job_completion(jobid) -- Waits for completion of job and gets the object once job completes

    generate_test_data() -- Generates test data for backup and restore

    gen_db_list() -- Generates a list of databases containing 'auto_full_dmp' in their name from the master database

    gen_db_map(when) -- Generates a map of the cluster's database metadata

    validate_restore() -- Validates that the database metadata before backup and after restore matches

    cluster_mgr_validate() -- Validates whether the EDB has started by checking the log backup on the master node

    cleanup_master() -- Cleans up test data from the master database

    delete_instance() -- Deletes the PostgreSQL Cluster instance if it exists

    run()           --  run function of this test case

    tear_down()     -- tear down function of the test case

Input Example:
    "testCases":
        {
            "70813": {
                    "nodes" :[node1 (master),node2,node3]
                    "plan"  : plan_name
                    "cluster_bin" : cluster_bin
                    "cluster_conf" " cluster_conf
                    }
        }

            note -->
                node: The nodes list where each element is a dictionary representing a node,
                      containing the following key-value pairs:
                node (dict):
                {
                    server (str): The name of the server.
                    password (str): The password for accessing the PostgreSQL server
                    port (int): The port number on which the PostgreSQL server is running
                    bin_dir (str): The directory where PostgreSQL binary files are located
                    lib_dir (str): The directory where PostgreSQL library files are located
                    archive_wal_dir (str): The directory where Write-Ahead Logging (WAL) files are archived
                }
"""
import random
import time
import cvpysdk.job
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import machine, database_helper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import PostgreSQLClusterInstanceDetails
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Databases.subclient import PostgreSQLSubclient
from Web.AdminConsole.Databases.backupset import PostgreSQLBackupset
import Web.Common.exceptions as cvexceptions
from Database.PostgreSQL.PostgresUtils import pgsqlhelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """
        Initializes test case class object
        """
        super().__init__()
        self.name = "ACC test case for postgresql cluster EFM"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_instance = None
        self.db_instance_details = None
        self.db_config_tab = None
        self.instance_name = None
        self.pg_cluster_object = None
        self.tcinputs = {
            "nodes": None,
            "plan": None,
            "cluster_bin": None,
            "cluster_conf": None
        }
        self.database_list = None
        self.master_node = None
        self.master_db_object = None
        self.cluster_instance = None
        self.db_map_after_restore = None
        self.db_map_before_backup = None
        self.cluster_subclient = None
        self.cluster_backupset = None
        self.jobs = {}
        self.job_list = None

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
        self.instance_name = "efm_test_cluster"
        self.navigator = self.admin_console.navigator
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance_details = PostgreSQLClusterInstanceDetails(self.admin_console)
        master_con_info = {
            'client_name': self.tcinputs['nodes'][0]['server'],
            'instance_name': 'dummy',
            'port': self.tcinputs['nodes'][0]['port'],
            'hostname': self.commcell.clients.get(self.tcinputs['nodes'][0]['server']).client_hostname,
            'user_name': 'postgres',
            'password': self.tcinputs['nodes'][0]['password'],
            'bin_directory': self.tcinputs['nodes'][0]['bin_dir']
        }
        self.master_node = pgsqlhelper.PostgresHelper(self.commcell, connection_info=master_con_info)
        self.master_db_object = database_helper.PostgreSQL(
            self.master_node.postgres_server_url,
            self.master_node.postgres_port,
            self.master_node.postgres_db_user_name,
            self.master_node.postgres_password,
            "postgres")

    @test_step
    def add_instance(self):
        """Add new PostgreSQl CLuster instance"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance.add_postgresql_cluster_instance(
            instance_name=self.instance_name,
            nodes=self.tcinputs['nodes'],
            plan=self.tcinputs['plan'],
            cluster_type="EDB Failover Manager",
            cluster_conf=self.tcinputs['cluster_conf'],
            cluster_bin=self.tcinputs['cluster_bin']
        )
        self.job_list = self.commcell.job_controller.all_jobs(clients_name=self.instance_name)
        self.log.info(f"Found {len(self.job_list)} jobs, wiating for them to finish")
        for job_ids in self.job_list.keys():
            self.log.info(f'waiting for {job_ids} to finish')
            job = cvpysdk.job.Job(self.commcell, job_ids)
            job.wait_for_completion()
            self.log.info(f'{job_ids} Finished')

    @test_step
    def edit_instance(self):
        """Edit DB instance by adding a new node."""
        self.admin_console.driver.refresh()
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
            self.instance_name, self.instance_name
        )
        self.client = self.commcell.clients.get(self.instance_name)
        cluster_instance = self.client.agents.get('postgresql').instances.get(self.instance_name)
        self.pg_cluster_object = pgsqlhelper.PostgresCusterHelper(self.commcell, self.client, cluster_instance)
        self.log.info("Starting instance configuration edit.")
        self.db_instance_details = PostgreSQLClusterInstanceDetails(self.admin_console)

        # Verify and perform move up operation
        nodes_before = self.pg_cluster_object.get_node_priority()
        self.log.debug(f"Nodes before priority change: {nodes_before}")
        self.log.info("Updating node priority.")
        self.db_instance_details.move_cluster_node_up(2)
        nodes_after = self.pg_cluster_object.get_node_priority()
        self.log.debug(f"Nodes after priority change: {nodes_after}")
        if nodes_before == nodes_after:
            raise cvexceptions.CVTestStepFailure("Priority update change failed")
        self.log.info("Node priority updated successfully.")

        # Verify and perform move down operation
        nodes_before = self.pg_cluster_object.get_node_priority()
        self.log.debug(f"Nodes before priority change: {nodes_before}")
        self.log.info("Updating node priority.")
        self.db_instance_details.move_cluster_node_down(1)
        nodes_after = self.pg_cluster_object.get_node_priority()
        self.log.debug(f"Nodes after priority change: {nodes_after}")
        if nodes_before == nodes_after:
            raise cvexceptions.CVTestStepFailure("Priority update change failed")
        self.log.info("Node priority updated successfully.")

        # Verify and perform delete operation
        time.sleep(5)
        self.log.info('waiting for nodes to load')
        nodes_before = self.pg_cluster_object.get_node_priority()
        self.log.debug(f"Nodes before deletion: {nodes_before}")
        self.log.info("Deleting node.")
        self.db_instance_details.delete_cluster_node(2)
        nodes_after = self.pg_cluster_object.get_node_priority()
        self.log.debug(f"Nodes after deletion: {nodes_after}")
        if len(nodes_before) == len(nodes_after):
            raise cvexceptions.CVTestStepFailure("Node deletion failed")
        self.log.info("Node deleted successfully.")

        # Verify and perform add operation
        time.sleep(5)
        self.log.info('waiting for nodes to load')
        node_to_add = {}
        for node in self.tcinputs['nodes']:
            if node['server'] == nodes_before['2']:
                node_to_add = node
        nodes_before = self.pg_cluster_object.get_node_priority()
        self.log.debug(f"Nodes before addition: {nodes_before}")
        self.log.info("Adding new node.")
        self.db_instance_details.add_cluster_node(node_to_add, cluster_bin=self.tcinputs['cluster_bin'],
                                                  cluster_conf=self.tcinputs['cluster_conf'])
        nodes_after = self.pg_cluster_object.get_node_priority()
        self.log.debug(f"Nodes after addition: {nodes_after}")
        if len(nodes_before) == len(nodes_after):
            raise cvexceptions.CVTestStepFailure("Node addition failed")
        self.log.info("New node added successfully.")

    @test_step
    def fs_backup(self, backup_type):
        """
        Helper function for fs based backups
            Args:
                backup_type: full_backup, incr_backup
        """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance.select_instance(DBInstances.Types.POSTGRES, self.instance_name, self.instance_name)
        self.db_instance_details = PostgreSQLClusterInstanceDetails(self.admin_console)
        self.cluster_instance = self.client.agents.get('postgresql').instances.get(self.instance_name)
        self.cluster_subclient = self.cluster_instance.backupsets.get('fsbasedbackupset')
        self.db_instance_details.click_on_entity('FSBasedBackupSet')
        self.log.info("#" * 10 + " Running FSBased Backup " + "#" * 10)
        self.log.info("Running FSBased Backup.")
        self.db_instance_details.click_on_entity('default')
        db_group_page = PostgreSQLSubclient(self.admin_console)
        self.jobs['fs_backup'] = db_group_page.backup(backup_type=backup_type)
        self.wait_for_job_completion(self.jobs['fs_backup'])
        self.log.info("FSbased backup compeleted successfully.")

    @test_step
    def backup_validation(self):
        """
        Validates the backup process for a PostgreSQL Cluster instance.
        Raises:
            cvexceptions.CVTestStepFailure
        """
        cluster_instance = self.client.agents.get('postgresql').instances.get(self.instance_name)
        self.pg_cluster_object = pgsqlhelper.PostgresCusterHelper(self.commcell, self.client, cluster_instance)

        self.log.info("Checking if data backup occurred on standby.")
        if not self.pg_cluster_object.is_data_backup_on_standby(self.jobs['fs_backup']):
            self.log.error('Data phase did not happen from standby during backup.')
            raise cvexceptions.CVTestStepFailure('Data phase happened from master in backup.')

        self.log.info("Data phase verification successful for file system-based backup.")

        self.log.info("Checking if log backup occurred on master.")
        if not self.pg_cluster_object.is_log_backup_on('master', self.jobs['fs_backup']):
            self.log.error('Log phase did not happen from master during backup.')
            raise cvexceptions.CVTestStepFailure('Log phase happened from standby in backup.')

        self.log.info("Log phase verification successful. Validating log deletion on master.")
        if not self.pg_cluster_object.validate_log_delete(self.pg_cluster_object.master_node):
            self.log.error('Log delete not successful on master.')
            raise cvexceptions.CVTestStepFailure('Log delete not successful on master.')

        self.log.info("Log deletion validation successful. Backup process completed without errors.")

    @test_step
    def fs_restore(self, restore_to_entire_cluster, restore_node=None):
        """
        Helper function for fs based restores
            Args:
                restore_to_entire_cluster : bool value to set restore to entire cluster or single node
                restore_node: if restore to single node, value of the node for restore
        """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
            self.instance_name, self.instance_name)
        self.db_instance_details = PostgreSQLClusterInstanceDetails(self.admin_console)
        self.cluster_instance = self.client.agents.get('postgresql').instances.get(self.instance_name)
        self.cluster_subclient = self.cluster_instance.backupsets.get('fsbasedbackupset')
        self.db_instance_details.click_on_entity('FSBasedBackupSet')
        self.cluster_backupset = PostgreSQLBackupset(self.admin_console)
        self.log.info("#" * 10 + "  Running FSBased Restore  " + "#" * 10)
        self.cluster_backupset.access_restore()
        restore_panel = self.cluster_backupset.restore_folders(
            database_type=DBInstances.Types.POSTGRES, all_files=True)
        self.jobs['fs_restore'] = restore_panel.in_place_restore(fsbased_restore=True,
                                                                 cluster_restore=True,
                                                                 cleanup_directories=True,
                                                                 restore_to_entire_cluster=restore_to_entire_cluster,
                                                                 restore_to_client_name=restore_node)
        self.wait_for_job_completion(self.jobs['fs_restore'])
        self.log.info("FSbased restore compeleted successfully.")

    @test_step
    def wait_for_job_completion(self, jobid):
        """ Waits for completion of job and gets the object once job completes
        Args:
            jobid   (str): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise cvexceptions.CVTestStepFailure(f"Failed to run job:{jobid} with error: {job_obj.delay_reason}")
        self.log.info("Successfully finished %s job", jobid)

    @test_step
    def generate_test_data(self):
        """ Generates test data for backup and restore """
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
    def gen_db_map(self, when):
        """
        Generates a map of the cluster's database metadata.

        Args:
            when (str): Specifies whether to generate the map 'before' or 'after' an event (e.g., backup or restore).
        """
        if when == 'before':
            self.log.info("Generating cluster DB info before backup.")
            self.db_map_before_backup = self.master_node.get_metadata()
        elif when == 'after':
            self.log.info("Generating cluster DB info after restore.")
            self.db_map_after_restore = self.master_node.get_metadata()
        else:
            self.log.error(f"Invalid argument for 'when': {when}")
            raise cvexceptions.CVTestStepFailure(f"Invalid argument for 'when': {when}")

    @test_step
    def validate_restore(self):
        """
        Validates that the database metadata before backup and after restore matches.

        Raises:
            cvexceptions.CVTestStepFailure
        """
        self.log.info("Validating DB info before backup and after restore.")
        if not self.master_node.validate_db_info(self.db_map_before_backup, self.db_map_after_restore):
            self.log.error('Database info validation failed: metadata before backup and after restore do not match.')
            raise cvexceptions.CVTestStepFailure('Database info before backup and after restore do not match.')
        self.log.info("Database info validated successfully: metadata matches before backup and after restore.")

    @test_step
    def cluster_mgr_validate(self):
        """
        Validates whether the EDB has started by checking the log backup on the master node.

        Raises:
            cvexceptions.CVTestStepFailure
        """
        try:
            job_id = self.jobs['fs_restore']
            self.log.info("Checking EDB startup for job id %s", job_id)

            node = self.commcell.clients.get(self.pg_cluster_object.master_node)
            log_path = node.log_directory

            lin_machine_object = machine.Machine(node, self.commcell)
            log_path = lin_machine_object.join_path(log_path, 'PostgresRestoreCtrl.log')

            command = f"cat {log_path} | grep {job_id} | grep 'Started Local EFM Agent'"
            self.log.debug("Executing command on client machine: %s", command)

            output = lin_machine_object.execute_command(command)

            if output.exception_message:
                self.log.error("Error executing command on client machine: %s", output.exception_message)
                raise cvexceptions.CVTestStepFailure("Unable to run the command on client machine")

            if str(job_id) in output.formatted_output:
                self.log.info("EDB startup confirmed for job id %s", job_id)
            else:
                self.log.info("EDB startup not found for job id %s", job_id)

        except Exception as e:
            self.log.error("Error checking EDB startup: %s", str(e))
            raise cvexceptions.CVTestStepFailure

    @test_step
    def cleanup_master(self):
        """
        Cleans up test data from the master database.
        """
        self.log.info("Cleaning up test data from master database.")
        self.master_node.cleanup_test_data(self.database_list)
        self.log.info("Test data cleanup complete.")

    @test_step
    def delete_instance(self):
        """
        Deletes the PostgreSQL Cluster instance if it exists.
        """
        try:
            self.log.info("Navigating to database instances.")
            self.navigator.navigate_to_db_instances()

            if self.db_instance.is_instance_exists(DBInstances.Types.POSTGRES, self.instance_name, self.instance_name):
                self.log.info("Instance %s exists. Proceeding to delete.", self.instance_name)
                self.db_instance.select_instance(DBInstances.Types.POSTGRES, self.instance_name, self.instance_name)
                PostgreSQLClusterInstanceDetails(self.admin_console).delete_instance()
                self.log.info("Instance %s deleted successfully.", self.instance_name)
            else:
                self.log.info("Instance %s does not exist.", self.instance_name)

        except Exception as e:
            self.log.error("Error deleting instance %s: %s", self.instance_name, str(e))
            raise

    def run(self):
        """Run function of this test case"""
        try:
            self.add_instance()
            self.edit_instance()
            self.generate_test_data()
            self.gen_db_list()
            self.gen_db_map('before')
            self.fs_backup(RBackup.BackupType.FULL)
            self.backup_validation()
            self.cleanup_master()
            self.fs_restore(restore_to_entire_cluster=True)
            self.gen_db_map('after')
            self.validate_restore()
            self.cluster_mgr_validate()
        except Exception:
            raise cvexceptions.CVWebAutomationException('Test case failed')

    def tear_down(self):
        """Tear Down function of this test case"""
        self.delete_instance()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
