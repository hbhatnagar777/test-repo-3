# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Dynamics 365: Metallic: Restore related records upto 3 levels

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""
import datetime
import time
from enum import Enum
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
        Class for executing Dynamics 365: Metallic: Restore related records upto 3 levels case

    Example for test case inputs:

    """
    test_step = TestStep()

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.logical_name = None
        self.d365_api_helper = None
        self.d365_obj = None
        self.testcaseutils = CVTestCase
        self.name = "Dynamics 365: Metallic: Restore related records upto 3 levels"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.client_name: str = str()
        self.d365_helper: Dynamics365Metallic = None
        self.d365_plan: str = str()
        self.tcinputs = {
            "Dynamics_Client_Name": None,
            "RestoreCount": None
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
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """Run function for the test case"""
        try:
            self.d365_helper.navigate_to_client(self.tcinputs["Dynamics_Client_Name"])
            self.log.info("Running Level 1 in place restore")
            JobIdLevelOne = self.d365_helper.dynamics365_apps.run_restore(tables=self.d365_helper.d365tables,
                                                                          restore_type=RESTORE_TYPES.IN_PLACE,
                                                                          record_option=RESTORE_RECORD_OPTIONS.OVERWRITE,
                                                                          restore_level="Level 1")
            self.wait_for_job_completion(job_id=JobIdLevelOne)
            _restore_job = self.commcell.job_controller.get(JobIdLevelOne)
            if not _restore_job.num_of_files_transferred == self.tcinputs["RestoreCount"]["Level 1"]:
                raise Exception("Level 1 restore count is not matching")
            self.d365_helper.navigate_to_client(self.tcinputs["Dynamics_Client_Name"])
            self.log.info("Running Level 2 in place restore")
            JobIdLevelTwo = self.d365_helper.dynamics365_apps.run_restore(tables=self.d365_helper.d365tables,
                                                                          restore_type=RESTORE_TYPES.IN_PLACE,
                                                                          record_option=RESTORE_RECORD_OPTIONS.OVERWRITE,
                                                                          restore_level="Level 2")
            self.wait_for_job_completion(job_id=JobIdLevelTwo)
            _restore_job = self.commcell.job_controller.get(JobIdLevelTwo)
            if not _restore_job.num_of_files_transferred == self.tcinputs["RestoreCount"]["Level 2"]:
                raise Exception("Level 2 restore count is not matching")
            self.d365_helper.navigate_to_client(self.tcinputs["Dynamics_Client_Name"])
            self.log.info("Running Level 3 in place restore")
            JobIdLevelThree = self.d365_helper.dynamics365_apps.run_restore(tables=self.d365_helper.d365tables,
                                                                            restore_type=RESTORE_TYPES.IN_PLACE,
                                                                            record_option=RESTORE_RECORD_OPTIONS.OVERWRITE,
                                                                            restore_level="Level 3")
            self.wait_for_job_completion(job_id=JobIdLevelThree)
            _restore_job = self.commcell.job_controller.get(JobIdLevelThree)
            if not _restore_job.num_of_files_transferred == self.tcinputs["RestoreCount"]["Level 3"]:
                raise Exception("Level 3 restore count is not matching")
        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        """Tear-Down function for the test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
