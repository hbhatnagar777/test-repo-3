# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
** This is a protected class and should not be inherited directly. Use AdminConsole class. **
This module provides all the common functions or operations that can be
used by the complete AdminConsole Automation Package


Classes:

    _AdminConsoleBase() ---> object()


AdminConsoleBase   --  acts as the base class for all the other classes
                            such as _Navigator, login_page, and others

    Functions:

    __init__()                      --  initialize an instance of the AdminConsoleHelper class

    fill_form_by_id()               --  fill the values in a textfield specified by the id

    search_for()                    --  Opens the address specified in the url in the browser

    navigate()                      --  opens the url in browser

    get_driver_obj()                --  returns the webdriver object

    current_url()                   --  returns the currently opened url in the browser

    check_if_entity_exists()        --  checks whether an entity exists on the webpage or not

    wait_for_completion()           --  wait for the page to load

    select_value_from_dropdown()    --  Selects the value from the dropdown

    error_out_screenshot()          --  save the webpage screenshot

    cv_table_next_button_exists()   --  check if *next* button exists

    cv_table_click_next_button()    --  click on *next* button

    cv_table_click_first_button()   --  click on *first* button

    mouseover_and_click()           --  move mouse over and click on an element

    is_element_present()            --  Checks if the given element is present in the given parent
                                            tag

    scroll_into_view()              -- Scrolls to a particular element of the page

    label_getvalue                    -- Fetch the value corresponding to given label.

    tile_select_hyperlink           -- This selects the hyperlink at tile label level.

                                       hyperlink within tile wont be selected.

    cvselect_from_dropdown          -- Selects the value from the dropdown.Use this for cv multi
                                       select option

    select_radio                    -- Selects radio button given the value.

    submit_form                     -- Clicks save Button on open forms.

    toggle_enable                   -- Enables the toggle bar if disabled

    toggle_disable                  -- Disables the toggle bar if enabled

    enable_toggle                   -- Method to enable given toggle using index of toggle

    disable_toggle                  -- Method to disable given toggle using index of toggle

    toggle_edit                     -- Selects edit button next to toggle

    select_hyperlink                -- Selects hyperlink in the given page.

    click_by_xpath                  -- Clicks the element with the given path

    checkbox_select                 -- Selects all the checkbox that matches the IDs
                                       in the values lists

    checkbox_deselect               -- Deselects all the checkbox that matches the IDs
                                       in the values lists
    select_destination_host()       -- Selects a ESX host as destination host or snap mount ESX

    get_notification()              -- Gets the Job Text on submitted job

    get_jobid_from_popup()          -- Gets the job id from pop up

    click_yes_button()              -- Clicks on yes button

    check_error_message()           -- Checks if there is any error message

    get_error_message()             -- get error message if any on the page

    search_vm()                     -- Searches for the VM while selecting content or
                                       during restore

    get_locale_name()               -- Gets the name of the locale thats currently selected

    change_language()               -- Changes the language to the given one

    select_for_restore()            -- Selects files and folders for restore

    recovery_point_restore()        -- Restored data from the time selected in recovery points

    select_overview_tab()           -- Selects the overview tab

    select_configuration_tab()      -- Selects the configuration tab

    select_content_tab ()           -- Select the content tab

    select_distribution_tab()       -- Selects the distribution tab

    expand_options()                -- Expands the advanced options or other chevron elements

    snapshot_engine()               -- Sets the snapshot engine for the subclient

    backup_for_specific_date()      -- It will open the backed up contents from a specific date

    backup_for_date_range()         -- Opens the backed up content from a specific date range

    refresh_page()                  -- Refreshes the page

    open_new_tab()                  -- To open a new tab

    switch_to_latest_tab()          -- To switch to the latest tab

    close_current_tab()             -- To close the current tab

    check_radio_button()            -- Check if radio button exists

    access_sub_menu()               -- Method to click on the item under a dropdown
    in database page

    click_button()                  -- Clicks on button by text value or id value

    get_element_value_by_id()       -- Gets element value when given the Id

    click_button_using_id()         -- Method to click on a button using id

    click_button_using_text()       -- Method to click on a button using text

    search_aws_vm()                 -- Searches for the AWS VM while selecting content or
                                       during restore

    wait_for_element_to_be_clickable()  --  Wait for element to be clickable

    expand_cvaccordion()                --  Click the heading of an accordion using the label.

    select_report_tab()             --  Select the tab with the name specified in the report page

    fill_form_by_xpath()            --  Fills form for given xpath

    check_error_page()              --  Checks if page shows error while redirecting

    click_on_base_body()            --  Clicks on body tag to collapse menus/callouts

    is_any_parent_disabled()        --  Method to check if any parent element is disabled

    click_menu_backdrop()           --  Clicks on only mui-backdrop div to close menus

    access_jobs_notification()      -- Clicks on jobs notification to open callout on top header

    access_alerts_notification()    -- Clicks on alerts notification to open callout on top header

    access_events_notification()    -- Clicks on events notification to open callout on top header
