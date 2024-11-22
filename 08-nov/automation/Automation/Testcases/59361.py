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

    run_restore()               --  method to run restore and validate test data

    verify_restore()            --  method to verify restore has succeeded in case
                                    job goes into pending

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "59361":
                        {
                          "ClientName":"client",
                          "InstanceName":"instance",
                          "DestinationClient": "client1",
                          "DestinationInstance": "instance1"
                          "RedirectAllPath": "redirect/all/path"
                        }
            }

"""

import time
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


class TestCase(CVTestCase):
    """ Class for executing Duplicate database for standby Test for oracle """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Oracle IDA Command Center - Duplicate database for standby"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_59361'
        self.database_type = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'DestinationClient': None,
            'DestinationInstance': None}
        self.dest_client = None
        self.dest_instance = None
        self.oracle_helper_object = None
        self.dest_oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.restore_completed = None

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
                    self.oracle_helper_object.db_execute('alter database open resetlogs')
                    job_obj.kill()
                    job_killed = True
                    break

            if pending_time > timeout or waiting_time > timeout:
                job_obj.kill()
                break

            previous_status = status
        if restore_job and job_killed:
            self.log.info("Verified restore is completed. "
                          "Database is opened and restore job killed")
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
    def run_restore(self):
        """ method to run restore"""
        self.admin_console.select_breadcrumb_link_using_text(
            self.tcinputs['InstanceName'])
        self.admin_console.refresh_page()
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True)
        redirect_all_path = ''
        if "RedirectAllPath" in self.tcinputs:
            redirect_all_path = self.tcinputs["RedirectAllPath"]
        job_id = restore_panel.out_of_place_restore(
            self.tcinputs["DestinationClient"], self.tcinputs["DestinationInstance"],
            redirect_all_path=redirect_all_path,
            rman_duplicate=True, duplicate_standby=True, recover_to="Most recent backup")
        self.wait_for_job_completion(job_id, restore_job=True)
        self.log.info("Restore completed")
        self.restore_completed = True

    @test_step
    def verify_restore(self, jobid):
        """Verifies restore if job goes into pending state due to RMAN script execution failure
            Args:
                jobid : Job ID of restore job
        """
        restore_file = self.oracle_helper_object.fetch_rman_log(jobid, self.client, "restore")
        error_msg = restore_file.rsplit("ERROR MESSAGE STACK")[-1]
        return "RMAN-06054" in error_msg

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

            self.log.info("Preparing for Backup.")
            self.db_instance_details.click_on_entity('default')
            job_id = self.subclient_page.backup(backup_type=RBackup.BackupType.FULL)
            self.wait_for_job_completion(job_id)
            self.log.info("Oracle Full Backup is completed")
            self.oracle_helper_object.backup_validation(job_id, 'Online Full')

            self.log.info("Preparing for Restore.")
            self.run_restore()

            self.log.info("Validating Backed up content")
            if not self.dest_oracle_helper_object:
                self.dest_oracle_helper_object = self.create_helper_object(
                    self.dest_client, self.dest_instance, check_instance_status=False)
                self.dest_oracle_helper_object.recover_standby()
                self.log.info("Waiting for log shipping")
                time.sleep(600)
                self.oracle_helper_object.switch_logfile()
                self.dest_oracle_helper_object.recover_standby(apply=False)
                self.dest_oracle_helper_object.alter_db_state(state='open read only')
            self.dest_oracle_helper_object.validation(
                self.tablespace_name, num_of_files, "CV_TABLE_01", row_limit, standby=True)
            self.log.info("Validation Successfull.")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
