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
import random
import time
from typing import Set, Any, List

from Application.Dynamics365.constants import D365JobPhases
from Application.Exchange.ExchangeMailbox.utils import test_step
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Helper.dynamics365_helper import Dynamics365Helper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception
from Application.Dynamics365 import CVDynamics365


class TestCase(CVTestCase):
    """
    Class for executing
        Dynamics 365 CRM: Backup Stats, Health Report.

    Example for test case inputs:
        "63041":
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
          "D365_Instance": "<env-name>",
          "D365_Plan": "<D365-Plan>",
          "Dynamics365Plan": "<D365-Plan>"
        }
    """

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name            (str)       --  name of this test case

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
        self.name = "Dynamics 365 CRM: Backup Stats, Health Report "
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.client_name = None
        self.d365_helper: Dynamics365Helper = None
        self.cv_dynamics365: CVDynamics365 = None

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
            self.cv_dynamics365 = CVDynamics365(self)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def get_tables_for_removal(self, associated_tables: list) -> list[Any]:
        """
            Get 5 tables at random for manually associating
        """
        _tables = random.sample(associated_tables, 3)
        _tables_manual_association = list()
        for _table in _tables:
            _t_name, _e_name = _table.get("name"), _table.get("environment_name")
            _tables_manual_association.append((_t_name, _e_name))
        self.log.info("Setting Tables: {} to association type Manual".format(_tables_manual_association))
        return _tables_manual_association

    @test_step
    def run_and_verify_backup_health_report(self, _associated_tables_count: int, _removed_tables_count: int):
        """Initiates client level backup job and verifies it"""
        try:
            self.log.info("Running a backup for the Dynamics 365 CRM Client.")
            _bkp_job = self.cv_dynamics365.d365_operations.run_d365_client_backup()

            _expected_table_count = _associated_tables_count - _removed_tables_count
            self.d365_helper.verify_backup_job_stats(job_id=_bkp_job.job_id,
                                                     status_tab_expected_stats={
                                                         "Total": _expected_table_count,
                                                         "Successful": _expected_table_count
                                                     })

            self.d365_helper.verify_backup_health_report_stats(associated_tables_count=_associated_tables_count,
                                                               excluded_tables_count=_removed_tables_count)
            return _bkp_job
        except Exception:
            raise CVTestStepFailure('Exception while verifying backup/ backup health report for client')

    def run(self):
        """Run function for the test case"""
        try:
            self.client_name = self.d365_helper.create_dynamics365_client()
            self.log.info("Dynamics 365 Client created with Client Name: {}".format(self.client_name))

            self.cv_dynamics365.client_name = self.client_name

            self.log.info("Initializing SDK objects")
            self.d365_helper.initialize_sdk_objects_for_client()

            d365_plan = self.tcinputs.get("D365_Plan")

            self.cv_dynamics365.d365api_helper.create_contacts(instance_name=self.cv_dynamics365.d365instances[0])

            self.cv_dynamics365.d365_operations.associate_environment()
            self.log.info("Associated Dynamics 365 Instance")

            self.log.info("Excluding Some tables from backup")
            _associated_tables = self.subclient.get_associated_tables(refresh=True)
            _tables_for_manual_association = self.get_tables_for_removal(associated_tables=_associated_tables)

            self.log.info("Accessing some other tab so that association changes get reflected")
            self.d365_helper.dynamics365_apps.get_instances_configured_count()

            self.d365_helper.modify_client_association(tables=_tables_for_manual_association, operation="EXCLUDE")
            self.log.info("Excluded :{} tables from backup".format(_tables_for_manual_association))

            _bkp_job = self.run_and_verify_backup_health_report(_associated_tables_count=len(_associated_tables),
                                                                _removed_tables_count=len(
                                                                    _tables_for_manual_association))

            self.d365_helper.verify_client_overview_summary(last_bkp_job=_bkp_job,
                                                            associated_tables_count=len(_associated_tables),
                                                            removed_tables_count=len(_tables_for_manual_association))


        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        """Tear down function for this test case"""
        try:
            if self.status == constants.PASSED:
                self.cv_dynamics365.d365_operations.delete_d365_client()
                self.cv_dynamics365.d365api_helper.delete_contacts(
                    instance_name=self.cv_dynamics365.d365instances[0])

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
