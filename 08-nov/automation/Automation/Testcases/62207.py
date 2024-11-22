# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
"62207": {
            "ClientName": "CvClientName",
            "AgentName": "DB2",
            "instance_name": "dummy_inst",
            "db2_username": "dummy_user",
            "db2_user_password": "test_passwd",
            "plan": "plan name",
            "src_database": "Source Database",
            "credential_name": "cred_name"
    }

TestCase: Class for executing this test case

TestCase:
    __init__()                              --  initialize TestCase class

    setup()                                 --  setup function of this test case

    run()                                   --  run function of this test case

    prerequisite_setup_test_case()          -- Prerequisites needed to run the testcase

    get_home_path()                         --  Gets instance home path

    delete_existing_instance()              --  Deletes Existing instance on Command Center

    add_db2_instance()                      -- Adds DB2 instance on Command Center

    delete_database()                       -- Deletes database if it exists on Command Center

    add_database()                          -- Adds database to Command Center

    create_log_subclient()                  -- Creates log subclient for log backup

    update_db2_client_machine_property()    -- Edit db2 parameters on client to make them ready for backup

    prepare_data_on_client()                -- Prepares data on client

    run backup()                            -- Runs backup on Command Center

    validate_backup_job()                   -- Validates Backup Jobs

    run_restore()                           -- RUns restore on Command Center

    validate_restore_job()                  -- Validates Restore jobs

    cleanup()                               -- Cleans up the setup

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

        self.name = "Command Center - DB2 Recover Database Operation"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_instance = None
        self.db_instance_details = None
        self.db_backupset = None
        self.dbtype = None
        self.client_machine = None
        self.home_path = None
        self.db2_helper = None
        self.sto_grp = None
        self.table_data = None
        self.table_name = None
        self.tablespace_name = None
        self.page_container = None
        self.tcinputs = {
            "instance_name": None,
            "db2_username": None,
            "db2_user_password": None,
            "plan": None,
            "src_database": None,
            "credential_name": None
        }

    def setup(self):
        """Setup function of this test case"""
        try:
            self.client_machine = Machine(machine_name=self.client.client_hostname,
                                          username=self.tcinputs['db2_username'],
                                          password=self.tcinputs['db2_user_password'])

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
            self.table_name = f"T{self.id}"
            self.sto_grp = f"STG{self.id}"
            self.tablespace_name = f"TS{self.id}"
            self.page_container = PageContainer(self.admin_console)

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

        self.get_home_path()
        self.navigator.navigate_to_db_instances()
        self.delete_existing_instance()
        self.db_instance.react_instances_table.reload_data()
        self.add_db2_instance()
        self.log.info("Sleeping for 30 seconds.")
        time.sleep(30)
        self.add_database(database_name=self.tcinputs['src_database'])
        self.update_db2_client_machine_property()
        self.log.info("Sleeping for 30 seconds.")
        time.sleep(30)

    @test_step
    def get_home_path(self):
        """
        Gets Instance home path
        """
        if "windows" in self.client_machine.os_info.lower():
            self.home_path = self.client_machine.get_registry_value(value="DB2 Path Name",
                                                                    win_key="HKLM:\\SOFTWARE\\IBM\\DB2\\").strip()
            self.tcinputs['db2_username'] = self.client.display_name + "\\" + self.tcinputs["db2_username"]
        else:
            self.home_path = self.client_machine.execute_command(command='echo $HOME').output.strip()
        self.log.info("Home path for the instance:%s", self.home_path)

    @test_step
    def delete_existing_instance(self):
        """
        Deletes if instance exists on Command Center
        """
        if self.db_instance.is_instance_exists(database_type=self.dbtype,
                                               instance_name=self.tcinputs["instance_name"],
                                               client_name=self.client.display_name):
            self.db_instance.select_instance(database_type=self.dbtype,
                                             instance_name=self.tcinputs["instance_name"],
                                             client_name=self.client.display_name)
            self.db_instance_details.delete_instance()

    @test_step
    def add_db2_instance(self):
        """
        Adds DB2 instance on Command Center
        """
        self.db_instance.add_db2_instance(server_name=self.client.display_name,
                                          plan=self.tcinputs["plan"],
                                          instance_name=self.tcinputs["instance_name"],
                                          db2_home=self.home_path,
                                          db2_username=self.tcinputs["db2_username"],
                                          db2_user_password=self.tcinputs["db2_user_password"],
                                          credential_name=self.tcinputs["credential_name"])
        self.commcell.refresh()
        self.admin_console.refresh_page()

    @test_step
    def delete_database(self, database_name):
        """
        Deletes database if it exists on Command Center
        Args:
            database_name (str) -- Database name to be deleted
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
            database_name (str) -- Database name to be deleted
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
                                                                  path=self.home_path,
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
        backup_job_id = self.db_backupset.db2_backup(subclient_name=subclient_name,
                                                     backup_type=backup_type.lower())
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
        Runs a recover job
        Raises:
            CVTestStepFailure -- If Restore Job Fails
        """
        self.db2_helper.disconnect_applications()
        self.db_backupset.access_restore()
        restore_job = self.db_backupset.restore_folders(database_type=self.dbtype, all_files=True)
        restore_job_id = restore_job.in_place_restore(endlogs=True, recover=True)
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
        self.db2_helper.disconnect_applications()
        self.db2_helper.reconnect()

        self.db2_helper.restore_validation(table_space=self.tablespace_name,
                                           table_name=f"SCHEMAFULL.{self.table_name}",
                                           tablecount_full=self.table_data[0],
                                           storage_grps=[self.sto_grp])
        self.log.info("Verified Restore.")

    @test_step
    def cleanup(self):
        """Cleanup"""
        self.db2_helper.drop_tablespace(tblspace_name=self.tablespace_name)
        self.db2_helper.drop_storage_group(stogroup_name=self.sto_grp)
        self.db2_helper.close_db2_connection()
        self.client_machine.disconnect()

    def tear_down(self):
        """Tear down function of this test case"""
        self.admin_console.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
