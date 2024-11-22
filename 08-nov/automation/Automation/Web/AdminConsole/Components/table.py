"""
Module to deal with Tables used in Admin console pages

Table:

    access_action_item()                :     Selects the action item in table

    access_context_action_item()        :     Selects the action item in table right click menu

    access_link()                       :     Selects the entity from list page and navigates to
                                              given entity's details

    access_link_by_column()             :     Search by column value and access link text

    access_link_without_text()          :     Search by column value and access any link inside cell

    get_column_data()                   :     Get column data

    get_number_of_columns()             :     Gets number of columns present in table

    get_visible_column_names()          :     Get visible Column names

    select_dropdown()                   :     Selects the dropdown on top of table

    search_for()                        :     Clears the search bar and fills given value
    
    clear_search()                      :     Clears the search bar and resets to default

    context_menu_sequential_select()    :     Opens the context menu on the filtered enitity and clicks on the elements in the list sequentially

CVTable:

    access_action_item()                :     Selects the action item in the table action menu

    access_link()                       :     Navigates to the given entity

    search_for()                        :     Performs the search with the keyword on the table

ReactTable:

    access_action_item()                :     Selects the action item in table

    access_context_action_item()        :     Selects the action item in table right click menu

    access_link()                       :     Selects the entity from list page and navigates to
                                              given entity's details

    access_link_by_column()             :     Search by column value and access link text

    get_column_data()                   :     Get column data

    get_number_of_columns()             :     Gets number of columns present in table

    get_visible_column_names()          :     Get visible Column names

    get_all_column_names()              :     Gets all column names from table

    search_for()                        :     Clears the search bar and fills given value

    clear_search()                      :     Clears the search bar and resets to default

    reload_data()                       :     Reloads the table data by clicking reload button

    get_table_data()                    :     returns entire table data

    is_entity_present_in_column()       :     checks whether given entity is present in column or not

    get_total_rows_count()              :     gets total table rows count

    select_all_rows()                   :     selects all rows in table

    select_rows()                       :     Selectes rows based on list input

    access_toolbar_menu()               :     Access table toolbar menu to perform operation

    access_menu_from_dropdown()         :     Access table toolbar menu item from dropdown

    apply_filter_over_column()          :     Applies filter values over column in table

    clear_column_filter()               :     clears the column filter applied on table

    display_hidden_column()             :     Method to select non default column to be displayed on table

    apply_sort_over_column()            :     Applies sorting order on column

    get_grid_actions_list()             :     Gets visible grid action menu list from table

    view_by_title()                     :     Select table view from top of table title

    select_company()                    :     Selects company in the react table

    select_default_filter()             :     Selects the value from given filter in the react table

    go_to_page()                        :     Goes to the specified page in the table

    get_applied_pagination()            :     Gets the pagination setting currently active

    get_all_tabs()                      :     Method to return all the available Tabs in the react table

    hover_click_actions_sub_menu()      :     Clicks the actions menu, hover to the action item and
                                                        clicks the action element in a sub-menu

    list_views()                        :     Lists all the views available in the react table

    currently_selected_view()           :     Returns the name of the view active currently

    create_view()                       :     Creates a view in the react table

    edit_view()                         :     Edits a view in the react table

    select_view()                       :     Selects a view form the react table

    delete_view()                       :     Deletes a view form the react table

    wait_column_values()                :     Waits for column values to match given strings

    wait_for_rows()                     :     Waits for specified rows to appear in table

    unselect_all_rows()                 :     Uncheck all checkboxes of selected rows

    click_forward_arrow()               :     Clicks the row action with the given action name for the given row

    select_row_action()                 :     Clicks the row action with the given action name for the given row

    type_input_for_row()                :     Enter the given input_value to the input field
                                                        with given type for given row
                                                        
    hide_selected_column_names()        :     Method to hide the list of the columns from the table      
    
    click_grid_reset_button()          :     Method to click on reset button of the grid       
    
    click_reset_column_widths()        :    Method to click on reset column width option     

    setup_table()                      :    Wrapper to setup table columns and search

    get_rows_data()                     :   Method to get table data as OrderedDict of rows

    export_csv()                        :   Method to export table data into csv files

    get_grid_stats()                      --  Returns the stats under grid info component in job details page

    access_link_by_column_title         :   Method to search by entity_name and access link_text under column_title
                                            on React Table
    click_action_menu()                 :  Clicks on Action menu of selected entity

    access_action_item_inline()         :  Selects the action item in table inline

Rfilter()       -- class which contains column filter criteria enum for react tables

Integration tests for components are added in below mentioned test cases, for any new functionality added here
add the corresponding integration method

        TC 59679        --      Test case for Rtable class(React table)

        TC 56174        --      Test case for Table class(Kendo Grid table)

ContainerTable()
    __get_column_name()               :   Get the column names form the Container table

    __get_row_data()                  :   Get the row value from the container table

    get_table_data()                  :   Get data from container table

"""
import enum
from time import sleep
from collections import OrderedDict

from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, \
    StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains, ScrollOrigin
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from Web.Common.page_object import (WebAction, PageService)
from Web.Common.exceptions import CVWebAutomationException

from .panel import RDropDown


