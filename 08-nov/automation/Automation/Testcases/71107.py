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

    data_validation()           --  Validates the testdata restore

    create_test_data()          --  creates a table in the database and populates it with sample data

    create_new_subclient()      --  creates new subclient with util_file device

    delete_subclient()          --  deletes existing subclient if exists

    run_backup()                --  method to Runs backup job

    run_restore()               --  method to run restore

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "71107":
                        {
                          "ClientName":"client",
                          "InstanceName":"instance",
                          "Plan":"planname"
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
from datetime import datetime
from pytz import timezone


class TestCase(CVTestCase):
    """ Class for executing Disable Switch current log TestCase using \
    util_file device for SAP for Oracle """
    test_step = TestStep()

    def __init__(self):
        """
        Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "SAP Oracle Disable Switch current log test from Command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_71107_TSP'
        self.table_name = "CV_71107_TABLE"
        self.database_type = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'Plan': None}
        self.sap_oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.db_file = None
        self.backup_job_id = None


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
                "database is not in open state")
        else:
            self.log.info("database is in open state")

    @TestStep()
    def create_test_data(self):
        """
        Create a table in the database and populate table with records.
        """
        self.log.info("getting data file path")
        self.data_file = self.sap_oracle_helper_object.get_datafile(self.tablespace_name)
        self.log.info("Datafile location is: {0} delay_reason dbfile ". \
                      format(str(self.data_file)))
        self.log.info("Creating test tables in the database")
        retcode = self.sap_oracle_helper_object.create_test_tables(self.data_file, \
                                                                   self.tablespace_name, self.table_name, True)
        if retcode == 0:
            self.log.info("test data creation is sucessful")

    @TestStep()
    def data_validation(self):
        """
        validates  a tablespace/table in the database after restore.
        """

        self.log.info("validating full tablespace/table data")
        status = self.sap_oracle_helper_object.test_tables_validation(self.tablespace_name, self.table_name)
        if status == 0:
            self.log.info("tablespace/tables are restored sucessfully")
        else:
            raise CVTestStepFailure(
                "tablespace/tables are restored sucessfully")

        status = self.sap_oracle_helper_object.fetch_brtools_log_validation(self.backup_job_id, \
                                                                            "backup", \
                                                                            "Will not switch the logfile as this option has been disabled.")
        if status == 0:
            self.log.info("Brtools validation is correct for disable switch current log")
        else:
            raise CVTestStepFailure(
                "Brtools validation is not correct for disable switch current log")

    @test_step
    def create_new_subclient(self):
        """ Adding new subclient """
        self.db_instance_details.access_subclients_tab()
        if self.admin_console.check_if_entity_exists('link', self.tablespace_name):
            self.db_instance_details.click_on_entity(self.tablespace_name)
            self.subclient_page.delete_subclient()
        self.add_subclient = self.db_instance_details.click_add_subclient(DBInstances.Types.SAP_ORACLE)
        self.add_subclient.add_subclient(
            subclient_name=self.tablespace_name, plan=self.tcinputs["Plan"],
            disable_switch_log="True")
        self.log.info("Waiting for subclient creation completion")
        self.automation_subclient = self.tablespace_name

    @test_step
    def delete_subclient(self):
        """ Deletes subclient if exists """
        self.db_instance_details.access_subclients_tab()
        if self.automation_subclient:
            self.db_instance_details.click_on_entity(self.automation_subclient)
            self.subclient_page.delete_subclient()
            self.log.info("Waiting for subclient deletion completion")
        else:
            self.log.info("subclient doesn't exist..no need to delete")

    @test_step
    def run_backup(self, first_backup_job=False, backup_type=RBackup.BackupType.FULL):
        """
        Runs a backup job on the subclient
            Args:
             first_backup_job  (bool):  True for the first backup job run
              default: False
             backup_type   (RBackup.BackupType):  Type of backup to perform
        """
        if first_backup_job:
            job_id = self.subclient_page.backup(backup_type=backup_type)
        else:
            job_id = self.subclient_page.backup(backup_type=backup_type)
        self.backup_job_id = job_id
        self.wait_for_job_completion(self.backup_job_id)
        if first_backup_job:
            self.time = datetime.now(timezone('Asia/Kolkata')).strftime('%m/%d/%Y %H:%M:%S')
        self.log.info("Backup is completed")

    @test_step
    def run_restore(self):
        """
        Method to run restore
        """
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs['InstanceName'])
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True)
        job_id = restore_panel.in_place_restore(recover_to="most recent state")
        self.wait_for_job_completion(job_id)
        self.log.info("Restore completed")

    def run(self):
        """
        Main function for test case execution
        """
        try:
            self.create_helper_object()

            self.create_test_data()

            self.navigate_to_instance()

            self.create_new_subclient()

            self.run_backup(first_backup_job=True)

            self.sap_oracle_helper_object.db_shutdown()

            self.sap_oracle_helper_object.rename_datafile(self.data_file)

            self.run_restore()

            self.data_validation()

            self.navigate_to_instance()

            self.delete_subclient()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)