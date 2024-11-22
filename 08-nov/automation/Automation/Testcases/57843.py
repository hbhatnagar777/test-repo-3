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

    restore_instance()          --  method to run restore and validate test data

    create_mysql_helper_object()--  creates object of MYSQLHelper class

    create_test_data()          --  creates specified number of test databases
                                    with input prefix name

    backup_subclient            --  method to run backup job

    create_instance_if_not_exists()--   method to check if instance exists, else
                                        create new instance

    delete_data_dir()           --  method to delete databases in data directory
                                    of MySQL server

    navigate_to_instance()      --  navigates to specified instance

    navigate_to_entity_action() --  navigates to mysql instance, clicks on Database group tab,
                                    selects the action on the entity

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "57843": {
                    "ClientName": "mysql_client",
                    "DatabaseUser": "username",
                    "SocketFile": "/var/lib/mysql/mysql.sock",
                    "Port": 3306,
                    "SnapEngine": "NetApp",
                    "TestData": [1, 2, 2] (e.g. [No. of Databases, No. of Tables, No. of Rows),
                    "ProxyNode: "proxy_node"
                 }
              }

"""
import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.AdminConsole.Databases.db_instance_details import MySQLInstanceDetails
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Components.browse import RBrowse
from Web.Common.page_object import TestStep, handle_testcase_exception
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """ Class for executing Test for MySQL Intellisnap on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "ACCT1 - Acceptance Test for MySQL Intellisnap from Command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instances = None
        self.db_instance_details = None
        self.helper_object = None
        self.restore_panel = None
        self.database_group = None
        self.dbhelper_object = None
        self.browse = None
        self.instance_name = None
        self.tcinputs = {
            "ClientName": None,
            "DatabaseUser": None,
            "SocketFile": None,
            "Port": None,
            "SnapEngine": None,
            "TestData": [None, None, None]
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
        self.dbhelper_object = DbHelper(self.commcell)
        self.browse = RBrowse(self.admin_console)
        self.instance_name = self.tcinputs["ClientName"] + "_" + str(self.tcinputs["Port"])

    def tear_down(self):
        """ tear down method for testcase """
        self.helper_object.cleanup_test_data("auto")

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and returns job end date
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
    def restore_instance(self, db_list=None, all_db=None, storage_copy="Automatic"):
        """Executes restore according to restore type input and validates restore
            db_list  (list):  List of databases to restore
            all_db  (Boolean):  True if all databases to be restored
            storage_copy (str): Automatic, Snap copy, Primary
        """
        self.browse.select_storage_copy(storage_copy)
        if all_db:
            self.restore_panel = self.database_group.restore_folders(DBInstances.Types.MYSQL,
                                                                     all_files=True)
        else:
            self.restore_panel = self.database_group.restore_folders(DBInstances.Types.MYSQL,
                                                                     db_list)
        job_id = self.restore_panel.in_place_restore()
        self.wait_for_job_completion(job_id)
        self.admin_console.select_breadcrumb_link_using_text(self.instance_name)

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
        if self.tcinputs["TestData"] is not None:
            num_of_db, num_of_tables, num_of_rows = self.tcinputs["TestData"]
            db_list = self.helper_object.generate_test_data(prefix + "_" + timestamp,
                                                            num_of_db,
                                                            num_of_tables,
                                                            num_of_rows)
        else:
            db_list = self.helper_object.generate_test_data(
                database_prefix=prefix + "_" + timestamp)
        return db_list

    @test_step
    def backup_subclient(self, backup_type):
        """Executes backup according to backup type
        Args:
            backup_type  (Backup.BackupType):  Type of backup required
        """
        if backup_type.value == "FULL":
            self.log.info("Full Backup")
            job_id = self.database_group.backup(backup_type=backup_type, immediate_backup_copy=True)
            self.log.info("Full backup job started")
            self.wait_for_job_completion(job_id)
            self.log.info("Full backup job completed")
            if "native" or "netapp" in self.tcinputs["SnapEngine"].lower():
                self.log.info(
                    (f"{self.tcinputs['SnapEngine']} engine is being run. Backup "
                     "copy job will run inline to snap backup"))
                self.log.info("Getting the backup job ID of backup copy job")
                backup_copy_job = self.dbhelper_object.get_backup_copy_job(job_id)
                self.log.info("Job ID of backup copy Job is: %s", backup_copy_job.job_id)
            else:
                log_backup_job = self.dbhelper_object.get_snap_log_backup_job(job_id)
                self.log.info("Log backup job with ID:%s is now completed", log_backup_job.job_id)
        else:
            self.log.info("Incremental Backup")
            job_id = self.database_group.backup(backup_type=backup_type)
            self.wait_for_job_completion(job_id)
        return job_id

    @test_step
    def check_if_instance_exists(self):
        """Checks if instance exists and navigates to instance"""
        self.log.info("Checking if %s instance exists", self.instance_name)
        if self.database_instances.is_instance_exists(DBInstances.Types.MYSQL, self.instance_name,
                                                      self.tcinputs['ClientName']):
            self.log.info("Instance found")
            self.admin_console.select_hyperlink(self.instance_name)
        else:
            raise Exception("{0} instance not found. Create instance "
                            "of database server".format(self.instance_name))

    def delete_data_dir(self, data_directory):
        """
        Deletes data directory of client MySQL server
        Args:
            data_directory(str):Path where database contents are stores
        """

        self.helper_object.stop_mysql_server()
        self.helper_object.machine_object.remove_directory(data_directory)

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.MYSQL,
                                                self.instance_name,
                                                self.tcinputs["ClientName"])

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

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigator.navigate_to_db_instances()
            self.admin_console.wait_for_completion()
            self.check_if_instance_exists()
            self.create_mysql_helper_object()
            self.create_test_data("auto")
            self.db_instance_details.click_on_entity("default")
            flag = False
            if self.database_group.is_snapshot_enabled():
                if self.database_group.get_snap_engine() != self.tcinputs["SnapEngine"]:
                    flag = True
                if self.database_group.get_proxy_node() != self.tcinputs.get("ProxyNode", "None"):
                    flag = True
                if flag:
                    self.log.info("Configuration mismatch in Snapshot engine, resetting the snap engine as provided in User Input")
            if flag or not self.database_group.is_snapshot_enabled():
                self.database_group.disable_snapshot()
                self.database_group.enable_snapshot(self.tcinputs["SnapEngine"], self.tcinputs.get("ProxyNode", "None"))
                self.admin_console.refresh_page()
            if not self.database_group.is_all_databases_in_content():
                raise Exception("All databases not in subclient content after enabling"
                                "hardware snapshot")
            self.log.info("Verified all databases in subclient content")
            self.backup_subclient(RBackup.BackupType.FULL)
            data_directory = self.helper_object.data_directory
            db_info_after_incr1_bkp = self.helper_object.get_database_information()
            self.admin_console.select_breadcrumb_link_using_text(self.instance_name)

            self.log.info("Restoring from Automatic source")
            self.delete_data_dir(data_directory)
            self.navigate_to_entity_action("default", "Restore")
            self.restore_instance(all_db=True, storage_copy="Automatic")
            self.helper_object.start_mysql_server()
            db_info_after_restore = self.helper_object.get_database_information()
            self.helper_object.validate_db_info(db_info_after_incr1_bkp, db_info_after_restore)

            self.log.info("Restoring from Primary source")
            self.delete_data_dir(data_directory)
            self.navigate_to_entity_action("default", "Restore")
            self.restore_instance(all_db=True, storage_copy="Primary")
            self.helper_object.start_mysql_server()
            db_info_after_restore = self.helper_object.get_database_information()
            self.helper_object.validate_db_info(db_info_after_incr1_bkp, db_info_after_restore)

            if self.tcinputs["SnapEngine"] == "NetApp":
                self.log.info("Restoring from Primary copy")
                self.delete_data_dir(data_directory)
                self.navigate_to_entity_action("default", "Restore")
                self.restore_instance(all_db=True, storage_copy="Primary Snap")
                self.helper_object.start_mysql_server()
                db_info_after_restore = self.helper_object.get_database_information()
                self.helper_object.validate_db_info(db_info_after_incr1_bkp, db_info_after_restore)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