class Table:
    """Table Component used in Command Center"""

    def __init__(self, admin_console, id=None):
        self._admin_console = admin_console
        self._driver = admin_console.driver
        if id:
            self._xp = "//div[@id='" + id + "']"
        else:
            self._xp = "//div[contains(@class,'cv-kendo-grid')] | //div[contains(@class,'k-grid')]"

    @WebAction()
    def __fetch_table_title(self):
        """Fetches the table title"""
        title = self._driver.find_element(By.XPATH, "//div[@class='cv-k-grid-title']/h2")
        return title.text

    @WebAction()
    def __get_column_names(self):
        """Read Column names"""
        col_xp = "//th[@role='columnheader' and not(@style='display:none')]"
        columns = self._driver.find_elements(By.XPATH, self._xp + col_xp)
        column_names = []
        for column in columns:
            self.__scroll_to_element(column)
            if column.is_displayed():
                column_names.append(column.text)
        self.__scroll_reset()
        return column_names

    @WebAction(delay=0)
    def __get_data_from_column_by_idx(self, col_idx):
        """Read data from column"""
        row_xp = f"//td[@role='gridcell' and not(contains(@id,':checkbox')) and not(@style='display:none')][{col_idx}]"
        rows = self._driver.find_elements(By.XPATH, self._xp + row_xp)
        data = []
        for cell in rows:
            self.__scroll_to_element(cell)
            if cell.is_displayed():
                data.append(cell.text.strip())
        self.__scroll_reset()
        return data

    @WebAction()
    def __get_grid_actions_list(self):
        """Reads data from grid actions menu"""
        return self._driver.find_elements(By.XPATH, "//*[contains(@id,'cv-permit-actions-dropdown-menu')]/div//hr | "
                                                    "//*[contains(@id,'cv-permit-actions-dropdown-menu')]/div//a")

    @WebAction()
    def __expand_search(self):
        """expands the search bar"""
        self._driver.find_element(By.XPATH, self._xp + "//div[contains(@id,'search-input-container')]").click()

    @WebAction()
    def __is_search_visible(self):
        """check if search bar is available"""
        search = self._driver.find_elements(By.XPATH, self._xp + "//input[@type='search']")
        return search and search[0].is_displayed()

    @WebAction()
    def __click_search(self):
        """enter search on grid"""
        search = self._driver.find_element(By.XPATH,
                                           self._xp + "//span[contains(@class, 'k-i-search')]")
        search.click()

    @WebAction(delay=0)
    def __enter_search_term(self, value):
        """enter search on grid"""
        element = self._driver.find_element(By.XPATH,
                                            self._xp + "/div[contains(@class,'k-grid-toolbar')]//following-sibling::div")
        attribute = element.get_attribute("class").split("cv-k-grid-")
        attribute = [item.strip() for item in attribute]
        if "toolbar-primary" in attribute and "search-focus" not in attribute:
            self.__expand_search()
        search = self._driver.find_element(By.XPATH, self._xp + "//input[@type='search']")
        search.clear()
        search.send_keys(value)

    @WebAction(delay=0)
    def __clear_search_box(self):
        """Clears the search box"""
        cross = self._driver.find_elements(By.XPATH, "//span[contains(@class,'k-icon k-i-close k-i-x')]")
        if cross and cross[0].is_displayed():
            cross[0].click()
            self._admin_console.wait_for_completion()

    @WebAction(delay=1)
    def __click_actions_menu(self, entity_name, partial_selection, second_entity=None):
        """
        Clicks Action menu
        """
        if not partial_selection:
            xp = (f"//*[text() ='{entity_name}']/ancestor::tr//"
                  f"div[contains(@class,'permittedActions')]//a")
            if second_entity is not None:
                xp = (f"//*[text() ='{entity_name}']/ancestor::tr/descendant::td//"
                      f"*[text()='{second_entity}']/ancestor::tr//"
                      f"div[contains(@class,\'permittedActions\')]//a")
            if not self._admin_console.check_if_entity_exists("xpath", xp):
                xp = (f"//*[text() ='{entity_name}']/ancestor::tr//"
                      f"span[contains(@class,'action-btn grid-action-icon')]")
                if not self._admin_console.check_if_entity_exists("xpath", xp):
                    xp = (f"//*[text() ='{entity_name}']/ancestor::tr//"
                          f"span[contains(@class,'grid-action-icon')]")
        else:
            xp = (f"//*[contains(text(), '{entity_name}')]/ancestor::tr//"
                  f"div[contains(@class,'permittedActions')]//a")
            if not self._admin_console.check_if_entity_exists("xpath", xp):
                xp = (f"//*[contains(text(), '{entity_name}')]/ancestor::tr//"
                      f"span[contains(@class,'action-btn grid-action-icon')]")
                if not self._admin_console.check_if_entity_exists("xpath", xp):
                    xp = (f"//*[contains(text(), '{entity_name}')]/ancestor::tr//"
                          f"span[contains(@class,'grid-action-icon')]")
        self._driver.find_element(By.XPATH, xp).click()

    @WebAction(delay=1)
    def __click_action_item(self, action_item):
        """Clicks on Action item under action menu"""
        elem = self._driver.find_element(By.XPATH,
                                         f"//ul[contains(@style,'display: block')]//a[text()='{action_item}']"
                                         )
        ActionChains(self._driver).move_to_element(elem).click().perform()

    @WebAction(delay=1)
    def __right_click_menu(self, entity_name):
        """
        Clicks context menu
        """
        entity = self._driver.find_element(By.XPATH,
                                           f"{self._xp}//*[contains(text(),'{entity_name}')]")
        actions = ActionChains(self._driver)
        actions.move_to_element(entity).context_click().perform()

    @WebAction(delay=1)
    def __click_context_action_item(self, action_item):
        """
        Clicks action item from context click drop down
        """
        elem = self._driver.find_element(By.XPATH,
                                         f"//div[@class='k-animation-container']//a[text()='{action_item}']"
                                         )
        ActionChains(self._driver).move_to_element(elem).click().perform()

    @WebAction(delay=1)
    def __mouse_over_and_click(self, entity_name):
        """
        Hovers over and clicks on options. Specific to context menu.
        """
        element = self._driver.find_element(By.XPATH,
                                            f"//div[@class='k-animation-container']//a[text()='{entity_name}']"
                                            )
        self._admin_console.mouseover_and_click(element, element)

    @WebAction()
    def __click_title_dropdown(self, label=None):
        """
        Clicks on title drop down on top of table
        """
        if label:
            dropdown_elem = self._driver.find_elements(By.XPATH, f"//div[@class='cv-k-grid-title']"
                                                                 f"//span[text()='{label}']/..//"
                                                                 f"a[contains(@class,'uib-dropdown-toggle')]")
        else:
            dropdown_elem = self._driver.find_elements(By.XPATH, f"//div[@class='cv-k-grid-title']"
                                                                 f"//a[contains(@class,'uib-dropdown-toggle')]")
        if self._admin_console.check_if_entity_exists("xpath", self._xp + "//div[@class='k-header k-grid-toolbar']"):
            self._admin_console.scroll_into_view(self._xp + "//div[@class='k-header k-grid-toolbar']")
        for elem in dropdown_elem:
            if elem.is_displayed():
                elem.click()
                break
        sleep(2)

    @PageService()
    def select_dropdown(self, label=None):
        """
        Clicks the dropdown above the table
        Args:
            label (str): Name on top of the table dropdown
        """
        self.__click_title_dropdown(label)

    @WebAction()
    def __filter_by_type(self, title_to_filter):
        """
        select filter by type

        Args:
            title_to_filter   (str):   title to select

        """
        elems = self._driver.find_elements(By.XPATH, f"//div[contains(@class, 'k-animation-container')]"
                                                     f"//a[text()='{title_to_filter}']")
        if not elems:
            elems = self._driver.find_elements(By.XPATH,
                                               f"//ul[contains(@class, 'cv-server-filter')]//a[text()='{title_to_filter}']"
                                               f" | //ul[contains(@class, 'dropdown-menu ')]//a[text()='{title_to_filter}']"
                                               )

        for elem in elems:
            if elem.is_displayed():
                elem.click()

    @WebAction(delay=0)
    def __select_row(self, name, deselect=False):
        """Select/deselect specified row"""
        xp = self._xp + f"//*[contains(text(), '{name}')]/ancestor::tr//input[@type='checkbox']/ancestor::td"
        rows = self._driver.find_elements(By.XPATH, xp)
        if not rows:
            raise NoSuchElementException(f"Rows not found with name [{name}]")
        for each_row in rows:
            if not each_row.is_displayed():
                continue
            row_class = each_row.find_element(By.XPATH, "..").get_attribute('class')
            if ((not deselect and 'k-state-selected' in row_class) or
                    (deselect and 'k-state-selected' not in row_class)):
                #  In case of multiple tables on same page we might face some issue
                continue
            hover = ActionChains(self._driver).move_to_element(each_row)
            hover.perform()
            sleep(1)
            try:
                each_row.click()
            except ElementClickInterceptedException:
                checkbox_xp = xp.split("/ancestor::td")[0]
                checked = bool(self._driver.find_element(By.XPATH, checkbox_xp).get_attribute('aria-checked'))
                if checked:
                    return
                else:
                    raise CVWebAutomationException("Checkbox not selected.")

    @WebAction()
    def __is_tool_bar_action_visible(self, menu_id):
        """Checks whether the toolbar menu is visible or not"""
        xp = f"//div[@class='toolbar']//li[contains(@data-cv-menu-item-id, '{menu_id}')]"
        menu_items = self._driver.find_elements(By.XPATH, xp)
        for menu_item in menu_items:
            if menu_item is None:
                continue
            menu_item_class = menu_item.get_attribute('class')
            if 'hidden' in menu_item_class or 'disabled' in menu_item_class or not menu_item.is_displayed():
                return False
        return True

    @WebAction()
    def __click_expand_tool_bar_menu(self):
        """Clicks on the tool bar menu's expand options button"""
        xp = "//li[@id='batch-action-menu_moreItem']"
        for element in self._driver.find_elements(By.XPATH, xp):
            if element is not None and element.is_displayed():
                element.click()
                break

    @WebAction()
    def __click_tool_bar_menu(self, menu_id):
        """
        click tool bar menu in table
        Args:
            menu_id: value of attribute data-cv-menu-item-id
        """
        xp = f"//li[contains(@data-cv-menu-item-id,'{menu_id}')]"
        menu_obj = [each_element for each_element in self._driver.find_elements(By.XPATH, xp) if
                    each_element.is_displayed()]
        if menu_obj:
            menu_obj[0].click()
        else:
            raise CVWebAutomationException("data-cv-menu-item-id [%s] element not found" % menu_id)

    @WebAction()
    def __expand_column_filter(self, column_name):
        """ Method to expand column filter drop down """
        col_settings_drop_down = self._driver.find_element(By.XPATH,
                                                           f"//th[@role='columnheader' and @data-title='{column_name}']"
                                                           f"//a[@aria-label='Column Settings']")
        col_settings_drop_down.click()
        sleep(2)

    @WebAction()
    def __click_menu_item(self, menu_item):
        """Method to click on any menu item"""
        menus = self._driver.find_elements(By.XPATH,
                                           "//div[@class='k-animation-container']//ul[@role='menubar']")
        for menu in menus:
            if menu.is_displayed():
                menu.find_element(By.XPATH, f".//span[contains(text(),'{menu_item}')]").click()
                break

    @WebAction()
    def __hover_menu_item(self, menu_item):
        """Method to hover on any menu item"""
        menus = self._driver.find_elements(By.XPATH,
                                           "//div[@class='k-animation-container']//ul[@role='menubar']")
        for menu in menus:
            if menu.is_displayed():
                item = menu.find_element(By.XPATH, f".//span[@class='k-link' and text()='{menu_item}']")
                self._driver.execute_script(
                    "var evObj = document.createEvent('MouseEvents'); "
                    "evObj.initMouseEvent(\"mouseover\",true, false, window, 0, 0, 0, 0, 0, false, false, "
                    "false, false, 0, null); arguments[0].focus();"
                    "arguments[0].dispatchEvent(evObj);", item)
                # hover = ActionChains(self._driver).move_to_element(item)
                # hover.perform()
                sleep(2)
                return

    @PageService()
    def __click_filter_menu_item(self):
        """ Method to click on Filter menu item """
        self.__click_menu_item("Filter")

    @PageService()
    def __hover_filter_menu_item(self):
        """ Method to hover on Filter menu item """
        self.__hover_menu_item("Filter")

    @PageService()
    def __click_columns_menu_item(self):
        """ Method to click on Columns menu item """
        self.__click_menu_item("Columns")

    @PageService()
    def __hover_columns_menu_item(self):
        """ Method to hover on Columns menu item """
        self.__hover_menu_item("Columns")

    @PageService()
    def __click_sort_item(self, ascending=True):
        """Method to click on Sort Ascending/Descending menu item"""
        menu_item = "Sort Ascending" if ascending else "Sort Descending"
        self.__click_menu_item(menu_item)

    @WebAction(delay=1)
    def __clear_integer_filter_criteria_textbox(self):
        """ Method to clear integer filter criteria textbox
        Args:
            integer_type(bool) : integer type filter
        """
        f_criteria_textbox = self._driver.find_elements(By.XPATH,
                                                        "//input[contains(@data-bind, 'value:filters[0].value')]/../input"
                                                        )
        for textbox in f_criteria_textbox:
            if textbox.is_displayed():
                textbox.clear()
                break

    @WebAction(delay=1)
    def __clear_filter_criteria_textbox(self):
        """ Method to clear filter criteria textbox
        Args:
            integer_type(bool) : integer type filter
        """
        f_criteria_textbox = self._driver.find_elements(By.XPATH,
                                                        "//input[contains(@data-bind, 'value:filters[0].value')]"
                                                        )
        for textbox in f_criteria_textbox:
            if textbox.is_displayed():
                textbox.clear()
                break

    @WebAction(delay=1)
    def __enter_filter_criteria(self, filter_term, integer_type=False):
        """
        Method to enter filter criteria

        Args:
            filter_term (str) : string to be filtered for a column
            integer_type(bool) : integer type filter
        """
        if integer_type:
            f_criteria = self._driver.find_elements(By.XPATH,
                                                    "//input[contains(@data-bind, 'value:filters[0].value')]/../input"
                                                    )
        else:
            f_criteria = self._driver.find_elements(By.XPATH,
                                                    "//input[contains(@data-bind, 'value:filters[0].value')]"
                                                    )
        for criteria in f_criteria:
            if criteria.is_displayed():
                criteria.send_keys(filter_term)
                break

    @WebAction(delay=1)
    def __enter_multi_filter_criteria(self, filter_term):
        """
        Method to enter filter criteria

        Args:
            filter_term (str) : string to be filtered for a column
        """
        f_criteria = self._driver.find_elements(By.XPATH,
                                                "//div[contains(@class, 'k-multiselect-wrap k-floatwrap')]/input"
                                                )
        for criteria in f_criteria:
            if criteria.is_displayed():
                criteria.send_keys(filter_term)
                break

    @WebAction(delay=1)
    def __click_filter_button(self):
        """ Method to click on filter button """
        filter_buttons = self._driver.find_elements(By.XPATH,
                                                    "//button[@type='submit' and contains(text(),'Filter')]")
        for filter_button in filter_buttons:
            if filter_button.is_displayed():
                filter_button.click()
                break

    @WebAction()
    def __select_filter_checkbox(self, filter_term):
        """ Method to click on filter term """
        xpath = f"//li[contains(@class, 'k-item')]/label[@title='{filter_term}']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __click_clear_filter_button(self):
        """ Method to click on clear filter button """
        filter_buttons = self._driver.find_elements(By.XPATH,
                                                    "//button[@type='reset' and contains(text(),'Clear')]")
        for filter_button in filter_buttons:
            if filter_button.is_displayed():
                filter_button.click()
                break

    @WebAction()
    def __select_hidden_column(self, column_name):
        """ Method to click on the column to be displayed """
        self._driver.find_element(By.XPATH,
                                  f"//li[@role='menuitemcheckbox']/span[contains(text(), '{column_name}')]"
                                  ).click()

    @WebAction()
    def __read_paging_info(self):
        """read paging info"""
        return self._driver.find_element(By.XPATH,
                                         self._xp + "//span[contains(@class,'pager-info')]"
                                         ).text

    @WebAction()
    def __get_pagination_drop_downs(self):
        """Method returns all pagination drop down elements on page"""
        drop_downs = self._driver.find_elements(By.XPATH,
                                                "//span[@class='k-widget k-dropdown k-header']")
        return drop_downs

    @WebAction()
    def __get_pagination_drop_down_option_elements(self, pagination_value):
        """Method to get elements of all options of given pagination value"""
        elements = self._driver.find_elements(By.XPATH,
                                              f"//ul[@data-role='staticlist']//li[text()='{pagination_value}']")
        return elements

    @WebAction()
    def __click_expand_row(self, row_text):
        """click expand icon near rows"""
        self._driver.find_element(By.XPATH,
                                  self._xp + f"//*[text()='{row_text}']/ancestor::tr//a[@class='k-icon k-i-expand']"
                                  ).click()

    @WebAction()
    def __select_all_rows(self):
        """Selects all rows"""
        xp = "//th[contains(@id,'checkbox')] |" \
             "//th[contains(@id,'active_cell') and @class='k-header']"
        self._driver.find_element(By.XPATH, xp).click()

    @WebAction()
    def __fetch_all_column_names(self):
        """Method to get all column names"""
        column_names = self._driver.find_elements(By.XPATH, "//li[@role='menuitemcheckbox']/span")
        return column_names

    @WebAction()
    def __scroll_to_element(self, element):
        """Scrolls to element position"""
        self._driver.execute_script("arguments[0].scrollIntoView();", element)

    @WebAction()
    def __scroll_reset(self):
        """Scrolls back to top left default position"""
        self._admin_console.scroll_into_view(self._xp + "//th[@role='columnheader'][1]")

    @WebAction()
    def click_cell_text(self, row_entity, column_name, span_class="", span_id=""):
        """
        Clicks text inside table cell given by row and column
        
        Args:
            row_entity  (str)   -   any string to identify row from
            column_name  (str)  -   name of column of cell
            span_class  (str)   -   class the span element inside cell belongs To
            span_id (str)       -   id of the span element inside cell
        """
        column_list = self.__get_column_names()
        col_idx = column_list.index(column_name) + 1
        row_xp = f"//*[text()='{row_entity}']/ancestor::tr"
        cell_xp = f"//td[@role='gridcell' and not(contains(@id,':checkbox')) " \
                  f"and not(@style='display:none')][{col_idx}]/span"
        class_constraint = f"@class='{span_class}'" if span_class else ""
        id_constraint = f"@id='{span_id}'" if span_id else ""
        if span_class or span_id:
            cell_xp += f'[{class_constraint}{" and " if span_class and span_id else ""}{id_constraint}]'
        cell = self._driver.find_element(By.XPATH, self._xp + row_xp + cell_xp)
        cell.click()

    @WebAction()
    def click_title(self):
        """Clicks static element, i.e, title (for collapsing menus and popups)"""
        title = self._driver.find_element(By.XPATH, "//div[@class='cv-k-grid-title']/h2")
        self._driver.execute_script("arguments[0].click();", title)

    @PageService()
    def get_all_column_names(self):
        """Gets all column names"""
        columns = self.__get_column_names()
        self.__expand_column_filter(columns[0])
        self.__click_columns_menu_item()
        name_elements = self.__fetch_all_column_names()
        self.__expand_column_filter(columns[0])
        return [name_elem.text for name_elem in name_elements]

    @PageService()
    def view_by_title(self, value, label=None):
        """
        Filter by type in grid

        Args:
            value   (str):   title to select
        """
        self.__click_title_dropdown(label)
        self.__filter_by_type(value)
        self._admin_console.wait_for_completion()

    @PageService()
    def search_for(self, value):
        """
        Clears the search bar and fills in the user given value

        Args:
            value (str)  -- the value to be searched
        """

        self.__enter_search_term(value)
        self._admin_console.wait_for_completion()

    @PageService()
    def clear_search(self):
        """
        Clears the search bar and resets the search to default
        """
        self.__clear_search_box()

    @PageService()
    def get_number_of_columns(self):
        """
        gets number of columns present in table
        """
        return len(self.__get_column_names())

    @PageService()
    def get_visible_column_names(self):
        """Get visible Column names"""
        return self.__get_column_names()

    @PageService()
    def get_column_data(self, column_name, fetch_all=False):
        """
        Get column data
        Args:
            column_name: Column Name
            fetch_all: Fetch all the data across multiple pages
        Returns:
            list of column data
        """
        if not fetch_all:
            column_list = self.__get_column_names()
            if column_list:
                col_idx = column_list.index(column_name) + 1
                return self.__get_data_from_column_by_idx(col_idx)

            return []
        else:
            data = []
            while True:
                column_list = self.__get_column_names()
                if column_list:
                    col_idx = column_list.index(column_name) + 1
                    data = data + self.__get_data_from_column_by_idx(col_idx)

                if self.has_next_page():
                    self.__click_next_page()
                    self._admin_console.wait_for_completion()
                else:
                    break

            return data

    @PageService
    def get_grid_actions_list(self, name, group_by=False):
        """Gets visible grid actions
            Args:

                name        (str)       :   Search term to be applied on table
        """
        if self.__is_search_visible():
            self.search_for(name)
        self._admin_console.wait_for_completion()
        self.__click_actions_menu(name)
        self._admin_console.wait_for_completion()
        flatten_grid_list = []
        nested_grid_list = []
        group_list = []
        grid_actions_list = self.__get_grid_actions_list()
        grid_actions_list = [action.text for action in grid_actions_list]
        # close the action menu
        self.__click_actions_menu(name)
        if group_by:
            for action in grid_actions_list:
                if action == '':
                    nested_grid_list += [group_list]
                    group_list = []
                else:
                    group_list += [action]
            nested_grid_list += [group_list]
            return nested_grid_list
        else:
            for action in grid_actions_list:
                if action != '':
                    flatten_grid_list += [action]
            return flatten_grid_list

    @PageService()
    def access_action_item(self, entity_name, action_item, partial_selection=False, second_entity=None, search=True):
        """
        Selects the action item in table

        Args:
            entity_name (str): Entity against which action item has to be selected

            action_item (str): action item which has to be selected

            partial_selection (bool) : flag to determine if entity name should be
            selected in case of partial match or not

            second_entity (str): Additional entity against which action item has to be selected.
            This is useful when the same instance name exists across multiple clients.

            search (bool) : Set to false if search is not required

        Raises:
            Exception:
                if unable to click on Action item
                or if the action item is not visible

        """
        self._admin_console.unswitch_to_react_frame()
        if search:
            if self.__is_search_visible():
                self.search_for(entity_name)
        self._admin_console.scroll_into_view(self._xp)
        self.__click_actions_menu(entity_name, partial_selection, second_entity)
        self._admin_console.wait_for_completion()
        self.__click_action_item(action_item)
        self._admin_console.wait_for_completion()

    @PageService()
    def access_link(self, entity_name):
        """
        Access the hyperlink (eg. list page for companies, plans, users etc)

        Args:
            entity_name (str): Entity for which the details are to be accessed

        """
        if self.__is_search_visible():
            self.search_for(entity_name)
        self._admin_console.scroll_into_view(self._xp)
        self._admin_console.select_hyperlink(entity_name)

    @PageService()
    def access_link_by_column(self, entity_name, link_text):
        """
        search by entity_name and access by link_text

        Args:
            entity_name : name to search for in table
            link_text   : link text to click

        """
        if self.__is_search_visible():
            self.search_for(entity_name)
        self._admin_console.scroll_into_view(self._xp)
        self._admin_console.select_hyperlink(link_text)

    @PageService()
    def access_context_action_item(self, entity_name, action_item):
        """
        Selects the action item in table right click menu

        Args:
            entity_name (str): Entity against which action item has to be selected

            action_item (str): action item which has to be selected

        Raises:
            Exception:
                if unable to click on Action item
                or if the action item is not visible
        """
        if self.__is_search_visible():
            self.search_for(entity_name)
        self._admin_console.scroll_into_view(self._xp)
        self.__right_click_menu(entity_name)
        self._admin_console.wait_for_completion()
        self.__click_context_action_item(action_item)
        self._admin_console.wait_for_completion()

    @PageService()
    def access_toolbar_menu(self, menu_id):
        """
        Access tool bar menu in table
        Args:
            menu_id: value of attribute data-cv-menu-item-id in the menu
        """
        if not self.__is_tool_bar_action_visible(menu_id):
            self.__click_expand_tool_bar_menu()
        self.__click_tool_bar_menu(menu_id)
        self._admin_console.wait_for_completion()

    @PageService()
    def access_menu_from_dropdown(self, menu_id):
        """Alias for access_toolbar_menu
        Args:
            menu_id: value of attribute data-cv-menu-item-id in the menu
        """
        self.access_toolbar_menu(menu_id)

    @PageService()
    def select_rows(self, names):
        """
        Select rows which contains names
        Args:
            names                  (List)       --    string to be selected which are hyperlinks
        """
        self._admin_console.scroll_into_view(self._xp)
        for each_name in names:
            self.__select_row(each_name, deselect=False)

    @PageService()
    def deselect_rows(self, names):
        """
        Deselect rows which contains names
        Args:
            names                  (List)       --    string to be selected which are hyperlinks
        """
        self._admin_console.scroll_into_view(self._xp)
        for each_name in names:
            self.__select_row(each_name, deselect=True)

    @PageService()
    def select_all_rows(self):
        """
        Select all the rows present
        """
        self.__select_all_rows()

    def __access_filter_menu(self, column_name):
        self._admin_console.scroll_into_view(self._xp)
        self.__expand_column_filter(column_name)
        self.__click_filter_menu_item()

    @PageService()
    def apply_filter_over_integer_column(self, column_name, filter_term):
        """
        Method to apply filter on integer type column (ex: jobid in Jobs page)

        Args:
            column_name (str) : Column to be applied filter on

            filter_term (str) : value to be filtered with
        """
        self.__access_filter_menu(column_name)
        self.__clear_integer_filter_criteria_textbox()
        self.__clear_filter_criteria_textbox()
        self.__enter_filter_criteria(filter_term, integer_type=True)
        self.__click_filter_button()
        self._admin_console.wait_for_completion()

    @PageService()
    def apply_filter_over_column(self, column_name, filter_term):
        """
        Method to apply filter on given column

        Args:
            column_name (str) : Column to be applied filter on

            filter_term (str) : value to be filtered with
        """
        self.__access_filter_menu(column_name)
        self.__clear_filter_criteria_textbox()
        self.__enter_filter_criteria(filter_term)
        self.__click_filter_button()
        self._admin_console.wait_for_completion()

    @PageService()
    def apply_filter_over_column_selection(self, column_name, filter_term):
        """
        Method to apply filter on a list in given column

        Args:
            column_name (str) : Column to be applied filter on

            filter_term (str) : value to be filtered with
        """
        self.__access_filter_menu(column_name)
        self.__enter_multi_filter_criteria(filter_term)
        self.__select_filter_checkbox(filter_term)
        self.__click_filter_button()
        self.__click_filter_button()
        self._admin_console.wait_for_completion()

    @PageService()
    def apply_sort_over_column(self, column_name, ascending=True):
        """
        Method to apply a sort on the column name specified
        Args:
            column_name (str): The column to apply sort on
            ascending  (bool): Whether the sort is ascending or not
        """
        self._admin_console.scroll_into_view(self._xp)
        self.__expand_column_filter(column_name)
        self.__click_sort_item(ascending)

    @PageService()
    def display_hidden_column(self, column_name):
        """
        Method to display hidden/non-default column
        Args:
            column_name (str/list):  The column/columns to be displayed
        """
        if isinstance(column_name, str):
            column_name = [column_name]
        self._admin_console.scroll_into_view(self._xp)
        columns = self.__get_column_names()
        self.__expand_column_filter(columns[0])
        self.__hover_columns_menu_item()
        for column in column_name:
            if column not in columns:
                self.__select_hidden_column(column)
        self.__expand_column_filter(columns[0])
        self._admin_console.wait_for_completion()

    @PageService()
    def clear_column_filter(self, column_name):
        """
        Method to clear filter from column

        Args:
            column_name (str) : Column name, filter to be removed from
        """
        self._admin_console.scroll_into_view(self._xp)
        self.__expand_column_filter(column_name)
        self.__hover_filter_menu_item()
        self.__click_clear_filter_button()
        self._admin_console.wait_for_completion()

    @PageService()
    def get_table_data(self):
        """Dump all data in the table as json"""
        columns = self.__get_column_names()
        return {
            columns[i]: self.__get_data_from_column_by_idx(i + 1)
            for i in range(len(columns))
        }

    @PageService()
    def is_entity_present_in_column(self, column_name, entity_name):
        """
        Check entity present
        Args:
            column_name (str) : Column Name to be searched in
            entity_name (str) : Name of entity to be checked

        """
        if self.__is_search_visible():
            self.search_for(entity_name)
        self._admin_console.scroll_into_view(self._xp)
        list_of_entities = self.get_column_data(column_name)
        if entity_name in list_of_entities:
            return True
        return False

    @PageService()
    def get_total_rows_count(self, search_keyword=None):
        """get total rows count"""
        if search_keyword:
            if self.__is_search_visible():
                self.search_for(search_keyword)
        page_txt = self.__read_paging_info()
        if page_txt:
            if page_txt == 'No items to display':
                return 0
            return page_txt.split()[-2]
        else:
            return len(self.__get_data_from_column_by_idx(1))

    @PageService()
    def set_pagination(self, pagination_value):
        """ Method to set pagination """

        drop_downs = self.__get_pagination_drop_downs()
        for dd in drop_downs:
            if dd.is_displayed():
                self._admin_console.scroll_into_view(
                    "//span[@class='k-widget k-dropdown k-header']"
                )
                ActionChains(self._driver).move_to_element(dd).click().perform()
        sleep(15)
        elements = self.__get_pagination_drop_down_option_elements(pagination_value)
        for elem in elements:
            if elem.is_displayed():
                ActionChains(self._driver).move_to_element(elem).click().perform()

    @PageService()
    def expand_row(self, row_text):
        """
        expands rows
        Args:
            row_text: text exist on row where expand has to be clicked
        """
        self.__click_expand_row(row_text)
        self._admin_console.wait_for_completion()

    @PageService()
    def hover_click_actions_sub_menu(self, entity_name, mouse_move_over_id, mouse_click_id, partial_selection=False):
        """Clicks the actions menu, hover to the element1 and clicks the element2 for an entity

                Args:
                    entity_name (str)  --  Entity name whose action menu is to be clicked

                    mouse_move_over_id (xpath) -- mouse move over element id

                    mouse_click_id (xpath)    -- mouse click element id

                    partial_selection  (bool)  --  Whether partial selection to be honored

        """
        self.__click_actions_menu(entity_name, partial_selection)
        self._admin_console.wait_for_completion()
        mouse_move_over = self._driver.find_element(By.ID, mouse_move_over_id)
        mouse_click = self._driver.find_element(By.ID, mouse_click_id)
        self._admin_console.mouseover_and_click(mouse_move_over, mouse_click)

    @WebAction()
    def __click_next_page(self):
        """Clicks on next page button"""
        elements = self._driver.find_elements(By.XPATH,
                                              "//a[not(contains(@class, 'k-disabled')) and contains(@title, 'Go to the next page')]")
        for elem in elements:
            if elem.is_displayed():
                elem.click()

    @WebAction()
    def has_next_page(self):
        """checks if table has next page icon"""
        if self._admin_console.check_if_entity_exists("xpath", "//*[not(contains(@class, 'k-state-disabled')) "
                                                               "and contains(@title, 'Go to the next page')]"):
            return self._driver.find_element(By.XPATH, "//*[not(contains(@class, 'k-state-disabled')) "
                                                       "and contains(@title, 'Go to the next page')]").is_displayed()

        return False

    @PageService()
    def context_menu_sequential_select(self, entity_name, elements: list):
        """Opens the context menu on the filtered enitity and clicks on the elements in the list sequentially

                Args:
                    entity_name (str)  --  Entity name to open context menu

                    elements  (list)  --  List of element names for sequential selection

        """
        self._admin_console.scroll_into_view(self._xp)
        self.__right_click_menu(entity_name)
        self._admin_console.wait_for_completion()
        for element in elements:
            self.__mouse_over_and_click(element)
        self._admin_console.wait_for_completion()

    @WebAction(delay=1)
    def click_action_menu(self, entity_name, partial_selection=False):
        """Clicks on Actions menu"""
        self.__click_actions_menu(entity_name, partial_selection)


