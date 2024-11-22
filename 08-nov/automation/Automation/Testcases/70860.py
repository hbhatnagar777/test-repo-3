# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
ACC test case for PostgreSQL cluster failover

TestCase:   Class for executing this test case

TestCase:

    __init__() -- initialize TestCase class

    setup() -- setup the requirements for the test case

    change_use_master_option(enable=True) -- enable or disable the use master option

    toggle_server(server, action='stop') -- change server status

    get_job_status(job_id) -- fetch the job status

    backup_validation() -- validate backup process

    fs_backup(backup_type) -- run file system-based backups

    job_restore(job_id, destination=None) -- restore a job to the specified destination

    restore_from_instance() -- restore from a database instance to the cluster

    redirect_validation() -- validate the success of a redirect restore on all cluster nodes

    pg_rewind_validation() -- validate the success of pg_rewind

    promote_standby() -- promote the standby server to the primary server

    old_master_to_standby() -- convert the old master server to a standby server

    copy_files(from_dir, destination_dir) -- copy configuration files from data folder to temp and vice versa

    clean_temp() -- remove temporary directories on all cluster nodes

    wait_for_job_completion(jobid) -- wait for job completion

    generate_test_data() -- generate test data for backup and restore

    gen_db_list() -- generate a list of databases containing 'auto_full_dmp'

    gen_db_map(when) -- generate a map of the cluster's database metadata

    validate_restore() -- validate database information before backup and after restore

    cleanup_master() -- clean up test data from the master database

    run() -- run function of this test case

    tear_down() -- tear down function of the test case


Input Example:
    "testCases":
        {
            "70860": {
                    "ClientName" : Postgres cluster client name
                    }
        }
