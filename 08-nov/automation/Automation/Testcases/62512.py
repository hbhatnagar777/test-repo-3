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
"62512": {
          "partition_node_client_1": "node 1 client name",
          "partition_node_client_2": "node 2 client name",
          "instance_name": "test_inst",
          "database_name": "test_db",
          "plan": "backup_plan",
          "db2_username": "test_user",
          "db2_user_password": "test_passwd"
        }

TestCase: Class for executing this test case

TestCase:
     __init__()                                 --  initialize TestCase class

    setup()                                     --  setup the parameters and common object necessary

    run()                                       --  run function of this test case

    prerequisite_setup_test_case()              --  Prerequisite setup needed for the test case

    navigate_to_database_page()                 --  Navigates to given backupset page

    get_home_path()                             --  Gets home path for the instance

    sleep_and_wait()                            --  Sleeps for given time

    add_instance()                              --  Adds instance

    select_instance()                           --  Selects given instance

    add_backupset()                             --  Adds Backupset

    add_subclient()                             --  Adds subclient

    update_db2_client_machine_property()        --  Updating DB2 logging properties on client

    prepare_data_on_client()                    --  Prepares data on client

    run_backup()                                --  Runs a backup

    validate_backup()                           --  Validates given backup job

    run_restore()                               --  Runs a restore

    validate_restore_job()                      --  Validates given restore job for contents

    validate_automatic_log_backup()             --  Validates Automatic Log Backup feature for Multinode Client

    wait_for_job()                              --  Waits for given job to complete

    run_cmd_line_backup()                       --  Runs the given command line backup

    run_cmd_line_restore()                      --  Runs the command line restore

    generate_tablespace_list()                  --  Generates list of tablespaces

    delete_database()                           --  Deletes Existing Database on Command Center

    delete_instance()                           --  Deletes Existing Instance on Command Center

    tear_down()                                 --  Tear down method to cleanup the entities
"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.machine import Machine
from Database.DB2Utils.db2_multinode_helper import DB2MultiNode
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import Db2InstanceDetails
from Web.AdminConsole.Databases.backupset import DB2Backupset
from Web.AdminConsole.Databases.subclient import DB2Subclient
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.browse import RBrowse

