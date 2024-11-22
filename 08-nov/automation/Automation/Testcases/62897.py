# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for Dynamics 365: Basic Test case for Backup and Restore

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Helper.dynamics365_helper import Dynamics365Helper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import handle_testcase_exception
from Application.Dynamics365 import CVDynamics365


class TestCase(CVTestCase):
    """
    Class for executing
        Dynamics 365 CRM: Retention Validation

    Example for test case inputs:
        "62897":
        {
          "Dynamics_Client_Name": <name-of-dynamics-client>,
          "ServerPlan": "<Server-Plan>>",
          "IndexServer": <Index-Server>>,
          "AccessNode": <access-node>>,
          "office_app_type": "Dynamics365",
          "TokenAdminUser": <global-admin-userid>>,
          "TokenAdminPassword": <global-admin-password>>,
          "application_id":<azure-app-application-id>,
          "azure_directory_id":<azure-tenet-id>,
          "application_key_value":<azure-app-key-value>,
          "D365_Instance": "<env-name>",
          "D365_Plan": "<D365-Plan>",
          "Dynamics365Plan": "<D365-Plan>",
          "D365-Environments": "<env-name>",
          "D365-Tables": "<table-name>"
        }
    """

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name            (str)       --  name of this test case

                tcinputs    (dict)      --  dict of test case inputs with input name as dict key
                                                and value as input type

                        Ex: {

                             "MY_INPUT_NAME": None

                        }

                browser                 (object)    --  Browser object

                navigator               (object)    --  Navigator Object for Admin Console
                admin_console           (object)    --  Admin Console object

                client_name             (str)       --   Name of Dynamics 365 Client
                d365_obj                (object)    --   Object of CVDynamics 365 class
                machine                 (object)    --  Object of Machine Class
        """
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = "Dynamics 365 CRM: Retention Validation "
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.client_name = None
        self.d365_helper: Dynamics365Helper = None
        self.cv_dynamics365: CVDynamics365 = None

    def setup(self):
        """Initial configuration for the testcase."""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname, enable_ssl=True)

            self.admin_console.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword'],
                stay_logged_in=True)
            self.log.info("Logged in to Admin Console")

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_dynamics365()
            self.log.info("Navigated to D365 Page")

            self.log.info("Creating an object for Dynamics 365 Helper")
            self.d365_helper = Dynamics365Helper(admin_console=self.admin_console, tc_object=self, is_react=True)
            self.cv_dynamics365 = CVDynamics365(self)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """Run function for the test case"""
        try:
            self.log.info("Creating Dynamics 365 CRM Client")
            self.client_name = self.d365_helper.create_dynamics365_client()
            self.log.info("Dynamics 365 Client created with Client Name: {}".format(self.client_name))

            self.cv_dynamics365.client_name = self.client_name

            for tables in self.cv_dynamics365.d365tables:
                self.cv_dynamics365.d365api_helper.cleanup_table(tables[0], tables[1])

            d365_plan = self.tcinputs.get("D365_Plan")
            self.cv_dynamics365.d365_operations.associate_tables()
            self.log.info("Associated Dynamics 365 Table")

            self.log.info("Populating Data")
            for tables in self.cv_dynamics365.d365tables:
                self.cv_dynamics365.d365api_helper.create_table_records(tables[0], tables[1])
            self.log.info("Tables data Populated")

            self.log.info("Running D365 CRM Client Level Backup")
            _first_bkp_job = self.cv_dynamics365.d365_operations.run_d365_client_backup()
            self.log.info("D365 Client level Backup Completed with job ID: {}".format(_first_bkp_job.job_id))

            self.log.info("Cleaning Data")
            for tables in self.cv_dynamics365.d365tables:
                self.cv_dynamics365.d365api_helper.cleanup_table(tables[0], tables[1])
            self.log.info("Cleanup Complete")

            self.log.info("Running D365 CRM Client Level Backup")
            _second_bkp_job = self.cv_dynamics365.d365_operations.run_d365_client_backup(skip_playback_check=True)
            self.log.info("D365 Client level Backup Completed with job ID: {}".format(_second_bkp_job.job_id))

            d365_table_dict = dict()
            plan_obj = self.cv_dynamics365.d365_operations.get_plan_obj(d365_plan)
            retention_period = plan_obj._properties['office365Info']['o365CloudOffice']['caRetention']['detail'] \
                ['cloudAppPolicy']['retentionPolicy']['numOfDaysForMediaPruning']

            for table in self.cv_dynamics365.d365tables:
                d365_table_dict[table[0]] = retention_period

            self.cv_dynamics365.solr_helper.validate_retention(d365_table_dict)

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        """Tear down function for the test case"""
        try:
            if self.status == constants.PASSED:
                self.cv_dynamics365.d365_operations.delete_d365_client()
                self.cv_dynamics365.d365api_helper.delete_accounts(
                    instance_name=self.cv_dynamics365.d365instances[0])
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
