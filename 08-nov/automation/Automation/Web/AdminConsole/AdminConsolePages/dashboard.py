# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Operations on admin console dashboard page

get_dash_pane_titles           -- Gets all the pane's titles present in dashboard page

access_details_page            -- Access details page of specified pane

get_page_title                 -- Gets title of the current page
"""
from selenium.webdriver.common.by import By

from enum import Enum
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.dialog import RModalDialog, RSecurity
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.callout import Callout


class OverviewDashboard(Enum):
    """Panes used in Overview Dashboard page"""
    pane_environment = "Environment"
    pane_needs_attentions = "Needs attention"
    pane_sla = "SLA"
    pane_jobs_in_last_24_hours = "Jobs in the last 24 hours"
    pane_health = "Health"
    pane_disk_space = "Storage space"
    pane_storage_usage = "Storage"
    pane_storage_data_retention = "Storage - data retention"
    pane_current_capacity_usage = "Current capacity"
    pane_last_week_backup_job_summary = "Last week job summary"
    pane_top_5_largest_servers = "Top 5 largest servers"

    # Entities present in different panes
    entity_file_servers = "FILE SERVERS"
    entity_servers = "SERVERS"
    entity_vms = "VMs"
    entity_laptops = "LAPTOPS"
    entity_users = "USERS"
    entity_infrastructures = "INFRA MACHINES"
    entity_jobs = "JOBS"
    entity_running = "RUNNING"
    entity_success = "SUCCESS"
    entity_failed = "FAILED"
    entity_events = "EVENTS"
    entity_disk_library = "DISK LIBRARY"
    entity_space_savings = "SPACE SAVINGS"


class ApplianceDashboard(Enum):
    """Panes used in Overview Dashboard page"""
    pane_environment = "Environment"
    pane_needs_attentions = "Needs attention"
    pane_system = "System"
    pane_hardware = "Hardware Component"
    pane_disk_space = "Disk space"
    pane_sla = "SLA"
    pane_jobs_in_last_24_hours = "Jobs in the last 24 hours"
    pane_current_capacity_usage = "Top 5 largest servers"

    # Entities present in different panes
    entity_appliances = "APPLIANCES"
    entity_servers = "SERVERS"
    entity_vms = "VMs"
    entity_critical_alerts = "CRITICAL ALERTS"
    entity_infrastructures = "INFRASTRUCTURES"
    entity_jobs = "JOBS"
    entity_running = "RUNNING"
    entity_success = "SUCCESS"
    entity_failed = "FAILED"
    entity_critical_events = "CRITICAL EVENTS"


class VirtualizationDashboard(Enum):
    """Panes used in Overview Dashboard page"""
    pane_hypervisors = "Hypervisors"
    pane_vms = "VMs"
    pane_sla = "CommCell SLA"
    pane_jobs_in_last_24_hours = "Jobs in the last 24 hours"
    pane_last_week_backup_job_summary = "Last week job summary"
    pane_largest_hypervisors = "Largest hypervisors"
    # Entities present in different panes
    entity_protected = "PROTECTED"
    entity_not_protected = "NOT PROTECTED"
    entity_backed_up_with_error = "BACKED UP WITH ERROR"
    entity_running = "RUNNING"
    entity_success = "SUCCESS"
    entity_failed = "FAILED"
    entity_events = "EVENTS"


class OrchestrationDashboard(Enum):
    """Panes used in Orchestration Dashboard page"""
    header_databases = "Databases"
    header_file_servers = "File servers"
    header_applications = "Applications"
    header_vms = "VMs"
    # Panes present under different headers
    pane_overview = "Overview"
    pane_last_month_stats = "Last month stats"
    pane_replication_groups = "Replication groups"
    # Entities present in different panes
    entity_servers = "SERVERS"
    entity_clones = "CLONES"
    entity_cloud_migration = "CLOUD MIGRATIONS"
    entity_failover_runs = "FAILOVER RUNS"
    entity_file_servers = "FILE SERVERS"
    entity_live_mounts = "LIVE MOUNTS"
    entity_vms = "VMs"


class Dashboard:

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
        """
        self.__admin_console = admin_console
        self.driver = admin_console.driver

    """Operations on dashboard page"""

    @WebAction()
    def _read_dash_pane_titles(self, header=None):
        """Get panels titles present in dashboard page
        Args:
            header  (String) :   Header name for different dashboard sections
        Returns:
            List with all pane titles
        """
        if header:
            xpath = f"//span[contains(.,'{header}') and contains(@data-ng-bind," \
                    f"'orchestrationPaneCtrl.paneData." \
                    f"title.text')]/../../..//*[contains(@class, 'dash-pane-header-title')]"
        else:
            xpath = "//*[contains(@class, 'dash-pane-header-title')]"
        return [each_panel.text for each_panel in self.driver.find_elements(By.XPATH, xpath)]

    @WebAction()
    def _read_headers(self):
        """Get header names"""
        xpath = "//*[contains(@data-ng-bind, 'orchestrationPaneCtrl.paneData.title.text')]"
        return [each_header.text for each_header in self.driver.find_elements(By.XPATH, xpath)]

    @WebAction()
    def _get_page_title(self):
        """Get page title"""
        title_obj = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'page-title')]")
        if not title_obj:
            title_obj = self.driver.find_elements(By.XPATH, "//h2")
        if not title_obj:
            # self.__admin_console.switch_to_react_frame()
            title_obj = self.driver.find_elements(By.CLASS_NAME, "grid-title")

        return title_obj[0].text

    @WebAction()
    def _access_details_page(self, pane_name=None, entity_name=None, header_name=None):
        """
        Click on details page specified pane
        """
        if header_name:
            if entity_name:
                xpath = f"//span[contains(.,'{header_name}') and contains(@data-ng-bind," \
                        f"'orchestrationPaneCtrl.paneData.title.text')]/../../.." \
                        f"//cv-reports-pane-header/span/*[text() = '{pane_name}']/../../../.." \
                        f"//span[text() = '{entity_name}']"
            elif pane_name:
                xpath = f"//span[contains(.,'{header_name}') and contains(@data-ng-bind," \
                        f"'orchestrationPaneCtrl.paneData.title.text')]/../../.." \
                        f"//cv-reports-pane-header/span/*[text() ='{pane_name}']"
            else:
                xpath = f"//span[contains(text(),'{header_name}') and contains(@data-ng-bind," \
                        f"'orchestrationPaneCtrl.paneData.title.text')]"
        else:
            if entity_name:
                xpath = "//cv-reports-pane-header/span/*[text() = '{0}']/../../.." \
                        "//span[text() = '{1}']" \
                    .format(pane_name, entity_name)
            else:
                xpath = "//cv-reports-pane-header/span/*[text() = '{0}']".format(pane_name)
        self.driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def _access_dashboard(self, dashboard_type):
        """
        Click on dashboard header and select given dashboard type
        Args:
            dashboard_type  (String) :  name of dashboard to be accessed
        """
        self.driver.find_element(By.XPATH,
                                 f"//button[contains(@class,'btn btn-link dropdown-toggle')]").click()
        self.driver.find_element(By.XPATH,
                                 f"//a[contains(text(),'{dashboard_type}')]").click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_dash_pane_titles(self, dashboard_type=None):
        """Get dash pane tiles present in dashboard page"""
        return self._read_dash_pane_titles(dashboard_type)

    @PageService()
    def access_details_page(self, pane_name=None, entity_name=None, header_name=None):
        """
        Access details page of specified pane
        Args:
            pane_name        (String) : Name of the pane on which details page to be accessed
            entity_name      (String) : Name of the entity within pane
            header_name      (String) : Name of the header containing the pane
        """
        self._access_details_page(pane_name, entity_name, header_name)
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_page_title(self):
        """Get page title"""
        return self._get_page_title()

    @PageService()
    def navigate_to_given_dashboard(self, dashboard_type):
        """
        Navigate to respective dashboard page as given
        Args:
            dashboard_type  (String) :  name of dashboard to be accessed
        """
        self._access_dashboard(dashboard_type)

    @PageService()
    def get_header_and_dash_pane_titles(self):
        """
        Get headers and dash pane tiles present in dashboard page
        Returns:
            Dictionary with all header and pane titles
                Eg.-{header1 : [panes], header2 : [panes]}
        """
        orchestration_dict = {}
        headers = self._read_headers()
        for header in headers:
            panes = self._read_dash_pane_titles(header)
            orchestration_dict['header'] = panes
        return orchestration_dict


