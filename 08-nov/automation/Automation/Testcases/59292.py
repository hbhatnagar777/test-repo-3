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

    verify_restore()            --  method to verify restore has succeeded in case
                                    job goes into pending

    cleanup()                   --  method to cleanup all testcase created changes

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "59292":
                        {
                          "ClientName":"client",
                          "InstanceName":"instance",
                          "DestinationClient": "client1",
                          "DestinationInstance": "instance1",
                          "Plan": "plan",
                          "RedirectAllPath": "redirect/all/path"    (optional)
                        }
            }

"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.OracleUtils.oraclehelper import OracleHelper


class TestCase(CVTestCase):
    """ Class for executing SOF backup and Cross machine restore Test for oracle """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Oracle IDA Command Center SOF backup and Cross machine restore"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_59292'
        self.database_type = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'DestinationClient': None,
            'DestinationInstance': None,
            'Plan': None}
        self.dest_client = None
        self.dest_instance = None
        self.oracle_helper_object = None
        self.dest_oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.add_subclient = None
        self.automation_subclient = None
        self.restore_completed = None
        self.client_machine_obj = None

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
        self.instance = self.client.agents.get("oracle").instances.get(
            self.tcinputs["InstanceName"])
        self.dest_client = self.commcell.clients.get(self.tcinputs["DestinationClient"])
        self.dest_instance = self.dest_client.agents.get("oracle").instances.get(
            self.tcinputs["DestinationInstance"])

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Deleting Automation Created tablespaces and tables")
        if self.oracle_helper_object:
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01"], tablespace=self.tablespace_name)
        if self.dest_oracle_helper_object and self.restore_completed:
            self.dest_oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01"], tablespace=self.tablespace_name)

    @test_step
    def wait_for_job_completion(self, jobid, restore_job=None):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
            restore_job (bool): True if job is a Restore job

        Returns:
            If restore_job, returns job pending reason
        """
        job_obj = self.commcell.job_controller.get(jobid)

        timeout = 30
        start_time = time.time()
        pending_time = 0
        waiting_time = 0
        previous_status = None
        status_list = ['pending', 'waiting']
        job_killed = False
        while not job_obj.is_finished:
            time.sleep(30)
            status = job_obj.status.lower()
            if status in status_list and previous_status not in status_list:
                start_time = time.time()

            if status == 'pending':
                pending_time = (time.time() - start_time) / 60
            else:
                pending_time = 0

            if status == 'waiting':
                waiting_time = (time.time() - start_time) / 60
            else:
                waiting_time = 0

            if pending_time > 5 and restore_job and 'RMAN-03002' in job_obj.pending_reason:
                if self.verify_restore(jobid):
                    self.dest_oracle_helper_object = self.create_helper_object(
                        self.dest_client, self.dest_instance, check_instance_status=False)
                    self.dest_oracle_helper_object.db_execute('alter database open resetlogs')
                    job_obj.kill()
                    job_killed = True
                    break

            if pending_time > timeout or waiting_time > timeout:
                job_obj.kill()
                break

            previous_status = status
        if restore_job and job_killed:
            self.log.info("Verified restore is completed."
                          " Database is opened and restore job killed")
        elif not job_obj.status.lower() not in ["failed", "killed", "failed to start"]:
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
        self.db_instance_details.access_subclients_tab()
        if self.admin_console.check_if_entity_exists('link', self.tablespace_name):
            self.db_instance_details.click_on_entity(self.tablespace_name)
            self.subclient_page.delete_subclient()
        self.add_subclient = self.db_instance_details.click_add_subclient(DBInstances.Types.ORACLE)
        self.add_subclient.add_subclient(
            subclient_name=self.tablespace_name, plan=self.tcinputs["Plan"])
        self.automation_subclient = self.tablespace_name

    @test_step
    def create_helper_object(self, client, instance, check_instance_status=True):
        """Creates oracle helper object
            Args:
                client                  (Client)    :   Client object
                instance                (Instance)  :   Instance object
                check_instance_status   (bool)      :   True if instance status must be verified
                    default:    True
        """
        oracle_helper_object = OracleHelper(self.commcell, client, instance)
        oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        if check_instance_status:
            oracle_helper_object.check_instance_status()
        return oracle_helper_object

    @test_step
    def validate_backup(self, jobid):
        """Validates Selective Online Full backup"""
        job_obj = self.commcell.job_controller.get(jobid)
        assert job_obj.backup_level == 'Online Full'
        self.client_machine_obj = Machine(self.client)
        mount_mode_logs = self.client_machine_obj.get_logs_for_job_from_file(
            job_id=jobid, log_file_name="ClOraAgent.log", search_term='oraMode = MOUNTED')
        mounted_mode = mount_mode_logs and mount_mode_logs != '\r\n'
        if mounted_mode:
            raise CVTestStepFailure("Database was not open during backup")

    @test_step
    def run_restore(self):
        """ method to run restore"""
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True)
        redirect_all_path = ''
        if "RedirectAllPath" in self.tcinputs:
            redirect_all_path = self.tcinputs["RedirectAllPath"]
        job_id = restore_panel.out_of_place_restore(
            self.tcinputs["DestinationClient"], self.tcinputs["DestinationInstance"],
            redirect_all_path=redirect_all_path)
        self.wait_for_job_completion(job_id, restore_job=True)
        self.log.info("Restore completed")
        self.restore_completed = True

    @test_step
    def verify_restore(self, jobid):
        """Verifies restore if job goes into pending state due to RMAN script execution failure
            Args:
                jobid : Job ID of restore job
        """
        restore_file = self.oracle_helper_object.fetch_rman_log(jobid, self.dest_client, "restore")
        error_msg = restore_file.rsplit("ERROR MESSAGE STACK")[-1]
        return "RMAN-06054" in error_msg

    @test_step
    def cleanup(self):
        """Cleans up testcase created instance"""
        if self.automation_subclient:
            self.navigate_to_instance()
            self.db_instance_details.click_on_entity(self.automation_subclient)
            self.admin_console.wait_for_completion()
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
            else:
                raise Exception('Instance not found')
            self.navigate_to_instance()
            self.log.info("Generating Sample Data for test")
            table_limit = 1
            num_of_files = 1
            row_limit = 10
            self.oracle_helper_object = self.create_helper_object(self.client, self.instance)
            self.oracle_helper_object.create_sample_data(
                self.tablespace_name, table_limit, num_of_files)
            self.oracle_helper_object.db_execute('alter system switch logfile')
            self.log.info("Test Data Generated successfully")

            self.log.info("Creating new Subclient")
            self.new_subclient()
            time.sleep(30)
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

            self.log.info("Preparing for Restore.")
            self.run_restore()

            self.log.info("Validating Backed up content")
            if not self.dest_oracle_helper_object:
                self.dest_oracle_helper_object = self.create_helper_object(
                    self.dest_client, self.dest_instance, check_instance_status=False)
            self.dest_oracle_helper_object.validation(
                self.tablespace_name, num_of_files, "CV_TABLE_01", row_limit)
            self.log.info("Validation Successfull.")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
