from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Apps page file"""

import time

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys

from Reports.storeutils import StoreUtils

from Web.Common.exceptions import (
    CVTimeOutException,
    CVWebAutomationException
)
from Web.Common.page_object import (
    PageService,
    WebAction
)
_STORE_CONFIG = StoreUtils.get_store_config()


class AppsPage:

    """Apps Page class"""

    def __init__(self, webconsole):
        self.webconsole = webconsole
        self.driver = webconsole.browser.driver

    @WebAction()
    def __click_new_app(self):
        """Click new app"""
        add_button = self.driver.find_element(By.XPATH, 
            "//*[@id='add-button-svg']"
        )
        add_button.click()

    @WebAction()
    def __click_search_field(self):
        """Click search field"""
        search_field = self.driver.find_element(By.XPATH, 
            "//*[@class='app-list-search']"
        )
        search_field.click()

    @WebAction()
    def __set_search_field(self, app_name):
        """Set search field"""
        search_input = self.driver.find_element(By.XPATH, 
            "//*[@class='app-list-search']/input"
        )
        search_input.send_keys(app_name)

    @WebAction(log=False)
    def __is_loading_cube_visible(self):
        """Is loading cube visible"""
        try:
            loading_cube = self.driver.find_element(By.XPATH, 
                "//*[@class='ab-no-apps-msg' and contains(., 'Loading')]"
            )
            return loading_cube.is_displayed()
        except WebDriverException:
            return False

    @WebAction()
    def __get_visible_app_names(self):
        """Get name of the first app"""
        apps = self.driver.find_elements(By.XPATH, 
            "//label[@class='app-name']/a[@class='app-name-link']"
        )
        return [app.text for app in apps if len(app.text) > 0]

    @WebAction()
    def __click_get_icon(self):
        """Clicking Get Icon on Apps page"""
        button = self.driver.find_element(By.XPATH, 
            "//*[@class='header-svg-icon get-button-svg']"
        )
        button.click()

    @WebAction()
    def __click_install_from_store(self):
        """Clicking install from Store option"""
        h_link = self.driver.find_element(By.XPATH, 
            "//*[@id='appStoreLink' and contains(., 'Install From Store')]"
        )
        h_link.click()

    def __wait_for_loading_cube(self, timeout=60):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.__is_loading_cube_visible():
                time.sleep(1)
            else:
                return
        raise CVTimeOutException(
            timeout,
            "Timeout occurred waiting for App load",
            self.driver.current_url
        )

    @PageService()
    def lookup_app(self, app_name):
        """Find app"""
        self.__click_search_field()
        self.__set_search_field(app_name)
        time.sleep(2)
        if app_name not in self.__get_visible_app_names():
            raise CVWebAutomationException(
                f"App [{app_name}] not found, lookup failed"
            )

    @PageService()
    def wait_for_load_complete(self, timeout=60):
        """Wait till loading is complete"""
        self.__wait_for_loading_cube(timeout)
        self.webconsole.wait_till_load_complete()

    @PageService()
    def goto_new_app(self):
        """Goto App builder page"""
        self.__click_new_app()
        self.wait_for_load_complete()

    @PageService(hide_args=True)
    def goto_store(self,
                   username=_STORE_CONFIG.PREMIUM_USERNAME,
                   password=_STORE_CONFIG.PREMIUM_USERNAME):
        """Open Store from Apps page"""
        from Web.WebConsole.Store import storeapp
        self.__click_get_icon()
        self.__click_install_from_store()
        storeapp.StoreLogin(self.webconsole).login(
            username, password
        )

    @PageService()
    def get_apps(self):
        """Get all apps on Apps Page"""
        return self.__get_visible_app_names()


class App:

    """App class"""

    def __init__(self, app_name, apps_page: AppsPage):
        self._app_name = app_name
        self.__apps_page = apps_page
        self.__driver = apps_page.driver

    @WebAction()
    def __open_app_menu(self, name):
        """Open the app menu"""
        app_menu = self.__driver.find_element(By.XPATH, 
            f"//*[@class='app-tile' and contains(., '{name}')]//button"
        )
        app_menu.click()

    @WebAction()
    def __click_menu_option(self, option_name):
        """Click option name on the menu"""
        option = self.__driver.find_element(By.XPATH, 
            "//*[@class='app-grid-tile-action-menu open']"
            f"//li[contains(., '{option_name}')]"
        )
        option.click()

    @WebAction()
    def __confirm_delete(self):
        """Click Yes on confirmation dialogue"""
        delete_btn = self.__driver.find_element(By.XPATH, 
            "//*[@class='modal-content']//button[.='Yes']"
        )
        delete_btn.click()

    @WebAction()
    def __search_user(self, to_user):
        """Searches the given user"""
        search = self.__driver.find_element(By.XPATH, "//h2/following-sibling::input[@type='text']")
        search.clear()
        search.send_keys(to_user)
        search.send_keys(Keys.RETURN)

    @WebAction()
    def __select_user(self, to_user):
        """Selects the Given user"""
        user = self.__driver.find_element(By.XPATH, f"//*[.='{to_user}']")
        user.click()

    @WebAction()
    def __click_move_right(self):
        """Clicks the move right button"""
        user = self.__driver.find_element(By.XPATH, "//button[.='>']")
        user.click()

    @WebAction()
    def __click_apply(self):
        """Clicks the apply button"""
        user = self.__driver.find_element(By.XPATH, "//button[.='Apply']")
        user.click()

    @PageService()
    def delete(self):
        """Delete app"""
        self.__open_app_menu(self._app_name)
        self.__click_menu_option("Delete")
        time.sleep(2)  # Delay in addition to the WebAction delay
        self.__confirm_delete()
        self.__apps_page.wait_for_load_complete()
        self.__apps_page.webconsole.wait_till_load_complete()
        self.__apps_page.webconsole.get_all_unread_notifications(
            expected_count=1,
            expected_notifications=["Successfully deleted app."]
        )

    @PageService()
    def export(self):
        """Export app"""
        self.__open_app_menu(self._app_name)
        self.__click_menu_option("Export")
        time.sleep(2)
        self.__apps_page.wait_for_load_complete()
        self.__apps_page.webconsole.get_all_unread_notifications(
            expected_count=1,
            expected_notifications=[f"Exporting {self._app_name}"]
        )

    @PageService()
    def share(self, to_user):
        """Share app"""
        self.__open_app_menu(self._app_name)
        self.__click_menu_option("Share")
        time.sleep(2)
        self.__search_user(to_user)
        time.sleep(2)
        self.__select_user(to_user)
        self.__click_move_right()
        self.__click_apply()
        self.__apps_page.wait_for_load_complete()
        self.__apps_page.webconsole.get_all_unread_notifications(
            expected_count=1,
            expected_notifications=["Successfully updated security associations."]
        )


class AppBuilder:

    """App Builder class"""

    def __init__(self, apps_page: AppsPage):
        self.__apps_page = apps_page
        self.__driver = apps_page.driver

    @WebAction()
    def __set_name_input(self, name):
        """Type name into name field"""
        name_field = self.__driver.find_element(By.XPATH, 
            "//input[contains(@class,'app-name-input')]"
        )
        name_field.send_keys(name)

    @WebAction()
    def __set_category(self, category):
        """Set category"""
        filter_tab = self.__driver.find_element(By.XPATH, 
            f"//*[@class='quick-filter-links']/li[.='{category}']"
        )
        filter_tab.click()

    @WebAction()
    def __set_search_field(self, search_text):
        """Set search field"""
        search_input = self.__driver.find_element(By.XPATH, 
            "//input[@placeholder='Search']"
        )
        search_input.clear()
        search_input.send_keys(search_text)

    @WebAction()
    def __set_primary_component(self, name):
        """Set primary component"""
        ribbon = self.__driver.find_element(By.XPATH, 
            f"//div[@class='component-tile' and contains(.//@title, '{name}')]"
            "//*[@*='Set as primary component']"
        )
        ribbon.click()

    @WebAction(log=False)
    def __is_package_visible(self, name):
        """Is package visible"""
        try:
            self.__driver.find_element(By.XPATH, f"//*[@title='{name}']")
            return True
        except WebDriverException:
            return False

    @WebAction()
    def __click_package(self, name):
        """Click package"""
        package = self.__driver.find_element(By.XPATH, 
            f"//*[@class='resource-tile' and contains(div//@title, '{name}')]"
        )
        package.click()

    @WebAction()
    def __click_add_component(self):
        """Click add component button"""
        add_comp_button = self.__driver.find_element(By.XPATH, 
            "//button[contains(@class, 'ab-add-components-btn')]"
        )
        add_comp_button.click()

    @WebAction()
    def __click_done(self):
        """Click save"""
        button = self.__driver.find_element(By.XPATH, 
            "//button[@ng-reflect-tooltip='Done']"
        )
        button.click()

    @WebAction()
    def __click_finish(self):
        """Click finish"""
        finish = self.__driver.find_element(By.XPATH, "//button[.='Finish']")
        finish.click()

    @WebAction(log=False)
    def __focus_on_search_panel(self):
        """Scroll up to search and category panel"""
        elem = self.__driver.find_element(By.XPATH, "/*")
        elem.send_keys(Keys.HOME)

    @WebAction()
    def __get_selected_category(self):
        """Get selected category"""
        li = self.__driver.find_element(By.XPATH, 
            f"//*[@class='quick-filter-links']/li[@class='qf-link selected-tab']"
        )
        return li.text

    def __search_package(self, name, category):
        if self.__is_package_visible(name):
            return
        self.__focus_on_search_panel()
        if self.__get_selected_category() != category:
            self.__set_category(category)
        self.__apps_page.wait_for_load_complete()
        self.__set_search_field(name)
        time.sleep(2)
        if self.__is_package_visible(name) is False:
            raise CVWebAutomationException(
                f"[{name}] package is not visible under {category}"
            )

    @PageService()
    def _add_workflow(self, name):
        """Add workflow"""
        self.__search_package(name, "Workflows")
        self.__click_package(name)

    @PageService()
    def _add_report(self, report_name):
        """Add report"""
        self.__search_package(report_name, "Reports")
        self.__click_package(report_name)

    @PageService()
    def _add_tools(self, tool_name):
        """Add tool"""
        self.__search_package(tool_name, "Tools")
        self.__click_package(tool_name)

    @PageService()
    def _add_alert(self, alert_name):
        """Add alert"""
        self.__search_package(alert_name, "Alerts")
        self.__click_package(alert_name)

    @PageService()
    def add_components(self, workflows=None, reports=None, tools=None, alerts=None):
        """Add component

        Args:
            workflows (list): Workflows
            reports (list): Reports
            tools (list): Tools
            alerts (list): Alerts
        """

        workflows = workflows if workflows else []
        reports = reports if reports else []
        tools = tools if tools else []
        alerts = alerts if alerts else []

        self.__click_add_component()
        self.__apps_page.wait_for_load_complete()
        for report in reports:
            self._add_report(report)
        for workflow in workflows:
            self._add_workflow(workflow)
        for alert in alerts:
            self._add_alert(alert)
        for tool in tools:
            self._add_tools(tool)
        self.__click_done()
        self.__apps_page.wait_for_load_complete()

    @PageService()
    def set_name(self, name):
        """Set App name"""
        self.__set_name_input(name)

    @PageService()
    def set_primary_component(self, name):
        """Set primary component"""
        self.__set_primary_component(name)

    @PageService()
    def save(self):
        """Save app"""
        self.__click_finish()
        self.__apps_page.wait_for_load_complete()
