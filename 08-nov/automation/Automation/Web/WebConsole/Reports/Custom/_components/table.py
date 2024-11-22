from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""All the operations common to table and pivot component goes to this file."""
import re
from time import sleep

from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException

from Web.Common.page_object import (
    WebAction,
    PageService
)
from .column import (
    ColumnBuilder,
    ColumnViewer,
    ColumnProperties
)
from .button import (
    ButtonViewer,
    ButtonBuilder,
    ButtonProperties
)

from .base import CRComponentBuilder
from .base import CRComponentProperties
from .base import CRComponentViewer


class TableBuilder(CRComponentBuilder):
    """Actions common to Pivot and Table Builder go here"""


class TableViewer(CRComponentViewer):
    """Actions common to Pivot and  Data Table under webconsole goes here"""

    @WebAction()
    def __click_additional_columns(self):
        """Click Additional columns dropdown"""
        dropdown = self._driver.find_element(By.XPATH,
            self._x + "//button[@title='Add or remove columns']")
        dropdown.click()

    @WebAction()
    def __click_column_settings(self):
        """Click column settings"""
        try:
            visible_col_setting = [
                col for col in
                self._driver.find_elements(By.XPATH,
                    f"{self._x}//*[@title='Column Settings']"
                )
                if col.is_displayed()
            ][0]
            visible_col_setting.click()
        except IndexError:
            raise WebDriverException(
                f"Unable to click column settings. Element with XPath "
                f"[{self._x}//*[@title='Column Settings']] "
                f"does not exist."
            )

    @WebAction()
    def __get_pagination(self):
        """ get the number of pages in the table"""
        page_n = self._driver.find_element(By.XPATH,
            f"{self._x}//*[contains(@class,'k-pager-info')]"
        )
        return page_n.text

    @WebAction()
    def __click_inside_settings_menu(self, option):
        """Click option inside column settings"""
        xpath = f"//*[@data-role='menu']//*[contains(@class,'{option}')]"
        try:
            menu_option = [
                option for option in
                self._driver.find_elements(By.XPATH, xpath)
                if option.is_displayed()
            ][0]
            menu_option.click()
        except IndexError:
            raise WebDriverException(
                f"Unable to click column settings. Element with XPath "
                f"{xpath} does not exist."
            )

    @WebAction()
    def __click_column_on_additional_col_menu(self, column_name):
        """Click column on hidden column dropdown"""
        checkbox = self._driver.find_element(By.XPATH,
            self._x +
            f"//*[@role='menuitemcheckbox']/*[.='{column_name}']"
        )
        checkbox.click()

    @WebAction()
    def __click_row_select(self):
        """click on number of rows  """
        count_button = self._driver.find_element(By.XPATH,
            f"{self._x}//*[@*='k-select']"
        )
        count_button.click()

    @WebAction()
    def __select_rows(self, count):
        """Select number of rows to be displayed on table"""
        option = self._driver.find_element(By.XPATH,
            f"//*[@class='k-list-scroller']//li[.='{count}']"
        )
        option.click()

    @WebAction()
    def __click_table_gear(self):
        """Click the gear icon on the table"""
        menu = self._driver.find_element(By.XPATH, self._x + "//ul[@data-role='menu']")
        self._driver.execute_script("arguments[0].scrollIntoView();", menu)
        menu.click()
        sleep(3)

    @WebAction()
    def _is_table_gear_present(self):
        """Returns boolean if gear icon on the table"""
        menu = self._driver.find_element(By.XPATH, self._x + "//ul[@data-role='menu']")
        try:
            if menu.is_enabled() and menu.is_displayed():
                sleep(2)
                return True
            else:
                return False
        except:
            return False

    @WebAction()
    def __select_gear_menu_option(self, name):
        """Click on menu option of table"""
        button = self._driver.find_element(By.XPATH,
            f"{self._x}//*[contains(@class, '{name}')]"
        )
        button.click()

    @WebAction()
    def __set_filter(self, column_name, value):
        """Apply the filter to the corresponding column"""
        filter_field = self._driver.find_element(By.XPATH,
            f"{self._x}//*[@field-displayname='{column_name}']/input"
        )
        filter_field.clear()
        filter_field.send_keys(value)
        filter_field.send_keys(Keys.ENTER)

    @WebAction()
    def __fetch_table_title(self):
        """Fetches the table title"""
        title = self._driver.find_element(By.XPATH,
            f"{self._x}//div[@class='reportstabletitle panel-table-title']/span"
        )
        return title.text

    @WebAction()
    def __get_column_names(self):
        """Read all column names from table"""
        return [
            column.get_attribute("title") for column in
            self._driver.find_elements(By.XPATH,
                f"{self._x}//th[@role='columnheader']"
            )
            if column.is_displayed()
        ]

    @WebAction()
    def __get_row_count(self):
        """Get number of rows (including table header)"""
        pager_info = self._driver.find_element(By.XPATH, f"{self._x}//span[@class = 'k-pager-info k-label']").text
        if pager_info.split()[0] == 'No':
            return 0
        count = re.findall(r'of (\d+)', pager_info)
        return int(count[0])

    @WebAction(delay=0)
    def __get_rows_by_column_name(self, column_name):
        """Get all the rows inside the column"""
        return [
            cell.text for cell in self._driver.find_elements(By.XPATH,
                f"{self._x}//td[@data-label='{column_name}']"
            )
        ]

    @WebAction(delay=0)
    def __get_rows_by_column_idx(self, index):
        """Get all the rows inside the column using index"""
        return [
            cell.text for cell in self._driver.find_elements(By.XPATH, f"{self._x}//tbody/tr/td[{index}]")
        ]

    @WebAction(delay=0)
    def __get_attributed_cells_by_column_name(self, column_name):
        """Get style attributes of all cell values inside column"""
        return [
            {
                "bg_color": cell.value_of_css_property('background-color'),
                "font_color": cell.value_of_css_property('color'),
                "font_size": cell.value_of_css_property('font-size'),
                "data": cell.text
            }
            for cell in self._driver.find_elements(By.XPATH,
                f"{self._x}//td[@data-colid='{column_name}']"
            )
        ]

    @WebAction()
    def __is_filter_enabled(self):
        """ Check the filter is enabled by default or not"""
        element = self._driver.find_element(By.XPATH,
            f"{self._x}//tr[@class='k-filter-row']//th[not(@style='display: none;')]//input"
        )
        return element.is_displayed()

    @WebAction()
    def __access_action_menu(self, entity_name):
        """Clicks on the action menu
        Args:
            entity_name (str): table cell value in whose row action menu has to be clicked
        """
        self._driver.find_element(By.XPATH,
            f"//td[@title ='{entity_name}']/../td[@data-label='Actions']//button"
        ).click()

    @WebAction()
    def __click_action_menu_link(self, entity_name, Action_item):
        """
        clicks link on action menu
        entity_name (str): table cell value in whose row action menu has to be clicked
        Action_item (str): item to access in action menu
        """
        self._driver.find_element(By.XPATH,
            f"//td[@title ='{entity_name}']/../td[@data-label='Actions']"
            f"//a[@title='{Action_item}']"
        ).click()

    @WebAction()
    def __type_in_search(self, entity, search_id=None):
        """Types in the given entity to the search box"""
        xpath = self._x + '//../input[@type="search"]'
        if search_id:
            xpath = self._x + f'//../input[@type="search" and @id="{search_id}"]"'
        element = self._driver.find_element_by_xpath(xpath)
        element.clear()
        element.send_keys(entity)
        element.send_keys(Keys.ENTER)

    @WebAction()
    def __copy_rest_api_url(self):
        """Returns the REST API URL"""
        url = self._driver.find_element(By.TAG_NAME, 'code').text
        button = self._driver.find_element(By.XPATH,
            "//*[contains(@class,'rest-api-modal')]/descendant::*[text()='Close']"
        )
        button.click()
        return url

    @WebAction()
    def __get_all_columns(self):
        """
        get all the column from the additional columns
        Returns:
        """
        xpath = self._x + '//li[@role="menuitemcheckbox"]'
        return [
            column.text for column in self._driver.find_elements(By.XPATH, xpath)
        ]

    @WebAction()
    def get_all_hidden_columns(self):
        """
        get all the hidden columns from the table
        Returns:

        """
        xpath = "//*[@class='column-selector k-state-default ng-scope']"
        return [
            column.text for column in self._driver.find_elements(By.XPATH, xpath) if column.text != '']

    @WebAction()
    def __click_on_additional_columns(self):
        """
        click on additonal columns
                """
        xpath = f"{self._x}//*[@title='Columns']"
        self._driver.find_element(By.XPATH, xpath).click()

    @PageService()
    def get_pagination(self):
        """
        get the page count
        """
        if 'No items to display' in self.__get_pagination():
            return 0
        else:
            ful_text = self.__get_pagination().split()
            return int(ful_text[4])

    @PageService()
    def enable_all_columns(self):
        """
        enable all the columns
        Returns:
        """
        self.__click_table_gear()
        self.__click_on_additional_columns()
        hidden_columns = self.get_all_hidden_columns()
        for column in hidden_columns:
            self.__click_column_on_additional_col_menu(column)
        self.__click_table_gear()

    @PageService()
    def get_all_columns(self):
        """
        get all the columns form the table
        Returns:
        """
        self.__click_table_gear()
        self.__select_gear_menu_option("table-column-selector")
        columns = self.__get_all_columns()
        self.__click_table_gear()
        return columns

    @PageService()
    def get_row_count(self):
        """To get the number of rows in the table"""
        return self.__get_row_count()

    @PageService()
    def configure_alert(self):
        """Opens configure alert window"""
        self.__click_table_gear()
        self.__select_gear_menu_option("table-alarm")
        sleep(1)

    @PageService()
    def export_to_csv(self):
        """Export to CSV using the Table Level CSV export option"""
        self.__click_table_gear()
        self.__select_gear_menu_option("table-export-csv")
        self._webconsole.wait_till_load_complete()
        self.__click_table_gear()

    @PageService()
    def rest_api(self):
        """Copy Rest API"""
        self.__click_table_gear()
        self.__select_gear_menu_option("table-rest-api")
        self._webconsole.wait_till_load_complete()
        return self.__copy_rest_api_url()

    @PageService()
    def charts(self):
        """Convert table into chart"""
        self.__click_table_gear()
        self.__select_gear_menu_option("table-quick-chart")
        self._webconsole.wait_till_load_complete()


    @PageService()
    def toggle_column_visibility(self, column_name):
        """Enable hidden column"""
        self.__click_table_gear()
        self.__click_inside_settings_menu("table-column-selector")
        self.__click_column_on_additional_col_menu(column_name)
        self._webconsole.wait_till_load_complete()
        self.__click_table_gear()

    @PageService()
    def set_filter(self, column_name, filter_string):
        """Filter table data"""
        if not self.__is_filter_enabled():
            self.__click_table_gear()
            self.__select_gear_menu_option("table-show-filter")
            self.__click_table_gear()
        self.__set_filter(column_name, filter_string)
        self._webconsole.wait_till_load_complete()

    @PageService()
    def set_number_of_rows(self, number_of_results=50):
        """Set the number of rows to show on a table"""
        self.__click_row_select()
        self.__select_rows(number_of_results)
        self._webconsole.wait_till_load_complete()

    @PageService()
    def get_attributed_table_data(self):
        """Fetches the table data along with style information."""
        return {
            col: self.__get_attributed_cells_by_column_name(col)
            for col in self.__get_column_names()
        }

    @PageService()
    def get_table_data(self):
        """Dump all data in the table as json"""
        return {
            col: self.__get_rows_by_column_name(col)
            for col in self.__get_column_names()
        }

    @PageService()
    def get_exported_table_data(self):
        """Dump all data from exported file in the table as json"""
        columns = self.__get_column_names()
        return {
            columns[i]: self.__get_rows_by_column_idx(i + 1)
            for i in range(len(columns))
        }

    @PageService()
    def get_table_title(self):
        """Returns the table title"""
        return self.__fetch_table_title()

    @PageService()
    def expand_table(self):
        """ Expands table if needed"""
        gear_icon = self._is_table_gear_present()
        if not gear_icon:
            # Expand table
            expand_icon = self._driver.find_element(By.XPATH, self._x +"//*[contains(@class,'arrowPlaceholder')]")
            expand_icon.click()

    @PageService()
    def get_table_columns(self):
        """Get all visible column names"""
        return self.__get_column_names()

    @PageService()
    def get_column_data(self, column_name):
        """Get column data"""
        return self.__get_rows_by_column_name(column_name)

    def get_rows_from_table_data(self):
        """
        Get all the table data in a row-wise fashion
        NOTE:
        This is NOT a page service, always prefer self.get_table_data
        Returns: table date with list of list
        """
        table_data = self.get_table_data()
        return list(map(list, zip(*(table_data.values()))))

    def get_rows_from_exported_file_table_data(self):
        """
        Get all the table data in a row-wise fashion from the exported file
        Returns: table date with list of list
        """
        table_data = self.get_exported_table_data()
        return list(map(list, zip(*(table_data.values()))))

    @PageService()
    def access_action_item(self, entity_name, Action_item):
        """
        Access action item component in table
        Args:
            entity_name (str): table cell value in whose row action menu has to be clicked
            Action_item (str): item to access in action menu
        """
        self.__access_action_menu(entity_name)
        self.__click_action_menu_link(entity_name, Action_item)

    @PageService()
    def search_from_table(self, entity, search_id=None):
        """Searches the given entity through the table
        Args:
            entity      (str)   :   Entity text to be searched from table data
            search_id   (str)   :   Search Bar ID if multiple search bars are present
        """
        self.__type_in_search(entity, search_id=search_id)
        self._webconsole.wait_till_load_complete()


class PivotTableViewer(TableViewer):
    """Actions specific to Pivot Table under WebConsole goes here"""
    @property
    def type(self):
        """Returns:Category type as 'Table'"""
        return "PIVOT_TABLE"


class TableProperties(CRComponentProperties):
    """Actions common to Pivot and Table Properties panel go here"""

    @PageService()
    def set_cell_expression(self, script):
        """Sets cell expression

        Args:
            script (str)    : script which is to be entered

        """
        self._select_current_component()
        self._click_scripts_tab()
        self._click_add_expression()
        self._set_code_editor(script)
        self._click_save_on_code_editor()

    @PageService()
    def set_row_style(self, script):
        """Sets row style

        Args:
            script (str)    : script which is to be entered

        """
        self._select_current_component()
        self._click_scripts_tab()
        self._click_add_style()
        self._set_code_editor(script)
        self._click_save_on_code_editor()


class DataTableBuilder(TableBuilder):
    """This class contains all the builder actions specific to Data Table"""

    @property
    def category(self):
        """
        Returns:Category type as 'Table'
        """
        return "Table"

    @property
    def name(self):
        """
        Returns:Name as 'Data Table'
        """
        return "Data Table"

    @WebAction()
    def __drag_dataset_to_table(self):
        """Drag dataset to table"""
        self._drag_dataset_to_component(self._x + "//div[@id='table_%s']" % self.id)

    @WebAction()
    def __drag_column_to_table(self, column_name):
        """Drag column to table"""
        self._drag_column_from_dataset(column_name, self._x + "//div[@id='table_%s']" % self.id)

    @WebAction()
    def __click_add_button(self):
        """Clicks add button on the table"""
        button = self._driver.find_element(By.XPATH, self._x + "//button[@title='Add New Button']")
        button.click()

    @WebAction()
    def __get_button_id(self):
        """Retrieve component ID"""
        xpath = "//div[@class='buttonPanel hideOnExportFriendly ng-scope']//ul/li"
        elements = self._driver.find_elements(By.XPATH, self._x + xpath)
        button = elements[-2].find_element(By.XPATH, ".//button")
        return button.get_attribute('id').strip()

    @PageService()
    def add_column_from_dataset(self, column=None):
        """Add column from associated dataset to table

        Args:
            column (iterable): Any iterable of column name
        """
        if column:
            self._validate_dataset_column(self.dataset_name, column)
            self.__drag_column_to_table(column)
        else:
            self.__drag_dataset_to_table()
        self._webconsole.wait_till_line_load()

    @PageService()
    def add_column(self, column, drag_from_dataset=True):
        """Adds Column to the table

        Args:
            column (obj): Object of type column which is to be added.
            drag_from_dataset ( bool) : if set, only configure the component for column

        """
        if not isinstance(column, Column):
            raise TypeError("Invalid component type")

        if drag_from_dataset:
            self._select_current_component()
            self._select_current_component()
            self.__drag_column_to_table(column.title)
            self._webconsole.wait_till_line_load()
        xpath = self._x + "//th[@title='%s']" % column.title
        column.configure_builder_component(self._webconsole, self.dataset_name,
                                           self.page_name, column.title, xpath)

    @PageService()
    def add_button(self, button):
        """Adds Button to the table

        Args:
            button (obj): Object of type button which is to be added.

        """

        if not isinstance(button, Button):
            raise TypeError("Invalid component type")
        self.__click_add_button()
        id_ = self.__get_button_id()
        xpath = self._x + "//button[@id='%s']" % id_
        button.configure_builder_component(self._webconsole, self.dataset_name,
                                           self.page_name, id_, xpath)
        button.set_component_title(button.title)

    @PageService()
    def associate_column_in_builder(self, column):
        """Configures column object"""
        if not isinstance(column, Column):
            raise TypeError("Invalid component type")
        xpath = self._x + "//th[@title='%s']" % column.title
        column.configure_builder_component(self._webconsole, self.dataset_name,
                                           self.page_name, column.title, xpath)


class PivotTableBuilder(TableBuilder):
    """This class contains all the builder actions specific to Pivot Table"""
    @property
    def name(self):
        """
        Returns:Name as 'Pivot Table'
        """
        return "Pivot Table"

    @property
    def category(self):
        """
        Returns:Category type as 'Table'
        """
        return "Table"

    @WebAction()
    def __drag_column_to_pivot_row(self, column_name):
        """Drag column to pivot row"""
        self._drag_column_from_dataset(column_name, self._x + "//*[contains(text(),'Drop Pivot Row')]")

    @WebAction()
    def __drag_column_to_pivot_column(self, column_name):
        """Drag column to pivot column"""
        self._drag_column_from_dataset(column_name, self._x + "//*[contains(text(),'Drop Pivot Column')]")

    @PageService()
    def set_pivot_row(self, column):
        """Sets the pivot row for the pivot table

        Args:
            column (str): A valid column name
        """
        self._validate_dataset_column(self.dataset_name, column)
        self.__drag_column_to_pivot_row(column)
        self._webconsole.wait_till_line_load()

    @PageService()
    def set_pivot_column(self, column):
        """Sets the pivot row for the pivot table

        Args:
            column (str): A valid column name
        """
        self._validate_dataset_column(self.dataset_name, column)
        self.__drag_column_to_pivot_column(column)
        self._webconsole.wait_till_line_load()


class DataTableViewer(TableViewer):
    """This class contains all the viewer actions specific to Data Table"""

    @property
    def type(self):
        """Returns:Category type as 'Table'"""
        return "TABLE"

    @WebAction()
    def __select_row(self, row_no):
        """Selects the given row in the table"""
        row = self._driver.find_element(By.XPATH, self._x + f"//tr[{row_no}]//td[1]//input")
        self._browser.click_web_element(row)

    @PageService()
    def select_rows(self, rows):
        """Selects the given list of rows"

        Args:
            rows (list) : List of row numbers for which checkbox have to be selected.

        """
        list(map(self.__select_row, rows))

    @PageService()
    def select_row_by_value(self, column_name, row_value):
        """Select rows checkbox by specified column value"""
        row_data = self.get_column_data(column_name)
        for each_row_value in row_value:
            for row_number in range(len(row_data)):
                if each_row_value in row_data[row_number]:
                    self.__select_row(row_number + 1)

    def associate_button(self, button):
        if not isinstance(button, ButtonViewer):
            raise ValueError("invalid component type")
        button.configure_viewer_component(self._webconsole, page="Page0")
        button._set_x(None, self._x + f"//button[@id='{button.id}']")

    def associate_column(self, column):
        if not isinstance(column, ColumnViewer):
            raise ValueError("invalid component type")
        column.configure_viewer_component(self._webconsole, page="Page0")
        column.id = column.title
        column._set_x(None, self._x + "//th/span[@title='%s']" % column.title)


class DataTableProperties(TableProperties):
    """This class contains all the Properties panel actions specific to Data Table"""

    @WebAction()
    def __toggle_button_panel(self):
        """Toggles 'Enable Button panel'."""
        enable_button = self._driver.find_element(By.XPATH, "//*[@for='enableButtonPanel']")
        enable_button.click()

    @WebAction()
    def __toggle_row_selection(self):
        """Toggles 'Enable Row Selection'."""
        row_selection = self._driver.find_element(By.XPATH, "//*[@for='enableRowSelection']")
        row_selection.click()

    @WebAction()
    def __toggle_multiple_row_selection(self):
        """Toggles Enable Multiple Row Selection'."""
        multiple_row_selection = self._driver.find_element(By.XPATH, "//*[@for='enableMultiRowSelection']")
        multiple_row_selection.click()

    @PageService()
    def toggle_button_panel(self):
        """Toggles 'Enable Button panel'."""
        self._select_current_component()
        self.__toggle_button_panel()

    @PageService()
    def toggle_row_selection(self):
        """Toggles 'Enable Row Selection'."""
        self._select_current_component()
        self.__toggle_row_selection()

    @PageService()
    def toggle_multiple_row_selection(self):
        """Toggles Enable Multiple Row Selection'."""
        self._select_current_component()
        self.__toggle_multiple_row_selection()


