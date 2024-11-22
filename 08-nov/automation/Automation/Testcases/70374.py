# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
ACC test case for PostgreSQL cluster native replication

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    dump_backup()   --  run dump based backups

    dump_restore(db_list)   --  run dump based restore

    dump_backup_verification() -- verify the dump-based backup process

    fs_backup(backup_type) -- run fs based backups

    fs_restore(db_list, restore_to_entire_cluster, restore_node) -- run fs based restores

    fs_backup_verification(archive_mode) -- verify the file system-based backup process

    copy_files(from, dest) -- copy postgres conf files to the given folder

    wait_for_job_completion(jobid)   -- wait for entered jobid to be complete

    generate_test_data()    -- Generates test data for backup and restore

    shutdown_and_restart_cluster() -- shutdown and restart PostgreSQL cluster nodes

    update_conf(attribute, value) -- update PostgreSQL configuration file with the given attribute and value

    gen_db_list() -- generate a list of databases containing 'auto_full_dmp'

    gen_db_map(when) -- generate a database map before or after backup

    validate_restore() -- validate database information before backup and after restore

    cleanup_master() -- cleanup test data from the master node

    run()           --  run function of this test case

    tear_down()     -- tear down function of the test case

Input Example:
    "testCases":
        {
            "70374": {
                    "ClientName" : Postgres cluster client name
                    }
        }
