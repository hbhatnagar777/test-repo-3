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
from Web.Common.page_object import handle_testcase_exception, TestStep
from Application.Dynamics365 import CVDynamics365


class TestCase(CVTestCase):
    """
    Class for executing
        Dynamics 365 CRM: Test Case for point in time restore validation

    Example for test case inputs:
        "63011":
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
          "OOP-Restore-Environment" : "<dest-environment>"
          "D365_Instance": "<env-name>",
        }
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name            (str)       --  name of this test case


                tcinputs    (dict)      --  dict of test case inputs with input name as dict key
                                                and value as input type

                        Ex: {

                             "MY_INPUT_NAME": None

                        }

                browser                 (object)    --      Browser object

                navigator               (object)    --      Navigator Object for Admin Console
                admin_console           (object)    --      Admin Console object

                client_name             (str)       --      Name of Dynamics 365 Client
                d365_obj                (object)    --      Object of CVDynamics 365 class
                cv_dynamics365          (object)    --      Object of CVDynamics365 Class
        """
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = "Dynamics 365 CRM: Out of Place Restore Basic and Advanced Cases "
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

            self.log.info("Creating Dynamics 365 CRM Client")
            #self.client_name = self.d365_helper.create_dynamics365_client()
            #self.log.info("Dynamics 365 Client created with Client Name: {}".format(self.client_name))

            self.cv_dynamics365.client_name = 'Dynamics365TC-630411681976859'

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def get_number_of_eligible_items_for_restore(self, table_props: dict) -> int:
        """
            Method to get the number of items eligible for restore
        """
        self.log.info("Items eligible for restore: {}".format(len(table_props)))
        return len(table_props)

    @test_step
    def validate_number_of_items_in_restore_job(self, restore_job, expected_count: int):
        """
            Method to get the number of items in the restore job.
            This method will help validate that the number of items is populated correctly.
            And correct number of items are picked for restore.
        """
        _job_item_count = restore_job.details.get("jobDetail").get("detailInfo").get('numOfObjects')
        self.log.info("Number of Items in Restore Job: {} : {} and Expected Item Count: {}".format(
            restore_job.job_id,
            _job_item_count, expected_count))

        assert expected_count == _job_item_count

    def run(self):
        """Run function for the test case"""
        try:

            self.cv_dynamics365.d365_operations.associate_environment()

            self.cv_dynamics365.d365api_helper.delete_accounts(
                instance_name=self.cv_dynamics365.d365instances[0])

            self.log.info("Creating Test Data in Accounts Table")
            self.cv_dynamics365.d365api_helper.create_accounts(
                instance_name=self.cv_dynamics365.d365instances[0])
            self.log.info("Table data Populated")

            self.log.info("Getting Properties Before Backup Job")
            _initial_accounts = self.cv_dynamics365.d365api_helper.get_table_properties(
                table_name="Account",
                instance_name=self.cv_dynamics365.d365instances[0])
            self.log.info("Fetched Table Properties")

            self.log.info("-" * 30)

            _first_bkp_job = self.cv_dynamics365.d365_operations.run_d365_client_backup()
            self.log.info("D365 Client level Backup Completed with job ID: {}".format(_first_bkp_job.job_id))
            _bkp_item_count = self.get_number_of_eligible_items_for_restore(table_props=_initial_accounts)

            self.log.info("-" * 30)

            _destination_environment = self.tcinputs.get("OOP-Restore-Environment")
            _restore_table = (self.cv_dynamics365.d365instances[0], "account")

            self.cv_dynamics365.d365api_helper.delete_accounts(instance_name=_destination_environment)

            self.log.info("-" * 30)

            self.log.info("Running OOP Restore with Skip Option")
            _oop_skip_rst_job = self.cv_dynamics365.d365_operations.run_out_of_place_restore(
                overwrite=False,
                restore_content=[
                    _restore_table],
                destination_environment=_destination_environment)
            _oop_skip_rst_accounts = self.cv_dynamics365.d365api_helper.get_table_properties(
                table_name="Account",
                instance_name=_destination_environment)

            self.log.info("Validating OOP Restore with Skip Option")
            self.validate_number_of_items_in_restore_job(restore_job=_oop_skip_rst_job,
                                                         expected_count=_bkp_item_count)
            self.log.info("Validated OOP Restore with Skip Option")

            self.log.info("-" * 30)

            self.cv_dynamics365.d365api_helper.modify_accounts(instance_name=_destination_environment)
            # this will help ensure that the accounts are modified to new value and overwrite is actually
            # overwriting them to back up value

            self.log.info("Running OOP Restore with Overwrite Option")
            _oop_overwrite_restore = self.cv_dynamics365.d365_operations.run_out_of_place_restore(
                overwrite=True,
                restore_content=[
                    _restore_table],
                destination_environment=_destination_environment)
            _oop_overwrite_rst_accounts = self.cv_dynamics365.d365api_helper.get_table_properties(
                table_name="Account",
                instance_name=_destination_environment)

            self.log.info("Validating OOP Restore with Over- Write Option when data exists")
            self.validate_number_of_items_in_restore_job(restore_job=_oop_overwrite_restore,
                                                         expected_count=_bkp_item_count)
            self.log.info("Validated OOP Restore with Over- Write Option when data exists")

            self.log.info("-" * 30)

            self.log.info("Cleaning destination environment")
            self.cv_dynamics365.d365api_helper.delete_accounts(instance_name=_destination_environment)

            self.log.info("-" * 30)

            self.log.info("Running OOP Restore with Overwrite Option with entities missing from destination")
            # This will help verify: when records are not present in destination, and an overwrite restore is run,
            # so restore is working correctly.

            _oop_overwrite_restore_after_cleanup = self.cv_dynamics365.d365_operations.run_out_of_place_restore(
                overwrite=True,
                restore_content=[
                    _restore_table],
                destination_environment=_destination_environment)
            _oop_overwrite_rst_accounts_after_cleanup = self.cv_dynamics365.d365api_helper.get_table_properties(
                table_name="Account",
                instance_name=_destination_environment)

            self.log.info("Validating OOP Restore with Over- Write Option when entities are missing from destination")
            self.validate_number_of_items_in_restore_job(restore_job=_oop_overwrite_restore_after_cleanup,
                                                         expected_count=_bkp_item_count)
            self.log.info("Validated OOP Restore with Over- Write Option when entities are missing from destination")

            self.log.info("-" * 30)

            self.log.info("Running OOP Restore with Skip Option with entities present in destination")
            # This will help verify: when records are present in destination, and an skip restore is run,
            # so none of the records are restored.

            _oop_skip_rst_job_second = self.cv_dynamics365.d365_operations.run_out_of_place_restore(
                overwrite=False,
                restore_content=[
                    _restore_table],
                destination_environment=_destination_environment)

            self.log.info("Validating OOP Restore with Skip option when entities are present in destination")
            self.validate_number_of_items_in_restore_job(restore_job=_oop_skip_rst_job_second,
                                                         expected_count=0)
            self.log.info("Validating OOP Restore with Skip option when entities are present in destination")

            self.log.info("-" * 30)

            self.log.info("Cleaning destination environment")
            self.cv_dynamics365.d365api_helper.delete_accounts(instance_name=_destination_environment)

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
