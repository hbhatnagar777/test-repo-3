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
        Class for executing Dynamics 365: Metallic: Basic Acceptance Test Case for Backup and Restore using custom configuration

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
        self.name = "Metallic Dynamics 365: Basic Acceptance case using Custom Configuration"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.client_name: str = str()
        self.d365_helper: Dynamics365Metallic = None
        self.d365_plan: str = str()
        self.tcinputs = {
            "Dynamics_Client_Name": None,
            "D365_Instance": list(),
            "application_id": None,
            "application_key_value": None,
            "azure_directory_id": None
        }
        self.service: Enum = HubServices.Dynamics365
        self.tenant_name: str = str()
        self.hub_utils: HubManagement = None
        self.tenant_user_name: str = str()
        self.inc_objects = None

    @test_step
    def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.hub_utils = HubManagement(self, self.commcell.webconsole_hostname)
        self.tenant_name = datetime.datetime.now().strftime('D365-Auto-%d-%B-%H-%M')
        current_timestamp = str(int(time.time()))
        self.tenant_user_name = self.hub_utils.create_tenant(
            company_name=self.tenant_name,
            email=f'cvd365autouser-{current_timestamp}@d365{current_timestamp}.com')

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

    @test_step
    def verify_incremental_backup(self, full_job_id: int, inc_job_id: int):
        """
            Method to wait for the job to complete
            Arguments:
                full_job_id      (int)--     Full backup Job ID
                inc_job_id       (int)--     Incremental backup Job ID
        """
        self.inc_objects = self.tcinputs["IncrementalObjects"]
        _full_job_id = self.commcell.job_controller.get(full_job_id)
        _inc_job_id = self.commcell.job_controller.get(inc_job_id)
        if _inc_job_id.num_of_files_transferred == self.inc_objects and _full_job_id.num_of_files_transferred > 0 \
                and _inc_job_id.num_of_files_transferred > 0:
            self.log.info(f"Incremental is verified")
        else:
            raise Exception("Incremental is not verified")

    def setup(self):
        """Initial configuration for the testcase."""
        try:
            self.create_tenant()
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()
            self.log.info("Creating a login object")
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.tenant_user_name,
                                     self.inputJSONnode["commcell"]["commcellPassword"],
                                     stay_logged_in=False)

            self.log.info("Creating an object for Dynamics 365 Helper")
            self.d365_helper = Dynamics365Metallic(admin_console=self.admin_console,
                                                   tc_object=self,
                                                   is_react=True)

            self.d365_helper.on_board_tenant()

            self.navigator = self.admin_console.navigator

            self.d365_helper.verify_tenant_on_boarding()

            self.d365_plan = self.d365_helper.get_dynamics365_plans_for_tenant()[0]
            self.navigator.navigate_to_service_catalogue()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """Run function for the test case"""
        try:
            self.d365_helper.select_dynamics_service()
            self.client_name = self.d365_helper.create_metallic_dynamics365_client()
            self.log.info("Dynamics 365 Client created with Client Name: {}".format(self.client_name))

            self.log.info("Associating an Instance")

            self.d365_helper.dynamics365_apps.add_association(assoc_type=D365AssociationTypes.TABLE,
                                                              plan=self.d365_plan,
                                                              tables=self.d365_helper.d365tables)

            self.log.info("Associated Dynamics 365 Tables: {}".format(self.d365_helper.d365tables))

            self.log.info("Running D365 CRM Client Level Backup")
            _bkp_job_id = self.d365_helper.dynamics365_apps.initiate_backup(content=[self.d365_helper.d365tables[0]])
            self.log.info("D365 Client level Backup Started with job ID: {}".format(_bkp_job_id))

            self.wait_for_job_completion(job_id=_bkp_job_id)
            self.log.info("Dynamics 365 CRM backup job is completed")

            self.d365_helper.navigate_to_client()

            self.log.info("Running D365 CRM Client Level Backup")
            _inc_bkp_job_id = self.d365_helper.dynamics365_apps.run_d365client_backup()
            self.log.info("D365 Client level Backup Started with job ID: {}".format(_bkp_job_id))

            self.wait_for_job_completion(job_id=_inc_bkp_job_id)
            self.log.info("Dynamics 365 CRM backup job is completed")

            self.verify_incremental_backup(full_job_id=_bkp_job_id, inc_job_id=_inc_bkp_job_id)

            self.log.info("Running Dynamics 365 Restore")
            _restore_job_id = self.d365_helper.dynamics365_apps.run_restore(tables=self.d365_helper.d365tables,
                                                                            restore_type=RESTORE_TYPES.IN_PLACE,
                                                                            record_option=RESTORE_RECORD_OPTIONS.OVERWRITE)
            self.log.info("Restore Completed Started Job ID: {}".format(_restore_job_id))

            self.wait_for_job_completion(_restore_job_id)

            self.d365_helper.validate_backup_and_restore(backup_job_id=_bkp_job_id, restore_job_id=_restore_job_id)

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        """Tear-Down function for the test case"""
        try:
            if self.status == constants.PASSED:
                self.navigator.navigate_to_dynamics365()
                self.d365_helper.delete_dynamics365_client(client_name=self.client_name)
                self.d365_helper.delete_automation_tenant(tenant_name=self.tenant_name)
                self.log.info("Test Case Completed!!!")
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)