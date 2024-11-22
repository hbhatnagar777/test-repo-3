# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
"62204": {
              "ClientName": "CvClientName",
              "AgentName": "DB2",
              "instance_name": "dummy_inst1",
              "db2_username": "dummy_user1",
              "db2_user_password": "test_passwd",
              "plan": "plan name",
              "src_database": "Source Database",
              "dest_instance_name": "dummy_inst2",
              "dest_db2_username": "dummy_user2",
              "dest_db2_user_password": "test_passwd",
              "credential_name": "cred_name",
              "dest_credential_name": "dest_cred_name"
        }

TestCase: Class for executing this test case

TestCase:
    __init__()                              --  initialize TestCase class

    setup()                                 --  setup function of this test case

    run()                                   --  run function of this test case

    prerequisite_setup_test_case()          --  Prerequisites needed to run the testcase

    verify_db2_version()                    --  Verify if source and destination db2 versions are same

    delete_database_directory()             --  Cleaning out existing destination database

    remove_existing_logs_dir()              --  Removes existing log staging directory for destination database

    drop_database_on_client()               --  Drops database on client

    get_redirect_path()                     --  Gets destination database path to redirect to

    get_user_details()                      -- Gets instance home path and other details

    delete_existing_instance()              --  Deletes Existing instance on Command Center

    add_db2_instance()                      --  Adds DB2 instance on Command Center

    delete_database()                       --  Deletes database if it exists on Command Center

    add_database()                          --  Adds database to Command Center

    create_log_subclient()                  --  Creates log subclient for log backup

    update_db2_client_machine_property()    --  Edit db2 parameters on client to make them ready for backup

    prepare_data_on_client()                --  Prepares data on client

    run backup()                            --  Runs backup on Command Center

    validate_backup_job()                   --  Validates Backup Jobs

    run_restore()                           --  RUns restore on Command Center

    validate_restore_job()                  --  Validates Restore jobs

    cleanup()                               --  Cleans up the setup

    tear_down()                             --  tear down function of this test case

"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.machine import Machine
from Database.DB2Utils.db2helper import DB2
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import Db2InstanceDetails
from Web.AdminConsole.Databases.backupset import DB2Backupset
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.Components.page_container import PageContainer


