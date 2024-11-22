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

    add_mysql_instance()            --  Method to create GCP MySQL Instance

    edit_ssl_properties()           --  Method to edit instance and add SSL Properties

    navigate_to_instance_page()     --  Connects to instance delete and recreates if exists else creates a new one

    set_mysql_helper_object()       --  Creates MySQL helper Object

    generate_test_data()            --  Generates test data for backup and restore

    navigate_to_db_group()          --  Navigates to database group Page

    backup()                        --  perform backup operation

    restore()                       --  perform restore operation

    cleanup()                       --  Deletes instance if it is created by automation

    run()                           --  run function of this test case

"""
import time
from cvpysdk.job import Job
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Databases.db_instance_details import MySQLInstanceDetails, CloudDBInstanceDetails
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import MySQLSubclient
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception

_CONFIG_DATA = get_config().MySQL


class TestCase(CVTestCase):
    """ ACC1 for GCP PAAS MySQL SSL from command center
            Example
            "60574": {
                "ClientName": "cv-ca",
                "PlanName": "plan",
                "InstanceName": "mysql",
                "DatabaseUser": "username",
                "Password": "password",
                "ssl_ca":"path-to-ssl-ca-on-proxy",
                "ssl_cert": "path-to-ssl-cert-on-proxy",
                "ssl_key": "path-to-ssl-key-on-proxy",
                "testdata": [1, 1, 1]
            }
        """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "ACC1 for GCP PAAS SSL enabled MySQL from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_instance = None
        self.db_instance_details = None
        self.mysql_helper_object = None
        self.database_list = None
        self.database_group = None
        self.is_automation_instance = False
        self.perform_instance_check = True

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

    def tear_down(self):
        """Tear down function for this testcase"""
        if self.mysql_helper_object:
            self.log.info("Deleting Automation Created Data")
            self.mysql_helper_object.cleanup_test_data(database_prefix='automation')
            self.log.info("Deleted Automation Created Data")

    @test_step
    def kill_active_jobs(self):
        """ Method to kill the active jobs running for the client """
        active_jobs = self.commcell.job_controller.active_jobs(self.tcinputs['ClientName'])
        if active_jobs:
            for job in active_jobs:
                Job(self.commcell, job).kill(True)
        else:
            self.log.info("No Active Jobs found for the client.")

    @test_step
    def add_mysql_instance(self):
        """ Method to create GCP MySQL Instance """
        self.is_automation_instance = True
        self.db_instance.add_gcp_mysql_instance(self.tcinputs['ClientName'],
                                                self.tcinputs['PlanName'],
                                                self.tcinputs['InstanceName'],
                                                self.tcinputs['DatabaseUser'],
                                                self.tcinputs['Password'],
                                                ssl=True,
                                                ssl_ca=self.tcinputs['ssl_ca'],
                                                ssl_cert=self.tcinputs['ssl_cert'],
                                                ssl_key=self.tcinputs['ssl_key'])

    @test_step
    def edit_ssl_properties(self):
        """ Method to edit instance and add SSL Properties """
        self.db_instance_details = CloudDBInstanceDetails(self.admin_console)
        self.db_instance_details.edit_cloud_mysql_ssl_properties(ssl_ca=self.tcinputs['ssl_ca'],
                                                                 ssl_cert=self.tcinputs['ssl_cert'],
                                                                 ssl_key=self.tcinputs['ssl_key'])

    @test_step
    def navigate_to_instance_page(self):
        """ Connects to instance if exists else creates a new instance """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance = DBInstances(self.admin_console)
        if self.perform_instance_check:
            self.perform_instance_check = False
            if self.db_instance.is_instance_exists(DBInstances.Types.MYSQL,
                                                   self.tcinputs["InstanceName"],
                                                   self.tcinputs["ClientName"]):
                self.log.info("Instance found!")
                self.admin_console.select_hyperlink(self.tcinputs["InstanceName"])
                self.edit_ssl_properties()
            else:
                self.log.info("Instance not found. Creating new instance")
                self.add_mysql_instance()
                self.log.info("Successfully created Instance.")

        self._agent = self._client.agents.get('MySQL')
        self._instance = self._agent.instances.get(self.tcinputs['InstanceName'])
        self.db_instance_details = MySQLInstanceDetails(self.admin_console)
        self.database_group = MySQLSubclient(self.admin_console)

    @test_step
    def set_mysql_helper_object(self):
        """ Generating MySQL helper object
        These are from config.json - these paths are ssl files on the controller """
        ssl_ca = _CONFIG_DATA.MySqlSSLOptions.ssl_ca
        ssl_cert = _CONFIG_DATA.MySqlSSLOptions.ssl_cert
        ssl_key = _CONFIG_DATA.MySqlSSLOptions.ssl_key
        self.log.info("Creating MySQL Helper Object")
        self.mysql_helper_object = MYSQLHelper(
            commcell=self.commcell,
            subclient='default',
            instance=self.instance,
            user=self.instance.mysql_username,
            port=self.instance.port,
            ssl_ca=ssl_ca,
            ssl_cert=ssl_cert,
            ssl_key=ssl_key
        )
        self.log.info("Created MySQL Helper Object.")

    @test_step
    def generate_test_data(self):
        """ Generates test data for backup and restore """
        timestamp = str(int(time.time()))
        data = self.tcinputs['testdata']
        db_prefix = "automation"
        self.log.info("Generating Test Data")
        self.database_list = self.mysql_helper_object.generate_test_data(
            database_prefix=db_prefix + "_" + timestamp,
            num_of_databases=data[0],
            num_of_tables=data[1],
            num_of_rows=data[2])
        self.log.info("Successfully generated Test Data.")

    @test_step
    def navigate_to_db_group(self):
        """ Navigates to database group Page """
        self.db_instance_details.click_on_entity('default')
        self.log.info("Conencted to 'default' database group.")

    @test_step
    def backup(self):
        """ perform backup operation """
        self.log.info("Running Full Backup.")
        job_id = self.database_group.backup(backup_type=RBackup.BackupType.FULL)
        self.wait_for_job_completion(job_id)
        self.log.info("Full backup compeleted successfully.")

    @test_step
    def restore(self):
        """ perform restore operation """
        self.log.info("Database list to restore --- %s", self.database_list)
        self.navigator.navigate_to_db_instances()
        self.db_instance.select_instance(
            DBInstances.Types.MYSQL,
            self.tcinputs['InstanceName'], self.tcinputs['ClientName'])
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=DBInstances.Types.MYSQL, items_to_restore=self.database_list)
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
                                             self.tcinputs["ClientName"])
            self.kill_active_jobs()
            self.db_instance_details.delete_instance()
            self.log.info("Deleted Instance")

    def run(self):
        """ Main method to run testcase """
        try:
            self.navigate_to_instance_page()
            self.set_mysql_helper_object()
            self.generate_test_data()
            self.navigate_to_db_group()
            self.log.info("Get the database meta data before backup")
            before_full_backup_db_list = self.mysql_helper_object.get_database_information()
            self.backup()
            self.tear_down()
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
