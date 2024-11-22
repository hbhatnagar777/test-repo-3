# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""ACCT-1-MySQL - instant app recovery feature

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    set_pit()       -- set the Point In Time (PIT) for instant clone

    backup()        -- perform a backup of the specified type (full or incremental or synthetic)

    check_backup_copy()     -- check and verify the backup copy job

    instance_clone()     -- clone a MySQL instance to the specified destination

    check_mysql_settings()  -- check and ensure MySQL settings are configured correctly

    check_backup_job_type_expected()    -- check if the backup job type matches the expected type

    create_mysql_helper_object()    -- create an object of the SDK mysqlhelper class

    create_test_data()    -- create test databases and optionally add tables to them

    clean_temp()          -- clean the temp directory for clones

    navigate_to_instance()    -- navigate to the MySQL instance page

    restore_validate(start, to)    -- validate data after restore process

    gen_db_map()    -- generate a map of the database state

    cleanup_test_data()    -- clean up the test data created for automation

    cleanup()              --  method to cleanup all testcase created changes

    run()           --  run function of this test case

    tear_down()     -- tear down function of the test case

Input Example:
    "testCases":
        {
            "50214": {
                    "ClientName" : "name of client host machine",
                    "InstanceName" : "name of the instance",
                    "SocketFile" : "Directory of socket file",
                    "db_port"   : "port running mysql database"
                    "dest_client" : "destination server for instant clone",
                    "dest_instance" : "destination instance for clone"
                    "clone_dir" : "clone working dir for clone",
                    "clone_port" : "port for clone",
                    "db_user" : "username of database user",
                    "bin_dir" : "path to bin files of mysql"
                    }
        }
