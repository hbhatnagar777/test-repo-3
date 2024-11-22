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

    wait_for_job_completion()   --  waits for completion of job and gets the
    object once job completes

    create_helper_object()      --  creates object of OracleHelper class

    create_test_data()          --  adds 10 rows to PDB

    validate_data()             --  checks if the rows added in PDB before are present in clone

    run_backup()                --  method to run backup

    run_clone()               --  method to clone pdb

    cleanup()                   --  method to clean up testcase created changes

    run()                       --  run function of this test case

Note:
    Connect string shouldn't be "/" for target unless it has RMAN catalog

Input Example:

    "testCases":
            {
                "70196":
                        {
                              "ClientName":"kpn-oracle",
                              "ServicePack": "SP36",
                              "InstanceName":"orclcdb",
                              "SnapEngine":"NetApp",   optional, if not given will be streaming backup
                              "ConnectString":"sys/password@orcl_cdb",
                              "DestinationConnectString": "sys/password@vienna",
                              "DestinationServer": "kpn-oracle",
                              "DestinationInstance": "vienna",
                              "PDBName": "PDB1",
                              "StagingPath": "/staging_area/",
                              "RedirectPath": "/redirect_pdb/"
                        }
            }

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Components.dialog import RBackup
from Database.dbhelper import DbHelper
from Web.Common.page_object import TestStep, handle_testcase_exception
from Database.OracleUtils.oraclehelper import OracleHelper

