# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Dynamics 365: Client Creation with Express Configuration and Modification of Configuration

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Dynamics365Pages.constants import D365AssociationTypes
from Web.AdminConsole.Dynamics365Pages.dynamics365 import Dynamics365Apps
from Web.AdminConsole.Helper.dynamics365_helper import Dynamics365Helper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing Dynamics 365: Client Creation with Express Configuration and Modification of Configuration

    Example for test case inputs:
        "64495":
        {
          "Name": "Dynamics365Client",
          "Dynamics_Client_Name": <name-of-dynamics-client>,
          "cloud_region": <cloud-region>,
          "ServerPlan": "<Server plan>",
          "IndexServer": "<Index Server>",
          "AccessNode": "<Access Node>",
          "office_app_type": "Dynamics365",
          "GlobalAdmin": "Global Administrator",
          "Password": "Global Admin Password",
          "TokenAdminUser": "Same as Global Admin",
          "TokenAdminPassword": "Same as Global Admin Password",
          "application_id": "Azure Application ID",
          "azure_directory_id": "Azure Directory ID",
          "application_key_value": "Azure Secret Key",
          "Dynamics365Plan": "Dynamics 365 Plan",
          "Tables": [["Table Name","Environment Name"]],
          "Columns": ["Column 1", "Column 2"],
          "D365_Plan": "AutoD365Plan"
        }
    """

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = "Dynamics 365: Client Creation with Express Configuration and Modification of Configuration"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.dynamics = None
        self.client_name = None
        self.d365_helper = None
        self.tcinputs = {
            "Dynamics_Client_Name": None,
            "ServerPlan": None,
            "IndexServer": None,
            "Columns": None,
        }

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
            self.client_name = self.d365_helper.create_dynamics365_client()
            self.log.info("Dynamics 365 Client created with Client Name: {}".format(self.client_name))

            self.log.info("Initializing SDK objects")
            self.d365_helper.initialize_sdk_objects_for_client()

            d365_plan = self.tcinputs.get("D365_Plan")
            self.d365_helper.add_client_association(assoc_type=D365AssociationTypes.TABLE, plan=d365_plan,
                                                    tables=self.d365_helper.d365tables)

            self.log.info("Associated Dynamics 365 Table")
            self.log.info("Running D365 CRM Client Level Backup")
            job_id = self.d365_helper.run_d365_client_backup()
            self.log.info("D365 Client level Backup Completed with job ID: {}".format(job_id))

            self.log.info("Changing attributes of the table ", self.d365_helper.d365tables[0][0])
            selected_columns = self.tcinputs.get("Columns")
            record_insights = (self.d365_helper.d365api_helper.
                               modify_single_record_of_table(table_name=self.d365_helper.d365tables[0][0],
                                                             instance_name=self.d365_helper.d365tables[0][1],
                                                             columns=selected_columns)
                                            )
            self.log.info("Attributes of the table changed")
            self.log.info("Running Attribute Restore Job")
            comparison_details = self.d365_helper.compare_and_restore_table_attributes(table_name=self.d365_helper.d365tables[0][0],
                                                                                       older_record=record_insights["OldRecord"],
                                                                                       newer_record=record_insights["UpdatedRecord"],
                                                                                       primary_attribute=record_insights["PrimaryNameAttribute"])

            self.log.info("Attribute Restore Job Completed with job ID: {}".format(comparison_details["Job ID"]))
            # Verify that the older_record data is same as obtained from the comparison details
            obtained_older_record = comparison_details["OldVersion"]
            obtained_updated_record = comparison_details["LiveVersion"]
            self.log.info("Confirming that the same attributes are changed in the table")
            for key in obtained_older_record.keys():
                if str(obtained_older_record[key]) != str(record_insights["OldRecord"].record_data[key]):
                    raise Exception("Older Record attributes are not same obtained from the comparison details")
            # Verify that the updated_record data is same as obtained from the comparison details
            for key in obtained_updated_record.keys():
                if str(obtained_updated_record[key]) != str(record_insights["UpdatedRecord"].record_data[key]):
                    raise Exception("Updated Record attributes are not same obtained from the comparison details")
            if not self.d365_helper.d365api_helper.compare_records(table_name=self.d365_helper.d365tables[0][0],
                                                                   instance_name=self.d365_helper.d365tables[0][1],
                                                                   older_record=record_insights["OldRecord"],
                                                                   columns=selected_columns):
                raise Exception("Record attributes are not same after restore")

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.navigator.navigate_to_dynamics365()
                self.d365_helper.delete_dynamics365_client()
                self.log.info("Client Deleted")
                self.log.info("Test Case Completed!!!")
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
