# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Dynamics 365: Metallic: Basic Acceptance Test Case for Backup and Restore

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
        Class for executing Dynamics 365: Metallic: Basic Acceptance Test Case for Backup and Restore

    Example for test case inputs:
        "62151":
        {
            "Dynamics_Client_Name": <name-of-dynamics-client>,
            "GlobalAdmin": <global-admin-userid>>,
            "Password": <global-admin-password>>,
            "Tables: :
            [
                ("table1" , "environment1"} , ("table1", "environment2")
            ]
        }
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = "Dynamics 365 Point in time restore"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.client_name: str = str()
        self.d365_helper: Dynamics365Metallic = None
        self.d365_plan: str = str()
        self.tcinputs = {
            "Name": None,
            "BackedUpEntities": list()
        }
        self.service: Enum = HubServices.Dynamics365
        self.tenant_name: str = str()
        self.hub_utils: HubManagement = None
        self.client_level_restore = dict()
        self.entity_level_restore = dict()
        self.tenant_user_name: str = str()

    @test_step
    def wait_for_job_completion(self, job_id: int):
        """
            Method to wait for the job to complete
            Arguments:
                job_id      (int)--     Job ID to wait for
        """
        job = self.commcell.job_controller.get(job_id)
        self.log.info("Waiting for Job with Job ID: {} to complete".format(job_id))
        _job_status = job.wait_for_completion()

        if _job_status is False:
            raise Exception(f'Job {job_id} did not complete successfully')
        else:
            self.log.info(f'Job {job_id} completed successfully')

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
            self.client_level_restore = self.tcinputs["BackedUpEntities"][0]
            self.entity_level_restore = self.tcinputs["BackedUpEntities"][1]
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """Run function for the test case"""
        try:
            self.d365_helper.navigate_to_client(self.tcinputs["Name"])
            self.log.info("Running Dynamics 365 Point in Time Restore at the client level")
            _restore_job_details = self.d365_helper.verify_point_in_time_restore(
                restore_dict=self.client_level_restore,
                restore_type=RESTORE_TYPES.IN_PLACE,
                record_option=RESTORE_RECORD_OPTIONS.OVERWRITE)
            self.d365_helper.navigate_to_client(self.tcinputs["Name"])
            self.log.info("Running Dynamics 365 Point in Time Restore at the Entity level")
            _restore_job_details = self.d365_helper.verify_point_in_time_restore(
                restore_dict=self.entity_level_restore,
                restore_type=RESTORE_TYPES.IN_PLACE,
                record_option=RESTORE_RECORD_OPTIONS.OVERWRITE
            )
        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        """Tear-Down function for the test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)