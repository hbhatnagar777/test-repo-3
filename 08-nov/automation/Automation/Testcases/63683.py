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
from Application.Dynamics365.d365web_api.constants import related_records


class TestCase(CVTestCase):
    """Class for executing Dynamics 365: Basic Test case for Backup and Restore

    Example for test case inputs:
        "63683": {
          "Dynamics_Client_Name": <name-of-dynamics-client>,
          "cloud_region": <1 for Default, 2 for GCC, 3 for GCC High>
          "ServerPlan": "<Server-Plan>",
          "IndexServer": <Index-Server>,
          "AccessNode": <access-node>,
          "office_app_type": "Dynamics365",
          "application_id":<azure-app-application-id>,
          "azure_directory_id":<azure-tenet-id>,
          "application_key_value":<azure-app-key-value>,
          "D365_Plan": "<name-of-D365-Plan>>",
          "TokenAdminUser": <global-admin-userid>>,
          "TokenAdminPassword": <global-admin-password>>,
          "D365_Instance": <instance-name>,
          "D365_Tables": {
                "Level 0": <level 0 tables>,
                "Level 1": <level 1 tables>,
                "Level 2": <level 2 tables>,
                "Level 3": <level 3 tables>,
                "Level 4": <level 4 tables>
            },
          "Relationships": {
                "<table-name>": <comma-separated-tables-to-which-its-related-to>,
                "<table-name>": <comma-separated-tables-to-which-its-related-to>,
                "<table-name>": <comma-separated-tables-to-which-its-related-to>
            }
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
        self.name = "Dynamics 365: Mixed Relation Related Restore Case"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.dynamics: Dynamics365Apps = None
        self.client_name = None
        self.d365_helper: Dynamics365Helper = None
        self.all_tables = []

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

            self.log.info("Running Cleanup for Tables")
            for level in self.tcinputs.get("D365_Tables"):
                for table in self.tcinputs.get("D365_Tables").get(level).split(','):
                    self.d365_helper.d365api_helper.cleanup_table(
                        table_name=table, instance_name=self.d365_helper.d365instances[0])
            self.log.info("Cleanup Complete")

            self.log.info("Populating Data")
            for level in self.tcinputs.get("D365_Tables"):
                for table in self.tcinputs.get("D365_Tables").get(level).split(','):
                    self.d365_helper.d365api_helper.create_table_records(
                        instance_name=self.d365_helper.d365instances[0],
                        table_name=table, number_of_records=related_records[level]
                    )
                    self.all_tables.append((table, self.d365_helper.d365instances[0]))
            self.log.info("Data Populated")

            self.log.info("Create related records")
            for table in self.tcinputs.get("Relationships"):
                self.d365_helper.d365api_helper.create_related_records(table,
                                                                       self.tcinputs.get("Relationships").get(table),
                                                                       self.d365_helper.d365instances[0])
            self.log.info("Related Records Created")

            self.log.info("Creating Dynamics 365 CRM Client")
            self.client_name = self.d365_helper.create_dynamics365_client()
            self.log.info("Dynamics 365 Client created with Client Name: {}".format(self.client_name))

            self.log.info("Initializing SDK objects")
            self.d365_helper.initialize_sdk_objects_for_client()

            d365_plan = self.tcinputs.get("D365_Plan")
            self.d365_helper.add_client_association(assoc_type=D365AssociationTypes.TABLE, plan=d365_plan,
                                                    tables=self.all_tables)
            self.log.info("Associated Dynamics 365 Instance")

            self.d365_helper.wait_for_discovery_to_complete()

            self.log.info("Getting Properties Before Backup Job")
            before_restore_prop = {}
            for level in self.tcinputs.get("D365_Tables"):
                for table in self.tcinputs.get("D365_Tables").get(level).split(','):
                    before_restore_prop[table] = self.d365_helper.d365api_helper.get_table_properties(
                        table_name=table, instance_name=self.d365_helper.d365instances[0])
            self.log.info("Fetched Table Properties")

            self.log.info("Running D365 CRM Client Level Backup")
            job_id = self.d365_helper.run_d365_client_backup()
            self.log.info("D365 Client level Backup Completed with job ID: {}".format(job_id))

            for restore_level in [None, "Level 1", "Level 2", "Level 3", "Level 0"]:

                self.log.info("Running Cleanup for Tables")
                for level in self.tcinputs.get("D365_Tables"):
                    if restore_level != "Level 0" or level != "Level 1":
                        for table in self.tcinputs.get("D365_Tables").get(level).split(','):
                            self.log.info(f"Cleaning up table {table}")
                            self.d365_helper.d365api_helper.cleanup_table(
                                table_name=table, instance_name=self.d365_helper.d365instances[0])
                self.log.info("Cleanup Complete")

                self.log.info("Running a Restore")
                restore_table = (self.tcinputs.get("D365_Tables").get("Level 0"), self.d365_helper.d365instances[0])
                restore_job_id = self.d365_helper.run_restore(tables=[restore_table],
                                                              restore_type=RESTORE_TYPES.IN_PLACE,
                                                              record_option=RESTORE_RECORD_OPTIONS.Skip,
                                                              restore_level=restore_level)
                self.log.info("Restore Completed with Job ID: {}".format(restore_job_id))

                self.log.info("Getting Properties After Restore Job")
                after_restore_prop = {}
                for level in self.tcinputs.get("D365_Tables"):
                    for table in self.tcinputs.get("D365_Tables").get(level).split(','):
                        after_restore_prop[table] = self.d365_helper.d365api_helper.get_table_properties(
                            table_name=table, instance_name=self.d365_helper.d365instances[0])
                self.log.info("Fetched Table Properties After Restore Job")

                self.log.info("Comparing Properties")
                self.d365_helper.cvd365_obj.restore.compare_table_prop(before_backup=before_restore_prop,
                                                                       after_restore=after_restore_prop,
                                                                       restore_level=restore_level)
                self.log.info("Table Properties Comparison Successful")

                self.log.info("Accessing some other tab to reselect the same table for restore next time")
                self.d365_helper.dynamics365_apps.get_instances_configured_count()

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.navigator.navigate_to_dynamics365()
                self.d365_helper.delete_dynamics365_client()
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
