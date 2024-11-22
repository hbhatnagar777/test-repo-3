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

    wait_for_job_completion()   --  waits for completion of job

    navigate_to_instance()      --  navigates to specified instance

    create_helper_object()      --  creates object of OracleHelper class

    fill_sample_data()          --  creates a table in the database and populates it with sample data

    drop_usertable()            --  drops user table from database

    run_backup()                --  method to Runs backup job

    run_restore()               --  method to run restore

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "3511":
                        {
                          "ClientName":"client",
                          "InstanceName":"instance"
                        }
            }

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.OracleUtils.oraclehelper import OracleHelper
from datetime import datetime
from pytz import timezone


class TestCase(CVTestCase):
    """ Class for executing PIT restore TestCase for Oracle """
    test_step = TestStep()

    def __init__(self):
        """
        Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Oracle Point in Time Restore from Command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_3511'
        self.database_type = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None}
        self.oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.time = None

    def setup(self):
        """
        Method to setup test variables
        """
        self.log.info("Started executing %s testcase", self.id)
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = OracleInstanceDetails(self.admin_console)
        self.subclient_page = SubClient(self.admin_console)
        self.database_type = DBInstances.Types.ORACLE

    def tear_down(self):
        """
        Tear down method for testcase
        """
        self.log.info("Deleting Automation Created tablespace and tables")
        if self.oracle_helper_object:
            self.oracle_helper_object.oracle_data_cleanup(self.tablespace_name, ["CV_TABLE_01"],
                                                          f"{self.tablespace_name}_user")

    @test_step
    def wait_for_job_completion(self, job_id):
        """
        Waits for completion of job and check job status
        Args:
            job_id   (int): Job_id of the job we are waiting for completion of.
        """
        job_obj = self.commcell.job_controller.get(job_id)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (job_id, job_obj.delay_reason)
            )

    @test_step
    def navigate_to_instance(self):
        """
        Navigates to Instance page
        """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.ORACLE,
                                                self.tcinputs["InstanceName"],
                                                self.tcinputs["ClientName"])

    @test_step
    def create_helper_object(self):
        """
        Creates oracle helper object
        """
        self.instance = self.client.agents.get("oracle").instances.get(
            self.tcinputs["InstanceName"])
        self.oracle_helper_object = OracleHelper(self.commcell, self.client, self.instance)
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

    @TestStep()
    def fill_sample_data(self):
        """
        Create a table in the database and populate table with records.
        """
        self.oracle_helper_object.create_sample_data(self.tablespace_name)

    @TestStep()
    def drop_usertable(self):
        """
        Drops the table from connected database.

        """
        self.oracle_helper_object.db_drop_table(f"{self.tablespace_name}_user", 'CV_TABLE_01')

    @test_step
    def run_backup(self, first_backup_job=False, backup_type=RBackup.BackupType.FULL):
        """
        Runs a backup job on the subclient
            Args:
             first_backup_job  (bool):  True for the first backup job run
              default: False
             backup_type   (RBackup.BackupType):  Type of backup to perform
        """
        if first_backup_job:
            job_id = self.subclient_page.backup(backup_type=backup_type)
        else:
            job_id = self.subclient_page.backup(backup_type=backup_type)
        self.wait_for_job_completion(job_id)
        if first_backup_job:
            self.time = datetime.now(timezone('Asia/Kolkata')).strftime('%m/%d/%Y %H:%M:%S')
        self.log.info("Backup is completed")

    @test_step
    def run_restore(self):
        """
        Method to run restore
        """
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True)
        job_id = restore_panel.in_place_restore(recover_to=self.time)
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed")

    def run(self):
        """
        Main function for test case execution
        """
        try:
            self.create_helper_object()

            self.fill_sample_data()

            self.navigate_to_instance()

            self.db_instance_details.click_on_entity('default')

            self.run_backup(first_backup_job=True)

            self.drop_usertable()

            user = "{0}_user".format(self.tablespace_name.lower())
            self.oracle_helper_object.db_create_table(
                self.tablespace_name, "CV_TABLE_INCR_", user, 1)

            self.run_backup(backup_type=RBackup.BackupType.INCR)

            self.run_restore()

            self.oracle_helper_object.validation(self.tablespace_name, 1, "CV_TABLE_01", 10)
            try:
                self.oracle_helper_object.validation(self.tablespace_name, 1, "CV_TABLE_INCR_01", 10)
            except Exception as exp:
                exp = str(exp)
                if exp == ("Failed to execute the SQL query\nError: \"ORA-00942: table or view does not exist\nHelp: "
                           "https://docs.oracle.com/error-help/db/ora-00942/\""):
                    self.log.info("Point in Time data validation is successful")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
