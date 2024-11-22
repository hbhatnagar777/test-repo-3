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

    check_if_instance_exists()  --  checks if instance exists

    navigate_to_instance()      --  navigates to specified instance

    create_helper_object()      --  creates object of OracleHelper class

    create_test_data()          --  creates test data

    new_subclient()             --  method to create new subclient

    backup_and_validate()       --  method to run backup and validate backup

    run_restore()               --  method to run restore

    validate_restore()          --  method to validate restore

    cleanup()                   --  method to cleanup all testcase created changes

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "5019":
                        {
                          "ClientName":"client",
                          "InstanceName":"instance",
                          "Plan":"XXXX"
                        }
            }

"""

from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import OracleSubclient
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.OracleUtils.oraclehelper import OracleHelper
import time


class TestCase(CVTestCase):
    """ Class for executing Archive log Backup Test for Oracle """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "CMP - Basic - Data Protection and Recovery - Archive logs"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_5019'
        self.database_type = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'Plan': None}
        self.oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.machine_object = None
        self.subclient_page = None
        self.add_subclient = None
        self.automation_subclient = None
        self.backup_scn = None
        self.restore_scn = None

    def setup(self):
        """ Method to setup test variables """
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
        self.subclient_page = OracleSubclient(self.admin_console)
        self.machine_object = Machine(self.client, self.commcell)
        self.database_type = DBInstances.Types.ORACLE

    def tear_down(self):
        """ tear down method for testcase """
        if self.status == constants.PASSED:
            self.cleanup()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    @test_step
    def wait_for_job_completion(self, jobid):
        """ Waits for completion of job and gets the object once job completes
            Args:
                jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )

    @test_step
    def check_if_instance_exists(self):
        """ Checking if instance exists """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        if self.database_instances.is_instance_exists(DBInstances.Types.ORACLE,
                                                      self.tcinputs["InstanceName"],
                                                      self.tcinputs["ClientName"]):
            self.log.info("Instance found")
        else:
            raise CVTestStepFailure("Instance not found")

    @test_step
    def navigate_to_instance(self):
        """ Navigates to Instance page """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.ORACLE,
                                                self.tcinputs["InstanceName"],
                                                self.tcinputs["ClientName"])

    @test_step
    def create_helper_object(self):
        """ Creates oracle helper object """
        self.instance = self.client.agents.get("oracle").instances.get(
            self.tcinputs["InstanceName"])
        self.oracle_helper_object = OracleHelper(self.commcell, self.client, self.instance)
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

    @test_step
    def create_test_data(self):
        """ Generating Sample Data for test """
        table_limit = 1
        num_of_files = 1
        row_limit = 10
        self.create_helper_object()
        self.oracle_helper_object.create_sample_data(
            self.tablespace_name, table_limit, num_of_files, row_limit)
        self.oracle_helper_object.db_execute('alter system switch logfile')
        self.log.info("Test Data Generated successfully")

    @test_step
    def new_subclient(self):
        """ Adding new subclient """
        self.db_instance_details.access_subclients_tab()
        if self.admin_console.check_if_entity_exists('link', self.tablespace_name):
            self.db_instance_details.click_on_entity(self.tablespace_name)
            time.sleep(60)
            self.subclient_page.delete_subclient()
        self.add_subclient = self.db_instance_details.click_add_subclient(DBInstances.Types.ORACLE)
        self.add_subclient.add_subclient(
            subclient_name=self.tablespace_name, plan=self.tcinputs["Plan"],
            backup_mode="Archive log backup", delete_archive_logs=False)
        self.log.info("Waiting for subclient creation completion")
        time.sleep(60)
        self.automation_subclient = self.tablespace_name

    @test_step
    def backup_and_validate(self):
        """ Method to run backup and validate backup """
        job_id = self.subclient_page.backup(backup_type=RBackup.BackupType.FULL)
        self.wait_for_job_completion(job_id)
        self.log.info("Oracle Full Backup is completed")

        self.log.info("Fetching SCN of backup job from ClOraAgent.log")
        search_term = f".*nextChange"
        output = self.machine_object.get_logs_for_job_from_file(job_id=job_id, log_file_name="ClOraAgent.log",
                                                                search_term=search_term)
        self.backup_scn = output.split('nextChange=[')[1].split(']')[0]

        self.log.info("Validation of Backup")
        rman_log = self.oracle_helper_object.fetch_rman_log(job_id, self.client, 'backup').splitlines()
        for log_line in rman_log:
            if "archived log backup set" in log_line:
                self.log.info("Validation of Backup is successful")
                return
        raise Exception("Backup Validation Failed")

    @test_step
    def run_restore(self):
        """ Method to run restore """
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True)
        job_id = restore_panel.in_place_restore()
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed")

        self.log.info("Fetching SCN from restore rman logs")
        rman_log = self.oracle_helper_object.fetch_rman_log(job_id, self.client, 'restore').splitlines()
        for log_line in rman_log:
            if "recover database until scn" in log_line:
                self.restore_scn = log_line.split(' ')[5]
                return

    @TestStep()
    def validate_restore(self):
        """ Validates if the restore job was successful """
        self.log.info("Validating restore by checking SCN values from backup log and restore log are same or not")
        if self.restore_scn == self.backup_scn:
            self.log.info("Validation of Restore is successful")
        else:
            raise Exception("Restore Validation Failed")

    @test_step
    def cleanup(self):
        """ cleanup method """
        if self.automation_subclient:
            self.navigate_to_instance()
            self.db_instance_details.click_on_entity(self.automation_subclient)
            self.subclient_page.delete_subclient()
        self.log.info("Deleting Automation Created tablespaces and tables")
        if self.oracle_helper_object:
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01"], tablespace=self.tablespace_name,
                user="{0}_user".format(self.tablespace_name.lower()))

    def run(self):
        """ Main function for test case execution """
        try:
            self.check_if_instance_exists()

            self.navigate_to_instance()

            self.create_test_data()

            self.new_subclient()

            self.backup_and_validate()

            self.run_restore()

            self.validate_restore()

        except Exception as exp:
            handle_testcase_exception(self, exp)
