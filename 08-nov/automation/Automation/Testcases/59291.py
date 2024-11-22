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

    new_subclient()             --  runs method to create new subclient

    create_helper_object()      --  creates object of OracleHelper class

    validate_backup()           --  method to validate backup

    run_restore()               --  method to run restore and validate test data

    cleanup()                   --  method to cleanup all testcase created changes

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "59291":
                        {
                          "ClientName":"client",
                          "InstanceName":"instance",
                          "Plan":"XXXX",
                          "ConnectString":"username/password@servicename"
                        }
            }

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Components.table import Rtable
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.OracleUtils.oraclehelper import OracleHelper
import time


class TestCase(CVTestCase):
    """ Class for testing auto discovery and offline backups for oracle """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Oracle IDA Command Center Auto discovery and Offline backups"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_59291'
        self.database_type = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'Plan': None,
            'ConnectString': None}
        self.oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.add_subclient = None
        self.automation_instance = None
        self.automation_subclient = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
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
        """ tear down method for testcase """
        self.log.info("Deleting Automation Created tablespaces and tables")
        if self.oracle_helper_object:
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01"], tablespace=self.tablespace_name)

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.ORACLE,
                                                self.tcinputs["InstanceName"],
                                                self.tcinputs["ClientName"])

    @test_step
    def new_subclient(self):
        """Adds new subclient"""
        if self.admin_console.check_if_entity_exists('link', self.tablespace_name):
            self.db_instance_details.click_on_entity(self.tablespace_name)
            self.subclient_page.delete_subclient()
        self.add_subclient = self.db_instance_details.click_add_subclient(DBInstances.Types.ORACLE)
        self.add_subclient.add_subclient(
            subclient_name=self.tablespace_name, plan=self.tcinputs["Plan"],
            backup_mode="Offline database")
        self.automation_subclient = self.tablespace_name

    @test_step
    def create_helper_object(self):
        """Creates oracle helper object"""
        self.instance = self.client.agents.get("oracle").instances.get(
            self.tcinputs["InstanceName"])
        self.oracle_helper_object = OracleHelper(self.commcell, self.client, self.instance)
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

    @test_step
    def validate_backup(self, jobid):
        """Validates Offline backup"""
        job_obj = self.commcell.job_controller.get(jobid)
        assert job_obj.backup_level == 'Offline Full'
        client_machine_obj = Machine(self.client)
        mount_mode_logs = client_machine_obj.get_logs_for_job_from_file(
            job_id=jobid, log_file_name="ClOraAgent.log", search_term='oraMode = MOUNTED')
        mounted_mode = mount_mode_logs and mount_mode_logs != '\r\n'
        lights_out_logs = client_machine_obj.get_logs_for_job_from_file(
            job_id=jobid, log_file_name="ClOraAgent.log", search_term='LightOut()')
        lights_out_script_executed = lights_out_logs and lights_out_logs != '\r\n'
        if not mounted_mode and lights_out_script_executed:
            raise CVTestStepFailure("Database was not shutdown during backup")

    @test_step
    def run_restore(self):
        """ method to run restore"""
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True)
        job_id = restore_panel.in_place_restore()
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed")

    def cleanup(self):
        """Cleans up testcase created instance"""
        if self.automation_instance is not None and self.automation_instance:
            self.navigate_to_instance()
            self.db_instance_details.delete_instance()
        else:
            if self.automation_subclient:
                self.navigate_to_instance()
                self.db_instance_details.click_on_entity(self.automation_subclient)
                self.subclient_page.delete_subclient()

    def run(self):
        """ Main function for test case execution """
        try:
            self.navigator.navigate_to_db_instances()
            self.admin_console.wait_for_completion()
            self.log.info("Checking if instance exists")
            if self.database_instances.is_instance_exists(DBInstances.Types.ORACLE,
                                                          self.tcinputs["InstanceName"],
                                                          self.tcinputs["ClientName"]):
                self.log.info("Instance found")
                self.navigate_to_instance()
                self.db_instance_details.delete_instance()
                self.automation_instance = False
            else:
                self.automation_instance = True
            self.database_instances.discover_instances(
                DBInstances.Types.ORACLE, self.tcinputs["ClientName"])
            time.sleep(300)
            Rtable(self.admin_console).reload_data()
            self.database_instances.select_instance(DBInstances.Types.ORACLE,
                                                    self.tcinputs["InstanceName"],
                                                    self.tcinputs["ClientName"])
            self.admin_console.wait_for_completion(5000)
            self.db_instance_details.edit_instance_update_credentials(
                self.tcinputs["ConnectString"], plan=self.tcinputs["Plan"])
            table_limit = 1
            num_of_files = 1
            row_limit = 10
            self.create_helper_object()
            self.oracle_helper_object.create_sample_data(
                self.tablespace_name, table_limit, num_of_files)
            self.oracle_helper_object.db_execute('alter system switch logfile')
            self.log.info("Test Data Generated successfully")

            self.log.info("Creating new Subclient")
            self.new_subclient()
            active_jobs = self.commcell.job_controller.active_jobs(
                client_name=self.tcinputs['ClientName'], job_filter="Backup")
            active_job = None
            for job in active_jobs:
                job_obj = self.commcell.job_controller.get(job)
                if job_obj.subclient_name == self.tablespace_name \
                        and job_obj.instance_name == self.instance.instance_name:
                    active_job = job_obj
                    break
            if active_job:
                job_id = active_job.job_id

            else:
                job_id = self.subclient_page.backup(backup_type=RBackup.BackupType.FULL)
            self.wait_for_job_completion(job_id)
            self.validate_backup(job_id)
            self.log.info("Oracle Full Backup is completed")

            self.log.info("Cleaning up tablespace and data before restore")
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01"], tablespace=self.tablespace_name)

            self.log.info("Preparing for Restore.")
            self.run_restore()

            self.log.info("Validating Backed up content")
            self.oracle_helper_object.validation(self.tablespace_name, num_of_files,
                                                 "CV_TABLE_01", row_limit)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
