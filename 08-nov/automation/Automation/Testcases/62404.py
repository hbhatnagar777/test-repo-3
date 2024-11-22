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

    run_table_level_restore()   --  Runs a table-level restore job

    validate_restore()          --  Validates whether the restore job was successful


Input Example:

    "testCases": {
        "62404": {
            "UserName": "SYS",
            "Password": "",
            "ClientName": "",
            "InstanceName": "",
            "AgentName": "Oracle",
            "NewSubclient": "",
            "Plan": "",
            "Tablespace": "",
            "Action_Dict": {Schema:[[Table,Action_item],[Table, Action_item]]},
            "Staging_path": ""
            "Destination_client": "",
            "Destination_instance": "",
            "Destination_UserName": "SYS",
            "Destination_Password": "",
            "Auxiliary_instance": "",
			"pFile": "/path/pfile.ora"
        }
    }
"""
from AutomationUtils.cvtestcase import CVTestCase
from Database.OracleUtils.oraclehelper import OracleHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.Instances.restore_panels import OracleRestorePanel
from Web.AdminConsole.Databases.Instances.add_subclient import AddOracleSubClient
from Web.AdminConsole.Databases.subclient import SubClient
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
import time


class TestCase(CVTestCase):
    """
    Class for executing basic acceptance test for Oracle table level OOP restore on Command Center
    """

    def __init__(self):
        """
        Initializes test case class object
        """

        super().__init__()
        self.name = "Oracle table level out of place restore with user created aux from command center"
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
            "Staging_path": None,
            "Destination_client": None,
            "Destination_instance": None,
            "Destination_UserName": None,
            "Destination_Password": None,
            "Auxiliary_instance": None
        }
        self.restore_panel = None
        self.subclient_object = None
        self.src_oracle_helper = None
        self.dest_oracle_helper = None
        self.dest_client = None
        self.dest_instance = None
        self.job_id = None

    def setup(self):
        """
        Method to setup test variables
        """

        self.src_oracle_helper = OracleHelper(self.commcell, self.client, self.instance, self.tcinputs['UserName'],
                                              self.tcinputs['Password'])
        self.src_oracle_helper.db_connect()
        self.dest_client = self.commcell.clients.get(self.tcinputs['Destination_client'])
        dest_agent = self.dest_client.agents.get(self.tcinputs['AgentName'])
        self.dest_instance = dest_agent.instances.get(self.tcinputs['Destination_instance'])
        self.dest_oracle_helper = OracleHelper(self.commcell, self.dest_client, self.dest_instance,
                                               self.tcinputs['Destination_UserName'],
                                               self.tcinputs['Destination_Password'])
        self.dest_oracle_helper.db_connect()
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

        self.src_oracle_helper.create_sample_data(self.tcinputs['Tablespace'], stored_procedure=True)
        self.dest_oracle_helper.create_sample_data(self.tcinputs['Tablespace'])
        self.dest_oracle_helper.db_drop_table(f"{self.tcinputs['Tablespace']}_user", 'CV_TABLE_01')

    @TestStep()
    def create_subclient(self):
        """
        Create a new oracle subclient with table-level metadata enabled
        """

        self.instance_details.click_add_subclient(DBInstances.Types.ORACLE)
        AddOracleSubClient(self.admin_console).add_subclient(subclient_name=self.tcinputs['NewSubclient'],
                                                             plan=self.tcinputs['Plan'], table_browse=True)

        self.admin_console.wait_for_completion(500)
        time.sleep(60)
        self.log.info("Waiting for subclient creation completion")
        self.instance.refresh()
        SubClient(self.admin_console).return_to_instance(self.instance.instance_name)


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
    def run_subclient_backup(self):
        """
        Runs a backup job on the subclient created
        """

        self.subclient_object = self.instance.subclients.get(self.tcinputs['NewSubclient'])
        job = self.subclient_object.backup(backup_level="full")
        self.wait_for_job_completion(job.job_id)

    @TestStep()
    def run_table_level_restore(self, table_option):
        """
        Select tables and run restore job. Fetches job_completion time of job object for
        point in time restore.
             Args:
              table_option  (str):  Table-level restore options.
                Accepted Values: Dump/Import
        """

        self.admin_console.refresh_page()
        self.instance_details.access_restore()
        self.admin_console.wait_for_completion(5000)
        self.browse.select_tableview()
        self.admin_console.wait_for_completion(5000)
        time.sleep(30)
        self.browse.select_from_multiple_pages({f"{self.tcinputs['Tablespace']}_user".upper(): ['CV_TABLE_01']})
        self.browse.select_from_actions_menu(self.tcinputs['Action_Dict'])
        self.browse.submit_for_restore()
        self.job_id = self.restore_panel.out_of_place_restore(
            self.tcinputs['Destination_client'], self.tcinputs['Destination_instance'],
            auxiliary_instance=self.tcinputs['Auxiliary_instance'], recover_to='Most recent backup',
            table_options=table_option, staging_path=self.tcinputs['Staging_path'],
            user_created_auxiliary=True, pfile=self.tcinputs['pFile']
        )
        self.wait_for_job_completion(self.job_id)

    @TestStep()
    def validate_restore(self, table_option):
        """
        Validates if the table-level restore job was successful.
            Args:
                  table_option  (str):  Restore job type that needs to be validated.
                    Accepted Values: Dump/Import
        """

        try:
            flag = False
            rman_log = self.dest_oracle_helper.fetch_rman_log(self.job_id, self.dest_client, 'restore').splitlines()
            for log_line in rman_log:
                if ("exported" and f"\"{self.tcinputs['Tablespace'].upper()}_USER\".\"CV_TABLE_01\"") in log_line:
                    if "10 rows" in log_line:
                        self.log.info("Export Successful")
                        flag = True
                        break
            if not flag:
                raise Exception("Restore Failed")
            if table_option == 'import':
                num_rows = self.dest_oracle_helper.db_table_validate(f"{self.tcinputs['Tablespace']}_user",
                                                                     'CV_TABLE_01')
                if num_rows != 10:
                    raise Exception("Restore Failed")
                self.log.info("Import Successful")
            self.log.info("Restore Successful")
        except Exception as exp:
            raise CVTestStepFailure from exp

    def tear_down(self):
        """
        Tear down method for test case
        """

        self.src_oracle_helper.oracle_data_cleanup(self.tcinputs['Tablespace'], ['CV_TABLE_01'],
                                                   f"{self.tcinputs['Tablespace']}_user")
        self.src_oracle_helper.db_drop_user(f"{self.tcinputs['Tablespace']}_user")

        self.dest_oracle_helper.oracle_data_cleanup(self.tcinputs['Tablespace'], ['CV_TABLE_01'],
                                                    f"{self.tcinputs['Tablespace']}_user")
        self.dest_oracle_helper.db_drop_user(f"{self.tcinputs['Tablespace']}_user")

        self.instance.subclients.delete(self.tcinputs['NewSubclient'])

    def run(self):
        """
        Main function for test case execution
        """

        try:

            self.fill_sample_data()

            self.create_subclient()

            self.run_subclient_backup()

            self.run_table_level_restore("Import")

            self.validate_restore("import")

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