"""

import random
import time

from cvpysdk.job import Job

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import database_helper
from AutomationUtils import machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
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
        self.name = "ACC test case for postgresql cluster failover"
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
        self.master_node_pg_object = None
        self.cluster_instance = None
        self.cluster_subclient = None
        self.cluster_pg_objects = {}
        self.cluster_backupset = None
        self.jobs_page = None
        self.db_map_after_restore = None
        self.db_map_before_backup = None
        self.full_backup = None
        self.incr_backup = None
        self.promote = False
        self.jobs = dict()
        self.job = None
        self.job_run = None
        self.first_backup = None

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
        self.job = Jobs(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.pg_cluster_instance = self.client.agents.get('postgresql').instances.get(self.tcinputs['ClientName'])
        self.pg_cluster_object = pgsqlhelper.PostgresCusterHelper(self.commcell, self.client, self.pg_cluster_instance)
        self.db_instance_details = PostgreSQLClusterInstanceDetails(self.admin_console)
        self.cluster_nodes = self.pg_cluster_object.nodes
        self.cluster_data = self.pg_cluster_object.node_data

        for i in self.cluster_nodes.keys():
            self.log.debug(f'generating postgres helper objects for {self.cluster_nodes[i]}')
            con_info = {
                'client_name': self.cluster_nodes[i],
                'instance_name': 'dummy',
                'port': self.cluster_data[self.cluster_nodes[i]]['port'],
                'hostname': self.commcell.clients.get(self.cluster_nodes[i]).client_hostname,
                'user_name': self.cluster_data[self.cluster_nodes[i]]['sa_user'],
                'password': self.cluster_data[self.cluster_nodes[i]]['sa_password'],
                'bin_directory': self.cluster_data[self.cluster_nodes[i]]['binary_file_path']
            }
            self.cluster_pg_objects[self.cluster_nodes[i]] = pgsqlhelper.PostgresHelper(self.commcell,
                                                                                        connection_info=con_info)
            self.log.debug('pghelper object generation successful')
        self.master_node = self.pg_cluster_object.master_node
        self.master_node_pg_object = self.cluster_pg_objects[self.master_node]
        self.full_backup = RBackup.BackupType.FULL
        self.incr_backup = RBackup.BackupType.INCR
        self.job_run = 0

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

    @test_step
    def toggle_server(self, server, action='stop'):
        """
        Changes server status
        Args:
            server : name of the server
            action : start/stop/restart tje server (default:stop)
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
    def get_job_status(self, job_id):
        """
        Fetched the job status
        Args:
            job_id (int) : id of the job for which the status is to be fetched
        Returns:
            Failed/Success
        Raises:
            CVTestStepFailure : if job not found
        """
        status = self.job.get_job_status(job_id)
        if 'FAILED' in status.upper():

            return 'Failed'
        elif 'SUCCESS' in status.upper():
            return 'Success'
        elif status is False:
            raise CVTestStepFailure(f"Could not find job with id {job_id}")

    @test_step
    def backup_validation(self):
        """validate backup process"""
        if not self.promote:
            self.navigator.navigate_to_db_instances()
            self.admin_console.wait_for_completion()
            self.db_instance = DBInstances(self.admin_console)
            self.db_instance.select_instance(
                DBInstances.Types.POSTGRES,
                self.tcinputs['ClientName'], self.tcinputs['ClientName'])
            self.db_instance_details = PostgreSQLClusterInstanceDetails(self.admin_console)
            if self.db_instance_details.master_if_standby_unavailable == 'False':
                self.log.info("Checking if backup failed because of no standby available")
                if not self.cluster_pg_objects[self.cluster_nodes['1']].get_postgres_status(
                        self.cluster_data[self.cluster_nodes['1']]["binary_file_path"],
                        self.cluster_data[self.cluster_nodes['1']]["data_dir"]):
                    if self.wait_for_job_completion(self.jobs['fs_backup']):
                        self.log.error("backup happened from master when use master option disabled")
                        raise CVTestStepFailure("BACKUP NOT FAILED")
            else:
                self.log.info("Checking if data backup occurred on master.")
                if not self.pg_cluster_object.is_log_backup_on('master', self.jobs['fs_backup']):
                    self.log.error('Data phase did not happen from standby during backup.')
                    raise CVTestStepFailure('Data phase happened from master in backup.')
        else:
            node = self.commcell.clients.get(self.master_node)
            log_path = node.log_directory
            lin_machine_object = machine.Machine(node, self.commcell)
            log_path = lin_machine_object.join_path(log_path, 'PostGresLogBackupParent.log')
            command = f"cat {log_path} | grep {self.jobs['fs_backup']} | grep 'Upgrading backup level'"
            self.log.info("checking if log backup converted to full on new master")
            output = lin_machine_object.execute_command(command)
            if output.exception_message == '':
                self.log.error("Error in standby promotion")
                raise CVTestStepFailure("Log backup not converted to full")
            if str(self.jobs['fs_backup']) in output.formatted_output:
                self.log.info("Log backup converted to full")

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
        self.cluster_instance = self.client.agents.get('postgresql').instances.get(self.tcinputs['ClientName'])
        self.cluster_subclient = self.cluster_instance.backupsets.get('fsbasedbackupset')
        self.db_instance_details.click_on_entity('FSBasedBackupSet')
        self.log.info("#" * 10 + " Running FSBased Backup " + "#" * 10)
        self.log.info("Running FSBased Backup.")
        self.db_instance_details.click_on_entity('default')
        db_group_page = PostgreSQLSubclient(self.admin_console)
        self.jobs[f'fs_backup'] = db_group_page.backup(backup_type=backup_type)
        if self.job_run == 1:
            self.first_backup = self.jobs['fs_backup']
        self.job_run += 1
        self.wait_for_job_completion(self.jobs['fs_backup'])

    @test_step
    def job_restore(self, job_id):
        """
        Restores a job to the specified destination.

        Args:
            job_id (str): ID of the job to be restored.
        """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['ClientName'], self.tcinputs['ClientName'])
        self.cluster_instance = self.client.agents.get('postgresql').instances.get(self.tcinputs['ClientName'])
        self.cluster_subclient = self.cluster_instance.backupsets.get('fsbasedbackupset')
        self.db_instance_details.click_on_entity('FSBasedBackupSet')
        self.cluster_backupset = PostgreSQLBackupset(self.admin_console)
        self.cluster_backupset.list_backup_history()
        self.job.job_restore(job_id)
        restore_panel = self.cluster_backupset.restore_folders(database_type=DBInstances.Types.POSTGRES, all_files=True)
        redirect_entries = {}
        for nodes in self.cluster_nodes.values():
            node = (nodes, self.commcell.clients.get(nodes).client_id)
            redirect_entries[node] = (f"{self.cluster_data[nodes]['data_dir']}", f'/tmp/{self.tcinputs["ClientName"]}')
        self.jobs['fs_job_restore'] = restore_panel.in_place_restore(fsbased_restore=True, cluster_restore=True,
                                                                     redirect_values=redirect_entries,
                                                                     cleanup_directories=True)
        self.job_run += 1
        self.wait_for_job_completion(self.jobs['fs_job_restore'])

    @test_step
    def restore_from_instance(self):
        """
        Restores from a database instance to the cluster.
        """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance.access_restore(self.tcinputs['ClientName'])
        restore_dialog = RModalDialog(self.admin_console, title="Restore")
        restore_dialog.select_checkbox(checkbox_label="FSBasedBackupSet")
        restore_dialog.click_submit()
        self.cluster_backupset = PostgreSQLBackupset(self.admin_console)
        restore_panel = self.cluster_backupset.restore_folders(database_type=DBInstances.Types.POSTGRES, all_files=True)
        redirect_entries = {}
        for nodes in self.cluster_nodes.values():
            node = (nodes, self.commcell.clients.get(nodes).client_id)
            redirect_entries[node] = (f'/tmp/{self.tcinputs["ClientName"]}', f"{self.cluster_data[nodes]['data_dir']}")
        self.jobs['fs_instance_restore'] = restore_panel.in_place_restore(fsbased_restore=True, cluster_restore=True,
                                                                          redirect_values=redirect_entries)
        self.job_run += 1
        self.wait_for_job_completion(self.jobs['fs_instance_restore'])

    @test_step
    def redirect_validation(self):
        """
        Validates the success of a redirect restore
        """
        machine_object = machine.Machine(self.commcell.clients.get(self.master_node))
        query = f"su postgres -c 'pg_ctl -D /tmp/{self.tcinputs['ClientName']} status'"
        output = machine_object.execute(query)
        if "server is running" not in output.formatted_output:
            raise CVTestStepFailure(f'Redirect restore failed on {self.master_node}')

    @test_step
    def pg_rewind_validation(self):
        """
        Validates the success of pg_rewind by checking the log file.
        """
        node = self.commcell.clients.get(self.pg_cluster_object.master_node)
        lin_machine_object = machine.Machine(node)
        log_path = node.log_directory
        log_path = lin_machine_object.join_path(log_path, 'PostgresRestoreCtrl.log')
        command = f"cat {log_path} | grep {self.jobs['fs_job_restore']} | grep 'pg_rewind: connected to server'"
        output = lin_machine_object.execute_command(command)
        if output.exception_message != '':
            raise CVTestStepFailure("Error in pg_rewind")
        if str(self.jobs['fs_job_restore']) in output.formatted_output:
            self.log.info("pg_rewind successful")

    @test_step
    def promote_standby(self):
        """
        Promotes the standby server to the primary server.
        """
        node = self.cluster_nodes['1']
        postgres_database_object = database_helper.PostgreSQL(
            self.commcell.clients.get(node).client_hostname,
            self.cluster_data[node]['port'],
            self.cluster_data[node]['sa_user'],
            self.cluster_data[node]['sa_password'],
            "postgres"
        )
        query = "select pg_promote();"
        result = postgres_database_object.execute(query)
        if not result.rows[0][0]:
            self.log.error("Could not promote the standby server")
            raise CVTestStepFailure('Failover error')
        else:
            query = "select pg_is_in_recovery();"
            result = postgres_database_object.execute(query)
            if result.rows[0][0]:
                self.log.error("Could not promote the standby server")
                raise CVTestStepFailure('Failover error')
        self.log.info(f"Promotion successfully done, {node} is now master")
        self.promote = True
        self.master_node = self.cluster_nodes['1']
        self.master_node_pg_object = self.cluster_pg_objects[self.master_node]

    @test_step
    def old_master_to_standby(self):
        """
        Converts the old master server to a standby server.
        """
        node = self.cluster_nodes['0']
        lin_machine_object = machine.Machine(node, self._commcell)
        command = f'su - postgres -c "rm -rf {self.cluster_data[node]["data_dir"]}/*"'
        self.log.info(f'executing {command}')
        lin_machine_object.execute_command(command)
        command = (f'su - postgres -c "pg_basebackup '
                   f'-h {self.commcell.clients.get(self.cluster_nodes["1"]).client_hostname} '
                   f'-p {self.cluster_data[node]["port"]} -D {self.cluster_data[node]["data_dir"]} -Xs -R -v -P"')
        self.log.info(f'executing {command}')
        lin_machine_object.execute_command(command)
        time.sleep(120)
        self.log.info("Waiting for replication to setup")
        self.toggle_server(server=node, action='start')

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
            machine_object = machine.Machine(self.commcell.clients.get(node))

            temp = f'/tmp/{self.tcinputs["ClientName"]}'
            query = f'mkdir {temp} && chown postgres:postgres {temp} && chmod 700 {temp}'
            self.log.info(f"making temp directory {temp} in {node}")
            machine_object.execute(query)

            if from_dir == 'data_dir' and destination_dir == 'temp':
                query = f'cp {data_dir}/*.conf {temp}'
                self.log.info(f"Executing command: {query} in {node}")
                machine_object.execute(query)
            elif from_dir == 'temp' and destination_dir == 'data_dir':
                query = f'cp {temp}/*.conf {data_dir}'
                self.log.info(f"Executing command: {query} in {node}")
                machine_object.execute(query)

    @test_step
    def clean_temp(self):
        """
        Removes temporary directories on all cluster nodes.
        """
        for node in self.cluster_nodes.values():
            machine_object = machine.Machine(self.commcell.clients.get(node))
            temp = f'/tmp/{self.tcinputs["ClientName"]}'
            query = f'rm -rf {temp}'
            self.log.info(f"Removing temp directory {temp} on {node}")
            machine_object.execute(query)

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
    def generate_test_data(self, node):
        """ Generates test data for backup and restore """
        self.log.info(f"Populating {node} with random data.")
        db_prefix = "auto_full_dmp"
        self.log.info("Generating Test Data")
        self.cluster_pg_objects[node].generate_test_data(
            self.cluster_pg_objects[node].postgres_server_url,
            random.randint(3, 10),
            random.randint(3, 10),
            random.randint(3, 10),
            self.cluster_pg_objects[node].postgres_port,
            self.cluster_pg_objects[node].postgres_db_user_name,
            self.cluster_pg_objects[node].postgres_password,
            True,
            db_prefix)
        self.log.info("Successfully generated Test Data.")

    @test_step
    def gen_db_list(self, node):
        """
        Generates a list of databases containing 'auto_full_dmp' in their name from the master database.
        """
        self.log.info("Generating list of databases containing 'auto_full_dmp'.")
        self.database_list = []
        db_object = database_helper.PostgreSQL(
            self.cluster_pg_objects[node].postgres_server_url,
            self.cluster_pg_objects[node].postgres_port,
            self.cluster_pg_objects[node].postgres_db_user_name,
            self.cluster_pg_objects[node].postgres_password,
            "postgres")
        db_list = db_object.get_db_list()
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
            self.db_map_before_backup = self.master_node_pg_object.get_metadata()
        elif when == 'after':
            self.log.info("Generating cluster DB info after restore.")
            self.db_map_after_restore = self.master_node_pg_object.get_metadata()
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
        if not self.master_node_pg_object.validate_db_info(self.db_map_before_backup, self.db_map_after_restore):
            self.log.error('Database info validation failed: metadata before backup and after restore do not match.')
            raise ValueError('Database info before backup and after restore do not match.')
        self.log.info("Database info validated successfully: metadata matches before backup and after restore.")

    @test_step
    def cleanup_master(self):
        """
        Cleans up test data from the master database.
        """
        self.log.info("Cleaning up test data from master database.")
        self.master_node_pg_object.cleanup_test_data(self.database_list)
        self.log.info("Test data cleanup complete.")

    def run(self):
        """Run function of this test case"""
        try:
            self.change_use_master_option(enable=False)
            self.toggle_server(server=self.cluster_nodes['1'])
            self.fs_backup(self.full_backup)
            self.backup_validation()
            self.change_use_master_option(enable=True)
            self.fs_backup(self.full_backup)
            self.backup_validation()
            self.toggle_server(server=self.cluster_nodes['1'], action='start')
            self.toggle_server(server=self.cluster_nodes['0'])
            self.promote_standby()
            self.generate_test_data(self.master_node)
            self.gen_db_list(self.master_node)
            self.gen_db_map('before')
            self.fs_backup(self.incr_backup)
            self.backup_validation()
            self.old_master_to_standby()
            self.copy_files('data_dir', 'temp')
            self.job_restore(self.first_backup)
            self.gen_db_map('after')
            self.validate_restore()
            self.pg_rewind_validation()
            self.redirect_validation()
            self.copy_files(from_dir='temp', destination_dir='data_dir')
            self.restore_from_instance()

        except Exception as e:
            self.log.error(f'An error occurred during execution: {e}')
            raise

    def tear_down(self):
        """Tear Down function of this test case"""
        self.cleanup_master()
        self.clean_temp()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
