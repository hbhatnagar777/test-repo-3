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

    navigate_to_instance()      --  navigates to specified instance

    add_instance()              --  creates a new instance of specified type
                                    with specified name and details

    create_helper_object()      --  creates object of OracleHelper class

    generate_sample_data()      --  method to generate data

    run_backup()                --  method to run backup

    run_restore()               --  method to run restore and validate test data

    validate_restore()          --  validate restore

    run()                       --  run function of this test case


Input Example:

    "testCases":
        {
            "71024":
                {
                    "RacInstanceName": "name of the instance",
                    "RacClusterName": "name of the cluster",
                    "DestRacInstanceName": "name of the destination instance",
                    "DestRacClusterName": "name of the destination cluster",
                    "RedirectAllPath": path to redirect database
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
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.OracleUtils.oraclehelper import OracleHelper, OracleRACHelper
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """ Class for executing Cross Machine Restore for Oracle RAC to Oracle Single Node"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Oracle RAC to Single Node Restore on Command Center - Cross Machine Restore"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tablespace_name = 'CV_71024'
        self.database_type = None,
        self.tcinputs = {
            'RacClusterName': None,
            'RacInstanceName': None,
            'DestRacClusterName': None,
            'DestRacInstanceName': None,
            }
        self.oracle_helper_object = None
        self.database_instances = None
        self.db_instance_details = None
        self.subclient_page = None
        self.automation_instance = None
        self.dest_client = None
        self.dest_instance = None
        self.dest_oracle_helper_object = None
        self.dbhelper = None

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
        self.database_type = DBInstances.Types.ORACLE_RAC
        self.dbhelper = DbHelper(self.commcell)

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Deleting Automation Created tablespaces and tables")
        if self.oracle_helper_object:
            self.oracle_helper_object.oracle_data_cleanup(
                tables=["CV_TABLE_01", "CV_TABLE_INCR_01"], tablespace=self.tablespace_name)

    @test_step
    def navigate_to_instance(self):
        """Navigates to Instance page"""
        self.log.info("Navigating to DB Instances page")
        self.navigator.navigate_to_db_instances()

        self.log.info("Checking if instance exists")
        if self.database_instances.is_instance_exists(DBInstances.Types.ORACLE_RAC,
                                                      self.tcinputs["RacInstanceName"],
                                                      self.tcinputs["RacClusterName"]):
            self.log.info("Instance found")
            self.database_instances.select_instance(DBInstances.Types.ORACLE_RAC,
                                                    self.tcinputs["RacInstanceName"],
                                                    self.tcinputs["RacClusterName"])
        else:
            raise CVTestStepFailure("Instance not found")


    @test_step
    def create_helper_object(self):
        """Creates Oracle helper object"""
        self.client = self.commcell.clients.get(self.tcinputs["RacClusterName"])
        self.instance = self.client.agents.get("oracle rac").instances.get(
            self.tcinputs["RacInstanceName"])
        self.oracle_helper_object = OracleRACHelper(self.commcell, self.client, self.instance)
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

        self.dest_client = self.commcell.clients.get(self.tcinputs["DestRacClusterName"])
        self.dest_instance = self.dest_client.agents.get("oracle").instances.get(
            self.tcinputs["DestRacInstanceName"])
        self.dest_oracle_helper_object = OracleHelper(self.commcell, self.dest_client, self.dest_instance)
        self.dest_oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.dest_oracle_helper_object.check_instance_status()

    @test_step
    def generate_sample_data(self):
        """ Method to generate sample data"""
        table_limit = 1
        num_of_files = 1
        self.oracle_helper_object.create_sample_data(
            self.tablespace_name, table_limit, num_of_files)
        tablespaces = self.oracle_helper_object.get_tablespaces()
        self.oracle_helper_object.db_execute('alter system switch logfile')
        self.log.info("Test Data Generated successfully")
        return tablespaces

    @test_step
    def run_backup(self):
        """ Method to trigger backup"""
        self.log.info("Preparing for Full Backup.")
        self.db_instance_details.click_on_entity('default')
        job_id = self.subclient_page.backup(backup_type=RBackup.BackupType.FULL)
        self.dbhelper.wait_for_job_completion(job_id)
        self.log.info("Oracle RAC Full Backup is completed")
        self.oracle_helper_object.backup_validation(job_id, 'Online Full')
        return job_id

    @test_step
    def run_restore(self, job_id):
        """ method to run restore"""
        self.log.info("Preparing for Oracle RAC Restore.")
        self.admin_console.select_breadcrumb_link_using_text(self.tcinputs["RacInstanceName"])
        self.db_instance_details.access_restore()
        restore_panel = self.db_instance_details.restore_folders(
            database_type=self.database_type, all_files=True)
        job_id = restore_panel.out_of_place_restore(
            self.tcinputs["DestRacClusterName"], self.tcinputs["DestRacInstanceName"], redirect_all_path=self.tcinputs.get("RedirectAllPath", None), recover_to="most recent backup")
        self.dbhelper.wait_for_job_completion(job_id)
        self.log.info("Oracle RAC Restore completed")
        return job_id

    @test_step
    def validate_restore(self, tablespaces):
        """ method to validate restore"""
        num_of_files = 1
        row_limit = 10
        self.log.info("Validating Backed up content")
        self.dest_oracle_helper_object.validation(self.tablespace_name, num_of_files,
                                             "CV_TABLE_01", row_limit)
        dest_tablespaces = self.dest_oracle_helper_object.get_tablespaces()
        if dest_tablespaces == tablespaces:
            self.log.info("Validation Successful.")
        else:
            raise CVTestStepFailure("Tablespaces in destination do not match")


    def run(self):
        """ Main function for test case execution """
        try:

            self.navigate_to_instance()
            self.create_helper_object()
            tablespaces = self.generate_sample_data()

            job_id = self.run_backup()

            restore_job_id = self.run_restore(job_id)

            self.validate_restore(restore_job_id, tablespaces)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