class ROverviewDashboard(Enum):
    """Panes used in Overview Dashboard page"""
    pane_environment = "Environment"
    pane_needs_attentions = "Needs attention"
    pane_sla = "SLA"
    pane_jobs_in_last_24_hours = "Jobs in the last 24 hours"
    pane_health = "Health"
    pane_disk_space = "Storage space"
    pane_storage_usage = "Storage"
    pane_current_capacity_usage = "Current capacity"
    pane_top_5_largest_servers = "Top 5 largest servers"
    pane_last_week_backup_job_summary = "Last week job summary"

    # Entities present in different panes
    entity_file_servers = "File servers"
    entity_servers = "Servers"
    entity_vms = "VMs"
    entity_laptops = "Laptops"
    entity_users = "Users"
    entity_infrastructures = "Infra machines"
    entity_jobs = "Jobs"
    entity_running = "Running"
    entity_success = "Success"
    entity_cwe = "CWE/CWW"
    entity_failed = "Failed"
    entity_events = "Events"
    entity_critical = "Critical"
    entity_warning = "Warning"
    entity_disk_library = "Disk library"
    entity_space_savings = "Space savings"


class EndpointDashboard(Enum):
    """Panes used in Overview Dashboard page"""
    pane_sla = "SLA"
    pane_jobs_in_last_24_hours = "Jobs in the last 24 hours"
    pane_last_week_backup_job_summary = "Last week job summary"
    pane_laptop_location = "Laptop location"

    # Entities present in different panes
    entity_laptops = "Laptops"
    entity_users = "Endpoint users"
    entity_critical_alerts = "Critical endpoint alerts"
    entity_running = "Running"
    entity_success = "Success"
    entity_failed = "Failed"
    entity_events = "Events"


