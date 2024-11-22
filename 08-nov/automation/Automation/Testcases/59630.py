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

    enable_snapshot()           --  Enables the snap on default subclient

    check_if_instance_exists()  --  Verifies if the source instance exists

    create_test_data()          --  Creates a tablespace and table on it

    drop_tablespace()           --  Drops a tablespace on the db

    populate_table()            -- Populates table with 10 rows

    is_restore_from_snap()      -- Verifies if the restore is done from snap copy

    verify_restore_is_from_revert() --  Verifies if the restore is done form hardware revert

    validate_data()              --  Validates the data for the restore

    run_backup()                --  method to run backup

    run_restore()               --  method to run restore and validate test data

    cleanup()                   --  method to clean up testcase created changes

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "59630":
                        {
                          "ClientName":"nginx1",
                          "InstanceName":"acct1",
                          "ConnectString":"sys/password@orcl",
                          "SnapEngine":"NetApp"     (optional, default: "NetApp")
                        }
            }

"""

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
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """ Class for executing Basic acceptance Test for oracle Snap"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Snap ACCT1-Acceptance Test for Oracle iDA from Command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_59630'
        self.database_type = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'ConnectString': None
        }
        self.oracle_helper_object = None
        self.destination_oracle_helper_obj = None
        self.destination_oracle_helper_obj2 = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.snap_engine = self.tcinputs.get("SnapEngine") or "NetApp"
        self.snapshot_enabled = None
        self.dbhelper_object = None

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
        self.oracle_helper_object = self.create_helper_object(self.tcinputs['ClientName'],
                                                              self.tcinputs['InstanceName'],
                                                              self.tcinputs['ConnectString'])
        self.destination_oracle_helper_obj = self.create_helper_object(self.tcinputs['DestinationClient'],
                                                                       self.tcinputs['DestinationInstance'],
                                                                       self.tcinputs['DestinationConnectString'])
        self.destination_oracle_helper_obj2 = self.create_helper_object(self.tcinputs['DestinationClient'],
                                                                        self.tcinputs['DestinationInstance2'],
                                                                        self.tcinputs['DestinationConnectString2'])

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Deleting Automation Created tablespaces and tables")
        if self.oracle_helper_object:
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01"], tablespace=self.tablespace_name)

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
    def create_helper_object(self, client_name, instance_name, connect_string):
        """Creates oracle helper object"""
        self.client = self.commcell.clients.get(client_name)
        self.instance = self.client.agents.get("oracle").instances.get(instance_name)
        user, temp = connect_string.split('/')[0], connect_string.split('/')[1]
        passwd, service_name = temp.split('@')[0], temp.split('@')[1]
        oracle_helper_obj = OracleHelper(self.commcell, self.client, self.instance,
                                         user, passwd)
        oracle_helper_obj.db_connect(OracleHelper.CONN_SYSDBA)
        oracle_helper_obj.check_instance_status()
        return oracle_helper_obj

    @test_step
    def run_backup(self, backup_type):
        """ method to run backup"""
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])
        self.db_instance_details.click_on_entity('default')
        if backup_type.value == "FULL":
            self.log.info("Full Backup")
        else:
            self.log.info("Incremental Backup")
        job_id = self.subclient_page.backup(backup_type=backup_type)
        self.log.info("Backup job started")
        self.wait_for_job_completion(job_id)
        self.log.info("Backup job completed")
        if "native" in self.snap_engine.lower():
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
    def enable_snapshot(self):
        """Enables snap on the subclient"""
        self.navigate_to_instance()
        self.db_instance_details.click_on_entity('default')
        self.admin_console.wait_for_completion(20000)
        self.snapshot_enabled = self.subclient_page.is_snapshot_enabled()
        self.subclient_page.disable_snapshot()
        self.subclient_page.enable_snapshot(
            snap_engine=self.snap_engine,
            backup_copy_interface="RMAN")

    @test_step
    def check_if_instance_exists(self):
        """Method checks if the instance exists"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.log.info("Checking if instance exists")
        if self.database_instances.is_instance_exists(DBInstances.Types.ORACLE,
                                                      self.tcinputs["InstanceName"],
                                                      self.tcinputs["ClientName"]):
            self.log.info("Instance found")
        else:
            raise Exception('Instance not found')

    @test_step
    def run_restore(self, inplace=True, revert=False):
        """ method to run restore"""
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True)
        job_id = None
        if inplace:
            job_id = restore_panel.in_place_restore(recover_to="Most recent backup", revert=revert)
        else:
            job_id = restore_panel.out_of_place_restore(self.destination_client, self.destination_instance,
                                                        recover_to="Most recent backup")
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed")
        return job_id

    def create_test_data(self):
        """Method creates data for the backup"""
        df_location = self.oracle_helper_object.db_fetch_dbf_location()
        self.oracle_helper_object.db_create_tablespace(tablespace_name=self.tablespace_name,
                                                       location=df_location, num_files=1)
        self.oracle_helper_object.db_create_table(tablespace_name=self.tablespace_name,
                                                  table_prefix="CV_TABLE_", user="SYS",
                                                  number=1)
        self.oracle_helper_object.db_execute('alter system switch logfile')

    def drop_tablespace(self):
        """Method drops the tablespace before the restore"""
        self.log.info("Cleaning up tablespace and data before restore")
        self.oracle_helper_object.oracle_data_cleanup(
            tables=["CV_TABLE_01"], tablespace=self.tablespace_name)

    def cleanup(self):
        """Cleans up testcase created instance"""
        if self.snapshot_enabled is not None and not self.snapshot_enabled:
            self.navigate_to_instance()
            self.db_instance_details.click_on_entity('default')
            self.subclient_page.disable_snapshot()

    def populate_table(self):
        """Populates the automation created table with 10 rows"""
        self.log.info("Populating the table with 10 rows")
        self.oracle_helper_object.db_populate_table(tblpref="CV_TABLE_", user="SYS")

    def is_restore_from_snap(self, job_id):
        """Method validates if the restore is from snap"""
        job = self.commcell.job_controller.get(job_id)
        self.log.info("Validating if the data is restored from snap copy or not")
        if not self.dbhelper_object.check_if_restore_from_snap_copy(job):
            raise Exception(
                "Data is not restored from snap copy."
            )
        self.log.info("Restore is done from snap.")

    def verify_restore_is_from_revert(self, job_id):
        """Method verifies if restore performed revert"""
        job = self.commcell.job_controller.get(job_id)
        self.log.info("Validating if the data is restored from hardware revert or not")
        if not self.dbhelper_object.check_if_restore_from_snap_copy(job):
            raise Exception(
                "Data is not restored from hardware revert."
            )
        self.log.info("Restore is done from hardware revert")

    @test_step
    def validate_data(self, oracle_helper_obj, rows):
        """Method validates the restore's copy and the restored data
        Args:
             oracle_helper_obj -- An Instance of the Oracle helper class
             rows(int)         -- Total of number of rows populated for the backup
        """

        self.log.info("Validating data")
        tablerecords = oracle_helper_obj.db_table_validate(user="SYS", tablename="CV_TABLE_01")
        if tablerecords != rows:
            raise CVTestStepFailure("Validation failed")
        self.log.info("Validation Successful")

    def run(self):
        """ Main function for test case execution """
        try:

            self.log.info(
                "#" * (10) + "  Oracle Backup/Restore Operations  " + "#" * (10))
            self.check_if_instance_exists()
            self.enable_snapshot()
            self.create_test_data()
            self.run_backup(RBackup.BackupType.FULL)
            self.drop_tablespace()
            job_id = self.run_restore(inplace=True)
            self.is_restore_from_snap(job_id=job_id)
            self.validate_data(self.oracle_helper_object, rows=10)
            # cross machine same db name
            self.populate_table()
            self.run_backup(RBackup.BackupType.FULL)
            job_id = self.run_restore(inplace=False)
            self.is_restore_from_snap(job_id=job_id)
            self.validate_data(self.destination_oracle_helper_obj,
                               rows=20)
            # perform crossmachine same db name
            self.populate_table()
            self.run_backup(RBackup.BackupType.FULL)
            job_id = self.run_restore(inplace=False)
            self.is_restore_from_snap(job_id=job_id)
            self.validate_data(self.destination_oracle_helper_obj2,
                               rows=30)
            # perform inplace revert
            self.populate_table()
            self.run_backup(RBackup.BackupType.FULL)
            self.drop_tablespace()
            job_id = self.run_restore(inplace=True, revert=True)
            self.verify_restore_is_from_revert(job_id=job_id)
            self.validate_data(self.oracle_helper_object, rows=40)
        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
