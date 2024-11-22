# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright CommVault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for Dynamics 365: Auto Discovery Validation

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Dynamics365Pages.constants import D365AssociationTypes, AssocStatusTypes
from Web.AdminConsole.Helper.dynamics365_helper import Dynamics365Helper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing Dynamics 365: Auto Discovery Validation

    Example for test case inputs:
        "60133":
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
          "D365_Instance":[<D365-Instance-to-backup>],
          "Tables":[
          [<name-of-table>, <name-of-instance>],
          [<name-of-table>, <name-of-instance>]
          ]
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

                client_name             (str)           --  Name of Dynamics 365 Client
                d365_obj                (object)        --  Object of CVDynamics 365 class
                machine                 (object)        --  Object of Machine Class
                d365_tables             (list<tuple>)   --  List of Dynamics 365 Tables
                d365_helper             (object)        --  Object of Dynamics365Helper class
        """
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = "Dynamics 365: Auto Discovery Validation "
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.client_name = None
        self.d365tables = None
        self.d365_helper: Dynamics365Helper = None
        self.d365_plan: str = str()

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

            self.log.info("Creating an object for Dynamics 365 Helper")
            self.d365_helper = Dynamics365Helper(admin_console=self.admin_console, tc_object=self, is_react=True)

            self.log.info("Creating a Dynamics 365 Plan")
            d365_plan_props = {
                'ret_period': self.tcinputs['D365_Plan_Details']['Retention_Period'],
                'ret_unit': self.tcinputs['D365_Plan_Details']['Retention_Unit']
            }
            self.d365_plan = self.d365_helper.create_dynamics365_plan(retention_prop=d365_plan_props)

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_dynamics365()
            self.d365tables = self.tcinputs.get("Tables")

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        try:
            self.log.info("Creating Dynamics 365 CRM Client")
            self.client_name = self.d365_helper.create_dynamics365_client()
            self.log.info("Dynamics 365 Client created with Client Name: {}".format(self.client_name))

            self.log.info("Initializing SDK objects")
            self.d365_helper.initialize_sdk_objects_for_client()

            self.log.info("Verifying App Config Values")
            self.d365_helper.verify_client_configuration_value()
            self.log.info("Client Config Values successfully verifies")

            self.log.info("Associating an Instance")
            self.d365_helper.add_client_association(assoc_type=D365AssociationTypes.INSTANCE, plan=self.d365_plan,
                                                    instances=self.d365_helper.d365instances)
            self.log.info("Associated Dynamics 365 Instance")

            self.d365_helper.wait_for_discovery_to_complete()

            self.log.info("Validating if all Tables got discovered")
            tables = self.d365_helper.d365api_helper.get_tables_in_instance(
                instance_name=self.d365_helper.d365instances[0])
            tables = self.d365_helper.d365api_helper.get_friendly_name_of_tables(tables_dict=tables)
            self.log.info("Tables from Dynamics 365: {}".format(tables))

            tables_dict = {self.d365_helper.d365instances[0]: tables}
            self.d365_helper.verify_tables_discovery(tables_dict=tables_dict,
                                                     instance_list=[self.d365_helper.d365instances[0]])
            self.log.info("Verified Auto Discovery of Tables")

            self.log.info("Adding some tables manually")
            self.d365_helper.add_client_association(assoc_type=D365AssociationTypes.TABLE, plan=self.d365_plan,
                                                    tables=self.d365tables)
            self.log.info("Manual Tables Associated")

            self.log.info("Verifying Table exclusion from backup")
            self.d365_helper.dynamics365_apps.exclude_content(name=self.d365tables[0][0],
                                                              instance_name=self.d365tables[0][1])
            self.d365_helper.verify_content_status(status=AssocStatusTypes.DISABLED, name=self.d365tables[0][0],
                                                   instance=self.d365tables[0][1], is_instance=False)
            self.log.info("Verified Table exclusion from backup")

            self.log.info("Verifying Table inclusion in content")
            self.d365_helper.dynamics365_apps.include_in_backup(name=self.d365tables[0][0],
                                                                instance_name=self.d365tables[0][1])
            self.d365_helper.verify_content_status(status=AssocStatusTypes.ACTIVE, name=self.d365tables[0][0],
                                                   instance=self.d365tables[0][1], is_instance=False)
            self.log.info("Verified Table inclusion in content")

            self.log.info("Verifying Instance Exclusion from Backup")
            self.d365_helper.dynamics365_apps.exclude_content(name=self.d365_helper.d365instances[0], is_instance=True)
            self.d365_helper.wait_for_discovery_to_complete()
            self.d365_helper.verify_content_status(status=AssocStatusTypes.DISABLED, is_instance=True,
                                                   name=self.d365_helper.d365instances[0])
            instance_tables = self.d365_helper.get_tables_for_instance(instance_name=self.d365_helper.d365instances[0])
            for table in instance_tables[:10]:
                self.d365_helper.verify_content_status(status=AssocStatusTypes.DISABLED, name=table, is_instance=False,
                                                       instance=self.d365_helper.d365instances[0])
                self.log.info(f"Verified Auto Discovery removal of table: {table} from backup")
            self.log.info("Verified Instance Exclusion from Backup")

            self.log.info("Verifying Instance Inclusion in Backup")
            self.d365_helper.dynamics365_apps.include_in_backup(is_instance=True,
                                                                name=self.d365_helper.d365instances[0])
            self.d365_helper.wait_for_discovery_to_complete()
            self.d365_helper.verify_content_status(status=AssocStatusTypes.ACTIVE, is_instance=True,
                                                   name=self.d365_helper.d365instances[0])
            instance_tables = self.d365_helper.get_tables_for_instance(instance_name=self.d365_helper.d365instances[0])
            for table in instance_tables[:10]:
                self.d365_helper.verify_content_status(status=AssocStatusTypes.ACTIVE, name=table, is_instance=False,
                                                       instance=self.d365_helper.d365instances[0])
                self.log.info(f"Verified Auto Discovery inclusion of table: {table} from backup")
            self.log.info("Verified Instance Inclusion in Backup")

            self.log.info("Verifying Instance Deletion from Backup")
            self.d365_helper.dynamics365_apps.delete_from_content(name=self.d365_helper.d365instances[0],
                                                                  is_instance=True)
            self.d365_helper.wait_for_discovery_to_complete()
            self.d365_helper.verify_content_status(status=AssocStatusTypes.DELETED, is_instance=True,
                                                   name=self.d365_helper.d365instances[0])
            instance_tables = self.d365_helper.get_tables_for_instance(instance_name=self.d365_helper.d365instances[0])
            for table in instance_tables[:10]:
                self.d365_helper.verify_content_status(status=AssocStatusTypes.DELETED, name=table, is_instance=False,
                                                       instance=self.d365_helper.d365instances[0])
                self.log.info(f"Verified Auto Discovery deletion of table: {table} from backup")
            self.log.info("Verified Instance Deletion from Backup")

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.navigator.navigate_to_dynamics365()
                self.d365_helper.delete_dynamics365_client()
                self.d365_helper.delete_dynamics365_plan(plan_name=self.d365_plan)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
