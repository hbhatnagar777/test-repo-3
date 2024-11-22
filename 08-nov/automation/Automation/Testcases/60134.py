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
from Web.AdminConsole.Dynamics365Pages.constants import D365AssociationTypes, AssocStatusTypes, \
    RESTORE_RECORD_OPTIONS, RESTORE_TYPES
from Web.AdminConsole.Dynamics365Pages.dynamics365 import Dynamics365Apps
from Web.AdminConsole.Helper.dynamics365_helper import Dynamics365Helper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing Dynamics 365: Basic Test case for Backup and Restore

    Example for test case inputs:
        "60134":
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
    test_step = TestStep()

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

                dynamics                (object)    --  Object of Dynamics365Apps Web Class

                client_name             (str)       --   Name of Dynamics 365 Client
                d365_obj                (object)    --   Object of CVDynamics 365 class
                machine                 (object)    --  Object of Machine Class
        """
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = "Dynamics 365: Basic Test case for Backup and Restore "
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.dynamics: Dynamics365Apps = None
        self.client_name = None
        self.d365_helper: Dynamics365Helper = None

    def setup(self):
        """Initial configuration for the testcase."""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname, enable_ssl=True)

            self.admin_console.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword'])
            self.log.info("Logged in to Admin Console")

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_dynamics365()
            self.log.info("Navigated to D365 Page")

            self.log.info("Creating an object for Dynamics 365 Helper")
            self.d365_helper = Dynamics365Helper(admin_console=self.admin_console, tc_object=self, is_react=True)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        try:
            self.log.info("Creating Dynamics 365 CRM Client")
            self.client_name = self.d365_helper.create_dynamics365_client()
            self.log.info("Dynamics 365 Client created with Client Name: {}".format(self.client_name))

            self.log.info("Initializing SDK objects")
            self.d365_helper.initialize_sdk_objects_for_client()

            d365_plan = self.tcinputs.get("D365_Plan")
            self.d365_helper.add_client_association(assoc_type=D365AssociationTypes.INSTANCE, plan=d365_plan,
                                                    instances=self.d365_helper.d365instances)
            self.log.info("Associated Dynamics 365 Instance")

            self.d365_helper.wait_for_discovery_to_complete()

            self.log.info("Populating Data")
            self.d365_helper.d365api_helper.create_contacts(
                instance_name=self.d365_helper.d365instances[0])
            self.log.info("Data Populated")

            self.log.info("Getting Properties Before Backup Job")
            before_restore_prop = {"Account": self.d365_helper.d365api_helper.get_table_properties(
                table_name="Account",
                instance_name=self.d365_helper.d365instances[0])}
            self.log.info("Fetched Table Properties")

            self.log.info("Running D365 CRM Client Level Backup")
            job_id = self.d365_helper.run_d365_client_backup()
            self.log.info("D365 Client level Backup Completed with job ID: {}".format(job_id))

            self.log.info("Running Cleanup for Table")
            self.d365_helper.d365api_helper.delete_contacts(instance_name=self.d365_helper.d365instances[0])
            self.log.info("Cleanup Complete")

            self.log.info("Running a Restore")
            restore_table = ("Account", self.d365_helper.d365instances[0])
            restore_job_id = self.d365_helper.run_restore(tables=[restore_table],
                                                          restore_type=RESTORE_TYPES.IN_PLACE,
                                                          record_option=RESTORE_RECORD_OPTIONS.Skip)
            self.log.info("Restore Completed with Job ID: {}".format(restore_job_id))

            self.log.info("Getting Properties After Restore Job")
            after_restore_prop = {"Account": self.d365_helper.d365api_helper.get_table_properties(
                table_name="Account",
                instance_name=self.d365_helper.d365instances[0])}
            self.log.info("Fetched Table Properties After Restore Job")

            self.log.info("Comparing Properties")
            self.d365_helper.cvd365_obj.restore.compare_table_prop(before_backup=before_restore_prop,
                                                                   after_restore=after_restore_prop)
            self.log.info("Table Properties Comparison Successful")

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.navigator.navigate_to_dynamics365()
                self.d365_helper.delete_dynamics365_client()
                self.d365_helper.d365api_helper.delete_contacts(instance_name=
                                                                self.d365_helper.d365instances[0])
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
