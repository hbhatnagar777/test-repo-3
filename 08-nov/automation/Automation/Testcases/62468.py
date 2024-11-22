# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case for performing a pdb clone (Redirect Individual) from Command Center

TestCase: Class for executing this test case

TestCase:

    __init__()  -- Initialize TestCase class

    setup()     -- Setup the Requirements for the test case

    run()       -- Run function of this test case

    tear_down() -- Tear Down function of this test case

    populate_table() --  Function to Create a table and populate it with data

    backup()  --  Function to back up client.

    drop_table() -- Function to delete backed up table

    navigate_to_pdbclone() -- Browse and navigate to the pdbclone restore page.

    restore() -- Run the pdb clone restore job

    validate() -- Validate if pdb was successfully cloned

Input Example:
    Providing all the inputs mentioned below is required.

    "testCases": {
        "62401": {
          "ClientName": "ClientName",
          "AgentName": "Oracle",
          "InstanceName": "InstanceName",
          "SubclientName": "SubclientName",
          "SysPassword": "",
          "FileFolders": ["FolderName"],
          "DestinationClient": "ClientName",
          "DestinationInstance": "InstanceName",
          "StagingPath": "StagingPath",
          "RedirectIndividualPdb": {"OldPdbName1":["NewPdbName1","DatafilePath1"],
                                    "OldPdbName2:["NewPdbName2","DatafilePath2"]}
        }
    }
"""

from AutomationUtils.cvtestcase import CVTestCase
from Database.OracleUtils.oraclehelper import OracleHelper
from Web.AdminConsole.Databases.Instances.restore_panels import OracleRestorePanel
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.Components.browse import Browse


class TestCase(CVTestCase):
    """Class for executing Test Case"""

    def __init__(self):
        super().__init__()
        self.name = "Testcase to verify oracle pdbclone (Redirect Individual Pdb Path) (62468)"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.browse = None
        self.db_instance_details = None
        self.db_instances = None
        self.oracle_helper = None
        self.oracle_restore_panel = None
        self.tcinputs = {"SysPassword": None,
                         "FileFolders": None,
                         "DestinationClient": None,
                         "DestinationInstance": None,
                         "StagingPath": None,
                         "RedirectIndividualPdb": None
                         }

    def setup(self):
        """Method to set up test variables"""
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.oracle_helper = OracleHelper(commcell=self.commcell, db_host=self.client,
                                          instance=self.instance, sys_user="sys",
                                          sys_password=self.tcinputs["SysPassword"])
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            username=self.inputJSONnode['commcell']['commcellUsername'],
            password=self.inputJSONnode['commcell']['commcellPassword'],
            stay_logged_in=True
        )
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.browse = Browse(self.admin_console)
        self.db_instances = DBInstances(self.admin_console)
        self.oracle_restore_panel = OracleRestorePanel(self.admin_console)
        self.log.info("Navigating to databases page")
        self.navigator = self.admin_console.navigator.navigate_to_databases()
        self.log.info("Selecting oracle from dropdown and selecting instance")
        self.db_instances.select_instance(database_type=DBInstances.Types.ORACLE,
                                          instance_name=self.tcinputs["InstanceName"],
                                          client_name=self.tcinputs["ClientName"])

    def tear_down(self):
        """Tear down method for testcase"""
        self.log.info("Dropping the created pdb after validation")
        for oldpdb_name in self.tcinputs["RedirectIndividualPdb"]:
            self.oracle_helper.db_drop_pdb(pdb_name=self.tcinputs["RedirectIndividualPdb"][oldpdb_name][0])

    @TestStep()
    def populate_table(self):
        """Populating the table with data"""
        for pdb in range(len(self.tcinputs["FileFolders"])):
            self.oracle_helper.db_connect_to_pdb(pdb_name=self.tcinputs["FileFolders"][pdb])
            self.oracle_helper.db_create_table(tablespace_name="vedtbspace", table_prefix=f"newpdbtb{pdb}", user="SYS",
                                               number=1)

    @TestStep()
    def backup(self):
        """Backing up the Oracle Client"""
        self.log.info("Running backup")
        self.oracle_helper.launch_backup_wait_to_complete(self.subclient)
        self.admin_console.refresh_page()

    @TestStep()
    def drop_table(self):
        """Dropping table after backup"""
        for pdb in range(len(self.tcinputs["FileFolders"])):
            self.oracle_helper.db_connect_to_pdb(pdb_name=self.tcinputs["FileFolders"][pdb])
            self.oracle_helper.db_drop_table(user="SYS", table=f"newpdbtb{pdb}01")

    @TestStep()
    def navigate_to_pdbclone(self):
        """Navigating to the pdb clone page in command center"""
        self.db_instance_details.access_restore()
        self.browse.clear_all_selection()
        self.browse.select_for_restore(file_folders=self.tcinputs["FileFolders"])
        self.browse.submit_for_restore()

    @TestStep()
    def restore(self):
        """Performing pdb clone restore"""
        try:
            job_id = self.oracle_restore_panel.out_of_place_restore(
                destination_client=self.tcinputs["DestinationClient"],
                destination_instance=self.tcinputs["DestinationInstance"],
                recover_to="most recent backup",
                pdb_clone=True, staging_path=self.tcinputs["StagingPath"],
                redirect_individual_pdb=self.tcinputs["RedirectIndividualPdb"])
            job = self.commcell.job_controller.get(job_id)
            if not job.wait_for_completion():
                raise CVTestStepFailure("Failed to run job ", job_id, "with error: ", job.delay_reason)
            self.log.info(f"Successfully finished job {job_id}")
        except Exception as exp:
            raise CVTestStepFailure from exp

    @TestStep()
    def validate(self):
        """Validating if restore went through successfully"""
        iterator = 0
        for oldpdb_name in self.tcinputs["RedirectIndividualPdb"]:
            self.oracle_helper.db_connect_to_pdb(pdb_name=self.tcinputs["RedirectIndividualPdb"][oldpdb_name][0])
            no_of_rec = self.oracle_helper.db_table_validate(user="SYS", tablename=f"newpdbtb{iterator}01")
            if no_of_rec != 10:
                raise CVTestStepFailure("Validation Failed,Pdb clone did not go through successfully")
            iterator += 1
        self.log.info("Validation successful, Pdb clone went through successfully")

    def run(self):
        """Main function for test case execution"""
        try:
            self.populate_table()
            self.backup()
            self.drop_table()
            self.navigate_to_pdbclone()
            self.restore()
            self.validate()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
