from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""All operations on Navigation goes in this file"""
from time import sleep

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from AutomationUtils import logger, config
from Reports.storeutils import StoreUtils
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.WebConsole.Reports.Metrics import commcellgroup

_CONSTANTS = config.get_config()
_STORE_CONSTANTS = StoreUtils.get_store_config()


class CommCellSearch:

    """
    This class is to manage activity on CommCell Search bar
    """

    def __init__(self, webconsole):
        """
        Args:
            webconsole (WebConsole): The webconsole object to use
        """
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver
        self._log = logger.get_log()

    @WebAction()
    def _set_search_field_on_dashboard(self, name):
        """
        Search with the name in search field
        """
        search_field = self._driver.find_element(By.XPATH, "//div[@id='search']/input")
        search_field.send_keys(name)

    @WebAction()
    def _get_commcell_from_search(self):
        """get the list of CommCells from search result"""
        commcells = []
        cclist = self._driver.find_elements(By.XPATH, "//li[@class='ui-menu-item']")
        for commcell in cclist:
            commcell_name = commcell.text.split(' - ')
            if commcell_name:
                commcells.append(commcell_name[-2].strip())
        return commcells

    @WebAction()
    def _click_commcell_search_list(self, commcell_name):
        """
        clicks on commcell name in search list
        Args:
            commcell_name: Name of the commcell in click in search list
        """
        cc_elem = "//li[@class='ui-menu-item']//*[contains(text(),'" + commcell_name + "')]"
        self._driver.find_element(By.XPATH, cc_elem).click()

    @PageService()
    def access_commcell(self, commcell_name):
        """
        Access CommCell from search bar
        Args:
            commcell_name: name of the commcell to access
        """
        self._set_search_field_on_dashboard(commcell_name)
        cc_list = self._get_commcell_from_search()
        if commcell_name in cc_list:
            self._click_commcell_search_list(commcell_name)
            self._webconsole.wait_till_load_complete()
        else:
            raise CVWebAutomationException(f"CommCell [{commcell_name}] doesn't exist in "
                                           f"Search result")


class Navigator:

    """
    This class holds the common navigation functionality for report app
    """

    def __init__(self, webconsole):
        """
        Args:
            webconsole (WebConsole): The webconsole object to use
        """
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver
        self._log = logger.get_log()
        self._cc_search = CommCellSearch(webconsole)

    @WebAction()
    def __click_on_panel(self, elem_id):
        """Clicks on the element name on the navigation panel"""
        navigation_elem = self._driver.find_element(By.ID, elem_id)
        navigation_elem.click()

    def _access_panel(self, elem_id):
        """Access to the section passed present on the navigation panel"""
        self._expand_navigation_panel()
        if self._is_navigation_panel_displayed():
            self.__click_on_panel(elem_id)
            self._webconsole.wait_till_load_complete()
        else:
            raise CVWebAutomationException(
                "Navigation panel not displayed in current page\n%s" %
                self._driver.title)

    def _is_navigation_panel_displayed(self):
        """Check if navigation panel is displayed"""
        return self._driver.execute_script("""
                element = document.getElementById('reportSideBar');
                return document.body.contains(element)""")

    @WebAction()
    def _is_worldwide_commcell_page(self):
        """Check if current page is commcell page"""
        return self._driver.title == "Worldwide CommCells"

    @WebAction()
    def _is_worldwide_reports_page(self):
        """Check if current page is worldwide reports page"""
        return self._driver.title == "Reports"

    @WebAction()
    def _is_worldwide_commcell_group_page(self):
        """Check if current page is worldwide commcell group page"""
        return self._driver.title == "CommCell Groups"

    @WebAction()
    def _is_worldwide_dashboard_page(self):
        """Check if current page is worldwide dashboard page"""
        return self._driver.title == "Worldwide Dashboard"

    @WebAction()
    def _is_contract_management_page(self):
        """Check if current page is worldwide dashboard page"""
        return self._driver.title == "Billing Group Associations"

    @WebAction()
    def _access_contract_management_page(self):
        """Open contract management page"""
        self._driver.get(self._webconsole.base_url + "cloud/contract/contractManagement.jsp")

    @WebAction()
    def _is_companies_page(self):
        """Check if the current page is companies page"""
        return self._driver.title == "Companies"

    @WebAction()
    def _set_search_field_on_reports_page(self, name):
        """Type search string on reports page"""
        search_field = self._driver.find_element(By.ID, "reportFilterSearch")
        search_field.send_keys(name)

    @WebAction(delay=2)
    def _get_commcell_count(self):
        """Reads the commcells count from the navigation menu present in CommCells label"""
        WebDriverWait(self._driver, 20).until(EC.presence_of_element_located((By.ID,'Commcells')))
        return int(
            self._driver.find_element(By.ID, 'Commcells').text.split("(")[1].split(")")[0])

    @WebAction()
    def _expand_navigation_panel(self):
        """Expands the navigation panel if its in closed state"""
        expand_xp = "//label[@class='vw-js-nav-trigger']//*[name()='path']"
        expand_icon = self._driver.find_elements(By.XPATH, expand_xp)
        expand_state = expand_icon[1].get_attribute('style')
        if expand_state == 'display: inline;':
            expand_icon[1].click()

    @WebAction()
    def _click_report_if_available(self, name):
        """
        Click on report icon
        Args:
            name: Report Name
        """
        report = self._driver.find_elements(By.XPATH, 
            "//div[@id='reportSearchDiv']//a[text()='%s']" % name)
        if report:
            report[0].click()
        else:
            raise CVWebAutomationException(
                "Report [%s] not found on Reports page" % name)

    @WebAction()
    def _click_configuration(self):
        """Click configuration on navigation panel"""
        config_link = self._driver.find_element(By.ID, "reportsManager")
        config_link.click()

    @WebAction()
    def _get_section_title(self):
        """Read Section title in navigation panel"""
        self._driver.find_element(By.XPATH, '//span[contains(@class,"sec-title")]')

    @WebAction()
    def __get_bread_crumb(self):
        """Fetches the bread crumbs on the top of the report"""
        return [element.text for element in self._driver.find_elements(By.XPATH, 
            "//*[contains(@class,'smartLinkMain')]")]

    @WebAction()
    def _access_report(self, name):
        """access report page"""
        self._set_search_field_on_reports_page(name)
        self._webconsole.wait_till_load_complete()
        sleep(3)
        self._click_report_if_available(name)
        self._webconsole.wait_till_load_complete()

    @WebAction()
    def __click_link_on_bread_crumb(self, page):
        """Clicks the given page on the bread crumb"""
        page = self._driver.find_element(By.XPATH, f"//*[contains(@class,'smartLinkMain') and "
                                                  f".='{page}']")
        page.click()

    @WebAction()
    def _click_custom_dashboard(self):
        """Click custom dashboard on navigation panel"""
        link = self._driver.find_element(By.XPATH, 
            "//*[@data-div='CustomDashboards']"
        )
        link.click()

    @WebAction()
    def _click_worldwide_dashboard(self):
        """
        click worldwide dashboard in the breadcrumbs
        """
        xpath = '//a[contains(@href,"/webconsole/reports/index.jsp?page=Dashboard")]'
        dashboard = self._driver.find_element(By.XPATH, xpath)
        dashboard.click()

    @WebAction()
    def _click_app(self, app_name):
        """Open App from Applications page"""
        link = self._driver.find_element(By.XPATH, 
            "//*[@class='displayText vw-app-text']//*[text()='%s']" %
            str(app_name)
        )
        link.click()

    @PageService()
    def goto_companies(self):
        """ Go to companies page"""
        if self._is_companies_page():
            return
        self._access_panel("companies")

    @PageService()
    def get_title(self):
        """Returns the tile of navigation menu like worldwide or commcell name"""
        self._get_section_title()

    @PageService()
    def is_it_single_commcell(self):
        """Find if webconsole contains singe CommCell"""
        self._expand_navigation_panel()
        if self._get_commcell_count() == 1:
            return True
        return False

    @PageService()
    def get_commcell_count(self):
        """Get the commcell count"""
        return self._get_commcell_count()

    @PageService(hide_args=True)
    def goto_store(self, username=_STORE_CONSTANTS.PREMIUM_USERNAME,
                   password=_STORE_CONSTANTS.PREMIUM_PASSWORD):
        """Open store page
        Args:
            username (str): Username for store login
            password (str): Password for store login
        """
        self._log.info("Trying to open store page as [%s]", username)
        from Web.WebConsole.Store import storeapp
        self._access_panel("appStoreLink")
        storeapp.StoreLogin(self._webconsole).login(username, password)
        self._webconsole.wait_till_load_complete()

    @PageService()
    def goto_worldwide_dashboard(self, public_cloud=False):
        """Open worldwide dashboard"""
        if self._is_worldwide_dashboard_page():
            return
        if not public_cloud:
            self._access_panel("dashboard")
        else:
            self._click_worldwide_dashboard()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def goto_worldwide_commcells(self):
        """Open worldwide commcells page"""
        if self._is_worldwide_commcell_page():
            return
        self._access_panel("Commcells")

    @PageService()
    def goto_worldwide_report(self, name=None):
        """
        Open report from worldwide page
        Args:
            name (str): optional parameter if provided corresponding reports will be accessed
        """
        if self.is_it_single_commcell():
            self.goto_commcell_reports()
        else:
            self._access_panel("reports")
        if name is not None:
            self._access_report(name)

    @PageService()
    def goto_commcell_group(self, commcell_group_name=None):
        """Open commcell group page"""
        self._access_panel("commcellGroups")
        self._webconsole.wait_till_load_complete()
        if commcell_group_name is None:
            return
        commcell_group_page = commcellgroup.CommcellGroup(self._webconsole)
        commcell_group_page.apply_filter(commcellgroup.ColumnNames.GROUP_NAME,
                                         commcell_group_name)
        self._webconsole.wait_till_load_complete()
        commcell_group_page.access_commcell_group(commcell_group_name)

    @PageService()
    def goto_commcells_in_group(self):
        """
        Goto commcells page in commcell group
        """
        self._access_panel("Commcells")

    @PageService()
    def goto_reports_configuration(self):
        """Open report configuration page"""
        self._click_configuration()
        self._access_panel("reportMgrLi")

    @PageService()
    def goto_settings_configuration(self):
        """Open report settings page"""
        self._click_configuration()
        self._access_panel("reportSettingsLi")

    @PageService()
    def goto_datasources_configuration(self):
        """Open datasource configuration page"""
        self._click_configuration()
        self._access_panel("generalLi")

    @PageService()
    def goto_dataset_configuration(self):
        """Open datasource configuration page"""
        self._click_configuration()
        self._access_panel("dataSetMgrLi")

    @PageService()
    def goto_alerts_configuration(self):
        """Open alerts configuration page"""
        self._click_configuration()
        self._access_panel("alarmsLi")

    @PageService()
    def goto_schedules_configuration(self):
        """Open schedule configuration page"""
        self._click_configuration()
        self._access_panel("schedulesLi")

    @PageService()
    def goto_commcell_dashboard(self, commcell_name):
        """
        Goto commcell dashboard page
        Args:
            commcell_name: name of the commcell to access

        """
        if self.is_it_single_commcell():
            self._access_panel("dashboard")
        else:
            self.goto_worldwide_dashboard()
            self._cc_search.access_commcell(commcell_name)
        self._webconsole.wait_till_load_complete()

    @PageService()
    def goto_health_report(self):
        """Goto health page"""
        self._access_panel('health')
        self._webconsole.wait_till_load_complete()
        sleep(3)  # time for the tile to load after page load

    @PageService()
    def goto_commcell_reports(self, report_name=None, commcell_name=None):
        """
        Goto commcell reports page
        Args:
            report_name: name of the report to access
            commcell_name: name of the commcell whose report to be accessed
        """
        if commcell_name and commcell_name not in self._driver.title:
            self.goto_commcell_dashboard(commcell_name)
        self._access_panel('reports')
        if report_name is None:
            return
        self._access_report(report_name)

    @PageService()
    def goto_report_settings(self):
        """
        Goto report settings page
        """
        self._click_configuration()
        self._access_panel("reportSettingsLi")

    @PageService()
    def goto_custom_dashboard(self):
        """Goto Reports dashboard"""
        self._click_configuration()
        self._click_custom_dashboard()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def goto_profile(self):
        """Goto profile page"""
        self._access_panel("CommcellprofileTab")

    @PageService()
    def goto_contract_management(self):
        """Goto contract management page"""
        if not self._is_contract_management_page():
            self._access_contract_management_page()
            self._webconsole.wait_till_load_complete(line_check=False)

    @PageService()
    def goto_report_builder(self):
        """Goto report builder"""
        self._driver.get(self._webconsole.base_url + "reportsplus/?")

    @PageService()
    def goto_reports(self):
        """Open reports app"""
        self._click_app("Reports")
        self._webconsole.wait_till_load_complete()

    @PageService()
    def get_bread_crumb(self):
        """Returns the bread crumb on the report page as a list"""
        return self.__get_bread_crumb()

    @PageService()
    def goto_page_via_breadcrumb(self, page):
        """Navigates to the desired page via the bread crumb"""
        self.__click_link_on_bread_crumb(page)
        self._webconsole.wait_till_load_complete()
