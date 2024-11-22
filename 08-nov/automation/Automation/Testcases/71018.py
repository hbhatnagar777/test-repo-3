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

    navigate_to_instance_page()     --  Connects to instance if exists else creates a new instance

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
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails, PostgreSQLInstanceDetails
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.subclient import PostgreSQLSubclient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """ Basic acceptance Test for GCP PAAS Alloydb backup and restore from command center
    Example if instance already exists:
    "71018": {
          "PlanName": "",
          "InstanceName": "alloydb[asia-south1]",
          "DatabaseUser": "",
          "Password": "",
          "testdata": [1,1,2],
          "AccessNode": "shri-rocky9",
          "CredentialName": "ash-gcp",
          "Endpoint" : "ip:port"
    }
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "GCP PAAS alloydb ACC1 from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.connection_info = None
        self.postgres_helper_object = None
        self.pgsql_db_object = None
        self.dbhelper_object = None
        self.db_group_page = None
        self.db_instance = None
        self.db_instance_details = None
        self.database_group = None
        self.generated_database_list = ["pgdb","pgdb2"]

    def setup(self):
        """ Method to setup test variables """
        self.log.info("*" * 10 + " Initialize browser objects. " + "*" * 10)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.db_group_page = PostgreSQLSubclient(self.admin_console)
        self.dbhelper_object = DbHelper(self.commcell)

    def tear_down(self):
        """ tear down function to delete automation generated data """
        pass

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

        ##use same cloud account name for each case
        name_prefix = "test_account"
        timestamp = str(int(time.time()))
        self.cloud_account = name_prefix + timestamp

        if self.perform_instance_check:
            self.perform_instance_check = False
            if self.db_instance.is_instance_exists(DBInstances.Types.POSTGRES,
                                                   self.tcinputs["InstanceName"],
                                                   self.cloud_account):
                self.log.info("Instance found!")
                self.admin_console.select_hyperlink(self.tcinputs["InstanceName"])
            else:
                self.log.info("Instance not found. Creating new instance")
                self.is_automation_instance = True
                self.db_instance.add_gcp_alloydb_instance(cloud_account=self.cloud_account,
                                                                plan=self.tcinputs['PlanName'],
                                                                instance_name=self.tcinputs['InstanceName'],
                                                                database_user=self.tcinputs['DatabaseUser'],
                                                                password=self.tcinputs['Password'],
                                                                access_node=self.tcinputs['AccessNode'],
                                                                credential_name=self.tcinputs['CredentialName'],
                                                                endpoint=self.tcinputs['Endpoint'])
                self.log.info("Successfully created Instance.")
        self.commcell.refresh()
        self._client = self.commcell.clients.get(self.cloud_account)
        self._agent = self._client.agents.get('PostgreSQL')
        self._instance = self._agent.instances.get(self.tcinputs['InstanceName'])
        self.db_instance_details = PostgreSQLInstanceDetails(self.admin_console)

    @test_step
    def navigate_to_db_group(self):
        """ Creates and Connects to a database group consisting of generated Test data( similar to a sub client ) """
        add_subclient_obj = self.db_instance_details.click_add_subclient(DBInstances.Types.POSTGRES)
        add_subclient_obj.add_subclient(subclient_name='automation_sc',
                                        number_backup_streams=2,
                                        collect_object_list=True,
                                        plan=self.tcinputs['PlanName'],
                                        database_list=self.generated_database_list
                                        )
        self.log.info("Subclient added successfully")

    @test_step
    def backup(self):
        """ perform backup operation """
        self.log.info("#" * 10 + "  DumpBased Backup/Restore Operations  " + "#" * 10)
        self.log.info("Running DumpBased Backup.")
        job_id = self.db_group_page.backup(backup_type=RBackup.BackupType.FULL)
        self.dbhelper_object.wait_for_job_completion(job_id)
        self.log.info("Dumpbased backup compeleted successfully.")

    @test_step
    def restore(self):
        """ perform restore operation """
        ####################### Running restore ###################################
        self.log.info(
            "#" * 10 + "  Running Restore  " + "#" * 10)
        self.log.info("Database list to restore ---- %s", self.generated_database_list)
        self.navigator.navigate_to_db_instances()

        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
            self.tcinputs['InstanceName'], self.cloud_account)
        self.db_instance_details.access_restore()

        restore_panel = self.db_instance_details.restore_folders(
            database_type=DBInstances.Types.POSTGRES, items_to_restore=self.generated_database_list)
        job_id = restore_panel.in_place_restore(fsbased_restore=False)
        self.dbhelper_object.wait_for_job_completion(job_id)
        self.log.info("Restore completed successfully.")

    @test_step
    def delete_subclient(self):
        """ Method to delete subclient/db group"""
        self.navigator.navigate_to_db_instances()
        self.db_instance.select_instance(
            DBInstances.Types.POSTGRES,
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
        self.db_instance.select_instance(DBInstances.Types.POSTGRES,
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
            self.navigate_to_db_group()

            self.log.info("Get the database meta data before backup")
            self.backup()
            self.restore()
            self.log.info("Get the database meta data after restore")
            self.log.info("GCP PostgreSQL Backup and Restore Finished.")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
