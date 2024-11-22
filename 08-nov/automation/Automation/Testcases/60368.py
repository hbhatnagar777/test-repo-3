# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
"60368": {
            "ClientName": "test_client",
            "AgentName": "DB2",
            "instance_name": "dummy_inst",
            "plan": "Storage Plan Name",
            "snap_path": "Snap Mounted Path",
            "db2_username": "dummy_user",
            "db2_user_password": "dummy_passwd",
            "credential_name": "cred_name"
        }

TestCase: Class for executing this test case

TestCase:
    __init__()                              --  initialize TestCase class

    setup()                                 --  setup the parameters and common object necessary

    run()                                   --  run function of this test case

    recreate_database_paths()               --  recreates snap paths

    create_database()                       --  Creates database on client

    delete_database_directory()             --   Cleaning out existing destination database

    remove_existing_logs_dir()              --   Removes existing log staging directory for destination database

    drop_database_on_client()               --  Drops database on client

    get_home_path()                         --  Gets instance home path

    delete_db2_instance()                   --  Deletes Existing instance on Command Center

    navigate_to_instance_details()          --  Navigates to Instance Details page

    run_backup()                            --  Runs a backup

    run_restore()                           --  Runs a restore

    verify_restore_history()                --  Verifies if restore job happened as expected on client

    tear_down()                             --  Tear down method to cleanup the entities
"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import Db2InstanceDetails
from Web.AdminConsole.Databases.backupset import DB2Backupset
from Web.AdminConsole.Databases.subclient import DB2Subclient
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Database.DB2Utils.db2helper import DB2
from Web.AdminConsole.Components.page_container import PageContainer

