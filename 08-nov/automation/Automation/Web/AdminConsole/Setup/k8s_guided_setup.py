# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to getting started page

==============

    add_cluster()               --  Add cluster step

    add_application_group()     --  Add application group step

    select_plan()               --  Select Plan step

    validate_summary_step()     --  Validate summary step

    click_next()                --  Click next button

    click_finish()              --  Click finish button

    click_cancel()              --  Click on the Cancel button

    select_cluster()            --  Select cluster from dropdown

"""
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.K8s.application_groups import K8sAppGroup
from Web.AdminConsole.K8s.clusters import AddK8sCluster
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService, WebAction


class KubernetesSetup:
    """
    Class for Kubernetes Getting Started / Guided Setup wizard
    """

    def __init__(self, admin_console):
        """
        Setup Class initialization

        """
        self.admin_console = admin_console
        self.__wizard = Wizard(admin_console)
        self.__alert = Alert(admin_console)
        self.k8s_server = AddK8sCluster(admin_console)
        self.k8s_app_grp = K8sAppGroup(admin_console)

    @WebAction()
    def __get_first_plan_name(self):
        """Get first plan from the list"""
        return self.admin_console.driver.find_element(
            By.XPATH,
            "//div[contains(@class, 'wizard-step-body')]/div[contains(@class, 'MuiGrid-container')]" +
            "//ul/preceding-sibling::span"
        ).text

    @PageService()
    def click_next(self):
        """
        Click Next or Submit button
        """
        try:
            self.__wizard.click_next()
        except NoSuchElementException:
            self.__wizard.click_button(name="Submit")
        self.admin_console.wait_for_completion()

    @PageService()
    def click_finish(self):
        """
        Click finish button
        """
        self.__wizard.click_button(name=self.admin_console.props['summary.finish'])
        self.admin_console.wait_for_completion()

    @PageService()
    def exit_wizard(self):
        """Exit wizard by clicking on Cancel on wizard and warning tile if any"""
        self.__wizard.click_cancel()
        self.admin_console.click_button_using_text(value=self.admin_console.props['action.exitWizard'])
        self.__alert.check_error_message()

    @PageService()
    def add_cluster(self, **kwargs):
        """
        Add cluster step
        Kwargs:
            api_endpoint    (str)   --  API Server endpoint of cluster
            cluster_name    (str)   --  Name of cluster
            authentication  (str)   --  Authentication type
            service_account (str)   --  Service account name
            service_token   (str)   --  Service account token
        """

        api_endpoint = kwargs.get("api_endpoint")
        name = kwargs.get("cluster_name")
        authentication = kwargs.get("authentication")
        service_account = kwargs.get("service_account")
        service_token = kwargs.get("service_token")

        try:
            self.k8s_server.set_hostname(api_endpoint)
            self.k8s_server.set_servername(name)
            self.k8s_server.select_authentication(authentication)
            self.k8s_server.set_service_account(service_account)
            self.k8s_server.set_service_token(service_token)
            self.click_next()
            self.__alert.check_error_message()

        except Exception as exp:
            raise CVWebAutomationException(
                f'Unsuccessful add cluster step : [{exp}]'
            )

    @PageService()
    def add_application_group(self, **kwargs):
        """
        Add application group step
        Kwargs:
            name            (string)    --  Name of the application group
            backup_content  (list)      --  Backup content as applications
            filter_content  (list)      --  Filter content as applications
            intelli_snap     (bool)      --  To enable/disable intelli snap
            backup_filters  (list)      --  Backup filters to be applied
        """

        name = kwargs.get("app_group_name")
        backup_content = kwargs.get("backup_content")
        filter_content = kwargs.get("filter_content", None)
        intelli_snap = kwargs.get("intelli_snap", False)
        backup_filters = kwargs.get('backup_filters', None)

        try:
            self.k8s_app_grp.set_appgroup_name(name)
            if intelli_snap:
                self.k8s_app_grp.enable_snap()
            self.k8s_app_grp.add_backup_content(backup_content)
            if filter_content:
                self.k8s_app_grp.add_filter_content(filter_content)
            if backup_filters:
                self.k8s_app_grp.add_backup_filters(backup_filters)
            self.click_next()
            self.__alert.check_error_message()

        except Exception as exp:
            raise CVWebAutomationException(
                f'Unsuccessful add application group step : [{exp}]'
            )

    @PageService()
    def select_cluster(self, **kwargs):
        """Select cluster from dropdown
            Kwargs:
                 cluster_name       (str)   --  Name of the cluster to select
        """

        name = kwargs.get("cluster_name")
        try:
            self.k8s_app_grp.set_cluster(name)
            self.click_next()
            self.__alert.check_error_message()

        except Exception as exp:
            raise CVWebAutomationException(
                f'Unsuccessful select cluster step : [{exp}]'
            )

    @PageService()
    def select_plan(self, **kwargs):
        """
        Select plan from plan step
        Kwargs:
            plan_name   (str)   --  Name of the plan
        """

        plan_name = kwargs.get("plan_name", None)
        try:

            # Currently, Plan has to be selected even if one does not want to create app group
            # As a workaround, we have to select any plan in the list to proceed to next step
            # if we do not intend to create an app group
            # Hence, if the plan_name is Null, we will select the first plan in the list and proceed
            plan_name = plan_name or self.__get_first_plan_name()
            self.__wizard.fill_text_in_field(id='searchPlanName', text=plan_name)
            self.__wizard.select_plan(plan_name=plan_name)

            self.click_next()
            self.__alert.check_error_message()

        except Exception as exp:
            raise CVWebAutomationException(
                f'Unsuccessful add plan step : [{exp}]'
            )

    @PageService()
    def select_access_nodes(self, **kwargs):
        """
        Select access nodes from access node dropdown step
        Kwargs:
            access_nodes    (list)  --  List of access nodes to select
        """

        access_nodes = kwargs.get("access_nodes", None)
        try:
            if access_nodes:
                self.__wizard.select_drop_down_values(id="accessNodeDropdown", values=access_nodes)
            self.click_next()
            self.__alert.check_error_message()
        except Exception as exp:
            raise CVWebAutomationException(
                f'Unsuccessful select access node step : [{exp}]'
            )

    @PageService()
    def validate_summary_step(self, **kwargs):
        """
        Validate summary in summary step
        Kwargs:
            cluster_name    (str)   --  Name of the cluster
            app_group_name  (str)   --  Name of application group
            plan_name       (str)   --  Name of the plan
        """

        cluster_name = kwargs.get("cluster_name")
        app_group_name = kwargs.get("app_group_name")
        plan_name = kwargs.get("plan_name")

        summary_dict = {}
        status = True
        error_list = []

        for row in self.admin_console.driver.find_elements(By.CLASS_NAME, 'tile-row'):
            summary_dict.update(
                {
                    row.find_element(By.CLASS_NAME, 'tile-row-label').text: row.find_element(
                        By.CLASS_NAME,
                        'tile-row-value').text
                }
            )

        if summary_dict[self.admin_console.props['label.k8ClusterName']] != cluster_name:
            status = False
            displayed = summary_dict[self.admin_console.props['label.k8ClusterName']]
            error_list.append(
                f'Summary listing incorrect cluster name - Expected: [{cluster_name}] Displayed: [{displayed}]'
            )
        if summary_dict[self.admin_console.props['label.appGrpName']] != app_group_name:
            status = False
            displayed = summary_dict[self.admin_console.props['label.appGrpName']]
            error_list.append(
                f'Summary listing incorrect app group name - Expected: [{app_group_name}] Displayed: [{displayed}]'
            )
        if plan_name and (summary_dict[self.admin_console.props['title.planName']] != plan_name):
            status = False
            displayed = summary_dict[self.admin_console.props['title.planName']]
            error_list.append(
                f'Summary listing incorrect plan name - Expected: [{plan_name}] Displayed: [{displayed}]'
            )

        self.click_finish()
        self.__alert.check_error_message()

        if not status:
            raise CVWebAutomationException(
                f'Incorrect Summary: {error_list}'
            )
