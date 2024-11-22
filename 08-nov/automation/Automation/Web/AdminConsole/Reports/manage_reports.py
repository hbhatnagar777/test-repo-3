from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
reports listing page of the AdminConsole
"""

import time

from selenium.common.exceptions import (
    WebDriverException,
    NoSuchElementException
)

from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.AdminConsole.Components.panel import RModalPanel
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.core import Checkbox
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.page_container import PageContainer
from Reports.storeutils import StoreUtils
from Web.WebConsole.Store import storeapp
from Web.AdminConsole.Adapter.WebConsoleAdapter import WebConsoleAdapter

_STORE_CONFIG = StoreUtils.get_store_config()


class _MockBrowser:

    def __init__(self, driver):
        self.driver = driver


class ManageReport:
    """Class for Reports Page"""

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self.checkbox = Checkbox(self._admin_console)
        self.rtable = Rtable(self._admin_console)
        self.rmodal_panel = RModalPanel(self._admin_console)
        self.page_container = PageContainer(self._admin_console)

    @WebAction()
    def __click_page_action_item(self, item):
        """Clicks on the given item under the page level action menu"""
        if self.__is_subscription_page():
            self._driver.find_element(By.XPATH, f"//li[.='{item}']").click()
        else:
            item = self._driver.find_element(By.XPATH, f"//button[.='{item}']")
            item.click()

    @WebAction()
    def __set_search(self, string):
        """Sets the given search string"""
        search = self._driver.find_element(
            By.XPATH, "//div[contains(@class,'page-action')]//input[@id='searchReportsField']")
        search.clear()
        search.send_keys(string)
        time.sleep(2)

    @WebAction()
    def __hover_on_report(self, report_name):
        """Hovers on the given report"""
        report_xpath = self._driver.find_element(By.XPATH,f"//div[@id='reportList']//following::"
                                                          f"a[@title='{report_name}']")
        actions_xpath = self._driver.find_element(By.XPATH, f"//div[@id='reportList']//following::"
                                                            f"a[@title='{report_name}']//following::button")
        self._admin_console.mouseover_and_click(
            mouse_move_over=report_xpath, mouse_click=actions_xpath
        )

    @WebAction()
    def __click_actions_of_a_report(self, report_name):
        """Clicks the actions of a given report"""
        actions = self._driver.find_element(By.XPATH,
                                            f"//div[@id='reportList']//following::"
                                            f"a[@title='{report_name}']//following::button")
        actions.click()

    @WebAction()
    def __click_actions_menu_item(self, menu_item):
        """Click actions menu option"""
        item = self._driver.find_element(By.XPATH, f"//li[@role='menuitem']//button[@aria-label='{menu_item}']")
        item.click()

    @WebAction()
    def __actions_menu(self):
        """Click Actions menu"""
        if self.__is_subscription_page():
            menu = self._driver.find_element(By.XPATH, "//div[text()='Manage']")
        else:
            menu = self._driver.find_element(By.XPATH, "//button[@aria-label='Actions']")
        menu.click()

    @WebAction()
    def __click_report(self, report_name):
        """Clicks Report"""
        xp = f"//*[@title='{report_name}' and @href]"
        links = [link for link in self._driver.find_elements(By.XPATH, xp)
                 if link.is_displayed()]
        if not links:
            raise NoSuchElementException(f"XPath {xp} not found")
        links[0].click()

    @WebAction()
    def __is_report_displayed(self, report_name):
        """Checks whether the report is displayed """
        report = self._driver.find_elements(By.XPATH, f"//*[@title='{report_name}']")
        if not report:
            return False
        return True if report[0].is_displayed() else False

    @WebAction()
    def __view_menu(self):
        """Clicks the view dropdown"""
        view = self._driver.find_element(By.XPATH,
                                         "//div[contains(@class,'page-action-item')][1]//span[contains(@class,'dropdownArrow')]"
                                         )
        view.click()

    @WebAction()
    def __get_dashboard_title(self):
        """
        get the report title

        Returns: report title
        """
        title_obj = self._driver.find_elements(By.XPATH, "//*[contains(@class, 'page-title')]")
        return title_obj[0].text

    @WebAction()
    def __click_update_report_icon(self):
        """Click update button"""
        link = self._driver.find_element(By.XPATH,
                                         "//*[contains(@class,'store-updates-label')]"
                                         )
        link.click()

    @WebAction()
    def __click_goto_store_for_update(self):
        """Click goto store"""
        btn = self._driver.find_element(By.XPATH,
                                        "//button[.='Go to store to update']"
                                        )
        btn.click()
        self._driver.switch_to.window(
            self._driver.window_handles[-1]
        )

    @WebAction()
    def __get_reports_available_for_update(self):
        """Get the list of reports available for update"""
        reports = self._driver.find_elements(By.XPATH,
                                             "//*[contains(@class,'report-with-update')]"
                                             )
        return [report.text.strip() for report in reports]

    @WebAction()
    def __is_subscription_page(self):
        """ Check if subscription is enabled for reports page"""
        xpath = "//div[@id='ReportSelfSubscriptionTable']"
        table = self._driver.find_elements(By.XPATH, xpath)
        if table:
            return True
        else:
            return False

    def __filter_subscriptions(self, schedule_name, subscription_type):
        """
        filters the subscriptions
        Returns: checkbox element id
        """
        # self.rtable.apply_filter_over_column('Name', schedule_name)
        if subscription_type == 1:
            element_id = f'{schedule_name}_SubscribeForMe'
        elif subscription_type == 2:
            element_id = f'{schedule_name}_SubscribeForTenantAdmin'
        else:
            raise CVWebAutomationException("unsupported subscription type pass 1 for user and 2 for user group")
        return element_id

    @PageService()
    def access_commcell_health(self, commcell_name):
        """ Access the commcell health report """
        self.page_container.select_tab("Health")
        self._admin_console.wait_for_completion()
        self.rtable.access_link(commcell_name)

    @PageService()
    def select_commcell_name(self, commcell_name):
        """ Access the commcell health report """
        self.page_container.select_tab("CommCells")
        self._admin_console.wait_for_completion()
        self.rtable.access_link(commcell_name)

    @PageService()
    def access_dashboard(self):
        """Access the Worldwide Dashboard report"""
        self.page_container.select_tab("Dashboard")

    @PageService()
    def access_commcell_group(self):
        """ Access the commcell groups page """
        self.page_container.select_tab("CommCell groups")

    @PageService()
    def get_dashboard_title(self):
        """
        get the report title

        Returns: report title
        """
        return self.__get_dashboard_title()

    @PageService()
    def access_commcell(self):
        """ Access the commcells page  """
        self.page_container.select_tab("CommCells")

    @PageService()
    def access_health(self):
        """ Access the commcells page  """
        self.page_container.select_tab("Health")

    @PageService()
    def access_report_tab(self):
        """ Access the reports tab """
        self.page_container.select_tab(self._admin_console.props['label.nav.reports'])

    @PageService()
    def check_subscription_checkbox(self, schedule_name, subscription_type):
        """
        Check the checkbox to enable subscription
        Args:
            schedule_name (str): name of the schedule
            subscription_type (int): 1 for user, 2 for user group
        """
        element_id = self.__filter_subscriptions(schedule_name, subscription_type)
        self.checkbox.check(id=element_id)
        self._admin_console.wait_for_completion()

    @PageService()
    def uncheck_subscription_checkbox(self, schedule_name, subscription_type):
        """
        Check the checkbox to enable subscription
        Args:
            schedule_name (str): name of the schedule
            subscription_type (int): 1 for user, 2 for user group
        """
        element_id = self.__filter_subscriptions(schedule_name, subscription_type)
        self.checkbox.uncheck(id=element_id)
        self._admin_console.wait_for_completion()

    @PageService()
    def view_schedules(self):
        """View Schedules"""
        self.__actions_menu()
        if self.__is_subscription_page():
            self.__click_page_action_item("Schedules")
        else:
            self.__click_page_action_item("View schedules")
        self._admin_console.wait_for_completion()

    @PageService()
    def view_alerts(self):
        """View alerts"""
        self.__actions_menu()
        if self.__is_subscription_page():
            self.__click_page_action_item("Alerts")
        else:
            self.__click_page_action_item("View alerts")
        self._admin_console.wait_for_completion()

    @PageService()
    def is_report_exists(self, report_name):
        """ Returns true if report exists else false

        Args:
            report_name: Name of the report

        Returns(bool):  True/False

        """
        return self.__is_report_displayed(report_name)

    @PageService()
    def add_report(self):
        """Adds report"""
        self.__actions_menu()
        try:
            self.__click_page_action_item('Add report')
        except WebDriverException:
            self.__actions_menu()
            raise CVWebAutomationException("Add report is not available")

        self._driver.switch_to.window(self._driver.window_handles[1])
        self._admin_console.wait_for_completion()

    @PageService()
    def import_template(self):
        """Imports template"""
        self.__actions_menu()
        self.__click_page_action_item("Import report")

    @PageService()
    def connect_to_store(self):
        """Connects to store"""
        self.__actions_menu()
        self.__click_page_action_item("Connect to store")
        self._admin_console.wait_for_completion()

    @PageService()
    def access_report(self, report_name):
        """Search reports page

        Args:
            report_name(str): Name of the report

        """
        if self.__is_subscription_page():
            self._admin_console.scroll_into_view("//div[@id='ReportSelfSubscriptionTable']")
            self._admin_console.select_hyperlink(report_name)
        else:
            self.__set_search(report_name)
            self.__click_report(report_name)
        self._admin_console.wait_for_completion()

    @PageService()
    def edit_report(self, report_name):
        """Edits the given report

        Args:__click_actions
            report_name(str): Name of the report

        """
        self.__hover_on_report(report_name)
        try:
            self.__click_actions_menu_item("Edit")
        except WebDriverException:
            raise CVWebAutomationException("User has no privileges")
        self._admin_console.wait_for_completion()

    @PageService()
    def report_permissions(self, report_name):
        """Access the security panel for the given report

        Args:
            report_name(str): Name of the report

        """
        self.__hover_on_report(report_name)
        self.__click_actions_menu_item("Security")
        self._admin_console.wait_for_completion()

    @PageService()
    def delete_report(self, report_name):
        """Deletes the given report

        Args:
            report_name(str): Name of the report

        """
        try:
            self.__set_search(report_name)
            self.__hover_on_report(report_name)
        except NoSuchElementException:
            return
        try:
            self.__click_actions_menu_item("Delete")
            self.__click_page_action_item("Yes")
        except WebDriverException:
            raise CVWebAutomationException("User has no privileges")
        self._admin_console.wait_for_completion()

    @PageService()
    def get_reports_available_for_update(self):
        """Get the reports which has an update to install from store"""
        self.__click_update_report_icon()
        reports = self.__get_reports_available_for_update()
        self.__click_update_report_icon()
        return reports

    @PageService(hide_args=True)
    def goto_store_for_update(self,
                              username=_STORE_CONFIG.PREMIUM_USERNAME,
                              password=_STORE_CONFIG.PREMIUM_USERNAME):
        """Goto to store to update reports which have updates"""
        browser = _MockBrowser(self._driver)
        self.__click_update_report_icon()
        self.__click_goto_store_for_update()
        wc = WebConsoleAdapter(self._admin_console, browser)
        storeapp.StoreLogin(wc).login(username, password)
        storeapp.StoreApp(wc).wait_till_load_complete()

    @PageService()
    def goto_commcell_reports(self, report_name=None, commcell_name=None):
        """
        Goto commcell reports page
        Args:
            report_name: name of the report to access
            commcell_name: name of the commcell whose report to be accessed
        """
        self.access_commcell()
        self.rtable.access_link(commcell_name)
        self.access_report_tab()
        self.access_report(report_name)


class Tag:
    """Class to deal with the Tags panel"""

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self.rmodal_panel = RModalPanel(self._admin_console)
        self.rdialog = RModalDialog(self._admin_console)

    @WebAction(delay=1)
    def _enter_tag_name(self, tag_name):
        """enter tag name"""
        self.rmodal_panel.search_and_select(select_value=tag_name, id="tagsAutoComplete")

    @WebAction()
    def _get_tags(self):
        """reads the associated tag names"""
        xpath = "//*[@class='group-tag-name']/span"
        tags = []
        tags_obj = self._driver.find_elements(By.XPATH, xpath)
        for e_tag in tags_obj:
            tags.append(e_tag.text)
        return tags

    @WebAction()
    def __click_tag(self):
        """
        click the tag from dropdown
        """
        xpath = "//li[@role='menuitem']//button[.='Tag']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __click_tile_action(self):
        """clicks the custom tag name provided"""
        xpath = "//div[@id='reportsList']/..//following-sibling::div//button"
        tag_elem = self._driver.find_element(By.XPATH, xpath)
        tag_elem.click()

    @WebAction()
    def __click_on_edit_tag(self, tag_name):
        """clicks on the tags name"""
        tag_xpath = f"//*[@class='group-tag-name']//a[text() = '{tag_name}']"
        tag_element = self._driver.find_element(By.XPATH, tag_xpath)
        edit_tag_xpath = f"//a[text() = '{tag_name}']/..//span[@title='Edit tag']"
        edit_tag_element = self._driver.find_element(By.XPATH, edit_tag_xpath)
        self._admin_console.mouseover_and_click(
            mouse_move_over=tag_element, mouse_click=edit_tag_element
        )

    @WebAction()
    def __hover_on_report(self, report_name):
        """Hovers on the given report"""
        report_xpath = self._driver.find_element(By.XPATH, f"//div[@id='reportList']//following::"
                                                           f"a[@title='{report_name}']")
        actions_xpath = self._driver.find_element(By.XPATH, f"//div[@id='reportList']//following::"
                                                            f"a[@title='{report_name}']//following::button")
        self._admin_console.mouseover_and_click(
            mouse_move_over=report_xpath, mouse_click=actions_xpath
        )

    @WebAction()
    def __set_tag_name(self, new_name):
        """ passes tag name to the edited tag field"""
        element = self._driver.find_element(By.XPATH, "//input[@id='tagName']")
        self._driver.execute_script("arguments[0].value=arguments[1];", element, new_name)
        self.rmodal_panel.save()

    @WebAction()
    def _click_delete_tag(self, tag_name):
        """click on delete icon on tag name"""
        xpath = f"//*[@id='editTagForm']//span[text()='{tag_name}']/..//*[@data-testid='CancelIcon']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __read_tags(self):
        """Reads the Tags from reports landing page"""
        return [
            tag.text.strip() for tag in
            self._driver.find_elements(By.XPATH, "//*[contains(@class,'group-tag-name-content')]")
            if len(tag.text.strip()) > 0
        ]

    @PageService()
    def tag_report(self, report_name):
        """Tags the given report

        Args:
            report_name(str): Name of the report
        """
        self.__hover_on_report(report_name)
        self.__click_tag()
        self._admin_console.wait_for_completion()

    @PageService()
    def get_tags(self):
        """Returns the visible Tags in reports landing page"""
        return self.__read_tags()

    @PageService()
    def click_tag(self, tag_name):
        """Clicks the custom tags"""
        self.__click_tile_action()
        self.__click_tag(tag_name)

    @PageService()
    def apply_to_all(self):
        """Enable appy to all"""
        self.rdialog.enable_toggle('applyTagChangesToAllUsers', 'Apply tag changes to all users')
        self.rmodal_panel.save()

    @PageService()
    def save(self):
        """Saves the Tag panel"""
        self._admin_console.click_button('Save')
        self._admin_console.wait_for_completion()

    @PageService()
    def create_tag(self, tag_name, apply_to_all=False):
        """Create a Tag

        Args:
            tag_name (str): name of the Tag

            apply_to_all (bool): True/False

        """
        self._enter_tag_name(tag_name)
        if apply_to_all:
            self.rdialog.enable_toggle('applyTagChangesToAllUsers', 'Apply tag changes to all users')
        else:
            self.rdialog.disable_toggle('applyTagChangesToAllUsers', 'Apply tag changes to all users')
        self.rmodal_panel.save()

    @PageService()
    def edit_tag(self, current_name, new_name):
        """Edits Tag name

        Args:
            current_name: current name for the tag

            new_name: new name which replaces current name

        """
        self.__click_on_edit_tag(current_name)
        self.__set_tag_name(new_name)
        self._admin_console.wait_for_completion()

    @PageService()
    def get_associated_tags(self):
        """Returns the assoicated Tags"""
        return self._get_tags()

    @PageService()
    def delete_tag(self, tag_name):
        """
        Delete the tag
        Args:
            tag_name: Name of the Tag

        """
        self._click_delete_tag(tag_name)
        self.rmodal_panel.save()
        self._admin_console.wait_for_completion()
