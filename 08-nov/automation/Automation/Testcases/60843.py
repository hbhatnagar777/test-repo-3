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
        Dynamics 365 CRM: Test Case for point in time restore validation

    Example for test case inputs:
        "60843":
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
          "D365_Plan": "<name-of-D365-Plan>>",
          "D365_Instance":[<D365-Instance-to-backup>]

        }
    """

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name            (str)       --  name of this test case


                show_to_user    (bool)      --  test case flag to determine if the test case is
                                                    to be shown to user or not
                    Accept:
                        True    -   test case will be shown to user from commcell gui

                        False   -   test case will not be shown to user

                    default: False

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
        self.name = "Dynamics 365 CRM: Test Case for point in time restore validation "
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
                self.browser, self.commcell.webconsole_hostname,enable_ssl=True)

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

            d365_plan = self.tcinputs.get("D365_Plan")
            self.cv_dynamics365.d365_operations.associate_environment()
            self.log.info("Associated Dynamics 365 Instance")

            self.log.info("Populating Data")
            self.cv_dynamics365.d365api_helper.create_accounts(
                instance_name=self.cv_dynamics365.d365instances[0])
            self.log.info("Data Populated")

            self.log.info("Getting Properties Before Backup Job")
            before_first_backup_prop = {"Account": self.cv_dynamics365.d365api_helper.get_table_properties(
                table_name="Account",
                instance_name=self.cv_dynamics365.d365instances[0])}
            self.log.info("Fetched Table Properties")

            self.log.info("Running D365 CRM Client Level Backup")
            _first_bkp_job = self.cv_dynamics365.d365_operations.run_d365_client_backup()
            self.log.info("D365 Client level Backup Completed with job ID: {}".format(_first_bkp_job.job_id))

            self.log.info("Populating Data")
            self.cv_dynamics365.d365api_helper.create_accounts(
                instance_name=self.cv_dynamics365.d365instances[0])
            self.log.info("Data Populated")

            self.log.info("Getting Properties Before Backup Job")
            before_second_backup_prop = {"Account": self.cv_dynamics365.d365api_helper.get_table_properties(
                table_name="Account",
                instance_name=self.cv_dynamics365.d365instances[0])}
            self.log.info("Fetched Table Properties")

            self.log.info("Running D365 CRM Client Level Backup")
            _second_bkp_job = self.cv_dynamics365.d365_operations.run_d365_client_backup()
            self.log.info("D365 Client level Backup Completed with job ID: {}".format(_second_bkp_job.job_id))

            self.log.info("Running Cleanup for Table")
            self.d365_helper.d365api_helper.delete_accounts(instance_name=
                                                            self.d365_helper.d365instances[0])
            self.log.info("Cleanup Complete")

            self.log.info("Running a Restore")
            restore_table = (self.cv_dynamics365.d365instances[0], "account")
            _first_restore_job = self.cv_dynamics365.d365_operations.run_inplace_restore(
                overwrite=True,
                job_id=_first_bkp_job.job_id,
                restore_content=[restore_table])

            self.log.info("Restore Completed with Job ID: {}".format(_first_restore_job.job_id))

            self.log.info("Getting Properties After Restore Job")
            after_first_restore_prop = {"Account": self.cv_dynamics365.d365api_helper.get_table_properties(
                table_name="Account",
                instance_name=self.cv_dynamics365.d365instances[0])}
            self.log.info("Fetched Table Properties After Restore Job")

            self.log.info("Running Second Restore")
            restore_table = (self.cv_dynamics365.d365instances[0], "account")
            _second_restore_job = self.cv_dynamics365.d365_operations.run_inplace_restore(
                overwrite=True,
                restore_content=[restore_table])

            self.log.info("Restore Completed with Job ID: {}".format(_second_restore_job.job_id))

            self.log.info("Getting Properties After Restore Job")
            after_second_restore_prop = {"Account": self.cv_dynamics365.d365api_helper.get_table_properties(
                table_name="Account",
                instance_name=self.cv_dynamics365.d365instances[0])}
            self.log.info("Fetched Table Properties After Restore Job")

            self.log.info("Comparing Properties")
            self.cv_dynamics365.restore.compare_table_prop(before_backup=before_first_backup_prop,
                                                           after_restore=after_first_restore_prop)
            self.log.info("Table Properties Comparison Successful")

            self.log.info("Comparing Properties")
            self.cv_dynamics365.restore.compare_table_prop(before_backup=before_second_backup_prop,
                                                           after_restore=after_second_restore_prop)
            self.log.info("Table Properties Comparison Successful")

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        """Tear down function for the test case"""
        try:
            if self.status == constants.PASSED:
                self.cv_dynamics365.d365_operations.delete_d365_client()
                self.d365_helper.d365api_helper.delete_accounts(instance_name=
                                                                self.d365_helper.d365instances[0])
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