class CVTable:
    """Older Table Component used in Command Center"""

    def __init__(self, admin_console):
        self.__driver = admin_console.driver
        self.__admin_console = admin_console

    @WebAction()
    def __click_entity(self, entity_name=None, row_index=None):
        """Clicks the given entity"""
        if entity_name is not None:
            link = self.__driver.find_element(By.XPATH, f"//cv-grid//a[text()='{entity_name}']")
            link.click()
        elif row_index is not None:
            link = self.__driver.find_element(By.XPATH, f"//div[contains(@class, 'ui-grid-row')][{row_index + 1}]//a")
            link.click()
        else:
            raise CVWebAutomationException("No entity_name or row_index provided. At least one is required")

    @WebAction()
    def __is_search_visible(self):
        """Returns True if the search is visible, False, if not"""
        search_xpath = "//cv-grid//input[@type='search']"
        if not self.__admin_console.check_if_entity_exists("xpath", search_xpath):
            return False
        return self.__driver.find_element(By.XPATH, search_xpath).is_displayed()

    @WebAction()
    def __set_search_string(self, keyword):
        """Clears the search box and sets with the given string"""
        search_box = self.__driver.find_element(By.XPATH, "//cv-grid//input[@type='search']")
        search_box.click()
        search_box.clear()
        search_box.send_keys(keyword)

    @WebAction()
    def __click_actions_button(self, entity_name=None, row_index=None):
        """Clicks the action button"""
        if entity_name is not None:
            button = self.__driver.find_element(By.XPATH,
                                                f"//cv-grid//*[text()='{entity_name}']/../following-sibling::div//*[name() = 'svg']")
            button.click()
        elif row_index is not None:
            button = self.__driver.find_element(By.XPATH, f"//div[contains(@class, 'ui-grid-row')][{row_index + 1}]"
                                                          f"//div[contains(@class, 'cv-permitted-actions')]")
            button.click()
        else:
            raise CVWebAutomationException("No entity_name or row_index provided. At least one is required")

    @WebAction()
    def __click_action(self, entity_name=None, action_item=None, row_index=None):
        """Clicks the given action item"""
        if not action_item:
            raise CVWebAutomationException("No action item provided")
        if entity_name is not None:
            option = self.__driver.find_element(By.XPATH,
                                                f"//cv-grid//*[text()='{entity_name}']/../following-sibling::div"
                                                f"//a[contains(text(),'{action_item}')]")
            option.click()
        elif row_index is not None:
            option = self.__driver.find_element(By.XPATH, f"//div[contains(@class, 'ui-grid-row')][{row_index + 1}]"
                                                          f"//div[contains(@class, 'cv-permitted-actions')]"
                                                          f"//a[contains(text(),'{action_item}')]")
            option.click()
        else:
            raise CVWebAutomationException("No entity_name or row_index provided. At least one is required")

    @PageService()
    def search_for(self, keyword):
        """performs the search with the given keyword on the table

        Args:
            keyword (str)  -- the value to be searched

        """
        if keyword is not None and self.__is_search_visible():
            self.__set_search_string(keyword)
            self.__admin_console.wait_for_completion()

    @PageService()
    def access_action_item(self, entity_name=None, action_item=None, row_index=None):
        """Selects the action item in the table action menu

        Args:
            entity_name (str)       : Entity against which action item has to be selected
            action_item (str)       : action item which has to be selected
            row_index (int)         : The index of the row to perform action on
        """
        if not action_item:
            raise CVWebAutomationException("No action item provided")
        self.search_for(entity_name)
        self.__click_actions_button(entity_name, row_index)
        self.__click_action(entity_name, action_item, row_index)
        self.__admin_console.wait_for_completion()

    @PageService()
    def access_link(self, entity_name=None, row_index=None):
        """Navigates to the given entity

        Args:
            entity_name (str): Entity which has to be accessed
            row_index (int)         : The index of the row to access link on
        """
        self.search_for(entity_name)
        self.__click_entity(entity_name, row_index)
        self.__admin_console.wait_for_completion()

    @WebAction(delay=0)
    def __get_index(self, entity_name):
        """
        Method to get index out of displayed user

        Args:
            entity_name (str) : value to get index for from table structure
        """
        index = 0
        selected = []
        element_list = self.__driver.find_elements(By.XPATH,
                                                   "//div[contains(@class,'ui-grid-render-container-body')]"
                                                   "//div[contains(@class,'ui-grid-row ng-scope')]")
        for element in element_list:
            if self.__admin_console.is_element_present(".//div[1]/span", element):
                if entity_name == element.find_element(By.XPATH, ".//div[1]/span").text:
                    selected.append(entity_name)
                    break
            else:
                if entity_name == element.find_element(By.XPATH, ".//div[1]/div").text:
                    selected.append(entity_name)
                    break
            index += 1
        return index, selected

    @WebAction()
    def __is_checked(self, index):
        """
        Method to check if the intended checkbox is checked

        Args:
            index (int) : index of the checkbox
        """
        chkbox_xp = "//div[@class='left ui-grid-render-container-left " \
                    "ui-grid-render-container']/div[2]"
        checkboxes = self.__driver.find_elements(By.XPATH,
                                                 chkbox_xp + "//div[@role='checkbox']")
        if 'ui-grid-row-selected' in checkboxes[index].get_attribute('class'):
            return True
        return False

    @WebAction()
    def __select_checkbox(self, index):
        """ select checkbox using index given """
        xp = "//td[contains(@id,'checkbox')]"
        if not self.__admin_console.check_if_entity_exists("xpath", xp):
            xp = "//div[@class='ui-grid-cell-contents']"
        checkboxes = self.__driver.find_elements(By.XPATH, xp)
        checkboxes[index].click()

    @WebAction()
    def __is_header_checked(self):
        """ Method to get checkbox state """
        header = self.__admin_console.driver.find_element(By.XPATH,
                                                          "//div[@class='left ui-grid-render-container-left "
                                                          "ui-grid-render-container']/div[1]")
        status = False
        if 'ui-grid-all-selected' in header.find_element(By.XPATH,
                                                         ".//div[@role='checkbox']").get_attribute("class"):
            status = True
        return status

    @WebAction(delay=0)
    def __select_header_checkbox(self):
        """ Method to click on checkbox to select/deselect """
        header = self.__admin_console.driver.find_element(By.XPATH,
                                                          "//div[@class='left ui-grid-render-container-left "
                                                          "ui-grid-render-container']/div[1]")
        header.find_element(By.XPATH, ".//div[@role='checkbox']").click()

    @WebAction(delay=0)
    def __get_column_names(self):
        """
        Read Column Names
        Returns: List of column names

        """
        path_selector = self.__admin_console.driver.find_element(By.XPATH,
                                                                 "//div[contains(@class,'ui-grid-render-container-body')]"
                                                                 "//div[contains(@class,'ui-grid-header ng-scope')]"
                                                                 )
        header_list = path_selector.text.split('\n')
        return header_list

    @WebAction(delay=0)
    def get_table_data(self):
        """
        Gets the table data
        Args:
        Returns:
            list of row data
        """
        column_names = self.__get_column_names()
        row_xpath = "//div[contains(@class, 'ui-grid-row')]"
        cell_xpath = ".//div[contains(@class, 'ui-grid-cell')]"
        rows = self.__driver.find_elements(By.XPATH, row_xpath)
        rows_data = []
        for row in rows:
            cells = {column: cell.text for column, cell in zip(column_names, row.find_elements(By.XPATH, cell_xpath))}
            rows_data.append(cells)
        return rows_data

    @WebAction(delay=0)
    def __get_data_from_column_by_idx(self, col_index):
        """
        Get Column Data for given column index
        Args:
            col_index: index of Table Column

        Returns: list of column data

        """
        col_path = f"//div[contains(@class,'ui-grid-render-container-body')]\
            //div[contains(@class,'ui-grid-row ng-scope')]/div[1]/div[{col_index}]"
        return [
            column.text for column in self.__admin_console.driver.find_elements(By.XPATH, col_path)
            if column.is_displayed()
        ]

    @WebAction()
    def __next_button_enabled(self):
        """ Method to check if button to next page is enabled """
        return self.__admin_console.driver.find_element(By.XPATH,
                                                        "//button[@ng-disabled='cantPageForward()']").is_enabled()

    @WebAction()
    def __click_next_button(self):
        """ Method to click next button on table"""
        self.__admin_console.driver.find_element(By.XPATH,
                                                 "//button[@ng-disabled='cantPageForward()']").click()

    @PageService()
    def get_column_data(self, column_name, data_from_all_pages=False):
        """
        Get Respective Column Data
        Args:
            column_name             (str):  Name of Column in Table
            data_from_all_pages     (bool): True if data is to be read from all
                                            pages of the table

        Returns: List of elements in required column

        """
        column_list = self.__get_column_names()
        if column_list and column_name in column_list:
            col_idx = column_list.index(column_name) + 1
            if not data_from_all_pages:
                return self.__get_data_from_column_by_idx(col_idx)
            else:
                content = self.__get_data_from_column_by_idx(col_idx)
                while True:
                    if self.__next_button_enabled():
                        self.__click_next_button()
                        self.__admin_console.wait_for_completion()
                        content.extend(self.__get_data_from_column_by_idx(col_idx))
                    else:
                        break
                return content
        else:
            return []

    @PageService()
    def select_checkbox(self, index):
        """ Public Method to select user by checking corresponding checkbox using index given """
        self.__select_checkbox(index)

    @PageService()
    def get_values_from_table(self, list_of_entities):
        """
        Method to get values from a table using the entity name
        Args:
            list_of_entities: List of entities for the given row(s)
        Returns:
            list with values from table: [<row>({<column-name>, <value>})]
            eg: [{"column1": "value1", "column2": "value2"},
            {"column1": "value3", "column2": "value4"}]
        """
        table = []
        column_values = {column: self.get_column_data(column) for column in self.__get_column_names()}
        for entity_name in list_of_entities:
            entity_name = entity_name.strip()
            index, _ = self.__get_index(entity_name)
            row = {column: value[index] for column, value in column_values.items()}
            table.append(row)
        return table

    @PageService()
    def filter_values_from_table(self, filter_dict):
        """
        Method to filter values from the table using the filters provided
        Args:
            filter_dict (dict): A dictionary of column_name:column_value pairs
        Returns:
            list with values from table: [<row>({<column-name>, <value>})]
            eg: [{"column1": "value1", "column2": "value2"},
            {"column1": "value3", "column2": "value4"}]
        """
        rows = self.get_table_data()
        filtered_rows = []
        row_indices = []
        for index, row in enumerate(rows):
            for column, value in filter_dict.items():
                if row[column] != value:
                    break
            else:
                row_indices.append(index)
                filtered_rows.append(row)
        return filtered_rows, row_indices

    @PageService()
    def select_values_from_table(self, list_of_entities):
        """
        Method to select values from a table

        Args:
            list_of_entities (list)  :  list of entities to be added

        Returns:
            None
        """

        entity_list = []
        selected = []
        for entity_name in list_of_entities:
            entity_list.append(entity_name.strip())

        for entity_name in entity_list:
            self.search_for(entity_name)
            index, selected_entity = self.__get_index(entity_name)
            selected.extend(selected_entity)
            if not self.__is_checked(index):
                self.__select_checkbox(index + 1)

        x_list = list(set(entity_list) - set(selected))
        if x_list:
            raise Exception(
                "Some entities could not be selected/not present in table" + str(x_list))

    @PageService()
    def select_all_values_from_table(self):
        """ Method to select all values from table """
        if not self.__is_header_checked():
            self.__select_header_checkbox()

    @PageService()
    def de_select_all_values_from_table(self):
        """ Method to de-select all values from table """
        if not self.__is_header_checked():
            self.__select_header_checkbox()
            self.__select_header_checkbox()
        else:
            self.__select_header_checkbox()


