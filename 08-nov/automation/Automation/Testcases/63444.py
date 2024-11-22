# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test Case for Dynamics 365: Launch Licensing Case

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.windows_machine import WindowsMachine
from Web.AdminConsole.Dynamics365Pages.constants import D365AssociationTypes, AssocStatusTypes, \
    RESTORE_RECORD_OPTIONS, RESTORE_TYPES
from Web.AdminConsole.Dynamics365Pages.dynamics365 import Dynamics365Apps
from Web.AdminConsole.Helper.dynamics365_helper import Dynamics365Helper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """
    Class for executing
        Dynamics 365: Launch Licensing Case

    Example for test case inputs:
        "63399":
        {
          "Dynamics_Client_Name": <name-of-dynamics-client>,
          "cloud_region": 1 for Default, 2 for GCC, 3 for GCC High
          "ServerPlan": "<Server-Plan>>",
          "IndexServer": <Index-Server>>,
          "AccessNode": <access-node>>,
          "office_app_type": "Dynamics365",
          "TokenAdminUser": <global-admin-userid>>,
          "TokenAdminPassword": <global-admin-password>>,
          "application_id":<azure-app-application-id>,
          "azure_directory_id":<azure-tenet-id>,
          "application_key_value":<azure-app-key-value>,
          "Lic_Username": <display-name-of-the-user>,
          "Lic_User_Password": <paasword>,
          "nick_name": <nick-name-of-the-user>,
          "skuId": <license-guid-to-be-assigned>,
          "Remove_License_Username": <username-for-which-license-is-to-be-removed>,
          "Remove_License_ID": <license-skuid-to-be-removed>,
          "all_licensed_users": [<list-of-users-currently-having-license>]

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
        self.name = "Dynamics 365 : Launch Licensing Case "
        self.browser = None
        self.navigator = None
        self.admin_console = None
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
                self.inputJSONnode['commcell']['commcellPassword'],
                stay_logged_in=True)
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

            self.log.info(f"Step1- Launching and verifying Licensing for client {self.client_name} with existing users")
            if self.d365_helper.cvd365_obj.d365_operations.run_and_verify_licensing():
                self.log.info("1. Licensing verified for the client with existing users")
            else:
                raise Exception("1. Licensing not working for existing users")

            user_obj = self.d365_helper.cvd365_obj.d365api_helper.users.create_user(
                name=self.tcinputs.get("Lic_Username"),
                password=self.tcinputs.get("Lic_User_Password"),
                nick_name=self.tcinputs.get("nick_name"))

            self.d365_helper.cvd365_obj.d365api_helper.users.assign_license(name=user_obj.display_name,
                                                                            sku_id=self.tcinputs.get("skuId"))
            self.log.info(
                f"Step2- Launching and verifying Licensing for client {self.client_name} with newly added user")
            if self.d365_helper.cvd365_obj.d365_operations.run_and_verify_licensing(
                    lic_added_user=user_obj.display_name):
                self.log.info("2. Licensing verified for the client with newly added user")
            else:
                raise Exception("2. Licensing not working for newly added user")

            self.d365_helper.cvd365_obj.d365api_helper.users.delete_user(name=user_obj.display_name)
            self.log.info(f"Step3- Launching and verifying Licensing for client {self.client_name} by deleting newly "
                          f"added user")
            if self.d365_helper.cvd365_obj.d365_operations.run_and_verify_licensing(
                    lic_removed_user=user_obj.display_name):
                self.log.info("3. Licensing verified for the client by deleting newly added user")
            else:
                raise Exception("3. Licensing not working by deleting newly added user")

            user_obj = self.d365_helper.cvd365_obj.d365api_helper.users.get_user(
                name=self.tcinputs.get("Remove_License_Username"))
            self.d365_helper.cvd365_obj.d365api_helper.users.assign_license(name=user_obj.display_name,
                                                                            remove_licenses=
                                                                            self.tcinputs.get("Remove_License_ID"))
            self.log.info(f"Step4- Launching and verifying Licensing for client {self.client_name} "
                          f"by removing license of an existing user")
            if self.d365_helper.cvd365_obj.d365_operations.run_and_verify_licensing(
                    lic_removed_user=user_obj.display_name):
                self.log.info("4. Licensing verified for the client by removing license of an existing user")
            else:
                raise Exception("4. Licensing not working by removing license of an existing user")

            self.d365_helper.cvd365_obj.d365api_helper.users.assign_license(name=user_obj.display_name,
                                                                            sku_id=
                                                                            self.tcinputs.get("Remove_License_ID"))
            self.log.info(f"Step5- Launching and verifying Licensing for client {self.client_name} "
                          f"by adding license back of an existing user")
            if self.d365_helper.cvd365_obj.d365_operations.run_and_verify_licensing(
                    lic_added_user=user_obj.display_name):
                self.log.info("5. Licensing verified for the client by adding license back of an existing user")
            else:
                raise Exception("5. Licensing not working by adding license back of an existing user")

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        """Tear down function for the test case"""
        try:
            if self.status == constants.PASSED:
                self.d365_helper.cvd365_obj.d365_operations.delete_d365_client()
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
