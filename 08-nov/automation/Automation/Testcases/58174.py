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

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "58174": {
                    "ClientName": "mysql_client",
                    "DatabaseUser": "username",
                    "SocketFile": "/var/lib/mysql/mysql.sock",
                    "Port": 3306
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
from Web.AdminConsole.Components.browse import Browse
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.Common.page_object import TestStep, handle_testcase_exception
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """ Class for executing Test for MySQL Block level backup on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Test for MySQL Block level Backup from Command Center"
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
        self.rpanel_info = None
        self.tcinputs = {
            "ClientName": None,
            "DatabaseUser": None,
            "SocketFile": None,
            "Port": None
        }

    def setup(self):
        """ Method to setup test variables """
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open(maximize=True)
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.rpanel_info = RPanelInfo(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = MySQLInstanceDetails(self.admin_console)
        self.database_group = MySQLSubclient(self.admin_console)
        self.dbhelper_object = DbHelper(self.commcell)
        self.browse = Browse(self.admin_console)
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
        end_time = time.strftime('%d-%B-%Y-%I-%M-%p', time.localtime(
            job_obj.summary['lastUpdateTime']))
        return end_time

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

    @test_step
    def restore_validate(self, data_restore, log_restore, db_info,
                         to_time=None, db_list=None,
                         database_group_level_restore=None):
        """Executes restore according to restore type input and validates restore
            data_restore (Boolean):  Checks data restore option
                default: True
            log_restore (Boolean):  Checks log restore option
                default: True
            db_info     (dict): Dictionary of database content before restore for validation
            to_time     (str):  time upto which content is to be restored
            db_list  (list):  List of databases to restore
            database_group_level_restore (Boolean): Database group level restore
                default: False
        """
        if database_group_level_restore:
            self.navigate_to_entity_action("default", "Restore")
            self.restore_panel = self.database_group.restore_folders(DBInstances.Types.MYSQL,
                                                                     all_files=True)
        else:
            self.db_instance_details.access_restore()
            self.restore_panel = self.database_group.restore_folders(DBInstances.Types.MYSQL,
                                                                 all_files=True, to_time=to_time)

        job_id = self.restore_panel.in_place_restore(data_restore=data_restore,
                                                     log_restore=log_restore)
        self.wait_for_job_completion(job_id)
        self.helper_object.start_mysql_server()
        db_info_after_restore = self.helper_object.get_database_information(db_list)
        self.helper_object.validate_db_info(db_info, db_info_after_restore)
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
        num_of_db, num_of_tables, num_of_rows = 10,10,10
        db_list = self.helper_object.generate_test_data(prefix + "_" + timestamp,
                                                            num_of_db,
                                                            num_of_tables,
                                                            num_of_rows)
        return db_list

    @test_step
    def backup_subclient(self, backup_type, data=False):
        """Executes backup according to the backup type
        Args:
            backup_type  (Backup.BackupType):  Type of backup required
            data            (bool)          :  Selects backup data option
                                                during incremental backup
        """
        incr_with_data = backup_type.value.startswith("INCR") and data
        if backup_type.value == "FULL" or incr_with_data:
            info = backup_type.value.title() + " Backup"
            if incr_with_data:
                info += " with data"
            self.log.info(info)
            if incr_with_data:
                job_id = self.database_group.backup(backup_type=backup_type,
                                                    enable_data_for_incremental=True,
                                                    immediate_backup_copy=True)
            else:
                job_id = self.database_group.backup(backup_type=backup_type,
                                                    immediate_backup_copy=True)
            self.log.info("backup job started")
            self.wait_for_job_completion(job_id)
            self.log.info("backup job completed")
            self.log.info(
                ("Native Snap engine is being run. Backup "
                 "copy job will run inline to snap backup"))
            self.log.info("Getting the backup job ID of backup copy job")
            backup_copy_job = self.dbhelper_object.get_backup_copy_job(job_id)
            self.log.info("Job ID of backup copy Job is: %s", backup_copy_job.job_id)
            end_time = self.wait_for_job_completion(backup_copy_job.job_id)
        else:
            self.log.info("Incremental Backup")
            job_id = self.database_group.backup(backup_type=backup_type)
            end_time = self.wait_for_job_completion(job_id)
        return end_time

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

    def enable_blocklevel_backup(self):
        """
        Enables use volume copy option in subclient page and verifies enable hardware
        snapshot is auto-selected
        """
        self.database_group.enable_blocklevel_backup()
        if not (self.database_group.is_snapshot_enabled()
                and self.database_group.get_snap_engine() == "Native", "NetApp"):
            raise Exception("Enable hardware snapshot is not auto selected"
                            " on enabling block level backup")

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigator.navigate_to_db_instances()
            self.admin_console.wait_for_completion()
            self.check_if_instance_exists()

            self.create_mysql_helper_object()
            db_list = self.create_test_data("auto")
            self.db_instance_details.click_on_entity("default")
            self.database_group.disable_blocklevel_backup()
            self.admin_console.refresh_page()
            self.database_group.database_group_autodiscovered_content()
            self.enable_blocklevel_backup()
            if not self.database_group.is_all_databases_in_content():
               raise Exception("All databases not in subclient content after enabling"
                               "hardware snapshot")
            self.log.info("Verified all databases in subclient content")

            # Full backup
            full_bkp_end_time = self.backup_subclient(
               RBackup.BackupType.FULL)
            db_info_after_full_bkp = self.helper_object.get_database_information()

            # Populate databases and run Data incremental backup
            self.helper_object.populate_database(subclient_content=db_list)
            incr1_bkp_end_time = self.backup_subclient(
               RBackup.BackupType.INCR, data=True)
            db_info_after_incr1_bkp = self.helper_object.get_database_information()

            # Populate databases and run Log incremental backup
            self.helper_object.populate_database(subclient_content=db_list)
            self.backup_subclient(RBackup.BackupType.INCR)
            data_directory = self.helper_object.data_directory
            db_info_after_incr2_bkp = self.helper_object.get_database_information()
            self.admin_console.select_breadcrumb_link_using_text(self.instance_name)

            self.delete_data_dir(data_directory)
            self.restore_validate(data_restore=True, log_restore=True,
                                  db_info = db_info_after_incr2_bkp,
                                  database_group_level_restore=True)

            self.delete_data_dir(data_directory)
            self.restore_validate(data_restore=True, log_restore=True,
                                  to_time=incr1_bkp_end_time,
                                  db_info=db_info_after_incr1_bkp)

            self.delete_data_dir(data_directory)
            self.restore_validate(data_restore=True, log_restore=False,
                                  to_time=full_bkp_end_time,
                                  db_info=db_info_after_full_bkp)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
