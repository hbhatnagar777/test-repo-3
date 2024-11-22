# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
** This is a protected class and should not be inherited directly. Use AdminConsole class. **
This module provides the function or operations that can be performed on the
Admin page on the AdminConsole

Class:

    _Navigator() -> AdminConsoleBase() -> object()

Functions:

navigate_to_hypervisors()               -- select and navigate to the *hypervisors* page
navigate_to_servers()                   -- select and navigate to the *servers* page
navigate_to_server_groups()             -- select and navigate to the *server groups* page
navigate_to_alerts()                    -- select and navigate to the *alerts* page
navigate_to_virtual_machines()          -- select and navigate to the *VMs* page
navigate_to_vm_groups()                 -- select and navigate to the *VMs groups* page
navigate_to_jobs()                      -- select and navigate to the *jobs* page
navigate_to_events()                    -- select and navigate to the *events* page
navigate_to_storage_policies()          -- select and navigate to the *storage policies* page
navigate_to_storage_targets()           -- select and navigate to the *storage targets* page
navigate_to_storage_pools()             -- select and navigate to the *storage pools* page
navigate_to_arrays()                    -- select and navigate to the *array* page
navigate_to_index_servers()             -- select and navigate to the *index servers* page
navigate_to_media_agents()              -- select and navigate to the *media agents* page
navigate_to_network_stores()            -- select and navigate to the *network stores* page
navigate_to_companies()                 -- select and navigate to the *companies* page
navigate_to_users()                     -- select and navigate to the *users* page
navigate_to_user_groups()               -- select and navigate to the *user groups* page
navigate_to_roles()                     -- select and navigate to the *roles* page
navigate_to_identity_servers()          -- select and navigate to the *identity servers* page
navigate_to_global_exceptions()         -- select and navigate to the *global exceptions* page
navigate_to_plugins()                   -- select and navigate to the *plugins* page
navigate_to_license()                   -- select and navigate to the *license* page
navigate_to_theme()                     -- select and navigate to the *theme* page
navigate_to_email_templates()           -- select and navigate to the *email template* page
navigate_to_navigation()                -- select and navigate to the *navigation* page
navigate_to_operation_window()          -- select and navigate to the *backup window* page
navigate_to_metrics_reporting()         -- select and navigate to the *metrics reporting* page
navigate_to_snmp()                      -- select and navigate to the *snmp* page
navigate_to_additional_settings()       -- select and navigate to the *settings* page
navigate_to_access_control()            -- select and navigate to the *access control* page
navigate_to_data()                      -- select and navigate to the *data* page
navigate_to_maintenance()               -- select and navigate to the *maintenance* page
navigate_to_certificate_administration()-- select and navigate to the *certificate
                                            administration* page
navigate_to_credential_manager()        -- select and navigate to the *credential manager* page
navigate_to_schedule_policies()         -- select and navigate to the *schedule policies* page
navigate_to_subclient_policies()        -- select and navigate to the *subclient policies* page
navigate_to_plan()                      -- select and navigate to the *plan* page
navigate_to_home()                      -- select and navigate to the *home* page
navigate_to_network()                   -- select and navigate to the *network* page
navigate_to_getting_started()           -- select and navigate to the *getting started* page
navigate_to_dashboard()                 -- select and navigate to the *dashboard* page
navigate_to_commcell()                  -- select and navigate to the *commcell* page
navigate_to_windows_servers()           -- select and navigate to the *windows servers* page
navigate_to_unix_servers()              -- select and navigate to the *unix servers* page
navigate_to_NAS_servers()               -- select and navigate to the *nas servers* page
navigate_to_devices()                   -- select and navigate to the *devices* page
navigate_to_devices_edgemode()          -- select and navigate to the *devices* page in edge mode as enduser
navigate_to_db_instances()              -- select and navigate to the *db instances* page
navigate_to_archiving()                 -- select and navigate to the *archiving* page
navigate_to_archivingv2()               -- select and navigate to the *archiving* page on metallic adminconsole
navigate_to_office365()                 -- select and navigate to the *office365* page
navigate_to_salesforce()                -- select and navigate to the *salesforce* page
navigate_to_exchange()                  -- select and navigate to the *exchange* page
navigate_to_sharepoint()                -- select and navigate to the *sharepoint* page
navigate_to_cloud_apps()                -- select and navigate to the *cloud apps* page
navigate_to_devops()                    -- select and navigate to the *devops* page
navigate_to_activedirectory             -- select and navigate to the active direcotry page
navigate_to_oracle_ebs()                -- select and navigate to the *oracle ebs* page
navigate_to_replication_targets()       -- select and navigate to the *replication target* page
navigate_to_replication_groups()        -- select and navigate to the *replication groups* page
navigate_to_replication_monitor()       -- select and navigate to the *replication monitor* page
navigate_to_reports()                   -- select and navigate to the *reports* page
navigate_to_recovery_groups()           -- select and navigate to the *recovery groups* page
navigate_to_life_cycle_policies()       -- select and navigate to the *lifecycle policies* page
navigate_to_governance_apps()           -- select and navigate to the *Governance apps* page
navigate_to_workflows()                 -- select and navigate to the *Workflows* page
navigate_to_approvals()                 -- select and navigate to the *Approvals* page
navigate_to_k8s_clusters()              -- select and navigate to the kubernetes "Clusters" page
navigate_to_k8s_appgroup()              -- select and navigate to the kubernetes "Application groups" page
navigate_to_k8s_applications()          -- select and navigate to the kubernetes "Application" page
navigate_to_disk_storage()              -- select and navigate to the Disk Storage page
navigate_to_cloud_storage()             -- select and navigate to the Cloud Storage page
navigate_to_tape_storage()              -- select and navigate to the Tape Storage page
navigate_to_air_gap_protect_storage()   -- select and navigate to the Air Gap Protect Storage page
navigate_to_hyperscale_storage()        -- select and navigate to the HyperScale storage page
navigate_to_dynamics365()               -- select and navigate to the Dynamics 365 "Application" page
navigate_to_my_data()                   -- select and navigate to the My Data Page under Web Console node
navigate_to_tags()                      -- select and navigate to the *tags* page
navigate_to_dips()                      -- select and navigate to the DIPs page
navigate_to_topologies                  -- select and navigate to the Network page
navigate_to_webconsole_monitoring()     -- select and navigate to webconsole monitoring page
navigate_to_unusual_file_activity()     -- select and navigate to unusual file activity page
navigate_to_service_catalog()           -- select and navigate to service catalog page on the cloud side
navigate_to_service_catalogue()         -- select and navigate to service catalog page on the metallic side
logout()                                -- sign the current user out of the AdminConsole
switch_to_activate_tab()                -- In getting started page, switch to activate tab
add_entity_from_search_bar()            -- add entity from global search using /ADD functionality
navigate_from_global_search()           -- navigate to a page using GOTO from global search
manage_entity_from_search_bar()         -- perform TAB entity actions from global search bar
get_category_global_search()            -- search entity from global search bar and return search result categories
navigate_to_usage                       -- Navigates to the usage page
navigate_to_backup_schedules()          -- select and navigate to the *Backup Schedules* page
navigate_to_risk_analysis()             -- Navigates to the Risk Analysis page
switch_risk_analysis_tabs()             -- Switches to the respective Risk Analysis Tab

