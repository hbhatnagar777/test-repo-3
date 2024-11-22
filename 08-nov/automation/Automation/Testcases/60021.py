# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  Method to setup test variables

    wait_for_job_completion()       --  Waits for completion of job and gets the object once job completes

    tear_down()                     --  tear down function to delete automation generated data

    kill_active_jobs()              --  Method to kill the active jobs running for the client

    connect_to_instance()           --  Connects to instance if exists else creates a new instance

    set_mysql_helper_object()    --  Creates MySQL helper Object

    generate_test_data()            --  Generates test data for backup and restore

    navigate_to_db_group()          --  Connects to database group( more like a subclient )

    backup()                        --  perform backup operation

    restore()                       --  perform restore operation

    cleanup()                       --  Deletes instance if it is created by automation

    run()                           --  run function of this test case

    start_rds()                     --  starts the rds instance

    clean_and_stop_rds               --  cleans the test generated data & stops RDS instance

    stop_rds()                      --  stops the rds instance

"""
import time
from cvpysdk.job import Job
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails, MySQLInstanceDetails
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Application.CloudApps.amazon_helper import AmazonRDSCLIHelper

_CONFIG_DATA = get_config().Virtualization.aws_login_creds
class TestCase(CVTestCase):
    """ Basic acceptance Test for Amazon RDS PAAS MySQL backup and restore from command center
    Example if instance already exists:
    "60021": {
        "ClientName": "shri-an3",
        "Port": "3306",
        "Region": "ap-south-1",
        "InstanceName": "mumbai[ap-south-1]",
        "testdata": [2,10,100]
    }

    Example if instance does not exist:
    "60021": {
          "Access_node": "shri-an3",
          "PlanName": "shri_aws_plan",
          "InstanceName": "mumbai[ap-south-1]",
          "DatabaseUser": "admin",
          "Password": "",
          "Port": "3306",
          "Region": "ap-south-1",
          "testdata": [
            2,
            10,
            100
          ],
          "CredentialName" : "Shrikant"
          }
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Amazon RDS PAAS MySQL ACC1 from Command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_instance = None
        self.db_instance_details = None
        self.perform_instance_check = True
        self.is_automation_instance = None
        self.mysql_helper_object = None
        self.database_group = None
        self.generated_database_list = None
        self.cloud_account = None

    @test_step
    def start_rds(self):
        """Method to start RDS instance if it's present and in stopped state"""
        access_key = _CONFIG_DATA.access_key
        secret_key = _CONFIG_DATA.secret_key
        self.region = self.tcinputs['Region']
        self._instance_identifier = self.tcinputs["InstanceName"][:self.tcinputs["InstanceName"].index('[')]
        self.amazon_rds_helper = AmazonRDSCLIHelper(access_key, secret_key)
        if self.amazon_rds_helper.is_instance_present(self.region, self._instance_identifier, availability=False):
            if not self.amazon_rds_helper.check_instance_state(self.region, self._instance_identifier):
                self.amazon_rds_helper.start_rds_instance(self.region, self._instance_identifier)
            else:
                self.log.info("Instance is in available state already")

    @test_step
    def stop_rds(self):
        """Method to stop RDS instance if it in available state"""
        if self.amazon_rds_helper.check_instance_state(self.region, self._instance_identifier):
            self.amazon_rds_helper.stop_rds_instance(self.region, self._instance_identifier)
        else:
            self.log.info("Instance is in stopped state already")

    def setup(self):
        """ setup test variables """
        self.log.info("*" * 10 + " Initialize browser objects. " + "*" * 10)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        

    @test_step
    def wait_for_job_completion(self, jobid):
        """ Waits for completion of job and gets the object once job completes
        Args:
            jobid   (str): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(f"Failed to run job:{jobid} with error: {job_obj.delay_reason}")
        self.log.info("Successfully finished %s job", jobid)


    @test_step
    def clean_and_stop_rds(self, stop_rds):
        """Tear down function for this testcase"""
        if self.amazon_rds_helper.check_instance_state(self.region, self._instance_identifier):
            if self.mysql_helper_object:
                self.log.info("Deleting Automation Created Data")
                self.mysql_helper_object.cleanup_test_data(database_prefix='automation')
                self.log.info("Deleted Automation Created Data")
        else:
            self.log.info("Instance not available for teardown")
        if stop_rds:
            self.stop_rds()

    def tear_down(self):
        self.clean_and_stop_rds(stop_rds=True)

    @test_step
    def kill_active_jobs(self):
        """ Method to kill the active jobs running for the client """
        active_jobs = self.commcell.job_controller.active_jobs(self.cloud_account)
        if active_jobs:
            for job in active_jobs:
                Job(self.commcell, job).kill(True)
        else:
            self.log.info("No Active Jobs found for the client.")

    @test_step
    def connect_to_instance(self):
        """ Connects to instance if exists else creates a new instance """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance = DBInstances(self.admin_console)

        name_prefix = "test_account"
        timestamp = str(int(time.time()))
        self.cloud_account = name_prefix + timestamp

        if self.perform_instance_check:
            self.perform_instance_check = False
            if self.db_instance.is_instance_exists(DBInstances.Types.MYSQL,
                                                   self.tcinputs["InstanceName"],
                                                   self.cloud_account):
                self.log.info("Instance found!")
                self.admin_console.select_hyperlink(self.tcinputs["InstanceName"])
            else:
                self.log.info("Instance not found. Creating new instance")
                self.is_automation_instance = True
                self.db_instance.add_amazonrds_mysql_instance(self.cloud_account,
                                                              self.tcinputs['PlanName'],
                                                              self.tcinputs['InstanceName'],
                                                              self.tcinputs['DatabaseUser'],
                                                              self.tcinputs['Password'],
                                                              self.tcinputs['Access_node'],
                                                              self.tcinputs['CredentialName'])
                self.log.info("Successfully created Instance.")

        self._client = self.commcell.clients.get(self.cloud_account)
        self._agent = self._client.agents.get('MySQL')
        self._instance = self._agent.instances.get(self.tcinputs['InstanceName'])
        self.db_instance_details = MySQLInstanceDetails(self.admin_console)

    @test_step
    def set_mysql_helper_object(self):
        """ Generating MySQL helper object """
        self.log.info("Creating MySQL Helper Object")
        self.mysql_helper_object = MYSQLHelper(
            commcell=self.commcell,
            subclient='default',
            instance=self.instance,
            user=self.instance.mysql_username,
            port=self.instance.port)
        self.log.info("Created MySQL Helper Object")

    @test_step
    def generate_test_data(self):
        """ Generates test data for backup and restore """
        timestamp = str(int(time.time()))
        data = self.tcinputs['testdata']
        db_prefix = "automation"
        self.log.info("Generating Test Data")
        self.generated_database_list = self.mysql_helper_object.generate_test_data(
            database_prefix=db_prefix + "_" + timestamp,
            num_of_databases=data[0],
            num_of_tables=data[1],
            num_of_rows=data[2])
        self.log.info("Successfully generated Test Data.")

    @test_step
    def navigate_to_db_group(self):
        """ Creates and Connects to a database group consisting of generated Test data( similar to a sub client ) """
        add_subclient_obj = self.db_instance_details.click_add_subclient(DBInstances.Types.MYSQL)
        add_subclient_obj.add_subclient('automation_sc',
                                        1,
                                        self.generated_database_list,
                                        self.tcinputs['PlanName'],)
        self.log.info("Subclient added successfully")

    @test_step
    def backup(self):
        """ perform backup operation """
        self.log.info("#" * 10 + "  Backup/Restore Operations  " + "#" * 10)
        self.log.info("Running Full Backup.")
        db_group_page = MySQLSubclient(self.admin_console)
        job_id = db_group_page.backup(backup_type=RBackup.BackupType.FULL)
        self.wait_for_job_completion(job_id)
        self.log.info("Full backup compeleted successfully.")

    @test_step
    def restore(self):
        """ perform restore operation """
        self.log.info(
            "#" * 10 + "  Running Restore  " + "#" * 10)
        self.log.info("Database list to restore ---- %s", self.generated_database_list)
        self.navigator.navigate_to_db_instances()

        self.db_instance.select_instance(
            DBInstances.Types.MYSQL,
            self.tcinputs['InstanceName'], self.cloud_account)
        self.db_instance_details.access_restore()

        restore_panel = self.db_instance_details.restore_folders(
            database_type=DBInstances.Types.MYSQL, items_to_restore=self.generated_database_list)
        job_id = restore_panel.in_place_restore(data_restore=False,
                                                log_restore=False,
                                                staging_location=None,
                                                notify_job_completion=False,
                                                is_cloud_db=True)
        self.wait_for_job_completion(job_id)
        self.log.info("Database restore completed successfully.")

    @test_step
    def cleanup(self):
        """Deletes instance if it is created by automation"""
        if self.is_automation_instance:
            self.navigator.navigate_to_db_instances()
            self.db_instance.select_instance(DBInstances.Types.MYSQL,
                                             self.tcinputs["InstanceName"],
                                             self.cloud_account)
            db_instance_details = DBInstanceDetails(self.admin_console)
            self.kill_active_jobs()
            db_instance_details.delete_instance()
            self.log.info("Deleted Instance")

    def run(self):
        """ Main method to run testcase """
        try:
            self.start_rds()
            self.connect_to_instance()
            self.set_mysql_helper_object()
            self.clean_and_stop_rds(stop_rds=False)
            self.generate_test_data()
            self.navigate_to_db_group()

            self.log.info("Get the database meta data before backup")
            before_full_backup_db_list = self.mysql_helper_object.get_database_information()
            self.backup()
            self.clean_and_stop_rds(stop_rds=False)
            self.restore()
            self.log.info("Get the database meta data after restore")
            after_restore_db_list = self.mysql_helper_object.get_database_information()

            self.mysql_helper_object.validate_db_info(before_full_backup_db_list,
                                                      after_restore_db_list)


        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
