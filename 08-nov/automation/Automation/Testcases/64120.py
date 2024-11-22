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
"64120": {
            "ClientName": "test_client",
            "AgentName": "DB2",
            "instance_name": "db2inst1",
            "database_name": "SAMPLE",
            "db2_username": "db2inst1",
            "db2_user_password": "test",
            "media_agent": "Linux_MA_name",
            "backup_location": "/ma"
        }

TestCase: Class for executing this test case

TestCase:

    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup the parameters and common object's necessary

    prerequisite_for_setup()                    -- Must needed steps to run the automation

    run()                                       --  run function of this test case

    create_storage()                            -- Creates a storage disk via command center

    create_plan()                               -- Creates a Plan with one min rpo enabled in command center

    enable_disk_cache()                         -- Enables one min rpo in given plan

    discover_instances()                        -- Discovers all DB2 Instances of given client

    select_instance()                           -- Goes to DB2 Instance details page of given DB2 instance

    refresh_commcell()                          --  Refreshes commcell properties and get updated client's properties

    edit_instance()                             --  Editing instance properties to add username and password and plan

    add_database()                              -- Adds given BACKUPSET to instance

    restart_commvault_services()                -- Restarts the commvault services on client computer

    initialize_db2_helper()                     -- Initializes db2 helper class object

    update_client_properties()                  --  Updating DB2 logging properties on client and takes cold backup

    add_data_to_database()                      --  Adds a tablespace and a table and populates the table with data

    backup_database()                           --  Takes a FULL Backup of given Database from command center

    get_active_log()                            --  Fetches DB2 Database active log file number using db2 helper

    generate_logs()                             -- Generates archive logs for given DB2 Database

    restore_database()                          -- Does a FULL Restore of given DB with latest browse options

    delete_instance()                           -- Deletes the DB2 instance

    delete_plan()                               -- Deletes the plan

    delete_storage()                            -- Deletes the storage disk

    cleanup()                                   -- Cleans up automation created data on both commvault and client

    tear_down()                                 --  Tear down method to clean up the entities
