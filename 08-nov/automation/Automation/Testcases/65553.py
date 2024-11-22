# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Dynamics 365: Metallic: Download and Compare with previous versions case

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""
import datetime
import time
from enum import Enum
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Metallic.hubutils import HubManagement
from Web.AdminConsole.Dynamics365Pages.constants import D365AssociationTypes, RESTORE_TYPES, RESTORE_RECORD_OPTIONS
from Web.AdminConsole.Helper.d365_metallic_helper import Dynamics365Metallic
from Web.AdminConsole.Hub.constants import HubServices
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """
        Class for executing Dynamics 365: Metallic: Download and Compare with previous versions case

    Example for test case inputs:
        "65553": {
                    "TenantUser": "<Tenant Admin User>",
                    "TenantPassword": "<Tenant Admin Password>",
                    "Dynamics_Client_Name": "<Dynamics 365 Client name>",
                    "AssociatedEntity":{
                        "TableName": "<Table Name>",
                        "EnvironmentName": "<Environment Name>",
                        "PrimaryColumnValue": "<Primary Column Value>",
                        "CompareVersions": ["1.0", "2.0"]
                    }
                }
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = "Dynamics 365: Metallic: Download and Compare with previous versions"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.client_name: str = str()
        self.d365_helper: Dynamics365Metallic = None
        self.d365_plan: str = str()
        self.tcinputs = {
            "Dynamics_Client_Name": None,
        }
        self.service: Enum = HubServices.Dynamics365
        self.tenant_name: str = str()
        self.hub_utils: HubManagement = None
        self.tenant_user_name: str = str()

    def setup(self):
        """Initial configuration for the testcase."""
        try:
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()
            self.log.info("Creating a login object")
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.tcinputs["TenantUser"],
                                     self.tcinputs["TenantPassword"],
                                     stay_logged_in=True)
            self.log.info("Creating an object for Dynamics 365 Helper")
            self.d365_helper = Dynamics365Metallic(admin_console=self.admin_console,
                                                   tc_object=self,
                                                   is_react=True)
            self.navigator = self.admin_console.navigator

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """Run function for the test case"""
        try:
            self.d365_helper.navigate_to_client(self.tcinputs["Dynamics_Client_Name"])
            self.d365_helper.validate_comparison_with_previous_versions(association_dict=self.tcinputs["AssociatedEntity"],
                                                                        is_download=True)
        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        """Tear-Down function for the test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
