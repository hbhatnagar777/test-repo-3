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
import datetime
import time

from Application.Dynamics365 import CVDynamics365, utils
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Metallic.hubutils import HubManagement
from Web.AdminConsole.Dynamics365Pages.constants import D365AssociationTypes
from Web.AdminConsole.Helper.d365_metallic_helper import Dynamics365Metallic
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """
    Class for executing
        Dynamics 365 CRM Metallic: Custom Config on-boarding and Application User creation

    Example for test case inputs:
        "62645":
        {
          "Dynamics_Client_Name": <name-of-dynamics-client>,
          "TokenAdminUser": <global-admin-userid>>,
          "TokenAdminPassword": <global-admin-password>>,
          "D365_Instance":<D365-Instance-to-backup>

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

                browser                 (object)    --  Browser object
                browser                 (object)    --  Browser object

                navigator               (object)    --  Navigator Object for Admin Console
                admin_console           (object)    --  Admin Console object

                client_name             (str)       --   Name of Dynamics 365 Client
                d365_obj                (object)    --   Object of CVDynamics 365 class
                machine                 (object)    --  Object of Machine Class
        """
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = "Dynamics 365 CRM Metallic: Custom Config on-boarding, Application User creation" \
                    " and Incremental Backup Test Case"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.client_name = None
        self.d365_helper: Dynamics365Metallic = None
        self.cv_dynamics365: CVDynamics365 = None

        self.tenant_name: str = str()
        self.hub_utils: HubManagement = None
        self.tenant_user_name: str = str()
        self.d365_plan: str = str()

    @test_step
    def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.hub_utils = HubManagement(self, self.commcell.webconsole_hostname)
        self.tenant_name = datetime.datetime.now().strftime('D365-Automation-%d-%B-%H-%M')
        current_timestamp = str(int(time.time()))
        self.tenant_user_name = self.hub_utils.create_tenant(
            company_name=self.tenant_name,
            email=f'cvd365autouser-{current_timestamp}@d365{current_timestamp}.com')

    def setup(self):
        """Initial configuration for the testcase."""
        try:
            self.create_tenant()

            utils.create_azure_app(self)
            self.log.info("Azure app for automation created")

            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()
            self.log.info("Creating a login object")
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.tenant_user_name,
                                     self.inputJSONnode['commcell']['commcellPassword'],
                                     stay_logged_in=True)

            # self.hub_dashboard.click_new_configuration()

            self.log.info("Creating an object for Dynamics 365 Helper")
            self.d365_helper = Dynamics365Metallic(admin_console=self.admin_console, tc_object=self)

            self.d365_helper.on_board_tenant()

            self.navigator = self.admin_console.navigator

            self.d365_plan = self.d365_helper.get_dynamics365_plans_for_tenant()[0]
            self.d365_helper.d365_plan = self.d365_plan
            self.navigator.navigate_to_dynamics365()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """Run function for the test case"""
        try:
            self.client_name = self.d365_helper.create_metallic_dynamics365_client()
            self.log.info("Dynamics 365 Client created with Client Name: {}".format(self.client_name))

            self.d365_helper.dynamics365_apps.configure_application_user(
                environment_name=self.d365_helper.d365instances[0],
                instance_modal=True)

            self.d365_helper.add_client_association(assoc_type=D365AssociationTypes.TABLE)
            self.log.info("Associated Dynamics 365 Instance")

            self.cv_dynamics365 = self.d365_helper.cvd365_obj

            self.log.info("Populating Data")
            self.cv_dynamics365.d365api_helper.create_contacts(
                instance_name=self.cv_dynamics365.d365instances[0])

            self.log.info("Data Populated")

            self.log.info("Running D365 CRM Client Level Backup")
            _first_bkp_job = self.d365_helper.run_d365_client_backup(is_metallic_env=True)
            self.log.info("D365 Client level Backup Completed with job ID: {}".format(_first_bkp_job))

            _number_of_records: int = 150
            self.log.info("Populating Data")
            self.cv_dynamics365.d365api_helper.create_contacts(
                instance_name=self.cv_dynamics365.d365instances[0], number_of_records=150)

            self.log.info("Data Populated")

            self.log.info("Running D365 CRM Client Level Backup")
            _second_bkp_job = self.d365_helper.run_d365_client_backup(is_metallic_env=True)
            self.log.info("D365 Client level Backup Completed with job ID: {}".format(_second_bkp_job))

            _bkp_items = self.cv_dynamics365.csdb_operations.number_of_items_in_backup_job(
                job_id=_second_bkp_job)
            if _bkp_items > _number_of_records:
                self.log.exception("Number of items in backup job are greater than the expected number of items")
                self.log.info(
                    "Backup job Items: {}, Expected Number of Items: {}".format(_bkp_items, _number_of_records))
                raise Exception(
                    "Incremental Backup Check Failed: Number of items in backup job are greater than the expected "
                    "number of items")

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        """Tear down function for the test case"""
        try:
            if self.status == constants.PASSED:
                self.cv_dynamics365.d365_operations.delete_d365_client()
                self.d365_helper.delete_automation_tenant(tenant_name=self.tenant_name)
                self.log.info("Test Case Completed!!!")
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.cv_dynamics365.d365api_helper.delete_contacts(
                instance_name=self.cv_dynamics365.d365instances[0])
