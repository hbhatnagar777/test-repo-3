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

    tear_down()                     --  tear down function to delete automation generated data

    kill_active_jobs()              --  Method to kill the active jobs running for the client

    navigate_to_instance_page()     --  Connects to instance if exists else creates new instance

    set_mysql_helper_object()       --  Creates MySQL helper object

    generate_test_data()            --  Generates test data for backup and restore

    navigate_to_db_group()          --  Creates a database group( more like a subclient )

    backup()                        --  perform backup operation

    restore()                       --  perform restore operation

    delete_subclient()              --  Method to delete subclient/db group

    cleanup()                       --  Deletes instance if it is created by automation

    run()                           --  run function of this test case
"""
import time
from cvpysdk.job import Job
from AutomationUtils.cvtestcase import CVTestCase
from Database.dbhelper import DbHelper
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails, MySQLInstanceDetails
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """ Basic acceptance Test for GCP PAAS MySQL backup and restore from command center
    "60019": {
          "PlanName": "-",
          "InstanceName": "-",
          "DatabaseUser": "-",
          "Password": "-",
          "testdata": [1,1,2],
          "AccessNode": "shri-rocky9",
          "CredentialName": "ash-gcp"
    }
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "GCP PAAS MySQL ACC1 from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_group_page = None
        self.dbhelper_object = None
        self.db_instance = None
        self.db_instance_details = None
        self.perform_instance_check = True
        self.mysql_helper_object = None
        self.database_group = None
        self.generated_database_list = None

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
        self.dbhelper_object = DbHelper(self.commcell)
        self.db_group_page = SubClient(self.admin_console)

    def tear_down(self):
        """Tear down function for this testcase"""
        if self.mysql_helper_object:
            self.log.info("Deleting Automation Created Data")
            self.mysql_helper_object.cleanup_test_data(database_prefix='automation')
            self.log.info("Deleted Automation Created Data")

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
    def navigate_to_instance_page(self):
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
                self.db_instance.add_gcp_mysql_instance(cloud_account=self.cloud_account,
                                                              plan=self.tcinputs['PlanName'],
                                                              instance_name=self.tcinputs['InstanceName'],
                                                              database_user=self.tcinputs['DatabaseUser'],
                                                              password=self.tcinputs['Password'],
                                                              access_node=self.tcinputs['AccessNode'],
                                                              credential_name=self.tcinputs['CredentialName'])
                self.log.info("Successfully created Instance.")

        self.commcell.refresh()
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
            user=self.tcinputs['DatabaseUser'],
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
        ###################### Running Full Backup ##############################
        self.log.info("#" * 10 + "  Backup/Restore Operations  " + "#" * 10)
        self.log.info("Running Full Backup.")
        job_id = self.db_group_page.backup(backup_type=RBackup.BackupType.FULL)
        self.dbhelper_object.wait_for_job_completion(job_id)
        self.log.info("Full backup compeleted successfully.")

    @test_step
    def restore(self):
        """ perform restore operation """
        ####################### Running restore ###################################
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
        self.dbhelper_object.wait_for_job_completion(job_id)
        self.log.info("Database restore completed successfully.")

    @test_step
    def delete_subclient(self):
        """ Method to delete subclient/db group"""
        self.navigator.navigate_to_db_instances()
        self.db_instance.select_instance(
            DBInstances.Types.MYSQL,
            self.tcinputs['InstanceName'], self.cloud_account)
        self.db_instance_details.select_entities_tab()
        self.admin_console.select_hyperlink('automation_sc')

        if self.db_group_page:
            self.db_group_page.delete_subclient()
            self.log.info("deleted subclient automation_sc")
        self.log.info("automation_sc subclient deleted.")

    @test_step
    def cleanup(self):
        """Deletes instance if it is created by automation"""
        self.delete_subclient()
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
            self.navigate_to_instance_page()
            self.set_mysql_helper_object()
            self.tear_down()
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