class RVirtualizationDashboard(Enum):
    """Panes used in Overview Dashboard page"""
    title = "Overview"
    pane_hypervisors = "Hypervisors"
    pane_vms = "VMs"
    pane_sla = "Backup Health"
    pane_jobs_in_last_24_hours = "Jobs in the last 24 hours"
    pane_last_week_backup_job_summary = "Last week job summary"
    pane_largest_hypervisors = "Largest hypervisors"
    # Entities present in different panes
    entity_protected = "Protected"
    entity_not_protected = "Not protected"
    entity_backed_up_with_error = "Backed up with error"
    entity_running = "Running"
    entity_success = "Success"
    entity_failed = "Failed"
    entity_events = "Events"
    entity_validation_failed = "Validation failed"


class RDisasterRecoveryDashboard(Enum):
    pane_environment = "Environment"
    pane_needs_attention = "Needs attention"
    pane_last_month_stats = "Last Month's Stats"
    pane_replication_status = "Replication status"
    pane_sla = "SLA"
    pane_largest_hypervisors = "Largest hypervisors"
    # Entities present in different panes
    entity_servers = "Servers"
    entity_file_servers = "File servers"
    entity_vms = "VMs"
    entity_replication_groups = "Replication groups"
    entity_infrastructure_machines = "Infra machines"
    entity_events = "Events"
    entity_in_sync = "In sync"
    entity_sync_pending = "Sync pending"
    entity_never_synced = "Never synced"


