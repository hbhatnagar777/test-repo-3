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

    wait_for_job_completion()   --  Waits for completion of job

    navigate_to_instance()      --  navigates to specified instance

    navigate_to_entity_action() --  navigates to database group tab performs action on the provided entity

    backup_and_validation()     --  method to executes backup of the subclient and validation of the binary log files

    validate_binary_logs()      --  method to validate the binary log files

    set_subclient_content()     --  method to set subclient content to test databases

    cleanup()                   --  method to cleanup all testcase created changes

    run()                       --  run function of this test case

    Input Example:

    "testCases":
            {
                "43714": {
                    "ClientName": "mysql",
                    "InstanceName":"mysql_1_3306",
                    "AgentName": "MySQL",
                    "Port": "3306",
                    "SubclientName":"default"
                }
            }
"""
import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Components.page_container import PageContainer
from Web.Common.page_object import TestStep, handle_testcase_exception
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Web.AdminConsole.Components.dialog import RBackup
from AutomationUtils.database_helper import MySQL


class TestCase(CVTestCase):
    """ Class for executing  testcase for Do not Purge Logs of MySQL IDA on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Data Protection: "Do not Purge Logs" with full and incremental backups'
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instances = None
        self.db_instance_details = None
        self.helper_object = None
        self.database_group = None
        self.db_group_content = None
        self.tcinputs = {
            "ClientName": None,
            "InstanceName": None,
            "Port": None,
            "SubclientName": None
        }
        self.mysql = None
        self.page_container = None
        self.db_list = None
        self.backup = None

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
        self.page_container = PageContainer(self.admin_console)
        self.backup = RBackup(self.admin_console)
        connection_info = {
            'client_name': self.client.client_name,
            'instance_name': self.instance.instance_name
        }
        if "windows" in self.client.os_info.lower():
            connection_info['socket_file'] = self.tcinputs['Port']
        else:
            connection_info['socket_file'] = self.tcinputs['SocketFile']
        self.helper_object = MYSQLHelper(commcell=self.commcell, hostname=self.client.client_hostname,
                                         user=self.instance.mysql_username,
                                         port=self.tcinputs["Port"], connection_info=connection_info
                                         )
        self.mysql = MySQL(self.helper_object.host_name,
                           self.helper_object.usr,
                           self.helper_object.pwd,
                           self.helper_object.port)

    def tear_down(self):
        """ tear down method for testcase """
        self.helper_object.cleanup_test_data("auto")

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
    def validate_binary_logs(self, is_purged=False, BinarylogsbeforeBackup=None, BinarylogsafterBackup=None):
        """
        method to validate the binary log files
        is_purged   (bool) : if the backup job is with purge log as True
        default : False
        BinarylogsbeforeBackup (list) : binary files before backup
        BinarylogsafterBackup (list)  : binary files after backup

        """
        self.log.info("### Validation of binary log files ###")
        log_list_before_backup = BinarylogsbeforeBackup[0]
        log_list_after_backup = BinarylogsafterBackup[0]

        if is_purged:
            if BinarylogsbeforeBackup[1] >= BinarylogsafterBackup[1]:
                for log_list_entry in log_list_before_backup:
                    for after_log in log_list_after_backup:
                        if log_list_entry[0] == after_log[0]:
                            self.log.info(f"Log file {log_list_entry[0]} found in after backup binary log list")
                            raise CVTestStepFailure("### Validation Failed ###")
                    self.log.info(f"Log file {log_list_entry[0]} validation successful")
            else:
                raise CVTestStepFailure(
                    "### Validation Failed ###\nLog files before backup must be more than after backup")
        else:
            if BinarylogsbeforeBackup[1] <= BinarylogsafterBackup[1]:
                after_backup_index = 0
                for log_list_entry in log_list_before_backup:
                    name_found = False
                    while after_backup_index < len(log_list_after_backup):
                        if log_list_entry[0] == log_list_after_backup[after_backup_index][0]:
                            self.log.info(f"Log file {log_list_entry[0]} validated")
                            name_found = True
                            after_backup_index += 1
                            break
                        after_backup_index += 1
                    if not name_found:
                        self.log.info(f"Binary log file {log_list_entry[0]} not found in after backup binary log list")
                        raise CVTestStepFailure("### Validation Failed ###")
            else:
                raise CVTestStepFailure(
                    "### Validation Failed ###\nLog files before backup must be less than after backup")
        self.log.info("### Validation Successful ###")

    @test_step
    def backup_and_validation(self):
        """
        method to executes backup of the subclient and validation of the binary log files
        """
        self.log.info("Get the binary log information from mysql server before Full backup")
        BinarylogsbeforeBackup = self.mysql.get_binary_logs()
        self.log.info("Full Backup with Purge binary logs as False from subclient level")
        job_id = self.database_group.backup(backup_type=RBackup.BackupType.FULL, purge_binary_log=False)
        self.wait_for_job_completion(job_id)
        self.log.info("Get the binary log information from mysql server after Full backup")
        BinarylogsafterBackup = self.mysql.get_binary_logs()
        self.validate_binary_logs(BinarylogsbeforeBackup=BinarylogsbeforeBackup,
                                  BinarylogsafterBackup=BinarylogsafterBackup)

        self.log.info("Get the binary log information from mysql server before 1st Incremental backup")
        Incr1BinarylogsbeforeBackup = self.mysql.get_binary_logs()
        self.helper_object.populate_database(self.db_list)
        self.log.info("1st Incremental Backup with Purge binary logs as False from instance level")
        self.navigator.navigate_to_db_instances()
        job_id = self.database_instances.backup(instance=self.instance.instance_name,
                                                backup_type=RBackup.BackupType.INCR,
                                                client=self.client.client_name,
                                                purge_binary_log=False)
        self.log.info("Get the binary log information from mysql server after 1st Incremental backup")
        Incr1BinarylogsafterBackup = self.mysql.get_binary_logs()
        self.validate_binary_logs(BinarylogsbeforeBackup=Incr1BinarylogsbeforeBackup,
                                  BinarylogsafterBackup=Incr1BinarylogsafterBackup)

        self.log.info("Get the binary log information from mysql server before 2nd Incremental backup")
        Incr2BinarylogsbeforeBackup = self.mysql.get_binary_logs()
        self.helper_object.populate_database(self.db_list)
        self.log.info("2nd Incremental Backup with Purge binary logs as False from instance details page")
        self.navigate_to_instance()
        self.page_container.access_page_action('Backup')
        job_id = self.backup.submit_backup(backup_type=RBackup.BackupType.INCR, purge_binary_log=False)
        self.wait_for_job_completion(job_id)
        self.log.info("Get the binary log information from mysql server after 2nd Incremental backup")
        Incr2BinarylogsafterBackup = self.mysql.get_binary_logs()
        self.validate_binary_logs(BinarylogsbeforeBackup=Incr2BinarylogsbeforeBackup,
                                  BinarylogsafterBackup=Incr2BinarylogsafterBackup)

        self.log.info("Get the binary log information from mysql server before 3nd Incremental backup")
        Incr3BinarylogsbeforeBackup = self.mysql.get_binary_logs()
        self.helper_object.populate_database(self.db_list)
        self.log.info("3nd Incremental Backup with Purge binary logs as True from instance details page")
        self.navigate_to_instance()
        self.page_container.access_page_action('Backup')
        job_id = self.backup.submit_backup(backup_type=RBackup.BackupType.INCR, purge_binary_log=True)
        self.wait_for_job_completion(job_id)
        self.log.info("Get the binary log information from mysql server after 3rd Incremental backup")
        Incr3BinarylogsafterBackup = self.mysql.get_binary_logs()
        self.validate_binary_logs(is_purged=True, BinarylogsbeforeBackup=Incr3BinarylogsbeforeBackup,
                                  BinarylogsafterBackup=Incr3BinarylogsafterBackup)

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
            self.log.info("Checking if MySql Binary Logging is enabled or not")
            self.helper_object.log_bin_on_mysql_server()
            self.db_group_content = \
                [db for db in [db.lstrip('\\').lstrip('/') for db in self.subclient.content]]
            self.db_list = self.helper_object.generate_test_data(f"auto_{int(time.time())}")
            self.db_instance_details.click_on_entity("default")
            self.backup_and_validation()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