class Rfilter(enum.Enum):
    """Enum for selecting criteria filter on column"""
    contains = 'Contains'
    not_contains = 'Does not contain'
    equals = 'Equals'
    not_equals = 'Does not equal'
    is_empty = 'Is empty'
    greater_than = 'Greater than'
    less_than = 'Less than'
    #  between = 'Between'


class Rtable():
    """React Table Component used in Command Center"""

    def __init__(self, admin_console, title=None, id=None, xpath=None):
        """ Initalize the React table object

                Args:

                    admin_console       (obj)       --  Admin console class object

                    title               (str)       --  Title of React table

                    id                  (str)       --  Table ID attribute value

                    xpath               (str)       --  Xpath of React Table

        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._xpath = "//div[contains(@class,'grid-holder')]"
        if title:
            modified_xpath = self._xpath.replace("//", "::")
            self._xpath = f"//*[@class='grid-title' and text()='{title}']/ancestor{modified_xpath}"
        if id:
            self._xpath = f"//div[contains(@id,'{id}')]"
        if xpath:
            self._xpath = xpath
        self._rdrop_down = RDropDown(admin_console)
        from .dialog import RModalDialog
        self._views_dialog = RModalDialog(admin_console, title='Manage views')
        self._create_view_dialog = RModalDialog(admin_console, title='Create view')
        self._delete_view_dialog = RModalDialog(admin_console, title='Delete view')

    @WebAction()
    def __wait_for_grid_load(self):
        """Wait for grid load"""
        waiter = WebDriverWait(self._driver, 60, poll_frequency=2)
        waiter.until_not(
            ec.presence_of_element_located(
                        (By.XPATH, f"{self._xpath}//div[contains(@class, 'grid-loading')] | //div[contains(@class, 'grid-loading')]"))
        )

    @WebAction()
    def __select_row_by_index(self, index):
        """Select row by index on React Table
            Args:
                index       (int)   : index of the row
        """
        row_xpath = f"{self._xpath}//tr[contains(@class,'k-master-row')][{index}]/td/input"
        row = self._driver.find_element(By.XPATH, row_xpath)
        row.click()

    @WebAction()
    def __expand_grid(self):
        """
        expand the grid if it is collapsed
        """
        table_element = self._driver.find_element(By.XPATH, self._xpath)
        attributes = table_element.get_attribute('class')
        if 'grid-collapsed' in attributes:
            table_element.find_element(By.XPATH, ".//button[@aria-label='Expand grid']").click()

    @WebAction()
    def __click_table_columns(self):
        """Method to click columns button on top of react table"""
        columns_xpath = f"//button[contains(@aria-label,'Columns')]"
        columns_element = self._driver.find_element(By.XPATH, columns_xpath)
        columns_element.click()
        sleep(2)

    @WebAction()
    def __apply_sort_order_on_column(self, column_name, sort_order):
        """Method to sort column on react table

            Args:

                column_name         (str)       --  Column name

                sort_order          (str)       --  Sort orderas string (ascending or descending)

            Raises:

                Exception:

                    if sorting fails on column

        """
        column_xpath = f"//div[contains(@class,'header-cell')]/*//a/span[contains(text(),'{column_name}')]" \
                       f"/ancestor::div[contains(@class,'header-cell')]"
        sorting_xpath = f"//parent::th[contains(@aria-sort,'{sort_order}')]"
        sort_link_xpath = "//a"
        self._admin_console.scroll_into_view(column_xpath)
        col_header = self._driver.find_element(By.XPATH, column_xpath)
        self.__scroll_to_element(col_header)
        if not self._admin_console.check_if_entity_exists("xpath", f"{column_xpath}{sorting_xpath}"):
            column_element = self._driver.find_element(By.XPATH, f"{column_xpath}{sort_link_xpath}")
            column_element.click()
            sleep(3)
            if not self._admin_console.check_if_entity_exists("xpath", f"{column_xpath}{sorting_xpath}"):
                column_element = self._driver.find_element(By.XPATH, f"{column_xpath}{sort_link_xpath}")
                column_element.click()
                sleep(3)
        if not self._admin_console.check_if_entity_exists("xpath", f"{column_xpath}{sorting_xpath}"):
            raise Exception("Sorting not done properly")

    @WebAction()
    def __select_hidden_column(self, column_name):
        """ Method to click on the column to be displayed
            Args:
                column_name     (str)       :   Name of the column
        """
        column_label_xp = f"//div[contains(@class,'k-column-list')]//label[span[text()='{column_name}']]"
        checkbox = self._driver.find_element(By.XPATH, f"{column_label_xp}/span[contains(@class, 'checkbox')]")
        wait_condition = "contains(@class, 'Mui-checked')"
        if 'Mui-checked' in checkbox.get_attribute('class'):
            wait_condition = f"not({wait_condition})"
        self.__scroll_to_element(checkbox)
        checkbox.click()
        WebDriverWait(self._driver, 10).until(
            ec.presence_of_element_located((By.XPATH, f"{column_label_xp}/span[{wait_condition}]"))
        )

    @WebAction()
    def __click_menu_item(self, menu_item):
        """Method to click on any menu item
            Args:
                menu_item       (str)   :   Menu item's k-icon k-i- class value
        """
        menus = self._driver.find_elements(By.XPATH,
                                           "//div[contains(@class,'dropdown-menu show')]/div")
        for menu in menus:
            if menu.is_displayed():
                menu.find_element(By.XPATH, f"*//span[contains(@class,'k-icon k-i-{menu_item}')]").click()
                sleep(2)
                break

    @WebAction()
    def __get_column_index(self, column_name):
        """Gets column index directly by xpath"""
        column_name = column_name.split("\n")[0]
        col_xp = f"//*[text()='{column_name}']/ancestor::th[@role='columnheader' and not(@style='display:none')]"
        try:
            column = self._driver.find_element(By.XPATH, self._xpath + col_xp)
        except NoSuchElementException:
            return -1
        self.__scroll_to_element(column)
        return int(column.get_property("ariaColIndex"))

    @WebAction()
    def __get_column_names(self):
        """Read Column names from React Table"""
        self.__scroll_reset()  # scroll top left before reading columns
        col_xp = "//th[@role='columnheader' and not(@style='display:none')]"
        columns = self._driver.find_elements(By.XPATH, self._xpath + col_xp)
        column_names = []
        for column in columns:
            self.__scroll_to_element(column)
            if column.is_displayed():
                column_names.append(column.text.split('\n')[0])
        if column_names and column_names[0] == '':
            column_names.pop(0)
        self.__scroll_reset()
        return column_names

    @WebAction(delay=0)
    def __get_data_from_column_by_idx(self, col_idx):
        """Read data from column using column position index in React Table"""
        # scroll all the way top to read from first row
        self.__inner_scroll(0, -1)
        row_xp = f"//td[contains(@role,'gridcell') and not(input[contains(@class,'k-checkbox')]) " \
                 f"and not(@style='display:none')][{col_idx}]"
        data = []
        row_cells = self._driver.find_elements(By.XPATH, self._xpath + row_xp)
        for cell in row_cells:
            self.__scroll_to_element(cell)
            if cell.is_displayed():
                data.append(cell.text.strip())
        return data

    @WebAction(delay=0)
    def __is_search_visible(self):
        """check if search bar is available in React Table
            Args:
                None
            Returns:
                bool        - True if search button is visible in table
                              False if search button is not visible in table
        """
        if self.__expand_search():
            search_box = self._driver.find_elements(By.XPATH,
                                                    self._xpath + "//input[contains(@data-testid,'grid-search-input')]")
            return search_box and search_box[0].is_displayed()
        return False

    @WebAction(delay=0)
    def __expand_search(self):
        """clicks on search button on React Table"""
        search_xpath = f"{self._xpath}//button[contains(@class,'grid-search-btn')]"
        if self._admin_console.check_if_entity_exists("xpath", search_xpath):
            search_btn = self._driver.find_element(By.XPATH, search_xpath)
            search_btn.click()
            return True
        return True  # Looks like now all search bars are expanded by default

    @WebAction()
    def __read_paging_info(self):
        """read paging info on React Table footer"""
        page_info_xpath = f"{self._xpath}//div[contains(@class,'k-pager-info k-label')]"
        page_info_xpath2 = f"{self._xpath}//div[contains(@class, 'grid-count')]"
        # new table info shown next to three dots button
        if self._admin_console.check_if_entity_exists("xpath", page_info_xpath):
            footer_element = self._driver.find_element(By.XPATH, page_info_xpath)
            return footer_element.text
        if self._admin_console.check_if_entity_exists("xpath", page_info_xpath2):
            header_element = self._driver.find_element(By.XPATH, page_info_xpath2)
            # appending the string ' items' to keep consistent with the footer page info format
            return header_element.text + " items"
        return None

    @WebAction()
    def __select_all_rows(self):
        """Selects all rows on React Table"""
        if not self._admin_console.check_if_entity_exists(
                "xpath", f"//div[contains(@class,'grid-rows-selected')]/ancestor::div[contains(@class,'grid-holder')]"):
            all_rows_xpath = self._xpath + "//th//input[contains(@class,'k-checkbox')]"
            if self._admin_console.check_if_entity_exists("xpath", all_rows_xpath):
                self._driver.find_element(By.XPATH, all_rows_xpath).click()
                return
            raise NoSuchElementException("SelectAll rows option not found on this table")

    @WebAction()
    def __uncheck_all_selected(self):
        """Un-select all rows are selected"""
        try:
            checkbox_xpath = "//tbody/tr[contains(@class, 'k-selected')]//input"
            for checkbox in self._driver.find_elements(By.XPATH, self._xpath + checkbox_xpath):
                checkbox.click()
        except (NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException) as e:
            parent_row_xpath = '//table//thead//th//input[contains(@class,"k-checkbox")]'
            self._driver.find_element(By.XPATH, parent_row_xpath).click()

    @WebAction()
    def __clear_search_box(self):
        """clears text from search box"""
        cross = self._driver.find_elements(By.XPATH, self._xpath + "//button[contains(@class,'grid-search-clear')]")
        if cross and cross[0].is_displayed():
            cross[0].click()
            self._admin_console.wait_for_completion()
        else:
            search_box = self._driver.find_element(By.XPATH,
                                                   self._xpath + "//input[contains(@data-testid,'grid-search-input')]")
            search_box.send_keys(Keys.CONTROL + "a")
            search_box.send_keys(Keys.BACKSPACE)
            self._admin_console.wait_for_completion()

    @WebAction(delay=0)
    def __set_search_string(self, keyword):
        """Clears the search box and sets with the given string on React Table
            Args:
                keyword         (str)       :   Keyword to be searched on table
        """
        self.__clear_search_box()
        if self.__expand_search():
            search_box = self._driver.find_element(By.XPATH,
                                                   self._xpath + "//input[contains(@data-testid,'grid-search-input')]")
            search_box.clear()
            search_box.send_keys(keyword)

    @WebAction()
    def __wait_actions_menu(self, timeout=8):
        """
        Waits till actions menu is opened and items are loaded

        Args:
            timeout (int)   -   seconds to wait before throwing timeout error
        """
        WebDriverWait(self._driver, timeout).until(
            ec.presence_of_element_located((
                By.XPATH,
                "//div[contains(@class,'grid-row-actions-container')]//ul//li"
            ))
        )

    @WebAction(delay=1)
    def __click_actions_menu(self, entity_name=None, second_entity=None, row_index=None):
        """Clicks Action menu on React Table row
            Args:
                entity_name     (str)    :    Name of entity whose action menu has to be clicked

                second_entity   (str)   :     Name of the second entity to be matched.
                Example: This is useful when the same instance name exists across multiple clients.
                We can use server name as second entity in such cases.

                row_index       (int)   :     index of the row
                this can be helpful when you wanted to access row wise
        """
        row_path = "//div[contains(@class,'action-cell')]/div[contains(@data-testid,'row-action')]"
        if entity_name is not None:
            menu_xpath = f"//*[text() ='{entity_name}']/ancestor::tr[contains(@class,'k-master-row')]{row_path}"
        if second_entity is not None:
            menu_xpath = f"//*[text() ='{entity_name}']/ancestor::tr//*[text() ='{second_entity}']" \
                         f"/ancestor::tr{row_path}"
        if row_index is not None:
            menu_xpath = f"//tr[contains(@class,'k-master-row')]{row_path}"
            self._driver.find_elements(By.XPATH, self._xpath + menu_xpath)[row_index].click()
            sleep(3)
            return

        self.__inner_scroll(1, 0)  # scroll to right most
        sleep(2)
        for attempt in range(3):
            try:
                self._driver.find_element(By.XPATH, self._xpath + menu_xpath).click()
                self.__wait_actions_menu()
                return
            except (StaleElementReferenceException, TimeoutException) as exp:
                if attempt == 2:
                    raise exp

    @WebAction(delay=1)
    def __click_action_item(self, action_item):
        """Clicks on Action item under action menu on React Table row
            Args:
                action_item         (str)   :   action name to be clicked
        """
        elem = self._driver.find_element(By.XPATH,
                                         f"//div[contains(@class,'grid-row-actions-container')]/*//li[text() ='{action_item}']")
        elem.click()
        sleep(2)

    @WebAction(delay=1)
    def __click_action_item_inline(self, entity_name, action_item):
        """Clicks on action item present inline"""
        action_xpath = f"//div[contains(@class,'grid-holder')]//*[text() ='{entity_name}']/ancestor::tr" \
                       f"//button[@title= '{action_item}' or @aria-label='{action_item}']"
        elem = self._driver.find_element(By.XPATH, action_xpath)
        elem.click()
        sleep(2)

    @WebAction(delay=0)
    def __select_row(self, name, partial_selection=True):
        """Select specified row on React Table
            Args:
                name                (str)   : entity name which needs to be selected on table
                partial_selection   (bool)  : will match as substring if true
        """
        selector = [f"text()='{name}'", f"contains(text(), '{name}')"][partial_selection]
        row_xpath = f"{self._xpath}//*[{selector}]/ancestor::tr/td/input[contains(@type,'checkbox')]"
        rows = self._driver.find_elements(By.XPATH, row_xpath)
        if not rows:
            raise NoSuchElementException("Rows not found with name [%s]" % name)
        for each_row in rows:
            if not each_row.is_displayed():
                #  In case of multiple tables on same page we might face some issue
                continue
            hover = ActionChains(self._driver).move_to_element(each_row)
            hover.perform()
            self._admin_console.wait_for_completion()
            each_row.click()

    @WebAction()
    def __click_more_options_menu(self, label):
        """clicks on 'more' option menu of react table"""
        expanded_xpath = f"//div[contains(@class,'grid-row-actions-container')]/*//ul[contains(@class,'MuiMenu-list')]"
        if not self._admin_console.check_if_entity_exists("xpath", expanded_xpath):
            if label:
                menu_xpath = f"{self._xpath}//span[contains(@class,'action-item')]//button[*[text()='{label}']]/span"
            else:
                menu_xpath = f"{self._xpath}//span[contains(@class,'action-item')]//button/span"

            if self._admin_console.check_if_entity_exists("xpath", menu_xpath):
                self._admin_console.driver.find_element(By.XPATH, menu_xpath).click()
                sleep(3)

    @WebAction()
    def __click_tool_bar_menu(self, menu_id):
        """
        click tool bar menu in react table
        Args:
            menu_id: Name of menu attribute
        """
        menu_xpath = f"{self._xpath}//span[contains(@class,'action-item')]/button//*[contains(text(),'{menu_id}') or contains(@id,'{menu_id}')]"
        if self._admin_console.check_if_entity_exists("xpath", menu_xpath):
            menu_obj = self._driver.find_element(By.XPATH, menu_xpath)
            menu_obj.click()
        else:
            raise CVWebAutomationException("Action item Button [%s] element not found" % menu_id)

    @WebAction()
    def __expand_filter(self):
        """ Method to expand column filter from table"""
        col_settings_drop_down = self._driver.find_element(By.XPATH,
                                                           f"{self._xpath}//span[contains(@class,'MuiChip-label') and text()='Add filter']")
        col_settings_drop_down.click()
        sleep(4)

    @WebAction()
    def get_applied_pagination(self):
        """
        Gets the pagination currently active in table if any
        """
        pager_label_xpath = f"{self._xpath}//span[contains(@class, 'k-input-inner')]"
        pager_elems = self._driver.find_elements(By.XPATH, pager_label_xpath)
        if pager_elems:
            return pager_elems[0].get_attribute("innerText")

    @WebAction()
    def __get_pagination_drop_downs(self):
        """Method returns all pagination drop down elements on page"""
        pager_xpath = "//span[contains(@class,'k-pager')]/*/button[contains(@class,'k-button')]"
        self._admin_console.scroll_into_view(pager_xpath)
        self._driver.find_element(By.XPATH, pager_xpath).click()
        drop_downs = self._driver.find_elements(By.XPATH,
                                                "//span[@class='k-list-item-text']")
        return drop_downs

    @WebAction()
    def __get_pagination_drop_down_option_elements(self, pagination_value):
        """Method to get elements of all options of given pagination value"""
        elements = self._driver.find_elements(By.XPATH,
                                              f"//ul[@role='listbox']//*[text()='{pagination_value}']")
        return elements

    @WebAction()
    def __get_applied_filter_count(self):
        """Method to return number of filters applied on table

                Returns:

                    int     --  Number of filters applied already on table
        """
        filter_xpath = "//span[contains(@class,'MuiChip-label') and normalize-space()!='Add filter']"
        if self._admin_console.check_if_entity_exists("xpath", filter_xpath):
            filters = self._driver.find_elements(By.XPATH, filter_xpath)
            return len(filters)
        return 0

    @WebAction()
    def get_all_tabs(self):
        """Method to return all the available Tabs"""
        return [tab.text for tab in self._driver.find_elements(By.XPATH, f"//button[contains(@class,'MuiTab-root')]")]

    @WebAction()
    def __select_tab(self, tab_header):
        """Selects the tab header in react table"""
        tab_xpath = f"//*[contains(@class,'MuiTab-root') and text()='{tab_header}']"
        tab_elem = self._driver.find_element(By.XPATH, tab_xpath)
        if 'Mui-selected' not in tab_elem.get_attribute('class'):
            self.__scroll_to_element(tab_elem)
            tab_elem.click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def __get_applied_filter_position(self, column_name, filter_term):
        """Returns the applied filter position on that table filter

                Args:

                    column_name     (str)   :   Name of the column

                    filter_term:    (str)   :   Search Term to be applied

                Returns:

                    Int         --  filter position based on given inpt filter name
        """
        filter_xpath = "//span[contains(@class,'MuiChip-label') and text()!='Add filter']|//span[contains(@class,'MuiChip-label')]//span[text()!='Add filter']"
        index = 0
        if self._admin_console.check_if_entity_exists("xpath", filter_xpath):
            filters = self._driver.find_elements(By.XPATH, filter_xpath)
            for filter in filters:
                if column_name in filter.text:
                    if filter_term in filter.text:
                        break
                    elif filter_term == "Enabled" and "true" in filter.text:
                        break
                    elif filter_term == "Disabled" and "false" in filter.text:
                        break
                index = index + 1
            else:
                raise CVWebAutomationException(f'Filter not found! {column_name} :  {filter_term}')
        return index

    @WebAction()
    def __delete_applied_filter(self, index):
        """Removes the applied filter on the table

            Args:

                index       (int)       --  Filter position displayed on the table
        """
        filter_xpath = f"//*[name()='svg' and contains(@class, 'MuiChip-deleteIcon')]"
        if self._admin_console.check_if_entity_exists("xpath", filter_xpath):
            filters = self._driver.find_elements(By.XPATH, filter_xpath)
            filters[index].click()
            self._admin_console.wait_for_completion()

    @WebAction()
    def __click_add_rule(self):
        """Click on Add rule button to apply new filter"""
        add_rule_button = self._driver.find_element(By.XPATH,
                                                    "//*[contains(@class,'MuiButton-root')]//*[text()='Add rule']")
        add_rule_button.click()

    @WebAction()
    def __click_type(self, list_type):
        """Clicks to select the Type attrbute of table
            Args:
                list_type       (str)   -- Selects the Type in react table
        """
        xpath = f"//span[contains(@class,'MuiListItemText')]//span[text()='{list_type}']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __apply_filter(self):
        """Applies the filter on the table"""
        apply_element = self._driver.find_element(By.XPATH,
                                                  f"//*[contains(@class,'MuiButton-text')]//*[contains(text(),'Apply filters')]")
        try:
            apply_element.click()
        except ElementClickInterceptedException as exp:
            self._driver.execute_script("arguments[0].click();", apply_element)
        sleep(3)

    @WebAction()
    def __select_dropdown_value_in_filter(self, value):
        """Selects dropdown value in apply filters modal

            Args:

                value       (str)   --  Value to be selected in dropdown
        """
        dropdown_value_xpath = f"//span[contains(@class,'MuiListItemText') and text()='{value}']"
        search_xpath = "//input[contains(@class,'MuiInputBase-inputTypeSearch')]"
        if self._admin_console.check_if_entity_exists("xpath", search_xpath):
            search_element = self._driver.find_element(By.XPATH, search_xpath)
            search_element.send_keys(u'\ue009' + 'a' + u'\ue003') # CTRL + A + Backspace
            search_element.send_keys(value)
            sleep(2)
        if not self._admin_console.check_if_entity_exists("xpath", dropdown_value_xpath):
            dropdown_value_xpath = f"//div[contains(@class,'MuiListItemText')]//span[text()='{value}']"
        dropdown_value = self._driver.find_element(By.XPATH, dropdown_value_xpath)
        dropdown_value.click()

    @WebAction()
    def __get_filter_input_type(self, index):
        """Gets the type of the filter - dropdown, text, numeric or date"""
        filter_dropdown_id = self._driver.find_element(
            By.XPATH,
            f"//div[contains(@id, 'edit-view-modal-rule-{index}-filter-') and contains(@id, '-filterConditionDropdown')]"
        ).get_attribute("id")
        for each_type in ['text', 'numeric', 'date', 'dropdown']:
            if each_type in filter_dropdown_id:
                return each_type

    @WebAction()
    def __set_filter_column(self, column_name, index):
        """Sets the column to apply filter for"""
        column_dd_id = f"edit-view-modal-rule-{index}-column-dropdown"
        self._rdrop_down.select_drop_down_values(
            drop_down_id=column_dd_id,
            values=[column_name]
        )

    @WebAction()
    def __set_filter_criteria(self, criteria, index, input_type):
        """Sets the criteria for filter"""
        criteria_dd_id = f"edit-view-modal-rule-{index}-filter-{input_type}-filterConditionDropdown"
        self._rdrop_down.select_drop_down_values(
            drop_down_id=criteria_dd_id,
            values=[criteria.value]
        )

    @WebAction()
    def __set_filter_term(self, filter_term, index, input_type):
        """Sets the filter term in its appropriate inputs"""
        filter_input_id = f"edit-view-modal-rule-{index}-filter-{input_type}-filterInput"
        if input_type in ['dropdown']:
            if isinstance(filter_term, str):
                filter_term = [filter_term]
            self._rdrop_down.select_drop_down_values(
                drop_down_id=filter_input_id + '-multiselect',
                values=filter_term,
                case_insensitive_selection=True
            )
        # elif input_type in ['date']:
        # TODO: handle date type filter inputs
        else:
            self._admin_console.fill_form_by_id(filter_input_id, filter_term)
            static_elem = self._driver.find_element(By.XPATH, "//*[@class='mui-modal-title']")
            self._driver.execute_script('arguments[0].click();', static_elem)
            sleep(2)

    @WebAction()
    def __expand_column_filter(self, column_name):
        """ Method to expand column filter drop down
            Args:
                 column_name        (str)   :   column name where we need to expand filter menu
             **Column got moved to top of react table. Not changing method signature to support older code**
        """
        col_settings_drop_down = self._driver.find_element(By.XPATH,
                                                           f"//button[contains(@class,'grid-toolbar-columns')]")
        self._driver.execute_script("arguments[0].click();", col_settings_drop_down)
        sleep(2)

    @WebAction()
    def __fetch_all_column_names(self):
        """Method to get all column names"""
        column_names = self._driver.find_elements(By.XPATH, "//div[contains(@class,'k-column-list-item')]/*//label")
        names = []
        for column_element in column_names:
            names.append(column_element.text)
        # close the menu bar before returning names
        self._admin_console.click_button('Save')
        return names

    @WebAction()
    def __get_grid_actions_list(self):
        """Reads data from grid actions menu"""
        return self._driver.find_elements(By.XPATH,
                                          "//div[contains(@class,'grid-row-actions-container')]//li[contains(@role,'menuitem')]")

    @WebAction()
    def __click_title_dropdown(self, dropdown_id):
        """
        Clicks on title drop down on top of table
        """
        if dropdown_id:
            self._driver.find_element(By.XPATH, f"{self._xpath}//div[@id='{dropdown_id}']").click()
        else:
            self._driver.find_element(By.XPATH,
                                      f"{self._xpath}/*//div[contains(@class,'MuiSelect-selectMenu')]").click()
        sleep(2)

    @WebAction()
    def __click_reload_data(self):
        """
        Clicks on reload data on top of table
        """
        button_xpath = f"{self._xpath}/*//button[contains(@class, 'grid-toolbar-refresh')]"
        self._driver.find_element(By.XPATH, button_xpath).click()
        sleep(2)

    @WebAction()
    def __filter_by_type(self, title_to_filter):
        """
        select filter by type

        Args:
            title_to_filter   (str):   title to select

        """
        self.__select_dropdown_value_in_filter(value=title_to_filter)

    @WebAction()
    def __mouse_hover_click_for_actions(self, action_item, sub_action_item):
        """
        Moves mouse to Actions element and then clicks on sub menu element in it

            Args :

                action_item (str)   --  Action name which needs to be mouse hovered

                sub_action_item (str)   --  Sub-menu item name to click

        """
        menu_xpath = f"//div[contains(@class,'grid-row-actions-container')]/*" \
                     f"//li[text() ='{action_item}']/*[@data-testid='ArrowRightIcon']"
        sub_menu_xpath = f"//ul[@role='menu']/*/li[@role='menuitem' and text()='{sub_action_item}']"
        mouse_move_over = self._driver.find_element(By.XPATH, menu_xpath)
        self._admin_console.scroll_into_view(menu_xpath)
        self._driver.execute_script(
            "var evObj = document.createEvent('MouseEvents'); "
            "evObj.initMouseEvent(\"mouseover\",true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);"
            "arguments[0].dispatchEvent(evObj);", mouse_move_over)
        sleep(2)
        mouse_click = self._driver.find_element(By.XPATH, sub_menu_xpath)
        mouse_click.click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def __scroll_to_element(self, element):
        """Scrolls to element position"""
        self._driver.execute_script("arguments[0].scrollIntoView();", element)

    @WebAction()
    def __scroll_reset(self):
        """Scrolls back to top left default position"""
        self.__wait_for_grid_load()
        self.__inner_scroll()
        self._admin_console.scroll_into_view(self._xpath + "//th[@role='columnheader'][1]")

    @WebAction()
    def __inner_scroll(self, del_x: float = -1, del_y: float = -1):
        """
        Access inner scrollbar inside table

        Args:
            del_x   (float) -   percentage of scroll to perform in horizontal direction
                                positive value is towards right and negative towards left
            del_y   (float) -   percentage of scroll to perform in vertical direction
                                positive value is downward and negative value is upward
        """
        try:
            scroll_container = self._driver.find_element(
                By.XPATH,
                f"{self._xpath}//div[contains(@class, 'virtual-content') and @role='presentation']"
            )
            max_scroll_width = int(scroll_container.get_attribute('scrollWidth')) - \
                               int(scroll_container.get_attribute('clientWidth'))
            max_scroll_height = int(scroll_container.get_attribute('scrollHeight')) - \
                                int(scroll_container.get_attribute('clientHeight'))
            ActionChains(self._driver).scroll_from_origin(
                ScrollOrigin.from_element(scroll_container),
                int(max_scroll_width * del_x),
                int(max_scroll_height * del_y)
            ).perform()
        except:
            return

    @WebAction()
    def __type_input_for_index(self, index, input_value, input_type='text'):
        """Enter the given input_value to the input field with given type for given row
            Args:
                index       (int)   --  index of the row
                input_value (str)   --  string value to be entered in the input field
                input_type  (str)   --  input type for the given input value
        """
        self._driver.find_elements(By.XPATH, f"//input[@type='{input_type}']")[index].send_keys(input_value)

    @WebAction()
    def __click_forward_arrow_for_index(self, index):
        """Clicks on the forward arrow icon on the given index
            Args:
                index       (int)   --  index of the row
        """
        self._driver.find_elements(By.XPATH, "//*[@data-testid='ArrowForwardIcon']")[index].click()

    @WebAction()
    def __click_row_action(self, index, action):
        """Clicks the row action with the given action name for the given row
            Args:
                index       (int)   --  index of the row
                action      (str)   --  action name to be selected for the row
        """
        self._driver.find_elements(By.XPATH, f"//button[@aria-label='{action}']")[index].click()

    @WebAction()
    def __click_long_menu_button(self):
        """Method to click menu next to the columns button on top of react table"""
        menu_xpath = f"//button[contains(@id,'long-button')]"
        columns_element = self._driver.find_element(By.XPATH, menu_xpath)
        columns_element.click()
        sleep(2)

    @WebAction()
    def __click_on_menu_option(self, text):
        """Method to click on given menu text from sub menu"""
        menu_xpath = f"//li[contains(text(),'{text}')]"
        columns_element = self._driver.find_element(By.XPATH, menu_xpath)
        columns_element.click()
        sleep(2)

    @WebAction()
    def __click_cell_text(self, row_entity, column_name, xp=None):
        """
        Clicks text inside table cell given by row and column, and optionally using further xpath
        (To access help labels/callouts/embedded inputs when link text is not known)

        Args:
            row_entity  (str)   -   any string to identify row from
            column_name  (str)  -   name of column of cell
            xp  (str)           -   x-path string to click inside cell
        """
        column_list = self.__get_column_names()
        col_idx = column_list.index(column_name) + 1
        row_xp = f"//*[text()='{row_entity}']/ancestor::tr"
        cell_xp = f"//td[@role='gridcell' and not(contains(@id,':checkbox')) " \
                  f"and not(@style='display:none')][{col_idx}]"
        if xp:
            cell_xp += xp
        else:
            cell_xp += '//span'
        cell = self._driver.find_element(By.XPATH, self._xpath + row_xp + cell_xp)
        cell.click()

    @WebAction()
    def __click_link_by_column_title(self, column_name, link_text):
        """Method to click on given link within a column"""
        column_idx = self.__get_column_index(column_name)
        link_xpath = f"//tr/td[{column_idx}]//a[text() = '{link_text}']"
        self._driver.find_element(By.XPATH, link_xpath).click()

    @PageService()
    def type_input_for_row(self, index, input_value, input_type='text'):
        """Enter the given input_value to the input field with given type for given row
            Args:
                index       (int)   --  index of the row
                input_value (str)   --  string value to be entered in the input field
                input_type  (str)   --  input type for the given input value
            """
        self.__type_input_for_index(index, input_value, input_type)

    @PageService()
    def click_forward_arrow(self, index):
        """Clicks on the forward arrow icon on the given row
            Args:
                index       (int)   --  index of the row
        """
        self.__click_forward_arrow_for_index(index)

    @PageService()
    def select_row_action(self, index, action):
        """Clicks the row action with the given action name for the given row
            Args:
                index       (int)   --  index of the row
                action      (str)   --  action name to be selected for the row
        """
        self.__click_row_action(index, action)

    @PageService()
    def get_visible_column_names(self):
        """Get visible Column names from React Table"""
        self.__wait_for_grid_load()
        return self.__get_column_names()

    @PageService()
    def get_number_of_columns(self):
        """
        gets number of columns present in React Table
        """
        self.__wait_for_grid_load()
        return len(self.__get_column_names())

    @PageService()
    def get_column_data(self, column_name, fetch_all=False):
        """
        Get column data
        Args:
            column_name: Column Name
            fetch_all: Fetch all the data across multiple pages
        Returns:
            list of column data
        """
        self.__wait_for_grid_load()
        if not fetch_all:
            column_list = self.__get_column_names()
            if column_list:
                col_idx = column_list.index(column_name) + 1
                return self.__get_data_from_column_by_idx(col_idx)

            return []
        else:
            data = []
            column_list = self.__get_column_names()
            while True:
                if column_list:
                    col_idx = column_list.index(column_name) + 1
                    data = data + self.__get_data_from_column_by_idx(col_idx)
                if self.has_next_page():
                    self.__click_next_page()
                    self._admin_console.wait_for_completion()
                else:
                    break

            return data

    @PageService()
    def search_for(self, keyword):
        """performs the search with the given keyword on the React Table

        Args:
            keyword (str)  -- the value to be searched

        """
        self.__set_search_string(keyword)
        self._admin_console.wait_for_completion()

    @PageService()
    def clear_search(self):
        """Clears the search bar and resets to default"""
        self.__clear_search_box()

    @PageService()
    def access_link(self, entity_name):
        """
        Access the hyperlink in React Table

        Args:
            entity_name (str): Entity for which the details are to be accessed

        """
        self.__wait_for_grid_load()
        if self.__is_search_visible():
            self.__set_search_string(entity_name)
            self._admin_console.wait_for_completion()
            self.__wait_for_grid_load()
        self._admin_console.scroll_into_view(self._xpath)
        self._admin_console.select_hyperlink(entity_name)

    @PageService()
    def access_link_by_column(self, entity_name, link_text):
        """
        search by entity_name and access by link_text on React Table

        Args:
            entity_name : name to search for in table
            link_text   : link text to click

        """
        self.__wait_for_grid_load()
        if self.__is_search_visible():
            self.__set_search_string(entity_name)
            self._admin_console.wait_for_completion()
        self._admin_console.scroll_into_view(self._xpath)
        self._admin_console.select_hyperlink(link_text)

    @PageService()
    def access_link_without_text(self, entity_name, column_name, **options):
        """
        search by entity_name and access the link under given column

        Args:
            entity_name (str)   -   entity name to identify row
            column_name (str)   -   name of column to identify cell with link
            options:
                cell_xp (str)   -   x path inside cell to click
        """
        if self.__is_search_visible():
            self.__set_search_string(entity_name)
            self._admin_console.wait_for_completion()
        self._admin_console.scroll_into_view(self._xpath)
        self.__click_cell_text(entity_name, column_name, options.get('cell_xp'))
        self._admin_console.wait_for_completion()

    @PageService()
    def access_link_by_column_title(self, entity_name, column_title, link_text):
        """
                search by entity_name and access link_text under column_title  on React Table

                Args:
                    entity_name : name to search for in table
                    link_text   : link text to click
                    column_title: column title for the link
                """
        self.__wait_for_grid_load()
        if self.__is_search_visible():
            self.__set_search_string(entity_name)
            self._admin_console.wait_for_completion()
        self._admin_console.scroll_into_view(self._xpath)
        self.__click_link_by_column_title(column_title, link_text)

    @PageService()
    def get_table_data(self, all_pages=False):
        """Dump all data in the React Table as json

        Args:
            all_pages (bool) : will browse through all pages if true
        """
        self.__wait_for_grid_load()
        columns = self.__get_column_names()
        if not all_pages:
            return {
                columns[i]: self.__get_data_from_column_by_idx(i + 1)
                for i in range(len(columns))
            }
        else:
            data = dict((col, []) for col in columns)
            if self.has_first_page():
                self.__click_first_page()
                self.__wait_for_grid_load()
            while True:
                for i in range(len(columns)):
                    data[columns[i]].extend(self.__get_data_from_column_by_idx(i + 1))
                if not self.has_next_page():
                    return data
                self.__click_next_page()
                self.__wait_for_grid_load()

    @PageService()
    def is_entity_present_in_column(self, column_name, entity_name, search_for=True):
        """
        Check entity present in React Table
        Args:
            column_name (str) : Column Name to be searched in
            entity_name (str) : Name of entity to be checked
            search_for  (bool): searches on grid for entity_name if set

        """
        self.__wait_for_grid_load()
        if search_for and self.__is_search_visible():
            self.__set_search_string(entity_name)
            self._admin_console.wait_for_completion()
        self._admin_console.scroll_into_view(self._xpath)
        column_list = self.__get_column_names()
        if column_list:
            col_idx = column_list.index(column_name) + 1
            list_of_entities = self.__get_data_from_column_by_idx(col_idx)
            if entity_name in list_of_entities:
                return True
        return False

    @PageService()
    def get_total_rows_count(self, search_keyword=None):
        """get total rows count from React Table
            Args:
                search_keyword      (str)   :   keyword to be searched on table
        """
        self.__wait_for_grid_load()
        if search_keyword:
            if self.__is_search_visible():
                self.__set_search_string(search_keyword)
                self._admin_console.wait_for_completion()
        page_txt = self.__read_paging_info()
        if page_txt:
            return int(page_txt.split()[-2])
        return len(self.__get_data_from_column_by_idx(1))

    @PageService()
    def select_all_rows(self):
        """
        Select all the rows present in React Table
        """
        self.__wait_for_grid_load()
        self.__select_all_rows()

    @PageService()
    def unselect_all_rows(self):
        """
        Unselect all selected rows in table
        """
        self.__wait_for_grid_load()
        self.__uncheck_all_selected()

    @PageService()
    def select_rows(self, names, partial_selection=False, search_for=False):
        """
        Select rows which contains given names in React Table
        Args:
            names                  (List)       --    entity name whose row has to be selected
            partial_selection      (bool)       --    entity name will match as substring also if true
            search_for             (bool)       --    searches on grid search field if set
        """
        self.__wait_for_grid_load()
        self._admin_console.scroll_into_view(self._xpath)
        for each_name in names:
            if search_for:
                self.search_for(each_name)
            self.__select_row(each_name, partial_selection)

    @PageService()
    def expand_grid(self):
        """
        expand the grid if it is collapsed
        """
        self.__expand_grid()

    @PageService()
    def access_action_item(self, entity_name, action_item, second_entity=None, search=True):
        """
        Selects the action item in React Table

        Args:
            entity_name (str): Entity against which action item has to be selected

            action_item (str): action item which has to be selected

            second_entity (basestring): Additional entity against which action item has to be selected.
            This is useful when the same instance name exists across multiple clients.

            search (bool) : set to false if search is not required

        Raises:
            Exception:
                if unable to click on Action item
                or if the action item is not visible

        """
        self.__wait_for_grid_load()
        if search:
            if self.__is_search_visible():
                self.__set_search_string(entity_name)
                self._admin_console.wait_for_completion()
                sleep(8)
        self._admin_console.scroll_into_view(self._xpath)
        self.__click_actions_menu(entity_name, second_entity)
        self._admin_console.wait_for_completion()
        sleep(5)
        self.__click_action_item(action_item)
        self._admin_console.wait_for_completion()

    @PageService()
    def access_action_item_by_row_index(self, action_item, row_index=0):
        """
        perform action on the row based on row index
        Args:
            action_item: (str) action to be performed on the row
            row_index: (int) index of the row

        """
        self.__wait_for_grid_load()
        self._admin_console.scroll_into_view(self._xpath)
        self.__click_actions_menu(row_index=row_index)
        self._admin_console.wait_for_completion()
        sleep(5)
        self.__click_action_item(action_item)
        self._admin_console.wait_for_completion()

    @PageService()
    def access_action_item_inline(self, entity_name, action_item):
        """Access action item inline
        Args:
            entity_name: Entity against which action item has to be selected
            action_item: name of the action item
        """
        self._admin_console.scroll_into_view(self._xpath)
        self.__click_action_item_inline(entity_name, action_item)
        self._admin_console.wait_for_completion()

    @PageService()
    def access_toolbar_menu(self, menu_id, wait_for_completion=True):
        """
        Access tool bar menu in table
        Args:
            menu_id: Name of menu attribute
            wait_for_completion: Waits for completion
        """
        self.__wait_for_grid_load()
        self.__click_tool_bar_menu(menu_id)
        if wait_for_completion:
            self._admin_console.wait_for_completion()

    @PageService()
    def access_menu_from_dropdown(self, menu_id, label=None):
        """Access menu item from dropdown menu
        Args:
            menu_id: name of attribute in the menu
        """
        self.__wait_for_grid_load()
        self.__click_more_options_menu(label)
        menu_xpath = f"//li[contains(text(),'{menu_id}') and @role='menuitem']"
        menu_element = self._driver.find_element(By.XPATH, menu_xpath)
        menu_element.click()
        self._admin_console.wait_for_completion()

    @PageService()
    def apply_filter_over_column(self, column_name, filter_term, criteria=Rfilter.contains):
        """
        Method to apply filter on given column

        Args:
            column_name (str) : Column to be applied filter on

            filter_term (str/list) : value/values to be filtered with, can be empty for Rfilter.is_empty

            criteria    (enum) : Criteria to be applied over
                None                    -- Does not modify, leaves default criteria

                **Contains**            -- Column should contain this search term [Input Box]

                **Does not contain**    -- Column should not contain this search term [Input box]

                **Equals**              -- Column should match this term exactly. [Drop Down]

                **Greater than          -- Column should contain greater than this search term [Input box]

                **Less than             -- Column should contain less than this search term [Input box]

                **Not Equals**          -- Column should not match this term. [Drop Down]

                **Is empty              -- Column should be empty [Drop Down]
        """
        self.__wait_for_grid_load()
        # lets find whether any filter is applied already
        index = self.__get_applied_filter_count()
        self.__expand_filter()
        if index >= 1:
            # Add it as new rule
            self.__click_add_rule()

        self.__set_filter_column(column_name, index)
        input_type = self.__get_filter_input_type(index)
        if criteria:
            self.__set_filter_criteria(criteria, index, input_type)
        if filter_term:
            self.__set_filter_term(filter_term, index, input_type)
        self.__apply_filter()

    @PageService()
    def apply_filter_over_integer_column(self, column_name, filter_term, criteria=Rfilter.contains):
        """
        Method to apply filter on integer type column (ex: jobid in Jobs page)

        Args:
            column_name (str) : Column to be applied filter on

            filter_term (str) : value to be filtered with

            criteria    (enum) : Criteria to be applied over

                **Contains**    --  Column should contain this search term [Input Box]

                **Does not contain -- Column should not contain this search term [Input box]

                **Greater than -- Column should contain greater than this search term [Input box]

                **Less than -- Column should contain less than this search term [Input box]

        """
        self.__wait_for_grid_load()
        self.apply_filter_over_column(column_name, filter_term, criteria)

    @PageService()
    def apply_filter_over_column_selection(self, column_name, filter_term, criteria=Rfilter.contains):
        """
        Method to apply filter on a list in given column

        Args:
            column_name (str) : Column to be applied filter on

            filter_term (str) : value to be filtered with

            criteria    (enum) : Criteria to be applied over

                **Contains**    --  Column should contain this search term [Input Box]

                **Does not contain -- Column should not contain this search term [Input box]

                **Is empty -- Column should be empty [Input box]

        """
        self.__wait_for_grid_load()
        self.apply_filter_over_column(column_name, filter_term, criteria)

    @PageService()
    def clear_column_filter(self, column_name, filter_term):
        """
        Method to clear filter from column

        Args:

            column_name (str) : Column name filter to be removed from

            filter_term (str) : value given for the filter

        """
        self.__wait_for_grid_load()
        filter_index = self.__get_applied_filter_position(column_name=column_name, filter_term=filter_term)
        self.__delete_applied_filter(index=filter_index)

    @PageService()
    def display_hidden_column(self, column_name):
        """
        Method to display hidden/non-default column
        Args:
            column_name (str/list):  The column/columns to be displayed
        """
        if isinstance(column_name, str):
            column_name = [column_name]
        self._admin_console.scroll_into_view(self._xpath)
        self.__wait_for_grid_load()
        columns = self.__get_column_names()
        self.__click_table_columns()
        for column in column_name:
            if column not in columns:
                self.__select_hidden_column(column)
        self._admin_console.click_save(exact_word=True)

    @PageService()
    def apply_sort_over_column(self, column_name, ascending=True):
        """
        Method to apply a sort on the column name specified
        Args:
            column_name (str): The column to apply sort on
            ascending  (bool): Whether the sort is ascending or not
        """
        self.__wait_for_grid_load()
        self._admin_console.scroll_into_view(self._xpath)
        sort_order = "ascending" if ascending else "descending"
        self.__apply_sort_order_on_column(column_name=column_name, sort_order=sort_order)
        self._admin_console.wait_for_completion()

    @PageService()
    def select_row_by_index(self, index):
        """
        Select row by index
        Args:
            index: index of the row
        """
        self.__wait_for_grid_load()
        self.__select_row_by_index(index)

    @PageService()
    def get_all_column_names(self):
        """Gets all column names"""
        self.__wait_for_grid_load()
        columns = self.__get_column_names()
        self.__expand_column_filter(columns[0])
        self.__click_menu_item("columns")
        return self.__fetch_all_column_names()

    @PageService()
    def get_grid_actions_list(self, name, group_by=False):
        """Gets visible grid actions
            Args:
                name        (str)   :   Search term which needs to be applied on table

                group_by    (bool)  :   Specifies whether to do grouping or not on action item list
        """
        self.__wait_for_grid_load()
        if self.__is_search_visible():
            self.__set_search_string(name)
            self._admin_console.wait_for_completion()
        self.__click_actions_menu(name)
        self._admin_console.wait_for_completion()
        flatten_grid_list = []
        nested_grid_list = []
        group_list = []
        grid_actions_list = self.__get_grid_actions_list()
        grid_actions_list = [action.text for action in grid_actions_list]
        if group_by:
            for action in grid_actions_list:
                if action == '':
                    nested_grid_list += [group_list]
                    group_list = []
                else:
                    group_list += [action]
            nested_grid_list += [group_list]
            return nested_grid_list
        else:
            for action in grid_actions_list:
                if action != '':
                    flatten_grid_list += [action]
            return flatten_grid_list

    @PageService()
    def expand_row(self, row_text, toggle=True):
        """
        Expand/Collapse row in Table
        Args:
            row_text (str) : Text exist on row where expand has to be clicked
            toggle (bool) : Expand row when toggle is True
        """
        self.__wait_for_grid_load()
        expand_icon_xp = self._xpath + "//tbody//*[contains(@class,'MuiIconButton-root')]"
        sub_grid_xp = self._xpath + "//tbody//tr[contains(@class,'k-detail-row')]"
        click_toggle = False

        if self.__is_search_visible():
            self.__set_search_string(row_text)
            self._admin_console.wait_for_completion()
        self._admin_console.scroll_into_view(self._xpath)
        if self._admin_console.check_if_entity_exists('xpath', expand_icon_xp):
            if toggle:
                if not self._admin_console.check_if_entity_exists('xpath', sub_grid_xp):
                    click_toggle = True
            else:
                if self._admin_console.check_if_entity_exists('xpath', sub_grid_xp):
                    click_toggle = True
            if click_toggle:
                self._driver.find_element(By.XPATH, expand_icon_xp).click()
                self._admin_console.wait_for_completion()

    @PageService()
    def get_pagination_options(self):
        """
        Gets the pagination options available

        Returns:
            list[str]    -   list of options in pagination dropdown
        """
        all_items = self.__get_pagination_drop_downs()
        all_options = [item.text for item in all_items]
        self._admin_console.click_on_base_body()
        return all_options

    @PageService()
    def set_pagination(self, pagination_value):
        """ 
        Method to set pagination on React Table
        
        Args:
            pagination_value    (int/str)   -   pagination value to set
                                                'max' for maximum available value
                                                'min' for minimum available value
        """
        self.__wait_for_grid_load()
        # Click on pager to make element visible before selection of page size
        all_items = self.__get_pagination_drop_downs()
        all_options = [item.text for item in all_items]
        sorted_options = sorted(
            int(option) for option in all_options if option != 'All'
        )
        if 'All' in all_options:
            sorted_options.append('All')

        if pagination_value == 'max':
            pagination_value = str(sorted_options[-1])
        elif pagination_value == 'min':
            pagination_value = str(sorted_options[0])

        elements = self.__get_pagination_drop_down_option_elements(pagination_value)
        for elem in elements:
            if elem.is_displayed():
                elem.click()

    @PageService()
    def access_context_action_item(self, entity_name, action_item):
        """
        Selects the action item in table right click menu

        Args:
            entity_name (str): Entity against which action item has to be selected

            action_item (str): action item which has to be selected

        Raises:
            Exception:
                if unable to click on Action item
                or if the action item is not visible
        """
        # To do
        pass

    @PageService()
    def view_by_title(self, value):
        """
        Filter by type in grid

        Args:
            value   (str):   title to select
        """
        self.__select_tab(tab_header=value)
        self.__wait_for_grid_load()
        self._admin_console.wait_for_completion()

    @PageService()
    def select_company(self, name):
        """selects the company name in the react table

            Args:

                name        (str)       --  Name of company needs to be selected

        """
        self.__wait_for_grid_load()
        self.__click_title_dropdown(dropdown_id='Company')
        self._admin_console.wait_for_completion()
        self.__filter_by_type(name)
        self._admin_console.wait_for_completion()

    @PageService()
    def set_default_filter(self, filter_id, filter_value):
        """selects the value from given filter in the react table

            Args:

                filter_id       (str)   --    Id of filter needs to be selected

                filter_value    (str)   --  Value in the filter needs to be selected

        """
        self.__wait_for_grid_load()
        self.__click_title_dropdown(dropdown_id=filter_id)
        self._admin_console.wait_for_completion()
        self.__filter_by_type(filter_value)
        self._admin_console.wait_for_completion()

    @PageService()
    def filter_type(self, list_type):
        """ Selects Type in react table
            Args:
                list_type        (str)      -- All or Infrastructure
        """
        self.__wait_for_grid_load()
        self.__click_title_dropdown(dropdown_id='Type')
        self._admin_console.wait_for_completion()
        self.__click_type(list_type)
        self._admin_console.wait_for_completion()

    @WebAction()
    def __access_page_button(self, title=None, text=None):
        """
        Util to access page button using its title or text
        
        Args:
            title   (str)   -   title of the button
            text    (str)   -   text of the button (if title is None)

        Returns:
            True if successfully clicked the button
            False if not found
        """
        page_button_xpath = f"{self._xpath}//div[@aria-roledescription='pager']" \
                            f"//a[not(contains(@class, 'k-disabled')) "
        if title:
            page_button_xpath += f"and contains(@title, '{title}') "
        if text:
            page_button_xpath += f"and text()='{text}'"
        page_button_xpath += "]"

        if self._admin_console.check_if_entity_exists("xpath", page_button_xpath):
            page_elem = self._driver.find_element(By.XPATH, page_button_xpath)
            self.__scroll_to_element(page_elem)
            if page_elem.is_displayed():
                page_elem.click()
                self._admin_console.wait_for_completion()
                return True
        return False

    @WebAction()
    def go_to_page(self, page_text):
        """
        Clicks on required page button if it is visible

        Args:
            page_text (int/str)   -   text of the page to access or one of below keywords
                                      Example: 1, 2, 'first', 'last', 'next', 'previous', '...'
        
        Returns:
            True    -   if successfully clicked the button
            False   -   if button could not be located
        """
        page_text = str(page_text).lower()
        if page_text in ['first', 'last', 'next', 'previous']:
            return self.__access_page_button(title=f"Go to the {page_text} page")
        return self.__access_page_button(text=page_text)

    @WebAction()
    def __click_next_page(self):
        """Clicks on next page button"""
        self.__access_page_button(title='Go to the next page')

    @WebAction()
    def __click_first_page(self):
        """Clicks on next page button"""
        self.__access_page_button(title='Go to the first page')

    @WebAction()
    def has_next_page(self):
        """checks if react table has next page icon"""
        return self._admin_console.check_if_entity_exists("xpath", "//*[not(contains(@class, 'k-disabled')) "
                                                                   "and contains(@title, 'Go to the next page')]")

    @WebAction()
    def has_first_page(self):
        """checks if react table has next page icon"""
        return self._admin_console.check_if_entity_exists("xpath", "//*[not(contains(@class, 'k-disabled')) "
                                                                   "and contains(@title, 'Go to the first page')]")

    @PageService()
    def reload_data(self):
        """Clicks on reload data in table actions"""
        self.__click_reload_data()
        self.__wait_for_grid_load()

    def hover_click_actions_sub_menu(self, entity_name, action_item, sub_action_item):
        """Clicks the actions menu, hover to the action item and clicks the action element in a sub-menu

                Args:
                    entity_name (str)  --  Entity name whose action menu is to be clicked

                    action_item (str)   --  Action name which needs to be mouse hovered

                    sub_action_item (str)   --  Sub-menu item name to click

        """
        self.__click_actions_menu(entity_name)
        self._admin_console.wait_for_completion()
        self.__mouse_hover_click_for_actions(action_item=action_item, sub_action_item=sub_action_item)

    @WebAction()
    def __click_views_gear_icon(self):
        """
        Clicks the manage views gear icon in rtable
        """
        xpath = f"//div[contains(@class, 'grid-views-bar')]//button[@aria-label='Manage views']"
        gear_button = self._driver.find_element(By.XPATH, self._xpath + xpath)
        self.__scroll_to_element(gear_button)
        gear_button.click()

    @WebAction()
    def __click_save_as_filter(self):
        """
        Clicks the save as filter options from filters
        """
        xpath = f"//div[contains(@class, 'grid-filters-bar')]//button[@aria-label='Save as view']"
        save_as_view_button = self._driver.find_element(By.XPATH, self._xpath + xpath)
        self.__scroll_to_element(save_as_view_button)
        save_as_view_button.click()

    @WebAction()
    def __get_views_list(self):
        """
        Returns list of view button elements in this grid
        """
        return self._driver.find_elements(
            By.XPATH, self._xpath + "//div[@role='tablist']/button"
        )

    @PageService()
    def list_views(self):
        """
        Returns list of visible views

        Returns:
            list    -   list of names of views under this grid
        """
        return [
            btn.text for btn in self.__get_views_list()
        ]

    @PageService()
    def currently_selected_view(self):
        """
        Returns the currently selected view
        """
        for btn in self.__get_views_list():
            if btn.get_attribute('aria-selected') == 'true':
                return btn.text

    @PageService()
    def create_view(self, view_name, rules=None, set_default=False):
        """
        Creates a new view for the table using given rules of from existing filter
        Args:
            view_name: Name of the view to be created
            rules: A dictionary of rules in the form of {<column-name>: <value>}
                    eg: {'Operation': 'Backup'}
                    rule conditions are left as default i.e. contains, equals..
                    if empty, will use 'save as view' feature from current filter
            set_default: Sets the view as default
        """
        if rules:
            self.__click_views_gear_icon()
            self._views_dialog.click_button_on_dialog("Create view")
            common_dialog = self._views_dialog
        else:
            self.__click_save_as_filter()
            common_dialog = self._create_view_dialog
        common_dialog.fill_input_by_xpath(view_name, "viewName")
        if set_default:
            common_dialog.checkbox.check(id="setAsDefaultView")
        else:
            common_dialog.checkbox.uncheck(id="setAsDefaultView")
        if rules:
            num_rules = len(rules)
            for rule_idx, rule_key in enumerate(rules):
                self.__set_filter_column(rule_key, rule_idx)
                input_type = self.__get_filter_input_type(rule_idx)
                self.__set_filter_term(rules[rule_key], rule_idx, input_type)
                if rule_idx < num_rules - 1:
                    # Click add rule only if rule is not the last
                    self._admin_console.click_button_using_text("Add rule")
            self._views_dialog.click_save_button()
        else:
            self._create_view_dialog.click_save_button()
        self._admin_console.wait_for_completion()
        self._admin_console.check_error_message()
        self._admin_console.wait_for_completion()

    @PageService()
    def edit_view(self, view_name, new_name, new_rules, set_default=False):
        """
        Edits a view for the table
        Args:
            view_name: Name of the view to edit
            new_name: New name for the view
            new_rules: A dictionary of rules in the form of {<column-name>: <value>}
                        eg: {'Operation': 'Backup'}
                        rule conditions are left as default i.e. contains, equals..
                        Existing rules will be cleared and replaced with these
            set_default: Sets the view as default
        """
        self.view_by_title(view_name)
        self.__click_views_gear_icon()
        self._views_dialog.click_button_on_dialog("Edit view")
        self._views_dialog.fill_input_by_xpath(new_name, "viewName")
        if set_default:
            self._views_dialog.checkbox.check(id="setAsDefaultView")
        else:
            self._views_dialog.checkbox.uncheck(id="setAsDefaultView")
        if new_rules:
            # clearing existing rules
            for _ in range(10):
                try:
                    self._views_dialog.click_button_on_dialog(aria_label='Delete')
                except IndexError:
                    break
            # adding new rules
            self._admin_console.click_button_using_text("Add rule")
            num_rules = len(new_rules)
            for rule_idx, rule_key in enumerate(new_rules):
                self.__set_filter_column(rule_key, rule_idx)
                input_type = self.__get_filter_input_type(rule_idx)
                self.__set_filter_term(new_rules[rule_key], rule_idx, input_type)
                if rule_idx < num_rules - 1:
                    # Click add rule only if rule is not the last
                    self._admin_console.click_button_using_text("Add rule")
        self._views_dialog.click_save_button()
        self._admin_console.wait_for_completion()
        self._admin_console.check_error_message()
        self._admin_console.wait_for_completion()

    @PageService()
    def select_view(self, view_name="All"):
        """
        Selects a view
        Args:
            view_name: Name of the view to select
        """
        self.view_by_title(view_name)

    @PageService()
    def delete_view(self, view_name):
        """
        Deletes a view
        Args:
            view_name: Name of the view to delete
        """
        self.__click_views_gear_icon()
        self._views_dialog.click_button_on_dialog("Delete view")
        self._rdrop_down.select_drop_down_values(drop_down_id="delete-view-modal-dropdown", values=[view_name])
        self._delete_view_dialog.click_button_on_dialog("Delete")

    @PageService()
    def delete_row(self, row_idx):
        """
        Clicks the 'X' icon on a particular row

        Args:
            row_idx (int): Index of the row to be deleted

        """
        self.__click_delete_icon(row_idx)
        self._admin_console.wait_for_completion()

    @PageService()
    def wait_column_values(self, entities, column, match_list, wait):
        """
        Waits for column values to match given strings under the rows given by entities
        Args:
            entities   (list): list of strict cell values whose corresponding rows will be monitored
            column      (str): column to check for value match
            match_list (list): list of values to match the column to
            wait        (int): maximum seconds to wait before timeout
        """
        col_idx = self.__get_column_index(column)

        WebDriverWait(self._driver, wait).until(
            ec.all_of(
                *[
                    ec.any_of(
                        *[
                            ec.text_to_be_present_in_element(
                                (By.XPATH, f"//*[text() ='{entity}']/ancestor::tr/td[{col_idx}]"), expected_text
                            ) for expected_text in match_list
                        ]
                    ) for entity in entities
                ]
            ),
            message=f"column {column} failed to match among {match_list} for rows given by {entities} "
                    f"within {wait} seconds "
        )

    @PageService()
    def wait_for_rows(self, entities, wait):
        """
        Waits for the rows given by entities to appear in table
        Args:
            entities   (list): list of strict cell values whose corresponding rows will be matched
            wait        (int): maximum seconds to wait before timeout
        """
        WebDriverWait(self._driver, wait).until(
            ec.all_of(
                *[
                    ec.visibility_of_element_located(
                        (By.XPATH, f"{self._xpath}//*[text() ='{entity}']/ancestor::tr")
                    ) for entity in entities
                ]
            ),
            message=f"rows given by {entities} failed to show up within {wait} seconds"
        )

    @PageService()
    def hide_selected_column_names(self, column_name):
        """Method to hide the given column
          Args:
            column_name (str/list):  The column/columns to be hidden from display
        """
        if isinstance(column_name, str):
            column_name = [column_name]
        self._admin_console.scroll_into_view(self._xpath)
        self.__wait_for_grid_load()
        columns = self.__get_column_names()
        self.__click_table_columns()
        for column in column_name:
            if column in columns:
                self.__select_hidden_column(column)
        self._admin_console.click_button('Save')

    @PageService()
    def click_grid_reset_button(self):
        """Method to click on reset button of the grid"""
        self._admin_console.scroll_into_view(self._xpath)
        self.__wait_for_grid_load()
        self.__click_table_columns()
        self._admin_console.click_button('Reset')

    @PageService()
    def click_reset_column_widths(self, text):
        """Method to click on reset column width option from menu next to grid columns on top of react table
          Args:
            text (str):  option text to be selected from menu items
        """
        self._admin_console.scroll_into_view(self._xpath)
        self.__wait_for_grid_load()
        self.__click_long_menu_button()
        self.__wait_for_grid_load()
        self.__click_on_menu_option(text)
        self._admin_console.wait_for_completion()

    @PageService()
    def setup_table(self, columns, search=None):
        """
        Wrapper Util to setup columns and search fields in table
        Args:
            columns (str/list)  -   column names to ensure visible, 'all' for all columns
            search  (str)       -   search to apply on table, if not given, will clear search
        """
        if search:
            self.search_for(search)
        else:
            self.clear_search() if self.__is_search_visible() else None
        if columns:
            if columns == 'all':
                columns = self.get_all_column_names()
            self.display_hidden_column(columns)
        self.click_reset_column_widths("Reset column widths")

    @PageService()
    def get_rows_data(self, columns=None, search=None, **kwargs):
        """
        Gets all data from table in OrderedDict format

        Args:
            columns (str/list)  -   hidden columns to include
                                    'all' for all columns
                                    [col1, col2...] for multiple columns
                                    default: No columns will not be modified
            search  (str)       -   keyword to search in table before fetching table data
                                    default: search will be cleared
            kwargs:
                pages   (int/str)   -   number of pages to read jobs data from
                                        'all' for all pages (max limit of 20)
                                        default: first page only
                id_column   (str)   -   column to use as key, will use row index default
        Returns:
            count       (int)               -   the total number of rows across all pages
            rows_data   (OrderedDict)       -   Ordered dict with key as the cell value corresponding
                                                to given id_column parameter, or row_index if not given.
                                                The value for each key in Ordered dict is a dict
                                                with {column: cell_value} for rest of the columns in 
                                                that row (order is preserved as top to bottom row)
        """
        self.setup_table(columns, search)

        id_col = kwargs.get('id_column')
        pages = kwargs.get('pages', 1)
        if pages == 'all':
            pages = 20  # limit max number of pages

        self.go_to_page('first')
        table_data = self.get_table_data()
        pages -= 1
        # loop to add other pages data if required
        while pages > 0 and self.go_to_page('next'):
            next_table_data = self.get_table_data()
            for column in table_data:
                table_data[column] += next_table_data[column]
            pages -= 1

        # convert column dicts to list of rows or OrderedDict
        rows_data = OrderedDict()
        if 'Actions' in table_data:
            del table_data['Actions']
        table_columns = list(table_data.keys())
        no_of_cols = len(table_data[table_columns[0]])
        for row_index in range(no_of_cols):
            id_key = table_data[id_col][row_index] if id_col else row_index
            rows_data[id_key] = {
                column: table_data[column][row_index]
                for column in table_columns
                if column != id_col
            }
        count = self.get_total_rows_count()
        return count, rows_data

    @PageService()
    def export_csv(self, columns=None, search=None, pages='all'):
        """
        Exports CSV from react table and returns filepaths

        Args:
            columns (list/str)  -   list of columns to make visible
                                    'all' for all columns
                                    default: columns will not be modified
            search  (str)       -   any search to apply if required
                                    default: search will be cleared
            pages   (int/str)   -   number of pages to download csv for
                                    'all' for all pages
                                    default: all pages

        Returns:
            files   (list)   -   list of file_path strings
        """
        # max pagination to cover maximum csv data per page
        try:
            self.set_pagination('max')
        except NoSuchElementException:
            pass

        self.setup_table(columns, search)

        if pages == 'all':
            pages = -1
        files = []
        self.go_to_page('first')
        self.click_reset_column_widths('Export CSV')
        latest_file = self._admin_console.browser.get_latest_downloaded_file()
        if latest_file:
            files.append(latest_file)
        while self.go_to_page('next') and len(files) != pages:
            self.click_reset_column_widths('Export CSV')
            latest_file = self._admin_console.browser.get_latest_downloaded_file()
            if latest_file:
                files.append(latest_file)
        return files

    def get_grid_stats(self):
        """Returns the stats under grid info component in job details page"""

        stats = {}
        xp = '//span[@class="kpi-category-label-wrapper"]/span[@class="kpi-category-count"]'

        values = self._driver.find_elements(By.XPATH, xp)

        headers = self._driver.find_elements(By.XPATH, xp + '//following-sibling::span')

        for i in range(len(headers)):
            stats[headers[i].text] = int(values[i].text)

        return stats

    @PageService()
    def reset_filters(self):
        """Method to reset all filters applied on the grid"""
        self.__clear_search_box()
        self.__select_tab('All')
        self.select_company('All')

        while self.__get_applied_filter_count():
            self.__delete_applied_filter(0)

    @WebAction(delay=1)
    def click_action_menu(self, entity_name):
        """
         Clicks on Actions menu of selected entity
         entity_name (str): Entity against which action item has to be selected
        """
        self.__click_actions_menu(entity_name)

    @WebAction()
    def __click_delete_icon(self, row_idx):
        """Clicks on delete icon on the row based on index"""
        self._driver.find_element(By.XPATH, f"{self._xpath}//tr[contains(@class, 'k-master-row') and "
                                            f"@aria-rowindex={row_idx + 1}]//td[last()]//div").click()


class RptTable(Rtable):
    """Automation module for react table found in report pages"""

    def __init__(self, admin_console, title=None, id=None):
        """ Initalize the React table object

                        Args:

                            admin_console       (obj)       --  Admin console class object

                            title               (str)       --  Title of React table

                            id                  (str)       --  Table ID attribute value

        """
        super().__init__(admin_console, title, id)

    @WebAction()
    def __wait_for_grid_load(self):
        """Wait for grid load"""
        waiter = WebDriverWait(self._driver, 60, poll_frequency=2)
        waiter.until_not(
            ec.presence_of_element_located(
                (By.XPATH, self._xpath + "//div[contains(@class, 'grid-loading')]"))
        )

    @WebAction(delay=1)
    def __click_action_item(self, action_item):
        """Clicks on Action item under action menu on React Table row
            Args:
                action_item         (str)   :   action name to be clicked
        """
        elem = self._driver.find_element(By.XPATH,
                                         f"//li[@role='menuitem']/div[text() ='{action_item}']")
        elem.click()
        sleep(2)

    @WebAction(delay=0)
    def __is_search_visible(self):
        """check if search bar is available in React Table
            Args:
                None
            Returns:
                bool        - True if search button is visible in table
                              False if search button is not visible in table
        """
        if self.__expand_search():
            search_box = self._driver.find_elements(By.XPATH,
                                                    self._xpath + "//input[contains(@data-testid,'grid-search-input')]")
            return search_box and search_box[0].is_displayed()
        return False

    @WebAction()
    def __clear_search_box(self):
        """clears text from search box"""
        cross = self._driver.find_elements(By.XPATH, self._xpath + "//button[contains(@class,'grid-search-clear')]")
        if cross and cross[0].is_displayed():
            cross[0].click()
            self._admin_console.wait_for_completion()

    @WebAction(delay=0)
    def __set_search_string(self, keyword):
        """Clears the search box and sets with the given string on React Table
            Args:
                keyword         (str)       :   Keyword to be searched on table
        """
        self.__clear_search_box()
        if self.__expand_search():
            search_box = self._driver.find_element(By.XPATH,
                                                   self._xpath + "//input[contains(@data-testid,'grid-search-input')]")
            search_box.clear()
            search_box.send_keys(keyword)

    @WebAction(delay=0)
    def __expand_search(self):
        """clicks on search button on React Table"""
        search_xpath = f"{self._xpath}//button[contains(@class,'grid-search-btn')]"
        if self._admin_console.check_if_entity_exists("xpath", search_xpath):
            search_btn = self._driver.find_element(By.XPATH, search_xpath)
            search_btn.click()
            return True
        return True  # Looks like now all search bars are expanded by default

    @WebAction(delay=1)
    def __click_actions_menu(self, entity_name=None, second_entity=None, row_index=None):
        """Clicks Action menu on React Table row
            Args:
                entity_name     (str)    :    Name of entity whose action menu has to be clicked

                second_entity   (str)   :     Name of the second entity to be matched.
                Example: This is useful when the same instance name exists across multiple clients.
                We can use server name as second entity in such cases.

                row_index       (int)   :     index of the row
                this can be helpful when you wanted to access row wise
        """
        row_path = "//div[contains(@class,'anchor-btn')]/descendant::div[contains(@role,'button')]"
        if entity_name is not None:
            menu_xpath = f"//*[text() ='{entity_name}']/ancestor::tr[contains(@class,'k-master-row')]{row_path}"
        if second_entity is not None:
            menu_xpath = f"//*[text() ='{entity_name}']/ancestor::tr//*[text() ='{second_entity}']" \
                         f"/ancestor::tr{row_path}"
        if row_index is not None:
            menu_xpath = f"//tr[contains(@class,'k-master-row')]{row_path}"
            self._driver.find_elements(By.XPATH, self._xpath + menu_xpath)[row_index].click()
            sleep(3)
            return
        self._driver.find_element(By.XPATH, self._xpath + menu_xpath).click()
        sleep(3)

    @WebAction(delay=0)
    def __is_search_visible(self):
        """check if search bar is available in React Table
            Args:
                None
            Returns:
                bool        - True if search button is visible in table
                              False if search button is not visible in table
        """
        if self.__expand_search():
            search_box = self._driver.find_elements(By.XPATH,
                                                    self._xpath + "//input[contains(@data-testid,'grid-search-input')]")
            return search_box and search_box[0].is_displayed()
        return False

    @PageService()
    def access_action_item(self, entity_name, action_item, second_entity=None, search=True):
        """
        Selects the action item in React Table

        Args:
            entity_name (str): Entity against which action item has to be selected

            action_item (str): action item which has to be selected

            second_entity (basestring): Additional entity against which action item has to be selected.
            This is useful when the same instance name exists across multiple clients.

            search (bool) : set to false if search is not required

        Raises:
            Exception:
                if unable to click on Action item
                or if the action item is not visible

        """
        self.__wait_for_grid_load()
        if search:
            if self.__is_search_visible():
                self.__set_search_string(entity_name)
                self._admin_console.wait_for_completion()
                sleep(8)
        self._admin_console.scroll_into_view(self._xpath)
        self.__click_actions_menu(entity_name, second_entity)
        self._admin_console.wait_for_completion()
        sleep(5)
        self.__click_action_item(action_item)
        self._admin_console.wait_for_completion()

class ContainerTable():
    """React Container Table Component used in Command Center"""

    def __init__(self, admin_console,xpath=None):
        """ Initalize the Container table object

                Args:

                    admin_console       (obj)       --  Admin console class object

                    xpath               (str)       --  Xpath of React Table

        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._xpath = "//div[contains(@class,'MuiTableContainer')]"

        if xpath:
            self._xpath=xpath

    @WebAction()
    def __get_column_name(self):
        """
        Get the column names from the Container table
        """
        column_name=[]
        for i in self._driver.find_elements(By.XPATH, self._xpath+"//th[contains(@class, 'MuiTableCell')]"):
            column_name.append(i.text)
        return column_name

    @WebAction()
    def __get_row_data(self):
        """
        Get the row values from the container table
        """
        row_data = []

        rows = self._driver.find_elements(By.XPATH, self._xpath + "//tr[contains(@class, 'MuiTableRow')]")

        for row in rows:
            cells = row.find_elements(By.XPATH, "./td[contains(@class, 'MuiTableCell')]")
            if cells:
                cell_values = [cell.text.strip() for cell in cells]
                row_data.append(cell_values)
        return row_data

    @PageService()
    def get_table_data(self):
        """
        Get data from container table

        Returns:
            dict with values from table: {<column-name>: [<value1>,<value2>,<value3>]}
            eg: {"column1": [value1,value2], "column2": [value1,value2]}
        """
        headers = self.__get_column_name()
        rows = self.__get_row_data()

        data = {col_name: [] for col_name in headers}
        for row in rows:
            for col_index, value in enumerate(row):
                if col_index < len(headers):
                    col_name = headers[col_index]
                    data[col_name].append(value)
        return data
