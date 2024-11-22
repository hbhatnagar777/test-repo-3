import re
from abc import ABC

from selenium.common import NoSuchElementException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from .base import CRComponentViewer
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import WebAction, PageService

from .button import (
    ButtonViewer
)

from .column import (
     ColumnViewer
)


class TableViewer(CRComponentViewer, ABC):
    """Actions common to Pivot and  Data Table under adminconsole goes here"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @WebAction()
    def __click_show_hide_columns(self):
        """Click Show/hide columns dropdown"""
        dropdown = self._driver.find_element(By.XPATH, f"{self._x}//*[@aria-label='Show/hide columns']")
        dropdown.click()

    @WebAction()
    def __get_pagination(self):
        """ get the pagination text in the table"""
        try:
            page_n = self._driver.find_element(By.XPATH,
                                               f"{self._x}//*[contains(@class,'k-pager-info')]"
                                               )
            return page_n.text
        except NoSuchElementException:  # pagination not shown if only 1 page present
            return ""

    @WebAction()
    def __click_column_on_additional_col_menu(self, column_name):
        """Click column on show/hide column dropdown"""
        checkbox = self._driver.find_element(By.XPATH,
                                             f"{self._x}//*[contains(@class,'k-column-list-item')]"
                                             f"//*[text()='{column_name}']")
        checkbox.click()

    @WebAction()
    def __click_rows_per_page_dropdown(self):
        """click on number of rows per page"""
        count_button = self._driver.find_element(By.XPATH,
                                                 f"{self._x}//*[contains(@class, 'k-pager-sizes')]//button"
                                                 )
        count_button.click()

    @WebAction()
    def __select_pagination_row_count(self, count):
        """Select number of rows to be displayed per page on table"""
        option = self._driver.find_element(By.XPATH,
                                           f"//*[contains(@class, 'k-list-item-text') and text()='{count}']"
                                           )
        option.click()

    @WebAction()
    def __click_more_actions(self):
        """clicks more actions"""
        menu = self._driver.find_element(By.XPATH, f"{self._x}//button[@id='long-button']")
        menu.click()

    @WebAction()
    def __select_more_action(self, text):
        """selects action from more actions"""
        xp = f"//*[@id='long-menu']//*[text()='{text}']"
        self._driver.find_element(By.XPATH, xp).click()

    @WebAction()
    def __click_table_gear(self):
        """Click the gear icon on the table"""
        menu = self._driver.find_element(By.XPATH,
                                         f"{self._x}//*[contains(@class, 'action-item')]/button")
        self._driver.execute_script("arguments[0].scrollIntoView();", menu)
        self._driver.execute_script("arguments[0].click();", menu)

    @WebAction()
    def _is_table_gear_present(self):
        """Returns boolean if gear icon on the table"""
        try:
            menu = self._driver.find_element(By.XPATH,
                                             f"{self._x}//*[contains(@class, 'row-actions')]"
                                             f"//*[contains(@class, 'action-item')]")
            if menu.is_enabled() and menu.is_displayed():
                return True
            else:
                return False
        except:
            return False

    @WebAction()
    def __set_filter(self, column_name, value):
        """Apply the filter to the corresponding column"""
        filter_field = self._driver.find_element(By.XPATH,
                                                 f"{self._x}//*[text()='{column_name}']"
                                                 f"/ancestor::th[@role='columnheader']//input"
                                                 )
        filter_field.send_keys(Keys.CONTROL + 'a')
        filter_field.send_keys(Keys.DELETE)
        filter_field.send_keys(value)
        filter_field.send_keys(Keys.ENTER)

    @WebAction()
    def __fetch_table_title(self):
        """Fetches the table title"""
        title = self._driver.find_element(By.XPATH,
                                          f"{self._x}//*[contains(@class, 'grid-title')]"
                                          )
        return title.text

    @WebAction()
    def __get_column_names(self, is_exported=False):
        """Read all column names from table"""
        if is_exported:
            # to handle empty headers
            return [
                column.text if len(self._driver.find_elements(By.XPATH, f"{self._x}//th")) > 0
                else ''
                for column in self._driver.find_elements(By.XPATH, f"{self._x}//th")
            ]

        return [
            # to handle empty headers
            column.find_element(By.XPATH, ".//*[contains(@class, 'header-cell-title')]").text
            if len(column.find_elements(By.XPATH, ".//*[contains(@class, 'header-cell-title')]")) > 0
            else ''
            for column in
            self._driver.find_elements(By.XPATH,
                                       f"{self._x}//th[@role='columnheader']"
                                       )
        ]

    @WebAction()
    def __get_row_count(self):
        """Get number of rows"""
        pager_info = self.__get_pagination()
        if pager_info == '':
            rows = self._driver.find_elements(By.XPATH, f"{self._x}//tbody//tr")

            if len(rows) == 1 and rows[0].text == 'No results found':
                return 0
            else:
                return len(rows)

        count = re.findall(r'of (\d+)', pager_info)
        return int(count[0])

    @WebAction()
    def __get_rows_by_column_idx(self, index):
        """Get all the rows inside the column using index"""
        return [
            cell.text for cell in self._driver.find_elements(By.XPATH, f"{self._x}//tbody/tr/td[{index}]")
        ]

    @WebAction()
    def __get_attributed_cells_by_column_idx(self, index):
        """Get style attributes of all cell values inside column"""
        return [
            {
                "bg_color": cell.value_of_css_property('background-color'),
                "font_color": cell.value_of_css_property('color'),
                "font_size": cell.value_of_css_property('font-size'),
                "data": cell.text
            }
            for cell in self._driver.find_elements(By.XPATH, f"{self._x}//tbody/tr/td[{index}]")
        ]

    @WebAction()
    def __is_filter_enabled(self):
        """ Check the filter is enabled by default or not"""
        elements = self._driver.find_elements(By.XPATH,
                                              f"{self._x}"
                                              f"//th[@role='columnheader']//div[contains(@class,'MuiTextField-root')]"
                                              )
        return len(elements) > 0

    @WebAction()
    def __click_action_menu(self, entity_name, col_name):
        """Clicks on the action menu
        Args:
            entity_name (str): table cell value in whose row action menu has to be clicked
        """
        columns = self.__get_column_names()
        index = columns.index(col_name) + 1

        self._driver.find_element(By.XPATH,
                                  f"//*[text()='{entity_name}']"
                                  f"/ancestor::tr[contains(@class, 'k-master-row')]"
                                  f"/td[{index}]//*[@aria-label='More']"
                                  ).click()

    @WebAction()
    def __click_action_menu_link(self, action_item):
        """
        clicks link on action menu
        entity_name (str): table cell value in whose row action menu has to be clicked
        Action_item (str): item to access in action menu
        """
        self._driver.find_element(By.XPATH,
                                  f"//div[@role='presentation' and @id='Component1-menu']//li//*[text()='{action_item}']"
                                  ).click()

    @WebAction()
    def __type_in_search(self, entity, search_id=None):
        """Types in the given entity to the search box"""
        xpath = f"{self._x}//input[@data-testid='grid-search-input']"
        if search_id:
            xpath = f"{self._x}//input[@data-testid='grid-search-input' and @id='{search_id}']"
        element = self._driver.find_element(By.XPATH, xpath)
        element.send_keys(Keys.CONTROL + 'a')
        element.send_keys(Keys.DELETE)
        element.send_keys(entity)
        element.send_keys(Keys.ENTER)

    @WebAction()
    def __copy_rest_api_url(self):
        """Returns the REST API URL"""
        url = self._driver.find_element(By.XPATH,
                                        "//*[contains(@class, 'mui-modal-dialog')]"
                                        "//p[contains(@class, 'MuiTypography-root')]").text
        return url

    @WebAction()
    def __get_all_list_items(self):
        """
        get all the items from the additional columns
        """
        xpath = f"{self._x}//*[contains(@class,'k-column-list-item')]"
        return [item.text for item in self._driver.find_elements(By.XPATH, xpath)]

    @WebAction()
    def _click(self, text):
        """clicks element containing {text}"""
        xp = f"{self._x}//*[text()='{text}']"
        self._driver.find_element(By.XPATH, xp).click()

    @PageService()
    def get_pagination(self):
        """
        get the page count
        """
        if self.__get_pagination() == '':
            return 0 if self.get_table_columns() == [] else 1
        else:
            ful_text = self.__get_pagination().split()
            return int(ful_text[4])

    @PageService()
    def enable_all_columns(self):
        """
        enable all the columns
        Returns:
        """
        self.__click_show_hide_columns()
        visible_cols = self.get_table_columns()
        hidden_columns = [col for col in self.__get_all_list_items() if col not in visible_cols]
        for column in hidden_columns:
            self.__click_column_on_additional_col_menu(column)
        self._click('Save')

    @PageService()
    def get_all_columns(self):
        """
        get all the columns form the table
        """
        self.__click_show_hide_columns()
        columns = self.__get_all_list_items()
        self._click('Save')
        return columns

    @PageService()
    def get_row_count(self):
        """To get the total number of rows"""
        return self.__get_row_count()

    @PageService()
    def configure_alert(self):
        """Opens configure alert window"""
        self.__click_table_gear()
        self._click("Configure alert")

    @PageService()
    def export_to_csv(self):
        """Export to CSV using the Table Level CSV export option"""
        self.__click_more_actions()
        self.__select_more_action("Export CSV")
        self._adminconsole.wait_for_completion()

    @PageService()
    def rest_api(self):
        """Copy Rest API"""
        self.__click_table_gear()
        self._click("REST API")
        self._adminconsole.wait_for_completion()

        dialog = RModalDialog(self._adminconsole)
        url = self.__copy_rest_api_url()
        dialog.click_close()

        return url

    @PageService()
    def charts(self):
        """Convert table into chart"""
        self.__click_table_gear()
        self._click("Charts")
        self._adminconsole.wait_for_completion()

    @PageService()
    def toggle_column_visibility(self, column_name):
        """Enable hidden column"""
        self.__click_show_hide_columns()
        self.__click_column_on_additional_col_menu(column_name)
        self._click('Save')
        self._adminconsole.wait_for_completion()

    @PageService()
    def set_filter(self, column_name, filter_string):
        """Filter table data"""
        if not self.__is_filter_enabled():
            self.__click_more_actions()
            self.__select_more_action("Show quick filters")
        self.__set_filter(column_name, filter_string)
        self._adminconsole.wait_for_completion()

    @PageService()
    def set_number_of_rows(self, number_of_results=50):
        """Set the number of rows to show on a table"""
        self.__click_rows_per_page_dropdown()
        self.__select_pagination_row_count(number_of_results)
        self._adminconsole.wait_for_completion()

    @PageService()
    def get_attributed_table_data(self):
        """Fetches the table data along with style information."""

        return {
            col: self.__get_attributed_cells_by_column_idx(i)
            for i, col in enumerate(self.__get_column_names())
        }

    @PageService()
    def get_table_data(self):
        """Dump all data in the table as json"""
        return {
            col: self.__get_rows_by_column_idx(i + 1)
            for i, col in enumerate(self.__get_column_names())
        }

    @PageService()
    def get_exported_table_data(self):
        """Dump all data from exported file in the table as json"""
        columns = self.__get_column_names(is_exported=True)
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
            expand_icon = self._driver.find_element(By.XPATH, f"{self._x}//*[@aria-label='Expand grid']")
            expand_icon.click()

    @PageService()
    def get_table_columns(self):
        """Get all visible column names"""
        return self.__get_column_names()

    @PageService()
    def get_column_data(self, column_name):
        """Get column data"""
        idx = self.get_table_columns().index(column_name)
        return self.__get_rows_by_column_idx(idx + 1)

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
    def access_action_item(self, entity_name, action_item, search=True, col_name='Actions'):
        """
        Selects the action menu in Table

        Args:
            entity_name (str): Entity against which action item has to be selected

            action_item (str): action item which has to be selected

            search (bool) : set to false if search is not required

            col_name (str) : column name where action menu is present
        """

        if search:
            self.__type_in_search(entity_name)
        self.__click_action_menu(entity_name, col_name)
        self._adminconsole.wait_for_completion()
        self.__click_action_menu_link(action_item)
        self._adminconsole.wait_for_completion()
        if search:
            self.__type_in_search('')

    @PageService()
    def search_from_table(self, entity, search_id=None):
        """Searches the given entity through the table
        Args:
            entity      (str)   :   Entity text to be searched from table data
            search_id   (str)   :   Search Bar ID if multiple search bars are present
        """
        self.__type_in_search(entity, search_id=search_id)
        self._adminconsole.wait_for_completion()


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
        """Selects the given list of rows

        Args:
            rows (list) : List of row numbers for which checkbox have to be selected.
        """

        for idx in rows:
            self.__select_row(idx)

    @PageService()
    def select_row_by_value(self, column_name, row_values):
        """Select rows checkbox by specified column value"""
        row_data = self.get_column_data(column_name)
        for row_number in range(len(row_data)):
            if row_data[row_number] in row_values:
                self.__select_row(row_number + 1)

    def associate_button(self, button):
        if not isinstance(button, ButtonViewer):
            raise ValueError("invalid component type")
        button.configure_viewer_component(self._adminconsole, page="Page0")
        button._set_x(None, self._x + f"//button[@id='{button.id}']")

    def associate_column(self, column):
        if not isinstance(column, ColumnViewer):
            raise ValueError("invalid component type")
        column.configure_viewer_component(self._adminconsole, page="Page0")
        column.id = column.title
        column._set_x(None, self._x + "//th/div[@title='%s']" % column.title)


class MailTable:
    """This class contains actions specific to table present in mail body"""

    def __init__(self, driver, table_id):
        """To initialize MailTable class

        Args:
            driver      (obj)   -- browser driver object

            table_id    (str)   -- Comp ID of the table

        """
        self.driver = driver
        self.id = table_id.replace("component", "table")
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


class Column(ColumnViewer):
    """
    Dummy class to reference all the Column Operations inside a table
    available on the report Builder
    """


class Button(ButtonViewer):
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


class Column(ColumnViewer):
    """
    Dummy class to reference all the Column Operations inside a table
    available on the report Builder
    """


class Button(ButtonViewer):
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
