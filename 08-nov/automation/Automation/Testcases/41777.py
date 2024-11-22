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

    navigate_to_entity_action() --  navigates to database group tab performs action on the provided entity

    restore_validate()          --  method to perform restore and validation of data restored

    create_mysql_helper_object()--  method to create object of SDK mysqlhelper class

    create_test_data()          -- method to generate test data

    set_subclient_content()     -- method to set subclient content to test databases

    backup_and_restore()        -- method to perform backup and restore

    cleanup()                   --  method to cleanup all testcase created changes

    run()                       --  run function of this test case

    Input Example:

    "testCases":
            {
                "41777": {
                    "ClientName": "mysql",
                    "InstanceName":"mysql_1_3306",
                    "DatabaseUser": "root",
                    "Port": "3306",
                    "DestClientName":"mysql_2",
                    "DestInstanceName":"mysql_2_3306"
                }
            }
"""

import ast
import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.Common.page_object import TestStep, handle_testcase_exception
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Web.AdminConsole.Components.dialog import RBackup


class TestCase(CVTestCase):
    """ Class for executing out of place log only restore testcase for MySQL IDA on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Mysql Log Only Restores"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instances = None
        self.db_instance_details = None
        self.source_helper_object = None
        self.dest_helper_object = None
        self.restore_panel = None
        self.database_group = None
        self.db_group_content = None
        self.instance_name = None
        self.subclient = None
        self.tcinputs = {
            "ClientName": None,
            "InstanceName": None,
            "DatabaseUser": None,
            "Port": None,
            "DestClientName": None,
            "DestInstanceName": None
        }

    def setup(self):
        """ Method to setup test variables """
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.database_group = MySQLSubclient(self.admin_console)

    def tear_down(self):
        """ tear down method for testcase """
        self.source_helper_object.cleanup_test_data("auto")
        self.dest_helper_object.cleanup_test_data("auto")

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
        """Navigates to Instance page
        """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.MYSQL,
                                                self.tcinputs['InstanceName'],
                                                self.tcinputs['ClientName'])

    @test_step
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
    def restore_validate(self, data_restore, log_restore, db_info, in_place=True):
        """Executes restore according to restore type input and validates restore
            data_restore (Boolean):  Checks data restore option
                default: True
            log_restore (Boolean):  Checks log restore option
                default: True
            db_info  (dict): Dictionary of database content before restore for validation
            in_place (Boolean): Checks if restore type is in place restore
               default:True
        """
        if data_restore and log_restore:
            info = "Data + Log "
        else:
            info = "Data only " if data_restore else "Log only "
        info += "restore"
        self.log.info(info)
        if in_place:
            job_id = self.restore_panel.in_place_restore(data_restore=data_restore,
                                                         log_restore=log_restore)
            self.wait_for_job_completion(job_id)
            db_info_after_restore = self.source_helper_object.get_database_information()
        else:
            job_id = self.restore_panel.out_of_place_restore(destination_client=self.tcinputs['DestClientName'],
                                                             destination_instance=self.tcinputs['DestInstanceName'],
                                                             data_restore=data_restore, log_restore=log_restore
                                                             )
            self.wait_for_job_completion(job_id)
            db_info_after_restore = self.dest_helper_object.get_database_information()

        self.source_helper_object.validate_db_info(db_info, db_info_after_restore)

    @test_step
    def create_mysql_helper_object(self, client_name, instance_name):
        """Creates object of SDK mysqlhelper class"""
        connection_info = {
            'client_name': client_name,
            'instance_name': instance_name
        }
        if "windows" in self.client.os_info.lower():
            connection_info['socket_file'] = self.tcinputs['Port']
        else:
            connection_info['socket_file'] = self.tcinputs['SocketFile']
        if client_name is self.tcinputs["ClientName"]:
            self.source_helper_object = MYSQLHelper(commcell=self.commcell, hostname=client_name,
                                                    user=self.tcinputs["DatabaseUser"],
                                                    port=self.tcinputs["Port"],
                                                    connection_info=connection_info)
        else:
            self.dest_helper_object = MYSQLHelper(commcell=self.commcell, hostname=client_name,
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
            db_list = self.source_helper_object.generate_test_data(prefix + "_" + timestamp,
                                                                   num_of_db, num_of_tables, num_of_rows)
        else:
            db_list = self.source_helper_object.generate_test_data(
                database_prefix=prefix + "_" + timestamp)
        return db_list

    @test_step
    def backup_and_restore(self):
        """
        Executes backup and restore of the subclient
        """
        self.log.info("Checking if MySql Binary Logging is enabled or not")
        self.source_helper_object.log_bin_on_mysql_server()
        self.log.info("MySql Binary Logging is enabled")

        self.log.info("Creating subclient object for subclient content")
        self.subclient = self.client.agents.get("MySQL").instances.get(
            self.tcinputs["InstanceName"]).subclients.get("default")
        self.db_group_content = \
            [db for db in [db.lstrip('\\').lstrip('/') for db in self.subclient.content]]

        db_list = self.create_test_data("auto")

        self.admin_console.refresh_page()

        self.log.info("Full Backup")
        job_id = self.database_group.backup(backup_type=RBackup.BackupType.FULL)
        self.wait_for_job_completion(job_id)

        self.subclient.refresh()
        content_to_restore = \
            [db for db in [db.lstrip('\\').lstrip('/') for db in self.subclient.content]
             if db not in ['mysql', 'sys', 'information_schema', 'performance_schema']]

        db_info_after_full_bkp = self.source_helper_object.get_database_information()

        self.log.info("Populating Data and running Incremental Backups")
        self.source_helper_object.populate_database(subclient_content=db_list)
        job_id = self.database_group.backup(backup_type=RBackup.BackupType.INCR)
        self.wait_for_job_completion(job_id)
        self.source_helper_object.populate_database(subclient_content=db_list)
        job_id = self.database_group.backup(backup_type=RBackup.BackupType.INCR)
        self.wait_for_job_completion(job_id)
        self.source_helper_object.populate_database(subclient_content=db_list)
        job_id = self.database_group.backup(backup_type=RBackup.BackupType.INCR)
        self.wait_for_job_completion(job_id)

        db_info_after_incr3_bkp = self.source_helper_object.get_database_information()

        self.source_helper_object.cleanup_test_data("auto")

        self.navigate_to_entity_action("default", "Restore")

        self.restore_panel = self.database_group.restore_folders(
            DBInstances.Types.MYSQL, content_to_restore)
        self.restore_validate(data_restore=True, log_restore=False,
                              db_info=db_info_after_full_bkp)

        self.restore_panel = self.database_group.restore_folders(
            DBInstances.Types.MYSQL, restore_items_from_previous_browse=True)
        self.restore_validate(data_restore=True, log_restore=False,
                              db_info=db_info_after_full_bkp, in_place=False)

        self.restore_panel = self.database_group.restore_folders(
            DBInstances.Types.MYSQL, restore_items_from_previous_browse=True)
        self.restore_validate(data_restore=False, log_restore=True,
                              db_info=db_info_after_incr3_bkp)

        self.restore_panel = self.database_group.restore_folders(
            DBInstances.Types.MYSQL, restore_items_from_previous_browse=True)
        self.restore_validate(data_restore=False, log_restore=True, in_place=False,
                              db_info=db_info_after_incr3_bkp)

        self.source_helper_object.cleanup_test_data("auto")
        self.dest_helper_object.cleanup_test_data("auto")

        self.restore_panel = self.database_group.restore_folders(
            DBInstances.Types.MYSQL, restore_items_from_previous_browse=True)
        self.restore_validate(data_restore=True, log_restore=True,
                              db_info=db_info_after_incr3_bkp)

        self.restore_panel = self.database_group.restore_folders(
            DBInstances.Types.MYSQL, restore_items_from_previous_browse=True)
        self.restore_validate(data_restore=True, log_restore=True, in_place=False,
                              db_info=db_info_after_incr3_bkp)

    @test_step
    def set_subclient_content(self, db_list):
        """Sets subclient content to test databases
        Args:
            db_list  (list):  List of databases to be in subclient content
        """
        self.admin_console.refresh_page()
        self.database_group.edit_content(db_list)

    @test_step
    def cleanup(self):
        """Removes testcase created changes"""
        try:
            self.navigate_to_instance()
            self.db_instance_details.click_on_entity("default")
            self.set_subclient_content(self.db_group_content)
        except Exception as e:
            self.log.info(e)
            pass

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigate_to_instance()
            self.admin_console.wait_for_completion()
            self.db_instance_details.click_on_entity("default")
            self.create_mysql_helper_object(self.tcinputs["ClientName"], self.tcinputs["InstanceName"])
            self.create_mysql_helper_object(self.tcinputs["DestClientName"], self.tcinputs["DestInstanceName"])
            self.backup_and_restore()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