class PreviewTable(DataTableViewer):

    def __init__(self):
        super().__init__("")

    def configure_viewer_component(self, webconsole, page=""):  # page is empty string for method
        self._webconsole = webconsole                           # signature compatibility with
        self._browser = webconsole.browser                      # base class
        self._driver = webconsole.browser.driver
        self.page_name = ""
        self._set_x(None, xp="//*[@id='PreviewTable']")


class Column(ColumnBuilder, ColumnViewer, ColumnProperties):
    """
    Dummy class to reference all the Column Operations inside a table
    available on the report Builder
    """


class Button(ButtonBuilder, ButtonViewer, ButtonProperties):
    """
    Dummy class to reference all the Button Operations inside a table
    available on the report Builder

    """


class ButtonInViewer(ButtonViewer):
    """
    Dummy class to expose all the private Button Viewer APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """


class ColumnInViewer(ColumnViewer):
    """Dummy class to expose all the private Column Viewer APIs as public

    For the builder and properties panel specific actions, refer builder.py file

    """


class MailTable:
    """This class contains actions specific to table present in mail body"""

    def __init__(self, driver, table_id):
        """To initialize MailTable class

        Args:
            driver      (obj)   -- browser driver object

            table_id    (str)   -- Comp ID of the table

        """
        self.driver = driver
        self.id = table_id.replace("component","table")
        self._x = "//*[@id='%s']" % self.id

    @WebAction()
    def __get_column_data(self, column_no):
        """
        Returns the row data

        Args:
             column_no     (str)   --  number of the column to be fetched

        Returns:
            (list)  -- column data

        """
        return [cell.text for cell in self.driver.find_elements(By.XPATH, f"{self._x}//tbody//tr//td[{column_no}]")]

    @WebAction()
    def __get_row_data(self, row_no):
        """
        Returns the row data

        Args:
             row_no     (str)   --  number of the row to be fetched

        Returns:
            (list)  -- row data

        """
        return [cell.text for cell in self.driver.find_elements(By.XPATH, f"{self._x}//tbody//tr[{row_no}]//td")]

    @WebAction()
    def __get_column_count(self):
        """To get the total number of columns present in the table

        Returns:
            (int)   -- Total number of columns present in the table

        """
        return len(self.driver.find_elements(By.XPATH, f"{self._x}//th"))

    @WebAction()
    def __get_row_count(self):
        """To get the total number of rows present in the table

        Returns:
            (int)   -- Total number of rows present in the table

        """
        return len(self.driver.find_elements(By.XPATH, f"{self._x}//tr"))

    @WebAction()
    def get_column_names(self):
        """To get the column names in the table

        Returns:
            (list)  -- table column names

        """
        return [column.text for column in self.driver.find_elements(By.XPATH, f"{self._x}//th")]

    @PageService()
    def get_data_table_columns(self):
        """To get the data present in the table as columns

        Returns:
            (list)  -- table columns

        """
        return [self.__get_column_data(column_no) for column_no in range(1, self.__get_column_count() + 1)]

    @PageService()
    def get_data_table_rows(self):
        """To get the data present in the table as rows

        Returns:
            (list)  -- table rows

        """
        return [self.__get_row_data(row_no) for row_no in range(1, self.__get_row_count() + 1)]

    @PageService()
    def get_table_data(self, row_limit=10):
        """To get the data present in the table

        Args:
            row_limit   (int)   -- To limit the number of rows picked
                                    default: 10

        Returns:
            (dict)  -- data of the table

        """
        column_names, column_data = self.get_column_names(), self.get_data_table_columns()
        return {column_names[no]: column_data[no][0:row_limit] for no in range(0, len(column_names))}
