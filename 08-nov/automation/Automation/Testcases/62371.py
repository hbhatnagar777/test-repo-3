# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for Verification of client level, backupset level, table level, and full backup option

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  set up the requirements for the test case

    run()           --  run function of this test case

"""
import datetime
import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Metallic.hubutils import HubManagement
from Web.AdminConsole.Dynamics365Pages.constants import D365AssociationTypes, RESTORE_TYPES, RESTORE_RECORD_OPTIONS
from Web.AdminConsole.Helper.d365_metallic_helper import Dynamics365Metallic
from Web.AdminConsole.Helper.dynamics365_helper import Dynamics365Helper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """
    Class for executing
        Dynamics 365 CRM: Test Case for Verification of client level,
        backupset level, table level, and full backup option

    Example for test case inputs:
        "62371":
        {
          "Dynamics_Client_Name": <name-of-dynamics-client>,
          "GlobalAdmin": <global-admin-userid>>,
          "Password": <global-admin-password>>,
          "D365_Instance":<D365-Instance-to-backup>
        }
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.name = "Dynamics 365  CRM Metallic Automation: " \
                    "Verification of client level, backup-set level, table level, and full backup option"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.d365_helper: Dynamics365Metallic = None
        self.client_name: str = str()
        self.d365_plan: str = str()
        self.hub_utils: HubManagement = None
        self.tenant_name: str = str()
        self.tenant_user_name: str = str()

    @test_step
    def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.hub_utils = HubManagement(self, self.commcell.webconsole_hostname)
        self.tenant_name = datetime.datetime.now().strftime('D365-Automation-%d-%B-%H-%M')
        current_timestamp = str(int(time.time()))
        self.tenant_user_name = self.hub_utils.create_tenant(
            company_name=self.tenant_name,
            email=f'cvd365autouser-{current_timestamp}@d365{current_timestamp}.com')

    @test_step
    def initiate_and_verify_client_level_backup(self, total_tables_in_backup):
        """Initiates client level backup job and verifies it"""
        try:
            _job_id = self.d365_helper.run_d365_client_backup(client_level=True, is_metallic_env=True)
            self.d365_helper.verify_backup_job_stats(job_id=_job_id,
                                                     status_tab_expected_stats={
                                                         "Total": total_tables_in_backup,
                                                         "Successful": total_tables_in_backup
                                                     })
            self.d365_helper.navigate_to_client()
            return _job_id
        except Exception:
            raise CVTestStepFailure('Exception while verifying client level backup')

    @test_step
    def initiate_and_verify_backupset_level_backup(self, total_tables_in_backup):
        """Initiates backupset level backup job and verifies it"""
        try:
            self.d365_helper.navigate_to_client()
            _backupset_level_job = self.d365_helper.run_d365_client_backup(client_level=False, is_metallic_env=True)
            self.d365_helper.verify_backup_job_stats(job_id=_backupset_level_job,
                                                     status_tab_expected_stats={
                                                         "Total": total_tables_in_backup,
                                                         "Successful": total_tables_in_backup
                                                     })
            self.d365_helper.navigate_to_client()
        except Exception:
            raise CVTestStepFailure('Exception while verifying backup set level backup')

    @test_step
    def initiate_and_verify_table_level_backup(self):
        """Initiates table level backup jobs and verifies them"""
        try:
            self.d365_helper.navigate_to_client()
            _configured_content = self.d365_helper.get_configured_content_list()
            _single_table_bkp = _configured_content[0]
            _single_site_bkp_job = self.d365_helper.initiate_backup_for_dynamics365_content(
                content=[(_single_table_bkp, self.d365_helper.d365instances[0])], is_instance=False,
                is_metallic_env=True)

            self.admin_console.refresh_page()
            _multiple_table_bkp = _configured_content[4:6]
            _multiple_table_bkp = [(_item, self.d365_helper.d365instances[0]) for _item in _multiple_table_bkp]
            # forming list of the format: [ (table-name, environment-name), (table2name, environment-name)]

            _multiple_table_bkp_job = self.d365_helper.initiate_backup_for_dynamics365_content(
                content=_multiple_table_bkp, is_instance=False, is_metallic_env=True)
            self.d365_helper.verify_backup_job_stats(job_id=_single_site_bkp_job,
                                                     status_tab_expected_stats={
                                                         "Total": 1,
                                                         "Successful": 1
                                                     })
            self.d365_helper.verify_backup_job_stats(job_id=_multiple_table_bkp_job,
                                                     status_tab_expected_stats={
                                                         "Total": 2,
                                                         "Successful": 2
                                                     })
            self.d365_helper.navigate_to_client()
        except Exception:
            raise CVTestStepFailure('Exception while verifying table level backup')

    @test_step
    def run_and_verify_full_backup(self, first_full_bkp_job):
        """
            Run a full backup job for the client and check if the number of items are
            matching with the first backup job for the client
                Since we are not populating any data anywhere, the item count should be matching

        """
        self.d365_helper.navigate_to_client()
        _full_bkp_job = self.d365_helper.run_d365_client_backup(full_backup=True, is_metallic_env=True)
        _full_bkp_items = self.d365_helper.cvd365_obj.csdb_operations.number_of_items_in_backup_job(
            job_id=_full_bkp_job)
        _first_bkp_items = self.d365_helper.cvd365_obj.csdb_operations.number_of_items_in_backup_job(
            job_id=first_full_bkp_job)

        if _full_bkp_items != _first_bkp_items:
            self.log.exception(
                "Number of items for first job: {} and full backup job: {} do not match".format(_first_bkp_items,
                                                                                                _full_bkp_items))
            raise CVTestStepFailure("Number of items for full backup job do not match as expected")

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
                                     self.inputJSONnode['commcell']['commcellPassword'],
                                     stay_logged_in=True)

            # self.hub_dashboard.click_new_configuration()
            self.log.info("Creating an object for Dynamics 365 Helper")
            self.d365_helper = Dynamics365Metallic(admin_console=self.admin_console, tc_object=self)

            self.d365_helper.on_board_tenant()

            self.navigator = self.admin_console.navigator

            self.d365_plan = self.d365_helper.get_dynamics365_plans_for_tenant()[0]

            self.navigator.navigate_to_dynamics365()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """ Run function for the test case """
        try:

            self.client_name = self.d365_helper.create_metallic_dynamics365_client()
            self.log.info("Dynamics 365 Client created with Client Name: {}".format(self.client_name))

            d365_plan = self.d365_plan
            self.d365_helper.add_client_association(assoc_type=D365AssociationTypes.INSTANCE,
                                                    plan=d365_plan,
                                                    instances=self.d365_helper.d365instances)
            self.log.info("Associated Dynamics 365 Instance")

            self.admin_console.refresh_page()

            _associated_tables = int(self.d365_helper.get_items_associated_count())
            self.log.info("Number of associated items to the client: {}".format(_associated_tables))

            _first_full_job = self.initiate_and_verify_client_level_backup(total_tables_in_backup=_associated_tables)

            self.initiate_and_verify_backupset_level_backup(total_tables_in_backup=_associated_tables)

            self.initiate_and_verify_table_level_backup()

            # self.run_and_verify_full_backup(_first_full_job)
            # full backup support is yet to be implemented for the
            # agent, will uncomment once agent side support is there

        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        """ Tear Down function for the test case """
        try:
            if self.status == constants.PASSED:
                self.navigator.navigate_to_dynamics365()
                self.d365_helper.delete_dynamics365_client(client_name=self.client_name)
                self.d365_helper.delete_automation_tenant(tenant_name=self.tenant_name)
                self.log.info("Client Deleted")
                self.log.info("Test Case Completed!!!")
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