"""
import time
from collections import OrderedDict

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Do not remove this import. Even though it is recognized as unused, it is being used inside an eval()
from selenium.webdriver.common.keys import Keys
from Web.AdminConsole.TeerHelpers.icons import get_icon_name
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (
    WebAction,
    PageService
)
from AutomationUtils import config

_CONSTANTS = config.get_config()


class _Navigator:
    """
    ** This is a protected class and should not be inherited directly **
    This module provides the navigator function or operations that can be performed on the
    Admin page on the AdminConsole.
    """

    def __init__(self, admin_console):
        """
        Initializes the properties of the class for the selected locale

        Args:
            admin_console  (AdminConsole):    instance of the AdminConsole class

        """
        self.admin_console = admin_console
        self.driver = admin_console.driver
        self.admin_console.load_properties(self)
        self.xpath = "//*[@id='side-nav-wrapper']"
        # Performance Stats
        self.start_time_load = None
        self.end_time_load = None
        from Web.AdminConsole.Components.panel import RDropDown
        self.dropdown = RDropDown(self.admin_console)

    @WebAction()
    def __search_navigation(self, nav):
        """
        Searches for a given nav bar element by the href
        Args:
            nav (str): string to search
        """
        global_search = self.driver.find_element(By.XPATH, "//input[@id='nav-search-field']")
        if not global_search.is_displayed():
            self.driver.find_element(
                By.XPATH, "//div[contains(@class, 'hamburger-menu')]/button"
            ).click()
            time.sleep(4)
        global_search.send_keys(Keys.CONTROL + "a")
        global_search.send_keys(Keys.DELETE)
        global_search.send_keys(nav)

    @WebAction()
    def __access_by_id(self, nav_id):
        """
        Access by id
        Args:
            nav_id (str): id to acess
        """
        self.driver.find_element(
            By.XPATH, f"//nav[contains(@class, 'nav side-nav navigation')]//a[@id='{nav_id}']/span"
        ).click()

    @WebAction()
    def __generic_access_by_id(self, generic_id):
        """
        Access by id
        Args:
            generic_id (str): id to acess
        """
        elem = self.driver.find_elements(By.XPATH, f'//*[@id="{generic_id}"]')
        if elem is None:
            return False
        self.driver.find_elements(By.XPATH, f'//*[@id="{generic_id}"]').click()
        return True

    @WebAction()
    def __access_by_link(self, href):
        """
        Access by link
        Args:
            href: link text to acess
        """
        self.driver.find_element(By.XPATH, f"//a[@href='#/{href}']/span").click()

    @WebAction()
    def __access_by_title(self, title: str, parents: list[str] = None) -> None:
        """
        Clicks a nav list item using link title name

        Args:
            title   (str)   -   the Nav item's name or title
            parents (list)  -   List of parent navs under which this nav is to be clicked
                                (for separating ambiguous navs with same name, but different hierarchy)
        """
        parents_xpath = ""
        if parents:
            parents_xpath = ' or '.join([f"@title='{parent_title}'" for parent_title in parents])
            parents_xpath = f"//a[{parents_xpath}]"
        try:
            self.driver.find_element(By.XPATH, f"{self.xpath}{parents_xpath}//a[@title='{title}']").click()
        except NoSuchElementException:
            self.driver.find_element(
                By.XPATH, f"{self.xpath}{parents_xpath}/following-sibling::*//a[@title='{title}']").click()

    @WebAction()
    def __access_tile_by_title(self, title: str) -> None:
        """
        Access tile by its title

        Args:
            title   (str)   -   the tile's title or name
        """
        self.driver.find_element(
            By.XPATH, f"//a[contains(@id, 'tileMenuSelection') and contains(., '{title}')]"
        ).click()

    @WebAction()
    def __search_result_category(self) -> dict:
        """
        Returns global search result categories and list of entities listed for each category
            e.g. result = {'Server groups': ['test', 'test_automatic']}
        """
        result = {}
        categories = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'MuiAutocomplete-popper')]"
                                                       "//div[contains(@class,'MuiListSubheader-root "
                                                       "MuiListSubheader-gutters')]")
        for category in categories:
            entities = category.find_elements(By.XPATH,"./following-sibling::ul//a")
            result[category.text] = [entity.text for entity in entities]
        return result

    @WebAction()
    def __click_navigation_button(self):
        """
        Expand the navigation button
        """
        if self.admin_console.check_if_entity_exists(
                "xpath",
                "//nav[@id='left-side-nav' and contains(@class,'collapsed')]"
        ):
            navigation_button_xpath = "//*[contains(@class, 'hamburger-menu') or contains(@class, 'hamburguer-icon')]"
            navigation_button = self.driver.find_element(By.XPATH, navigation_button_xpath)
            navigation_button.click()

    @PageService()
    def search_nav_by_id(self, nav, nav_id):
        """
        Searches for a given nav bar element by the id
        Args:
            nav (str): string to search
            nav_id (str) : id of element to navigate
        """
        self.__click_navigation_button()
        self.__search_navigation(nav)
        self.start_time_load = time.time()
        self.admin_console.clear_perfstats()
        self.__access_by_id(nav_id)
        self.admin_console.wait_for_completion()
        self.end_time_load = time.time()

    @PageService()
    def __search_navs(self, nav, href):
        """
        Searches for a given nav bar element by the href
        Args:
            nav: string to search
            href: link text to access
        """
        self.__click_navigation_button()
        self.__search_navigation(nav)
        self.start_time_load = time.time()
        self.admin_console.clear_perfstats()
        self.__access_by_link(href)
        self.admin_console.wait_for_completion()
        self.end_time_load = time.time()

    @WebAction()
    def _click_home_icon(self):
        """ Method to click on home icon """
        home_icon = self.driver.find_element(By.XPATH, "//div[@class='logo-bar-default']")
        home_icon.click()

    @WebAction()
    def _click_user_settings_drop_down(self):
        """ Method to expand user settings drop down """
        user_settings_drop_down = self.driver.find_element(By.XPATH,
                                                           "//div[@class='header-user-settings-anchor']")
        user_settings_drop_down.click()
        self.admin_console.wait_for_completion()

    @WebAction()
    def _click_logout(self):
        """ Method to click on logout option in user settings drop down"""
        logout = self.driver.find_element(By.XPATH, "//*[@id='user-header-logout']")
        logout.click()
        self.admin_console.wait_for_completion()

    @WebAction()
    def _navigate_back_to_login_page(self):
        """ Method to navigate back to login page from post logout screen """
        back_link = self.driver.find_element(By.XPATH, "//div[@class='links']/a[1]")
        back_link.click()
        self.admin_console.wait_for_completion()

    @WebAction()
    def __read_company_switcher_text(self):
        """ Method to get the text from company switcher"""
        company_switcher = self.driver.find_elements(By.ID, "//div[@id='header-company-dropdown']//p")
        if company_switcher:
            return company_switcher[0].text.strip()

    @WebAction()
    def __read_entire_left_nav(self, parent_elem=None) -> dict:
        """
        Method to read all the nav items structure using recursion

        Args:
            parent_elem (WebElement)    -   web element to limit scope of recursion

        Returns:
            nav_tree    (dict)  -   the left navs tree structure as nested dicts
        """
        if parent_elem is None:
            parent_elem = self.driver.find_element(By.ID, "side-nav-wrapper")
        nav_tree = {}
        same_level_nav_xpath = "(.//li[@class='nav-item'])[1]/../*"
        sub_nav_xpath = ".//div[contains(@class, 'collapse in')]"
        for nav_item_elem in parent_elem.find_elements(By.XPATH, same_level_nav_xpath):
            nav_link = nav_item_elem.find_element(By.XPATH, './/a[1]')
            nav_title = nav_link.get_attribute('title')
            nav_href = nav_link.get_attribute('href')
            sub_nav_container = nav_item_elem.find_elements(By.XPATH, sub_nav_xpath)
            if sub_nav_container:
                nav_tree.update({
                    nav_title: self.__read_entire_left_nav(sub_nav_container[0])
                })
            else:
                nav_tree.update({
                    nav_title: nav_href
                })
        return nav_tree

    @WebAction()
    def __entity_not_visible(self):
        """

        :return:
        """
        try:
            self.driver.find_element(By.XPATH, "//span[contains(text(),'No items found')]")
            return True
        except NoSuchElementException:
            self.admin_console.log.info("Entity is visible")
            return False

    @PageService()
    def check_if_element_exists(self, nav):
        """ Method to check if element is visible in navigation bar

        Args:
            nav (str): string to search
        """
        self.__search_navigation(nav)
        self.admin_console.wait_for_completion()
        self.admin_console.unswitch_to_react_frame()
        if self.__entity_not_visible():
            return False
        return True

    @PageService()
    def access_nav_route(self, nav_route: str, wait: bool = True) -> dict:
        """
        Method to access any nav route

        Args:
            nav_route (str): route to the nav seperated by '/'
                            example: 'Protect/Virtualization/Overview', 'Data Insights/Recovery', 'Jobs'
            wait    (bool):  waits for the nav route page to load if True

        Returns:
            nav_search_result   (dict): nested dict describing nav hierarchy visible after search
            example:
            {
                'Cleanroom': {
                    'Targets': 'href_url_of_that_link',
                    ...
                },
                'Replication groups': {
                    'target': 'href_url_of_that_link'
                },
                'Targets': 'href_url'
            }
        """
        from .alert import Alert
        self.__click_navigation_button()
        nav_route = nav_route.split('/')
        self.__search_navigation(nav_route[-1])
        search_result = self.__read_entire_left_nav()
        try:
            if len(nav_route) > 1:
                if nav_route[-1] in nav_route[:-1]:
                    # this is super ambiguous case where same nav name for child and parent
                    # this happens when tile or tab name is same as the page's name
                    # we send control flow to except block which handles the tile/tab access case
                    raise NoSuchElementException('ambiguous case, to be handled by except block')
                # to avoid duplicate navs case, use parent hierarchy to avoid accessing wrong but same name nav
                self.__access_by_title(nav_route[-1], nav_route[:-1])
            elif nav_route[-1] in search_result:
                self.__access_by_title(nav_route[-1])
            else:
                raise CVWebAutomationException(f"Nav route {nav_route} is not accessible!")
            if wait:
                try:
                    self.admin_console.wait_for_completion()
                    Alert(self.admin_console).check_error_message(5)
                except TimeoutException:
                    raise CVWebAutomationException(f"Nav route {nav_route} failed to load properly!")
            return search_result
        except NoSuchElementException:
            if len(nav_route) > 1:
                # case where last route elem is tab or tile link requiring click from parent page
                # so it is the parent of this route that we must access using left nav
                if len(nav_route) > 2:
                    # to avoid case where even parent nav route has duplicate
                    self.__access_by_title(nav_route[-2], nav_route[:-2])
                else:
                    self.__access_by_title(nav_route[-2])
                self.admin_console.wait_for_completion()
                try:
                    self.__access_tile_by_title(nav_route[-1])
                except:
                    self.admin_console.access_tab(nav_route[-1])
                if wait:
                    try:
                        self.admin_console.wait_for_completion()
                        Alert(self.admin_console).check_error_message(5)
                    except TimeoutException:
                        raise CVWebAutomationException(f"Nav route {nav_route} failed to load properly!")
                return search_result
        raise CVWebAutomationException(f"Nav route {nav_route} is not accessible!")

    @PageService()
    def check_if_id_exists(self, nav_id):
        """ Method to check if id is present in the source code

        Args:
            nav_id (str): string to search
        """
        try:
            self.driver.find_element(By.XPATH, f'//*[@id="{nav_id}"]')
            return True
        except NoSuchElementException:
            self.admin_console.log.info(nav_id + " is not present")
            return False

    def navigate_to_virtualization(self):
        """
        Navigates to Virtualization page"""
        self.search_nav_by_id(self.admin_console.props['label.virtualization'], 'navigationItem_vsa')

    def navigate_to_hypervisors(self):
        """
        Navigates to hypervisors page
        """
        self.navigate_to_virtualization()
        self.admin_console.access_tab(self.admin_console.props['label.nav.hypervisors'])

    def navigate_to_server_groups(self):
        """
        Navigates to server groups page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.serverGroups'], "navigationItem_serverGroups"
        )

    def navigate_to_service_commcell(self):
        """Function to navigate to service commcell page"""
        self.search_nav_by_id("Service CommCells", "navigationItem_serviceCommcells")

    def navigate_to_servers(self):
        """
        Navigates to active servers page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.clients'], "navigationItem_clientGroupDetails"
        )

    def navigate_to_file_servers(self):
        """
        Navigates to file servers page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.serversDashboard'], "navigationItem_fsServersList"
        )

    def navigate_to_alerts(self):
        """
        Navigates to alerts page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.alerts'], "navigationItem_triggeredAlerts"
        )

    def navigate_to_virtual_machines(self):
        """
        Navigates to VMs page
        """
        self.navigate_to_virtualization()
        self.admin_console.access_tab(self.admin_console.props['label.nav.vms'])

    def navigate_to_vm_groups(self):
        """
        Navigates to VM groups page
        """
        self.navigate_to_virtualization()
        self.admin_console.access_tab(self.admin_console.props['label.nav.vmGroups'])

    def navigate_to_jobs(self):
        """
        Navigates to jobs page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.jobs'], 'navigationItem_activeJobs')

    def navigate_to_network(self):
        """
        Navigates to Network page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.network'], "navigationItem_network")

    def navigate_to_network_topologies(self):
        """
        Navigate to topologies : Tenant admin mode
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.network'], "navigationItem_NetworkTopology"
        )

    def navigate_to_events(self):
        """
        Navigates to events page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.events'], "navigationItem_events")

    def navigate_to_storage_pools(self):
        """
        Navigates to storage pools page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.storagePool'], "navigationItem_mstoragePool"
        )

    def navigate_to_arrays(self):
        """
        Navigates to Arrays page
        """
        self.navigate_to_infrastructure()
        self.admin_console.access_tile('tileMenuSelection_arrays')

    def navigate_to_index_servers(self):
        """
        Navigates to Index Servers page
        """
        self.navigate_to_infrastructure()
        self.admin_console.access_tile('tileMenuSelection_indexServers')

    def navigate_to_media_agents(self, istenantadmin=False):
        """
        Navigates to Media Agents page
        """
        if istenantadmin:
            self.search_nav_by_id(
                self.admin_console.props['label.nav.mediaAgent'], "navigationItem_mediaAgent"
            )
        else:
            self.navigate_to_infrastructure()
            self.admin_console.access_tile('tileMenuSelection_mediaAgents')

    def navigate_to_resource_pool(self):
        """
        Navigates to Resource Pool page
        """
        self.navigate_to_infrastructure()
        self.admin_console.access_tile('tileMenuSelection_resourcePool')

    def navigate_to_network_stores(self):
        """
        Navigates to Media Agents page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.networkStore'], 'navigationItem_networkStore'
        )

    def navigate_to_infrastructure(self):
        """
        Navigates to Infrastructure
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.infrastructure'], "navigationItem_mInfrastructure"
        )

    def navigate_to_companies(self):
        """
        Navigates to Companies page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.subscriptions'], "navigationItem_subscriptions"
        )

    def navigate_to_company(self):
        """
        Navigates to Company page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.subscription'], "navigationItem_subscriptions"
        )

    def navigate_to_users(self):
        """
        Navigates to users page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.users'], 'navigationItem_users')

    def navigate_to_user_groups(self):
        """
        Navigates to user groups page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.userGroups'], "navigationItem_userGroups")

    def navigate_to_roles(self):
        """
        Navigates to roles page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.roles'], "navigationItem_roles")

    def navigate_to_identity_servers(self):
        """
        Navigates to Identity Servers page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.identityServers'], "navigationItem_identityServers"
        )

    def navigate_to_credential_manager(self):
        """
        Navigates to Credential Manager page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.credentialVault'],
                              'navigationItem_credentialManager')

    def navigate_to_key_management_servers(self):
        """
        Navigates to the Key management servers
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.keyManagement'], 'navigationItem_musers'
        )
        self.admin_console.access_tile("tileMenuSelection_keyManagement")

    def navigate_to_global_exceptions(self):
        """
        Navigates to Global exceptions page
        """
        self.navigate_to_systems()
        self.admin_console.access_tile("tileMenuSelection_globalExceptions")

    def navigate_to_plugins(self):
        """
        Navigates to Plugins page
        """
        self.navigate_to_systems()
        self.admin_console.access_tile("tileMenuSelection_plugin")

    def navigate_to_operation_window(self):
        """
        Navigates to Operation Window page
        """
        self.navigate_to_systems()
        self.admin_console.access_tile("tileMenuSelection_blackoutWindow")

    def navigate_to_metrics_reporting(self):
        """
        Navigates to Metrics Reporting page
        """
        self.navigate_to_systems()
        self.admin_console.access_tile('tileMenuSelection_metricsReporting')

    def navigate_to_metrics(self):
        """
        Navigates to Metrics reports
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.metrics'], "navigationItem_metrics")

    def navigate_to_snmp(self):
        """
        Navigates to snmp page
        """
        self.navigate_to_systems()
        self.admin_console.access_tile('tileMenuSelection_snmpv3')

    def navigate_to_additional_settings(self):
        """
        Navigates to Additional settings page
        """
        self.navigate_to_systems()
        self.admin_console.access_tile('tileMenuSelection_additionalSettings')

    def navigate_to_license(self):
        """
        Navigates to License page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.license'], "navigationItem_license")

    def navigate_to_theme(self):
        """
        Navigates to Theme page
        """
        self.navigate_to_customization()
        self.admin_console.access_tile("tileMenuSelection_customization")

    def navigate_to_email_templates(self):
        """
        Navigates to Email Templates page
        """
        self.navigate_to_customization()
        self.admin_console.access_tile("tileMenuSelection_emailTemplates")

    def navigate_to_navigation(self):
        """
        Navigates to navigation page
        """
        self.navigate_to_customization()
        try:
            self.admin_console.access_tile("tileMenuSelection_navigationPreferences")
        except NoSuchElementException:
            self.admin_console.click_by_xpath("//a[contains(@href,'navigationPreferences')]")

    def navigate_to_customization(self):
        """
        Navigates to customization
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.masterCustomization'], "navigationItem_masterCustomization"
        )

    def navigate_to_operations(self):
        """
        Navigates to Operations
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.operations'], "navigationItem_operation"
        )

    def navigate_to_access_control(self):
        """
        Navigates to Access control page
        """
        self.navigate_to_systems()
        self.admin_console.access_tile("tileMenuSelection_accessControl")

    def navigate_to_data(self):
        """
        Navigates to Data page
        """
        self.__search_navs(self.admin_console.props['label.nav.data'], "dataOptions")

    def navigate_to_systems(self):
        """
        Navigates to Systems
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.system'], "navigationItem_settings")

    def navigate_to_regions(self):
        """
        Navigates to Regions
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.regions'], "navigationItem_regions")

    def navigate_to_maintenance(self):
        """
        Navigates to Maintenance page
        """
        self.navigate_to_systems()
        self.admin_console.access_tile("tileMenuSelection_maintenance")

    def navigate_to_certificate_administration(self):
        """
        Navigates to Certificate Administration page
        """
        self.__search_navs(self.admin_console.props['label.nav.certificate'], "certificate")

    def navigate_to_schedule_policies(self):
        """
        Navigates to Schedule policies page
        """
        self.__search_navs(self.admin_console.props['label.nav.schedulePolicies'], "schedulePolicies")

    def navigate_to_subclient_policies(self):
        """
        Navigates to subclient policies page
        """
        self.__search_navs(self.admin_console.props['label.nav.subclientPolicies'], "subclientPolicies")

    def navigate_to_plan(self):
        """
        Navigates to Plan page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.profile'], "navigationItem_profile")

    def navigate_to_entity_tags(self):
        """Navigates to Entity tags
            Note: To be used when directly
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.tags'], "navigationItem_entityTagManager"
        )

    def navigate_to_backup_schedules(self):
        """
        Navigates to Schedule Policy Page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.schedulePolicies'], "navigationItem_schedulePolicies")

    def navigate_to_tags(self, is_entity_tag=False):
        """
        Navigates to Tags page
        """
        if is_entity_tag:
            self.search_nav_by_id(
                self.admin_console.props['label.nav.tags'], "navigationItem_entityTagManager"
            )
        else:
            self.search_nav_by_id(self.admin_console.props['label.nav.tags'], "navigationItem_entityTagManager")
            self.admin_console.access_tile("tileMenuSelection_dataClassificationTags")

    def navigate_to_home(self):
        """
        Navigates to the main page(servers)
        """
        self._click_home_icon()

    def navigate_to_getting_started(self):
        """
        Navigates to the Getting Started page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.gettingStarted'], "navigationItem_gettingStarted"
        )

    def navigate_to_dashboard(self):
        """
        Navigates to the dashboard page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.dashboard'], "navigationItem_dashboard")

    def navigate_to_commcell(self):
        """
        Navigates to the commcell page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.commCell'], "navigationItem_commCell")

    def navigate_to_nas_servers(self):
        """
        Navigates to the NAS File servers Page
        """
        self.__search_navs(self.admin_console.props['label.nav.NASFS'], "nasServers/")

    def navigate_to_devices(self):
        """
        Navigates to the Devices page
        """
        self.__search_navs(self.admin_console.props['label.nav.devices'], "laptops/Overview")
        self.admin_console.access_tab('Laptops')

    def navigate_to_devices_edgemode(self):
        """
        Navigates to the Devices page in edgemode
        """
        self.__search_navs(self.admin_console.props['label.nav.devices'], "laptops/Overview")

    def navigate_to_databases(self):
        """
        Navigate to databases
        """
        self.search_nav_by_id(self.admin_console.props['label.dbs'], "navigationItem_dbs-new")
        self.admin_console.access_tab(self.admin_console.props['label.nav.databaseDashboard'])

    def navigate_to_db_instances(self):
        """
        Navigates to the DB instances page
        """
        self.search_nav_by_id(self.admin_console.props['label.dbs'], "navigationItem_dbs-new")
        self.admin_console.access_tab(self.admin_console.props['label.nav.instances'])

    def navigate_to_archiving(self):
        """
        Navigates to the Archiving page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.archiving'], "navigationItem_archiveFileServers"
        )

    def navigate_to_archivingv2(self):
        """
        Navigates to the Archiving page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.archiving'], "navigationItem_archiveFileServersV2"
        )

    def navigate_to_office365(self, access_tab=True):
        """
        Navigates to the Office 365 Page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.office365'], 'navigationItem_office365V2'
        )
        if access_tab:
            self.admin_console.access_tab('Apps')

    def navigate_to_googleworkspace(self, access_tab=True):
        """
        Navigates to the Google Workspace App Page
        """
        self.search_nav_by_id(
            'Google Workspace', 'navigationItem_gsuiteApps'
        )
        if access_tab:
            self.admin_console.access_tab('Apps')

    def navigate_to_salesforce(self):
        """
        Navigates to the Salesforce page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.salesforce'], 'navigationItem_salesforceOrganizations'
        )

    def navigate_to_exchange(self):
        """
        Navigates to the exchange Apps page
        """
        self.__search_navs(self.admin_console.props['label.exchange'], "exchange")

    def navigate_to_sharepoint(self):
        """
        Navigates to the sharepoint Apps page
        """
        self.__search_navs(self.admin_console.props['label.sharepoint'], "sharepoint/")

    def navigate_to_cloud_apps(self):
        """
        Navigates to the cloud apps page
        """
        self.search_nav_by_id(self.admin_console.props['label.capps'], "navigationItem_cappsClients")

    def navigate_to_activedirectory(self):
        """
        Navigates to the active directory Apps page
        """
        self.search_nav_by_id(nav="Active Directory", nav_id="navigationItem_activeDirectory")

    def navigate_to_devops(self):
        """
        Navigates to the DevOps apps page
        """
        self.search_nav_by_id(self.admin_console.props["label.devOps"], "navigationItem_gitAppsAccounts")

    def navigate_to_cvapps(self):
        """
        Navigates to the Developer Tools page
        """
        self.search_nav_by_id(self.admin_console.props["label.nav.developerTools"], "navigationItem_developerTools")
        self.admin_console.access_tile('tileMenuSelection_cvApps')

    def navigate_to_dips(self):
        """
        Navigates to the DIPs page network
        """
        self.navigate_to_network()
        self.admin_console.access_tile('tileMenuSelection_dataOptions')

    def navigate_to_topologies(self):
        """
        Navigates to the Network topologies page
        """
        self.navigate_to_network()
        self.admin_console.access_tile('tileMenuSelection_NetworkTopology')

    def navigate_to_oracle_ebs(self):
        """
        Navigates to the Oracle EBS page
        """
        self.__search_navs(self.admin_console.props['label.ebs'], "ebsApps")

    def navigate_to_failover_groups(self):
        """
        Navigates to the Failover Groups page
        """
        self.navigate_to_replication_groups()
        self.admin_console.access_tab(self.admin_console.props['label.nav.failoverGroups'])

    def navigate_to_replication_targets(self):
        """
        Navigates to the Replication Targets page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.targets'], "navigationItem_recoveryTargetList"
        )

    def navigate_to_replication_groups(self):
        """
        Navigates to the Replication Groups page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.replication.groups'], "navigationItem_replication"
        )

    def navigate_to_rpstore(self):
        """
        Navigates to the RP store page
        """
        self.navigate_to_replication_groups()
        self.admin_console.access_tab(self.admin_console.props['label.nav.storageTargets.rpStores'])

    def navigate_to_replication_monitor(self):
        """
        Navigates to the Replication Monitor page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.replication.monitor'], "navigationItem_vsaReplicationMonitor"
        )

    def navigate_to_continuous_replication(self):
        """
        Navigates to the continuous tab of the Replication monitor page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.replication.monitor'], "navigationItem_vsaReplicationMonitor"
        )
        self.admin_console.access_tab("Continuous")

    def navigate_to_reports(self):
        """
        Navigates to the reports page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.reports'], "navigationItem_reports")

    def navigate_to_manage_reports(self):
        """
        Navigates to the reports manage page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.reports'], "navigationItem_manageReports")

    def navigate_to_manage_datasources(self):
        """
        Navigates to manage datasources page
        """

        try:
            self.navigate_to_manage_reports()
            self.admin_console.access_tile('tileMenuSelection_dataSources')
        except NoSuchElementException:
            self.search_nav_by_id(self.admin_console.props['label.nav.reports'], "navigationItem_datasourceManager")

    def navigate_to_big_data(self):
        """
        Navigates to the big data page
        """
        self.__search_navs(self.admin_console.props['label.nav.bigDataApps'], "bigDataApps")

    def navigate_to_governance_apps(self):
        """
        Navigates to the Governance apps page
        """
        self.__search_navs(self.admin_console.props['label.nav.activate'], "activate")

    def navigate_to_risk_analysis(self):
        """
        Navigates to the Risk Analysis page
        """
        self.__search_navs(self.admin_console.props['label.riskAnalysis'], "sdg")

    def switch_risk_analysis_tabs(self, ra_tab):
        """
        Switches to the respective Risk Analysis Tab
        Args:
            ra_tab(RATab)        --  Input representing the label name. Ex: RATab.PROJECTS
        """
        self.admin_console.access_tab(
            self.admin_console.props[ra_tab.value]
        )

    def navigate_to_object_storage(self):
        """
        Navigates to object storage page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.cloudStorage'], 'navigationItem_cloudStorageApp'
        )

        self.admin_console.access_tab(
            self.admin_console.props["label.objectStorageInstances"]
        )

    def navigate_to_storage_policies(self):
        """
        Navigates to storage policies page
        """
        self.__search_navs(self.admin_console.props['label.nav.storage'], "storagePolicies")

    def navigate_to_storage_targets(self):
        """
        Navigates to storage targets page
        """
        self.__search_navs(self.admin_console.props['label.nav.storage'], "nav/mstoragePool")
        self.admin_console.access_tile('Storage targets')

    def navigate_to_disk_storage(self):
        """
        Navigates to disk storage page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.disk'], "navigationItem_storageDisk")

    def navigate_to_tape_storage(self):
        """
        Navigates to tape storage page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.tape'], "navigationItem_storageTape")

    def navigate_to_cloud_storage(self):
        """
        Navigates to cloud storage page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.cloud'], "navigationItem_storageCloud")

    def navigate_to_air_gap_protect_storage(self):
        """
        Navigates to air gap protect storage page
        """
        self.search_nav_by_id(self.admin_console.props['label.metallicStorage'], "navigationItem_storageMetallic")

    def navigate_to_hyperscale_storage(self):
        """
        Navigate to Hyperscale storage page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.hyperscale'], "navigationItem_storageHyperscale"
        )

    def navigate_to_workflows(self):
        """
        Navigates to workflows page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.webconsole.forms'], "navigationItem_formsNav"
        )

    def navigate_to_approvals(self):
        """
        Navigates to approvals page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.approvals'], "navigationItem_approvalsNav"
        )

    def navigate_to_kubernetes(self):
        """
        Navigates to kubernetes page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.kubernetes'], 'navigationItem_kubernetes'
        )

    def navigate_to_k8s_clusters(self):
        """
        Navigates to the Kubernetes clusters page
        """
        self.admin_console.access_tab(self.admin_console.props['label.nav.clusters'])

    def navigate_to_k8s_appgroup(self):
        """
        Navigates to the Kubernetes application group page
        """
        self.admin_console.access_tab(self.admin_console.props['label.nav.applicationGroups'])

    def navigate_to_k8s_applications(self):
        """
        Navigates to the Kubernetes application page
        """
        self.navigate_to_k8s_clusters()
        self.admin_console.access_tab(self.admin_console.props['label.nav.applications'])

    def navigate_to_metallic(self):
        """
        Navigates to the Metallic page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.Metallic'], 'navigationItem_metallic')

    def navigate_to_dynamics365(self, access_tab=True):
        """
        Navigates to the Dynamics 365 Page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.dynamics365'], "navigationItem_dynamics365"
        )
        if access_tab:
            self.admin_console.access_tab("Apps")

    def navigate_to_migration(self):
        """
        Navigates to the Migration Page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.migration'], "navigationItem_migration")

    def navigate_to_developer_tools(self):
        """
        Navigates to the Developer Tools Page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.developerTools'], "navigationItem_developerTools")

    def navigate_to_alert_rules(self):
        """
        Navigates to the Developer Tools Page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.developerTools'], "navigationItem_developerTools")
        self.admin_console.click_by_id("tileMenuSelection_alertRules")

    @PageService()
    def navigate_to_my_data(self):
        """
        Navigates to the My Data page under Web Console node
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.webconsole.mydata'], "navigationItem_webconsoleMyData"
        )

    @PageService()
    def navigate_to_download_center(self):
        """
        Navigates to the Download center page under Web Console node
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.webconsole.downloadCenter'], "navigationItem_downloadCenter"
        )

    @PageService()
    def navigate_to_webconsole_monitoring(self):
        """
        Navigates to webconsole monitoring page
        """
        self.search_nav_by_id(
            self.admin_console.props['label.nav.webconsole.monitoring'], "navigationItem_webconsoleMonitoring"
        )

    @PageService()
    def navigate_to_office365_licensing_usage(self):
        """Navigates to Office 365 Usage page"""
        self.search_nav_by_id(
            nav="Usage", nav_id="navigationItem_usageSummary"
        )

    @PageService()
    def navigate_to_unusual_file_activity(self):
        """
        Navigates to unusual file activity page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.fileAnomaly'], "navigationItem_fileAnomaly")

    @PageService()
    def navigate_to_service_catalogue(self):
        """
            Navigates to Service Catalogue Page on Metallic OEM
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.serviceCatalog'], "navigationItem_serviceCatalogV2")

    @PageService()
    def navigate_to_gcm_service_commcells(self):
        """
            Navigates to Service Commcell Page on GCM App
        """
        self.search_nav_by_id("Service CommCells", "navigationItem_environment")

    @PageService()
    def navigate_to_service_catalog(self):
        """
            Navigate to Service Catalog page on Commvault OEM
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.serviceCatalog'], "navigationItem_serviceCatalog")

    def navigate_to_recovery_groups(self):
        """
        Navigate to Cleanroom recovery groups page
        """
        self.search_nav_by_id(self.admin_console.props['label.nav.recoveryGroups'], "navigationItem_recoveryGroupList")

    @PageService(react_frame=False)
    def logout(self, url=None):
        """        Logs out from the current user

        Args:
                url      (str)   --  URL to be loaded

        """
        if not _CONSTANTS.SECURITY_TEST:  # skip logout while doing security test
            self._click_user_settings_drop_down()
            self._click_logout()
            if url:
                self.admin_console.navigate(url)
            else:
                self._navigate_back_to_login_page()

    @PageService()
    def switch_company_as_operator(self, company_name: str):
        """
        To Select the company

        Args:
            company_name: name of the company that has to be selected

        Returns:
        """
        self.dropdown.select_drop_down_values(
            drop_down_id='header-company-dropdown', values=[company_name], search_key=lambda s: s.split('(')[0].strip()
        )
        self.admin_console.close_popup()
        self.admin_console.close_warning_dialog()
        self.admin_console.check_error_page()
        if shown_company := self.__read_company_switcher_text():
            if shown_company.split('(')[0].strip().lower() not in company_name.lower():
                raise CVWebAutomationException(f"company name: {company_name} not shown in switcher post switching!")

    @PageService()
    def operating_company_displayed(self):
        """Gets the current company operating on

        Returns:
            str     -   the current text displayed in company switcher
            None    -   if no companies being operated
        """
        company_text = self.__read_company_switcher_text()
        if company_text not in ['Select a company', 'Select company']:
            return company_text

    @PageService()
    def operating_companies_displayed(self, search: str = None):
        """Gets the list of companies displayed under company switcher

        Args:
            search  (str)       -       any search string to apply first

        Returns:
            companies_displayed (list)  -   list of companies displayed
        """
        return self.dropdown.get_values_of_drop_down(
            drop_down_id='header-company-dropdown',
            search=search
        )

    def __expand_commcell_selection_dd(self):
        """Clicks and opens up commcell selection drop down"""
        dd_element = self.driver.find_element(By.ID, "header-commcell-dropdown")
        dd_element.click()

    def __select_commcell_from_drop_down(self, commcell_name):
        """Selects the commcell name from opened dropdown

        Args:
            commcell_name (str): commcell name to be selected

        """
        xpath = f"//*[contains(@class,'MuiMenu-list')]//li[@value='{commcell_name}']"
        # todo: support clicking new tab icon xpath found in global
        result_item = self.driver.find_element(By.XPATH, xpath)
        result_item.location_once_scrolled_into_view
        result_item.click()

    @WebAction()
    def __read_service_commcell_name(self):
        """Gets the service commcell name displayed

        Returns:
            commcell_name   (str)   -   name of commcell
        """
        commcell_switcher = self.driver.find_element(By.ID, "header-commcell-dropdown")
        return commcell_switcher.text.strip()

    @WebAction()
    def __read_service_commcells(self):
        """Gets the commcell names displayed under the switcher's dropdown along with other information

        Returns:
            OrderedDict    -   dict with commcell names as key and {icon, hover_label} dict as value
        """
        displayed_links = OrderedDict()
        for link_element in self.driver.find_elements(By.XPATH, "//div[@id='menu-']//li[@role='menuitem']"):
            commcell_name = link_element.text.strip()
            icon_elem = link_element.find_element(By.XPATH, ".//*[name()='svg']")
            hover_label = link_element.find_element(
                By.XPATH, ".//div[contains(@class, 'mui-tooltip')]").get_attribute('aria-label').strip()
            displayed_links[commcell_name] = {'icon': get_icon_name(icon_elem), 'hover_label': hover_label}
        return displayed_links

    @PageService()
    def switch_service_commcell(self, commcell_name):
        """Change commcell for a multicommcell setup

        Args:
            commcell_name (str): name of the commcell to switch to

        """
        self.__expand_commcell_selection_dd()
        time.sleep(2)
        self.__select_commcell_from_drop_down(commcell_name)
        self.admin_console.wait_for_completion()
        self.admin_console.close_popup()
        self.admin_console.close_warning_dialog()
        self.admin_console.check_error_page()
        if self.service_commcell_displayed().strip() != commcell_name.strip():
            raise CVWebAutomationException(f"commcell name: {commcell_name} not shown in switcher post switching")

    @PageService()
    def service_commcell_displayed(self):
        """Gets the current service commcell displayed in switcher

        Returns:
            service_name    (str)   -   name of service commcell displayed
        """
        return self.__read_service_commcell_name()

    @PageService()
    def service_commcells_displayed(self):
        """
        Gets all the service commcells displayed under commcell switcher dropdown, as ordereddict

        Returns:
            OrderedDict    -   dict with commcell name key and icon, hover_label information in value

            Example: {
                commcellname1: {'icon': 'global', 'hover_label': 'https://commcellname1.com' },
                ...
            }
        """
        self.__expand_commcell_selection_dd()
        displayed_data = self.__read_service_commcells()
        self.dropdown.collapse_dropdown(drop_down_id='header-commcell-dropdown')
        return displayed_data

    @PageService()
    def switch_to_activate_tab(self):
        """
                Navigates to Activate tab in getting started page
        """
        self.admin_console.select_hyperlink(self.admin_console.props['label.activate'])

    @WebAction()
    def __wait_for_universal_search_options(self, option_text):
        """
        Wait till options appear after typing into the universal search

        Args:
            option_text (str)   : text expected in the options
        """
        cmd_complete_xp = f"//ul[@id='global-search-text-input-listbox']//*[contains(text(), '{option_text}')]"
        wait = WebDriverWait(self.driver, 30)
        wait.until(ec.presence_of_element_located((By.XPATH, cmd_complete_xp)))

    @WebAction()
    def __type_into_universal_search(self, search_string):
        """
        Args:
            search_string   (str):  key or string to typed in to universal search

        """

        #self.admin_console.unswitch_to_react_frame()
        if search_string in ["TAB", "UP", "DOWN"]:
            self.driver.find_element(By.ID, "global-search-text-input").send_keys(
                eval(f"Keys.{search_string}"))
        else:
            self.driver.find_element(By.ID, "global-search-text-input").send_keys(search_string)
        self.admin_console.wait_for_completion()

    @WebAction()
    def __highlight_given_option(self, result_xpath):
        """Method to cycle through options till given option is highlighted"""

        while "Mui-focused" not in result_xpath.find_element(By.XPATH, "./ancestor::li//li").get_attribute(
                'class'):
            self.__type_into_universal_search("DOWN")
            self.admin_console.wait_for_completion()

    @PageService()
    def __select_search_result(self, result, result_header=None, operation: str = 'CLICK'):
        """
        Args:
            result            (str): Name of entity to be selected
            result_header     (str): Entity type to be selected
            operation   (str)   -- operation to be performed on the entity
                expected inputs : CLICK (to select the entity and navigate to the page) ;
                                    TAB (to list/search the entities list under the page)

        """

        if result_header:
            result_xpath = f"//div[contains(text(),'{result_header}')]/following::ul//a[contains(text(),'{result}')]"
        else:
            result_xpath = f"//div[contains(@class,'MuiAutocomplete-popper')]//a[contains(text(),'{result}')]"
        element = self.driver.find_element(By.XPATH, result_xpath)
        self.admin_console.scroll_into_view(result_xpath)
        if operation.upper() == 'CLICK':
            element.click()
        else:
            self.__type_into_universal_search("DOWN")
            self.__highlight_given_option(element)
            self.__type_into_universal_search("TAB")

    @WebAction()
    def __select_action_for_global_search(self, action: str):
        """
        select action to be performed from global search action drop down
        Args:
            action(str) -- action to be performed
            e.g. Add, Goto, Backup, Restore, Logs
        """
        # check the current selected option
        current_action = self.driver.find_element(By.XPATH, ".//li[contains(@class,'Dropdown-singleEntry')]").text
        if action.upper() != current_action:
            dropdown = self.driver.find_element(By.XPATH, "//div[@id='global-search-action-dropdown']"
                                                         "//ancestor::div[contains(@class, 'dd-form-control')]")
            dropdown.click()
            actions = ["Search", "Add", 'Goto', "Backup", "Restore", "Files", "Logs", "Help", "Additional Settings"]
            if action.capitalize() in actions:
                wait = WebDriverWait(self.driver, 10)
                element = wait.until(ec.element_to_be_clickable((By.XPATH, f".//*[contains(text(),"
                                                                           f"'{action.capitalize()}')]//ancestor::li")))
                element.click()
            else:
                raise ValueError("Invalid action passed")

    @PageService()
    def add_entity_from_search_bar(self, entity_type: str):
        """Adds entity using /Add command on universal search bar

        Args:
            entity_type (str)   -- Type of entity to be added e.g. File server, Company, Plan etc.
        """
        self.__select_action_for_global_search("Add")
        self.admin_console.fill_form_by_id("global-search-text-input", entity_type.capitalize())
        self.__select_search_result(entity_type.capitalize())

    @PageService()
    def navigate_from_global_search(self, entity_type: str, operation: str = 'CLICK'):
        """
        Method to navigate to a page using GOTO from global search

        args:
            entity_type     (str)    --  name of the entity's category
            operation   (str)   -- operation to be performed on the entity
                expected : CLICK (to select the entity and navigate to the page)
                           TAB (to list/search the entities list under the page)
        """
        self.__select_action_for_global_search("Goto")
        self.admin_console.fill_form_by_id("global-search-text-input", entity_type.capitalize())
        self.__select_search_result(entity_type.capitalize(), operation=operation)

    @PageService()
    def manage_entity_from_search_bar(self, entity_type: str, entity_name: str, action: str, reset: bool = False):
        """
        Manage entity from search bar by searching entity and selecting action from the search bar

        Args:
            entity_type     (str)   -- Type of the entity
            entity_name     (str)   --  Name of the entity to manage
            action          (str)   -- Action you want to perform on the entity
            reset           (bool)  --  flag to decide whether to reset the global search bar or not

        """
        if reset:
            self.__select_action_for_global_search('SEARCH')

        # from GOTO navigate to entity -> search entity -> perform tab actions
        # Type entity_type in GOTO and press TAB
        self.navigate_from_global_search(entity_type, operation="TAB")

        # type entity name and press TAB
        self.admin_console.fill_form_by_id("global-search-text-input", entity_name)
        self.__select_search_result(result=entity_name,
                                    result_header=entity_type.capitalize(),
                                    operation="TAB")

        # type action in search bar and click
        action = action.capitalize()
        self.__type_into_universal_search(action)
        self.__wait_for_universal_search_options(action)
        self.__select_search_result(result=action, operation="TAB")

    @PageService()
    def get_category_global_search(self, entity_type: str, entity_name: str) -> list:
        """
        search entity from global search bar and return search result categories

        Args:
            entity_type     (str)   --  category of the entity
            entity_name     (str)   --  Name of the entity to search

        returns:
            list -- list of the entities listed under the category
        """
        self.__select_action_for_global_search("Search")
        self.admin_console.fill_form_by_id("global-search-text-input", entity_name)
        self.__wait_for_universal_search_options(entity_name)
        result = self.__search_result_category()
        # e.g. result = {'entity_type':['entity1','entity2','entity3']}
        return result[entity_type]

    @PageService()
    def get_nav_colors(self):
        """ Gets the different colors visible in nav bar and header """
        self.__click_navigation_button()
        theme_elements = {
            'headerColor': ('//*[@id="cv-header"]', 'background'),
            'headerTextColor': ('//*[@id="user-account-toggle"]/a', 'color'),
            'navBg': ('//*[@id="left-side-nav"]', 'background-color'),
            'navIconColor': ('//*[@id="nav-search-field"]', 'color')
        }
        theme_colors = {}
        for theme_tag, color_prop in theme_elements.items():
            xpath, css_prop = color_prop
            theme_colors[theme_tag] = self.admin_console.get_element_color(xpath, css_prop)
        return theme_colors

    @PageService()
    def navigate_to_usage(self):
        """
        Navigates to the usage page
        """
        self.search_nav_by_id(nav="Usage", nav_id="navigationItem_usageSummary")
