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

    new_subclient()             --  runs method to create new subclient

    restore_instance()          --  method to run restore

    create_mysql_helper_object()--  creates object of MYSQLHelper class

    create_test_data()          --  method to create test databases according to input

    backup_subclient()          --  method to run backup job
    
    cleanup()                   --  method to remove testcase created changes

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "57841": {
                    "ClientName": "mysql_client",
                    "DBGroupPlan": "plan",
                    "DatabaseGroupName": "dbgroup1",
                    "DatabaseUser": "username",
                    "SocketFile": "/var/lib/mysql/mysql.sock",
                    "Port": 3306,
                    "TestData": [10, 20, 100] (eg. [No. of Databases, No. of Tables, No. of Rows)
                     as list or string representation of list ie. "[10, 20, 100]"
                                                                (optional, default:[5,10,50])
                }
            }
On completion of execution of this testcase, regardless of testcase passing/failing, 
automation created subclient is deleted
"""

import ast
import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Components.browse import RBrowse
from Web.Common.page_object import TestStep, handle_testcase_exception
from Database.MySQLUtils.mysqlhelper import MYSQLHelper


class TestCase(CVTestCase):
    """ Class for executing Basic acceptance Test for MySQL pint in time restore """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "MySQL Point in Time Restore from Command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instances = None
        self.db_instance_details = None
        self.db_instance = None
        self.helper_object = None
        self.restore_panel = None
        self.database_group = None
        self.add_subclient = None
        self.browse = None
        self.instance_name = None
        self.subclient_created = False
        self.tcinputs = {
            "ClientName": None,
            "DBGroupPlan": None,
            "DatabaseGroupName": None,
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
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.database_group = MySQLSubclient(self.admin_console)
        self.browse = RBrowse(self.admin_console)
        self.instance_name = self.tcinputs["ClientName"] + "_" + str(self.tcinputs["Port"])

    def tear_down(self):
        """ tear down method for testcase """
        self.helper_object.cleanup_test_data("auto")

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid

        Returns:  Job start and end time
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)
        start_time = time.strftime('%d-%B-%Y-%I-%M-%p', time.localtime(
            job_obj.summary['jobStartTime']))
        end_time = time.strftime('%d-%B-%Y-%I-%M-%p', time.localtime(
            job_obj.summary['lastUpdateTime']))
        return start_time, end_time

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.MYSQL,
                                                self.instance_name,
                                                self.tcinputs["ClientName"])

    @test_step
    def new_subclient(self, database_list):
        """Adds new subclient"""
        if self.admin_console.check_if_entity_exists('link', self.tcinputs['DatabaseGroupName']):
            self.db_instance_details.click_on_entity(self.tcinputs['DatabaseGroupName'])
            self.database_group.delete_subclient()
        self.add_subclient = self.db_instance_details.click_add_subclient(DBInstances.Types.MYSQL)
        self.add_subclient.add_subclient(subclient_name=self.tcinputs['DatabaseGroupName'],
                                         number_backup_streams=2, database_list=database_list,
                                         plan=self.tcinputs['DBGroupPlan'])
        self.subclient_created = True

    @test_step
    def restore_instance(self, data_restore, log_restore, to_time,
                         db_list=None, all_files=False):
        """Executes restore according to restore type input and validates restore
            data_restore (Boolean):  Checks data restore option
                default: True
            log_restore (Boolean):  Checks log restore option
                default: True
            db_list  (list):  List of databases to restore
        """
        self.admin_console.click_button_using_text('Restore')

        to_time = time.strftime('%d-%B-%Y-%H-%M',
                                time.localtime(time.mktime(time.strptime(to_time,
                                                                         '%d-%B-%Y-%I-%M-%p'))+60))
        self.admin_console.wait_for_completion()
        self.browse.show_backups_by_date_range(to_time=to_time, prop="Showing backup as of", index=0)
        if all_files:
            self.restore_panel = self.database_group.restore_folders(DBInstances.Types.MYSQL,
                                                                     all_files=all_files)
        else:
            self.restore_panel = self.database_group.restore_folders(DBInstances.Types.MYSQL,
                                                                     items_to_restore=db_list)
        job_id = self.restore_panel.in_place_restore(data_restore=data_restore,
                                                     log_restore=log_restore,
                                                     notify_job_completion=False)
        self.wait_for_job_completion(job_id)
        return job_id

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
    def backup_subclient(self, backup_type):
        """Executes backup according to backup type
        Args:
            backup_type  (RBackup.BackupType):  Type of backup required
        """
        job_start_time, job_end_time = "", ""
        if backup_type.value == "FULL":
            self.log.info("Full Backup")
            job_id = self.database_group.backup(backup_type=backup_type)
            job_start_time, job_end_time = self.wait_for_job_completion(job_id)
        elif backup_type.value == "INCREMENTAL":
            self.log.info("Incremental Backup")
            job_id = self.database_group.backup(backup_type=backup_type)
            job_start_time, job_end_time = self.wait_for_job_completion(job_id)

        return job_start_time, job_end_time, job_id

    @test_step
    def check_if_instance_exists(self):
        """Checks if instance exists and navigates to instance"""
        info = "Checking if {0} instance exists".format(self.instance_name)
        self.log.info(info)
        if self.database_instances.is_instance_exists(DBInstances.Types.MYSQL, self.instance_name,
                                                      self.tcinputs['ClientName']):
            self.log.info("Instance found")
            self.admin_console.select_hyperlink(self.instance_name)
        else:
            raise Exception("{0} instance not found. Create instance "
                            "of database server".format(self.instance_name))

    @test_step
    def cleanup(self):
        """Removes testcase created database group"""
        self.navigate_to_instance()
        self.db_instance_details.click_on_entity(self.tcinputs['DatabaseGroupName'])
        self.database_group.delete_subclient()

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigator.navigate_to_db_instances()
            self.admin_console.wait_for_completion()
            self.check_if_instance_exists()
            self.create_mysql_helper_object()
            db_list = self.create_test_data("auto")
            self.admin_console.refresh_page()
            self.new_subclient(db_list)
            self.admin_console.wait_for_completion()
            active_jobs = self.commcell.job_controller.active_jobs(
                client_name=self.tcinputs['ClientName'], job_filter="Backup")
            active_job = None
            for job in active_jobs:
                job_obj = self.commcell.job_controller.get(job)
                if job_obj.subclient_name == self.tcinputs['DatabaseGroupName'] \
                        and job_obj.instance_name == self.instance_name:
                    active_job = job_obj
                    break
            if active_job:
                full_job_start_time, full_job_end_time = self.wait_for_job_completion(active_job.job_id)
                full_job_id = active_job.job_id

            else:
                full_job_start_time, full_job_end_time, full_job_id = \
                    self.backup_subclient(backup_type=RBackup.BackupType.FULL)

            self.helper_object.populate_database(subclient_content=db_list)
            incr_job1_start_time, incr_job1_end_time, incr1_job_id = \
                self.backup_subclient(backup_type=RBackup.BackupType.INCR)

            db_info_after_incr_job1 = self.helper_object.get_database_information(db_list)

            self.log.info("Waiting for 120 seconds before incremental backup 2")
            time.sleep(120)

            self.helper_object.populate_database(db_list)

            self.backup_subclient(backup_type=RBackup.BackupType.INCR)

            db_info_after_incr_job2 = self.helper_object.get_database_information(db_list)
            self.helper_object.cleanup_test_data("auto")
            current_url = self.admin_console.current_url()
            job_details_url = current_url.split("/#/")[0] + f"/#/jobs/{full_job_id}"
            self.admin_console.navigate(job_details_url)
            self.restore_instance(data_restore=True, log_restore=True,
                                  all_files=True, to_time=incr_job1_end_time)

            db_info_after_restore = self.helper_object.get_database_information(db_list)

            self.helper_object.cleanup_test_data("auto")

            self.helper_object.validate_db_info(db_info_after_incr_job1, db_info_after_restore)

            if db_info_after_incr_job2 != db_info_after_restore:
                info = "Database Information validation failed..!! " \
                     "Verified data backed up between incremental" \
                     " backups 1 and 2 not restored"
                self.log.info(info)
                self.log.info("Database info for incremental backup job 2:%s",
                              db_info_after_incr_job2)
                self.log.info("Database info after restore job:%s",
                              db_info_after_restore)
            else:
                ex_str = "Database Information validation success!! " \
                     "Verified data backed up between incremental" \
                     " backups 1 and 2 restored"
                raise Exception(ex_str)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            if self.subclient_created:
                self.cleanup()
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
