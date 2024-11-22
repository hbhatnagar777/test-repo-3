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

    create_helper_object()      --  creates object of SAPOraclehelper class

    create_test_data()          --  creates a table in the database and populates it with sample data

    enable_snap_operations()    --  method to enable snap operations

    run_backup()                --  method to Runs backup job

    run_backup_copy()           --  method to run backup copy operation

    run_restore()               --  method to run restore

    validate_restore()          --  method to validate restore

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "70852":
                        {
                          "ClientName":"client",
                          "InstanceName":"instance",
                          "Plan":"plan",
                          "SnapEngine":"NetApp"
                        }
            }

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import SAPOracleInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.SAPOracleUtils.saporaclehelper import SAPOracleHelper
from Database.dbhelper import DbHelper
from datetime import datetime
from pytz import timezone


class TestCase(CVTestCase):
    """ Class for executing SNAP Acct1 TestCase SAP for Oracle """
    test_step = TestStep()

    def __init__(self):
        """
        Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "SAP Oracle SNAP Acct1 from Command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_71075_TSP'
        self.table_name = "CV_71075_TABLE"
        self.database_type = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'Plan': None,
            "SnapEngine": None}
        self.sap_oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.db_file=None
        self.snap_engine = self.tcinputs.get("SnapEngine") or "NetApp"
        self.snapshot_enabled = None
        self.dbhelper_object = None
        self.last_job_id = None


    def setup(self):
        """
        Method to setup test variables
        """
        self.log.info("Started executing %s testcase", self.id)
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = SAPOracleInstanceDetails(self.admin_console)
        self.subclient_page = SubClient(self.admin_console)
        self.database_type = DBInstances.Types.SAP_ORACLE
        self.dbhelper_object = DbHelper(self.commcell)
        
    def tear_down(self):
        """
        Tear down method for testcase
        """
        self.log.info("Deleting Automation Created tablespace and tables")
        if self.sap_oracle_helper_object:
            status = self.sap_oracle_helper_object.drop_tablespace(self.tablespace_name)
            if status == 0:
                self.log.info("tablespace spaces are cleaned up sucessgully")
            else:
                self.log.info("there is some issue with tablespace cleanup created by \
                automation.please cleanup manually")
            

    @test_step
    def wait_for_job_completion(self, job_id):
        """
        Waits for completion of job and check job status
        Args:
            job_id   (int): Job_id of the job we are waiting for completion of.
        """
        job_obj = self.commcell.job_controller.get(job_id)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (job_id, job_obj.delay_reason)
            )

    @test_step
    def navigate_to_instance(self):
        """
        Navigates to Instance page
        """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.database_instances.select_instance(DBInstances.Types.SAP_ORACLE,
                                                self.tcinputs["InstanceName"],
                                                self.tcinputs["ClientName"])

    @test_step
    def create_helper_object(self):
        """
        Creates sap oracle helper object
        """
        self.instance = self.client.agents.get("sap for oracle").instances.get(
            self.tcinputs["InstanceName"])
        self.sap_oracle_helper_object = SAPOracleHelper(self.commcell, self.client, self.instance)
        self.sap_oracle_helper_object.db_connect(SAPOracleHelper.CONN_SYSDBA)
        status = self.sap_oracle_helper_object.get_database_state()
        if status != "OPEN":
                raise CVTestStepFailure(
                "database is not in open state" )
        else:
                self.log.info("database is in open state")

    @TestStep()
    def create_test_data(self):
        """
        Create a table in the database and populate table with records.
        """
        self.log.info("getting data file path")
        self.data_file = self.sap_oracle_helper_object.get_datafile(self.tablespace_name)
        self.log.info("Datafile location is: {0} delay_reason dbfile ".\
                         format(str(self.data_file)))
        self.log.info("Creating test tables in the database")
        retcode = self.sap_oracle_helper_object.create_test_tables(self.data_file,\
                                                               self.tablespace_name, self.table_name, True)
        if retcode == 0:
               self.log.info("test data creation is sucessful")

    @test_step
    def enable_snap_operations(self):
        """ Method to enable snap backup operation
        
        """
        self.snapshot_enabled = self.subclient_page.is_snapshot_enabled()
        if self.snapshot_enabled:
            self.log.info("Snapshot is already enabled for the Subclient, disabling it")
            self.subclient_page.disable_snapshot()
        self.subclient_page.enable_snapshot(snap_engine=self.snap_engine)
        self.log.info("Snap enabled for the Subclient")

            
    @test_step
    def run_backup(self, backup_type=RBackup.BackupType.FULL):
        """
        Runs a backup job on the subclient
            Args:
             first_backup_job  (bool):  True for the first backup job run
              default: False
             backup_type   (RBackup.BackupType):  Type of backup to perform
        """
        job_id = self.subclient_page.backup(backup_type=backup_type)
        self.last_job_id = job_id
        self.wait_for_job_completion(job_id)
        self.log.info("Backup is completed")
    
    @test_step
    def run_backup_copy(self):
        """ Method to run backup copy operation """
        self.log.info("#### Running Backup Copy ####")
        self.dbhelper_object.run_backup_copy(self.tcinputs["Plan"])
        job_id = self.dbhelper_object.get_backup_copy_job(self.last_job_id).job_id
        self.log.info("Backup copy is completed")

    @test_step
    def run_restore(self, from_backup_copy=False):
        """
        Method to run restore
        """
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])
        self.db_instance_details.access_restore()
        
        if not from_backup_copy:
            self.log.info("Running restore from snap backup")
            restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True, copy= 'snap copy')
        else:
            self.log.info("Running restore from backup copy")
            restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True, copy='Primary')
        job_id = restore_panel.in_place_restore(recover_to="most recent state")
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed")

    @test_step
    def validate_restore(self):
        """
        Method to verify restores
        """
        self.log.info("Validating restore")
        status = self.sap_oracle_helper_object.test_tables_validation(self.tablespace_name, self.table_name)
        if status == 0:
            self.log.info("tablespace/tables are restored sucessfully")
        else:
            raise CVTestStepFailure(
                "tablespace/tables are not restored sucessfully")


    def run(self): 
        """
        Main function for test case execution
        """
        try:
            self.create_helper_object()

            self.create_test_data()

            self.navigate_to_instance()

            self.db_instance_details.click_on_entity('snap')

            self.enable_snap_operations()

            self.run_backup()

            self.run_backup_copy()

            self.sap_oracle_helper_object.db_shutdown()

            self.sap_oracle_helper_object.rename_datafile(self.data_file)

            self.run_restore()
            
            self.validate_restore()

            self.sap_oracle_helper_object.db_shutdown()

            self.sap_oracle_helper_object.rename_datafile(self.data_file)

            self.run_restore(from_backup_copy=True)

            self.validate_restore()
            
        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
