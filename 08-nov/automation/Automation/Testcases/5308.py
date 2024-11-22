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
"5308": {
            "ClientName": "test_client",
            "AgentName": "DB2",
            "instance_name": "db2inst1",
            "database_name": "SAMPLE",
            "db2_username" : "dbusername",
            "db2_user_password" : "dbpassword",
            "number_of_streams": 4,
            "plan": "BackupPlan"
        }

TestCase: Class for executing this test case

TestCase:
    __init__()                          --  initialize TestCase class

    setup()                             --  set up the parameters and common object necessary

    run()                               --  run function of this test case

    refresh_commcell()                  --  Refreshes commcell properties and get updated client's properties

    run_backup()                        --  Runs a backup

    run_restore()                        --  Runs a restore

    tear_down()                         --  Tear down method to clean up the entities

    cleanup()                           --  Deleting the subclient
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Database.DB2Utils.db2helper import DB2
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import Db2InstanceDetails
from Web.AdminConsole.Databases.backupset import DB2Backupset
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.Components.page_container import PageContainer


class TestCase(CVTestCase):
    """ Command center: DB2 Restore to a New Database from Online Backup """

    test_step = TestStep()

    def __init__(self):
        """Initial configs for test case"""
        super(TestCase, self).__init__()
        self.name = "DB2 Restore to a New Database from Online Backup"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_instance = None
        self.db_instance_details = None
        self.db_backupset = None
        self.db2_helper = None
        self.client_displayname = None
        self.dbtype = None
        self.client_machine = None
        self.dest_db = None
        self.redirect_path = None
        self.table_name = None
        self.sto_grp = None
        self.tablespace_name = None
        self.tblcount_full = None
        self.tablespace_list = None
        self.operation = ['N', 'O', 'E']
        self.page_container = None
        self.tcinputs = {
            "instance_name": None,
            "database_name": None,
            "number_of_streams": None,
            "plan": None,
            "db2_username": None,
            "db2_user_password": None
        }

    def setup(self):
        """ Required setups for test case. """
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
            self.client_displayname = self.client.display_name
            self.dbtype = DBInstances.Types.DB2
            self.dest_db = f"DES{self.id}"
            self.sto_grp = f"STG{self.id}"
            self.table_name = f"T{self.id}"
            self.tablespace_name = f"TS{self.id}"
            self.page_container = PageContainer(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """ Main method to run test case
            Raises:
                Exception:
                    If database is not present for that instance
        """
        try:
            self.prerequisite_setup_test_case()
            self.refresh_commcell()
            self.db_instance_details.click_on_entity(entity_name=self.tcinputs["database_name"])
            self.add_subclient()
            self.refresh_commcell()
            self.navigator.navigate_to_db_instances()
            self.db_instance.select_instance(database_type=self.dbtype,
                                             instance_name=self.tcinputs["instance_name"],
                                             client_name=self.client_displayname)
            self.db_instance_details.click_on_entity(entity_name=self.tcinputs["database_name"])
            self.page_container.select_entities_tab()
            self.tblcount_full, self.tablespace_list = self.db2_helper.add_data_to_database(self.tablespace_name, self.table_name, self.tcinputs["database_name"])
            self.run_backup()
            self.run_restore()
            self.log.info('****** Test Case %s Passed ******', self.id)
            self.cleanup()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    @test_step
    def prerequisite_setup_test_case(self):
        """ Prerequisite setup for test case """
        self.navigator.navigate_to_db_instances()
        self.delete_instance()
        self.refresh_commcell()
        self.discover_instance()
        self.db_instance.select_instance(database_type=self.dbtype,
                                         instance_name=self.tcinputs["instance_name"],
                                         client_name=self.client_displayname)
        if "windows" in self.client.os_info.lower():
            self.tcinputs["db2_username"] = self.client_displayname + "/" + self.tcinputs["db2_username"]

        self.edit_instance_property()
        self.add_database(self.tcinputs['database_name'])
        instance = self.agent.instances.get(self.tcinputs['instance_name'])
        backupset = instance.backupsets.get(self.tcinputs['database_name'])
        self.db2_helper = DB2(commcell=self.commcell,
                              client=self.client,
                              instance=instance,
                              backupset=backupset)
        self.db2_helper.remove_existing_logs_dir(instance_name=self.tcinputs["instance_name"], dest_db=self.dest_db)
        self.db2_helper.drop_database_on_client(database_name=self.dest_db)
        self.redirect_path = self.db2_helper.get_redirect_path(database_name=self.tcinputs["database_name"])

    @test_step
    def discover_instance(self):
        """
        Discover Instances if not exist already
        """
        if not self.db_instance.is_instance_exists(database_type=self.dbtype,
                                                   instance_name=self.tcinputs["instance_name"],
                                                   client_name=self.client_displayname):
            self.db_instance.discover_instances(database_engine=self.dbtype,
                                                server_name=self.client_displayname)
            self.refresh_commcell()
            self.admin_console.refresh_page()
            self.db_instance.react_instances_table.reload_data()

    @test_step
    def edit_instance_property(self):
        """
        Changes DB2 instance properties.
        """
        self.db_instance_details.db2_edit_instance_properties(username=self.tcinputs["db2_username"],
                                                              password=self.tcinputs["db2_user_password"],
                                                              plan=self.tcinputs["plan"])
        self.admin_console.refresh_page()

    @test_step
    def add_database(self, database_name):
        """
        Adds database if it does not exist
        """
        self.refresh_commcell()
        self.admin_console.refresh_page()
        self.db_instance_details.discover_databases()
        self.admin_console.refresh_page()
        if database_name not in self.db_instance_details.get_instance_entities():
            self.db_instance_details.add_db2_database(database_name=database_name,
                                                      plan=self.tcinputs["plan"])
            self.admin_console.refresh_page()

    @test_step
    def add_subclient(self):
        """
        Creates subclient if does not exist
        """
        if self.id not in self.db_backupset.list_subclients():
            self.db_backupset.add_db2_subclient(subclient_name=self.id,
                                                plan=self.tcinputs["plan"],
                                                number_data_streams=self.tcinputs["number_of_streams"],
                                                type_backup="online",
                                                backup_logs=True)
    @test_step
    def refresh_commcell(self):
        """ Refreshing Commcell object to refresh the properties after adding new properties. """
        self.commcell.refresh()

    @test_step
    def run_backup(self):
        """Runs backup
            Raises:
                Exception:
                    If backup job fails
        """

        full_backup_job_id = self.db_backupset.db2_backup(subclient_name=self.id,
                                                          backup_type="full")

        job = self.commcell.job_controller.get(int(full_backup_job_id))
        self.log.info("Waiting for Backup to Complete (Job Id: %s)", full_backup_job_id)
        job_status = job.wait_for_completion()

        self.log.info("Started backup validation !!")
        self.db2_helper.reconnect()
        (backup_time_stamp, streams) = self.db2_helper.get_backup_time_stamp_and_streams(full_backup_job_id)
        self.db2_helper.backup_validation(self.operation[0], self.tablespace_list, backup_time_stamp)
        self.log.info(f"Successfully validated backup job {full_backup_job_id}")

        if not job_status:
            raise CVTestStepFailure("Backup Job Failed for DB2!")

    @test_step
    def run_restore(self):
        """Runs restore
                Raises:
                    Exception:
                        If restore job fails
        """

        self.page_container.select_overview_tab()
        self.db_backupset.access_restore()
        restore_job = self.db_backupset.restore_folders(database_type=self.dbtype, all_files=True)
        restore_job_id = restore_job.out_of_place_restore(destination_client=self.client.display_name,
                                                          destination_instance=self.tcinputs["instance_name"],
                                                          destination_db=self.dest_db,
                                                          target_db_path=self.redirect_path,
                                                          endlogs=True
                                                          )
        job = self.commcell.job_controller.get(restore_job_id)
        self.log.info("Waiting for Restore Job to Complete (Job Id: %s)", restore_job_id)
        job_status = job.wait_for_completion()

        all_jobs = self.commcell.job_controller.active_jobs(client_name=self.client.display_name)
        for job_id in all_jobs:
            job = self.commcell.job_controller.get(job_id)
            self.log.info("Waiting for Jobs to Complete (Job Id: %s)", job_id)
            job_status = job.wait_for_completion()

        self.log.info("Validating the restore of given database")
        self.db2_helper.reconnect()
        self.log.info(f"parameters that are passed for "
                      f"restore are {self.tablespace_name, self.table_name, self.tblcount_full}")
        self.db2_helper.restore_validation(self.tablespace_name, self.table_name, self.tblcount_full)
        self.log.info("Successfully validated the restore of given db")

        if not job_status:
            raise CVTestStepFailure("Restore Job Failed for DB2!")

    @test_step
    def delete_instance(self):
        """Deletes instance if exist"""
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
    def cleanup(self):
        """Cleanup method for test case"""
        self.navigator.navigate_to_db_instances()
        self.delete_instance()

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Deleting Automation Created databases")
        if self.db2_helper is not None:
            self.db2_helper.drop_tablespace(self.tablespace_name)
