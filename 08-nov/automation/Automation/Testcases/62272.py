# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
"62272": {
            "ClientName": "CVClientName",
            "AgentName": "DB2",
            "instance_name": "dummy_inst",
            "db2_username": "dummy_user",
            "db2_user_password": "test_passwd",
            "storage_policy": "policy name",
            "snap_path": "Snap Mounted path",
            "credential_name": "cred_name"
        }

TestCase: Class for executing this test case

TestCase:
    __init__()                              --  initialize TestCase class

    setup()                                 --  setup function of this test case

    run()                                   --  run function of this test case

    recreate_database_paths()               --  recreates snap paths

    create_database()                       --  Creates database on client

    delete_database_directory()             --   Cleaning out existing destination database

    remove_existing_logs_dir()              --   Removes existing log staging directory for destination database

    drop_database_on_client()               --  Drops database on client

    get_home_path()                         --  Gets instance home path

    delete_db2_instance()                   --  Deletes Existing instance on Command Center

    add_db2_instance()                      -- Adds DB2 instance

    add_db2_database()                      -- Adds DB2 database

    add_subclient()                         -- Creates subclient for backup

    update_db2_client_machine_property()    -- Edit db2 parameters on client to make them ready for backup

    prepare_data_on_client()                -- Prepares data on client

    delete_index_v1_subclient()             -- Deletes V1 index for each subclient and restart services

    wait_for_job()                          --  Waits for given job to complete

    run backup()                            -- Runs backup

    run_restore()                           -- RUns restore

    validate_restore_job()                  -- Validates Restore jobs

    tear_down()                             --  tear down function of this test case

"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.machine import Machine
from Database.dbhelper import DbHelper
from Database.DB2Utils.db2helper import DB2


