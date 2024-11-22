# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    tear_down()                 --  tear down method for testcase

    wait_for_job_completion()   --  Waits for completion of job and gets the
                                    end date once job completes

    navigate_to_instance()      --  navigates to specified instance

    add_instance()              --  creates a new instance of specified type
                                    with specified name and details

    navigate_to_entity_action() --  navigates to mysql instance, clicks on Database group tab,
                                    selects the action on the entity

    restore_validate()          --  method to run restore and validate test data

    create_mysql_helper_object()--  creates object of MYSQLHelper class

    create_test_data()          --  method to create test databases according to input

    set_subclient_content()     --  sets content of the subclient to database list
                                    argument passed as input

    backup_subclient()          --  method to run backup job

    enable_xtrabackup()         --  method to enable xtrabackup for current instance
    
    cleanup()                   --  method to remove testcase created changes

    is_xtra_backup_enabled()    --  method to check if xtrabackup is enabled

    autodiscovery_backup_and_restore() -- method to perform autodiscovery, backup and restore

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "57840": {
                    "ClientName": "mysql_client",
                    "Plan": "plan",
                    "DatabaseUser": "username",
                    "DatabasePassword": "password",
                    "SocketFile": "/var/lib/mysql/mysql.sock",  (optional, for unix client)
                    "BinaryDirectory": "/usr/bin",
                    "LogDirectory": "/var/lib/mysql",
                    "ConfigFile": "/etc/my.cnf",
                    "UnixUsername": "username",                 (optional, for unix client)
                    "NTUsername": "username",                   (optional, for windows client)
                    "NTPassword": "password",                   (optional, for windows client)
                    "Port": 3306,
                    "XtraBackup": "/usr/bin",
                    "TestData": [10, 20, 100] (eg. [No. of Databases, No. of Tables, No. of Rows)
                     as list or string representation of list ie. "[10, 20, 100]"
                                                                (optional, default:[5,10,50])
                }
            }