"""
import inspect
import re
import time
import os
from time import sleep

from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException, WebDriverException,
    InvalidSelectorException
)
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.color import Color
from AutomationUtils import (constants, config)
from AutomationUtils import logger

from Web.AdminConsole.Helper.adminconsoleconstants import LocaleFile
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.Common.exceptions import (
    CVWebAutomationException
)


class _AdminConsoleBase(object):
    """
    ** This is a protected class and should not be inherited directly. Use AdminConsole class. **
    Base class for all the Admin Console pages
    """

    def __init__(self, driver, browser=None):
        self.driver = driver
        self.browser = browser
        self.url = self.current_url()
        self.log = logger.get_log()
        self.cb_flag = False
        self.ext = None
        self.loaded_locale_files = []
        self.props = {}
        self.locale_ids = {}
        self.implicit_wait_config = config.get_config().BrowserConstants.IMPLICIT_WAIT_TIME
        self._perf_test = config.get_config().PERFORMANCE_TEST
        self._nwlogger = config.get_config().NWLOGGER
        self.__start_time = None
        self.__end_time = None
        self.login_stats = None
        self._service_pack = None

    @property
    def performance_test(self):
        return self._perf_test

    @property
    def nwloggermode(self):
        return self._nwlogger

    @property
    def start_time_load(self):
        return self.__start_time

    @start_time_load.setter
    def start_time_load(self, value):
        self.__start_time = value

    @property
    def end_time_load(self):
        return self.__end_time

    @end_time_load.setter
    def end_time_load(self, value):
        self.__end_time = value

    @property
    def service_pack(self):
        if self._service_pack is None:
            self._service_pack = self.browser.get_js_variable('cv.currentSP')
        return self._service_pack

    @WebAction(log=False, delay=1)
    def __wait_for_loader(self, wait_time):
        """
        Waits for the loader on the page to load completely so that all items on page are visible
        """
        loader_xpaths = [
            "//span[@class = 'grid-spinner']",
            "//div[@class='loading-spinner']",
            "//*[contains(@class, 'loader-backdrop')]",
            "//*[@role = 'progressbar']",
            "//*[contains(text(),'loading') or contains(text(),'Loading')]",
            "//div[contains(@class, 'mui-modal-body')]//div[contains(text(),'Loading...')]",
            "//*[contains(@class, 'tile-loading')]",
            "//div[contains(@title, 'Loading')]",
            "//*[contains(@class, 'grid-loading')]"

        ]
        for xpath in loader_xpaths:
            WebDriverWait(self.driver, wait_time).until(ec.invisibility_of_element_located((By.XPATH, xpath)))
        # For Metallic Hub
        if self.check_if_entity_exists("xpath", "//mdb-spinner"):
            invisibility_of_spinner = ec.invisibility_of_element_located((By.XPATH, "//mdb-spinner"))
            visibility_of_welcome_dialog = ec.visibility_of_element_located(
                (By.XPATH, "//*[contains(text(), 'Welcome to Metallic')]"))
            WebDriverWait(self.driver, wait_time).until(
                lambda driver: invisibility_of_spinner(driver) or visibility_of_welcome_dialog(driver)
            )

    @PageService(log=False)
    def __wait_for_react_loader(self, wait_time):
        """
        waits for react page to load
        """
        loader_xpaths = [
            "//div[contains(@class, 'loader-container')]//*[@role = 'progressbar']",
            "//*[contains(text(),'loading') or contains(text(),'Loading')]",
            "//div[@title='Loading...'] | //span[contains(@class, 'MuiCircularProgress-root')]"
        ]
        for xpath in loader_xpaths:
            WebDriverWait(self.driver, wait_time).until(ec.invisibility_of_element_located((By.XPATH, xpath)))

    def __check_sort(self, select):
        """
        Checks if the dropdown items are in sorted order

        Args:
            select (Select): Select values from element search

        Raises:
            Exception:
                If the elements are not in sorted order

        """
        self.log.info("Checks if options are in sorted order")
        unsorted_list = []
        global_list = ['Not Connected', 'Select MediaAgent', 'Select a vendor type',
                       'Create MediaAgent', 'Select datastore', 'Select resource pool']

        for option in select.options:
            if option.get_attribute('label') not in global_list:
                unsorted_list.append(option.get_attribute('label').lower())
        sorted_list = sorted(unsorted_list)
        self.log.info("Unsorted List : %s", str(unsorted_list))
        self.log.info("Sorted List : %s", str(sorted_list))

        if not sorted_list == unsorted_list:
            raise Exception("The dropdown elements are not in a sorted order")

    def load_properties(self, class_obj, unique=False):
        """
        Loads the properties of the current class

        Args:
            class_obj   (object):   instance of the class whose locale properties has to be loaded
            unique      (bool):  set to True to if key is unique to the class. default is False

        """
        if not self.ext:
            self.get_locale_name()
        class_list = []
        files_list = ''
        # Get the parent classes of the given class
        base_classes = inspect.getmro(class_obj.__class__)
        for base in base_classes:
            if base.__name__ in ['object', 'AdminConsoleBase']:
                continue
            class_list.append(base.__name__)
        class_list = list(set(class_list))

        for locale_class in class_list:
            try:
                files_list += LocaleFile[locale_class].value + ','
            except KeyError:
                pass

        locale_files = [x.strip() for x in files_list.rsplit(',', 1)[0].split(",")]
        unique_dict = dict()
        for locale_file in locale_files:
            if unique or locale_file not in self.loaded_locale_files:
                if not unique:
                    self.loaded_locale_files.append(locale_file)
                file_name = locale_file + self.ext
                file_path = os.path.join(constants.ADMINCONSOLE_DIRECTORY, 'Localization', file_name)
                if not os.path.exists(file_path):
                    continue
                prop_file = open(file_path, 'r', encoding='UTF-8')
                for line in prop_file.readlines():
                    try:
                        line = line.strip()
                        if line.isspace() or line.startswith("#") or line == '' or "=" not in line:
                            continue
                        key, value = [x.strip() for x in line.split("=", 1)]
                        if unique:
                            unique_dict[key] = value
                        else:
                            self.props[key] = value
                    except Exception as exp:
                        self.log.exception("Exception occurred while getting the locale properties. "
                                           "%s", str(exp))
                prop_file.close()
        if unique_dict:
            self.props[class_obj.__class__.__name__] = unique_dict

    @WebAction()
    def __click_menu(self, name):
        """ Method to click on the menu next to the tab on a page """
        angular_xpath = f"//span[@data-ng-bind='action.title' and text()='{name}']"
        react_xpath = (f"//div[contains(@class, 'page-actions')]"
                       f"//span[contains(@class, 'MuiButton-label')]"
                       f"//*[contains(text(), '{name}')]")
        if self.check_if_entity_exists("xpath", angular_xpath):
            self.driver.find_element(By.XPATH, angular_xpath).click()
        elif self.check_if_entity_exists("xpath", react_xpath):
            self.driver.find_element(By.XPATH, react_xpath).click()
        else:
            raise WebDriverException(f"Page action menu [{name}] not found")

    @WebAction()
    def __click_main_bar_dropdown(self, col_id=None):
        """ Method to click on the dropdown menu next to a tab """
        if not col_id:
            self.driver.find_element(
                By.XPATH, "//a[contains(@class, 'uib-dropdown-toggle main-tab-menu-toggle')]"
            ).click()
        else:
            self.driver.find_element(
                By.XPATH,
                f"//label[@class='col-xs-{col_id} col-md-3 col-lg-3 cv-main-bar-dropdown-menu menu "
                f"ng-scope dropdown']//a[@class='uib-dropdown-toggle main-tab-menu-toggle dropdown-toggle']"
                f"//*[local-name()='svg']"
            ).click()

    @WebAction()
    def __click_action_menu_dropdown(self):
        """Method to click on action menu's dropdown"""
        self.driver.find_element(By.XPATH, "//span[contains(@class, 'uib-dropdown')]").click()

    @WebAction()
    def __check_action_visible(self, link_text):
        """Checks if the action menu with text is visible or not
        Args:
            link_text (str): Element ID of the action button
        """
        xpath = f"//div[contains(@class,'page-action')]//*[contains(text(), '{link_text}')]"
        return (self.check_if_entity_exists("xpath", xpath) and
                self.driver.find_element(By.XPATH, xpath).is_displayed())

    @WebAction()
    def __click_page_action_item(self, link_text):
        """Clicks on the action menu with text"""
        xpath = f"//div[contains(@class,'page-action')]//*[contains(text(), '{link_text}')]"
        self.driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __click_dropdown_action_item(self, link_text):
        """Clicks on the more actions dropdown action item"""
        xpath = f"//ul[contains(@class, 'moreAction')]//a[contains(text(), '{link_text}')]"
        self.driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def click_by_id(self, id):
        """ Method to click on the dropdown menu next to a tab """
        self.driver.find_element(By.XPATH, f'//*[@id="{id}"]').click()
        self.wait_for_completion()

    @WebAction()
    def select_main_bar_tab_item(self, link_text):
        """Select main bar tab item matching with passed text"""
        xpath = f'//a[contains(@class,"cv-main-bar-tab-menu-link")]/span[contains(text(),"{link_text}")]'
        self.driver.find_element(By.XPATH, xpath).click()
        self.wait_for_completion()

    @WebAction()
    def __click_access_sub_menu(self, name):
        """Method to click on the access sub menu if visible"""
        elems = self.driver.find_elements(
            By.XPATH, f"//div[@class='panel-body' and normalize-space()='{name}']"
        )
        for elem in elems:
            if elem.is_displayed():
                elem.click()
                break

    @WebAction()
    def __click_on_action(self, action_name):
        """
        clicks on actions of class cv-main-bar-action
        Args:
            action_name:  text used for action
        """
        self.driver.find_element(
            By.XPATH, f"//a[contains(@class,'cv-main-bar-action') and contains(text(),'{action_name}')]"
        ).click()

    @WebAction()
    def __get_page_actions_list(self):
        """Reads data from page actions menu"""
        if self.check_if_entity_exists("xpath", "//div[contains(@class,'cv-main-bar-dropdown-menu')]"):
            self.driver.find_element(By.XPATH, "//div[contains(@class,'cv-main-bar-dropdown-menu')]").click()
            self.wait_for_completion()
        return self.driver.find_elements(By.XPATH, "//*[@id='moreActions']/li//span | //*[@id='moreActions']/li//hr")

    @WebAction()
    def __expand_locale_selection_drop_down(self):
        """ Method to expand language selection drop down on home screen """
        username = self.driver.find_element(By.XPATH, "//div[@class='header-user-settings-anchor']")
        username.click()
        time.sleep(2)
        language_dropdown = self.driver.find_element(By.XPATH, "//div[@id='user-header-lang']")
        action = ActionChains(self.driver)
        action.move_to_element(language_dropdown).perform()

    @WebAction()
    def __get_selected_locale(self):
        """
        Method to get selected locale

        Returns:
            selected_locale (str) : Current selected locale in admin console
        """
        xp = ("//div[@id='user-header-lang-menu']//ul[contains(@class, 'MuiMenu-list')]"
              "//li[contains(@class, 'selected')]")
        selected_locale = self.driver.find_element(By.XPATH, xp).get_attribute('id')
        # get the body element, and move to the top left corner
        # this will remove languages popup
        # click the body element to remove the user actions dropdown
        body_element = self.driver.find_element(By.XPATH, "//body")
        actions = ActionChains(self.driver)
        actions.move_to_element_with_offset(body_element, 0, 0).perform()
        body_element.click()
        return selected_locale

    def __get_locale_ids(self):
        """ Method to get locale Ids """
        file_path = os.path.join(constants.ADMINCONSOLE_DIRECTORY, 'Localization',
                                 "HeaderLanguages.properties")
        lang_file = open(file_path, 'r', encoding='UTF-8')
        for line in lang_file.readlines():
            line = line.strip()
            line = [x.strip() for x in line.split("=")]
            self.locale_ids[line[1].lower()] = line[0].lower()
        lang_file.close()

    def __select_language(self, lang_id):
        """
        Method to select localization language of Admin Console

        Args:
            lang_id (str) : language id for language to be selected
        """
        self.driver.find_element(By.ID, lang_id).click()
        self.wait_for_completion()

    @WebAction()
    def __click_on_toggle(self, label):
        """
        Clicks on toggle element

        Args:
            label(str) : value of toggle label if label to be clicked on
        """
        xpath_toggle = f"//*[contains(text(),'{label}')]/preceding-sibling::toggle-control"
        self.driver.find_element(By.XPATH, xpath_toggle).click()

    @WebAction()
    def __get_all_languages(self):
        """
        Returns the list of all language's locale name

        Returns:
            (list)  -- List of all languages

        """
        languages = []

        for language in self.driver.find_elements(By.XPATH, "//li[@id='user-header-dropdown_mn_active']//li"):
            languages.append(language.text)

        return languages

    @WebAction(log=False, delay=1)
    def __wait_for_load_line(self, wait_time):
        """
        Waits for the loader for two times on the page to load completely so that all items on page are visible
        This method first waits for load line to be invisible, after which it again looks to see if another load line
        is visible. The second check is added to fit cases where load line is spawned right after the
        finish of the previous load line
        """
        waiter = WebDriverWait(self.driver, wait_time / 2, poll_frequency=2)
        try:
            waiter.until(ec.invisibility_of_element_located((By.XPATH, "//div[@id='loading-bar']")))
        except TimeoutException:
            pass
        try:
            waiter.until(ec.invisibility_of_element_located((By.XPATH, "//div[@id='loading-bar']")))
        except TimeoutException as excep:
            raise CVWebAutomationException(excep)

    @WebAction()
    def unswitch_to_react_frame(self):
        """Move out of React frame"""
        self.driver.switch_to.window(self.driver.current_window_handle)

    @WebAction()
    def navigate(self, url):
        """Opens the address specified in the url in the browser.

        Args:
            url (str): the URL to navigate to
        """
        try:
            self.driver.get(url)
            self.wait_for_completion()
            self.close_warning_dialog()
        except Exception as exp:
            raise exp

    def current_url(self):
        """Returns the currently opened url in the browser."""
        return self.driver.current_url

    def check_if_entity_exists(self, entity_name, entity_value):
        """Check if a particular element exists or not
        :param entity_name      (str)   --  the entity attribute to check for presence
        :param entity_value     (str)   --  the entity to be checked
        :return:
            True    --  If the entity is available
            False   --  If the entity is not available
        """
        try:
            if entity_name == "link":
                return self.driver.find_element(By.LINK_TEXT, entity_value).is_displayed()
            elif entity_name == "id":
                return self.driver.find_element(By.ID, entity_value).is_displayed()
            elif entity_name == "css":
                return self.driver.find_element(By.CSS_SELECTOR, entity_value).is_displayed()
            elif entity_name == "xpath":
                return self.driver.find_element(By.XPATH, entity_value).is_displayed()
            elif entity_name == "name":
                return self.driver.find_element(By.NAME, entity_value).is_displayed()
            elif entity_name == "class":
                return self.driver.find_element(By.CLASS_NAME, entity_value).is_displayed()
        except NoSuchElementException:
            return False

    def __is_page_loaded(self, wait_time=100):
        """
        Wait for page to load
        """
        sleep_time = 2
        if self.performance_test:
            sleep_time = 0.1

        load_time = 0
        while load_time <= wait_time:
            if self.driver.execute_script("return document.readyState") == "complete":
                break
            sleep(sleep_time)
            load_time = load_time + sleep_time

    @PageService(react_frame=False)
    def wait_for_completion(self, wait_time=300):
        """Waits for the page load to complete"""
        self.__is_page_loaded()
        self.driver.implicitly_wait(0)
        self.__wait_for_loader(wait_time)
        try:
            self.__wait_for_load_line(wait_time)
        except Exception:
            self.log.info("Retrying for the loader to finish")
            self.__wait_for_load_line(wait_time)
        finally:
            self.__wait_for_react_loader(wait_time)
            self.driver.implicitly_wait(self.implicit_wait_config)

    @PageService()
    def select_value_from_dropdown(self, select_id, value, attribute=False, check_sort=True,
                                   search=False):
        """ Selects the value from the drop down

            Args:

                select_id       (str) -- the ID or name of the dropdown element

                value           (str) -- the value to be chosen from the dropdown
                                         in case of multi select drop down
                                          value will be list of string.

                attribute       (str) -- true, if the value of the option should be used

                check_sort      (bool) -- true if dropdown has to be checked for sorted order

                search          (bool):  true if the value contains more text than actual
                    Eg: value to be selected is Datastore1
                        value displayed in UI is Datastore1 (Free: 5GB, total: 10GB)

            Raises:
                Exception:
                    if failed to choose the value from dropdown
        """
        try:
            if self.check_if_entity_exists("id", select_id) and \
                    self.driver.find_element(By.ID, select_id).tag_name.lower() == "select":
                select = Select(self.driver.find_element(By.ID, select_id))

            elif self.check_if_entity_exists("name", select_id) and \
                    self.driver.find_element(By.NAME, select_id).tag_name.lower() == "select":
                select = Select(self.driver.find_element(By.NAME, select_id))

            elif self.check_if_entity_exists("xpath",
                                             "//label[contains(text(), '" + select_id + "')]"
                                                                                        "/select"):
                select = Select(
                    self.driver.find_element(By.XPATH, "//label[contains(text(), '" + select_id + "')]/select")
                )

            else:
                raise CVWebAutomationException(f"There is no dropdown with the given name or ID {select_id}")

            if self.cb_flag:
                if check_sort:
                    self.__check_sort(select)

            flag = 1

            if search:
                if not isinstance(value, str):
                    raise CVWebAutomationException("Expected string for value to select")
                pattern = re.compile(value, re.IGNORECASE)
                if attribute:
                    sel = "value"
                else:
                    sel = "label"
                for option in select.options:
                    attr_value = option.get_attribute(sel)
                    if pattern.search(attr_value):
                        option.click()
                        self.wait_for_completion()
                        flag = 0
                        break

            elif isinstance(value, str):
                for option in select.options:
                    if attribute:
                        element_value = option.get_attribute('value')
                    else:
                        element_value = option.get_attribute('label')
                    if value.lower() == element_value.lower() \
                            or value.lower() == element_value[:len(element_value) - 3].lower():
                        option.click()
                        self.wait_for_completion()
                        flag = 0
                        break

            else:
                raise CVWebAutomationException("Expected type string for argument:value ")

            if flag != 0:
                raise CVWebAutomationException("The specified option was not present in the list")

        except Exception as exp:
            raise CVWebAutomationException(
                "Exception occurred while selecting an option from the dropdown. {0}".format(str(exp))
            )

    @WebAction()
    def cv_table_next_button_exists(self):
        """
        Checks if there is a button to navigate to the next page.
        """
        try:
            return bool(self.driver.find_element(By.XPATH, "//button[@ng-disabled='cantPageForward()']").is_displayed())
        except Exception:
            return False

    @WebAction()
    def cv_table_click_next_button(self):
        """
        Clicks on the button to navigate to the next page.
        """
        self.driver.find_element(By.XPATH, "//button[@ng-disabled='cantPageForward()']").click()
        self.wait_for_completion()

    @WebAction()
    def cv_table_click_first_button(self):
        """
        Clicks on the button to navigate to the first page.
        """
        self.driver.find_element(By.XPATH, "//button[@ng-click='pageFirstPageClick()']").click()
        self.wait_for_completion()

    @WebAction()
    def mouseover(self, mouse_move_over):
        """
        Pass MouseMoveOver and MouseClick Element.

        Args:
            mouse_move_over (WebElement) -- mouse move over element

        """
        hover = ActionChains(self.driver).move_to_element(mouse_move_over)
        hover.perform()
        sleep(2)

    @PageService()
    def mouseover_and_click(self, mouse_move_over, mouse_click):
        """
        Pass MouseMoveOver and MouseClick Element.

        Args:
            mouse_move_over (WebElement) -- mouse move over element

            mouse_click (WebElement)    -- mouse click element
        """
        hover = ActionChains(self.driver).move_to_element(mouse_move_over)
        hover.perform()
        sleep(2)
        mouse_click.click()
        self.wait_for_completion()

    def is_element_present(self, locator, root_tag=None):
        """ Checks if the given element is present in the given parent tag

            Args:
                locator     (str) -- the xpath of the element to be located
                root_tag    (str) -- the parent tag under which the element is to be located (default: None)
            Returns:
                True    --  If the element is present
                False   --  If the element is not present
        """
        try:
            if not root_tag:
                self.driver.find_element(By.XPATH, locator)
            else:
                root_tag.find_element(By.XPATH, locator)
        except Exception:
            return False
        return True

    @WebAction()
    def close_popup(self):
        """
        Checks for pop up and closes it if it is present
        """  
        if self.check_if_entity_exists("xpath", "//button[@aria-label='No thanks, I’ll explore on my own.']/div"):
            self.driver.find_element(By.XPATH, "//button[@aria-label='No thanks, I’ll explore on my own.']/div").click()
            self.wait_for_completion()     
        elif self.check_if_entity_exists("xpath", "//div[contains(@class, 'button-container')]//button"):
            self.driver.find_element(By.XPATH, "//div[contains(@class, 'button-container')]//button").click()
            self.wait_for_completion()
        elif self.check_if_entity_exists("xpath", "//div[@role='dialog']//span[contains(@class,'positive-modal-btn')]"):
            self.driver.find_element(By.XPATH, "//div[@role='dialog']//span[contains(@class,'positive-modal-btn')]").click()
            self.wait_for_completion()



    @WebAction()
    def close_warning_dialog(self):
        """close warning dialog shown after user login"""
        # close unwanted dialog showing after login like disaster recovery/License expiry etc
        close_btn = "//div[contains(@role,'dialog')]/*//button"

        close_btn2 = "//span[contains(@class,'positive-modal-btn')]"
        if self.check_if_entity_exists("xpath", close_btn):
            self.driver.find_element(By.XPATH, close_btn).click()
            time.sleep(2)

        elif self.check_if_entity_exists("xpath", close_btn2):
            self.driver.find_element(By.XPATH, close_btn2).click()
            time.sleep(2)

    @PageService()
    def access_tile(self, id):
        """access the page based on id"""
        self.clear_perfstats()
        self.start_time_load = time.time()
        self.__click_title(id)
        self.wait_for_completion()

    @WebAction()
    def __click_title(self, id):
        """ Method to click on the given tile """
        self.start_time_load = time.time()
        self.driver.find_element(By.ID, id).click()

    def clear_perfstats(self):
        """Clear the API stats and browser network stats based on the config"""
        if self.performance_test:
            self.browser.clear_browser_networkstats()
            if self._nwlogger:
                self.browser.switch_to_first_tab()
                self.browser.accept_alert("del")
                self.browser.switch_to_latest_tab()

    @PageService()
    def access_tab(self, tab_header):
        """ access the tab with the given title"""
        if self.get_current_tab().lower() != tab_header.lower():
            self.clear_perfstats()
            self.__click_tab(tab_header=tab_header)
            self.wait_for_completion()
            self.end_time_load = time.time()

    @WebAction()
    def __click_tab(self, tab_header):
        """ Method to click on the given tile """
        self.start_time_load = time.time()
        self.driver.find_element(
            By.XPATH,
            f"//span[@ng-bind='tab.title' and text()='{tab_header}']"
            f" | //a[contains(@class, 'MuiTab-root')]//span[contains(text(), '{tab_header}')]"
        ).click()  # xpath updated to support both angular and react pages

    @WebAction()
    def scroll_into_view(self, element_name):
        """
        Scrolls the element into view
        """
        elem = ""

        if self.check_if_entity_exists("xpath", element_name):
            elem = self.driver.find_element(By.XPATH, element_name)

        elif self.check_if_entity_exists("id", element_name):
            elem = self.driver.find_element(By.ID, element_name)

        if elem:
            self.driver.execute_script("arguments[0].scrollIntoView();", elem)

    @WebAction()
    def scroll_into_view_using_web_element(self, web_elem):
        """
        Scrolls into view using web element
        """

        self.driver.execute_script("arguments[0].scrollIntoView();", web_elem)

    @WebAction()
    def __check_toggle_status(self, label):
        """
        Checks the status of toggle

        Args:
            label          (str):   Label corresponding to the toggle option.

        Returns:
            Status
        """
        return 'enabled' in self.driver.find_element(
            By.XPATH, f"//*[contains(text(),'{label}')]/preceding-sibling::toggle-control/div"
        ).get_attribute('class')

    @PageService()
    def toggle_enable(self, label):
        """
        Enables the toggle bar if disabled,
        Args:
            label          (str):   Label corresponding to the toggle option.

        Note : Please do not use this method, as we are deprecating this, please use method enable_toggle instead
        """
        if not self.__check_toggle_status(label):
            self.__click_on_toggle(label)
            self.wait_for_completion()

    @WebAction()
    def __return_toggle(self, cv_toggle):
        """
        Method to return list of toggles present on page

        Returns:
                toggle_list (list) : List of toggles present on page
        """
        self.unswitch_to_react_frame()
        if not cv_toggle:
            toggle_control_list = self.driver.find_elements(By.XPATH, "//toggle-control")
            return toggle_control_list
        else:
            toggle_cv_list = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'cv-toggle-wrapper')]")
            if not toggle_cv_list:
                toggle_cv_list = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'cv-toggle')]")
            return toggle_cv_list

    @WebAction()
    def __is_toggle_enabled(self, toggle=None, toggle_id=None, cv_toggle=False):
        """ Method to check toggle status """
        if toggle and not cv_toggle:
            return 'enabled' in toggle.find_element(By.XPATH, "./div").get_attribute('class')
        elif cv_toggle:
            if toggle_id:
                toggle = self.driver.find_element(By.ID, toggle_id)
            return 'isOn' in toggle.find_element(By.XPATH, "./div").get_attribute('class')
        else:
            return 'enabled' in self.driver.find_element(
                By.XPATH, f"*//toggle-control[@id='{toggle_id}']/div").get_attribute('class')

    @WebAction()
    def __click_toggle(self, toggle=None, toggle_id=None):
        """ Method to click on toggle button """
        if toggle:
            toggle.click()
        else:
            self.driver.find_element(By.ID, toggle_id).click()

    @PageService()
    def enable_toggle(self, index=None, toggle_id=None, cv_toggle=False):
        """
        Method to Enable toggle

        Args:
            index (int) :   index corresponding to the toggle option (Ex.- 0,1....so on)
            toggle_id      (str):   Id corresponding to the toggle-control tag
            cv_toggle       (bool) : Whether cv toggle element is present or not
        """
        if index is not None:
            toggle_list = self.__return_toggle(cv_toggle)
            if not self.__is_toggle_enabled(toggle=toggle_list[index], cv_toggle=cv_toggle):
                self.__click_toggle(toggle_list[index])
                self.wait_for_completion()
        elif toggle_id:
            if not self.__is_toggle_enabled(toggle_id=toggle_id, cv_toggle=cv_toggle):
                self.__click_toggle(toggle_id=toggle_id)
                self.wait_for_completion()

    @PageService()
    def disable_toggle(self, index=None, toggle_id=None, cv_toggle=False):
        """
        Method to Disable toggle

        Args:
            index (int) :   index corresponding to the toggle option (Ex.- 0,1....so on)
            toggle_id      (str):   Id corresponding to the toggle-control tag
            cv_toggle       (bool) : Whether cv toggle element is present or not
        """
        if index is not None:
            toggle_list = self.__return_toggle(cv_toggle)
            if self.__is_toggle_enabled(toggle=toggle_list[index], cv_toggle=cv_toggle):
                self.__click_toggle(toggle_list[index])
                self.wait_for_completion()
        else:
            if self.__is_toggle_enabled(toggle_id=toggle_id, cv_toggle=cv_toggle):
                self.__click_toggle(toggle_id=toggle_id)
                self.wait_for_completion()

    @WebAction()
    def submit_form(self, wait=True, form_name=None):
        """
        Clicks save Button on open forms.
        Since it searches by type , should work on all forms.

        Raises:
            Exception:
                If the button is not found
        """
        if form_name:
            form_elem = self.driver.find_element(By.NAME, form_name)
            form_elem.find_element(By.XPATH, ".//button[@type='submit']").click()
        else:
            elems = self.driver.find_elements(By.XPATH, "//button[@type='submit']")
            for elem in elems:
                if elem.is_displayed():
                    elem.click()
                    break
        if wait:
            self.wait_for_completion()

    @WebAction()
    def cancel_form(self, form_name=None):
        """
        Clicks Cancel Button on open forms.

        Raises:
            Exception:
                If the button is not found
        """
        if form_name:
            form_elem = self.driver.find_element(By.NAME, form_name)
            form_elem.find_element(By.XPATH, ".//button[contains(.,'Cancel')]").click()
        else:
            self.driver.find_element(By.XPATH, "//button[contains(.,'Cancel')]").click()
            self.wait_for_completion()

    @WebAction()
    def button_next(self):
        """
        Clicks the Next button on forms

        Raises:
            Exception:
                If the button is not found
        """
        self.driver.find_element(By.XPATH, f"//button[contains(.,'{self.props['Next']}')]").click()
        self.wait_for_completion()

    @WebAction()
    def select_radio(self, id=None, value=None, name=None):
        """
        Selects radio button based on given id/value attribute.

        Args:
            id      (str)   -- ID of the radio button.
            value   (str)   -- Value of the radio button
            name    (str)   --  name of the radio button

        """
        xpath_radio = f"//input[@type = 'radio'][@id='{id}']"

        if value is not None and name is not None:
            xpath_radio = f"//input[@type = 'radio'][@value='{value}'][@name='{name}']"

        if value is not None:
            xpath_radio = f"//input[@type = 'radio'][@value='{value}']"

        if name is not None:
            xpath_radio = f"//input[@type = 'radio'][@name='{name}']"

        self.driver.find_element(By.XPATH, xpath_radio).click()

    @WebAction()
    def label_getvalue(self, label):
        """
        Fetch the value corresponding to given label.

        Args:
            label   (str)   -- Name of the label.

        Raises:
            Exception:
                If the tile is not found

        """
        xpath_label = "//span[contains(text(), '" + label + "')]"
        xpath_value = xpath_label + "/../span[2]"
        xpath2_value = xpath_label + "/../a"
        if self.check_if_entity_exists("xpath", xpath_label):
            return self.driver.find_element(By.XPATH, xpath_value).text
        elif self.check_if_entity_exists("xpath", xpath2_value):
            return self.driver.find_element(By.XPATH, xpath2_value).text
        else:
            raise NoSuchElementException("Label :[{}] not found".format(label))

    def tile_select_hyperlink(self, tile_name, link_text):
        """
        This selects the hyperlink at tile label level. hyperlink within tile wont be selected.

        Args:

            tile_name   (str)   -- name of the tile on which operation needs to be performed.

            link_text   (str)   -- hyperlink name.

        """
        xpath_load_tile = "//cv-tile-component//span[contains(., '" + tile_name + "')]"
        xpath1 = xpath_load_tile + "/..//a[contains(.,'" + link_text + "')]"
        xpath2 = xpath_load_tile + "/../..//a[contains(.,'" + link_text + "')]"
        if self.check_if_entity_exists("xpath", xpath1):
            xpath_tile_hyperlink = xpath1
        elif self.check_if_entity_exists("xpath", xpath2):
            xpath_tile_hyperlink = xpath2
        else:
            raise Exception(
                "Could not locate Hyperlink:[{}] in  tile :[{}] not found".format(
                    link_text, tile_name))
        self.scroll_into_view(xpath_tile_hyperlink)
        self.driver.find_element(By.XPATH, xpath_tile_hyperlink).click()
        self.wait_for_completion()

    def cvselect_from_dropdown(self, label, value=None, select_all=False):
        """ Selects the value from the dropdown.Use this for cv multi select option


            Args:
                label       (str) -- Label name for the dropdown element

                value       (str) -- the value to be chosen from the dropdown

                select_all  (bool)-- To select all the values in the dropdown (default: False)


            Raises:

                Exception:

                    if dropdown cannot be loaded

                    if value not present in drop down list

                    if value is not string or list
        """
        if self.check_if_entity_exists("xpath", "//label[contains(text(),'" + label + "')]"):
            label_xpath = "//label[contains(text(),'" + label + "')]"
        elif self.check_if_entity_exists("xpath", "//label/span[contains(text(),'"
                                                  + label + "')]"):
            label_xpath = "//label/span[contains(text(),'" + label + "')]"
        else:
            raise Exception("There is no label with the given text")

        if self.check_if_entity_exists("xpath", label_xpath + "/..//isteven-multi-select"):
            xpath_select_cvdropdown = label_xpath + "/..//isteven-multi-select"
        elif self.check_if_entity_exists("xpath", label_xpath +
                                                  "/../div/cv-client-picker/isteven-multi-select"):
            xpath_select_cvdropdown = label_xpath + "/../div/cv-client-picker/isteven-multi-select"
        else:
            label_for = self.driver.find_element(By.XPATH, label_xpath).get_attribute("for")
            xpath_select_cvdropdown = "//isteven-multi-select[@id='" + label_for + "']"

        xpath_select_cvdropdown_search_ok = xpath_select_cvdropdown + \
                                            "//div[@class='line-searchOk']"
        xpath_select_cvdropdown_options = xpath_select_cvdropdown + \
                                          "//div[@class='checkBoxContainer']/div"

        if self.check_if_entity_exists("xpath", xpath_select_cvdropdown):
            self.driver.find_element(By.XPATH, xpath_select_cvdropdown).click()
            self.wait_for_completion()
        else:
            raise Exception("There is no dropdown with the given name or ID")

        if select_all:
            if self.check_if_entity_exists('xpath',
                                           "//button[@ng-bind-html='lang.selectAll']"):
                self.driver.find_element(By.XPATH, "//button[@ng-bind-html='lang.selectAll']").click()
                self.wait_for_completion()
                self.driver.find_element(By.XPATH, xpath_select_cvdropdown_search_ok).click()
                self.wait_for_completion()
                return
            else:
                raise Exception("could not locate select all button")

        if isinstance(value, str):
            """
            To verify sorting , test on scale setup , if we can get all list.
            for option in xpath_select_cvdropdown_options:
                option = option + "/div/label/span"
                if value.lower() == option.text().lower():
                    option.click()
                    break
            """
            value = [value]

        value = [x.lower() for x in value]
        for item in value:
            xpath_select_cvdropdown_search = xpath_select_cvdropdown + \
                                             "//div[@class='line-search']/input"

            if self.check_if_entity_exists("xpath", xpath_select_cvdropdown_search):
                self.driver.find_element(By.XPATH, xpath_select_cvdropdown_search).clear()
                self.driver.find_element(By.XPATH, xpath_select_cvdropdown_search).send_keys(item)

            options = self.driver.find_elements(By.XPATH, xpath_select_cvdropdown_options)
            for option in options:
                option_name = option.find_element(By.XPATH, "./div/label/span")
                if option_name.text.strip().lower() == item:
                    class_value = option.get_attribute('class')
                    if 'selected' not in class_value:
                        option_name.click()
                        self.wait_for_completion()
                    break

            if self.check_if_entity_exists("xpath", xpath_select_cvdropdown_search):
                self.driver.find_element(By.XPATH, "//button[@class='clearButton']").click()
                self.wait_for_completion()

        if self.check_if_entity_exists("xpath", xpath_select_cvdropdown):
            self.driver.find_element(By.XPATH, xpath_select_cvdropdown).click()
            self.wait_for_completion()

    @WebAction()
    def checkbox_select(self, checkbox_id=None, checkbox_name=None):
        """
        Selects checkbox that matches the ID
        Args:
            checkbox_id   (str)  -- id of the checkbox from dev or input tag
            checkbox_name (str)  -- name displayed for the checkbox
        """
        if checkbox_name:
            xp = f"//label[contains(text(), '{checkbox_name}')]"
            chkbox = self.driver.find_element(By.XPATH, xp)
            chkbox.click()
            return

        xp = f"//*[@id = '{checkbox_id}']"
        chkbox = self.driver.find_element(By.XPATH, xp)
        if (chkbox.tag_name == 'input' and not chkbox.is_selected()) or chkbox.get_attribute(
                "data-state") == 'unchecked' \
                or 'partial-selection' in chkbox.get_attribute('class'):
            xpath = (f"//*[@id = '{checkbox_id}']/following-sibling::label | "
                     f"//*[@id = '{checkbox_id}']/following-sibling::span")
            element = self.driver.find_element(By.XPATH, xpath)
            self.driver.execute_script("arguments[0].click();", element)

    @WebAction()
    def checkbox_deselect(self, checkbox_id):
        """
        Deselects checkbox that matches the ID
        Args:
            checkbox_id  (str)  -- id of the checkbox from dev or input tag
        """
        xp = f"//*[@id = '{checkbox_id}']"
        chkbox = self.driver.find_element(By.XPATH, xp)
        if chkbox.is_selected() or chkbox.get_attribute("data-state") == 'checked':
            xpath = (f"//*[@id = '{checkbox_id}']/following-sibling::label | "
                     f"//*[@id = '{checkbox_id}']/following-sibling::span")
            self.driver.find_element(By.XPATH, xpath).click()

    def refresh_page(self):
        """Refreshes the contents in the browser tab"""
        self.driver.refresh()
        self.wait_for_completion()

    @WebAction()
    def select_hyperlink(self, link_text, index=0, wait_for_load=True):
        """
        Selects hyperlink in the given page.

        Args:

            link_text       (str)   --  Link name as displayed in the webpage.

            index           (int)   --  Index in case multiple links exist, default is 0.

            wait_for_load   (bool)  --  Waits for page to load, default is True.

        Returns:

        """
        for _ in range(5):
            try:
                xp = f"//a[text() = '{link_text}'] | //li[text() = '{link_text}']"
                if self.check_if_entity_exists("xpath", xp) and index == 0:
                    links = self.driver.find_elements(By.XPATH, xp)
                    for link in links:
                        if link.is_displayed():
                            link.click()
                            break
                else:
                    xp = f'//a[contains(text(),"{link_text}")]'
                    self.driver.find_elements(By.XPATH, xp)[index].click()
                if wait_for_load:
                    self.wait_for_completion()
                return
            except StaleElementReferenceException:
                continue

    @WebAction()
    def click_by_xpath(self, xpath):
        """Clicks on element with the given xpath"""
        self.driver.find_element(By.XPATH, xpath).click()
        self.wait_for_completion()

    @PageService()
    def click_recent_downloads(self):
        """Clicks on recent download on the navbar"""
        self.unswitch_to_react_frame()
        self.click_by_xpath("//a[@id='recentDownloadList']")

    @PageService()
    def access_page_action_menu(self, link_text):
        """
        Access page access menu with div having class page-action
        Args:
            link_text(str): Link text

        """
        if not self.__check_action_visible(link_text):
            self.__click_action_menu_dropdown()
            self.__click_dropdown_action_item(link_text)
        else:
            self.__click_page_action_item(link_text)
        self.wait_for_completion()

    @WebAction()
    def access_page_action_menu_by_class(self, class_name):
        """
        Access page access menu with div having class page-action
        Args:
            class_name(str): class name

        """
        xp = f"//div[contains(@class,'page-action')]//*[@class='{class_name}']"
        self.driver.find_element(By.XPATH, xp).click()
        self.wait_for_completion()

    def select_destination_host(self, host, contains_host_name=False):
        """
        Selects a ESX host as destination host or snap mount ESX

        Args:
            host        (str):   the esx host to choose as destination or snap mount

            contains_host_name    (bool):         if the host match should be partial

        """

        def expand_buttons(button_elements, contains_text=False):
            """
            Expands the non-collapsed buttons

            Args:
                button_elements  (list):   the list of buttons to expand

                contains_text    (bool):   if the host match should be partial

            Returns:
                0  :  if the given host is selected

                1  :  if the given host could not be selected

            """
            inter_buttons = []

            for elem in button_elements:
                elem.click()
                self.wait_for_completion()
                flag = 1
                child_elements = elem.find_elements(By.XPATH, "./../../div[2]/div")
                for child in child_elements:
                    host_elem = child.find_element(By.XPATH, "./div[1]/span")
                    if contains_text:
                        if host.strip() in host_elem.text.strip():
                            if 'selected' not in host_elem.find_element(By.XPATH, "./../../div").get_attribute('class'):
                                host_elem.click()
                                self.wait_for_completion()
                            flag = 0
                            break
                    else:
                        if host_elem.text.strip() == host:
                            if 'selected' not in host_elem.find_element(By.XPATH, "./../../div").get_attribute('class'):
                                host_elem.click()
                                self.wait_for_completion()
                            flag = 0
                            break
                if flag == 1:
                    inter_buttons.append(elem)
                else:
                    break
            for item in inter_buttons:
                button_elements.remove(item)
            if not button_elements:
                return 1
            return 0

        if self.check_if_entity_exists("xpath", "//div[@class='browseAndSelectVM']//"
                                                "div[@class='ng-scope selected']"):
            xpath = "//div[@class='browseAndSelectVM']//div[@class='ng-scope selected']/span"

            span = self.driver.find_element(By.XPATH, xpath)
            if span.text.strip() == host:
                return

        buttons = self.driver.find_elements(By.XPATH, "//div[@class='browseAndSelectVM']//button[@class='collapsed']")
        while buttons:
            ret = expand_buttons(buttons, contains_host_name)
            if ret == 0:
                buttons = []
            else:
                buttons = self.driver.find_elements(
                    By.XPATH, "//div[@class='browseAndSelectVM']//button[@class='collapsed']"
                )
                if not buttons:
                    raise Exception("The ESX was not found")

    @WebAction(delay=0)
    def __read_notification_text(self, wait_time, **kwargs):
        """
        Reads the notification text

        Args:
            wait_time   (int)   -- time to wait for the popup

        Returns:
            notification_text (str): the notification string
        """
        self.unswitch_to_react_frame()
        try:
            WebDriverWait(self.driver, wait_time).until(ec.presence_of_element_located((
                By.XPATH, "//div[@class='toasts-container ']/span/div/div/div/div/div")))
            if not kwargs.get("multiple_job_ids"):
                notification_text = self.driver.find_element(By.XPATH,
                                                             "//div[@class='toasts-container ']/span/div/div/div/div/div").text
            else:
                notification_text = [elem.text for elem in
                                     self.driver.find_elements(By.XPATH,
                                                               "//div[@class='toasts-container ']/span/div/div/div/div")]
            if not notification_text:
                WebDriverWait(self.driver, wait_time).until(ec.presence_of_element_located((
                    By.XPATH, "//div[@class='toasts-container ']/span/div/div/div/div/div")))
                if not kwargs.get("multiple_job_ids"):
                    notification_text = self.driver.find_element(By.XPATH,
                                                                 "//div[@class='toasts-container ']/span/div/div/div/div/div").text
                else:
                    notification_text = [elem.text for elem in
                                         self.driver.find_elements(By.XPATH,
                                                                   "//div[@class='toasts-container ']/span/div/div/div/div")]
            if kwargs.get("hyperlink"):
                notification_text = " ".join(
                    [
                        notification_text,
                        self.driver.find_element(
                            By.XPATH, "//div[@class='toasts-container ']/span/div/div/div/div/div/a"
                        ).get_attribute('href')
                    ]
                )
            return notification_text
        except TimeoutException:
            return ""

    @PageService()
    def get_notification(self, wait_time=60, **kwargs):
        """
        Gets the notification text

        Args:
            wait_time   (int)   -- time to wait for the popup (default: 60)

        Returns:

            notification_text (str): the notification string

        """
        return self.__read_notification_text(wait_time, **kwargs)

    @PageService()
    def get_jobid_from_popup(self, wait_time=60, **kwargs):
        """
        Gets the job id from pop up

        Args:
            wait_time  (int): Number of seconds it should wait for the popup to show up.
            kwargs :
                1. hyperlink (bool) : If hyperlink in the notification should be utilised to extract the job ID
                2. multiple_job_ids(bool): If multiple jobs are triggered at once

        Returns:
            job_id (int):  the job id for the submitted request
            or
            job_id (list): List of job IDs if multiple_job_ids is passed to the method

        """
        attempts = 3

        while attempts > 0:
            job_text = self.get_notification(wait_time, **kwargs)
            if isinstance(job_text, list):
                job_id_list = list()
                for job in job_text:
                    if job:
                        job_id = re.findall(r'\d+', job)[0]
                        self.log.info("Job %s has started", str(job_id))
                        job_id_list.append(job_id)
                return job_id_list
            if job_text:
                job_id = re.findall(r'\d+', job_text)[0]
                self.log.info("Job %s has started", str(job_id))
                return job_id
            attempts -= 1

        raise CVWebAutomationException("No notification is popped up to extract job id")

    def get_error_message(self):
        """
        get if there is any error message

        Args:

        Returns:
            error message string
            empty string when there is no error message
        """
        exp = ""

        xpath_list = ["//span[contains(@class,'performActionMessage')]",
                      "//*[contains(@class, 'serverMessage')]",
                      "//*[@class='help-block']",
                      "//div[@class='growl-item alert ng-scope alert-error alert-danger']",
                      "//span[contains(@class, 'error')]",
                      "//div[contains(@class,'vw-login-message error-box error')]",
                      "//*[contains(@class, 'MuiAlert-standardError')]",
                      "//*[contains(@class, 'Mui-error MuiFormHelperText')]"
                      ]
        final_xpath = ""
        for xpath in xpath_list:
            if xpath == "//div[@class=" \
                        "'growl-item alert ng-scope alert-error alert-danger']":
                xpath = xpath + "/div/div/div"
            final_xpath = final_xpath + xpath + '|'

        final_xpath = final_xpath[:-1]
        if self.check_if_entity_exists("xpath", final_xpath):
            exp = self.driver.find_element(By.XPATH, final_xpath).text

        return exp

    @PageService(react_frame=False)
    def check_error_message(self, raise_error=True):
        """
        Checks if there is any error message

        Args:
            raise_error (bool): should error be raised or not

        Raises:
            Exception:
                if there is an error message after submitting the request

        """
        exp = self.get_error_message()

        if exp != "":
            self.log.error(exp)

        if exp != "" and raise_error:
            raise CVWebAutomationException(exp)

    def search_vm(self, vm_name, zone=None, region=None):
        """
        Searches for a VM in the vcenter

        Args:
            vm_name  (str)    :   the name of the VM to be searched

            zone     (str)    :   availability zone of AWS instance

            region   (str)    :   region of AWS instance

        Raises:
            Exception:
                if the given VM is not found in the vcenter

        """

        try:
            self.log.info("Searching for VM %s", str(vm_name))
            if zone is not None and region is not None:
                self.search_aws_vm(zone, region)
            else:
                if self.check_if_entity_exists('xpath', '//input[@placeholder="Search VMs"]'):
                    search = self.driver.find_element(By.XPATH, '//input[@placeholder="Search VMs"]')
                elif self.check_if_entity_exists('xpath', '//input[@placeholder="Search instances"]'):
                    search = self.driver.find_element(By.XPATH, '//input[@placeholder="Search instances"]')
                elif self.check_if_entity_exists('id', 'select2-chosen-1'):
                    self.driver.find_element(By.ID, 'select2-chosen-1').click()
                    self.wait_for_completion()
                    search = self.driver.find_element(By.ID, 's2id_autogen1_search')
                elif self.check_if_entity_exists('xpath', '//input[@placeholder="Search"]'):
                    search = self.driver.find_element(By.XPATH, '//input[@placeholder="Search"]')
                else:
                    raise NoSuchElementException("There is no option to search vms")

                search.clear()
                search.send_keys(vm_name)
                search.send_keys(Keys.ENTER)
                self.wait_for_completion()

            if self.check_if_entity_exists("xpath", "//span[@title='{0}']".format(vm_name)):
                self.driver.find_element(By.XPATH, "//span[@title='{0}']".format(vm_name)).click()
            elif self.check_if_entity_exists("xpath", "//span[text()='{0}']".format(vm_name)):
                self.driver.find_element(By.XPATH, "//span[text()='{0}']".format(vm_name)).click()
            elif self.check_if_entity_exists("xpath", "//span[contains(text(),'{0}')]".format(vm_name)):
                self.driver.find_element(By.XPATH, "//span[contains(text(),'{0}')]".format(vm_name)).click()
            else:
                raise Exception("There is no VM named {0}.".format(vm_name))
            self.log.info("Selected the VM %s", str(vm_name))
        except Exception as exp:
            raise Exception("Exception occurred while searching and selecting VM. {0}".format(
                str(exp)
            ))

    def cv_single_select(self, label, value):
        """
        Selects an element from the dropdown

        Args:
            label   (str):   the label corresponding to the dropdown
            value   (str):   the value to be selected in the dropdown

        Raises:
            Exception:
                if the value passed is not a string or
                if the dropdown is not present or
                if the plan is not present in the dropdown

        """
        if not isinstance(value, str):
            raise Exception("The dropdown will accept only single value. Please pass a string")

        if self.check_if_entity_exists("xpath", "//label[contains(text(),'" + label + "')]"):
            label_xpath = "//label[contains(text(),'" + label + "')]"
        elif self.check_if_entity_exists("xpath", "//label/span[contains(text(),'" + label + "')]"
                                         ):
            label_xpath = "//label/span[contains(text(),'" + label + "')]"
        else:
            raise Exception("There is no dropdown with the given name or ID")

        select_xpath = label_xpath + "//isteven-multi-select"
        if not self.check_if_entity_exists("xpath", select_xpath):
            select_xpath = label_xpath + "/..//isteven-multi-select"
            if not self.check_if_entity_exists("xpath", select_xpath):
                select_xpath = label_xpath + "/../..//isteven-multi-select"

        try:
            self.driver.find_element(By.XPATH, select_xpath).click()
            self.wait_for_completion()
        except Exception:
            raise Exception('Drop down cannot be found by cv_single_select, please check the logs')

        # To use search box if exists
        search = f"{select_xpath}//div[@class='line-search']/input"
        if self.check_if_entity_exists('xpath', search):
            self.driver.find_element(By.XPATH, search).clear()
            self.driver.find_element(By.XPATH, search).send_keys(value)
            self.wait_for_completion()

        select_option_xpath = select_xpath + "//div[@class='checkBoxContainer']"
        if self.check_if_entity_exists("xpath", select_option_xpath):
            span_xpath = select_option_xpath + "//span[contains(text(),'" + value + "')]"
            div_xpath = select_option_xpath + "//div[contains(text(),'" + value + "')]"

            if self.check_if_entity_exists('xpath', span_xpath):
                checkbox_sibling = span_xpath + "/preceding-sibling::input"
                if not self.driver.find_element(By.XPATH, checkbox_sibling).is_selected():
                    self.driver.find_element(By.XPATH, span_xpath).click()
                    self.wait_for_completion()
                else:
                    self.driver.find_element(By.XPATH, select_xpath).click()
                    self.wait_for_completion()

            elif self.check_if_entity_exists('xpath', div_xpath):
                self.driver.find_element(By.XPATH, div_xpath).click()
                self.wait_for_completion()

        else:
            raise Exception("The given value is not present")

    def date_picker(self,
                    time_value,
                    time_id=None,
                    pick_time_only=False):
        """
        Picks the time in the date or time picker

        Args:
            time_value   (dict):        the time to be set as range during the browse

                Sample dict:    {   'year':     2017,
                                    'month':    december,
                                    'date':     31,
                                    'hours':    09,
                                    'minutes':  19,
                                    'session':  'AM'
                                }

            time_id      (str):  from / to be chosen as date range

            pick_time_only (bool):     Picks only the time if True

        """
        if time_id:
            # Used during browse to select from and to time
            year_month = f"//div[@id='{time_id}']/div//tr[1]/th[2]/button"
            date_xpath = f"//div[@id='{time_id}']/div//button/span[contains(text()" \
                         f",'{time_value['date']}') and not(contains(@class,'text-muted'))]"
            hours_xpath = f"//div[@id='{time_id}']//td[contains(@class," \
                          "'form-group uib-time hours')]/input"
            mins_xpath = f"//div[@id='{time_id}']//td[contains(@class," \
                         "'form-group uib-time minutes')]/input"
            session_xpath = f"//div[@id='{time_id}']//td[@class='uib-time am-pm']/button"
            hfs_pit_xpath = ""
        else:
            # Used during schedule creation
            year_month = "//tr[1]/th[2]/button"
            date_xpath = f"//button/span[contains(text(),'{time_value['date']}')" \
                         " and not(contains(@class,'text-muted'))]"
            hours_xpath = "//td[contains(@class, 'form-group uib-time hours')]/input"
            mins_xpath = "//td[contains(@class, 'form-group uib-time minutes')]/input"
            session_xpath = "//td[@class='uib-time am-pm']/button"
            hfs_pit_xpath = "//td[@class='uib-decrement hours']/a[@class='btn btn-link']"

        if not pick_time_only:
            self.driver.find_element(By.XPATH, year_month).click()
            self.wait_for_completion()

            if time_value.get('year'):
                self.driver.find_element(By.XPATH, year_month).click()
                self.wait_for_completion()
                self.driver.find_element(By.XPATH, f"//button/span[contains(text(),'{time_value['year']}')]").click()
                self.wait_for_completion()
            self.driver.find_element(
                By.XPATH, f"//button/span[contains(text(),'{time_value['month'].capitalize()}')]"
            ).click()
            self.wait_for_completion()
            self.driver.find_element(By.XPATH, date_xpath).click()
            self.wait_for_completion()

        if time_value.get('hours'):
            if time_value.get('hfs_pit'):
                self.driver.find_element(By.XPATH, hfs_pit_xpath).click()
            if (hour_elem := self.driver.find_element(By.XPATH, hours_xpath)).is_displayed() \
                    and (min_elem := self.driver.find_element(By.XPATH, mins_xpath)).is_displayed():
                hour_elem.clear()
                hour_elem.send_keys(time_value['hours'])
                min_elem.clear()
                min_elem.send_keys(time_value['mins'])
            else:
                if time_value['hours'] > 12:
                    time_string = f"{time_value['hours'] - 12}:{time_value['minutes']:02d} PM"
                elif time_value['hours'] == 12:
                    time_string = f"{time_value['hours']}:{time_value['minutes']:02d} PM"
                else:
                    time_string = f"{time_value['hours']}:{time_value['minutes']:02d} AM"
                try:
                    self.click_by_xpath(f"//cv-time-slot-picker//span[text() = '{time_string}']")
                except NoSuchElementException as exp:
                    raise Exception(f"No backup job found at time {time_value}") from exp

        if time_value.get('session'):
            sess = self.driver.find_element(By.XPATH, session_xpath)
            if not time_value['session'] == sess.text:
                sess.click()

    @WebAction()
    def click_button_using_text(self, value):
        """
        Method to click on a button using text

        Args:
            value (str) : text of the button to be clicked
        """
        buttons = self.driver.find_elements(By.XPATH, f"//button[contains(.,'{value}')]")
        for button in buttons:
            if button.is_displayed():
                button.click()
                break

    @WebAction()
    def click_button_using_id(self, value):
        """
        Method to click on a button using id

        Args:
            value (str)    : id of the button to be clicked
        """
        self.driver.find_element(By.XPATH, f"//button[@id='{value}']").click()

    def click_button(self, value=None, id=None, wait_for_completion=True):
        """
        Clicks on button by text value or id value

        Args:
            value (str)                 : text of the button to be clicked
            id (str)                    : id of the button to be clicked
            wait_for_completion (bool)  : Whether to wait for loading to finish
        Returns:
            None

        Raises:
            Exception   : if both value and id are None
        """
        if value:
            self.click_button_using_text(value)
        elif id:
            self.click_button_using_id(id)
        else:
            raise Exception('click_button: Please provide at least one input')
        if wait_for_completion:
            self.wait_for_completion()

    @WebAction()
    def get_element_value_by_id(self, element_id):
        """
        Gives the element value with the help of id
        Args:
            element_id (Str): Id of the element
        Returns (str) : Value of the given element
        """
        return self.driver.find_element(By.ID, element_id).get_attribute("value")

    @PageService
    def get_page_actions_list(self, group_by=False):
        """Gets visible page actions from drop down menu"""
        flatten_grid_list = []
        nested_grid_list = []
        group_list = []
        page_actions_list = self.__get_page_actions_list()
        page_actions_list = [action.text for action in page_actions_list]
        if group_by:
            for action in page_actions_list:
                if action == '':
                    nested_grid_list += [group_list]
                    group_list = []
                else:
                    group_list += [action]
            nested_grid_list += [group_list]
            return nested_grid_list
        else:
            for action in page_actions_list:
                if action != '':
                    flatten_grid_list += [action]
            return flatten_grid_list

    @PageService()
    def get_locale_name(self):
        """
        Returns the currently selected language's locale name in admin console

        Returns:
            locale    (str):   the language in action

        """
        self.__expand_locale_selection_drop_down()
        selected_locale = self.__get_selected_locale()

        if selected_locale in ["en_US", "en"]:
            selected_locale = "en"
            self.ext = ".properties"
        else:
            self.ext = "_" + selected_locale + ".properties"
        return selected_locale

    @PageService()
    def get_all_languages(self):
        """
        Returns the list of all language's locale name

        Returns:
            (list)  -- List of all languages

        """
        self.__expand_locale_selection_drop_down()
        return self.__get_all_languages()

    @PageService()
    def check_for_locale_errors(self):
        """To check for locale errors on the page"""
        try:
            self.driver.find_element(By.XPATH, '//span[contains(text(), "??")] | //div[contains(text(), "??")]')
        except NoSuchElementException:
            pass
        else:
            raise CVWebAutomationException(f'Locale errors found on {self.driver.current_url} page')

    @PageService(react_frame=False)
    def change_language(self, language, page_obj):
        """
        Change the localization language of admin console

        Args:
            page_obj    (object):       the instance of the class

            language    (str):   the language to be changed to in English

        """

        if not self.locale_ids:
            self.__get_locale_ids()
        if self.locale_ids.get(language.lower()):
            lang_id = self.locale_ids[language.lower()]
        else:
            raise Exception("There is no language with the given name. Please check your input")

        self.__expand_locale_selection_drop_down()
        self.__select_language(lang_id)
        self.get_locale_name()
        self.props = {}
        self.loaded_locale_files = []
        self.load_properties(page_obj)

    def select_for_restore(self, file_folders, all_files=False, select_one=False, file_paths=False):
        """
        Selects files, folders for restore

        Args:
            file_folders (list):    the list of files and folders to select for restore

            all_files   (bool):     select all the files shown for restore / download

            select_one  (bool):     select first file in the list for restore /download

            file_paths  (bool):     select the file paths specified in file_folders list.
                                    for file restore from vm.

        Raises:
            Exception:
                if at least one of the files / folders could not be selected

        """
        import re
        self.log.info("Selecting items to submit for restore")
        if all_files:
            elem = self.driver.find_element(By.XPATH, "//div[@class='ui-grid-header-cell-wrapper']/div/div/div/div/div")
            if 'selected' not in elem.get_attribute('class'):
                elem.click()
                self.wait_for_completion()
            return

        selected = []
        while True:
            elements = self.driver.find_elements(By.XPATH, "//div[1]/div[2]/div[2]/div[@class='ui-grid-canvas']/div")
            index = 1
            flag = []
            for elem in elements:
                if file_paths:
                    f_elem = elem.find_element(By.XPATH, "./div/div[3]").text
                else:
                    f_elem = elem.find_element(By.XPATH, "./div/div[1]").text
                for file in file_folders:
                    file_path_components = file.split('\\') if '\\' in file else file.split('/')
                    file_regex = r"(\\\|/)".join(file_path_components)
                    if (f_elem == file) or (re.search(file_regex, f_elem)):
                        flag.append(index)
                        selected.append(file)
                    else:
                        continue
                index = index + 1
            for flg in flag:
                flg = str(flg)
                self.driver.find_element(
                    By.XPATH,
                    "//div[1]/div[1]/div[2]/div[@class='ui-grid-canvas']/div[" +
                    flg +
                    "]/div/div/div/div/div"
                ).click()
                file_folders = list(set(file_folders) - set(selected))
                if select_one:
                    file_folders = []
                    break
            if self.cv_table_next_button_exists():
                if self.driver.find_element(By.XPATH, "//button[@ng-disabled='cantPageForward()']").is_enabled():
                    self.cv_table_click_next_button()
                    continue
                else:
                    break
            else:
                break
        if file_folders:
            raise Exception("Could not find the items " + str(file_folders))

    @PageService()
    def recovery_point_restore(self, recovery_time=None):
        """
        Restores the VM from the backup history

        Args:
            recovery_time     (str):   the backup date in 01-September-1960 format

        """
        try:
            self.select_overview_tab()
            if recovery_time:
                calender = {
                    'date': (recovery_time.split("-"))[0],
                    'month': (recovery_time.split("-"))[1],
                    'year': (recovery_time.split("-"))[2]
                }
                self.date_picker(calender)
            self.tile_select_hyperlink("Recovery point", "Restore")
        except Exception as exp:
            raise CVWebAutomationException(
                "Either recovery point was not given or the current date does not have any backups. ", exp)

    @WebAction(delay=0)
    def fill_form_by_id(self, element_id, value):
        """
        Fill the value in a text field with id element id.

        Args:
            element_id (str) -- the ID attribute of the element to be filled
            value (str)      -- the value to be filled in the element

        Raises:
            Exception:
                If there is no element with given name/id

        """
        element = self.driver.find_element(By.ID, element_id)
        element.send_keys(u'\ue009' + 'a' + u'\ue003')  # CTRL + A + Backspace
        element.send_keys(value)
        self.wait_for_completion()

    @WebAction()
    def fill_form_by_name(self, name, value):
        """
        Fill the value in a text field with id element id.

        Args:
            name (str) - name attribute value of the element
            value (str)      -- the value to be filled in the element

        Raises:
            Exception:
                If there is no element with given name/id

        """
        element = self.driver.find_element(By.NAME, name)
        element.send_keys(u'\ue009' + 'a' + u'\ue003')  # CTRL + A + Backspace
        element.send_keys(value)
        self.wait_for_completion()

    @WebAction()
    def fill_form_by_class_name(self, name, value):
        """
        Fill the value in a text field with 'name' as its class.

        Args:
            name (str) - name attribute value of the element

            value (str)      -- the value to be filled in the element

        Raises:
            Exception:
                If there is no element with given name/id

        """
        element = self.driver.find_element(By.CLASS_NAME, name)
        element.send_keys(u'\ue009' + 'a' + u'\ue003')  # CTRL + A + Backspace
        element.send_keys(value)
        self.wait_for_completion()

    @PageService()
    def select_overview_tab(self):
        """
        Selects the overview tab

        Raises:
            NoSuchElementException:
                if the Overview tab is not present
        """
        self.access_tab(self.props['label.tab.overview'])

    @PageService()
    def select_configuration_tab(self):
        """
        Selects the configuration tab

        Raises:
            NoSuchElementException:
                if the configuration tab is not present
        """
        self.access_tab(self.props['label.nav.configuration'])

    @PageService()
    def select_file_servers_tab(self):
        """
        Selects the file servers tab

        Raises:
            NoSuchElementException:
                if the file servers tab is not present
        """
        self.access_tab(self.props['label.nav.servers'])

    @PageService()
    def select_content_tab(self):
        """
        Selects the content tab

        Raises:
            NoSuchElementException:
                if the content tab is not present
        """
        self.access_tab(self.props['label.content'])

    @PageService()
    def get_current_tab(self):
        """
        Returns the current navigated tab

        Returns:
                CurrentTab      (str)--     Current Navigated Tab
        """

        return self.driver.find_element(
            By.XPATH,
            "//div[contains(@class,'selected')]/*/span[contains(@ng-bind,'tab.title')] | "
            "//a[contains(@class, 'MuiTab-root') and contains(@aria-selected, 'true')]"
        ).text

    def expand_options(self, label):
        """
        Expands the advanced options or other chevron options

        Raises:
            NoSuchElementException:
                if the element is not found

        """
        xpath = "//div[contains(text(),'" + label + "')]/i"
        if self.check_if_entity_exists("xpath", xpath):
            class_value = self.driver.find_element(By.XPATH, xpath).get_attribute("class")
            if 'ion-chevron-right' in class_value:
                self.driver.find_element(By.XPATH, xpath).click()
                self.wait_for_completion()
        else:
            raise NoSuchElementException("No chevron found with the given label %s", label)

    @WebAction()
    def check_radio_button(self, label):
        """
        checks if radio button given the value exists.

        Args:
            label  (str)   -- Label text of the radio button.

        Returns:
            True or False
        """
        xpath_radio_from_value = f"//input[@type='radio']/../../label[contains(.,'{label}')]"
        return self.check_if_entity_exists("xpath", xpath_radio_from_value)

    @WebAction(delay=0)
    def expand_accordion(self, label):
        """Clicks the heading of an accordion"""
        xp = f"//span[contains(text(),'{label}')]/..//i[contains(@class,'glyphicon-chevron-right')]"
        expand_icon = self.driver.find_elements(By.XPATH, xp)
        if expand_icon:
            expand_icon[0].click()

    @WebAction(delay=0)
    def close_accordion(self, label):
        """Clicks the heading of an accordion"""
        xp = f"//span[contains(text(),'{label}')]/..//i[contains(@class,'glyphicon-chevron-down')]"
        expand_icon = self.driver.find_elements(By.XPATH, xp)
        if expand_icon:
            expand_icon[0].click()

    @WebAction()
    def __is_cvaccordion_expanded(self, label):
        """
        Checks if the cv-accordion is expanded or not
        Args:
            label   (str) :  label of the CVAccordion to be checked
        Returns:
            True or False, whether the cv accordion is open or not
        """
        xpath = f"//div[@accordion-label='{label}']//div[contains(@class, 'cv-accordion-header')]"
        return 'expanded' in self.driver.find_element(By.XPATH, xpath).get_attribute("class")

    @WebAction()
    def __click_cvaccordion(self, label):
        """
        Click the heading of an accordion using the label.
        Args:
            label   (str) :  label of the CVAccordion to be clicked
        """
        xpath = f"//div[@accordion-label='{label}']//div[contains(@class, 'cv-accordion-header')]"
        self.driver.find_element(By.XPATH, xpath).click()

    @PageService()
    def expand_cvaccordion(self, label):
        """
        Expand the accordion using the label provided

        Args:
            label   (str) :  label of the CVAccordion to be expanded
        """
        if not self.__is_cvaccordion_expanded(label):
            self.__click_cvaccordion(label)

    @PageService()
    def close_cvaccordion(self, label):
        """
        Close the accordion using the label provided

        Args:
            label   (str) :  label of the CVAccordion to be closed
        """
        if self.__is_cvaccordion_expanded(label):
            self.__click_cvaccordion(label)

    @PageService()
    def access_menu(self, name):
        """
        Click menu item
        Args:
            name: localized menu text
        """
        self.__click_menu(name)
        self.wait_for_completion()

    @PageService()
    def access_menu_from_dropdown(self, name):
        """ Method to click on the menu under a dropdown on a page
        Args:
            name: localized menu text
        """
        self.__click_main_bar_dropdown()
        self.wait_for_completion()
        self.access_menu(name)

    @PageService()
    def access_sub_menu(self, name):
        """ Method to click on the item under a dropdown in database page
        Args:
            name: localized sub menu text
        """
        self.unswitch_to_react_frame()
        self.__click_access_sub_menu(name)
        self.wait_for_completion()

    @PageService()
    def access_action(self, action_name):
        """
        Access action in page
        Args:
            action_name: text used for action
        """
        self.__click_on_action(action_name)
        self.wait_for_completion()

    @WebAction()
    def __click_breadcrumb_link(self, link_text):
        """
        Method to click on breadcrumb link using given text

        Args:
            link_text (str)  -- Text on the breadcrumb link
        """
        xp = f"//a[contains(text(),'{link_text}')]"
        self.driver.find_element(By.XPATH, xp).click()

    @PageService()
    def select_breadcrumb_link_using_text(self, link_text):
        """
        Selects breadcrumb link containing the given text
        Args:
            link_text (str)  -- Text on the breadcrumb link
        """
        self.__click_breadcrumb_link(link_text)
        self.wait_for_completion()

    @WebAction()
    def access_tab_action(self, name):
        """ Method to click on the item under a dropdown in acess tab
        Args:
            name: localized sub menu text
        """
        self.driver.find_element(By.XPATH, f"//a[@class='tabAction'][contains(text(),'{name}')]").click()

    @WebAction()
    def access_tab_from_dropdown(self, name, col_id=None):
        """Method to click on the the access tab drop down
        Args:
            name       (str): Name of the access tab to click
            col_id      (int): Column id to click
        """
        if col_id:
            self.__click_main_bar_dropdown(col_id)
        else:
            self.__click_main_bar_dropdown()
        self.wait_for_completion()
        self.access_tab_action(name)

    @WebAction()
    def search_aws_vm(self, zone=None, region=None):
        """
        Searches for a AWS zone

        Args:

            zone     (str)    :   availability zone of AWS instance

            region   (str)    :   region of AWS instance

        """

        self.click_by_xpath('//span[contains(text(),"' + region + '")]/span')
        self.click_by_xpath('//span[@title="' + zone + '"]')

    @WebAction()
    def wait_for_element_to_be_clickable(self, element_id, wait_time=30):
        """
        Waits until element is clickable

        Args:
            element_id (str)    --  element id
            wait_time (int)     --  max time to wait in seconds

        Raises:
            Exception           --  if element does not become clickable after wait_time
        """
        try:
            WebDriverWait(self.driver, wait_time).until(ec.element_to_be_clickable((By.ID, element_id)))
        except TimeoutException:
            raise Exception(f"Element id {element_id} is not clickable")

    @WebAction()
    def wait_for_element_based_on_xpath(self, xpath, wait_time=30):
        """
        Waits for an element to be clickable based on the given XPath.

        Args:
            xpath (str): The XPath of the element to wait for.
            wait_time (int, optional): The maximum time to wait in seconds. Defaults to 30.

        Raises:
            Exception: If the element is not clickable within the specified wait time.

        """
        try:
            WebDriverWait(self.driver, wait_time).until(ec.element_to_be_clickable((By.XPATH, xpath)))
        except TimeoutException:
            raise Exception(f"Timeout waiting for element after {wait_time} seconds")

    @WebAction()
    def select_report_tab(self, tab_name):
        """
        Select the tab with the name specified in the report page

        Args:
            tab_name (str)      --  localized name of the tab to be selected
        """
        self.driver.find_element(By.XPATH, f"//li[@class='ng-binding ng-scope' and contains(.,'{tab_name}')]").click()

    @WebAction()
    def fill_form_by_xpath(self, xpath, value):
        """
        Fill the value in a text field with id element id.

        Args:
            xpath (basestring)      -- xpath of input element
            value (basestring)      -- the value to be filled in the element

        Raises:
            Exception:
                If there is no element with given name/id

        """
        element = self.driver.find_element(By.XPATH, xpath)
        element.send_keys(u'\ue009' + 'a' + u'\ue003')  # CTRL + A + Backspace
        element.send_keys(value)
        self.wait_for_completion()

    @WebAction()
    def click_cancel(self):
        """
        Clicks on the cancel button for forms,dialogs and panels
        Raises:
            Exception: If there is no cancel button visible
        """
        xpath = (f"//button[contains(@class, 'MuiButton-outlined') and "
                 f"contains(text(), '{self.props['label.cancel']}')]")
        self.driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def click_save(self, exact_word=False):
        """
       Clicks on the save button for forms,dialogs and panels
       Args:
           exact_word   (bool)  :   Whether to check for the exact label 'Save'
       Raises:
           Exception            :   If there is no save button visible
       """
        if exact_word:
            xpath = f"//button[@aria-label = '{self.props['label.save']}']"
        else:
            xpath = f"//button[contains(@aria-label,'{self.props['label.save']}')]"
        self.driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def check_error_page(self) -> None:
        """Method to check if the page header is Error"""
        if self.driver.title == "Error":
            err_element = self.driver.find_elements(By.XPATH, "//div[@class='server-down-wrapper'] "
                                                              "| //div[@class='error'] ")
            if err_element:
                raise CVWebAutomationException(f"Error Received in page: {err_element[0].text}")

    @WebAction()
    def click_submit(self, wait=True, index=0):
        """
        Clicks the submit button on forms,dialogs and panels
        """
        submit_btn_xp = f"//button[contains(@aria-label,'{self.props['label.submit']}')]"
        self.driver.find_elements(By.XPATH, submit_btn_xp)[index].click()
        if wait:
            self.wait_for_completion()

    @WebAction()
    def __read_username(self):
        """Gets the username displayed in user settings header"""
        user_settings_drop_down = self.driver.find_element(By.XPATH, "//span[@class='header-user-settings-name']")
        return user_settings_drop_down.get_attribute('outerText').strip()

    @PageService(react_frame=False)
    def logged_in_user(self):
        """Returns the username displayed on top right"""
        return self.__read_username()

    @WebAction()
    def get_element_color(self, xpath, css_property='background-color'):
        """ Gets the web element's color from its css property """
        color_pattern = r'rgba?\(\d+,\s*\d+,\s*\d+(,\s*\d+)?\)'
        return Color.from_string(
            re.match(
                color_pattern,
                self.driver.find_element(By.XPATH, xpath).value_of_css_property(css_property)
            ).group()
        ).hex

    @WebAction()
    def __get_react_errors(self) -> list:
        """Finds and returns the react errors"""
        elements = self.driver.find_elements(By.XPATH, "//p[contains(@class, 'Mui-error')]")
        errors = []

        for element in elements:
            errors.append(element.text)

        return errors

    @PageService()
    def check_for_react_errors(self, raise_error: bool = True) -> None:
        """Checks for any inline errors in react

        Args:
            raise_error(bool): should raise error or not
        """
        errors = self.__get_react_errors()

        if errors:
            self.log.error(errors)

        if errors and raise_error:
            raise CVWebAutomationException(errors)

    @WebAction()
    def __open_hotkey_dialog(self):
        """Method to open hotkey dialog"""
        body_element = self.driver.find_element(By.TAG_NAME, 'body')
        body_element.send_keys("debuguisettings")

    @WebAction()
    def __search_hotkey(self, hotkey_name: str) -> None:
        """Method to search hotkey"""
        search_box = self.driver.find_element(By.ID, 'hotkeySearch')
        search_box.send_keys(u'\ue009' + 'a' + u'\ue003')  # CTRL + A + Backspace
        search_box.send_keys(hotkey_name)

    @PageService()
    def hotkey_settings(self, hotkey_name: str, enable: bool = True) -> None:
        """ Method to enable / disable hotkey

        Args:
            hotkey_name (str): Hotkey name
            enable (bool): Hotkey to be enabled / disabled
        """
        self.__open_hotkey_dialog()
        self.wait_for_completion()
        self.__search_hotkey(hotkey_name)

        toggle_element = self.driver.find_element(By.ID, hotkey_name)
        toggle_enabled = toggle_element.is_selected()

        if enable and not toggle_enabled:
            toggle_element.click()

        if not enable and toggle_enabled:
            toggle_element.click()

        self.click_button_using_text('Save')
        self.wait_for_completion()

    @WebAction()
    def click_on_base_body(self):
        """
        Clicks body tag to collapse menus or callouts
        """
        self.driver.find_element(By.TAG_NAME, 'body').click()

    @PageService()
    def is_any_parent_disabled(self, element: WebElement) -> bool:
        """
        Check if any of the parent elements is disabled.

        Args:
            element (WebElement): Child web element to be considered.

        Returns:
            bool: True if any parent element is disabled, False otherwise.
        """
        while element:
            try:
                if element.get_attribute("disabled") or 'disabled' in element.get_attribute("class"):
                    return True  # Parent is disabled
                element = element.find_element(By.XPATH, '..')  # Move to the next parent
            except InvalidSelectorException:
                break  # Exit the loop when there are no more parent elements

        return False  # No parent is disabled

    @PageService()
    def access_activity(self):
        """Method to access all activity from header"""
        self.click_by_id("header-activity-notifications")
        self.select_hyperlink(self.props['label.viewAll'])

    @PageService()
    def access_jobs_notification(self):
        """Method to access job notification on top header"""
        self.click_by_id("header-job-notifications")

    @PageService()
    def access_alerts_notification(self):
        """Method to access alerts notification on top header"""
        self.click_by_id("header-alert-notifications")

    @PageService()
    def access_events_notification(self):
        """Method to access events notification on top header"""
        self.click_by_id("header-event-notifications")

    @WebAction()
    def click_menu_backdrop(self):
        """
        Web Action to collapse open menus by clicking only on
        Backdrop div so No other elem is clicked by accident
        """
        for _ in range(5):
            backdrops = self.driver.find_elements(
                By.XPATH,
                "//div[@aria-hidden='true' and contains(@class, 'MuiBackdrop-invisible')]"
            )
            if not backdrops:
                return
            for hidden_div in backdrops:
                if hidden_div.is_displayed():
                    try:
                        hidden_div.click()
                    except WebDriverException:
                        pass