class RDashboard:

    def __init__(self, admin_console: AdminConsole):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
        """
        self.__admin_console = admin_console
        self.driver = admin_console.driver
        self._dropdown = RDropDown(self.__admin_console)
        self._callout = Callout(self.__admin_console)

    """Operations on dashboard page"""

    @WebAction()
    def _get_pane_titles(self):
        """Get panels titles present in dashboard page
        Returns:
            List with all pane titles
        """
        xpath = "//span[contains(@class,'tile-header')]"
        return [each_panel.text for each_panel in self.driver.find_elements(By.XPATH, xpath)]

    @WebAction()
    def _get_entity_titles(self, pane_name, get_count=False, is_global=False):
        """Get entity titles present in given pane
        Args:
            pane_name        (String) : Name of the pane whose entities need to be listed
            get_count        (Boolean): return count along with title
            is_global        (Boolean): If global dashboard, returns count of individual service commcells as well
        Returns:
            List with all entity titles
        Example:
            with get_count = True
                {'File servers': '12', 'VMs': '44', 'Laptops': '2', 'Users': '1,549'}

            with get_count and is_global = True
                {'File servers': {'Total': '12', 'service2': '2', 'service3': '3', 'service7': '2', 'machine3': '1', 'routercs': '4'},
                'VMs': {'Total': '44', 'routercs': '44'}, 'Laptops': {'Total': '2', 'service3': '2'},
                'Users': {'Total': '1,549', 'machine3': '23', 'service7': '129', 'routercs': '257', 'service3': '552', 'service2': '588'}}
        """
        if get_count:
            container_xpath = (f"//*[contains(@class,'tile-header')]/*[text()='{pane_name}']"
                               f"/ancestor-or-self::span/../following-sibling::div//div[@class='kpi-tile']")
            containers = self.driver.find_elements(By.XPATH, container_xpath)
            container_info = {}
            for kpi in containers:

                if not kpi.find_elements(By.XPATH, ".//*[contains(@class,'kpi-title')]"):
                    return []

                title = kpi.find_element(By.XPATH, ".//*[contains(@class,'kpi-title')]")
                count = kpi.find_element(By.XPATH, ".//*[contains(@class,'kpi-subtitle')]")
                kpi_info = {}
                if is_global:
                    kpi_info['Total'] = count.text
                    # Dummy click to close callout
                    self.driver.find_element(By.XPATH, "//span[@class='dashboard-title']").click()
                    count.click()

                    callout_element = self.driver.find_elements(By.XPATH, "//div[@class='popover-body']")
                    if not callout_element:
                        self.__admin_console.log.error(f"No Callout opened for {title.text}")
                    else:
                        items = callout_element[0].find_elements(By.XPATH, ".//span")
                        i = 0
                        while i < len(items):
                            kpi_info[items[i].text] = items[i + 1].text
                            i += 2

                if kpi_info:
                    container_info[title.text] = kpi_info
                else:
                    container_info[title.text] = count.text

            return container_info

        xpath = "//*[contains(@class,'tile-header')]/*[text()=\"{}\"]/" \
                "ancestor-or-self::span/../" \
                "following-sibling::div/" \
                "descendant::*[contains(@class,'kpi-title')]".format(pane_name)

        return [entity.text for entity in self.driver.find_elements(By.XPATH, xpath)]

    @WebAction()
    def _get_page_title(self):
        """Get page title"""
        title_obj = self.driver.find_elements(By.XPATH, "//span[contains(@class, 'dashboard-title')]")
        if not title_obj:
            title_obj = self.driver.find_elements(By.XPATH, "//a[@role='tab' and @aria-selected='true']/span")
        if not title_obj:
            title_obj = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'page-title')]")
        if not title_obj:
            title_obj = self.driver.find_elements(By.XPATH, "//h2")
        if not title_obj:
            title_obj = self.driver.find_elements(By.CLASS_NAME, "grid-title")
        return title_obj[0].text

    @WebAction()
    def _access_details_page(self, pane_name=None, entity_name=None):
        """
        Click on details' page specified pane
        """
        if entity_name:
            xpath = "//*[contains(@class,'tile-header')]/*[text()=\"{}\"]/" \
                    "ancestor-or-self::span/../" \
                    "following-sibling::div/" \
                    "descendant::*[text()=\"{}\"]".format(pane_name, entity_name)
        else:
            xpath = "//*[contains(@class,'tile-header')]/*[text()=\"{}\"]".format(pane_name)
        self.driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def _access_dashboard(self, dashboard_type):
        """
        Click on dashboard header and select given dashboard type
        Args:
            dashboard_type  (String) :  name of dashboard to be accessed
        """
        self._dropdown.select_drop_down_values(drop_down_id='dashboardDropdown', values=[dashboard_type])
        self.__admin_console.wait_for_completion()

    @WebAction()
    def _perform_dashboard_actions(self, action):
        """
        Clicks on More button to perform actions like Edit/Clone/Security/Delete/Revert
        Args:
            action (str) : Name of the action {Edit / Clone / Security / Delete / Revert }
        """
        self.driver.find_element(By.XPATH, "//div[@aria-label='More' and @role='button']").click()
        self.__admin_console.wait_for_completion()
        self.driver.find_element(By.XPATH, "//li[contains(@class,'menu-dropdown-item')]/div[text()='{}']".
                                 format(action)).click()

    @WebAction()
    def _get_dashboard_actions(self):
        """
        Clicks on More button to verify presence of actions like Edit/Clone/Security/Delete/Revert
        """
        self.driver.find_element(By.XPATH, "//div[@aria-controls='popup-menu']").click()
        self.__admin_console.wait_for_completion()
        actions = self.driver.find_elements(By.XPATH, "//li[contains(@class,'menu-dropdown-item')]/div[2]")
        self.driver.find_element(By.XPATH, "//div[@id='popup-menu']").click()
        return [each_panel.text for each_panel in actions]

    @PageService()
    def save(self):
        """
        Save the dashboard
        """
        self.driver.find_element(By.XPATH, "//div[text()='Save']").click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def _get_customer_action_pending_count(self):
        """
        get customer action pending count from dashboard SLA tile
        Returns:
            count(INT) : count of custom action pending
        """
        xpath = "//td[@title='Customer action pending']/..//span"
        custom_pending = self.driver.find_elements(By.XPATH, xpath)
        if custom_pending:
            return int(custom_pending[0].text)
        else:
            return 0

    @WebAction()
    def _get_msp_action_pending_count(self):
        """
        get the MSP action pending from dashboard SLA tile
        Returns:
            count(INT) : count of MSP action pending
        """
        xpath = "//td[@title='Service provider action pending']/..//span"
        msp_pending = self.driver.find_elements(By.XPATH, xpath)
        if msp_pending:
            return int(msp_pending[0].text)
        else:
            return 0

    @PageService()
    def get_customer_action_pending_count(self):
        """
        get the customer action pending from Sla tile
        Returns:
            count (INT) : count of customer action pending
        """

        customer_action = self._get_customer_action_pending_count()
        return customer_action

    @PageService()
    def get_msp_action_pending_count(self):
        """
        get the msp action pending from sla tile
        Returns:
            count(INT) : msp action pending count
        """
        msp_action = self._get_msp_action_pending_count()
        return msp_action

    @PageService()
    def remove_tile(self, tile_name):
        """
        Removes tile in edit mode
        Args:
            tile_name  (String) :  name of tile to be removed from the dashboard
        """
        self.driver.find_element(By.XPATH, f"//span[contains(@class,'tile-header') and text()='{tile_name}']/"
                                           "ancestor::div[contains(@class,'react-grid-item')]/span").click()

    @PageService()
    def get_dash_pane_titles(self):
        """Get dash pane tiles present in dashboard page"""
        return self._get_pane_titles()

    @PageService()
    def access_details_page(self, pane_name=None, entity_name=None):
        """
        Access details page of specified pane
        Args:
            pane_name        (String) : Name of the pane on which details page to be accessed
            entity_name      (String) : Name of the entity within pane
        """
        self._access_details_page(pane_name, entity_name)
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_page_title(self):
        """Get page title"""
        return self._get_page_title()

    @PageService()
    def get_all_dashboards(self):
        """
        Lists all the Dashboards
        Returns:
            dlist List(str) : List of all dashboards
        """
        dlist = self._dropdown.get_values_of_drop_down('dashboardDropdown')
        return dlist

    @PageService()
    def navigate_to_given_dashboard(self, dashboard_type):
        """
        Navigate to respective dashboard page as given
        Args:
            dashboard_type  (String) :  name of dashboard to be accessed
        """
        self._access_dashboard(dashboard_type)

    @PageService()
    def get_pane_and_entity_titles(self, get_count=False, is_global=False):
        """
        Get Panes and Entities present in dashboard page
        Args:
            get_count (Boolean): return count along with title
            is_global (Boolean): If global dashboard, returns count of individual service commcells as well
        Returns:
            Dictionary with all panes and entities
            Eg: {pane1 : [entities], pane2:[entities]}

            with get_count = True
                {'Environment': {'File servers': '12', 'VMs': '44', 'Laptops': '2', 'Users': '1,549'},
                'Needs attention': {'Servers': '3', 'Infra machines': '0', 'Jobs': '1'}, 'SLA': {},
                'Jobs in the last 24 hours': {'Running': '21', 'Success': '44', 'Failed': '3', 'Events': '0'},
                'Health': {'Critical': '29', 'Warning': '7'}, 'Current capacity': {}, 'Storage space': {},
                'Top 5 largest servers': {}, 'Storage': {'Disk library': '486.33 GB', 'Space savings': '70.5%'}
                }
            with get_count and is_global = True
                {'Environment': {'File servers': {'Total': '12', 'service2': '2', 'service3': '3', 'service7': '2', 'machine3': '1', 'routercs': '4'},
                'VMs': {'Total': '44', 'routercs': '44'}, 'Laptops': {'Total': '2', 'service3': '2'},
                'Users': {'Total': '1,549', 'machine3': '23', 'service7': '129', 'routercs': '257', 'service3': '552', 'service2': '588'}},
                'Needs attention': {'S....}}
        """
        pane_dict = {}
        panes = self._get_pane_titles()
        for pane in panes:
            entities = self._get_entity_titles(pane, get_count, is_global)
            pane_dict[pane] = entities
        return pane_dict

    @PageService()
    def get_dashboard_sla(self):
        """
        get admin console dashboard sla value
        """
        return self.driver.find_element(By.CLASS_NAME, 'dial-center-percent').text[:-1]

    @PageService()
    def clone_dashboard(self, dashboard_name):
        """
        Clones the dashboard
        Args:
            dashboard_name (str) : Name for the cloned dashboard
        """
        self._perform_dashboard_actions('Clone')
        clone_modal = RModalDialog(self.__admin_console)
        clone_modal.fill_text_in_field('dashboardName', dashboard_name)
        clone_modal.click_submit()
        self.__admin_console.wait_for_completion()
        self.save()

    @PageService()
    def dashboard_security(self, user):
        """
        Associate a user or a user group that can view this dashboard.
        """
        self._perform_dashboard_actions('Security')
        security = RSecurity(self.__admin_console)
        security.associate_permissions(user)

    @PageService()
    def delete_dashboard(self):
        """
        Deletes the given dashboard
        """
        self._perform_dashboard_actions('Delete')
        delete_panel = RPanelInfo(self.__admin_console)
        delete_panel.click_button('Yes')

    @PageService()
    def edit_dashboard(self):
        """ Edit dashboard"""
        self._perform_dashboard_actions('Edit')

    @PageService()
    def revert_dashboard(self):
        """ Revert dashboard"""
        self._perform_dashboard_actions('Revert')
        revert_panel = RPanelInfo(self.__admin_console)
        revert_panel.click_button('Yes')

    @PageService()
    def get_dashboard_actions(self):
        """ Get dashboard actions list """
        actions = self._get_dashboard_actions()
        return actions

    ## Methods for Global Overview Dashboard ##

    @PageService()
    def open_callout(self, pane_name: str, entity_name: str) -> None:
        """ Open callout for given entity in the pane on global dashboard page
        
        Args:
            pane_name (str) : name of the pane
            entity_name (str) : name of the entity

        Example:
            open_callout(ROverviewDashboard.pane_environment.value, ROverviewDashboard.entity_file_servers.value)
        """
        self.access_details_page(pane_name, entity_name)  # clicking on entity opens callout

    @PageService()
    def available_commcells(self, pane_name: str, entity_name: str) -> dict:
        """ Get available commcells from callout
        
        Args:
            pane_name (str) : name of the pane
            entity_name (str) : name of the entity

        Returns:
            dict : {commcell_name_1 : 'count_1', commcell_name_2 : 'count_2', ...}

        Example:
            available_commcells(ROverviewDashboard.pane_environment.value, ROverviewDashboard.entity_file_servers.value)
        """
        self.open_callout(pane_name, entity_name)
        return self._callout.get_entities_count()

    @PageService()
    def click_on_commcell_from_callout(self, commcell_name: str, pane_name: str = None,
                                       entity_name: str = None) -> None:
        """ 
        Method to click on a commcell from the callout 
        
        Args:
            commcell_name (str) : name of the commcell
            pane_name (str) : name of the pane (optional)
            entity_name (str) : name of the entity (optional)
        """
        if pane_name and entity_name:
            self.open_callout(pane_name, entity_name)
        self._callout.perform_action(commcell_name)
