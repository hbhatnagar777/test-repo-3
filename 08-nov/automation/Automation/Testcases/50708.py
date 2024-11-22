# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Backup and Restore check for MyISAM and InnoDB Databases.

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    backup()        -- perform a backup of the specified type (full or incremental or synthetic)

    restore()       -- preform restore operation for the instnace

    create_mysql_helper_object()    -- create an object of the SDK mysqlhelper class

    create_test_data()    -- create test databases and optionally add tables to them

    navigate_to_instance()    -- navigate to the MySQL instance page

    restore_validate(start, to)    -- validate data after restore process

    cleanup_test_data()    -- clean up the test data created for automation

    cleanup()              --  method to cleanup all testcase created changes

    run()           --  run function of this test case

    tear_down()     -- tear down function of the test case

Input Example:
    "testCases":
        {
            "50708": {
                    "ClientName" : "name of client host machine",
                    "InstanceName" : "name of the instance",
                    "SocketFile" : "Directory of socket file",
                    "db_port"   : "port running mysql database"
                    }
        }
"""
from AutomationUtils.cvtestcase import CVTestCase
from Database.dbhelper import DbHelper
from Web.AdminConsole.Databases.db_instance_details import MySQLInstanceDetails
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Components.dialog import RBackup
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Web.Common.exceptions import CVWebAutomationException


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """
        Initializes test case class object
        """
        super().__init__()
        self.name = "Backup and Restore check for MyISAM and InnoDB Databases.."
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
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance_details = MySQLInstanceDetails(self.admin_console)
        self.dbhelper = DbHelper(self.commcell)
        self.db_group = MySQLSubclient(self.admin_console)
        self.full_backup = RBackup.BackupType.FULL
        self.incr_backup = RBackup.BackupType.INCR
        self.synth_backup = RBackup.BackupType.SYNTH

    @test_step
    def backup(self, backup_type, data_for_inc=False):
        """
        Helper function for performing backups.
        Args:
            backup_type: full_backup, incr_backup
            data_for_inc: Boolean to enable data for incremental backups
        """
        self.navigate_to_instance()
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
    def restore(self):
        """
        Helper function for performing restore.
        """
        self.navigate_to_instance()
        # self.db_instance_details.click_on_entity('default')
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(database_type=DBInstances.Types.MYSQL,
                                                                items_to_restore=self.database_list)
        self.last_job = restore_panel.in_place_restore()
        self.dbhelper.wait_for_job_completion(self.last_job)

    @test_step
    def create_mysql_helper_object(self, socket_file, port):
        """
        Creates object of SDK mysqlhelper class.
        Args:
            socket_file: MySQL socket file
            port: MySQL port
        """
        connection_info = {
            'client_name': self.tcinputs["ClientName"],
            'instance_name': self.tcinputs["InstanceName"],
            'socket_file': socket_file
        }
        self.helper_object = MYSQLHelper(
            commcell=self.commcell, hostname=self.commcell.clients.get(self.tcinputs["ClientName"]).client_hostname,
            user='root', port=port, connection_info=connection_info)
        self.log.info("Created MySQL helper object.")

    @test_step
    def create_test_data(self, engine):
        """
        Creates test databases according to input.
        Args:
            engine: Engine for created tables
        """
        db_list = self.helper_object.generate_test_data(database_prefix="automation_db", num_of_databases=1,
                                                        engine=engine)
        self.database_list = db_list
        self.log.info(f"Created test databases: {db_list}")

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page."""
        self.log.info("Navigating to MySQL Instance page.")
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance.select_instance(DBInstances.Types.MYSQL, self.tcinputs["InstanceName"],
                                         self.tcinputs["ClientName"])

    @test_step
    def cleanup_test_data(self):
        """Cleans up test data."""
        self.helper_object.cleanup_test_data("automation")
        self.log.info("Cleaned up test data.")

    @test_step
    def cleanup(self):
        """Removes testcase created changes"""
        try:
            self.cleanup_test_data()
        except Exception as e:
            self.log.error(e)

    def run(self):
        """Run function of this test case"""
        try:
            self.create_mysql_helper_object(socket_file=self.tcinputs["ClientName"], port=self.tcinputs["db_port"])
            self.helper_object.basic_setup_on_mysql_server(log_bin_check=True)
            self.create_test_data(engine='MyISAM')
            self.db_map['before'] = self.helper_object.get_database_information()
            self.backup(self.full_backup)
            self.cleanup_test_data()
            self.restore()
            self.helper_object.check_table_engine(database_name=self.database_list[0], engine='MyISAM')
            self.db_map['after'] = self.helper_object.get_database_information()
            self.helper_object.validate_db_info(self.db_map['before'], self.db_map['after'])
            self.cleanup_test_data()
            self.create_test_data(engine='InnoDB')
            self.db_map['before'] = self.helper_object.get_database_information()
            self.backup(self.full_backup)
            self.cleanup_test_data()
            self.restore()
            self.helper_object.check_table_engine(database_name=self.database_list[0], engine='InnoDB')
            self.db_map['after'] = self.helper_object.get_database_information()
            self.helper_object.validate_db_info(self.db_map['before'], self.db_map['after'])

        except Exception:
            raise CVWebAutomationException('Test case failed')

        finally:
            self.cleanup()

    def tear_down(self):
        """Tear Down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
