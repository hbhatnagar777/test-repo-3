# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright CommVault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
    This module provides the function or operations that can be used to run
    Metallic web automation for Dynamics 365 CRM.

    To begin, create an instance of Dynamics365Metallic for test case.

    To initialize the instance, pass the testcase object to the Dynamics 365 Apps class
        and the admin console object

    This file consists of only one class Dynamics365Metallic.
"""

import time
from enum import Enum

import Application.Dynamics365.constants as dynamics365_constants
from AutomationUtils import logger
from Metallic.hubutils import HubManagement
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Dynamics365Pages import constants as d365_constants
from Web.AdminConsole.Dynamics365Pages.constants import \
    metallic_d365_plan_retention_dict
from Web.AdminConsole.Dynamics365Pages.dynamics365 import Dynamics365Apps
from Web.AdminConsole.Helper.dynamics365_helper import Dynamics365Helper
from Web.AdminConsole.Hub.constants import HubServices
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import TestStep


class Dynamics365Metallic(Dynamics365Helper):
    """
        Helper Class for Dynamics 365 CRM Metallic.
            Inherits base Dynamics365Helper for core functionalities.
            This file only has extra helper methods needed for Metallic configuration
    """

    test_step = TestStep()

    def __init__(self, tc_object, admin_console, is_react=False):
        """Initializes the Dynamics365Apps class instance

                Args:
                    tc_object       (Object)    --  Testcase object
                    admin_console   (Object)    --  Object denoting the admin console

        """
        Dynamics365Helper.__init__(self, admin_console=admin_console, tc_object=tc_object, is_react=is_react)
        self.tc_inputs = tc_object.tcinputs
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self.log = logger.get_log()
        self._commcell = tc_object.commcell
        self.tc_object = tc_object
        self.service_catalogue = None
        self.newly_created_app_name: str = str()

        self.app_stats_dict = {}

        # Required Components
        # self.plans = Plans(self._admin_console)
        # self._plan_details = PlanDetails(self._admin_console)
        self._hub_utils: HubManagement = HubManagement(tc_object, self._commcell.webconsole_hostname)
        # self.hub_dashboard: Dashboard = None

        # D365 Specific components/ requirements
        # self.dynamics365_apps = Dynamics365Apps(tc_object=tc_object, admin_console=self._admin_console)
        self.__plans = None
        self.__plan_details = None
        self.__is_react = is_react
        self.tenant_name: str = tc_object.tenant_name
        self.testcase_id = tc_object.id

        self.service: Enum = HubServices.Dynamics365

        self.log.info("Logger initialized for Dynamics 365 Pages - Metallic")

    @property
    def _plan_details(self):
        """Plan details object"""
        if self.__plan_details is None:
            self.__plan_details = PlanDetails(self._admin_console)
        return self.__plan_details

    @test_step
    def __get_retention_period(self):
        """
            Returns retention period of the Dynamics 365 plan set on the admin console
        """
        _d365_plan_details = self._plan_details.plan_info(plan_type=d365_constants.Dynamics365.D365_PLAN_TYPE.value)

        if "Retention" not in _d365_plan_details.keys():
            raise CVWebAutomationException("Retention tab/ label not found for the Dynamics 365 Plan(s)")

        _d365_plan_retention = _d365_plan_details["Retention"]
        return _d365_plan_retention.get(self._admin_console.props['label.retentionPeriod'],
                                        _d365_plan_retention.get(self._admin_console.props['label.retentionDays']))

    @test_step
    def __get_converted_retention_period(self, retention_period):
        """
        Converts the retention period to no of days format and returns it

             Args:
                    retention_period(str) : retention period
                    Example: '5-years', 'infinite'

        """
        self.log.info(f'Given retention period : {retention_period}')

        converted_retention_period = metallic_d365_plan_retention_dict[retention_period]
        self.log.info(f'Converted retention period : {converted_retention_period}')
        return converted_retention_period

    @test_step
    def _verify_d365_plan_retention(self, plans: list):
        """
            Verifies retention for the created Dynamics 365 plans

            Args:
                    plans(list)      : list of plans

        """
        tenant_name = self.tenant_name.lower()
        for plan in plans:
            if 'metallic-d365-plan' in plan.lower():
                # verify if it is none among the three
                # then proceed
                expected_retention = self.__get_converted_retention_period(
                    plan.split(tenant_name)[-1].split('metallic-d365-plan')[0].strip('-'))

                if plan not in metallic_d365_plan_retention_dict.keys():
                    continue
                self.plans.select_plan(plan)

                actual_retention = self.__get_retention_period()

                if expected_retention != actual_retention:
                    raise Exception(f'Retention is not set correctly for {plan}'
                                    f'Expected Value: {expected_retention}, Actual Value: {actual_retention}')
                else:
                    self.log.info(f'Retention is set correctly for {plan}')
            self._plan_details.redirect_to_plans()

    @test_step
    def verify_dynamics365_plans_creation_for_tenant(self):
        """
            Gets the list of all the available Dynamics 365 Plans.
        """
        _d365_plans = self.plans.list_plans(plan_type=d365_constants.Dynamics365.D365_PLAN_TYPE.value)
        if len(_d365_plans) < 3:
            self.log.info("Number of Dynamics 365 Plans Fetched: {}".format(len(_d365_plans)))
            self.log.info("Plans Fetched: {}".format(_d365_plans))
            raise CVWebAutomationException(
                "Adequate number of Dynamics 365 Plans were not created on tenant on- boarding")

        self._verify_d365_plan_retention(plans=_d365_plans)
        self.dynamics365_apps.d365_plan = _d365_plans[0]

    @test_step
    def get_dynamics365_plans_for_tenant(self):
        """
            Method to get all the Dynamics 365 Plans present for the tenant
        """
        self._admin_console.navigator.navigate_to_plan()
        _d365_plans = self.plans.list_plans(plan_type=d365_constants.Dynamics365.D365_PLAN_TYPE.value)
        return _d365_plans

    @test_step
    def create_metallic_dynamics365_client(self):
        """
            Method to create a Dynamics 365 Client

            Returns:
            client_name             (str)--     Name of the Dynamics 365 client that was created
        """
        self.dynamics365_apps.create_dynamics365_app(client_name=self.client_name, is_metallic=True,
                                                     cloud_region=self.cloud_region)

        self.client_name = self.dynamics365_apps.get_app_name()

        self.log.info("Created Dynamics 365 CRM Client with Client Name: {}".format(self.client_name))

        self.dynamics365_apps.client_name = self.client_name

        return self.client_name

    @test_step
    def delete_dynamics365_client(self, client_name: str = str()):
        """
            Method to delete the Dynamics 365 client
        """
        if not client_name:
            client_name = self.client_name
        self.dynamics365_apps.delete_dynamics365_app(client_name)
        self.log.info("Deleted Dynamics 365 CRM client with client name: {}".format(client_name))

    @test_step
    def validate_backup_and_restore(self, backup_job_id: int, restore_job_id: int):
        """
            Validate the backup/ restore for the Dynamics 365 client
        """
        _bkp_job = self._commcell.job_controller.get(backup_job_id)
        _restore_job = self._commcell.job_controller.get(restore_job_id)

        if _bkp_job.num_of_files_transferred == 0 or \
                _restore_job.num_of_files_transferred == 0:
            raise Exception(f'Restore is not verified')
        return True

    @test_step
    def verify_tenant_on_boarding(self):
        """
            Method to verify that on the on-boarding of the tenant
            and after activation of the Dynamics 365 Solution
            The required Dynamics 365 plans were successfully created

            It also picks one of the plan and uses that for further test.
        """
        self._admin_console.navigator.navigate_to_plan()
        self.verify_dynamics365_plans_creation_for_tenant()

    @test_step
    def on_board_tenant(self):
        """
            On- Board the newly created tenant.
            Enable new configuration for Dynamics 365
        """
        if not self.__is_react:
            self.hub_dashboard = Dashboard(self._admin_console, self.service)
            self.hub_dashboard.click_get_started()
            self.hub_dashboard.choose_service_from_dashboard()
            self.hub_dashboard.click_continue()
            self.hub_dashboard.wait_for_creation_of_storage_and_plan()
            self.hub_dashboard.select_option_to_enable_region_based_storage(value='No')
        else:
            self.service_catalogue = ServiceCatalogue(self._admin_console, self.service)
            self.service_catalogue.start_dynamics365_trial()

    @test_step
    def select_dynamics_service(self):
        """Selects the dynamics 365 service from Service Catalogue"""
        self.service_catalogue.choose_service_from_service_catalogue(self.service.value, 'Dynamics 365')

    @test_step
    def delete_automation_tenant(self, tenant_name: str):
        """
            Method to deactivate and delete the tenants created on Metallic commcell
            for automation purposes.

            Arguments:
                tenant_name     (str)--     Name of the tenant to be deleted
        """
        if not tenant_name:
            tenant_name = self.tenant_name
        self._hub_utils.deactivate_tenant(tenant_name=tenant_name)
        self._hub_utils.delete_tenant(tenant_name=tenant_name)

    @test_step
    def wait_for_index_playback(self):
        """
            Wait for the Index Playback for Metallic environment
        """
        self.dynamics365_apps.select_client_restore()
        success = False
        while not success:
            time.sleep(60)
            success = self.dynamics365_apps.is_playback_completed()
            self._admin_console.refresh_page()
        self.navigate_to_client()

    @test_step
    def verify_point_in_time_restore(self, restore_dict: dict = None,
                                     restore_type: Enum = None,
                                     dest_instance: str = str(),
                                     record_option: Enum = None,
                                     is_instance: bool = False,
                                     restore_level: str = None):
        """
        Performs PIT restore and verifies the job details
            :param restore_dict:
            :param restore_type:
            :param dest_instance:
            :param record_option:
            :param is_instance:
            :param restore_level:
            :return:
        """
        backup_job_details = self.dynamics365_apps.get_job_details(restore_dict["JobId"])
        year, month, date, start_time = self.dynamics365_apps.jobs.get_job_start_time(backup_job_details)
        self.navigate_to_client(client_name=self.tc_inputs["Name"])
        time_dict = {
            "Year": year,
            "Month": month,
            "Date": date,
            "Start Time": start_time
        }
        restore_dict.update(time_dict)
        restore_job_details = self.dynamics365_apps.run_point_in_time_restore(restore_dict,
                                                                              restore_type,
                                                                              dest_instance,
                                                                              record_option,
                                                                              is_instance,
                                                                              restore_level)
        if restore_job_details['Status'] not in \
                ["Committed", "Completed", "Completed w/ one or more errors"]:
            raise CVWebAutomationException('Job did not complete successfully')
        if restore_dict["ClientLevel"]:
            if restore_job_details["Successful Tables"] == restore_job_details["SelectedItems"]:
                self.log.info("Selected Tables were successfully restored using PIT restore feature")
            else:
                raise CVWebAutomationException("Selected Tables were not restored successfully. Please check.")
        else:
            if int(restore_job_details["No of files restored"]) == restore_job_details["SelectedItems"]:
                self.log.info("Selected Rows were successfully restored using PIT restore feature")
            else:
                raise CVWebAutomationException("Selected Rows were not restored successfully. Please check.")

    @test_step
    def validate_comparison_with_previous_versions(self, association_dict: dict, is_download: bool = False):
        """
        Validates the comparison of the association dictionary with the previous version

        association_dict (dict) -- Should contain the following information about the table records and versions

                association dict -- {
                                        "TableName": "Account",
                                        "EnvironmentName" : "cv-test",
                                        "PrimaryColumnValue" : "Row value of the primary column",
                                        "CompareVersions" : ["1.0","2.0"]
                                    }
        is_download (bool) -- Pass true if you want to download and verify the existence of records file
        """
        if association_dict:
            if not isinstance(association_dict["CompareVersions"], list):
                raise CVWebAutomationException("Please pass versions to compare in the form of list")
            comparison_data = self.dynamics365_apps.compare_versions_of_records(association_dict)
            if len(comparison_data["Attribute"]) == 0:
                raise CVWebAutomationException("There are no attributes which are changed in two versions")
            else:
                self.log.info("There are attributes which are changed in both the versions")
                self._admin_console.click_button("Close")
                self._admin_console.click_button("Close")
        if is_download:
            self.dynamics365_apps.download_properties(association_dict["PrimaryColumnValue"])