class TestCase(CVTestCase):
    """ Command center: DB2 MultiNode ACCT-1 """

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Command Center: DB2 DPF ACCT-1"
        self.dbtype = None
        self.browser = None
        self.browser_driver = None
        self.admin_console = None
        self.navigator = None
        self.db_instance = None
        self.db_instance_details = None
        self.db_backupset = None
        self.db_subclient = None
        self.client_machine = None
        self.client_object_1 = None
        self.client_object_2 = None
        self.pseudo_client_name = None
        self.pseudo_client_object = None
        self.home_path = None
        self.db2_helper = None
        self.table_data = None
        self.table_name = None
        self.sto_grp = None
        self.tablespace_name = None
        self.page_container = None
        self.browse = None
        self.tcinputs = {
            "partition_node_client_1": None,
            "partition_node_client_2": None,
            "instance_name": None,
            "db2_username": None,
            "db2_user_password": None,
            "database_name": None,
            "plan": None
        }

    def setup(self):
        """ Initial configuration for the test case. """

        try:

            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.browser_driver = self.browser.driver
            self.admin_console = AdminConsole(self.browser,
                                              self.inputJSONnode['commcell']['webconsoleHostname'])
            self.admin_console.login(username=self.inputJSONnode['commcell']["commcellUsername"],
                                     password=self.inputJSONnode['commcell']["commcellPassword"])

            self.navigator = self.admin_console.navigator
            self.dbtype = DBInstances.Types.DB2_MULTINODE
            self.client_object_1 = self.commcell.clients.get(name=self.tcinputs["partition_node_client_1"])
            self.client_object_2 = self.commcell.clients.get(name=self.tcinputs["partition_node_client_2"])
            self.db_instance = DBInstances(admin_console=self.admin_console)
            self.db_instance_details = Db2InstanceDetails(admin_console=self.admin_console)
            self.db_backupset = DB2Backupset(admin_console=self.admin_console)
            self.db_subclient = DB2Subclient(admin_console=self.admin_console)

            self.client_machine = Machine(machine_name=self.client_object_1.client_hostname,
                                          username=self.tcinputs['db2_username'],
                                          password=self.tcinputs['db2_user_password'])

            self.pseudo_client_name = f"DB2_{self.id}_DPF_CL"
            self.sto_grp = f"STG{self.id}"
            self.table_name = f"T{self.id}"
            self.tablespace_name = f"TS{self.id}"
            self.page_container = PageContainer(admin_console=self.admin_console)
            self.browse = RBrowse(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """ Main method to run test case """
        self.prerequisite_setup_test_case()

        self.add_instance()

        self.pseudo_client_object = self.commcell.clients.get(name=self.pseudo_client_name)

        self.delete_database()

        self.add_backupset()
        self.sleep_and_wait(sleep_time=30)
        self.commcell.refresh()
        self.admin_console.refresh_page()

        self.db_instance_details.click_on_entity(entity_name=self.tcinputs["database_name"])

        self.update_db2_client_machine_property()

        self.add_subclient(name=self.id)
        self.navigate_to_database_page()
        self.add_subclient(name="logs_backup", data=False)
        self.navigate_to_database_page()
        self.page_container.select_entities_tab()
        # Command Center Backups
        self.prepare_data_on_client(table_type="FULL", create_tablespace=True)
        self.run_backup(subclient=f"{self.id}")
        self.prepare_data_on_client(table_type="INCR")
        self.run_backup(subclient=f"{self.id}", backup_type="Incremental")
        self.prepare_data_on_client(table_type="DELTA")
        self.run_backup(subclient=f"{self.id}", backup_type="Differential")

        self.db2_helper.db2_archive_log(archive_number_of_times=5)

        self.run_backup(subclient="logs_backup")

        self.admin_console.refresh_page()
        time.sleep(10)

        self.navigator.navigate_to_databases()

        self.db_instance.react_instances_table.reload_data()
        self.sleep_and_wait(sleep_time=30)
        self.commcell.refresh()
        self.admin_console.refresh_page()

        self.navigate_to_database_page()

        # Command Center: Restore
        self.run_restore()
        self.validate_restore_job(table_name=f"SCHEMAFULL.{self.table_name}_FULL")

        self.navigate_to_database_page()

        # Command Center: Recover
        self.run_restore(recover=True)
        self.validate_restore_job(table_name=f"SCHEMAFULL.{self.table_name}_FULL")

        self.navigate_to_database_page()
        tablespace_list = self.generate_tablespace_list(tablespace_name=self.tablespace_name)
        self.run_restore(tablespace_list=tablespace_list)
        self.validate_restore_job(table_name=f"SCHEMAFULL.{self.table_name}_FULL")

        self.navigate_to_database_page()

        # Automatic log backup
        self.validate_automatic_log_backup()

        # Command Center Offline Backups
        self.add_subclient(name=f"{self.id}_offline",
                           data=True,
                           logs=False,
                           type_backup="offline")
        self.navigate_to_database_page()
        self.page_container.select_entities_tab()
        self.prepare_data_on_client(table_type="OFFFULL")
        self.run_backup(subclient=f"{self.id}_offline")
        self.prepare_data_on_client(table_type="OFFINCR")
        self.run_backup(subclient=f"{self.id}_offline", backup_type="Incremental")
        self.prepare_data_on_client(table_type="OFFDELTA")
        self.run_backup(subclient=f"{self.id}_offline", backup_type="Differential")

        self.admin_console.refresh_page()
        time.sleep(10)
        self.page_container.select_overview_tab()
        # Command Center: Restore
        self.run_restore()
        self.validate_restore_job(table_name=f"SCHEMAOFFFULL.{self.table_name}_OFFFULL")

        # Tablespace restore from offline backup will fail right now. Form for SP29: 147216
        # self.navigate_to_database_page()
        # self.run_restore(tablespace_list=tablespace_list)
        # self.validate_restore_job(table_name=f"SCHEMAFULL.{self.table_name}_FULL")

        # Command Line offline Backups
        self.prepare_data_on_client(table_type="CMDOFFFULL")
        self.table_data = self.db2_helper.prepare_data(table_name=f"SCHEMACMDOFFFULL.{self.table_name}_CMDOFFFULL")
        self.run_cmd_line_backup(online=False)

        self.prepare_data_on_client(table_type="CMDOFFINCR")
        self.run_cmd_line_backup(backup_type="Incremental", online=False)
        self.prepare_data_on_client(table_type="CMDOFFDELTA")
        backup_timestamp = self.run_cmd_line_backup(backup_type="Differential", online=False)

        self.run_cmd_line_restore(backup_timestamp=backup_timestamp, online=False)
        self.validate_restore_job(table_name=f"SCHEMACMDOFFFULL.{self.table_name}_CMDOFFFULL")

    @test_step
    def prerequisite_setup_test_case(self):
        """ Prerequisite setup for test case """
        self.navigator.navigate_to_db_instances()
        if self.db_instance.is_instance_exists(database_type=self.dbtype,
                                               instance_name=self.tcinputs["instance_name"],
                                               client_name=self.pseudo_client_name):
            self.select_instance()

            self.db_instance_details.delete_instance()
            self.sleep_and_wait(sleep_time=30)

        self.db_instance.react_instances_table.reload_data()
        self.commcell.refresh()
        self.admin_console.refresh_page()

        self.get_home_path()

    @test_step
    def navigate_to_database_page(self):
        """
        Navigates to database base
        """
        self.navigator.navigate_to_db_instances()
        self.db_instance.react_instances_table.reload_data()
        self.select_instance()
        self.db_instance_details.click_on_entity(entity_name=self.tcinputs["database_name"])

    @test_step
    def get_home_path(self):
        """
        Gets Instance home path
        """
        self.home_path = self.client_machine.execute_command(command='echo $HOME').output.strip()
        self.log.info("Home path for the instance:%s", self.home_path)

    def sleep_and_wait(self, sleep_time):
        """
        Sleeps for given seconds
        Args:
            sleep_time        (int)       --  Time to sleep for
        """
        self.log.info("Sleeping for %s seconds.", sleep_time)
        time.sleep(sleep_time)

    @test_step
    def add_instance(self):
        """ Adding instance """
        self.db_instance.add_db2_instance(server_name=self.tcinputs["partition_node_client_1"],
                                          plan=self.tcinputs["plan"],
                                          instance_name=self.tcinputs["instance_name"],
                                          db2_home=self.home_path,
                                          db2_username=self.tcinputs["db2_username"],
                                          db2_user_password=self.tcinputs["db2_user_password"],
                                          pseudo_client_dpf=self.pseudo_client_name)

    @test_step
    def select_instance(self):
        """
        Selects the instance
        """
        self.db_instance.select_instance(database_type=self.dbtype,
                                         instance_name=self.tcinputs['instance_name'],
                                         client_name=self.pseudo_client_name)

    @test_step
    def add_backupset(self):
        """ Adding database """
        if self.tcinputs["database_name"] not in self.db_instance_details.get_instance_entities():
            self.db_instance_details.add_db2_database(database_name=self.tcinputs["database_name"],
                                                      plan=self.tcinputs["plan"])

    @test_step
    def add_subclient(self, name, data=True, logs=True, type_backup="online"):
        """
        Creates a subclient
        Args:
            name            (str)   --  Name of subclient to create
            data            (bool)  --  Data Backup enable for subclient
                default - True
            logs            (bool)   --  Log Backup enable for subclient
                default - True
            type_backup      (str): type of backup - online or offline
                default: online
        """
        if name not in self.db_backupset.list_subclients():
            self.db_backupset.add_db2_subclient(subclient_name=name,
                                                plan=self.tcinputs["plan"],
                                                data_backup=data,
                                                backup_logs=logs,
                                                type_backup=type_backup,
                                                partitioned_database=True)

    @test_step
    def update_db2_client_machine_property(self):
        """Edit db2 parameters on client to make them ready for backup"""

        agent = self.pseudo_client_object.agents.get("DB2 MultiNode")
        instance = agent.instances.get(self.tcinputs['instance_name'])
        backupset = instance.backupsets.get(self.tcinputs['database_name'])

        self.db2_helper = DB2MultiNode(commcell=self.commcell,
                                       pseudo_client=self.pseudo_client_object)

        self.db2_helper.db2_instance_setter(instance_object=instance,
                                            user=self.tcinputs["db2_username"],
                                            home_directory=self.home_path,
                                            backupset=backupset)
        self.db2_helper.run_db2_config_script(cold_backup_path="/dev/null")

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
        datafiles = self.db2_helper.get_datafile_locations()
        self.db2_helper.create_table2(datafiles=datafiles,
                                      tablespace_name=self.tablespace_name,
                                      table_name=f"SCHEMA{table_type}.{self.table_name}_{table_type}",
                                      flag_recreate_tablespace=create_tablespace)
        if create_tablespace:
            stogrp_created = self.db2_helper.create_storage_group(storage_group_name=self.sto_grp,
                                                                  path=self.home_path,
                                                                  flag_recreate_storage_group=True)
            if not stogrp_created:
                raise CVTestStepFailure("Storage group creation failed!")
            self.table_data = self.db2_helper.prepare_data(
                table_name=f"SCHEMA{table_type}.{self.table_name}_{table_type}")

    @test_step
    def run_backup(self, subclient, backup_type="Full"):
        """
        Runs backup
        Args:
            subclient       (str)   --  Subclient to run backup on
            backup_type               (str)               -- Type of backup
                default: Full

        Raises:
            Exception:
                If backup job fails
        """

        backup_job_id = self.db_backupset.db2_backup(subclient_name=subclient, backup_type=backup_type.lower())
        job = self.commcell.job_controller.get(backup_job_id)
        self.wait_for_job(job)

        self.db2_helper.reconnect()

        if "logs" not in subclient:
            online = False if "offline" in subclient.lower() else True
            self.validate_backup_job(backup_job_object=job,
                                     type_backup=backup_type,
                                     online=online)

    @test_step
    def validate_backup_job(self, backup_job_object=None, online=True,
                            type_backup="Full", cli_backup_timestamp=None):
        """
        Validates Backup Jobs
        Args:
            backup_job_object       (Job)   -- Backup Job Object
                default: None
            online                  (bool)  -- Online backup or not
                default: True
            type_backup             (str)   -- Backup type
                default: "Full"
            cli_backup_timestamp    (dict)  -- Cli backup timestamp
                default: None
        """
        if not cli_backup_timestamp:
            backup_time_stamp, _ = self.db2_helper.get_backup_time_stamp_and_streams(jobid=backup_job_object.job_id)
            commonutils = CommonUtils(self.commcell)
            commonutils.backup_validation(backup_job_object.job_id, type_backup)
        else:
            backup_time_stamp = cli_backup_timestamp
        backup_keys = {
            "full": {"offline": "F", "online": "N"},
            "incremental": {"offline": "I", "online": "O"},
            "differential": {"offline": "D", "online": "E"}
        }
        online_image = "online" if online else "offline"
        self.log.info("### Running Backup Validation ###")
        time.sleep(30)
        self.db2_helper.backup_validation(operation_type=backup_keys[type_backup.lower()][online_image.lower()],
                                          tablespaces_count=self.table_data[1],
                                          backup_time_stamp=backup_time_stamp)

        self.log.info("Successfully ran %s backup.", type_backup)

    @test_step
    def run_restore(self, recover=False, tablespace_list=None):
        """
        Runs restore/recover job
        Args:
            recover (bool)  --  Run recover job or not
                default: False
            tablespace_list (list)  --  List of tablespaces to restore
                default: None -> Complete Database restore

        Raises:
            Exception:
                If Restore Job Fails
        """
        if recover:
            self.log.info("####### Starting Recover Job #######")
        else:
            self.log.info("####### Starting Restore Job #######")
            self.db2_helper.delete_tablespace_file(tablespace_name=self.tablespace_name)
        self.db2_helper.disconnect_applications()
        self.db_backupset.access_restore()
        self.browse.show_latest_backups(database=True)
        self.log.info("Sleeping for 30 seconds.")
        time.sleep(30)
        if tablespace_list:
            restore_job = self.db_backupset.restore_folders(database_type=self.dbtype,
                                                            items_to_restore=tablespace_list)
        else:
            restore_job = self.db_backupset.restore_folders(database_type=self.dbtype, all_files=True)
        restore_job_id = restore_job.in_place_restore(endlogs=True, recover=recover)
        job = self.commcell.job_controller.get(restore_job_id)
        self.wait_for_job(job)

        all_jobs = self.commcell.job_controller.active_jobs(client_name=self.pseudo_client_name)
        for job_id in all_jobs:
            job = self.commcell.job_controller.get(job_id)
            self.wait_for_job(job)

        self.log.info("Restore Job Completed. Verifying the restore")
        self.db2_helper.reconnect()

    @test_step
    def validate_restore_job(self, table_name):
        """
        Validates Restore Jobs
        Args:
            table_name  (str)   --  Table Name to validate from
        """

        self.commcell.refresh()
        self.pseudo_client_object.refresh()

        if self.db2_helper.restore_validation(table_space=self.tablespace_name,
                                              table_name=table_name,
                                              tablecount_full=self.table_data[0]):

            self.log.info("Verified Restore.")
        else:
            raise Exception("Restore validation failed.")

    @test_step
    def validate_automatic_log_backup(self):
        """
        Validates Automatic log backup
        Raises:
            CVTestStepFailure:
                Automatic log backup did not run
        """
        current_file = self.db2_helper.get_active_logfile()[1]
        self.db2_helper.set_log_threshold_on_clients(threshold=5)
        self.db2_helper.db2_archive_log(archive_number_of_times=20)
        time.sleep(10)
        new_active_log_file = self.db2_helper.get_active_logfile()[1]
        if new_active_log_file == current_file:
            raise CVTestStepFailure("Archiving Log Failed")
        time.sleep(20)
        all_jobs = self.commcell.job_controller.finished_jobs(client_name=self.pseudo_client_name,
                                                              lookup_time=0.02,
                                                              job_filter="Backup")
        for job_id in all_jobs:
            if 'application' in all_jobs[job_id]['operation'].lower() and \
                    'restore' in all_jobs[job_id]['operation'].lower():
                continue
            job = self.commcell.job_controller.get(job_id)
            self.wait_for_job(job)
        self.db2_helper.remove_log_threshold()
        self.db2_helper.reconnect()

    @test_step
    def wait_for_job(self, job_object):
        """
        Waits for Job method
        Args:
            job_object (Job): Job object to wait for.

        Raises:
            CVTestStepFailure:
                If Job fails to complete.
        """
        self.log.info(f"Waiting for {job_object.job_type} Job to Complete (Job Id: {job_object.job_id})")
        if not job_object.wait_for_completion():
            raise CVTestStepFailure(f"{job_object.job_type} Job Failed with reason: {job_object.delay_reason}")

    @test_step
    def run_cmd_line_backup(self, backup_type="Full", online=True):
        """
        Runs backup
        Args:
            backup_type               (str)               -- Type of backup
                default: Full
            online                      (bool)              -- Online backup should be taken or not
                default: True
        """
        self.log.info("### Running CLI Backups ###")
        backup_timestamp = self.db2_helper.third_party_command_backup(backup_type=backup_type,
                                                                      online=online)
        self.db2_helper.reconnect()
        self.validate_backup_job(cli_backup_timestamp=backup_timestamp,
                                 type_backup=backup_type.lower(),
                                 online=online)

        return backup_timestamp

    @test_step
    def run_cmd_line_restore(self, backup_timestamp, online=True, recover=False):
        """
        Run command line
        Args:
            backup_timestamp (str)  -   Backup timestamp
            online           (bool) -   Backup image is online or not
                default: True
            recover          (bool) -   Run recover or not
                default: False
        """
        version = self.db2_helper.get_db2_version()
        self.db2_helper.disconnect_applications()
        if recover:
            self.db2_helper.third_party_command_recover()
        else:
            self.db2_helper.third_party_command_restore(backup_time=backup_timestamp,
                                                        version=version,
                                                        restore_cycle=True,
                                                        online=online)

        self.db2_helper.reconnect()

    def generate_tablespace_list(self, tablespace_name):
        """
        Generates tablespace list
        Args:
            tablespace_name (str)   --  Tablespace to generate list of nodes for
        """
        tablespace_list = list()
        for node in range(self.db2_helper.num_nodes):
            tablespace_list.append(f"{tablespace_name}_NODE{str(node).zfill(4)}")
        return tablespace_list

    @test_step
    def delete_database(self):
        """
        Deletes database if it exists
        """
        if self.tcinputs["database_name"] in self.db_instance_details.get_instance_entities():
            self.db_instance_details.delete_entity(self.tcinputs["database_name"])
        self.admin_console.refresh_page()
        self.commcell.refresh()

    @test_step
    def delete_instance(self):
        """Deletes instance"""
        self.db_instance_details.delete_instance()

    def tear_down(self):
        """ Logout from all the objects and close the browser. """
        self.admin_console.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