On completion of execution of this testcase, regardless of testcase passing/failing, 
if instance is created by automation, it is deleted. Otherwise, default subclient 
content is reverted to content before execution of this testcase
"""

import ast
import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.AdminConsole.Databases.db_instance_details import MySQLInstanceDetails
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Database.MySQLUtils.mysqlhelper import MYSQLHelper


class TestCase(CVTestCase):
    """ Class for executing Basic acceptance Test for MySQL IDA
     using XtraBackup on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "ACCT1 - Acceptance Test for MySQL Xtrabackup from Command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instances = None
        self.db_instance_details = None
        self.helper_object = None
        self.restore_panel = None
        self.database_group = None
        self.db_group_content = None
        self.automation_instance = None
        self.instance_name = None
        self.tcinputs = {
            "ClientName": None,
            "Plan": None,
            "DatabaseUser": None,
            "DatabasePassword": None,
            "BinaryDirectory": None,
            "LogDirectory": None,
            "ConfigFile": None,
            "Port": None,
            "XtraBackup": None
        }

    def setup(self):
        """ Method to setup test variables """
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open(maximize=True)
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = MySQLInstanceDetails(self.admin_console)
        self.database_group = MySQLSubclient(self.admin_console)
        self.instance_name = self.tcinputs["ClientName"] + "_" + str(self.tcinputs["Port"])

    def tear_down(self):
        """ tear down method for testcase """
        self.helper_object.cleanup_test_data("auto")
        self.helper_object.cleanup_test_data("test")

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.MYSQL,
                                                self.instance_name,
                                                self.tcinputs["ClientName"])

    @test_step
    def add_instance(self):
        """Adds new instance"""
        unix = "windows" not in self.client.os_info.lower()
        self.database_instances.add_mysql_instance(server_name=self.tcinputs["ClientName"],
                                                   instance_name=self.instance_name,
                                                   plan=self.tcinputs["Plan"],
                                                   database_user=self.tcinputs["DatabaseUser"],
                                                   password=self.tcinputs["DatabasePassword"],
                                                   unix=unix,
                                                   unix_username=self.tcinputs.get("UnixUsername"),
                                                   nt_username=self.tcinputs.get('NTUsername'),
                                                   nt_password=self.tcinputs.get('NTPassword'),
                                                   xtra_backup_bin_path=self.tcinputs['XtraBackup'],
                                                   socketfile_directory=self.tcinputs.get("SocketFile"),
                                                   binary_directory=self.tcinputs["BinaryDirectory"],
                                                   log_directory=self.tcinputs["LogDirectory"],
                                                   config_directory=self.tcinputs["ConfigFile"],
                                                   port=self.tcinputs["Port"])
        self.log.info("Instance successfully created")
        self.automation_instance = True
        self.admin_console.wait_for_completion()

    def navigate_to_entity_action(self, entity_name, action_item):
        """Navigates to MySQL Instance details page, clicks on 'Database groups' tab and
        performs action on the provided entity
        Args:
            entity_name (str)   :   Name of entity
            action_item (str)   :   Name of action item
        """
        self.log.info("Navigate to instance details page")
        self.navigate_to_instance()
        self.db_instance_details.access_actions_item_of_entity(
            entity_name=entity_name, action_item=action_item)
        self.admin_console.wait_for_completion()

    @test_step
    def restore_validate(self, data_restore, log_restore, db_info):
        """Executes restore according to restore type input and validates restore
            data_restore (Boolean):  Checks data restore option
                default: True
            log_restore (Boolean):  Checks log restore option
                default: True
            db_info  (dict): Dictionary of database content before restore for validation
        """
        if data_restore and log_restore:
            info = "Data + Log "
        else:
            info = "Data only " if data_restore else "Log only "
        info += "restore"
        self.log.info(info)
        job_id = self.restore_panel.in_place_restore(data_restore=data_restore,
                                                     log_restore=log_restore)
        self.wait_for_job_completion(job_id)

        db_info_after_restore = self.helper_object.get_database_information()
        self.helper_object.validate_db_info(db_info, db_info_after_restore)

    @test_step
    def create_mysql_helper_object(self):
        """Creates object of SDK mysqlhelper class"""
        connection_info = {
            'client_name': self.tcinputs["ClientName"],
            'instance_name': self.instance_name
        }
        if "windows" in self.client.os_info.lower():
            connection_info['socket_file'] = self.tcinputs['Port']
        else:
            connection_info['socket_file'] = self.tcinputs['SocketFile']
        self.helper_object = MYSQLHelper(commcell=self.commcell,
                                         hostname=self.tcinputs["ClientName"],
                                         user=self.tcinputs["DatabaseUser"],
                                         port=self.tcinputs["Port"],
                                         connection_info=connection_info)

    @test_step
    def create_test_data(self, prefix):
        """Creates test databases according to input
            returns:    list of names of databases created
        """
        timestamp = str(int(time.time()))
        if self.tcinputs.get("TestData"):
            if isinstance(self.tcinputs["TestData"], str):
                num_of_db, num_of_tables, num_of_rows = ast.literal_eval(self.tcinputs["TestData"])
            else:
                num_of_db, num_of_tables, num_of_rows = self.tcinputs["TestData"]
            db_list = self.helper_object.generate_test_data(prefix+"_"+timestamp,
                                                            num_of_db,
                                                            num_of_tables,
                                                            num_of_rows)
        else:
            db_list = self.helper_object.generate_test_data(database_prefix=prefix+"_"+timestamp)
        return db_list

    @test_step
    def set_subclient_content(self, db_list):
        """Sets subclient content to test databases
        Args:
            db_list  (list):  List of databases to be in subclient content
        """
        self.admin_console.refresh_page()
        self.database_group.edit_content(db_list)

    @test_step
    def backup_subclient(self, backup_type):
        """Executes backup according to backup type
        Args:
            backup_type  (Backup.BackupType):  Type of backup required
        """
        if backup_type.value == "FULL":
            self.log.info("Full Backup")
            job_id = self.database_group.backup(backup_type=backup_type)
            self.wait_for_job_completion(job_id)
        else:
            self.log.info("Incremental Backup")
            job_id = self.database_group.backup(backup_type=backup_type)
            self.wait_for_job_completion(job_id)
        return job_id

    @test_step
    def enable_xtrabackup(self):
        """
        Edits instance properties to enable xtrabackup
        """
        self.db_instance_details.enable_xtrabackup(self.tcinputs["XtraBackup"])

    @test_step
    def cleanup(self):
        """Removes testcase created changes"""
        try:
            if self.automation_instance:
                self.navigate_to_instance()
                self.db_instance_details.delete_instance()
            else:
                self.log.info("Logging out before cleanup")
                self.admin_console.logout_silently(self.admin_console)
                self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                         self.inputJSONnode['commcell']['commcellPassword'])
                self.navigate_to_instance()
                self.db_instance_details.click_on_entity("default")
                self.set_subclient_content(self.db_group_content)
        except Exception as e:
            self.log.info(e)
            pass

    @test_step
    def is_xtra_backup_enabled(self, job_id):
        """Check if xtra backup is enabled or not"""
        if not self.helper_object.is_xtrabackup_effective(str(job_id),
                                                          self.client.log_directory):
            raise Exception("xtrabackup was not effective during FULL backup")
        self.log.info("xtrrabackup was effective during FULL backup")

    @test_step
    def autodiscovery_backup_and_restore(self):
        """Validate Autodiscovery, perform full backup and restore"""
        self.navigate_to_instance()
        db_list1 = self.create_test_data("test")
        self.db_instance_details.click_on_entity("default")
        self.log.info("Autodiscovery Validation")
        self.database_group.validate_autodiscover(database_list=db_list1)
        self.log.info("Autodiscovery Validated")
        self.backup_subclient(RBackup.BackupType.FULL)

        self.subclient.refresh()
        content_to_restore = \
            [db for db in [db.lstrip('\\').lstrip('/') for db in self.subclient.content]
             if db not in ['mysql', 'sys', 'information_schema', 'performance_schema']]
        db_info_before_restore = self.helper_object.get_database_information()
        self.helper_object.cleanup_test_data("test")
        self.navigate_to_entity_action("default", "Restore")
        self.restore_panel = self.database_group.restore_folders(DBInstances.Types.MYSQL, content_to_restore)
        self.restore_validate(data_restore=True, log_restore=True, db_info=db_info_before_restore)

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigator.navigate_to_db_instances()
            self.admin_console.wait_for_completion()
            if self.database_instances.is_instance_exists(DBInstances.Types.MYSQL,
                                                          self.instance_name,
                                                          self.tcinputs['ClientName']):
                self.log.info("Instance found")
                self.admin_console.select_hyperlink(self.instance_name)
                self.enable_xtrabackup()
            else:
                self.log.info("Instance not found. Creating new instance")
                self.add_instance()
                self.log.info("Instance successfully created")
            self.db_instance_details.click_on_entity("default")
            self.log.info("Creating subclient object for subclient content")
            self.subclient = self.client.agents.get("MySQL").instances.get(
                self.instance_name).subclients.get("default")
            self.db_group_content = \
                [db for db in [db.lstrip('\\').lstrip('/') for db in self.subclient.content]]
            self.create_mysql_helper_object()
            db_list = self.create_test_data("auto")
            self.admin_console.refresh_page()
            job_id = self.backup_subclient(RBackup.BackupType.FULL)
            self.subclient.refresh()
            content_to_restore = \
                [db for db in [db.lstrip('\\').lstrip('/') for db in self.subclient.content]
                 if db not in ['mysql', 'sys', 'information_schema', 'performance_schema']]
            self.is_xtra_backup_enabled(job_id)
            db_info_after_full_bkp = self.helper_object.get_database_information()
            self.helper_object.populate_database(subclient_content=db_list)
            self.backup_subclient(RBackup.BackupType.INCR)
            self.helper_object.populate_database(subclient_content=db_list)
            self.backup_subclient(RBackup.BackupType.INCR)
            db_info_after_incr2_bkp = self.helper_object.get_database_information()
            self.helper_object.cleanup_test_data("auto")
            self.navigate_to_entity_action("default", "Restore")
            self.restore_panel = self.database_group.restore_folders(DBInstances.Types.MYSQL, content_to_restore)
            self.restore_validate(data_restore=True, log_restore=False, db_info=db_info_after_full_bkp)
            self.restore_panel = self.database_group.restore_folders(DBInstances.Types.MYSQL, restore_items_from_previous_browse=True)
            self.restore_validate(data_restore=False, log_restore=True, db_info=db_info_after_incr2_bkp)
            self.helper_object.cleanup_test_data("auto")
            self.restore_panel = self.database_group.restore_folders(DBInstances.Types.MYSQL, restore_items_from_previous_browse=True)
            self.restore_validate(data_restore=True, log_restore=True, db_info=db_info_after_incr2_bkp)
            self.autodiscovery_backup_and_restore()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
