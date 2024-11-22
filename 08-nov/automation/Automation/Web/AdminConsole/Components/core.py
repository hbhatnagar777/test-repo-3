# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""

Toggle:

    is_enabled()                    :     Method to check if toggle is enabled

    enable()                        :     Method to enable the toggle

    disable()                       :     Method to disable the toggle

    is_exists()                     :     Method to check if toggle is available

    is_editable()                   :     Method to check if toggle can be enabled or disabled

Checkbox:

    is_checked()                    :     Method to check if checkbox is checked

    check()                         :     Method to check the checkbox

    uncheck()                       :     Method to uncheck the checkbox

    is_exists()                     :     Method to check if checkbox is available

    is_editable()                   :     Method to check if checkbox can be checked or unchecked

TreeView:

    select_all()                    :     Method to select all items in the tree

    clear_all()                     :     Method to clear selected items in the tree

    clear_all_selected()            :     Method to clear selected items using Clear all

    check_show_selected()           :     Method to show only selected items

    uncheck_show_selected()         :     Method to show all items

    select_items()                  :     Method to select items in the tree

    unselect_items()                :     Method to unselect items in the tree

    expand_or_collapse_node()       :     Method to expand or collapse node in the tree

CalendarView:

   open_calendar()                  :     Open the calendar component

    read_date()                     :     Reads the date value next to given label str

    set_date()                      :     Click on the 'Set' button on CalendarView component

    select_date()                   :     Set the date value in component

    select_time()                   :     Set the time value in the component

    set_date_and_time()             :     Set date and time from CalendarView

SearchFilter:

    click_filter()                     :  clicks filter in search bar

    clear_search()                     :  clears applied filters or searched value

    apply_input_type_filter()          :  applies input type filter

    apply_dropdown_type_filter()       :  applies dropdown filter

    submit()                           :  clicks submit

FacetPanel:

    click_value_of_facet()              :  clicks facet value

    get_values_from_facet()              :  gets values from facet


RfacetPanel:

    select_value_in_dropdown()      :     Selects value from dropdown inside filter facet panel