class TestCase(CVTestCase):
    """ Command center: Verify Snap Restore uses correct backup job in case of Mixed Backups. """

    test_step = TestStep()

    def __init__(self):
        """Initial configs for test case"""
        super(TestCase, self).__init__()
        self.name = "DB2 Verify Snap Restore uses correct backup job in case of Mixed Backups"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.dbtype = None
        self.db_instance = None
        self.db_instance_details = None
        self.db_backupset = None
        self.db_subclient = None
        self.instance = None
        self.backupset = None
        self.snap_subclient = None
        self.jobs_page = None
        self.database1 = None
        self.database2 = None
        self.client_displayname = None
        self.page_container = None
        self.tcinputs = {
            "instance_name": None,
            "plan": None,
            "snap_path": None,
            "db2_username": None,
            "db2_user_password": None,
            "credential_name": None
        }

    def setup(self):
        """ Must needed setups for test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            self.admin_console.login(username=self.inputJSONnode['commcell']["commcellUsername"],
                                     password=self.inputJSONnode['commcell']["commcellPassword"])

            self.navigator = self.admin_console.navigator
            self.db_instance = DBInstances(admin_console=self.admin_console)
            self.db_instance_details = Db2InstanceDetails(admin_console=self.admin_console)
            self.db_backupset = DB2Backupset(admin_console=self.admin_console)
            self.db_subclient = DB2Subclient(admin_console=self.admin_console)
            self.jobs_page = Jobs(admin_console=self.admin_console)
            self.dbtype = DBInstances.Types.DB2
            self.database1 = "DBSNAP2"
            self.database2 = "DBSNAP3"
            self.src_database_name = f"DB{self.id}"
            self.snap_subclient = f'{self.id}'
            self.client_displayname = self.client.display_name
            self.page_container = PageContainer(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """ Main method to run test case """

        self.prerequisite_setup_test_case()
        self.navigator.navigate_to_db_instances()

        self.db_instance.select_instance(database_type=self.dbtype,
                                         instance_name=self.tcinputs["instance_name"],
                                         client_name=self.client_displayname)

        self.db_instance_details.click_on_entity(entity_name=self.src_database_name)

        self.add_snap_subclient()

        self.commcell.refresh()

        self.instance = self.agent.instances.get(self.tcinputs['instance_name'])
        self.backupset = self.instance.backupsets.get(self.src_database_name)
        self.subclient = self.backupset.subclients.get("default")
        self.snap_subclient = self.backupset.subclients.get(self.snap_subclient)

        self.navigate_to_instance_details()
        self.db2_helper = DB2(commcell=self.commcell,
                              client=self.client,
                              instance=self.instance,
                              backupset=self.backupset)
        self.db2_helper.update_db2_database_configuration1(cold_backup_path='/dev/null')
        self.db2_helper.db2_cold_backup(cold_backup_path="/dev/null",
                                        db_name=self.backupset.name)
        self.db_instance_details.click_on_entity(entity_name=self.backupset.name)
        self.page_container.select_entities_tab()

        traditional_backup_job_id1 = self.run_backup()

        snap_backup_job_id = self.run_backup(backup_type="snap")

        traditional_backup_job_id2 = self.run_backup()

        self.admin_console.refresh_page()

        self.store_backup_info(traditional_backup_ids=[traditional_backup_job_id1, traditional_backup_job_id2])

        self.drop_database_on_client(database_name=self.src_database_name)

        redirect_storage_group_dict = {'IBMSTOGROUP': '{0}/storage1'.format(self.home_path)}

        self.client_machine.create_directory(directory_name=redirect_storage_group_dict["IBMSTOGROUP"],
                                             force_create=True)

        self.page_container.select_overview_tab()
        self.run_restore(job_id=snap_backup_job_id,
                         database_name=self.database1,
                         database_path=self.home_path,
                         roll_forward=False,
                         redirect_sto_grp_path=redirect_storage_group_dict)

        self.verify_restore_history(database=self.database1,
                                    only_one=True)

        self.navigate_to_instance_details()
        self.db_instance_details.click_on_entity(entity_name=self.backupset.name)

        self.drop_database_on_client(database_name=self.database1)

        redirect_storage_group_dict['IBMSTOGROUP'] = '{0}/storage2'.format(self.home_path)
        self.client_machine.create_directory(directory_name=redirect_storage_group_dict["IBMSTOGROUP"],
                                             force_create=True)
        self.run_restore(job_id=traditional_backup_job_id2,
                         database_name=self.database2,
                         database_path=self.home_path,
                         roll_forward=True,
                         redirect_sto_grp_path=redirect_storage_group_dict)

        self.verify_restore_history(database=self.database2)
        self.drop_database_on_client(database_name=self.database2)
        self.recreate_database_paths()

    @test_step
    def prerequisite_setup_test_case(self):
        """ Prerequisite setup for test case """
        path_sep_needed = True if self.tcinputs['snap_path'][-1] != '/' else False
        self.db_dir = f"{self.tcinputs['snap_path']}{'/' if path_sep_needed else ''}db/"
        self.dbpath = f"{self.tcinputs['snap_path']}{'/' if path_sep_needed else ''}dbpath/"

        self.client_machine = Machine(machine_name=self.client.client_hostname,
                                      username=self.tcinputs['db2_username'],
                                      password=self.tcinputs['db2_user_password'])

        self.client_machine_root = Machine(machine_name=self.client.client_hostname,
                                           commcell_object=self.commcell)

        self.log.info("Cleaning up the Client")
        self.drop_database_on_client(database_name=self.database1)
        self.drop_database_on_client(database_name=self.database2)
        self.drop_database_on_client(database_name=self.src_database_name)
        self.create_database(database_name=self.src_database_name)
        self.remove_existing_logs_dir()

        self.navigator.navigate_to_db_instances()
        self.delete_instance()
        self.db_instance.react_instances_table.reload_data()
        self.get_home_path()

        self.discover_instance()
        self.admin_console.refresh_page()
        self.db_instance.react_instances_table.reload_data()

        self.db_instance.select_instance(database_type=self.dbtype,
                                         instance_name=self.tcinputs["instance_name"],
                                         client_name=self.client_displayname)

        self.edit_instance_property()
        self.log.info("Sleeping for 60 seconds to let database discovery run.")
        time.sleep(60)
        self.admin_console.refresh_page()
        self.commcell.refresh()
        self.delete_database()
        self.add_database()

        self.commcell.refresh()
        self.admin_console.refresh_page()

    @test_step
    def drop_database_on_client(self, database_name):
        """
        Drops database on client
        Args:
            database_name (str) -- Name of database to drop
        """
        self.log.info("Dropping database %s on client machine", database_name)

        database_cmd = "db2 force application all"
        self.log.info("Disconnecting database %s from all connections using command: %s", database_name, database_cmd)
        output = self.client_machine.execute_command(command=database_cmd)
        self.log.info(output.output)

        database_cmd = f"db2 deactivate db {database_name}"
        self.log.info("Deactivating database %s on client using command: %s", database_name, database_cmd)
        output = self.client_machine.execute_command(command=database_cmd)
        self.log.info(output.output)

        if "SQL1031N" in output.output:
            database_cmd = f"db2 uncatalog database {database_name}"
            self.log.info("Uncataloging database %s on client using command: %s", database_name, database_cmd)
            output = self.client_machine.execute_command(command=database_cmd)
            self.log.info(output.output)

        database_cmd = f"db2 drop db {database_name}"
        self.log.info("Dropping database %s on client using command: %s", database_name, database_cmd)
        output = self.client_machine.execute_command(command=database_cmd)
        self.log.info(output.output)

    @test_step
    def create_database(self, database_name):
        """
        Creates database on client machine
        Args:
            database_name (str) -- Name of database to create
        """
        self.log.info("Creating database %s on client machine", database_name)

        database_cmd = "db2 force application all"
        self.log.info("Disconnecting database %s from all connections using command: %s", database_name, database_cmd)
        output = self.client_machine.execute_command(command=database_cmd)
        self.log.info(output.output)

        self.recreate_database_paths()

        database_cmd = f"db2 create database {database_name} on '{self.db_dir}' dbpath on '{self.dbpath}'"
        self.log.info("Creating database %s on client using command: %s", database_name, database_cmd)
        output = self.client_machine.execute_command(command=database_cmd)
        self.log.info(output.output)

    @test_step
    def recreate_database_paths(self):
        """
        Recreates snap paths
        """
        self.log.info("### Recreating Database Paths ###")

        self.client_machine_root.remove_directory(directory_name=self.db_dir)
        self.client_machine_root.remove_directory(directory_name=self.dbpath)
        self.client_machine.create_directory(directory_name=self.db_dir,
                                             force_create=True)
        self.client_machine.create_directory(directory_name=self.dbpath,
                                             force_create=True)

    @test_step
    def remove_existing_logs_dir(self):
        """
        Removes existing logs staging directory for destination database
        """
        self.log.info("### Removing existing logging directories ###")

        archive_path = self.client_machine.get_registry_value(commvault_key="Db2Agent",
                                                              value="sDB2_ARCHIVE_PATH").strip()
        audit_error_path = self.client_machine.get_registry_value(commvault_key="Db2Agent",
                                                                  value="sDB2_AUDIT_ERROR_PATH").strip()
        retrieve_path = self.client_machine.get_registry_value(commvault_key="Db2Agent",
                                                               value="sDB2_RETRIEVE_PATH").strip()
        retrieve_path = f"{retrieve_path}/retrievePath"

        self.log.info("Archive Path: %s", archive_path)
        self.log.info("Audit Path: %s", audit_error_path)
        self.log.info("Retrieve Path: %s", retrieve_path)

        self.delete_database_directory(path=f"{archive_path}/{self.tcinputs['instance_name']}/",
                                       database_name=self.src_database_name)
        self.delete_database_directory(path=f"{retrieve_path}/{self.tcinputs['instance_name']}/",
                                       database_name=self.src_database_name)

        self.delete_database_directory(path=f"{archive_path}/{self.tcinputs['instance_name']}/",
                                       database_name=self.database1)
        self.delete_database_directory(path=f"{retrieve_path}/{self.tcinputs['instance_name']}/",
                                       database_name=self.database1)

        self.delete_database_directory(path=f"{archive_path}/{self.tcinputs['instance_name']}/",
                                       database_name=self.database2)
        self.delete_database_directory(path=f"{retrieve_path}/{self.tcinputs['instance_name']}/",
                                       database_name=self.database2)

        
        cmd = f"rm -rf {audit_error_path}/*"
        self.log.info("Removing audit error files: %s", cmd)
        self.client_machine.execute_command(command=cmd)

    @test_step
    def delete_database_directory(self, path, database_name):
        """
        Deletes existing database directory
        Args:
            path (str)  -- Base path of database
            database_name (str) -- Database name to delete path for
        """
        self.log.info("Deleting file %s", f"{path}{database_name}")
        try:
            self.client_machine.remove_directory(directory_name=f"{path}{database_name}")
        except Exception as _:
            pass
    
    @test_step
    def get_home_path(self):
        """
        Gets Instance home path
        """
        self.log.info("### Getting Instance Home Path ###")
        self.home_path = self.client_machine.execute_command(command='echo $HOME').output.strip()
        self.log.info("Home path for the instance:%s", self.home_path)

    @test_step
    def delete_instance(self):
        """Deletes instance if exists"""
        if self.db_instance.is_instance_exists(database_type=self.dbtype,
                                               instance_name=self.tcinputs["instance_name"],
                                               client_name=self.client_displayname):
            self.db_instance.select_instance(database_type=self.dbtype,
                                             instance_name=self.tcinputs["instance_name"],
                                             client_name=self.client_displayname)
            self.db_instance_details.delete_instance()
        else:
            self.log.info("Instance does not exists.")

    @test_step
    def discover_instance(self):
        """
        Discover Instances
        """
        if self.db_instance.is_instance_exists(database_type=self.dbtype,
                                               instance_name=self.tcinputs["instance_name"],
                                               client_name=self.client_displayname):
            self.delete_instance()

        self.db_instance.discover_instances(database_engine=self.dbtype,
                                            server_name=self.client_displayname)

    @test_step
    def edit_instance_property(self):
        """
        Changes DB2 instance properties.
        """
        self.db_instance_details.db2_edit_instance_properties(username=self.tcinputs["db2_username"],
                                                              password=self.tcinputs["db2_user_password"],
                                                              plan=self.tcinputs["plan"],
                                                              credential_name=self.tcinputs["credential_name"])
        self.admin_console.refresh_page()

    @test_step
    def delete_database(self):
        """
        Deletes database if it exists
        """
        self.commcell.refresh()
        self.admin_console.refresh_page()
        if self.src_database_name in self.db_instance_details.get_instance_entities():
            self.db_instance_details.delete_entity(self.src_database_name)
        self.admin_console.refresh_page()
        self.commcell.refresh()

    @test_step
    def add_database(self):
        """
        Adds database if does not exist
        """
        if self.src_database_name not in self.db_instance_details.get_instance_entities():
            self.db_instance_details.add_db2_database(database_name=self.src_database_name,
                                                      plan=self.tcinputs["plan"])
            self.admin_console.refresh_page()

    @test_step
    def navigate_to_instance_details(self):
        """
        Navigates to Instance Details Page
        """
        self.navigator.navigate_to_databases()
        self.db_instance.select_instance(database_type=self.dbtype,
                                         instance_name=self.tcinputs["instance_name"],
                                         client_name=self.client.display_name)

    @test_step
    def add_snap_subclient(self):
        """Adding Snap Subclient"""
        if self.snap_subclient not in self.db_backupset.list_subclients():
            self.db_backupset.add_db2_subclient(subclient_name=self.snap_subclient,
                                                plan=self.tcinputs["plan"],
                                                backup_logs=True)

        self.navigate_to_instance_details()
        self.db_instance_details.click_on_entity(entity_name=self.src_database_name)
        self.db_backupset.access_subclient(subclient_name=self.snap_subclient)
        self.db_subclient.enable_snapshot(snap_engine="NetApp", proxy_node=self.client.display_name)

    @test_step
    def run_backup(self, backup_type="traditional"):
        """Runs backup
            type               (str)               -- Type of backup
                -default: traditional
            Raises:
                Exception:
                    If backup job fails
        """
        if backup_type.lower() == "snap":
            backup_job_id = self.db_backupset.db2_backup(subclient_name=self.snap_subclient.name, backup_type="full")
            subclient_id = self.snap_subclient.subclient_id
        else:
            backup_job_id = self.db_backupset.db2_backup(subclient_name=self.subclient.name, backup_type="full")
            subclient_id = self.subclient.subclient_id
        job = self.commcell.job_controller.get(backup_job_id)
        self.log.info("Waiting for Backup to Complete (Job Number: %s)", backup_job_id)

        job_status = job.wait_for_completion()

        all_jobs = self.commcell.job_controller.active_jobs(client_name=self.client.display_name)

        for key, _ in all_jobs.items():
            if str(all_jobs[key]['subclient_id']) == subclient_id:
                job = self.commcell.job_controller.get(key)
                self.log.info("Waiting for Jobs to Complete (Job Id: %s)", key)
                job_status = job.wait_for_completion()

        if not job_status:
            raise CVTestStepFailure("Backup Job Failed for DB2!")

        return backup_job_id

    @test_step
    def run_restore(self, job_id, database_name, database_path,
                    roll_forward=True, redirect_sto_grp_path=None, redirect_table_space_path=None):
        """Runs restore
            job_id                      (str)               -- Job id to restore from
            database_name               (str)               -- Target database name
            database_path               (str)               -- Target database path
            roll_forward                (bool)              -- Rollforward or not
                -default: True
            redirect_sto_grp_path       (dict)              -- Redirect storage group paths
                - default: None
            redirect_table_space_path   (dict)              -- Redirect tablespace paths
                - default: None
            Raises:
                Exception:
                    If restore job fails
        """
        self.db_backupset.list_backup_history()
        self.jobs_page.job_restore(job_id)
        restore_job = self.db_backupset.restore_folders(database_type=self.dbtype, all_files=True)
        restore_job_id = restore_job.out_of_place_restore(destination_client=self.client.display_name,
                                                          destination_instance=self.instance.name,
                                                          destination_db=database_name,
                                                          target_db_path=database_path,
                                                          rollforward=roll_forward,
                                                          endlogs=roll_forward,
                                                          redirect=True,
                                                          redirect_sto_grp_path=redirect_sto_grp_path,
                                                          redirect_tablespace_path=redirect_table_space_path)

        restore_job = self.commcell.job_controller.get(restore_job_id)

        self.log.info("Waiting for Restore Job to Complete (Job Number: %s)", restore_job_id)
        job_status = restore_job.wait_for_completion()

        all_jobs = self.commcell.job_controller.active_jobs(client_name=self.client.display_name)
        for key, _ in all_jobs.items():
            if 'application' in all_jobs[key]['operation'].lower() and \
                    'restore' in all_jobs[key]['operation'].lower():

                job = self.commcell.job_controller.get(key)
                self.log.info("Waiting for Jobs to Complete (Job Id: %s)", key)
                job_status = job.wait_for_completion()

        if not job_status:
            raise CVTestStepFailure("Restore Job Failed for DB2!")

    @test_step
    def store_backup_info(self, traditional_backup_ids):
        """Stores Source database backup info
            Args:
                traditional_backup_ids             (list)              -- List of Job Ids of traditional backup
            Raises:
                Exception:
                    If restore job is not what expected
        """
        self.timestamps = []
        for job_id in traditional_backup_ids:
            self.timestamps.append(self.db2_helper.get_backup_time_stamp_and_streams(job_id)[0])
        

    @test_step
    def verify_restore_history(self, database, only_one=False):
        """Verifies restore job id on Restore History Page
            Args:
                database                            (str)              --  Database Name
                only_one                            (bool)             --  Only first timestamp present
            Raises:
                Exception:
                    If restore job is not what expected
        """
        self.log.info("Sleeping for 30 seconds")
        time.sleep(30)

        self.client_machine.execute_command("db2 terminate; db2 force application all; db2stop")
        self.client_machine.execute_command("db2start")
        
        cmd = "db2 list backup since {} for db {}"
        backup_history = self.client_machine.execute_command(cmd.format(self.timestamps[0], database)).output
        verified=False
        if only_one:
            if (self.timestamps[0] in backup_history) and (self.timestamps[1] not in backup_history):
                self.log.info("%s present in %s Backup History and %s not present in %s Backup History.",
                                self.timestamps[0], database, self.timestamps[1], database)
                verified=True
        else:
            if (self.timestamps[0] in backup_history) and (self.timestamps[1] in backup_history):
                self.log.info("%s and %s present in %s Backup History",
                                self.timestamps[0], self.timestamps[1], database)
                verified=True
        if verified:
            self.log.info("Snap Restore Verified.")
        else:
            raise CVTestStepFailure("Snap Restore Not Verified.")

    @test_step
    def cleanup(self):
        """Cleanup method for test case"""
        self.db2_helper.close_db2_connection()
        self.drop_database_on_client(database_name=self.src_database_name)
        self.drop_database_on_client(database_name=self.database1)
        self.drop_database_on_client(database_name=self.database2)
        self.db2_helper.disconnect_applications()
        self.client_machine.execute_command(command='db2_kill')
        self.client_machine.execute_command(command='db2start')
        self.client_machine.disconnect()
        self.client_machine_root.disconnect()
        self.navigator.navigate_to_databases()
        self.delete_instance()

    def tear_down(self):
        """ Logout from all the objects and close the browser. """

        self.admin_console.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