"""

import random
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import database_helper
from AutomationUtils import machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure
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
        self.name = "ACC test case for postgresql cluster native replication"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_instance = None
        self.db_instance_details = None
        self.pg_cluster_object = None
        self.pg_cluster_instance = None
        self.tcinputs = {
            "ClientName": None
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
        self.db_map_after_restore = None
        self.db_map_before_backup = None
        self.full_backup = None
        self.incr_backup = None
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
        self.log.info('Running a FS Backup to update node priority in csdb')
        self.fs_backup(RBackup.BackupType.FULL)
        self.cluster_nodes = self.pg_cluster_object.get_node_priority()
        if len(self.cluster_nodes) <= 2:
            self.log.error("Less than 3 nodes, provide another node.")
            raise Exception("Less than 3 nodes, provide another node")
        self.cluster_data = self.pg_cluster_object.get_node_data()
        for i in self.cluster_nodes.keys():
            self.log.debug(f'generating postgres helper objects for {self.cluster_nodes[i]}')
            con_info = {
                'client_name': self.cluster_nodes[i],
                'instance_name': 'dummy',
                'port': self.cluster_data[self.cluster_nodes[i]]['port'],
                'hostname': self.commcell.clients.get(self.cluster_nodes['0']).client_hostname,
                'user_name': self.cluster_data[self.cluster_nodes[i]]['sa_user'],
                'password': self.cluster_data[self.cluster_nodes[i]]['sa_password'],
                'bin_directory': self.cluster_data[self.cluster_nodes[i]]['binary_file_path']
            }
            self.cluster_pg_objects[i] = pgsqlhelper.PostgresHelper(self.commcell, connection_info=con_info)
            self.log.debug('pghelper object generation successful')
        self.master_node = self.cluster_pg_objects['0']
        self.master_db_object = database_helper.PostgreSQL(
            self.master_node.postgres_server_url,
            self.master_node.postgres_port,
            self.master_node.postgres_db_user_name,
            self.master_node.postgres_password,
            "postgres")
        self.full_backup = RBackup.BackupType.FULL
        self.incr_backup = RBackup.BackupType.INCR

    @test_step
    def dump_based_backup(self):
        """
        Helper function for dump based backups
        """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['ClientName'], self.tcinputs['ClientName'])
        self.db_instance_details = PostgreSQLClusterInstanceDetails(self.admin_console)
        self.cluster_instance = self.client.agents.get('postgresql').instances.get(self.tcinputs['ClientName'])
        self.cluster_subclient = self.cluster_instance.backupsets.get('dumpbasedbackupset')
        self.db_instance_details.click_on_entity('DumpBasedBackupSet')
        self.log.info("#" * 10 + "  DumpBased Backup Operations  " + "#" * 10)
        self.log.info("Running DumpBased Backup.")
        self.db_instance_details.click_on_entity('default')
        db_group_page = PostgreSQLSubclient(self.admin_console)
        self.jobs['dump_backup'] = db_group_page.backup(backup_type=self.full_backup)
        self.wait_for_job_completion(self.jobs['dump_backup'])
        self.log.info("Dumpbased backup compeleted successfully.")

    @test_step
    def dump_based_restore(self, db_list):
        """
         Helper function for Dump based restores
            Args:
                db_list: list of databses created to restore
        """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['ClientName'], self.tcinputs['ClientName'])
        self.db_instance_details = PostgreSQLClusterInstanceDetails(self.admin_console)
        self.cluster_instance = self.client.agents.get('postgresql').instances.get(self.tcinputs['ClientName'])
        self.cluster_subclient = self.cluster_instance.backupsets.get('dumpbasedbackupset')
        self.cluster_backupset = PostgreSQLBackupset(self.admin_console)
        self.log.info("#" * 10 + "  Running DumpBasedBackupSet Restore  " + "#" * 10)
        self.cluster_backupset.access_restore()
        restore_panel = self.cluster_backupset.restore_folders(
            database_type=DBInstances.Types.POSTGRES, items_to_restore=db_list)
        self.jobs['dump_restore'] = restore_panel.in_place_restore()
        self.wait_for_job_completion(self.jobs['dump_restore'])
        self.log.info("Dumpbased restore compeleted successfully.")

    @test_step
    def dump_backup_verification(self):
        """
        Verifies that the data backup for a dump-based backup occurred on the standby node.

        Raises:
            RuntimeError: If the data backup phase did not happen on the standby node.
        """
        self.log.info("Checking if data backup happened on standby.")
        if not self.pg_cluster_object.is_data_backup_on_standby(self.jobs['dump_backup']):
            self.log.error('Data phase did not happen from standby during dump-based backup.')
            raise RuntimeError('Data phase happened from master in dump backup.')

        self.log.info("Data phase verification successful for dump-based backup.")

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
        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['ClientName'], self.tcinputs['ClientName'])
        self.db_instance_details = PostgreSQLClusterInstanceDetails(self.admin_console)
        self.cluster_instance = self.client.agents.get('postgresql').instances.get(self.tcinputs['ClientName'])
        self.cluster_subclient = self.cluster_instance.backupsets.get('fsbasedbackupset')
        self.db_instance_details.click_on_entity('FSBasedBackupSet')
        self.log.info("#" * 10 + " Running FSBased Backup " + "#" * 10)
        self.log.info("Running FSBased Backup.")
        self.db_instance_details.click_on_entity('default')
        db_group_page = PostgreSQLSubclient(self.admin_console)
        self.jobs[f'fs_backup'] = db_group_page.backup(backup_type=backup_type)
        self.wait_for_job_completion(self.jobs[f'fs_backup'])
        self.log.info("FSbased backup compeleted successfully.")

    @test_step
    def fs_restore(self, restore_to_entire_cluster, restore_node=None):
        """
        Helper function for fs based restores
            Args:
                restore_to_entire_cluster : bool value to set restore to entire cluster or single node
                restore_node: if restore to single node, value of the node for restore
        """
        if restore_to_entire_cluster:
            self.log.info("Starting cluster-wide file system restore.")
        else:
            self.log.info("Starting single node file system restore.")
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['ClientName'], self.tcinputs['ClientName'])
        self.db_instance_details = PostgreSQLClusterInstanceDetails(self.admin_console)
        self.cluster_instance = self.client.agents.get('postgresql').instances.get(self.tcinputs['ClientName'])
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

    def fs_backup_verification(self, archive_mode):
        """
        Verifies the backup process based on the archive mode.

        Args:
            archive_mode (str): The archive mode of the PostgreSQL cluster ('on' or 'always').

        Raises:
            RuntimeError: If any phase of the backup process fails.
            ValueError: If an invalid archive mode is provided.
        """
        if archive_mode == 'on':
            self.log.info("Checking if data backup occurred on standby.")
            if not self.pg_cluster_object.is_data_backup_on_standby(self.jobs['fs_backup']):
                self.log.error('Data phase did not happen from standby during backup.')
                raise RuntimeError('Data phase happened from master in backup.')

            self.log.info("Data phase verification successful for file system-based backup.")

            self.log.info("Checking if log backup occurred on master.")
            if not self.pg_cluster_object.is_log_backup_on('master', self.jobs['fs_backup']):
                self.log.error('Log phase did not happen from master during backup.')
                raise RuntimeError('Log phase happened from standby in backup.')

            self.log.info("Log phase verification successful. Validating log deletion on master.")
            if not self.pg_cluster_object.validate_log_delete(self.cluster_nodes['0']):
                self.log.error('Log delete not successful on master.')
                raise RuntimeError('Log delete not successful on master.')

            self.log.info("Log deletion validation successful. Backup process completed without errors.")

        elif archive_mode == 'always':
            self.log.info("Checking if log backup occurred on standby.")
            if not self.pg_cluster_object.is_log_backup_on('standby', self.jobs['fs_backup']):
                self.log.error('Log phase did not happen from standby during log backup.')
                raise RuntimeError('Log phase happened from master in log backup.')

            self.log.info("Log phase verification successful for log backup. Validating log deletion on all nodes.")
            for node in self.cluster_nodes.values():
                if not self.pg_cluster_object.validate_log_delete(node):
                    self.log.error(f'Log delete not successful on node {node.client_name}.')
                    raise RuntimeError(f'Log delete not successful on node {node.client_name}.')

            self.log.info(
                "Log deletion validation successful on all nodes. Log backup process completed without errors.")
        else:
            self.log.error(f'Invalid archive mode provided: {archive_mode}.')
            raise ValueError(f'Invalid archive mode: {archive_mode}.')

    @test_step
    def copy_files(self, from_dir, destination_dir):
        """
        Copy conf file from data folder to temp and vice versa
            Args:
                from_dir (str) : temp (temp folder), data_dir (postgres data folder)
                destination_dir (str) : temp (temp folder), data_dir (postgres data folder)
        """
        for node in self.cluster_nodes.values():
            data_dir = self.cluster_data[node]['data_dir']
            machine_object = machine.Machine(self.commcell.clients.get(self.cluster_nodes['0']))

            temp = '/tmp'

            if from_dir == 'data_dir' and destination_dir == 'temp':
                query = f'cp {data_dir}/*.conf {temp}'
                self.log.info(f"Executing command: {query}")
                machine_object.execute(query)
            elif from_dir == 'temp' and destination_dir == 'data_dir':
                query = f'cp {temp}/*.conf {data_dir}'
                self.log.info(f"Executing command: {query}")
                machine_object.execute(query)

    @test_step
    def wait_for_job_completion(self, jobid):
        """ Waits for completion of job and gets the object once job completes
        Args:
            jobid   (str): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(f"Failed to run job:{jobid} with error: {job_obj.delay_reason}")
        self.log.info("Successfully finished %s job", jobid)

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
    def shutdown_and_restart_cluster(self):
        """Shuts down and restarts the PostgreSQL cluster's nodes."""
        for i, node in self.cluster_pg_objects.items():
            bin_path = self.cluster_data[self.cluster_nodes[i]]['binary_file_path']
            data_path = self.cluster_data[self.cluster_nodes[i]]['data_dir']
            if not node.get_postgres_status(bin_path, data_path):
                self.log.info(f"PostgreSQL server {node} is not running. Starting server...")
                node.start_postgres_server(bin_path, data_path)
            else:
                self.log.info(f"PostgreSQL server on node {i} is running. Restarting server...")
                node.stop_postgres_server(bin_path, data_path)
                node.start_postgres_server(bin_path, data_path)
            self.log.info(f"PostgreSQL server {node} restarted successfully.")

    @test_step
    def update_conf(self, attribute, value):
        """
        Updates the configuration file for each node in the cluster.

        Args:
            attribute (str): The configuration attribute to update.
            value (str): The value to set for the configuration attribute.
        """
        self.log.info(f"Starting configuration update to set {attribute} to '{value}'.")
        for node in self.cluster_nodes.values():
            self.pg_cluster_object.update_conf_file(node, attribute, value)
            self.log.info(f"Configuration update complete for node {node}.")

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
            raise ValueError(f"Invalid argument for 'when': {when}")

    @test_step
    def validate_restore(self):
        """
        Validates that the database metadata before backup and after restore matches.

        Raises:
            DatabaseRestoreValidationException: If the metadata before backup and after restore do not match.
        """
        self.log.info("Validating DB info before backup and after restore.")
        if not self.master_node.validate_db_info(self.db_map_before_backup, self.db_map_after_restore):
            self.log.error('Database info validation failed: metadata before backup and after restore do not match.')
            raise ValueError('Database info before backup and after restore do not match.')
        self.log.info("Database info validated successfully: metadata matches before backup and after restore.")

    @test_step
    def cleanup_master(self):
        """
        Cleans up test data from the master database.
        """
        self.log.info("Cleaning up test data from master database.")
        self.master_node.cleanup_test_data(self.database_list)
        self.log.info("Test data cleanup complete.")

    def run(self):
        """Run function of this test case"""
        try:
            ############### Dump-Based Backup and Restore ###############
            self.generate_test_data()
            self.gen_db_list()
            self.gen_db_map('before')
            self.dump_based_backup()
            self.dump_based_restore(self.database_list)
            self.gen_db_map('after')
            self.validate_restore()
            self.cleanup_master()

            ############ File System-Based Backup ###############
            ############### Archive mode = on
            self.update_conf('archive_mode', 'on')
            self.shutdown_and_restart_cluster()
            self.generate_test_data()
            self.gen_db_list()
            self.gen_db_map('before')
            self.fs_backup(self.full_backup)
            self.fs_backup_verification('on')

            ############### Archive mode = always
            self.update_conf('archive_mode', 'always')
            self.shutdown_and_restart_cluster()
            self.fs_backup(self.incr_backup)
            self.fs_backup_verification('always')
            self.cleanup_master()

            ############## File System-Based Restore ###############
            ############## Single node
            self.copy_files('data_dir', 'temp')
            self.fs_restore(False, self.pg_cluster_object.get_master_node())
            self.gen_db_map('after')
            self.validate_restore()

            ############### Cluster
            self.copy_files('temp', 'data_dir')
            self.fs_restore(restore_to_entire_cluster=True)
            self.gen_db_map('after')
            self.validate_restore()

        except Exception as e:
            self.log.error(f'An error occurred during execution: {e}')
            raise

    def tear_down(self):
        """Tear Down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