class TestCase(CVTestCase):
    """Class for executing Index reconstruction case for DB2 V1 clients"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "DB2 Indexing V1: Reconstruction Case for DB2 Snap Database."
        self.db2_helper_object = None
        self.db_helper = None
        self.src_database_name = None
        self.instance = None
        self.backupset = None
        self.subclient = None
        self.log_subclient = None
        self.client_machine = None
        self.client_machine_root = None
        self.dest_db = None
        self.home_path = None
        self.table_data = None
        self.table_name = None
        self.sto_grp = None
        self.tablespace_name = None
        self.db_dir = None
        self.dbpath = None
        self.db2_base = None
        self.tcinputs = {
            "instance_name": None,
            "db2_username": None,
            "db2_user_password": None,
            "storage_policy": None,
            "snap_path": None,
            "credential_name": None
        }

    def setup(self):
        """Setup function for this testcase"""

        self.src_database_name = "IDXV1SNP"
        self.dest_db = f"DES{self.id}"
        self.sto_grp = f"STG{self.id}"
        self.table_name = f"T{self.id}"
        self.tablespace_name = f"TS{self.id}"
        path_sep = "\\" if "windows" in self.client.os_info.lower() else "/"
        path_sep_needed = True if self.tcinputs['snap_path'][-1] != path_sep else False
        self.db_dir = f"{self.tcinputs['snap_path']}{path_sep if path_sep_needed else ''}db{path_sep}"
        self.dbpath = f"{self.tcinputs['snap_path']}{path_sep if path_sep_needed else ''}dbpath{path_sep}"

        self.client_machine = Machine(machine_name=self.client.client_hostname,
                                      username=self.tcinputs['db2_username'],
                                      password=self.tcinputs['db2_user_password'])

        self.client_machine_root = Machine(machine_name=self.client.client_hostname,
                                           commcell_object=self.commcell)

        self.db2_base = ""
        if "windows" in self.client_machine.os_info.lower():
            self.db2_base = " set-item -path env:DB2CLP -value **$$** ; " \
                            "set-item -path env:DB2INSTANCE -value \"%s\" ;" % self.tcinputs["instance_name"]

        self.log.info("Cleaning up the Client")
        self.drop_database_on_client(database_name=self.src_database_name)
        self.drop_database_on_client(database_name=self.dest_db)
        self.create_database(database_name=self.src_database_name)
        self.remove_existing_logs_dir()

        self.delete_db2_instance()
        self.get_home_path()
        self.client.enable_intelli_snap()
        self.add_db2_instance()
        self.add_db2_backupset(database_name=self.src_database_name)
        self.backupset = self.instance.backupsets.get(backupset_name=self.src_database_name)
        self.add_subclient()

        self.commcell.refresh()

        self.db2_helper_object = DB2(commcell=self.commcell,
                                     client=self.client,
                                     instance=self.instance,
                                     backupset=self.backupset)

        if self.db2_helper_object.is_index_v2_db2():
            raise Exception("This testcase requires the client to be Indexing V1")

        self.db_helper = DbHelper(self.commcell)

    def run(self):
        """Main function for test case execution"""

        try:
            self.update_db2_client_machine_property()

            # Full
            self.prepare_data_on_client()
            self.run_backup(backup_type="Full")

            # Log backup
            self.db2_helper_object.db2_archive_log(self.backupset.backupset_name.upper(), 25)
            self.log.info("Sleeping for 30 seconds")
            time.sleep(30)
            self.run_backup(backup_type="log")

            self.commcell.refresh()

            self.delete_index_v1_subclient(self.subclient)
            self.delete_index_v1_subclient(self.log_subclient)
            self.log.info("Sleeping for 30 seconds")
            time.sleep(30)

            self.run_restore()

            self.validate_restore_job()
            self.log.info("****TEST CASE PASSED****")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.log.info("!!!!TEST CASE FAILED!!!!")
            self.result_string = exp
            self.status = constants.FAILED

    def create_database(self, database_name):
        """
        Creates database on client machine
        Args:
            database_name (str) -- Name of database to create
        """
        self.log.info("Creating database %s on client machine", database_name)

        restore_grant_cmd = f"{self.db2_base} db2set DB2_RESTORE_GRANT_ADMIN_AUTHORITIES=ON; db2set"
        output = self.client_machine.execute_command(command=restore_grant_cmd)
        self.log.info(output.output)

        if "windows" in self.client_machine.os_info.lower():
            db_create_grant_cmd = f"{self.db2_base} db2set DB2_CREATE_DB_ON_PATH=YES; db2set"
            output = self.client_machine.execute_command(command=db_create_grant_cmd)
            self.log.info(output.output)

        database_cmd = f"{self.db2_base} db2 force application all"
        self.log.info("Disconnecting database %s from all connections using command: %s", database_name, database_cmd)
        output = self.client_machine.execute_command(command=database_cmd)
        self.log.info(output.output)

        self.recreate_database_paths()

        database_cmd = f"{self.db2_base} db2 create database {database_name} on '{self.db_dir}' dbpath on '{self.dbpath}'"
        self.log.info("Creating database %s on client using command: %s", database_name, database_cmd)
        output = self.client_machine.execute_command(command=database_cmd)
        self.log.info(output.output)

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

    def remove_existing_logs_dir(self):
        """
        Removes existing logs staging directory for destination database
        """
        self.log.info("### Removing existing logging directories ###")
        path_sep = "\\" if "windows" in self.client.os_info.lower() else "/"

        archive_path = self.client_machine.get_registry_value(commvault_key="Db2Agent",
                                                              value="sDB2_ARCHIVE_PATH").strip()
        audit_error_path = self.client_machine.get_registry_value(commvault_key="Db2Agent",
                                                                  value="sDB2_AUDIT_ERROR_PATH").strip()
        retrieve_path = self.client_machine.get_registry_value(commvault_key="Db2Agent",
                                                               value="sDB2_RETRIEVE_PATH").strip()
        retrieve_path = f"{retrieve_path}{path_sep}retrievePath"

        self.log.info("Archive Path: %s", archive_path)
        self.log.info("Audit Path: %s", audit_error_path)
        self.log.info("Retrieve Path: %s", retrieve_path)

        self.delete_database_directory(path=f"{archive_path}{path_sep}{self.tcinputs['instance_name']}{path_sep}",
                                       database_name=self.src_database_name)
        self.delete_database_directory(path=f"{retrieve_path}{path_sep}{self.tcinputs['instance_name']}{path_sep}",
                                       database_name=self.src_database_name)

        self.delete_database_directory(path=f"{archive_path}{path_sep}{self.tcinputs['instance_name']}{path_sep}",
                                       database_name=self.dest_db)
        self.delete_database_directory(path=f"{retrieve_path}{path_sep}{self.tcinputs['instance_name']}{path_sep}",
                                       database_name=self.dest_db)

        if "windows" in self.client.os_info.lower():
            cmd = "Get-ChildItem -Path %s -Include * -Recurse | foreach { $_.Delete()}" % audit_error_path
        else:
            cmd = f"rm -rf {audit_error_path}/*"
        self.log.info("Removing audit error files: %s", cmd)
        self.client_machine.execute_command(command=cmd)

    def get_home_path(self):
        """
        Gets Instance home path
        """
        self.log.info("### Getting Instance Home Path ###")
        if "windows" in self.client_machine.os_info.lower():
            self.home_path = self.client_machine.get_registry_value(value="DB2 Path Name",
                                                                    win_key="HKLM:\\SOFTWARE\\IBM\\DB2\\").strip()
        else:
            self.home_path = self.client_machine.execute_command(command='echo $HOME').output.strip()
        self.log.info("Home path for the instance:%s", self.home_path)

    def delete_db2_instance(self):
        """
        Deletes DB2 Instance
        """
        self.log.info("### Deleting DB2 Instance ###")
        instances = self.agent.instances
        if instances.has_instance(instance_name=self.tcinputs['instance_name']):
            self.log.info("Deleting instance from CS as it already exist!")
            instances.delete(self.tcinputs['instance_name'])
            instances.refresh()
            self.log.info("Sleeping for 10 seconds")
            time.sleep(10)
        else:
            self.log.info("Instance does not exists on CS.")

    def add_db2_instance(self):
        """
        Adds DB2 Instance
        Raises:
            Exception:
                If adding instance fails.
        """
        self.log.info("### Adding DB2 Instance ###")
        instances = self.agent.instances
        db2_instance_options = {
            'instance_name': self.tcinputs['instance_name'],
            'data_storage_policy': self.tcinputs['storage_policy'],
            'log_storage_policy': self.tcinputs['storage_policy'],
            'command_storage_policy': self.tcinputs['storage_policy'],
            'home_directory': self.home_path,
            'password': self.tcinputs['db2_user_password'],
            'user_name': self.tcinputs['db2_username'],
            'credential_name': self.tcinputs['credential_name']
        }
        if "windows" in self.client_machine.os_info.lower():
            db2_instance_options["user_name"] = f"{self.client.client_name}\{self.tcinputs['db2_username']}"
        instances.add_db2_instance(db2_options=db2_instance_options)
        self.log.info("Sleeping for 10 seconds")
        time.sleep(10)
        instances.refresh()
        self.instance = instances.get(self.tcinputs['instance_name'])

    def add_db2_backupset(self, database_name):
        """
        Adds DB2 Backupset
        """
        self.instance.refresh()
        self.log.info("### Adding DB2 Backupset ###")
        if self.instance.backupsets.has_backupset(backupset_name=database_name):
            self.instance.backupsets.delete(database_name)
            time.sleep(10)
            self.log.info("Sleeping for 10 seconds")
            self.instance.refresh()
        self.instance.backupsets.add(backupset_name=database_name,
                                     storage_policy=self.tcinputs['storage_policy'])
        self.log.info("Sleeping for 10 seconds")
        time.sleep(10)
        self.instance.refresh()

    def add_subclient(self):
        """
        Creates a subclient
        """
        self.log.info("### Creating Subclient ###")

        self.backupset.refresh()
        self.backupset.subclients.add(subclient_name=self.id,
                                      storage_policy=self.tcinputs['storage_policy'],
                                      description="Index V1 Reconstruction DB2 Snap")
        self.backupset.refresh()
        self.backupset.subclients.add(subclient_name=f"{self.id}log",
                                      storage_policy=self.tcinputs['storage_policy'],
                                      description="Index V1 Reconstruction Snap")
        self.log.info("Sleeping for 10 seconds")
        time.sleep(10)
        self.backupset.refresh()
        self.subclient = self.backupset.subclients.get(subclient_name=self.id)
        self.log_subclient = self.backupset.subclients.get(subclient_name=f"{self.id}log")
        self.subclient.enable_intelli_snap(snap_engine_name="NetApp",
                                           proxy_options={
                                               "use_source_if_proxy_unreachable": True,
                                               "snap_proxy": self.client.display_name
                                           })
        self.log_subclient.disable_backupdata()

    def prepare_data_on_client(self):
        """
        Prepares data on client
        Raises:
            Exception - When storage group creation fails
        """
        self.log.info("### Preparing Data on Client ###")
        datafile = self.db2_helper_object.get_datafile_location()
        self.db2_helper_object.create_table2(datafile=datafile,
                                             tablespace_name=self.tablespace_name,
                                             table_name=f"SCHEMAFULL.{self.table_name}_FULL",
                                             flag_create_tablespace=True)

        storage_group_created = self.db2_helper_object.create_storage_group(storage_group_name=self.sto_grp,
                                                                            path=self.db_dir,
                                                                            flag_recreate_storage_group=True)
        if not storage_group_created:
            raise Exception("Storage group creation failed!")
        self.table_data = self.db2_helper_object.prepare_data(
            table_name=f"SCHEMAFULL.{self.table_name}_FULL")

    def drop_database_on_client(self, database_name):
        """
        Drops database on client
        Args:
            database_name (str) -- Name of database to drop
        """
        self.log.info("Dropping database %s on client machine", database_name)

        database_cmd = f"{self.db2_base} db2 force application all"
        self.log.info("Disconnecting database %s from all connections using command: %s", database_name, database_cmd)
        output = self.client_machine.execute_command(command=database_cmd)
        self.log.info(output.output)

        database_cmd = f"{self.db2_base} db2 deactivate db {database_name}"
        self.log.info("Deactivating database %s on client using command: %s", database_name, database_cmd)
        output = self.client_machine.execute_command(command=database_cmd)
        self.log.info(output.output)

        if "SQL1031N" in output.output:
            database_cmd = f"{self.db2_base} db2 uncatalog database {database_name}"
            self.log.info("Uncataloging database %s on client using command: %s", database_name, database_cmd)
            output = self.client_machine.execute_command(command=database_cmd)
            self.log.info(output.output)

        database_cmd = f"{self.db2_base} db2 drop db {database_name}"
        self.log.info("Dropping database %s on client using command: %s", database_name, database_cmd)
        output = self.client_machine.execute_command(command=database_cmd)
        self.log.info(output.output)

    def update_db2_client_machine_property(self):
        """Edit db2 parameters on client to make them ready for backup"""
        self.log.info("### Updating DB2 Database Configuration on client ###")
        cold_backup_dir = "/dev/null"
        if "windows" in self.client.os_info.lower():
            cold_backup_dir = f"{self.client.install_directory}\\Base\\Temp"
        self.db2_helper_object.update_db2_database_configuration1(cold_backup_path=cold_backup_dir)

    def run_backup(self, backup_type):
        """
        Runs Backup for Backupset
        """
        self.backupset.refresh()
        if backup_type == "log":
            self.log.info("### Running GUI Log Backups ###")
            log_backup_job = self.log_subclient.backup(backup_level="FULL")
            self.wait_for_job(job_object=log_backup_job)
        else:
            self.log.info("### Running GUI Full Backup ###")
            backup_job = self.db2_helper_object.run_backup(subclient=self.subclient,
                                                           backup_type=backup_type.upper())
            self.wait_for_job(job_object=backup_job)

            self.log.info("Sleeping for 10 seconds")
            time.sleep(10)
            all_jobs = self.commcell.job_controller.active_jobs(client_name=self.client.display_name)

            for key, _ in all_jobs.items():
                if str(all_jobs[key]['subclient_id']) == self.subclient.subclient_id:
                    job = self.commcell.job_controller.get(key)
                    self.wait_for_job(job_object=job)

    def wait_for_job(self, job_object):
        """
        Waits for Job common method
        Args:
            job_object (Job): Job object to wait for.
        Raises:
            Exception:
                If Job fails to complete.
        """
        self.log.info(f"Waiting for {job_object.job_type} Job to Complete (Job Id: {job_object.job_id})")
        if not job_object.wait_for_completion():
            raise Exception(f"{job_object.job_type} Job Failed with reason: {job_object.delay_reason}")

    def delete_index_v1_subclient(self, subclient_object):
        """
        Deletes V1 index for each subclient and restart services
        Args:
            subclient_object (Subclient) - Subclient object
        """
        self.log.info("Performing index delete operation after backup for subclient: %s", subclient_object.display_name)
        self.db_helper.delete_v1_index_restart_service(subclient=subclient_object)

    def run_restore(self):
        """
        Runs restore
        """
        self.log.info("### Out of place restore ###")
        self.commcell.refresh()

        self.db2_helper_object.close_db2_connection()
        self.drop_database_on_client(database_name=self.src_database_name)
        self.recreate_database_paths()

        self.log.info("Starting Restore")

        restore_job = self.backupset.restore_out_of_place(dest_client_name=self.client.client_name,
                                                          dest_instance_name=self.instance.instance_name,
                                                          dest_backupset_name=self.dest_db,
                                                          target_path=self.dbpath,
                                                          redirect_enabled=True,
                                                          redirect_tablespace_path=self.db_dir,
                                                          redirect_storage_group_path={
                                                              "IBMSTOGROUP": self.db_dir,
                                                              self.sto_grp: self.db_dir
                                                          },
                                                          rollforward=True,
                                                          restore_incremental=False)
        self.wait_for_job(restore_job)
        all_jobs = self.commcell.job_controller.active_jobs(client_name=self.client.display_name)
        for job_id in all_jobs:
            job = self.commcell.job_controller.get(job_id)
            self.wait_for_job(job)

    def validate_restore_job(self):
        """
        Validates restore job
        """
        self.log.info("### Validating Restore Job ###")
        self.commcell.refresh()
        self.add_db2_backupset(database_name=self.dest_db)
        backupset = self.instance.backupsets.get(self.dest_db)

        dest_db2_helper = DB2(commcell=self.commcell,
                              client=self.client,
                              instance=self.instance,
                              backupset=backupset)
        dest_db2_helper.restore_validation(table_space=self.tablespace_name,
                                           table_name=f"SCHEMAFULL.{self.table_name}",
                                           tablecount_full=self.table_data[0],
                                           storage_grps=[self.sto_grp])
        self.log.info("Verified Restore.")
        dest_db2_helper.close_db2_connection()

    def tear_down(self):
        """tear down function to delete automation generated data"""
        self.log.info("### Teardown for the test case 62272 ###")
        try:
            self.log.info("Deleting Destination Database created from CS")
            self.instance.backupsets.delete(self.dest_db)
            self.drop_database_on_client(database_name=self.dest_db)
            self.client_machine.disconnect()
        except Exception as _:
            pass