"""
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.adminconsole import AdminConsole
from selenium.webdriver.remote.webelement import WebElement
from typing import List
import re
import time


class Toggle:
    """ Toggle Class """

    def __init__(self, admin_console, base_xpath=''):
        """Initalize the toggle class

        Args:
            admin_console    :   Instance of AdminConsoleBase

            base_xpath       :   Base component xpath to avoid collision
                                (eg: To handle toggles on dialog, send dialog's base xpath in the args)
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._xpath = base_xpath + "//*[text()='{0}']//ancestor::div[contains(@class, 'tile-row')" \
                                   " or contains(@class, 'teer-toggle')]//input"

    @WebAction()
    def __get_toggle_element(self, label=None, id=None):
        """Method to get the toggle element"""
        if label:
            return self._driver.find_element(By.XPATH, self._xpath.format(label))

        if id:
            return self._driver.find_element(By.ID, id)

        raise CVWebAutomationException('Either label or id is required as parameter')

    @WebAction()
    def __click_on_toggle(self, label=None, id=None):
        """Method to click on toggle"""
        self.__get_toggle_element(label, id).click()

    @PageService()
    def is_enabled(self, label=None, id=None):
        """ Method to get Status of the toggle

        Args:
            label   (str):   Label corresponding to the toggle option
            id      (str):   toggle id (refer id from input tag)
        """
        return self.__get_toggle_element(label, id).is_selected()

    @PageService()
    def enable(self, label=None, id=None):
        """ Method to Enable the toggle

        Args:
            label   (str):   Label corresponding to the toggle option
            id      (str):   toggle id (refer id from input tag)
        """
        status = self.is_enabled(label, id)
        if not status:
            self.__click_on_toggle(label, id)
            self._admin_console.wait_for_completion()

    @PageService()
    def disable(self, label=None, id=None):
        """ Method to Disable the toggle

        Args:
            label   (str):   Label corresponding to the toggle option
            id      (str):   toggle id (refer id from input tag)
        """
        status = self.is_enabled(label, id)
        if status:
            self.__click_on_toggle(label, id)
            self._admin_console.wait_for_completion()

    @PageService()
    def is_exists(self, label=None, id=None):
        """ Method to check if the toggle is available on the window

        Args:
            label   (str):   Label corresponding to the toggle option
            id      (str):   toggle id (refer id from input tag)
        """
        try:
            self.__get_toggle_element(label, id)
        except NoSuchElementException:
            return False
        else:
            return True

    @PageService()
    def is_editable(self, label=None, id=None):
        """ Method to check if the toggle is editable

        Args:
            label   (str):   Label corresponding to the toggle option
            id      (str):   toggle id (refer id from input tag)
        """
        editable = self.__get_toggle_element(label, id).is_enabled()
        return True if editable else False


class Checkbox:
    """ Checkbox Class """

    def __init__(self, admin_console, base_xpath=''):
        """Initalize the Checkbox class

        Args:
            admin_console    :   Instance of AdminConsoleBase

            base_xpath       :   Base component xpath to avoid collision
                                (eg: To handle checkbox on dialog, send dialog's base xpath in the args)
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._xpath = base_xpath + "//*[text()='{0}']//ancestor::div[contains(@class, 'k-mid') " \
                                   "or contains(@class, 'teer-checkbox') " \
                                   "or contains(@class, 'k-treeview-top') " \
                                   "or contains(@class, 'k-treeview-mid') " \
                                   "or contains(@class, 'k-treeview-bot') " \
                                   "]//input"
        self.partial_selection = False

    @WebAction()
    def __get_checkbox_element(self, label=None, id=None):
        """Method to get the checkbox element"""
        if label:
            selector = [f"text()='{label}'", f"contains(text(), '{label}')"][self.partial_selection]
            xp = self._xpath.replace("text()='{0}'", f"{selector}")
            return self._driver.find_element(By.XPATH, xp)

        if id:
            return self._driver.find_element(By.ID, id)

        raise CVWebAutomationException('Either label or id is required as parameter')

    @WebAction()
    def __click_on_checkbox(self, label=None, id=None):
        """Method to click on checkbox"""
        self.__get_checkbox_element(label, id).click()

    @PageService()
    def is_checked(self, label=None, id=None):
        """Method to get Status of the checkbox

        Args:
            label   (str):   Label corresponding to the checkbox option
            id      (str):   checkbox id (refer id from input tag)
        """
        return self.__get_checkbox_element(label, id).is_selected()

    @PageService()
    def check(self, label=None, id=None):
        """Method to check the checkbox

        Args:
            label   (str):   Label corresponding to the checkbox option
            id      (str):   checkbox id (refer id from input tag)
        """
        status = self.is_checked(label, id)
        if not status:
            self.__click_on_checkbox(label, id)

    @PageService()
    def uncheck(self, label=None, id=None):
        """Method to uncheck the checkbox

        Args:
            label   (str):   Label corresponding to the checkbox option
            id      (str):   checkbox id (refer id from input tag)
        """
        status = self.is_checked(label, id)
        if status:
            self.__click_on_checkbox(label, id)

    @PageService()
    def is_exists(self, label=None, id=None):
        """Method to check if the checkbox is available on the window

        Args:
            label   (str):   Label corresponding to the checkbox option
            id      (str):   checkbox id (refer id from input tag)
        """
        try:
            self.__get_checkbox_element(label, id)
        except NoSuchElementException:
            return False
        else:
            return True

    @PageService()
    def is_editable(self, label=None, id=None):
        """Method to check if the checkbox is editable

        Args:
            label   (str):   Label corresponding to the checkbox option
            id      (str):   checkbox id (refer id from input tag)
        """
        editable = self.__get_checkbox_element(label, id).is_enabled()
        return True if editable else False


class TreeView:
    """TreeView Component used in Command Center"""

    def __init__(self, admin_console, xpath=None):
        """
        Initialize the TreeView object

        Args:
            admin_console : Instance of AdminConsoleBase

            xpath : Base xpath (Optional)
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._action = ActionChains(self._driver)
        self.__base_xpath = "//*[contains(@class, 'treeview-tree-content')]"
        if xpath:
            self.__base_xpath = xpath + self.__base_xpath
        self.__toggle = Toggle(admin_console, self.__base_xpath)
        self.__checkbox = Checkbox(admin_console, self.__base_xpath)

    @WebAction()
    def __wait_for_spinner(self, wait_time: int) -> None:
        """Wait for spinner to load for folder"""
        waiter = WebDriverWait(self._driver, wait_time, poll_frequency=2)
        waiter.until_not(
            ec.presence_of_element_located(
                (By.XPATH, self.__base_xpath + "//span[contains(@class, 'k-i-loading')]"))
        )

    @WebAction()
    def __clear_tree_selection(self):
        """Clear selected nodes from the Tree"""
        self._driver.find_element(By.XPATH,
                                  "//div[@class='popup-menu-anchor anchor-btn']"
                                  "[@id='selectAllCheckbox-popupmenu-anchor']").click()
        self._driver.find_element(By.XPATH,
                                  "//div[contains(text(), 'Clear all')]/ancestor::li").click()

    @PageService()
    def select_all(self):
        """Method to select all the items"""
        self.__checkbox.check(id='selectAllCheckbox')

    @PageService()
    def clear_all(self):
        """Method to clear all selected items"""
        self.__checkbox.uncheck(id='selectAllCheckbox')

    @PageService()
    def clear_all_selected(self):
        """Method to clear all selected items"""
        self.__clear_tree_selection()

    @PageService()
    def show_selected(self):
        """Method to show only selected items"""
        self.__checkbox.check(id='showSelectedCheckbox')

    @PageService()
    def show_all(self):
        """Method to show all items"""
        self.__checkbox.uncheck(id='showSelectedCheckbox')

    @WebAction()
    def __get_search_bar(self):
        """Method to get search bar element"""
        search_bar = self._driver.find_element(By.XPATH, self.__base_xpath + "//input[@id='treeview search']")
        return search_bar

    @PageService()
    def __search_bar_exists(self):
        """Checks if search bar exists or not"""
        search_bar_xp = self.__base_xpath + "//input[@id='treeview search']"
        return self._admin_console.check_if_entity_exists("xpath", search_bar_xp)

    @WebAction()
    def clear_search(self):
        """Method to clear the search bar"""
        self.__get_search_bar().send_keys(u'\ue009' + 'a' + u'\ue003')  # CTRL + A + Backspace

    @WebAction()
    def set_search_text(self, keyword, wait_time=0):
        """
        Method to search for a particular Keyword

            Args:
                keyword   (str) : Keyword to search for
                wait_time (int) : Wait time to get the search results
        """
        search_bar = self.__get_search_bar()
        self.clear_search()
        search_bar.send_keys(keyword)
        if wait_time:
            self._driver.implicitly_wait(wait_time)

    @WebAction()
    def __choose_items(self, items, select_items=True, skip_items=False, wait_time=0):
        """
        Searches for items in the Tree, selects/unselects based on parameter select_items

            Args:
                items (list)        : list of items to search in Tree View
                select_items (bool) : whether to select or unselect the items
                skip_items  (bool)  : Skips the items if not found in the Tree View
                wait_time (int) : Wait time to get the search results

        """
        search_bar_exists = self.__search_bar_exists()
        for item in items:
            if search_bar_exists:
                self.set_search_text(item, wait_time)

            # if result not found, expand all the collapsed nodes available in the search result
            if not self.__checkbox.is_exists(item):
                while True:
                    # Find all currently visible collapsed nodes
                    collapsed_nodes = self._driver.find_elements(By.XPATH, "//*[@class='k-icon k-i-caret-alt-right']")

                    # If no more collapsed nodes are found, break the loop
                    if not collapsed_nodes:
                        break

                    for element in collapsed_nodes:
                        # Scroll into view and click to expand
                        self._driver.execute_script("arguments[0].scrollIntoView();", element)
                        element.click()
                        time.sleep(1)

                    # Short pause to allow the DOM to update after each expansion
                    time.sleep(1)

            # if result still not found, then skip this item and continue if skip flag is set
            if not self.__checkbox.is_exists(item) and skip_items:
                continue

            # if already checked, then uncheck the item
            if self.__checkbox.is_checked(item):
                self.__checkbox.uncheck(item)

            if select_items:
                self.__checkbox.check(item)
            else:
                self.__checkbox.uncheck(item)

        self._driver.implicitly_wait(self._admin_console.implicit_wait_config)
        if search_bar_exists:
            self.clear_search()

    @PageService()
    def select_items(self, items, partial_selection=False, skip_items=False, wait_time=0):
        """
        Selects items from the Tree

            Args:
                items (list) : list of items to select

                partial_selection   (bool) :  Flag to check for partial match in checkbox label

                skip_items  (bool)  : Skips the items if not found in the Tree View

                wait_time (int) : Wait time to get the search results

            Example:
                items = ['Desktop', 'Music', 'Google Drive']
        """
        if partial_selection:
            self.__checkbox.partial_selection = True

        self.__choose_items(items, True, skip_items, wait_time)

    @PageService()
    def unselect_items(self, items):
        """
        Unselects items from the Tree

            Args:
                items (list) : list of items to unselect
        """
        self.__choose_items(items, select_items=False)

    @WebAction()
    def __get_collapser_element(self, corresponding_item, partial_selection=False, **kwargs):
        """Method to get collapser element"""
        corresponding_item_xpath = f"//*[text()='{corresponding_item}']" if not partial_selection else f"//*[contains(text(),'{corresponding_item}')]"
        element_xpath = self.__base_xpath + corresponding_item_xpath + "/preceding::span[contains(@class, 'k-icon')][1]"
        self._admin_console.wait_for_element_based_on_xpath(element_xpath) if kwargs.get("wait_for_element", False) else None
        return self._driver.find_element(By.XPATH, element_xpath)

    @PageService()
    def expand_path(self, path=None, partial_selection=False, wait_time=60):
        """
        Sequentially expand nodes on a path

            Args:
                path    (list)  --  Path to expand. Last entry should be selected.
                partial_selection   (bool)  --  checks for partial text on node
                wait_time   (int)   --  wait for spinner to disappear

        """
        def is_element_stale(element):
            """Method to check if element is stale"""
            try:
                element.tag_name
                return False
            except StaleElementReferenceException:
                return True

        if not path:
            path = []
        new_folder_created = False
        current_node = self._driver.find_element(By.XPATH, self.__base_xpath)
        for index, node in enumerate(path):
            selector = [f"text()='{node}'", f"contains(text(), '{node}')"][partial_selection]
            try:
                if index == 0:
                    next_node = current_node.find_element(By.XPATH,
                                                          f"./descendant::span[{selector}]/preceding::"
                                                          f"span[contains(@class, 'k-icon')][1]")
                elif index == len(path) - 1:
                    next_node = current_node.find_element(By.XPATH, f"./following::span[{selector}]")

                else:
                    next_node = current_node.find_element(By.XPATH,
                                                          f"./following::span[{selector}]/preceding::"
                                                          f"span[contains(@class, 'k-icon')][1]")
            except (NoSuchElementException, StaleElementReferenceException) as e:
                try:
                    self.perform_action_on_node("New folder", path[index - 1],partial_selection=partial_selection)
                    from Web.AdminConsole.Components.dialog import RModalDialog
                    folder_modal = RModalDialog(self._admin_console, title="Add folder")
                    folder_modal.fill_text_in_field("folderName", node)
                    folder_modal.click_submit()
                    if is_element_stale(current_node):
                        selector = [f"text()='{path[index-1]}'", f"contains(text(), '{path[index-1]}')"][partial_selection]
                        node_xpath = f"{self.__base_xpath}" + f"//*[{selector}]/preceding::span[contains(@class, 'k-icon')][1]"
                        current_node = self._driver.find_element(By.XPATH, node_xpath)
                    if index == len(path) - 1:
                        next_node = current_node.find_element(By.XPATH, f"./following::span[{selector}]")
                    else:
                        next_node = current_node.find_element(By.XPATH,
                                                              f"./following::span[{selector}]/preceding::"
                                                              f"span[contains(@class, 'k-icon')][1]")
                    new_folder_created = True
                except Exception as e:
                    raise Exception("Failed to create New folder with error {}".format(e))

            if index == len(path) - 1 and not new_folder_created:
                self._driver.execute_script("arguments[0].scrollIntoView();", next_node)
                next_node.click()
            else:
                expand_attr = next_node.get_attribute("class")
                if 'alt-right' in expand_attr or 'expand' in expand_attr:
                    self._driver.execute_script("arguments[0].scrollIntoView();", next_node)
                    next_node.click()
                    self.__wait_for_spinner(wait_time=wait_time)

            current_node = next_node

    @PageService()
    def expand_node(self, node_name, wait_time=60, partial_selection=False, **kwargs):
        """
        Method to expand a node

            Args:
                node_name (str) : corresponding node name
                wait_time (int) : wait for spinner to disappear
                partial_selection(bool):checks for partial text on node
        """
        collapser = self.__get_collapser_element(node_name, partial_selection, **kwargs)
        collapser_attr = collapser.get_attribute("class")
        if 'alt-right' in collapser_attr or 'expand' in collapser_attr:
            self._driver.execute_script("arguments[0].scrollIntoView();", collapser)
            collapser.click()
        self.__wait_for_spinner(wait_time=wait_time)

    @PageService()
    def collapse_node(self, node_name):
        """
        Method to collapse a node

            Args:
                node_name (str) : corresponding node name
        """
        collapser = self.__get_collapser_element(node_name)
        collapser_attr = collapser.get_attribute("class")
        if 'alt-down' in collapser_attr or 'collapse' in collapser_attr:
            self._driver.execute_script("arguments[0].scrollIntoView();", collapser)
            collapser.click()

    @WebAction()
    def perform_action_on_node(self, action, node_name, partial_selection=False):
        """
        Method to Perform Actions on a Particular node

            Args:
                node_name (str) : corresponding node name
                action   : Actions that need to be performed on a node
        """
        if not partial_selection:
            node_xpath = f"{self.__base_xpath}" + f"//*[text()='{node_name}']"
        else:
            node_xpath = f"{self.__base_xpath}" + f"//*[contains(text(),'{node_name}')]"
        element = self._driver.find_element(By.XPATH, node_xpath)
        actions = ActionChains(self._driver)
        actions.move_to_element(element).perform()
        action_xpath = node_xpath + f"//ancestor::span//span[@title='{action}']/descendant::button"
        self._driver.find_element(By.XPATH, action_xpath).click()

    @WebAction()
    def select_item_by_label(self, label):
        """
        Checks the element with the given label

        label   (str)   : Label name to select

        Returns None
        """
        self.__checkbox.check(label=label)


class RCalendarView:
    """CalendarView Component used in Command Center for React view"""

    def __init__(self, admin_console, base_xpath: str = '') -> None:
        """
                Initialize the CalendarView object

                Args:
                    admin_console   : Instance of AdminConsoleBase

                    base_xpath      : Base xpath under which calendar is located
                """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self.log = admin_console.log
        self._actions = ActionChains(driver=self._driver)
        self.__xp = base_xpath + "//div[@id='teer-calendar']"
        self.__month_abbr = {
            "january": "Jan",
            "february": "Feb",
            "march": "Mar",
            "april": "Apr",
            "may": "May",
            "june": "Jun",
            "july": "Jul",
            "august": "Aug",
            "september": "Sep",
            "october": "Oct",
            "november": "Nov",
            "december": "Dec"
        }

    @PageService()
    def is_calendar_exists(self) -> bool:
        """Checks if calendar component exists or not in the overview page of a client

        Returns :

            returns true if calendar component exists in the overview page
            else returns false

        """
        try:
            self._driver.find_element(By.XPATH, self.__xp)
            return True
        except NoSuchElementException:
            return False

    @WebAction()
    def __select_month(self, month):
        """Select month from the React Calendar"""
        month_xpath = "//div/p[@id='month-sel-btn']"
        self._admin_console.scroll_into_view(month_xpath)
        element = self._driver.find_element(By.XPATH, month_xpath)
        element.click()
        select_month = f"//button[text()='{month}']"
        self._admin_console.scroll_into_view(select_month)
        element = self._driver.find_element(By.XPATH, select_month)
        element.click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def __select_year(self, year):
        """select the year on the React Calendar"""
        year_xpath = "//div/p[@id='year-sel-btn']"
        self._admin_console.scroll_into_view(year_xpath)
        element = self._driver.find_element(By.XPATH, year_xpath)
        element.click()
        select_year = f"//button[text()='{year}']"
        self._admin_console.scroll_into_view(select_year)
        element = self._driver.find_element(By.XPATH, select_year)
        element.click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def __select_day(self, day):
        """Select day from the React Calendar"""
        day_xpath = f"//div[@id='day-{day}-btn']/div"
        element = self._driver.find_element(By.XPATH, day_xpath)
        element.click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def select_time(self, time_info):
        """Select the time from CalendarView
                   Args:
                       time_info   (str)  :   Time value as dictionary
        """
        time_xp = f"//button/div[text()='{time_info}']"
        try:
            if self._admin_console.check_if_entity_exists("xpath", time_xp):
                self._driver.find_element(By.XPATH, time_xp).click()
            elif self._admin_console.check_if_entity_exists(
                    "xpath", f"//*[text()='Enter custom time']/..//following-sibling::div//input"):
                self._admin_console.fill_form_by_xpath(
                    f"//*[text()='Enter custom time']/..//following-sibling::div//input", time_info)
        except NoSuchElementException or ElementClickInterceptedException:
            raise CVWebAutomationException('Element not found or not able to interact')

    @PageService()
    def select_date(self, date_dict):
        """Selects year from the React calendar
        Args
            date_dict (dict) -- Date value as dictionary
                                Eg,
                                {
                                    'year': 1999,
                                    'month': "March",
                                    'day': 21,
                                }
        """
        if self.is_calendar_exists():
            # Select year in calendar
            self.__select_year(year=date_dict['year'])

            # Convert month from number to abbreviation and select in calendar
            month_abbr = self.__month_abbr[date_dict['month'].lower()]
            self.__select_month(month=month_abbr)

            # Select the day
            self.__select_day(day=str(int(date_dict['day'])))
        else:
            raise CVWebAutomationException("Calendar does not exist")

    @PageService()
    def set_date_and_time(self, date_time_dict):
        """Method to set date and time from CalendarView

                Args:

                    date_time_dict      (dict)  :   Date value as dictionary
                                                    Eg,
                                                    {
                                                        'year': 1999,
                                                        'month': "March",
                                                        'day': 21,
                                                        'time': "5:03 AM" or "17:03:00"
                                                    }

                """
        self.select_date(date_time_dict)
        self.select_time(date_time_dict["time"])


class CalendarView:
    """CalendarView Component used in Command Center"""

    def __init__(self, admin_console, base_xpath: str = '', date_only: bool = False) -> None:
        """
        Initialize the CalendarView object

        Args:
            admin_console   : Instance of AdminConsoleBase

            base_xpath      : Base xpath under which calendar is located

            date_only       : set True for the date only version of Calendar
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._actions = ActionChains(driver=self._driver)
        self.date_only = date_only
        self.__xp = base_xpath + "//div[contains(@class, 'cv-date-time-picker-popup')]"
        self.__header = self.__xp + "//div[contains(@class, 'k-calendar-header')]"
        self.__time_view = self.__xp + "//div[contains(@class, 'k-timeselector')]"
        self.__month_abbr = {
            "january": "Jan",
            "february": "Feb",
            "march": "Mar",
            "april": "Apr",
            "may": "May",
            "june": "Jun",
            "july": "Jul",
            "august": "Aug",
            "september": "Sep",
            "october": "Oct",
            "november": "Nov",
            "december": "Dec"
        }

    @WebAction()
    def __get_view_state(self) -> str:
        """Returns the state of the calendar view
            Eg, monthview, yearview, decadeview, centuryview
        """
        calendar_view_xpath = self.__xp + "//div[contains(@class, 'k-calendar-view')]"
        # For example : "k-calendar-view k-vstack k-calendar-monthview". We are interested in 'monthview'
        calendar_classes = self.__get_element_class(calendar_view_xpath).split()

        return calendar_classes[-1].split('-')[-1]

    @WebAction()
    def __click_title_button(self) -> None:
        """Click the title button
        """
        title_button = self.__header + "//button[contains(@class, 'k-calendar-title')]"
        self._driver.find_element(By.XPATH, title_button).click()

    @WebAction()
    def __click_today_button(self) -> None:
        """Click on Today button"""
        today_button = self.__header + "//button[contains(@class, 'k-calendar-nav-today')]"
        self._driver.find_element(By.XPATH, today_button).click()

    @WebAction()
    def __get_element_class(self, xpath: str) -> str:
        """Returns the class attribute of the element

            Args:

                xpath       (str)       :   Xpath to get classes
        """
        return self._driver.find_element(By.XPATH, xpath).get_attribute("class")

    @WebAction()
    def __change_view_state(self, state: str, click_today=True) -> None:
        """Change the view state of the calendar view

            Args:
                click_today (bool)      :   Does not click on TODAY button when set to false
                state       (str)       :   State to reach to
        """

        title_button_xpath = self.__header + "//button[contains(@class, 'k-calendar-title')]"

        if self.__get_view_state() != state:
            # Clicking on TODAY button closes calendar, do not click is click_today is set to false
            if click_today and not self.date_only:  # date only calendars don't have today button, it is default
                self.__click_today_button()
            while self.__get_view_state() != state:
                if 'disabled' not in self.__get_element_class(title_button_xpath):
                    self.__click_title_button()
                    self._admin_console.wait_for_completion()
                else:
                    raise CVWebAutomationException("Title button is disabled")

    @WebAction()
    def __select_year(self, year: int, click_today=True) -> None:
        """Select year value in calendar

            Args:
                click_today (bool)  :   Does not click on TODAY button when set to false
                year        (int)   :   Year to select
        """
        self.__change_view_state("centuryview", click_today=click_today)
        decade_xpath = self.__xp \
                       + f"//td[contains(@class, 'k-calendar-td')]/span[contains(text(), '{(year // 10) * 10}')]"
        year_xpath = self.__xp + f"//td[contains(@class, 'k-calendar-td')]/span[contains(text(), '{year}')]"
        self._driver.find_element(By.XPATH, decade_xpath).click()
        self._driver.find_element(By.XPATH, year_xpath).click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def __select_month(self, month: str, click_today=False) -> None:
        """Select month in calendar

            Args:
                month        (str)   :   Month to select
                click_today (bool)   :   Clicks on TODAY button when set to true.
        """
        self.__change_view_state("yearview", click_today=click_today)
        calendar_tables = self.__xp + \
                          f"//tbody[1]//td[contains(@class, 'k-calendar-td')]/span[contains(text(), '{month}')]"
        self._driver.find_element(By.XPATH, calendar_tables).click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def __select_day(self, day: int, click_today=False) -> None:
        """Select day in calendar

            Args:
                day         (int)   :   Day to select
                click_today (bool)  :   Clicks on TODAY button when set to true.
        """
        self.__change_view_state("monthview", click_today=click_today)
        calendar_tables = self.__xp + \
                          f"//td[contains(@class, 'k-calendar-td')]/span[contains(text(), '{day}')]"
        self._driver.find_element(By.XPATH, calendar_tables).click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def __get_time_set(self) -> dict:
        """
        Returns the time currently set (from time view's title) as dict {'hour': xx, 'minute': xx, 'second': xx or
                                                                                                        'AM/PM': xx}
        """
        time_title_xpath = "//div[contains(@class, 'k-time-header')]//span[contains(@class, 'k-title')]"
        time_title = self._driver.find_element(By.XPATH, self.__time_view + time_title_xpath).text.strip()
        try:
            time_str, session = time_title.split(" ")
        except ValueError:
            time_str = time_title
            session = None
        if session is not None:
            hour, minute = [int(value) for value in time_str.split(":")]
            return {'hour': hour, 'minute': minute, 'AM/PM': session}
        else:
            hour, minute, second = [int(value) for value in time_title.split(":")]
            return {'hour': hour, 'minute': minute, 'second': second}

    @WebAction()
    def __click_time(self, component, value) -> None:
        """Clicks on the time on the time slider

            Args:

                component       (str)       :   The label of the time slider (hour/minute/second/AM/PM)

                value           (str)       :   The value to select
        """

        # If intercepted exception occurs, then the element has an overlay span on top which means it is already
        # selected (overlay span is the highlight, making it un-clickable), so we skip and continue,
        # we retry 5 times if required
        for _ in range(5):
            try:
                xpath = self.__time_view + \
                        f"//div[contains(@class, 'k-time-list-wrapper')]//span[contains(text(), '{component}')]" \
                        "/parent::div//ul/li"

                element = self._driver.find_elements(By.XPATH, xpath + f"/span[text() = '{value}']")
                if not element:
                    element = self._driver.find_elements(By.XPATH, xpath + f"/span[contains(text(), '{value}')]")
                element = element[0]
                self._actions = ActionChains(driver=self._driver)
                self._actions.move_to_element(element).perform()
                element.click()
                self._admin_console.wait_for_completion()
            except ElementClickInterceptedException:
                pass
            # if the passed hour/minute/session is set correctly, only then return
            if (component == 'AM/PM' and self.__get_time_set()[component] == value) \
                    or (component != 'AM/PM' and int(self.__get_time_set()[component]) == int(value)):
                return

    @WebAction()
    def __click_set(self) -> None:
        """Click on 'Set' button"""
        self._driver.find_element(By.XPATH, self.__xp + "//button[@title='Set']").click()
        self._admin_console.wait_for_completion()

    @PageService()
    def open_calendar(self, label) -> None:
        """Open the calendar component

        Args:

                label     (str)  :   Label shown in front of the date picker

        """
        cal_xpath = f"//label[@title='{label}']/parent::div/following-sibling::div//button"
        self._driver.find_element(By.XPATH, cal_xpath).click()

    @PageService()
    def read_date(self, label: str) -> str:
        """
        Reads the date shown left of date-picker

        Args:
            label   (str)   -   the label above of the date-picker

        Returns:
            date_str    (str)   -   the date string visible next to date picker
        """
        cal_xpath = f"//label[@title='{label}']/parent::div/following-sibling::div//input"
        return self._driver.find_element(By.XPATH, cal_xpath).get_attribute("value")

    @PageService()
    def set_date(self) -> None:
        """Select 'Set' button in CalendarView component"""
        self.__click_set()

    @PageService()
    def select_date(self, date_time_dict: dict, click_today=True) -> None:
        """Select the date from CalendarView

            Args:
                click_today (bool)          :   Does not click on TODAY button when set to false
                date_time_dict      (dict)  :   Date value as dictionary
                                                Eg,
                                                {
                                                    'year': 1999,
                                                    'month': "March",
                                                    'day': 21,
                                                }

        """

        # Select year in calendar
        self.__select_year(year=int(date_time_dict['year']), click_today=click_today)

        # Convert month from number to abbreviation and select in calendar
        month_abbr = self.__month_abbr[date_time_dict['month'].lower()]
        self.__select_month(month=month_abbr, click_today=click_today)

        # Select the day
        self.__select_day(day=date_time_dict['day'], click_today=click_today)

    @PageService()
    def select_time(self, time_dict) -> None:
        """Select the time from CalendarView

            Args:

                time_dict   (dict)  :   Time value as dictionary
                                        Eg, {
                                                'hour': 09,
                                                'minute': 19,
                                                'second': 10,
                                                'session': 'AM'
                                            }
        """

        # Select hour
        self.__click_time(component='hour', value=time_dict['hour'])

        # Select minute
        self.__click_time(component='minute', value=time_dict['minute'])

        if 'session' in time_dict:
            # Select am or pm
            session = time_dict['session'].upper()
            self.__click_time(component='AM/PM', value=session)

        if 'second' in time_dict:
            # Select second
            self.__click_time(component='second', value=time_dict['second'])

    @PageService()
    def set_date_and_time(self, date_time_dict):
        """Method to set date and time from CalendarView

                Args:

                    date_time_dict      (dict)  :   Date value as dictionary
                                                    Eg,
                                                    {
                                                        'year': 1999,
                                                        'month': "March",
                                                        'day': 21,
                                                        'hour': 09,
                                                        'minute': 19,
                                                        'second': 10,
                                                        'session': 'AM'
                                                    }

                """
        self.select_date(date_time_dict)
        self.select_time(date_time_dict)
        self.__click_set()


class SearchFilter:
    """Advance SearchFilter applied in search bar"""

    def __init__(self, admin_console):
        """Initialize the SearchFilter class

                Args:
                    admin_console       (obj)    :   Instance of AdminConsole class
                """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._xpath = "//div[@class='cvSearchFilter']"

    @WebAction()
    def __click_filter_icon(self):
        """clicks filter icon in search bar"""
        filter=self._driver.find_element(By.XPATH, self._xpath+"/a[@class='cvSearchFilter-icon animated-toggle button']")
        filter.click()

    @WebAction()
    def __clear_search_bar(self):
        """clear search bar"""
        clear = self._driver.find_element(By.XPATH, self._xpath + "/a[contains(@class,'cvSearchFilter-icon button')]")
        clear.click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def __apply_input_filter(self, filter_name, filter_value):
        """
        applies input filter by name or placeholder value
        Args:
            filter_name     (str)  -- name of filter
            filter_value     (str)  -- value to be entered in input
        """
        elem = self._driver.find_element(
            By.XPATH, self._xpath+f"//input[@name='{filter_name}' or @placeholder='{filter_name}']")
        elem.clear()
        elem.send_keys(filter_value)

    @WebAction()
    def __apply_dropdown_filter(self,filter_label,filter_values):
        """
        applies dropdown filter
        Args:
            filter_label     (str)  -- label name of filter
            filter_values    (list)  -- values to be selected in dropdown
        """
        from Web.AdminConsole.Components.panel import DropDown
        drop_down_obj=DropDown(self._admin_console)
        drop_down_obj.select_drop_down_values(drop_down_label=filter_label,values=filter_values,partial_selection=True)

    @WebAction()
    def __select_dropdown_value(self, drop_down_label, filter_value):
        """selects dropdown value
            Args:
                drop_down_label  (str)  -- item-label name of filter
                filter_value    (list)  -- value to be selected in dropdown
        """
        parent_xpath = f"//isteven-multi-select[@item-label='{drop_down_label}']"
        self._driver.find_element(By.XPATH, f"//isteven-multi-select[@item-label='{drop_down_label}']").click()
        self._admin_console.scroll_into_view(
            f"{parent_xpath}//span[@class='title' and normalize-space()='{filter_value}']")
        value = self._driver.find_element(
            By.XPATH, f"{parent_xpath}//span[@class='title' and normalize-space()='{filter_value}']")
        value.click()

    @WebAction()
    def __click_submit(self):
        """clicks submit"""
        self._driver.find_element(By.XPATH, self._xpath + "//*[@id='submit']").click()

    @PageService()
    def click_filter(self):
        """ click filter in search bar """
        self.__click_filter_icon()

    @PageService()
    def clear_search(self):
        """clear search"""
        self.__clear_search_bar()

    @PageService()
    def apply_input_type_filter(self, filter_name, filter_value):
        """
        applies input type filter by name or placeholder value
        Args:
            filter_name     (str)  -- name of filter
            filter_value     (str)  -- value to be entered in input
        """
        self.__apply_input_filter(filter_name, filter_value)

    @PageService()
    def apply_dropdown_type_filter(self, filter_label, filter_values):
        """
         applies dropdown filter
        Args:
            filter_label     (str)  -- label name of filter
            filter_values    (list)  -- values to be selected in dropdown
        """
        self.__apply_dropdown_filter(filter_label, filter_values)

    @PageService()
    def submit(self):
        """ clicks submit"""
        self.__click_submit()

    @PageService()
    def select_dropdown_value(self, item_label, filter_value):
        """selects dropdown value
            Args:
                item_label     (str)  -- label name of filter
                filter_value    (list)  -- values to be selected in dropdown
        """
        self.__select_dropdown_value(item_label, filter_value)


class FacetPanel:
    """Class to interact with Facet panel"""

    def __init__(self, admin_console, facet_name):
        """
        Initialize Facet Panel Object
        Args:
            admin_console       (obj)       --  Admin console class object
            facet_name          (str)       --  Name of the Facet
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._xpath = f"//div[@accordion-label='{facet_name}']//span[@class='ng-binding ng-scope']"

    @WebAction()
    def __get_facet_value_index(self, facet_value):
        """
        gets facet value index
        Args:
            facet_value        (str)  --  facet value that needs to be selected
        Raises:
            Exception                 --  if facet value not present
        """
        result = self.get_values_from_facet()
        for each_value in result:
            if each_value.startswith(facet_value):
                return result.index(each_value)
        raise NoSuchElementException(f"Rows not found with name [{facet_value}]")

    @WebAction()
    def __click_facet_value(self, facet_value):
        """
        clicks facet value
        Args:
            facet_value       (str)  --  facet value that needs to be selected
        """
        idx = self.__get_facet_value_index(facet_value)
        facet = self._driver.find_elements(By.XPATH, self._xpath)
        facet[idx].click()

    @WebAction()
    def __get_facet_values(self):
        """
        gets facet values
        Returns:
            result           (list)  --  list of all the values under required facet
        """
        result = []
        rows = self._driver.find_elements(By.XPATH, self._xpath)
        for row in rows:
            txt = row.text
            result.append(txt)
        return result

    @PageService()
    def click_value_of_facet(self, facet_value):
        """
        clicks facet value
        Args:
            facet_value      (str)  --  facet value
            Ex: pdf,past week..etc
        """
        self.__click_facet_value(facet_value)

    @PageService()
    def get_values_from_facet(self):
        """
        gets values from facet
        """
        return self.__get_facet_values()


class RfacetPanel:
    """ Class to interact with react Facet panel"""

    def __init__(self, admin_console, facet_panel_name):
        """Initialize the RfacetPanel class

        Args:
            admin_console       (obj)    :   Instance of AdminConsole class

            facet_panel_name    (str)    :   Name of facet filter panel
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._xpath = f"//li[contains(@class,'facet-panel')]/*//div[contains(@class,'header-title')]" \
                      f"/label[contains(text(),'{facet_panel_name}')]"

    @WebAction()
    def expand_facet(self):
        """Expands the facet window"""
        not_expand_xpath = self._xpath + "/ancestor::div/span[contains(@class,'glyphicon-chevron-down')]"
        if self._admin_console.check_if_entity_exists("xpath", not_expand_xpath):
            self._driver.find_element(By.XPATH, not_expand_xpath).click()
            self._admin_console.wait_for_completion()

    @PageService()
    def select_value_in_dropdown(self, drop_down_label, values):
        """Selects value in dropdown inside facet panel

            Args:

                drop_down_label (str)       --  Drop down item label

                values          list(str)   --  list of value to select in dropdown

            Returns:

                None

        """
        from Web.AdminConsole.Components.panel import DropDown
        drop_down = DropDown(self._admin_console)
        self.expand_facet()
        drop_down.select_drop_down_values(values=values, drop_down_label=drop_down_label)
        self._admin_console.wait_for_completion()


class BlackoutWindow:
    """Class to interact with react Blackout Window"""

    def __init__(self, admin_console: AdminConsole):
        """Initialize the BlackoutWindow class

        Args:
            admin_console       (obj)    :   Instance of AdminConsole class
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._xpath = "//*[@class='backup-window-content']"
        self.days_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    @WebAction()
    def __get_base_element(self) -> WebElement:
        """Method to get base element for BlackoutWindow component"""
        return self._driver.find_element(By.XPATH, self._xpath)

    @WebAction()
    def __get_element(self, xpath: str) -> WebElement:
        """Method to get element on Blackout Window"""
        base_element = self.__get_base_element()
        return base_element.find_element(By.XPATH, xpath)

    @WebAction()
    def __get_elements(self, xpath: str) -> List[WebElement]:
        """Method to get elements on Blackout Window"""
        base_element = self.__get_base_element()
        return base_element.find_elements(By.XPATH, xpath)

    @WebAction()
    def __get_slot_elements_for_a_day(self, day: str) -> List[WebElement]:
        """Method to get checkbox elements for a specified day"""
        slots_xpath = f".//*[@id='{self.days_list.index(day.lower().title())}']//*[contains(@class,'week-time ')]"
        return self.__get_elements(slots_xpath)

    def __convert_to_24_hrs(self, time: str) -> int:
        """Method to convert am, pm to 24 hour format"""
        if time == '12am':
            return 0
        elif time.endswith('am'):
            return int(time[:-2])
        elif time == '12pm':
            return 12
        else:
            return int(time[:-2]) + 12

    def __format_timings_range(self, time_ranges: list) -> List[tuple]:
        """
            Method to convert range of am, pm to range of 24 hour format

            Args:
                time_range (list)   --    List of range of timings.

                e.g: ['12am-5am', '9am-12pm', '2pm-6pm', '9pm-12am']
        """
        ranges = []
        for time_range in time_ranges:
            start_time, end_time = time_range.split('-')

            start_24h = self.__convert_to_24_hrs(start_time)
            end_24h = self.__convert_to_24_hrs(end_time)

            if end_24h == 0: end_24h = 24  # "12am" is considered as 24th hour if it is end timing

            ranges.append((start_24h, end_24h))
        return ranges

    @WebAction()
    def __slot_select_label(self) -> str:
        """Method to know what selecting slot means"""
        selected = "//*[contains(@class,'week-time selected')]//following-sibling::span"
        return self.__get_element(selected).text

    @WebAction()
    def __slot_deselect_label(self) -> str:
        """Method to know what deselecting slot means"""
        deselected = "//*[@class='legend-symbol week-time']//following-sibling::span"
        return self.__get_element(deselected).text

    @PageService()
    def get_labels(self) -> dict:
        """Method to get information of selection/deselection labels"""
        return {
            'Selected Slot': self.__slot_select_label(),
            'DeSelected Slot': self.__slot_deselect_label()
        }

    @PageService()
    def select_all_day(self, day: str) -> None:
        """
            Method to select all slots for a specified day

            Args:
                day (str)   --     Day to select (e.g: Monday, Tuesday)
        """
        self.select_values(day, ['12am-12am'])

    @PageService()
    def clear_all_day(self, day: str) -> None:
        """
            Method to deselect all slots for a specified day

            Args:
                day (str)   --     Day to select (e.g: Monday, Tuesday)
        """
        self.deselect_values(day, ['12am-12am'])

    @PageService()
    def select_all(self) -> None:
        """Method to select all the slots"""
        select_all_btn = "//button[normalize-space()='Select all']"
        self.__get_element(select_all_btn).click()

    @PageService()
    def clear_all(self) -> None:
        """Method to clear all the slots"""
        clear_btn = "//button[normalize-space()='Clear']"
        self.__get_element(clear_btn).click()

    @PageService()
    def get_blackout_window_config(self) -> dict:
        """
            Method to get configured blackout window

            Return Example:
                blackout_window = {
                    'Monday and Thursday' : ['All day'],
                    'Tuesday' : ['2am-6am', '1pm-6pm'],
                    'Tuesday through Thursday' : ['9pm-12am'],
                    'Wednesday' : ['5am-2pm'],
                    'Friday' : ['1am-3am', '5am-1pm'],
                    'Saturday' : ['2am-5am', '9am-12pm', '2pm-6pm', '9pm-12am'],
                    'Sunday' : ['1am-5am', '7am-1pm', '7pm-11pm']
                }
        """
        blackout_list = self.__get_elements("//*[@class='schedule-list-backup']//li")
        return {day.strip(): time.strip().split(', ') for schedule in blackout_list for day, time in
                [schedule.text.split(':', 1)]}

    @WebAction()
    def __edit_values(self, day: str, time_ranges: list, select: bool = True) -> None:
        """
            Method to either select or deselect time slots

            Args:
                day (str)           --  Day of the week
                time_ranges (list)  --  List of time ranges to configure blackout window
                select  (bool)      --  whether to select the slots or deselect
        """
        range_24h = self.__format_timings_range(time_ranges)
        for start, end in range_24h:
            check_boxes = self.__get_slot_elements_for_a_day(day)
            for element in check_boxes[start:end]:
                is_selected_class = 'selected' in element.get_attribute("class")
                if 1000 > self._admin_console.service_pack >= 37 or self._admin_console.service_pack >= 3700:
                    # backup window colors switched from SP37 onwards, we need to unselect for selecting
                    if select == is_selected_class:
                        element.click()
                elif select != is_selected_class:
                    element.click()

    @PageService()
    def select_values(self, day: str, time_ranges: list) -> None:
        """
            Method to select time range for specified day

            Args:
                day (str)           --  Day of the week
                time_ranges (list)  --  List of time ranges to configure blackout window

                time_ranges example: ['2am-5am', '9am-12pm', '2pm-6pm', '9pm-12am']
        """
        self.__edit_values(day, time_ranges)

    @PageService()
    def deselect_values(self, day: str, time_ranges: list) -> None:
        """
            Method to deselect time range for specified day

            Args:
                day (str)           --  Day of the week
                time_ranges (list)  --  List of time ranges to configure blackout window

                time_ranges example: ['2am-5am', '9am-12pm', '2pm-6pm', '9pm-12am']

        """
        self.__edit_values(day, time_ranges, select=False)

    @PageService()
    def edit_blackout_window(self, input: dict) -> None:
        """
            Method to process input dictionary and edit the blackout window according to provided input

            input   (dict)  :   key value pair of day and its blackout timings

            Example:
                input = {
                    'Monday and Thursday' : ['All day'],
                    'Tuesday' : ['2am-6am', '1pm-6pm'],
                    'Tuesday through Thursday' : ['9pm-12am'],
                    'Wednesday' : ['5am-2pm'],
                    'Friday' : ['1am-3am', '5am-1pm'],
                    'Saturday' : ['2am-5am', '9am-12pm', '2pm-6pm', '9pm-12am'],
                    'Sunday' : ['1am-5am', '7am-1pm', '7pm-11pm']
                }
        """
        self.clear_all()
        for days, time_range in input.items():
            time_range = ['12am-12am'] if time_range == ['All day'] else time_range

            if 'through' in days:
                start_day, end_day = days.split(' through ')
                start_index = self.days_list.index(start_day)
                end_index = self.days_list.index(end_day)

                for day in self.days_list[start_index:end_index + 1]:
                    self.select_values(day, time_range)

            elif 'and' in days:
                pattern = re.compile(f"({'|'.join(self.days_list)})")
                for day in pattern.findall(days):
                    self.select_values(day, time_range)

            else:
                self.select_values(days, time_range)
