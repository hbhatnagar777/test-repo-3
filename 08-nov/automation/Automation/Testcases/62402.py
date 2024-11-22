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

    run()                       --  run method for test case

    tear_down()                 --  tear down method for test case

    fill_sample_data()          --  Creates a table in the database and populates it with sample data

    create_subclient()          --  Creates a subclient for a Oracle instance with table-level Metadata enabled.

    wait_for_job_completion()   --  Waits for the job to complete

    run_subclient_backup()      --  Runs backup job on subclient

    drop_usertable()            --  Drops user table from database

    run_table_level_restore()   --  Runs a table-level restore job

    validate_restore()          --  Validates whether the restore job was successful

    add_tablerows()             --  Adds rows to table in the database

Input Example:

    "testCases": {
        "62402": {
            "UserName": "SYS",
            "Password": "",
            "ClientName": "",
            "InstanceName": "",
            "AgentName": "Oracle",
            "NewSubclient": "",
            "Plan": "",
            "Tablespace": "",
            "Action_Dict": {Schema:[[Table,Action_item],[Table, Action_item]]},
            "staging_path": ""
        }
    }
"""
from AutomationUtils.cvtestcase import CVTestCase
from Database.OracleUtils.oraclehelper import OracleHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.Instances.restore_panels import OracleRestorePanel
from Web.AdminConsole.Databases.Instances.add_subclient import AddOracleSubClient
from Web.AdminConsole.Databases.subclient import SubClient
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from datetime import datetime
from pytz import timezone
import time


class TestCase(CVTestCase):
    """
    Class for executing basic acceptance test for Oracle table level restore on Command Center
    """

    def __init__(self):
        """
        Initializes test case class object
        """

        super().__init__()
        self.name = "ACCT1:Oracle table level restore from command center"
        self.browser = None
        self.browse = None
        self.admin_console = None
        self.instance_details = None
        self.tcinputs = {
            "UserName": None,
            "Password": None,
            "NewSubclient": None,
            "Plan": None,
            "Action_Dict": None,
            "Tablespace": None,
            "staging_path": None
        }
        self.time = None
        self.restore_panel = None
        self.subclient_object = None
        self.subclient_pageobj = None
        self.oracle_helper = None
        self.job_id = None

    def setup(self):
        """
        Method to setup test variables
        """

        self.oracle_helper = OracleHelper(self.commcell, self.client, self.instance, self.tcinputs['UserName'],
                                          self.tcinputs['Password'])
        self.oracle_helper.db_connect()
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            username=self.inputJSONnode['commcell']['commcellUsername'],
            password=self.inputJSONnode['commcell']['commcellPassword'],
            stay_logged_in=True
        )
        self.restore_panel = OracleRestorePanel(self.admin_console)
        self.browse = RBrowse(self.admin_console)
        self.admin_console.navigator.navigate_to_databases()
        DBInstances(self.admin_console).select_instance(DBInstances.Types.ORACLE, self.instance.instance_name,
                                                        self.client.client_name)
        self.instance_details = DBInstanceDetails(self.admin_console)

    @TestStep()
    def fill_sample_data(self):
        """
        Create a table in the database and populate table with records.
        """

        self.oracle_helper.create_sample_data(self.tcinputs['Tablespace'], stored_procedure=True)

    @TestStep()
    def create_subclient(self):
        """
        Create a new oracle subclient with table-level metadata enabled
        """

        self.instance_details.click_add_subclient(DBInstances.Types.ORACLE)
        AddOracleSubClient(self.admin_console).add_subclient(subclient_name=self.tcinputs['NewSubclient'],
                                                             plan=self.tcinputs['Plan'], table_browse=True)
        self.instance.refresh()
        self.log.info("Waiting for subclient creation completion")
        time.sleep(100)

    def wait_for_job_completion(self, job_id):
        """
        Wait for completion of job and check job status
            Args:
             job_id     (str): Job_id of the job we are waiting for completion of.
        """

        job_obj = self.commcell.job_controller.get(job_id)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                f"Failed to run job:{job_id} with error: {job_obj.delay_reason}"
            )
        self.log.info("Successfully finished %s job", job_id)

    @TestStep()
    def run_subclient_backup(self, first_backup_job=False):
        """
        Runs a backup job on the subclient created
            Args:
             first_backup_job  (bool):  True for the first backup job run.
              default: False
        """

        if first_backup_job:
            self.subclient_pageobj = SubClient(self.admin_console)
            job_id = self.subclient_pageobj.backup(RBackup.BackupType.FULL)
        else:
            self.subclient_object = self.instance.subclients.get(self.tcinputs['NewSubclient'])
            job = self.subclient_object.backup(backup_level="full")
            job_id = job.job_id
        self.wait_for_job_completion(job_id)
        if first_backup_job:
            self.time = datetime.now(timezone('Asia/Kolkata')).strftime('%m/%d/%Y %H:%M:%S')
            time.sleep(60)
            self.subclient_pageobj.return_to_instance(self.instance.instance_name)

    @TestStep()
    def drop_usertable(self):
        """
        Drops the table from connected database.

        """

        self.oracle_helper.db_drop_table(f"{self.tcinputs['Tablespace']}_user", 'CV_TABLE_01')

    @TestStep()
    def run_table_level_restore(self, table_option, recover_option, table_browse=False):
        """
        Select tables and run restore job. Fetches job_completion time of job object for
        point in time restore.
             Args:
              table_option  (str):  Table-level restore options.
                Accepted Values: Dump/Import

              recover_option(str):  Recover option for restore job.
                Accepted Values: "most recent backup"/"current time"/SCN number
                                /Point in time in format "%m/%d/%Y %H:%M:%S" (eg. 12/31/2020 23:59:59)

              table_browse        (bool):  Performs the required actions if table-level browse
                                           is to be performed when True.
                default: False
        """

        if table_browse:
            self.instance_details.access_restore()
            self.admin_console.wait_for_completion(1000)
            self.browse.select_tableview()
            self.admin_console.wait_for_completion(1000)
            self.browse.select_from_multiple_pages({f"{self.tcinputs['Tablespace']}_USER": ['CV_TABLE_01']},
                                                   self.instance.instance_name)
            self.browse.select_from_actions_menu(self.tcinputs['Action_Dict'], self.instance.instance_name)
        self.browse.submit_for_restore()
        if recover_option == 'Point in time':
            recover_option = self.time
        self.job_id = self.restore_panel.in_place_restore(recover_to=recover_option, table_options=table_option,
                                                          staging_path=self.tcinputs['staging_path'])
        self.wait_for_job_completion(self.job_id)

    @TestStep()
    def validate_restore(self, first_restore_job=True):
        """
        Validates if the table-level restore job was successful.
            Args:
                first_restore_job   (bool): Is true for the validation of the first restore job run
                    default: True
        """
        try:
            if first_restore_job:
                num_rows = self.oracle_helper.db_table_validate(f"{self.tcinputs['Tablespace']}_user", 'CV_TABLE_01')
                if num_rows != 10:
                    raise Exception("Restore Failed")
                self.log.info("Restore Successful")
            else:
                rman_log = self.oracle_helper.fetch_rman_log(self.job_id, self.client, 'restore').splitlines()
                for log_line in rman_log:
                    if ("exported" and "\"TESTCASE_USER\".\"CV_TABLE_01\"") in log_line:
                        if "10 rows" in log_line:
                            self.log.info("Restore Successful")
                            return
                raise Exception("Restore Failed")
        except Exception as exp:
            raise CVTestStepFailure from exp

    @TestStep()
    def add_tablerows(self):
        """
        Adds rows to existing table
        """

        self.oracle_helper.db_populate_table('CV_TABLE_', f"{self.tcinputs['Tablespace']}_user")

    def tear_down(self):
        """
        Tear down method for test case
        """

        self.oracle_helper.oracle_data_cleanup(self.tcinputs['Tablespace'], ['CV_TABLE_01'],
                                               f"{self.tcinputs['Tablespace']}_user")
        self.oracle_helper.db_drop_user(f"{self.tcinputs['Tablespace']}_user")
        self.instance.subclients.delete(self.tcinputs['NewSubclient'])

    def run(self):
        """
        Main function for test case execution
        """

        try:

            self.fill_sample_data()

            self.create_subclient()

            self.run_subclient_backup(True)

            self.drop_usertable()

            self.run_table_level_restore("Import", "Most recent backup", True)

            self.validate_restore()

            self.add_tablerows()

            self.run_subclient_backup()

            self.run_table_level_restore("Dump", "Point in time")

            self.validate_restore(False)

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
