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

    tear_down()                 --  tear down method for testcase, delete automation created test data

    create_helper_object()      -- Create Oracle helper object

    wait_for_job_completion()   --  Waits for completion of job and gets the
    object once job completes

    navigate_to_backupset()     --  navigates to specified backupset page of the instance

    run_backup()                --  Run backup operation

    run_restore                 --  Run restore operation

    backup_operations()         --  Running backup and create data for each backup

    restore_operations()        -- Restore operations for DB and validate after restore

    run()                       --  run function of this test case

Input Example:

    "testCases":
            {
                "70505":
                        {
                          "ClientName":"ABC",
                          "AgentName":"Oracle",
                          "InstanceName":"ABC",
                          "Hostname":"ABC",
                          "DestinationClient":"ABC",
                          "DestinationInstance":"ABC",
                          "DestinationHostname":"ABC",
                          "StagingPath":"E:\\Staging",
                          "RedirectPath":"E:\\Redirect",
                        }
            }

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Databases.backupset import Backupset
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Databases.Instances.restore_panels import OracleRestorePanel
from Database.OracleUtils.oraclehelper import OracleHelper


class TestCase(CVTestCase):
    """ Class for executing AWS RDS RMAN Export Based Backups """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "AWS RDS RMAN Export Based Backups"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instances = None
        self.db_instance_details = None
        self.backupset_page = None
        self.restore_panel = None
        self.subclient_page = None
        self.tablespace_name = 'CV_70505'
        self.oracle_helper = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "InstanceName": None,
            "Hostname": None,
            "DestinationClient": None,
            "DestinationInstance": None,
            "DestinationHostname": None,
            "StagingPath": None,
            "RedirectPath": None,
        }

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.log.info("**** Initialize browser objects ****")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.backupset_page = Backupset(self.admin_console)
        self.restore_panel = OracleRestorePanel(self.admin_console)
        self.subclient_page = SubClient(self.admin_console)

        self.create_helper_object()
        self.log.info("#### Oracle Helper Object created ####")

    @test_step
    def create_helper_object(self):
        """  Creates Oracle helper object """
        self.instance = self.client.agents.get("oracle").instances.get(
            self.tcinputs["InstanceName"])
        self.oracle_helper = OracleHelper(self.commcell, self.tcinputs['Hostname'], self.instance)
        self.oracle_helper.db_connect(mode=OracleHelper.CONN_DB_USER,ora_instance=self.tcinputs["InstanceName"][:self.tcinputs["InstanceName"].find("[")],
                                      host_name=self.tcinputs["Hostname"], rds=True)
        self.oracle_helper.check_instance_status()

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Deleting Automation Created tablespaces and tables")
        user = "{0}_user".format(self.tablespace_name.lower())
        if self.oracle_helper:
            self.oracle_helper.oracle_data_cleanup(
                tables=["CV_TABLE_01"], tablespace=self.tablespace_name, user=user)

    @test_step
    def wait_for_job_completion(self, jobid):
        """ Waits for completion of job and gets the object once job completes
            Args:
                jobid   (int) : Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                f"Failed to run job:{jobid} with error: {job_obj.delay_reason}"
            )
        self.log.info("Successfully finished %s job", jobid)

    @test_step
    def navigate_to_backupset(self):
        """ navigates to specified backupset page of the instance"""
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.ORACLE,
            self.tcinputs['InstanceName'], self.tcinputs['ClientName'])

    @test_step
    def run_backup(self, backup_type):
        """ Method to run DB backup
            Args:
                backup_type (backup_type): FULL/INCR

        """
        self.log.info(
            "#### Running %s backup for database %s ####", format(backup_type.name))
        job_id = self.subclient_page.backup(backup_type)
        self.wait_for_job_completion(job_id)
        self.log.info(
            "#### %s Backup is completed for database %s ####", format(backup_type.name))
        self.oracle_helper.backup_validation(job_id, 'Online Full' if backup_type == RBackup.BackupType.FULL else 'Incremental')

    @test_step
    def run_restore(self):
        """ method to run DB restore """
        self.backupset_page.access_restore()
        self.log.info("#### Running %s most recent Out of place Restore ####")
        self.admin_console.click_by_xpath("//span[text()='Name']//ancestor::th/preceding-sibling::th/input")
        self.backupset_page.access_restore()
        job_id = self.restore_panel.out_of_place_restore(destination_client=self.tcinputs['DestinationClient'],
                                                         destination_instance=self.tcinputs['DestinationInstance'],
                                                         recover_to="most recent backup",
                                                         staging_path=self.tcinputs['StagingPath'],
                                                         redirect_path=self.tcinputs['RedirectPath']
                                                         )
        self.wait_for_job_completion(job_id)
        self.log.info("#### Out of place restore is completed ####")

    @test_step
    def backup_operations(self):
        """
            backup operations for DB and metadata creation
            returns:
                dictionary (dict) : collected metadata after backup
        """
        self.navigate_to_backupset()
        self.backupset_page.access_subclient('default')
        table_limit = 1
        self.num_of_files = 1
        self.row_limit = 10
        self.oracle_helper.create_sample_data(
            self.tablespace_name, table_limit, self.num_of_files)
        self.log.info("Test Data Generated successfully")

        self.run_backup(RBackup.BackupType.FULL)

    @test_step
    def restore_operations(self):
        """
        Restore operations for DB and validate metadata after restore
        """

        self.navigate_to_backupset()
        self.run_restore()

        self.log.info("Validating Backed up content")
        self.dest_client = self.commcell.clients.get(self.tcinputs['DestinationClient'])
        dest_agent = self.dest_client.agents.get(self.tcinputs['AgentName'])
        self.dest_instance = dest_agent.instances.get(self.tcinputs['DestinationInstance'])
        self.dest_oracle_helper = OracleHelper(self.commcell, self.dest_client, self.dest_instance)
        self.dest_oracle_helper.db_connect(ora_instance=self.tcinputs["DestinationInstance"],host_name=self.tcinputs["DestinationHostname"])
        self.dest_oracle_helper.validation(self.tablespace_name, self.num_of_files,
                                             "CV_TABLE_01", self.row_limit, host_name=self.tcinputs["DestinationHostname"])

        self.log.info("Validation Successfull.")

    def run(self):
        """ Main function for test case execution """
        try:
            self.backup_operations()

            self.log.info("#### Database %s backup operations completed and metadata collected ####",
                          self.tcinputs['InstanceName'])
            self.restore_operations()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
