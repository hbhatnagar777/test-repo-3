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

    run_backup()                --  method to run backup

    run_restore()               --  method to run restore and validate test data

    cleanup()                   --  method to clean up testcase created changes

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "59631":
                        {
                          "ClientName":"nginx1",
                          "InstanceName":"acct1",
                          "RmanImageCopyPath": "/image_copy",
                          "ConnectString":"sys/password@orcl",
                          "SnapEngine":"NetApp"     (optional, default: "NetApp")
                        }
            }

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import OracleInstanceDetails
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Components.dialog import RBackup
from Database.dbhelper import DbHelper
from Web.AdminConsole.Databases.Instances.restore_panels import OracleRestorePanel
from Web.Common.page_object import TestStep, handle_testcase_exception
from Database.OracleUtils.oraclehelper import OracleHelper


class TestCase(CVTestCase):
    """ Class for executing test for oracle"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Snap with image copy Test for Oracle iDA from Command Center"
        self.browser = None
        self.browse = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_59631'
        self.database_type = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'RmanImageCopyPath': None
        }
        self.oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.restore_panel = None
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
        self.browse = RBrowse(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.restore_panel = OracleRestorePanel(self.admin_console)
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = OracleInstanceDetails(self.admin_console)
        self.subclient_page = SubClient(self.admin_console)
        self.database_type = DBInstances.Types.ORACLE
        self.dbhelper_object = DbHelper(self.commcell)

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Deleting Automation Created tablespaces and tables")
        if self.oracle_helper_object:
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01", "CV_TABLE_INCR_01"], tablespace=self.tablespace_name)

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
    def create_helper_object(self):
        """Creates oracle helper object"""
        self.client = self.commcell.clients.get(self.tcinputs['ClientName'])
        self.instance = self.client.agents.get("oracle").instances.get(
            self.tcinputs["InstanceName"])
        connect_string = self.tcinputs["ConnectString"]
        user, temp = connect_string.split('/')[0], connect_string.split('/')[1]
        passwd, service_name = temp.split('@')[0], temp.split('@')[1]
        self.oracle_helper_object = OracleHelper(self.commcell, self.client, self.instance,
                                                 user, passwd)
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

    @test_step
    def run_backup(self, backup_type):
        """ method to run backup"""
        self.navigate_to_instance()
        self.db_instance_details.click_on_entity('default')
        self.admin_console.wait_for_completion(1000)
        if backup_type.value == "FULL":
            self.log.info("Full Backup")
        elif backup_type.value == "INCR":
            self.log.info("Incremental Backup")
        elif backup_type.value == "SYNTH":
            self.log.info("Synthetic full Backup")
        job_id = self.subclient_page.backup(backup_type=backup_type)
        if type(job_id) is type(list()):
            job_id = int(job_id[0])
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
    def run_restore(self, primary_copy=None):
        """ method to run restore"""
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])
        self.db_instance_details.access_restore()
        self.admin_console.wait_for_completion(1000)
        if primary_copy:
            self.browse.select_action_dropdown_value(value='Restore from Primary', index=1)
            self.admin_console.wait_for_completion(1000)
        self.browse.submit_for_restore()
        job_id = self.restore_panel.in_place_restore(recover_to="Most recent backup")
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed")

    def cleanup(self):
        """Cleans up testcase created instance"""
        if self.snapshot_enabled is not None and not self.snapshot_enabled:
            self.navigate_to_instance()
            self.db_instance_details.click_on_entity('default')
            self.subclient_page.disable_snapshot()

    @test_step
    def enable_snapshot(self):
        """Method enables image copy for the subclient"""
        self.navigate_to_instance()
        self.db_instance_details.click_on_entity('default')
        self.admin_console.wait_for_completion(20000)
        self.subclient_page.disable_snapshot()
        self.subclient_page.enable_snapshot(
            snap_engine=self.snap_engine,
            proxy_node=self.tcinputs["ClientName"],
            rman_image_copy=self.tcinputs["RmanImageCopyPath"]
        )

    @test_step
    def create_sample_data(self):
        """Method creates sample data"""
        self.log.info("Generating Sample Data for test")
        table_limit = 1
        num_of_files = 1
        row_limit = 10
        self.oracle_helper_object.create_sample_data(
            self.tablespace_name, table_limit, num_of_files)
        self.log.info("Test Data Generated successfully")

    @test_step
    def validate(self, rows):
        """Validates if the restore went through successfully"""
        self.log.info("Validating the data")
        num_of_files = 1
        self.oracle_helper_object.validation(self.tablespace_name, num_of_files,
                                             "CV_TABLE_01", rows)
        self.log.info("Validation Successful.")

    @test_step
    def drop_tablespace(self):
        """Drops the tablespace"""
        self.oracle_helper_object.oracle_data_cleanup(
            tables="CV_TABLE_01", tablespace=self.tablespace_name)

    @test_step
    def populate_table(self):
        """populates the table with 10 more rows"""
        self.oracle_helper_object.db_populate_table(
            "CV_TABLE_", "{0}_user".format(self.tablespace_name.lower()), 1)


    def run(self):
        """ Main function for test case execution """
        try:

            self.log.info(
                "#" * (10) + "  Oracle Backup/Restore Operations  " + "#" * (10))
            self.enable_snapshot()
            self.create_helper_object()
            self.create_sample_data()
            self.run_backup(RBackup.BackupType.FULL)
            self.run_restore()
            self.validate(rows=10)
            self.populate_table()
            self.run_backup(RBackup.BackupType.INCR)
            self.run_restore(primary_copy=True)
            self.validate(rows=20)
            self.populate_table()
            self.run_backup(RBackup.BackupType.INCR)
            self.run_backup(RBackup.BackupType.SYNTH)
            self.run_restore()
            self.validate(rows=30)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)