"""

from datetime import datetime
from cvpysdk.job import Job
from AutomationUtils import machine
from AutomationUtils.cvtestcase import CVTestCase
from Database.dbhelper import DbHelper
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Databases.Instances.instant_clone import MySQLInstantClone
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import MySQLInstanceDetails
from Web.AdminConsole.Components.dialog import RBackup
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Web.Common.exceptions import CVTestStepFailure, CVWebAutomationException


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """
        Initializes test case class object
        """
        super().__init__()
        self.name = "ACCT-1-MySQL - instant app recovery feature"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_instance = None
        self.db_instance_details = None
        self.instant_clone = None
        self.helper_object = None
        self.database_subclient = None
        self.dbhelper = None
        self.db_group = None
        self.restore_panel = None
        self.tcinputs = {
            "ClientName": None,
            "InstanceName": None,
            "SocketFile": None,
            "db_port": None,
            "dest_client": None,
            "dest_instance": None,
            "clone_dir": None,
            "clone_port": None,
            "db_user": None,
            "bin_dir": None
        }
        self.database_list = None
        self.db_map = dict()
        self.full_backup = None
        self.incr_backup = None
        self.synth_backup = None
        self.last_job = None
        self.last_job_type = None
        self.job = None
        self.first_job = None

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
        self.job = Jobs(self.admin_console)
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance_details = MySQLInstanceDetails(self.admin_console)
        self.dbhelper = DbHelper(self.commcell)
        self.instant_clone = MySQLInstantClone(self.admin_console)
        self.db_group = MySQLSubclient(self.admin_console)
        self.full_backup = RBackup.BackupType.FULL
        self.incr_backup = RBackup.BackupType.INCR
        self.synth_backup = RBackup.BackupType.SYNTH

    @test_step
    def set_pit(self):
        """Sets the Point In Time (PIT) to the current time."""
        current_time = datetime.now()
        formatted_time = current_time.strftime("%m/%d/%Y %H:%M:%S")
        self.first_job = formatted_time
        self.log.info(f"Set PIT to {formatted_time}")

    @test_step
    def backup(self, backup_type, data_for_inc=False):
        """
        Helper function for performing backups.
        Args:
            backup_type: full_backup, incr_backup
            data_for_inc: Boolean to enable data for incremental backups
        """
        self.navigate_to_instance()
        self.database_subclient = self.client.agents.get('mysql').instances.get(
            self.tcinputs["InstanceName"]).subclients.get('default')
        self.log.info(f"Starting {backup_type} backup.")
        if backup_type == self.incr_backup:
            self.log.info(f"Incremental backup with data - {data_for_inc}")
        self.db_instance_details.click_on_entity('default')
        job_id = self.db_group.backup(backup_type=backup_type, enable_data_for_incremental=data_for_inc)
        if backup_type == self.synth_backup:
            job_id = str(job_id[0])
        self.dbhelper.wait_for_job_completion(job_id)
        self.last_job = job_id
        self.last_job_type = backup_type
        self.log.info(f"Backup completed successfully. Job ID: {job_id}")

    @test_step
    def check_backup_copy(self):
        """Checks the backup copy job."""
        self.dbhelper.get_backup_copy_job(self.last_job)

    @test_step
    def instance_clone(self, dest_client, dest_instance, port, clone_dir, custom=False, db_user=None,
                       bin_dir=None, pit="recent", overwrite=None):
        """
        Clones an instance.
        Args:
            dest_client: Destination client name
            dest_instance: Destination instance name
            port: Port number for cloned mysql database
            clone_dir: Clone working directory
            custom: (bool) use if providing custom username and bin_dir (optional, default-False)
            db_user: Database user (optional)
            bin_dir: Binary directory (optional)
            pit: Point in Time (optional, default-Most recent backup)
            overwrite: (bool) Overwrite existing instance (optional, default-False)
        """
        if pit == "recent":
            self.log.info(f"Cloning from Most recent backup from {self.last_job_type} with job id {self.last_job}")
            pit = "Most recent backup"
        else:
            self.log.info(f"Cloning from pit {pit} from first full backup")
        self.navigator.navigate_to_db_instances()
        self.db_instance.access_instant_clones_tab()
        self.instant_clone = self.db_instance.instant_clone(database_type=DBInstances.Types.MYSQL,
                                                            source_server=self.tcinputs['ClientName'],
                                                            source_instance=self.tcinputs["InstanceName"])
        job_details = self.instant_clone.instant_clone(
            destination_client=dest_client, destination_instance=dest_instance, custom=custom, port=port,
            clone_directory=clone_dir, username=db_user, binary_dir=bin_dir,
            recover_to=pit, overwrite=overwrite)
        job_id, bin_username = job_details[0], job_details[1]
        if not custom:
            self.log.info("Validating binary dir and username from csdb")
            query = ("SELECT "
                     "MAX(CASE WHEN p.attrName = 'MySQL binary file path' THEN p.attrVal END) AS bin_file, "
                     "MAX(CASE WHEN p.attrName = 'MySQL SA user' THEN p.attrVal END) AS username "
                     "FROM APP_InstanceProp p "
                     "JOIN APP_InstanceName n ON p.componentNameId = n.id "
                     f"WHERE n.name = '{self.tcinputs['InstanceName']}';")
            self.csdb.execute(query)
            cur = self.csdb.fetch_all_rows()
            bin_csdb, bin_modal = cur[0][0].rstrip('/').rstrip('\\'), bin_username[0].rstrip('/').rstrip('\\')
            user_csdb, user_modal = cur[0][1], bin_username[1]
            if bin_csdb != bin_modal and user_csdb != user_modal:
                raise CVTestStepFailure("Failed to confirm username and binary dir")
        self.dbhelper.wait_for_job_completion(job_id)
        self.log.info(f"Cloned instance to {dest_instance} on {dest_client}. With job {job_id}")

    @test_step
    def check_mysql_settings(self):
        """Checks MySQL settings and ensures log_bin is enabled."""
        self.helper_object.basic_setup_on_mysql_server(log_bin_check=True)
        self.log.info("Checked MySQL settings and ensured log_bin is enabled.")

    @test_step
    def check_backup_job_type_expected(self, job_id, job_type):
        """
        Checks if the job type is as expected.
        Args:
            job_id (int): Job ID to be checked
            job_type (str): Expected job type
        """
        job_info = Job(self.commcell, job_id)
        job_type_from_cs = job_info.backup_level
        if job_type_from_cs.lower() == job_type.lower():
            self.log.info(f"The job {job_id} was of type {job_type}.")
            return True
        else:
            error_msg = f"Job {job_id} is not of expected type {job_type}. Found type: {job_type_from_cs}."
            self.log.error(error_msg)
            raise CVTestStepFailure(error_msg)

    @test_step
    def create_mysql_helper_object(self, socket_file, port, entity=None):
        """
        Creates object of SDK mysqlhelper class.
        Args:
            socket_file: MySQL socket file
            port: MySQL port
            entity: Optional entity (to make helper object for clones)
        """
        connection_info = {
            'client_name': self.tcinputs["ClientName"],
            'instance_name': self.tcinputs["InstanceName"],
            'socket_file': socket_file
        }
        if entity is None:
            self.helper_object = MYSQLHelper(
                commcell=self.commcell, hostname=self.commcell.clients.get(self.tcinputs["ClientName"]).client_hostname,
                user='root', port=port, connection_info=connection_info)
            self.log.info("Created MySQL helper object.")
        else:
            clone_object = MYSQLHelper(
                commcell=self.commcell, hostname=self.commcell.clients.get(self.tcinputs["ClientName"]).client_hostname,
                user='root', port=port, connection_info=connection_info)
            self.log.info("Created MySQL helper clone object.")
            return clone_object

    @test_step
    def create_test_data(self, add_table=False):
        """
        Creates test databases according to input.
        Args:
            add_table: Boolean to add tables to the created database or make a new database(optional)
        """
        if not add_table:
            db_list = self.helper_object.generate_test_data(num_of_databases=1)
            self.database_list = db_list
            self.log.info(f"Created test databases: {db_list}")
        else:
            self.helper_object.create_table_with_text_db(database_name=self.database_list[0], no_of_tables=2)
            self.log.info(f"Added tables to database {self.database_list[0]}")

    @test_step
    def clean_temp(self):
        """
        Removes temporary directories on all cluster nodes.
        """
        machine_object = machine.Machine(self.commcell.clients.get(self.tcinputs["ClientName"]))
        query = f'rm -rf {self.tcinputs["clone_dir"]}/*'
        self.log.info(f"cleaning clone directory")
        machine_object.execute(query)

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page."""
        self.log.info("Navigating to MySQL Instance page.")
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance.select_instance(DBInstances.Types.MYSQL, self.tcinputs["InstanceName"],
                                         self.tcinputs["ClientName"])

    @test_step
    def restore_validate(self, before, after):
        """
        Executes restore according to restore type input and validates restore.
        Args:
            before: db_map for before the restore
            after: db_map for after the restore
        """
        self.helper_object.validate_db_info(self.db_map[before], self.db_map[after])
        self.log.info(f"Validated restore from {before} to {after}")

    @test_step
    def gen_db_map(self, when, entity=None):
        """
        Generates database map.
        Args:
            when: Time when the map is generated
            entity: Optional (to generate maps for clone)
        """
        if entity is None:
            self.db_map[when] = self.helper_object.get_database_information()
            self.log.info(f"Generated database map {when}")
            self.log.info(self.db_map[when])
        else:
            temp_object = self.create_mysql_helper_object(socket_file=f"{self.tcinputs['working_dir']}"
                                                                      f"/mysql_{self.last_job}.sock",
                                                          port=self.tcinputs["clone_port"], entity=entity)
            self.db_map[when] = temp_object.get_database_information()
            self.log.info(f"Generated database map {when} for {entity}")

    @test_step
    def cleanup_test_data(self):
        """Cleans up test data."""
        self.helper_object.cleanup_test_data("automation")
        self.log.info("Cleaned up test data.")

    @test_step
    def cleanup(self):
        """Removes testcase created changes"""
        try:
            self.clean_temp()
            self.cleanup_test_data()
        except Exception as e:
            self.log.error(e)

    def run(self):
        """Run function of this test case"""
        try:
            self.create_mysql_helper_object(socket_file=self.tcinputs["ClientName"], port=self.tcinputs["db_port"])
            self.check_mysql_settings()
            self.create_test_data()
            self.gen_db_map("beforeFULL1")
            self.backup(self.full_backup)
            self.set_pit()
            self.check_backup_job_type_expected(self.last_job, "full")
            self.check_backup_copy()
            self.create_test_data()
            self.gen_db_map("beforeINC1")
            self.backup(self.incr_backup)
            self.check_backup_job_type_expected(self.last_job, "incremental")
            self.instance_clone(dest_client=self.tcinputs["dest_client"], dest_instance=self.tcinputs["dest_instance"],
                                clone_dir=self.tcinputs["clone_dir"], port=self.tcinputs["clone_port"])
            self.gen_db_map("afterClone1", "clone")
            self.restore_validate("beforeINC1", "afterClone1")
            self.clean_temp()
            self.create_test_data(add_table=True)
            self.backup(self.incr_backup, data_for_inc=True)
            self.gen_db_map("beforeINC2")
            self.check_backup_copy()
            self.create_test_data(add_table=True)
            self.gen_db_map("beforeINC3")
            self.backup(self.incr_backup)
            self.check_backup_job_type_expected(self.last_job, "incremental")
            self.instance_clone(dest_client=self.tcinputs["dest_client"], dest_instance="< Custom >",
                                clone_dir=self.tcinputs["clone_dir"], port=self.tcinputs["clone_port"],
                                db_user=self.tcinputs["db_user"], bin_dir=self.tcinputs["bin_dir"], custom=True)
            self.gen_db_map("afterClone2", "clone")
            self.restore_validate("beforeINC3", "afterClone2")
            self.create_test_data(add_table=True)
            self.gen_db_map("beforeSYNTH1")
            self.backup(self.synth_backup)
            self.check_backup_job_type_expected(self.last_job, "incremental")
            self.instance_clone(dest_client=self.tcinputs["dest_client"], dest_instance="< Custom >",
                                clone_dir=self.tcinputs["clone_dir"], port=self.tcinputs["clone_port"],
                                db_user=self.tcinputs["db_user"], bin_dir=self.tcinputs["bin_dir"],
                                overwrite=True, custom=True)
            self.gen_db_map("afterClone3", "clone")
            self.restore_validate("beforeSYNTH1", "afterClone3")
            self.instance_clone(dest_client=self.tcinputs["dest_client"], dest_instance="< Custom >",
                                clone_dir=self.tcinputs["clone_dir"], port=self.tcinputs["clone_port"],
                                db_user=self.tcinputs["db_user"], bin_dir=self.tcinputs["bin_dir"],
                                overwrite=True, pit=self.first_job, custom=True)
            self.gen_db_map("afterClone4", "clone")
            self.restore_validate("beforeFULL1", "afterClone4")

        except Exception:
            raise CVWebAutomationException('Test case failed')

        finally:
            self.cleanup()

    def tear_down(self):
        """Tear Down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