class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()

        self.name = "Command Center - DB2 Out of place Restore: To Different Instance on Same machine"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_instance = None
        self.db_instance_details = None
        self.db_backupset = None
        self.dbtype = None
        self.source_instance = None
        self.destination_instance = None
        self.src_home_path = None
        self.dest_home_path = None
        self.redirect_path = None
        self.dest_db = None
        self.db2_helper = None
        self.sto_grp = None
        self.table_data = None
        self.table_name = None
        self.tablespace_name = None
        self.db2_base = None
        self.page_container = None
        self.tcinputs = {
            "instance_name": None,
            "db2_username": None,
            "db2_user_password": None,
            "plan": None,
            "src_database": None,
            "dest_instance_name": None,
            "dest_db2_username": None,
            "dest_db2_user_password": None,
            "credential_name": None,
            "dest_credential_name": None
        }

    def setup(self):
        """Setup function of this test case"""
        try:
            self.source_instance = Machine(machine_name=self.client.client_hostname,
                                           username=self.tcinputs['db2_username'],
                                           password=self.tcinputs['db2_user_password'])
            self.destination_instance = Machine(machine_name=self.client.client_hostname,
                                                username=self.tcinputs['dest_db2_username'],
                                                password=self.tcinputs['dest_db2_user_password'])

            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            self.admin_console.login(username=self.inputJSONnode['commcell']["commcellUsername"],
                                     password=self.inputJSONnode['commcell']["commcellPassword"])

            self.navigator = self.admin_console.navigator
            self.db_instance = DBInstances(admin_console=self.admin_console)
            self.db_instance_details = Db2InstanceDetails(admin_console=self.admin_console)
            self.db_backupset = DB2Backupset(admin_console=self.admin_console)
            self.dbtype = DBInstances.Types.DB2
            self.dest_db = f"DES{self.id}"
            self.sto_grp = f"STG{self.id}"
            self.table_name = f"T{self.id}"
            self.tablespace_name = f"TS{self.id}"
            self.db2_base = ""
            self.page_container = PageContainer(self.admin_console)
            if "windows" in self.destination_instance.os_info.lower():
                self.db2_base = "set-item -path env:DB2CLP -value **$$** ; $DB2INSTANCE=\"{0}\"; " \
                                "set-item -path env:DB2INSTANCE -value $DB2INSTANCE;"

            self.prerequisite_setup_test_case()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """Run function of this test case"""
        try:
            self.commcell.refresh()

            self.db_instance_details.click_on_entity(entity_name=self.tcinputs['src_database'])
            self.create_log_subclient()

            self.navigator.navigate_to_db_instances()
            self.db_instance.select_instance(database_type=self.dbtype,
                                             instance_name=self.tcinputs["instance_name"],
                                             client_name=self.client.display_name)
            self.db_instance_details.click_on_entity(entity_name=self.tcinputs['src_database'])
            self.page_container.select_entities_tab()

            # Full
            self.prepare_data_on_client(table_type="FULL", create_tablespace=True)
            self.run_backup()
            self.admin_console.refresh_page()

            # Incremental
            self.prepare_data_on_client(table_type="INCR")
            self.run_backup(backup_type="Incremental")
            self.admin_console.refresh_page()

            # Delta
            self.prepare_data_on_client(table_type="DEL")
            self.run_backup(backup_type="Differential")
            self.admin_console.refresh_page()

            # Log backup
            self.run_backup(subclient_name=self.id)
            self.admin_console.refresh_page()

            self.page_container.select_overview_tab()
            self.run_restore()

            self.navigator.navigate_to_db_instances()
            self.db_instance.select_instance(database_type=self.dbtype,
                                             instance_name=self.tcinputs["dest_instance_name"],
                                             client_name=self.client.display_name)
            self.add_database(database_name=self.dest_db)
            self.validate_restore_job()
            self.log.info('****** Test Case %s Passed ******', self.id)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            self.cleanup()

    @test_step
    def prerequisite_setup_test_case(self):
        """
        Runs prerequisite steps to create client side setups and details
        """
        self.verify_db2_version()
        self.src_home_path, self.tcinputs["db2_username"] = self.get_user_details(
            client_machine=self.source_instance,
            client_object=self.client,
            username=self.tcinputs["db2_username"])

        self.dest_home_path, self.tcinputs["dest_db2_username"] = self.get_user_details(
            client_machine=self.destination_instance,
            client_object=self.client,
            username=self.tcinputs["dest_db2_username"])

        self.remove_existing_logs_dir(client_machine=self.destination_instance,
                                      instance_name=self.tcinputs["dest_instance_name"])
        self.drop_database_on_client(client_machine=self.destination_instance,
                                     database_name=self.dest_db,
                                     instance_name=self.tcinputs["dest_instance_name"])
        self.get_redirect_path()

        self.navigator.navigate_to_db_instances()
        self.delete_existing_instance(client_name=self.client.display_name,
                                      instance_name=self.tcinputs["dest_instance_name"])
        self.add_db2_instance(server_name=self.client.display_name,
                              instance_name=self.tcinputs["dest_instance_name"],
                              home_path=self.dest_home_path,
                              username=self.tcinputs["dest_db2_username"],
                              password=self.tcinputs["dest_db2_user_password"],
                              credential_name=self.tcinputs["dest_credential_name"])

        self.navigator.navigate_to_db_instances()
        self.delete_existing_instance(client_name=self.client.display_name,
                                      instance_name=self.tcinputs["instance_name"])
        self.db_instance.react_instances_table.reload_data()
        self.add_db2_instance(server_name=self.client.display_name,
                              instance_name=self.tcinputs["instance_name"],
                              home_path=self.src_home_path,
                              username=self.tcinputs["db2_username"],
                              password=self.tcinputs["db2_user_password"],
                              credential_name=self.tcinputs["credential_name"])

        self.log.info("Sleeping for 30 seconds.")
        time.sleep(30)
        self.add_database(database_name=self.tcinputs['src_database'])
        self.update_db2_client_machine_property()
        self.log.info("Sleeping for 30 seconds.")
        time.sleep(30)

    @test_step
    def verify_db2_version(self):
        """
        Verify if source and destination db2 versions are same
        Raises:
            CVTestStepFailure - If db2 versions do no match
        """
        version_cmd = f"{self.db2_base.format(self.tcinputs['instance_name'])} db2level"
        source_version = self.source_instance.execute_command(command=version_cmd).output.strip()
        source_version = list(filter(None, "\n".join(source_version.splitlines()).splitlines()))
        self.log.info(source_version)
        source_version = source_version[3].split("\"")[1].split()[1][1:]
        self.log.info("Source Version: %s", source_version)

        version_cmd = f"{self.db2_base.format(self.tcinputs['instance_name'])} db2level"
        destination_version = self.destination_instance.execute_command(command=version_cmd).output.strip()
        destination_version = list(filter(None, "\n".join(destination_version.splitlines()).splitlines()))
        destination_version = destination_version[3].split("\"")[1].split()[1][1:]
        self.log.info("Destination Version: %s", destination_version)

        source_version = source_version.split('.')
        destination_version = destination_version.split('.')
        for version_index, _ in enumerate(source_version):
            if int(source_version[version_index]) != int(destination_version[version_index]):
                raise CVTestStepFailure("Destination DB2 Version Higher than Source. Cannot proceed with the test case")

    @test_step
    def delete_database_directory(self, client_machine, path, database_name):
        """
        Deletes existing database directory
        Args:
            client_machine (Machine) -- Client machine object to work with
            path (str)               -- Base path to work with
            database_name(str)       -- Database name to delete path for
        """
        self.log.info("Deleting file %s", f"{path}{database_name}")
        try:
            client_machine.remove_directory(directory_name=f"{path}{database_name}")
        except Exception as _:
            pass

    @test_step
    def remove_existing_logs_dir(self, client_machine, instance_name):
        """
        Removes existing log directory
        Args:
            client_machine (Machine) -- Client Machine Object to delete staging logs path on
            instance_name (str)      -- Instance name to delete log paths for
        """

        archive_path = client_machine.get_registry_value(commvault_key="Db2Agent",
                                                         value="sDB2_ARCHIVE_PATH").strip()
        audit_error_path = client_machine.get_registry_value(commvault_key="Db2Agent",
                                                             value="sDB2_AUDIT_ERROR_PATH").strip()
        retrieve_path = client_machine.get_registry_value(commvault_key="Db2Agent",
                                                          value="sDB2_RETRIEVE_PATH").strip()

        path_sep = "\\" if "windows" in self.client.os_info.lower() else "/"
        retrieve_path = f"{retrieve_path}{path_sep}retrievePath"

        self.log.info("Archive Path: %s", archive_path)
        self.log.info("Audit Path: %s", audit_error_path)
        self.log.info("Retrieve Path: %s", retrieve_path)

        self.delete_database_directory(client_machine=client_machine,
                                       path=f"{archive_path}{path_sep}{instance_name}{path_sep}",
                                       database_name=self.dest_db)
        self.delete_database_directory(client_machine=client_machine,
                                       path=f"{retrieve_path}{path_sep}{instance_name}{path_sep}",
                                       database_name=self.dest_db)

        if "windows" in self.client.os_info.lower():
            cmd = "Get-ChildItem -Path %s -Include * -Recurse | foreach { $_.Delete()}" % audit_error_path
        else:
            cmd = f"rm -rf {audit_error_path}/*"
        self.log.info("Removing audit error files: %s", cmd)
        client_machine.execute_command(command=cmd)

    @test_step
    def drop_database_on_client(self, client_machine, database_name, instance_name):
        """
        Drops database on client
        Args:
            client_machine (Machine)    --  Client Machine object to work with
            database_name (str)         -- Database name to be dropped
            instance_name (str)         -- Instance name on which database exists
        """
        database_cmd = f"{self.db2_base.format(instance_name)} db2 force application all"
        self.log.info("Disconnecting %s from all connections using command: %s", database_name, database_cmd)
        output = client_machine.execute_command(command=database_cmd)
        self.log.info(output.output)

        database_cmd = f"{self.db2_base.format(instance_name)} db2 deactivate db {database_name}"
        self.log.info("Deactivating database %s on client using command: %s", database_name, database_cmd)
        output = client_machine.execute_command(command=database_cmd)
        self.log.info(output.output)

        if "SQL1031N" in output.output:
            database_cmd = f"{self.db2_base.format(instance_name)} db2 uncatalog database {database_name}"
            self.log.info("Uncataloging database %s on client using command: %s", database_name, database_cmd)
            output = client_machine.execute_command(command=database_cmd)
            self.log.info(output.output)

        database_cmd = f"{self.db2_base.format(instance_name)} db2 drop db {database_name}"
        self.log.info("Dropping database %s on client using command: %s", database_name, database_cmd)
        output = client_machine.execute_command(command=database_cmd)
        self.log.info(output.output)

    @test_step
    def get_user_details(self, client_machine, client_object, username):
        """
        Gets Instance home path and User Credentials
        Args:
            client_machine (Machine)    --  Client Machine Object to work with
            client_object (Client)      -- Client Object to get client details from
            username (str)              -- Client username to get details for
        """
        db2_username = username
        if "windows" in client_machine.os_info.lower():
            home_path = client_machine.get_registry_value(value="DB2 Path Name",
                                                          win_key="HKLM:\\SOFTWARE\\IBM\\DB2\\").strip()
            db2_username = self.client.display_name + "\\" + self.tcinputs["db2_username"]
        else:
            home_path = client_machine.execute_command(command='echo $HOME').output.strip()
        self.log.info("Home path for the instance:%s", home_path)
        self.log.info("User name for the instance: %s", db2_username)

        return home_path, db2_username

    @test_step
    def get_redirect_path(self):
        """
        Get Redirect Path
        """

        index = 9
        if "windows" in self.destination_instance.os_info.lower():
            index = 1

        self.log.info("Creating temporary database.")
        create_database_cmd = f"{self.db2_base.format(self.tcinputs['dest_instance_name'])} db2 create db tp{self.id}"
        output = self.destination_instance.execute_command(command=create_database_cmd)
        self.log.info(output.output)

        get_redirect_path = f"{self.db2_base.format(self.tcinputs['dest_instance_name'])} db2 connect to tp{self.id};" \
                            f"db2 \"SELECT DBPARTITIONNUM, TYPE, PATH FROM TABLE(ADMIN_LIST_DB_PATHS()) AS FILES " \
                            f"where type='DB_STORAGE_PATH'\""
        output = self.destination_instance.execute_command(command=get_redirect_path).formatted_output
        self.log.info("Getting Redirect Path using command: %s", get_redirect_path)
        self.redirect_path = output[index][2]
        self.log.info("Redirect path for the instance %s:%s", self.tcinputs['dest_instance_name'], self.redirect_path)
        self.log.info("Dropping temporary database.")
        self.drop_database_on_client(client_machine=self.destination_instance,
                                     database_name=f"tp{self.id}",
                                     instance_name=self.tcinputs["dest_instance_name"])

        restore_grant_cmd = f"{self.db2_base.format(self.tcinputs['dest_instance_name'])} " \
                            f"db2set DB2_RESTORE_GRANT_ADMIN_AUTHORITIES=ON; db2set"
        output = self.destination_instance.execute_command(command=restore_grant_cmd)
        self.log.info(output.output)

    @test_step
    def delete_existing_instance(self, client_name, instance_name):
        """
        Deletes if instance exists on Command Center
        Args:
            client_name (str)   --  Client Name to delete instance for
            instance_name (str) -- Instance name to be deleted
        """
        if self.db_instance.is_instance_exists(database_type=self.dbtype,
                                               instance_name=instance_name,
                                               client_name=client_name):
            self.db_instance.select_instance(database_type=self.dbtype,
                                             instance_name=instance_name,
                                             client_name=client_name)
            self.admin_console.wait_for_completion()
            self.db_instance_details.delete_instance()

    @test_step
    def add_db2_instance(self, server_name, instance_name, home_path, username, password, credential_name):
        """
        Adds DB2 instance on Command Center
        Args:
            server_name (str)   --  Client Name to add instance for
            instance_name (str) -- Instance name to add
            home_path (str)     -- Instance Home Directory
            username (str)      -- Instance username
            password (str)      -- Instance Password
            credential_name(str)-- Credential Name
        """
        self.db_instance.add_db2_instance(server_name=server_name,
                                          plan=self.tcinputs["plan"],
                                          instance_name=instance_name,
                                          db2_home=home_path,
                                          db2_username=username,
                                          db2_user_password=password,
                                          credential_name=credential_name)
        self.commcell.refresh()
        self.admin_console.refresh_page()

    @test_step
    def delete_database(self, database_name):
        """
        Deletes database if it exists on Command Center
        Args:
            database_name (str)  -- Database name
        """
        if database_name in self.db_instance_details.get_instance_entities():
            self.db_instance_details.delete_entity(database_name)
        self.admin_console.refresh_page()
        self.commcell.refresh()

    @test_step
    def add_database(self, database_name):
        """
        Adding database to Command Center
        Args:
            database_name (str)  -- Database name
        """
        self.commcell.refresh()
        self.admin_console.refresh_page()
        if database_name in self.db_instance_details.get_instance_entities():
            self.delete_database(database_name=database_name)
            self.admin_console.access_tab("Databases")
        self.db_instance_details.add_db2_database(database_name=database_name,
                                                  plan=self.tcinputs["plan"])

    @test_step
    def create_log_subclient(self):
        """
        Creates log subclient
        """
        self.db_backupset.add_db2_subclient(subclient_name=self.id,
                                            plan=self.tcinputs["plan"],
                                            data_backup=False,
                                            backup_logs=True)

    @test_step
    def update_db2_client_machine_property(self):
        """Edit db2 parameters on client to make them ready for backup"""

        instance = self.agent.instances.get(self.tcinputs['instance_name'])
        backupset = instance.backupsets.get(self.tcinputs['src_database'])

        self.db2_helper = DB2(commcell=self.commcell,
                              client=self.client,
                              instance=instance,
                              backupset=backupset)
        cold_backup_dir = "/dev/null"
        if "windows" in self.client.os_info.lower():
            cold_backup_dir = f"{self.client.install_directory}\\Base\\Temp"
        self.db2_helper.update_db2_database_configuration1(cold_backup_path=cold_backup_dir)

    @test_step
    def prepare_data_on_client(self, table_type, create_tablespace=False):
        """
        Prepares data on client
        Args:
            table_type (str) -- Backup for which table is needed
            create_tablespace (bool) -- Need to create tablespace or not
                default: False
        Raises:
            CVTestStepFailure - When storage group creation fails
        """
        datafile = self.db2_helper.get_datafile_location()
        self.db2_helper.create_table2(datafile=datafile,
                                      tablespace_name=self.tablespace_name,
                                      table_name=f"SCHEMA{table_type}.{self.table_name}_{table_type}",
                                      flag_create_tablespace=create_tablespace)
        if create_tablespace:
            stogrp_created = self.db2_helper.create_storage_group(storage_group_name=self.sto_grp,
                                                                  path=self.src_home_path,
                                                                  flag_recreate_storage_group=True)
            if not stogrp_created:
                raise CVTestStepFailure("Storage group creation failed!")
            self.table_data = self.db2_helper.prepare_data(
                                            table_name=f"SCHEMA{table_type}.{self.table_name}_{table_type}")

    @test_step
    def run_backup(self, subclient_name="default", backup_type="Full"):
        """
        Runs backup
        Args:
            subclient_name (str) -- Subclient to run backup on
                default: "default"
            backup_type (str) -- Type of backup to run
                default: "Full"
        Raises:
            CVTestStepFailure - If backup job fails
        """
        backup_job_id = self.db_backupset.db2_backup(subclient_name=subclient_name, backup_type=backup_type.lower())
        job = self.commcell.job_controller.get(backup_job_id)
        self.log.info("Waiting for Backup to Complete (Job Id: %s)", backup_job_id)
        job_status = job.wait_for_completion()

        if subclient_name == "default":
            self.commcell.refresh()
            self.validate_backup_job(backup_job_object=job,
                                     type_backup=backup_type)

        if not job_status:
            raise CVTestStepFailure("Backup Job Failed for DB2!")

    @test_step
    def validate_backup_job(self, backup_job_object=None, type_backup="Full"):
        """
        Validates Backup Jobs
        Args:
            backup_job_object (Job): Backup Job Object
            type_backup       (Str): Backup type
        """
        backup_time_stamp, _ = self.db2_helper.get_backup_time_stamp_and_streams(jobid=backup_job_object.job_id)
        backup_keys = {
            "full": "N",
            "incremental": "O",
            "differential": "E"
        }
        self.log.info("### Running Backup Validation ###")
        time.sleep(30)
        self.db2_helper.backup_validation(operation_type=backup_keys[type_backup.lower()],
                                          tablespaces_count=self.table_data[1],
                                          backup_time_stamp=backup_time_stamp)

        commonutils = CommonUtils(self.commcell)
        commonutils.backup_validation(backup_job_object.job_id, type_backup)

        self.log.info("Successfully ran %s backup.", backup_job_object.backup_level)

    @test_step
    def run_restore(self):
        """
        Runs restore
        Raises:
            CVTestStepFailure -- If Restore Job Fails
        """
        self.db_backupset.access_restore()
        restore_job = self.db_backupset.restore_folders(database_type=self.dbtype, all_files=True)
        restore_job_id = restore_job.out_of_place_restore(destination_client=self.client.display_name,
                                                          destination_instance=self.tcinputs["dest_instance_name"],
                                                          destination_db=self.dest_db,
                                                          target_db_path=self.redirect_path,
                                                          endlogs=True,
                                                          redirect=True,
                                                          redirect_all_tablespace_path=self.redirect_path,
                                                          redirect_sto_grp_path={
                                                              "IBMSTOGROUP": self.redirect_path,
                                                              self.sto_grp: self.redirect_path
                                                          })
        job = self.commcell.job_controller.get(restore_job_id)
        self.log.info("Waiting for Restore Job to Complete (Job Id: %s)", restore_job_id)
        job_status = job.wait_for_completion()

        all_jobs = self.commcell.job_controller.active_jobs(client_name=self.client.display_name)
        for job_id in all_jobs:
            job = self.commcell.job_controller.get(job_id)
            self.log.info("Waiting for Jobs to Complete (Job Id: %s)", job_id)
            job_status = job.wait_for_completion()

        if not job_status:
            raise CVTestStepFailure("Restore Job Failed for DB2!")

    @test_step
    def validate_restore_job(self):
        """
        Validates restore job
        """
        self.commcell.refresh()

        instance = self.agent.instances.get(self.tcinputs['dest_instance_name'])
        backupset = instance.backupsets.get(self.dest_db)

        dest_db2_helper = DB2(commcell=self.commcell,
                              client=self.client,
                              instance=instance,
                              backupset=backupset)
        dest_db2_helper.restore_validation(table_space=self.tablespace_name,
                                           table_name=f"SCHEMAFULL.{self.table_name}",
                                           tablecount_full=self.table_data[0],
                                           storage_grps=[self.sto_grp])
        self.log.info("Verified Restore.")
        dest_db2_helper.close_db2_connection()

    @test_step
    def cleanup(self):
        """Cleanup"""
        self.db2_helper.drop_tablespace(tblspace_name=self.tablespace_name)
        self.db2_helper.drop_storage_group(stogroup_name=self.sto_grp)
        restore_grant_cmd = f"{self.db2_base.format(self.tcinputs['dest_instance_name'])} " \
                            f"db2set DB2_RESTORE_GRANT_ADMIN_AUTHORITIES= -immediate; db2set"
        output = self.destination_instance.execute_command(command=restore_grant_cmd)
        self.log.info(output.output)
        self.db2_helper.close_db2_connection()
        self.source_instance.disconnect()
        self.destination_instance.disconnect()

    def tear_down(self):
        """Tear down function of this test case"""
        self.admin_console.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