"""

from AutomationUtils.cvtestcase import CVTestCase
from Database.DB2Utils.db2helper import DB2
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import Db2InstanceDetails
from Web.AdminConsole.Databases.backupset import DB2Backupset
from Web.AdminConsole.Databases.subclient import DB2Subclient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Database.DB2Utils.db2helper import DB2
from AutomationUtils.machine import Machine
import time
from Web.AdminConsole.Components.page_container import PageContainer

class TestCase(CVTestCase):
    """ Command center: Backup and Restore History Check. """

    test_step = TestStep()

    def __init__(self):
        """Initial configs for test case"""
        super(TestCase, self).__init__()
        self.name = "DB2 One Min RPO Acceptance TestCase"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.dbtype = None
        self.db_instance = None
        self.db_instance_details = None
        self.db_backupset = None
        self.db_subclient = None
        self.client_displayname = None
        self.jobs_page = None
        self.plans_page = None
        self.plan_helper = None
        self.plan_detail = None
        self.storage_helper = None
        self.storage_name = None
        self.plan_name = None
        self.db2_helper = None
        self.archive_log_count = None
        self.instance = None
        self.backupset = None
        self.sub_client = None
        self.command_line_sub_client = None
        self.ma_obj = None
        self.operation = None
        self.tablespace_list = None
        self.tblcount_full = None
        self.tablespace_count = None
        self.table_name = None
        self.tablespace_name = None
        self.tcinputs = {
            "instance_name": None,
            "database_name": None,
            "db2_username": None,
            "db2_user_password": None,
            "media_agent": None,
            "backup_location": None
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
            self.dbtype = DBInstances.Types.DB2
            self.jobs_page = Jobs(admin_console=self.admin_console)
            self.client_displayname = self.client.display_name
            self.storage_helper = StorageMain(self.admin_console)
            self.plan_helper = PlanMain(self.admin_console)
            self.plans_page = Plans(self.admin_console)
            self.plan_detail = PlanDetails(self.admin_console)
            self.ma_obj = Machine(self.tcinputs["media_agent"], self.commcell)
            self.archive_log_count = 5
            self.storage_name = f"{self.tcinputs['media_agent']}Disk"
            self.plan_name = f"{self.id}Plan"
            self.plan_helper.plan_name = {"server_plan": self.plan_name}
            self.plan_helper.storage = {'pri_storage': self.storage_name,
                                        'pri_ret_period': '30',
                                        'ret_unit': 'Day(s)'}
            self.plan_helper.backup_data = None
            self.plan_helper.backup_day = None
            self.plan_helper.backup_duration = None
            self.plan_helper.rpo_hours = None
            self.plan_helper.allow_override = None
            self.plan_helper.snapshot_options = {'Enable_backup_copy': 'ON'}
            self.plan_helper.database_options = None
            self.operation = ['N', 'O', 'E']
            self.table_name = 'TBL64120'
            self.tablespace_name = 'TBS64120'
            self.page_container = PageContainer(self.admin_console)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def prerequisite_for_setup(self):
        """Prerequisites for test case to run"""
        try:
            self.delete_instance()
            self.delete_plan()
            self.delete_storage()
            if "windows" in self.client.os_info.lower():
                self.tcinputs["db2_username"] = self.client.client_hostname + "/" + self.tcinputs["db2_username"]
        except Exception as exception:
            self.log.info("Failed establishing prerequisite setup for testcase")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def create_storage(self):
        """ Creates a storage disk """
        try:
            self.log.info("Creating a storage disk")
            self.storage_helper.add_disk_storage(disk_storage_name=self.storage_name,
                                                 media_agent=self.tcinputs["media_agent"],
                                                 backup_location=self.tcinputs["backup_location"])
            self.log.info("Successfully created a storage disk")
        except Exception as exception:
            self.log.info("Failed to create storage disk")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def enable_disk_cache(self):
        """Enables disk cache option in plan"""
        try:
            self.navigator.navigate_to_plan()
            self.admin_console.refresh_page()
            self.plans_page.select_plan(self.plan_name)
            self.plan_detail.edit_database_options(use_disk_cache=True, commit_every=1)
            self.admin_console.refresh_page()
            self.log.info(f"Successfully enabled the disk cache for plan {self.plan_name}")
        except Exception as exception:
            self.log.info("Failed to enable the disk cache option inside plan")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def create_plan(self):
        """ Creates a plan with disk cache option enabled """
        try:
            self.log.info(f"Creating a plan {self.plan_name}")
            self.plan_helper.add_plan()
            self.refresh_commcell()
            self.log.info(f"Successfully created the plan")
            self.log.info("Enabling disk cache option in plan")
            self.enable_disk_cache()
            self.log.info("Successfully enabled disk cache option in plan")
        except Exception as exception:
            self.log.info("Failed to create the plan with disk cache enabled")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def discover_instances(self):
        """ Discovers all DB2 Instance's of given client"""
        try:
            self.navigator.navigate_to_db_instances()
            self.db_instance.discover_instances(self.dbtype, self.client_displayname)
            self.refresh_commcell()
            self.admin_console.refresh_page()
        except Exception as exception:
            self.log.info("Failed to Discover the instances of given client")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def select_instance(self):
        """Selects and navigates to given DB2 instance"""
        try:
            self.navigator.navigate_to_db_instances()
            self.admin_console.refresh_page()
            self.db_instance.select_instance(self.dbtype, self.tcinputs["instance_name"], self.client_displayname)
        except Exception as exception:
            self.log.info("Unable to find the given instance in DB instances page")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def edit_instance(self):
        """ Edits the instance properties of DB2 client """
        try:
            self.db_instance_details.db2_edit_instance_properties(username=self.tcinputs["db2_username"],
                                                                  password=self.tcinputs["db2_user_password"],
                                                                  plan=self.plan_name)
        except Exception as exception:
            self.log.info("Failed to edit instance properties")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def add_database(self):
        """ Discovers all databases inside DB2 client """
        try:
            self.admin_console.refresh_page()
            if self.tcinputs["database_name"] not in self.db_instance_details.get_instance_entities():
                self.db_instance_details.add_db2_database(self.tcinputs["database_name"], self.plan_name)
                self.refresh_commcell()
                self.admin_console.refresh_page()
            else:
                self.log.info("Backupset already exists")
        except Exception as exception:
            self.log.info("Error while adding database")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def restart_commvault_services(self):
        """Restarts the commvault's services on client machine"""
        try:
            self.client._service_operations(operation="RESTART")
            self.log.info("Waiting for commvault services to restart on client to ensure one min rpo is enabled")
            time.sleep(200)
            self.refresh_commcell()
        except Exception as exception:
            self.log.info(f"Failed to restart the services on client machine {exception}")

    @test_step
    def initialize_db2_helper(self):
        """Initializes db2 helper object"""
        try:
            self.instance = self.agent.instances.get(self.tcinputs['instance_name'])
            self.backupset = self.instance.backupsets.get(self.tcinputs['database_name'])
            self.sub_client = self.backupset.subclients.get("default")
            self.command_line_sub_client = self.backupset.subclients.get("(command line)")
            self.db2_helper = DB2(self.commcell, self.client, self.instance, self.backupset)
            self.refresh_commcell()
        except Exception as exception:
            self.log.info("Failed to initialize db2 helper of any of its parameters")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def update_client_properties(self):
        """ Updates logarchmeth1, logarchopt1 and vendoropt properties in client machine"""
        try:
            if "unix" in self.client.os_info.lower():
                backup_path = "/dev/null"
                self.log.info(f"Cold backup will be taken to the path {backup_path}")
            else:
                install_loc = self.client.install_directory
                backup_path = f"{install_loc}\\Base\\Temp"
                self.log.info(f"Cold backup will be taken to the path {backup_path}")
            self.db2_helper.update_db2_database_configuration1(cold_backup_path=backup_path)
        except Exception as exception:
            self.log.info("Failed to update the client machine properties or to take Database backup")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def add_data_to_database(self):
        """Adds tablespace , table to given database such that backup and restore can be validated"""
        try:
            datafile = self.db2_helper.get_datafile_location()
            self.log.info(
                f"creating the tablespace {self.tablespace_name} inside database {self.tcinputs['database_name']}")
            self.log.info(
                f"creating the table {self.table_name+'_FULL'} inside tablespace {self.tablespace_name}")
            self.db2_helper.create_table2(datafile, self.tablespace_name, self.table_name+'_FULL', True)
            self.log.info("Getting require parameters to validate backup and restore")
            (self.tblcount_full, self.tablespace_list, self.tablespace_count) = self.db2_helper.prepare_data(
                self.table_name+'_FULL')
            self.log.info(f"Rows count in the created table are {self.tblcount_full}")
            self.log.info(f"Tablespace list in the given database is {self.tablespace_list}")
            self.log.info(f"Tablespace count in the given database is {self.tablespace_count}")
        except Exception as exception:
            self.log.info(f"Failed to add data into the database {self.tcinputs['database_name']}")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def backup_database(self):
        """ Backup's the Database with full database backup option """
        try:
            self.update_client_properties()
            self.db_instance_details.click_on_entity(self.tcinputs["database_name"])
            self.sub_client.storage_policy = self.plan_name
            self.command_line_sub_client.storge_policy = self.plan_name
            self.refresh_commcell()
            self.admin_console.refresh_page()
            self.page_container.select_entities_tab()
            job_id = self.db_backupset.db2_backup(subclient_name="default", backup_type="full")
            job = self.commcell.job_controller.get(job_id)
            self.log.info(f"Waiting for backup job to get completed, id = {job_id}")
            job_status = job.wait_for_completion()
            if not job_status:
                raise CVTestStepFailure("Backup Job Failed for DB2!")
            self.db2_helper.reconnect()
            (backup_time_stamp, streams) = self.db2_helper.get_backup_time_stamp_and_streams(job_id)
            self.log.info("Started backup validation !!")
            self.db2_helper.backup_validation(self.operation[0], self.tablespace_list, backup_time_stamp)
            self.log.info(f"Successfully validated backup job {job_id}")
            return job_id
        except Exception as exception:
            self.log.info(f"Failed to validate or to backup the database")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def get_active_log(self):
        """ gets current active log file number """
        try:
            self.log.info(f"Fetching the active log file of DB {self.tcinputs['database_name']}")
            self.db2_helper.reconnect()
            active_log_number = self.db2_helper.get_active_logfile()[1]
            self.log.info(f"Active log file number of given DB {self.tcinputs['database_name']} is {active_log_number}")
            return active_log_number
        except Exception as exception:
            self.log.info(f"Failed to get active log number of db {self.tcinputs['database_name']}")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def generate_logs(self):
        """ Generates archive logs for DB """
        try:
            self.db2_helper.reconnect()
            self.db2_helper.db2_archive_log(self.tcinputs["database_name"], self.archive_log_count)
        except Exception as exception:
            self.log.info("Failed to generate the archive logs")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def restore_database(self):
        """ Restores DB with default options and latest browse """
        try:
            self.navigator.navigate_to_db_instances()
            self.select_instance()
            self.db_instance_details.click_on_entity(self.tcinputs["database_name"])
            self.db_backupset.access_restore()
            restore_job = self.db_backupset.restore_folders(database_type=self.dbtype, all_files=True)
            restore_job_id = restore_job.in_place_restore(endlogs=True)
            job = self.commcell.job_controller.get(restore_job_id)

            self.log.info(f"Waiting for Restore Job to Complete (Job Number: {restore_job_id})")
            job_status = job.wait_for_completion()

            all_jobs = self.commcell.job_controller.active_jobs(client_name=self.client_displayname)
            for job_id in all_jobs:
                job = self.commcell.job_controller.get(job_id)
                self.log.info(f"Waiting for Jobs to Complete (Job Id: {job_id})")
                job_status = job.wait_for_completion()

            self.log.info("Validating the restore of given database")
            self.db2_helper.reconnect()
            self.log.info(f"parameters that are passed for "
                          f"restore are {self.tablespace_name, self.table_name, self.tblcount_full}")
            self.db2_helper.restore_validation(self.tablespace_name, self.table_name, self.tblcount_full)
            self.log.info("Successfully validated the restore of given db")

            if not job_status:
                raise CVTestStepFailure("Restore Job Failed for DB2!")

        except Exception as exception:
            self.log.info(f"Failed to restore the db {self.tcinputs['database_name']}")
            raise CVTestStepFailure(exception) from exception

    def run(self):
        """ Main method to run test case """
        try:
            self.prerequisite_for_setup()
            self.create_storage()
            self.create_plan()
            self.discover_instances()
            self.select_instance()
            self.edit_instance()
            self.add_database()
            self.restart_commvault_services()
            self.initialize_db2_helper()
            self.add_data_to_database()
            job_id = self.backup_database()
            self.db2_helper.verify_one_min_rpo(job_id)
            active_log_number = self.get_active_log()
            self.generate_logs()
            self.db2_helper.verify_logs_on_ma(active_log_number, self.ma_obj)
            self.restore_database()
            self.log.info("************ TC PASSED *************")
        except Exception as exception:
            self.log.info(f"Testcase Failed with the exception {exception}")
            raise CVTestStepFailure(exception) from exception
        finally:
            self.cleanup()

    @test_step
    def delete_instance(self):
        """ Deletes DB2 Instance """
        self.navigator.navigate_to_db_instances()
        try:
            if self.db_instance.is_instance_exists(self.dbtype, self.tcinputs["instance_name"],
                                                   self.client_displayname):
                self.db_instance.select_instance(self.dbtype, self.tcinputs["instance_name"], self.client_displayname)
                self.db_instance_details.delete_instance()
            else:
                self.log.info("Instance Doesn't exist to delete")
        except Exception as exception:
            self.log.info("Deletion of Instance failed as Instance doesn't exist")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def delete_plan(self):
        """ Deletes Plan """
        self.navigator.navigate_to_plan()
        try:
            if self.plan_name in self.plans_page.list_plans():
                self.plans_page.delete_plan(self.plan_name)
            else:
                self.log.info("Plan Doesn't exist to delete")
        except Exception as exception:
            self.log.info(f"Deletion of plan failed as plan {self.plan_name} doesn't exist")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def delete_storage(self):
        """ Deletes Storge Disk """
        self.navigator.navigate_to_disk_storage()
        self.admin_console.refresh_page()
        try:
            if self.storage_name in self.storage_helper.list_disk_storage():
                self.storage_helper.delete_disk_storage(self.storage_name)
            else:
                self.log.info(f"Deletion of disk storage failed as {self.storage_name} doesn't exist")
        except Exception as exception:
            self.log.info("Deletion of disk failed as disk doesn't exist")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def cleanup(self):
        """Cleanup method for test case"""
        try:
            if self.db2_helper is not None:
                self.log.info("Deleting Automation Created Tablespaces")
                self.db2_helper.reconnect()
                self.db2_helper.drop_tablespace(self.tablespace_name)
            else:
                self.log.info("Unable to connect to database to delete automation created tablespaces")
            self.log.info("Deleting the given DB2 Instance from the command center")
            self.delete_instance()
            self.log.info(f"Deleting the automation created plan {self.plan_name} from command center")
            self.delete_plan()
            self.log.info(f"Deleting the automation created storage disk {self.storage_name} from command center")
            self.delete_storage()
        except Exception as exception:
            self.log.info(f"Error in cleanup method with the exception {exception}")
            raise CVTestStepFailure(exception) from exception

    @test_step
    def refresh_commcell(self):
        """ Refreshes the commcell """
        self.commcell.refresh()

    def tear_down(self):
        """ Logout from all the objects and close the browser. """

        self.admin_console.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
