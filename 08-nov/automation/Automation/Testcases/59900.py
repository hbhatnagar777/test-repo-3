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

    cleanup()                   --  method to cleanup all testcase created changes

    run()                       --  run function of this test case


Input Example:

    "testCases":
        {
            "59900":
                {
                    "RacInstanceName": "name of the instance",
                    "RacClusterName": "name of the cluster",
                    "DestinationRacInstance": "name of the destination instance",
                    "DestinationRacCluster": "name of the destination cluster",
                    "RedirectAllPath": "redirect/all/path"    (optional)
                }
        }


"""
import json
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Components.panel import Backup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.OracleUtils.oraclehelper import OracleRACHelper


class TestCase(CVTestCase):
    """ Class for executing out of place restore recover to SCN Test for oracle RAC """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Test for Oracle RAC on Command Center - recover to SCN"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_59900'
        self.database_type = None,
        self.tcinputs = {
            'RacClusterName': None,
            'RacInstanceName': None,
            'DestinationRacCluster': None,
            'DestinationRacInstance': None
            }
        self.oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.dest_client = None
        self.dest_instance = None
        self.dest_oracle_helper_object = None
        self.restore_completed = False

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
        self.subclient_page = SubClient(self.admin_console)
        self.database_type = DBInstances.Types.ORACLE_RAC
        self.dest_client = self.commcell.clients.get(self.tcinputs["DestinationRacCluster"])
        self.dest_instance = self.dest_client.agents.get("oracle").instances.get(
            self.tcinputs["DestinationRacInstance"])

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Deleting Automation Created tablespaces and tables")
        if self.oracle_helper_object:
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01", "CV_TABLE_TEST_01"], tablespace=self.tablespace_name,
                user="{0}_user".format(self.tablespace_name.lower()))
        if self.dest_oracle_helper_object and self.restore_completed:
            self.dest_oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01", "CV_TABLE_TEST_01"], tablespace=self.tablespace_name,
                user="{0}_user".format(self.tablespace_name.lower()))

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
    def check_if_instance_exists(self):
        """Checking if instance exists"""
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
        """Navigates to Instance page"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.ORACLE_RAC,
                                                self.tcinputs["RacInstanceName"],
                                                self.tcinputs["RacClusterName"])

    @test_step
    def create_helper_object(self):
        """Creates oracle RAC helper object"""
        self.client = self.commcell.clients.get(self.tcinputs["RacClusterName"])
        self.instance = self.client.agents.get("oracle rac").instances.get(
            self.tcinputs["RacInstanceName"])
        self.oracle_helper_object = OracleRACHelper(self.commcell, self.client, self.instance)
        self.oracle_helper_object.db_connect(OracleRACHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

    @test_step
    def create_test_data(self):
        """Generating sample data for test"""
        table_limit = 1
        num_of_files = 1
        row_limit = 10
        self.oracle_helper_object.create_sample_data(
            self.tablespace_name, table_limit, num_of_files)
        self.oracle_helper_object.db_execute('alter system switch logfile')
        self.log.info("Test Data Generated successfully")

    @test_step
    def run_backup(self, level):
        """ method to run backup"""
        if level.lower() == "full":
            self.log.info("Preparing for Full Backup.")
            job_id = self.subclient_page.backup(backup_type=Backup.BackupType.FULL)
            self.wait_for_job_completion(job_id)
            self.log.info("Oracle RAC Full Backup is completed")
            self.oracle_helper_object.backup_validation(job_id, 'Online Full')
        else:
            self.log.info("Preparing for Incremental Backup.")
            job_id = self.subclient_page.backup(backup_type=Backup.BackupType.INCR)
            self.wait_for_job_completion(job_id)
            self.log.info("Oracle RAC Incremental Backup is completed")
            self.oracle_helper_object.backup_validation(job_id, 'Incremental')

    @test_step
    def get_restore_scn(self):
        """ method to get SCN to restore from database"""
        self.log.info("Generating Sample Data for SCN Restore test")
        user = "{0}_user".format(self.tablespace_name.lower())
        self.oracle_helper_object.db_create_table(
            self.tablespace_name, "CV_TABLE_TEST_", user, table_limit)
        self.log.info("Successfully generated sample data for incremental backups")

        scn_after_full = self.oracle_helper_object.get_current_scn()

        self.log.info("Cleaning up table before Incremental backup")
        self.oracle_helper_object.oradb.drop_table(
            user, "CV_TABLE_TEST_01")
        return scn_after_full

    @test_step
    def run_restore(self, scn):
        """ method to run restore"""
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs["RacInstanceName"])
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True)
        redirect_all_path = None
        if "RedirectAllPath" in self.tcinputs:
            redirect_all_path = self.tcinputs["RedirectAllPath"]
        job_id = restore_panel.out_of_place_restore(
            destination_client=self.tcinputs.get("DestinationRacCluster"),
            destination_instance=self.tcinputs.get("DestinationRacInstance"),
            recover_to=scn, redirect_all_path=redirect_all_path)
        self.wait_for_job_completion(job_id)
        self.restore_completed = True
        self.log.info("Oracle RAC Restore completed")

    @test_step
    def validate_restore(self):
        """ method to validate restore"""
        table_limit = 1
        num_of_files = 1
        row_limit = 10
        if not self.dest_oracle_helper_object:
            self.dest_oracle_helper_object = self.create_helper_object(
                self.dest_client, self.dest_instance, check_instance_status=False)
        self.log.info("Validating Backed up content")

        self.dest_oracle_helper_object.validation(self.tablespace_name, num_of_files,
                                                  "CV_TABLE_01", row_limit)
        self.dest_oracle_helper_object.validation(self.tablespace_name, num_of_files,
                                                  "CV_TABLE_TEST_01", row_limit)
        self.log.info("Restore Validation Successful.")

    def run(self):
        """ Main function for test case execution """
        try:
            self.check_if_instance_exists()
            self.navigate_to_instance()
            self.create_helper_object()
            self.create_test_data()
            self.db_instance_details.click_on_entity('default')
            self.run_backup(level="full")
            scn_after_full = self.get_restore_scn()
            self.run_backup(level="incr")
            self.run_restore(scn=scn_after_full)
            self.validate_restore()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.log.info("Logging out of the admin console")
            AdminConsole.logout_silently(self.admin_console)
            self.log.info("Closing the browser")
            Browser.close_silently(self.browser)