from Automation.Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """ Class for executing basic acceptance Test for Oracle PDB clone"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "PDB Clone Test for Oracle iDA from Command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_70196'
        self.clone_pdb_name = ""
        self.database_type = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'ConnectString': None,
            "DestinationConnectString": None,
            "DestinationServer": None,
            "DestinationInstance": None,
            "PDBName": None,
            "StagingPath": None,
            "RedirectPath": None
        }
        self.oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.snap_engine = None
        self.snapshot_enabled = None
        self.dbhelper_object = None
        self.client = None
        self.instance = None

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
        self.database_type = DBInstances.Types.ORACLE
        self.dbhelper_object = DbHelper(self.commcell)
        self.clone_pdb_name = self.tcinputs['PDBName']+"CLONE"+self.tablespace_name
        self.snap_engine = self.tcinputs.get("SnapEngine") or None

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Deleting Automation Created tablespaces and tables")
        if self.oracle_helper_object:
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01"], tablespace=self.tablespace_name)
            self.oracle_helper_object.db_drop_pdb(self.clone_pdb_name)

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise Exception(
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
    def create_helper_object(self, connect_string, client, instance):
        """Creates oracle helper object"""

        self.client = client
        self.instance = instance

        user, temp = connect_string.split('/')[0], connect_string.split('/')[1]
        passwd, service_name = temp.split('@')[0], temp.split('@')[1]
        self.oracle_helper_object = OracleHelper(self.commcell, self.client, self.instance,
                                                 user, passwd)
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

    @test_step
    def run_backup(self, backup_type):
        """ method to run backup"""

        job_id = self.subclient_page.backup(backup_type=backup_type)
        self.log.info("Backup job started")
        self.wait_for_job_completion(job_id)
        self.log.info("Backup job completed")
        if self.snap_engine and "native" in self.snap_engine.lower():
            self.log.info(
                ("Native Snap engine is being run. Backup "
                 "copy job will run inline to snap backup"))
            self.log.info("Getting the backup job ID of backup copy job")
            backup_copy_job = self.dbhelper_object.get_backup_copy_job(job_id)
            self.log.info("Job ID of backup copy Job is: %s", backup_copy_job.job_id)
        else:
            self.subclient = self.instance.subclients.get("default")
            self.log.info(
                "Running backup copy job for storage policy: %s",
                self.subclient.storage_policy)
            self.dbhelper_object.run_backup_copy(self.subclient.storage_policy)
        return job_id

    @test_step
    def run_clone(self):
        """Method to clone pdb"""
        self.log.info("Preparing for Cloning.")
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])
        self.db_instance_details.access_restore()

        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, items_to_restore=[self.tcinputs['PDBName']], all_files=False)
        job_id = restore_panel.out_of_place_restore(self.tcinputs['DestinationServer'],
                                                    self.tcinputs['DestinationInstance'],
                                                    redirect_all_pdb_path=self.tcinputs['RedirectPath'],
                                                    pdb_clone=True,
                                                    staging_path=self.tcinputs['StagingPath'],
                                                    redirect_all_pdb_name=[self.clone_pdb_name],
                                                    recover_to="Most recent backup")
        self.wait_for_job_completion(job_id)
        self.log.info("Clone completed.")

    @test_step
    def create_test_data(self):
        """Creates the test data"""

        self.log.info("Generating Sample Data for test")
        self.oracle_helper_object.db_execute('alter system switch logfile')

        df_location = self.oracle_helper_object.db_fetch_dbf_location()
        self.oracle_helper_object.db_connect_to_pdb(pdb_name=self.tcinputs["PDBName"])
        self.oracle_helper_object.db_create_tablespace(tablespace_name=self.tablespace_name,
                                                       location=df_location, num_files=1)
        self.oracle_helper_object.db_create_table(tablespace_name=self.tablespace_name,
                                                  table_prefix="CV_TABLE_", user="SYS",
                                                  number=1)
        self.log.info("Test Data Generated successfully")

    @test_step
    def validate_data(self, row_limit):
        """Validates the data for the restore

           Args:
               row_limit   (int)   : Number of rows
        """
        self.log.info("Validating data")
        self.oracle_helper_object.db_connect_to_pdb(pdb_name=self.clone_pdb_name)
        table_records = self.oracle_helper_object.db_table_validate(user="SYS", tablename="CV_TABLE_01")

        if table_records != row_limit:
            raise CVTestStepFailure("Validation failed")

        self.log.info("Validation Successful")

    @test_step
    def handle_snapshot_toggle(self):
        """
            Enables snapshot if Snap engine exists in input, else disables it
        """
        self.snapshot_enabled = self.subclient_page.is_snapshot_enabled()
        self.subclient_page.disable_snapshot()

        if self.snap_engine:
            self.subclient_page.enable_snapshot(self.snap_engine)

    @test_step
    def check_if_instance_exists(self):
        """
            Checks if instance exists
        """
        self.log.info("Checking if instance exists")

        if self.database_instances.is_instance_exists(DBInstances.Types.ORACLE,
                                                      self.tcinputs["InstanceName"],
                                                      self.tcinputs["ClientName"]):
            self.log.info("Instance found")
        else:
            raise Exception('Instance not found')

    @test_step
    def clean_helper_tablespace(self):
        """
            Clears data in oracle helper object
        """
        self.log.info("Cleaning up tablespace and data before clone")
        self.oracle_helper_object.oracle_data_cleanup(
            tables=["CV_TABLE_01"], tablespace=self.tablespace_name)

    @test_step
    def cleanup(self):
        """Disables snapshot if it was not enabled before AND we ran snap backup"""
        try:
            if self.snap_engine and self.snapshot_enabled is not None and not self.snapshot_enabled:
                self.navigate_to_instance()
                self.db_instance_details.click_on_entity('default')
                self.subclient_page.disable_snapshot()

        except Exception as e:
            self.log.info(e)
            self.log.info("Testcase cleanup failed. Passing testcase.")
            self.status = constants.PASSED

    @test_step
    def navigate_to_db_instances(self):
        """
            Goes to db instances page
        """
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()

    @test_step
    def click_on_default(self):
        """
            Clicks on default subclient hyperlink
        """
        self.db_instance_details.click_on_entity('default')
        self.admin_console.wait_for_completion(2000)

    def run(self):
        """ Main function for test case execution """
        try:

            self.log.info(
                "#" * (10) + "  Oracle Backup/Restore Operations  " + "#" * (10))

            self.create_helper_object(self.tcinputs["ConnectString"],
                                      self.commcell.clients.get(self.tcinputs['ClientName']),
                                      self.client.agents.get("oracle").instances.get(
                                          self.tcinputs["InstanceName"]
                                        )
                                      )

            self.navigate_to_db_instances()

            self.check_if_instance_exists()

            self.navigate_to_instance()

            self.click_on_default()

            self.create_test_data()

            self.handle_snapshot_toggle()

            self.run_backup(RBackup.BackupType.FULL)

            self.clean_helper_tablespace()

            self.run_clone()

            self.create_helper_object(self.tcinputs["DestinationConnectString"],
                                      self.commcell.clients.get(self.tcinputs['DestinationServer']),
                                      self.client.agents.get("oracle").instances.get(
                                          self.tcinputs["DestinationInstance"]
                                        )
                                      )
            self.validate_data(10)

            self.cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
