from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Module to add all components used in Metrics reports
"""

from time import sleep
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from AutomationUtils import logger
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.cte import ConfigureAlert
from Web.Common.page_object import (WebAction, PageService)
LOG = logger.get_log()


class MetricsTable:
    """
    MetricsTable can be used to operate on tables present in Metrics reports
    """
    def __init__(self, webconsole: WebConsole, table_name='CommCell Details'):
        self._driver = webconsole.browser.driver
        self._webconsole = webconsole
        self._table_name = table_name
        self._table_id = None
        if table_name:
            self._comp_xp = (
                "//span[@class='reportstabletitle' and text()='%s']/../.." % self._table_name
            )
        else:
            self._comp_xp = "//div[@id='ccTableWrapper']"

    @property
    def id(self):
        """Returns the table ID"""
        if not self._table_id:
            self._table_id = self._driver.find_element(By.XPATH, 
                "//span[@class='reportstabletitle' and text()='%s']/ancestor::div[@comp]" % self._table_name
            ).get_attribute('comp')
        return self._table_id

    @WebAction()
    def _get_column_names(self):
        """Gets the column names"""
        enabled_columns_xp = self._comp_xp + "//th"
        return [column.text for column in self._driver.find_elements(By.XPATH, enabled_columns_xp)]

    @WebAction()
    def _is_filter_enabled(self):
        """Check if filter is enabled"""
        filter_xp = self._comp_xp + "//tr[contains(@id,'filterRow')]"
        filter_inp = self._driver.find_elements(By.XPATH, filter_xp)
        if filter_inp:
            return filter_inp[0].is_displayed()
        return False

    def _get_filter_objects(self):
        filter_inp_xpath = self._comp_xp + "//input[contains(@class, 'inLineFilter')]"
        return self._driver.find_elements(By.XPATH, filter_inp_xpath)

    @WebAction()
    def _click_additional_column_menu(self):
        """click on the additional Columns"""
        addtnl_icon_xp = self._comp_xp + "input[contains(@class,'AddorRemoveCols')]"
        self._driver.find_element(By.XPATH, addtnl_icon_xp).click()

    def _get_additonal_column_objs(self):
        """
        gets all additional column objects from additional columns list
        :return: additional column objects
        """
        addtnl_col_xp = self._comp_xp + "//ul[contains(@class, 'reportColums_container')]/li"
        return self._driver.find_elements(By.XPATH, addtnl_col_xp)

    @WebAction()
    def _click_column(self, column_name):
        """Clicks on the Column header"""
        try:
            col_xp = self._comp_xp + "//th[text()='%s']" % column_name
            self._driver.find_element(By.XPATH, col_xp).click()
        except NoSuchElementException as excep:
            raise NoSuchElementException(
                str(excep) +
                'Column %s doesnt exist in table [%s]' % (column_name, self._table_name)
            )

    @WebAction()
    def _expand_comp(self):
        """Expands the component"""
        expand_icon_xp = self._comp_xp + "//div[@class='arrowPlaceholder collapse']"
        self._driver.find_element(By.XPATH, expand_icon_xp).click()

    def _enable_column_chkbox(self, column_obj):
        chkbox = column_obj.find_element(By.TAG_NAME, 'div')
        if self._is_chkbox_enabled(chkbox) is False:
            chkbox.click()

    def _disable_column_chkbox(self, column_obj):
        chkbox = column_obj.find_element(By.TAG_NAME, 'div')
        if self._is_chkbox_enabled(chkbox) is True:
            chkbox.click()

    @WebAction()
    def _enable_columns(self, column_names_to_enable):
        """Enable columns"""
        avail_column_names = self.get_colums_from_additional_list()
        addtnl_col_objs = self._get_additonal_column_objs()
        self._click_additional_column_menu()
        for each_column in column_names_to_enable:
            try:
                col_indx = avail_column_names.index(each_column)
            except ValueError as excep:
                raise ValueError(
                    str(excep) +
                    "Column %s doesnt exist in table [%s]" % (each_column, self._table_name)
                )
            self._enable_column_chkbox(addtnl_col_objs[col_indx])
        self._click_additional_column_menu()

    @WebAction()
    def _disable_columns(self, column_names, addtnl_col_objs):
        """Disable Columns"""
        avail_column_names = self.get_colums_from_additional_list()
        self._click_additional_column_menu()
        for each_column in column_names:
            try:
                col_indx = avail_column_names.index(each_column)
            except ValueError as excep:
                raise ValueError(
                    str(excep) +
                    "Column %s doesnt exist in table [%s]" % (each_column, self._table_name)
                )
            self._disable_column_chkbox(addtnl_col_objs[col_indx])
        self._click_additional_column_menu()

    @WebAction()
    def _click_row_select(self):
        """click drop down for Row count selection"""
        tbl_length_xp = self._comp_xp + "//select[contains(@name, 'table_length')]"
        select_obj = self._driver.find_element(By.XPATH, tbl_length_xp)
        select_obj.click()

    @WebAction()
    def _select_rows(self, number_of_results):
        """Select the number of rows"""
        tbl_length_xp = self._comp_xp + "//select[contains(@name, 'table_length')]"
        select_obj = self._driver.find_element(By.XPATH, tbl_length_xp)
        for option in select_obj.find_elements(By.TAG_NAME, 'option'):
            if option.text == str(number_of_results):
                option.click()
                break

    @WebAction()
    def _open_alert(self):
        """Clicks on the alert"""
        alert_xp = self._comp_xp + "//input[contains(@class, 'tableAlarm')]"
        self._driver.find_element(By.XPATH, alert_xp).click()

    @staticmethod
    def _is_chkbox_enabled(chkbox):
        """
        :param chkbox object
        :return: True/False
        """
        return bool(str(chkbox.get_attribute('data-state')) == 'checked')

    @WebAction()
    def _get_data_from_column_by_idx(self, col_idx):
        """Read data from column"""
        odd_rows_xp = "//tr[@class='odd']/td[%d]" % col_idx
        even_rows_xp = "//tr[@class='even']/td[%d]" % col_idx
        odd_col_obj = self._driver.find_elements(By.XPATH, self._comp_xp + odd_rows_xp)
        odd_columns = [str(col.text).strip() for col in odd_col_obj]
        even_col_obj = self._driver.find_elements(By.XPATH, self._comp_xp + even_rows_xp)
        even_columns = [str(col.text).strip() for col in even_col_obj]
        col_data = []
        for idx, even_value in enumerate(even_columns):
            col_data.append(odd_columns[idx])
            col_data.append(even_value)
        if len(odd_columns) != len(even_columns):
            col_data.append(odd_columns[-1])
        return col_data

    @WebAction()
    def _get_row_data(self, row_idx):
        """Reads the row data"""
        row_xp = self._comp_xp + "//tbody/tr[%d]/td" % row_idx
        return [cellvalue.text for cellvalue in self._driver.find_elements(By.XPATH, row_xp)]

    @WebAction()
    def _click_csv_export(self):
        """Clicks on CSV export"""
        csv_xp = self._comp_xp + "//input[@class='tableExportExcel']"
        self._driver.find_element(By.XPATH, csv_xp).click()

    @WebAction()
    def _enter_filter_text(self, filters, column_number, value):
        """Enters text to filter panel"""
        filters[column_number].clear()
        filters[column_number].send_keys(value)
        filters[column_number].send_keys(Keys.RETURN)
        sleep(2)

    @property
    def is_csv_export_exists(self):
        """Check if CSV export option exist"""
        csv_xp = self._comp_xp + "//input[@class='tableExportExcel']"
        try:
            self._driver.find_element(By.XPATH, csv_xp)
            return True
        except NoSuchElementException:
            return False

    @PageService()
    def set_filter(self, column_name, value):
        """
        Send string in filter. this will enable filter if not enabled
        :param column_name: name of the column to set filter
        :param value: value to be sent in filter
        """
        self.enable_filter()
        filters = self._get_filter_objects()
        try:
            column_number = self._get_column_names().index(column_name)
        except ValueError as excep:
            raise ValueError(
                str(excep) +
                "Column %s doesnt exist in table [%s]" % (column_name, self._table_name)
            )
        self._enter_filter_text(filters, column_number, value)

    @PageService()
    def sort_column(self, column_name):
        """
        clicks on the column name to sort the column
        :param column_name: name on column to do the operation
        """
        self._click_column(column_name)

    @PageService()
    def expand(self):
        """
        expands the table
        """
        self._expand_comp()

    @PageService()
    def get_colums_from_additional_list(self):
        """
        gets column names from additional column list
        :return: list of column name from additional column list
        """
        self._click_additional_column_menu()
        addtnl_col_objs = self._get_additonal_column_objs()
        column_list = []
        for each_column_obj in addtnl_col_objs:
            column_list.append(str(each_column_obj.find_element(By.TAG_NAME, 'span').text))
        self._click_additional_column_menu()
        return column_list

    @PageService()
    def enable_filter(self):
        """
        enables filter on the table
        """
        if self._is_filter_enabled() is not True:
            filter_icon_xp = self._comp_xp + "//div[@class='reports_Filter  hideOnExportFriendly']"
            self._driver.find_element(By.XPATH, filter_icon_xp).click()

    @PageService()
    def get_number_of_columns(self):
        """
        gets number of columns present in table
        """
        return len(self._get_column_names())

    @PageService()
    def get_visible_column_names(self):
        """Get visible Column names"""
        return self._get_column_names()

    @PageService()
    def remove_columns(self, column_names):
        """
        removes the given column in table
        :param column_names: name of the column to remove
        """
        self._click_additional_column_menu()
        addtnl_col_objs = self._get_additonal_column_objs()
        self._disable_columns(column_names, addtnl_col_objs)
        self._click_additional_column_menu()

    @PageService()
    def add_columns(self, columns_to_enable=None):
        """
        add columns in the table from additional columns
        :param columns_to_enable: list of columns to enable if none all columns will be enabled
        """
        if columns_to_enable is None:
            columns_to_enable = self.get_colums_from_additional_list()
        self._click_additional_column_menu()
        self._enable_columns(columns_to_enable)
        self._click_additional_column_menu()

    @PageService()
    def get_data_from_column(self, column_name):
        """
        Returns a list of data for the given column
        :param column_name:
        :return: list of column data
        """
        col_idx = self._get_column_names().index(column_name) + 1
        return self._get_data_from_column_by_idx(col_idx)

    @PageService()
    def get_rows_count(self):
        """
        gets visible rows count
        :return: rows count
        """
        return len(self.get_data_from_column(self._get_column_names()[0]))

    @PageService()
    def get_table_title(self):
        """Returns table title"""
        return self.__get_table_title()

    @WebAction()
    def __get_table_title(self):
        """Fetches table title"""
        name = self._driver.find_element(By.XPATH, f"{self._comp_xp}//h1//*[text()='{self._table_name}']")
        return name.text

    @PageService()
    def get_data(self):
        """
        Reads whole table for all the columns visible
        :return: list fo rows(list of list)
        """
        rowcount = self.get_rows_count()
        table_data = []
        for row_idx in range(1, int(rowcount) + 1):
            table_data.append(self._get_row_data(row_idx))
        return table_data

    @PageService()
    def show_number_of_results(self, number_of_results=50):
        """
        selects the number of rows to be shown in table
        :param number_of_results: value to select in number of rows
        """
        self._click_row_select()
        self._select_rows(number_of_results)
        self._click_row_select()  # to close the panel

    @PageService()
    def csv_export(self):
        """
        performs a csv export on the table
        """
        self._click_csv_export()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def open_alert(self):
        """
        opens alert panel for the table
        :return: alert object
        """
        self._open_alert()
        return ConfigureAlert(self._webconsole)


class HealthTable:
    """Class to access Param type health Table like value assessment and scale statistics"""

    def __init__(self, webconsole, table_name, parameter_name):
        self._driver = webconsole.browser.driver
        self._webconsole = webconsole
        self.table = MetricsTable(webconsole, table_name)
        self.parameter_name = parameter_name

    @WebAction()
    def _filter_by_parameter(self):
        """Filters the health table by parameter"""
        self.table.set_filter(column_name='Parameter', value=self.parameter_name)

    @WebAction()
    def _read_status(self):
        """Reads the health status"""
        return self.table.get_data_from_column(column_name='Status')[0]

    @WebAction()
    def _read_outcome(self):
        """Reads the outcome of the health parameter"""
        return self.table.get_data_from_column(column_name='Outcome')[0]

    @WebAction()
    def _click_details(self):
        """clicks on view details on the remarks column"""
        details_xp = "//tr[1]/td[4]//a[text() = 'View Details']"
        self._driver.find_element(By.XPATH, self.table._comp_xp + details_xp).click()

    @PageService()
    def get_status(self):
        """ Gets the health status"""
        self._filter_by_parameter()
        return self._read_status()

    @PageService()
    def get_outcome(self):
        """ Get the outcome content"""
        self._filter_by_parameter()
        return self._read_outcome()

    @PageService()
    def access_view_details(self):
        """ Access the details page of health param in the table"""
        self._filter_by_parameter()
        self._click_details()
        self._webconsole.wait_till_load_complete()


class MailTable:
    """ This class can be used to get details of table content present in email"""
    def __init__(self, browser):
        self.browser = browser
        self._driver = self.browser.driver

    @WebAction()
    def _get_column_names(self):
        """Returns column names in mail table"""
        return [column.text for column in self._driver.find_elements(By.XPATH, "//table[@class="
                                                                              "'datatable']//th")]

    @WebAction()
    def _get_rows_count(self):
        """Returns rows count"""
        return len(self._driver.find_elements(By.XPATH, "//table[@class='datatable']//tr"))-1

    @WebAction()
    def _get_col_count(self):
        """get all column date"""
        col_xpath = f"//table[@class='datatable']//th"
        col_count = self._driver.find_elements(By.XPATH, col_xpath)
        return len(col_count)

    @WebAction()
    def _get_col_date(self, col_idx):
        """get all column date"""
        col_xpath = f"//table[@class='datatable']//td[{col_idx}]"
        col_values = [cellvalue.text for cellvalue in self._driver.find_elements(By.XPATH, col_xpath)]
        return list(filter(None, col_values))

    @PageService()
    def get_column_date(self):
        """ get each column data"""
        col_count = self._get_col_count()
        col_data = []
        for each_idx in range(1, int(col_count)+1):
            col_data.append(self._get_col_date(each_idx))
        return col_data

    @WebAction()
    def _get_row_data(self, row_idx):
        """Reads the row data"""
        row_xp = "//table[@class='datatable']//tr[%d]/td" % (row_idx + 1)
        return [cellvalue.text for cellvalue in self._driver.find_elements(By.XPATH, row_xp)]

    @WebAction()
    def _get_col_data(self, col_idx):
        """get all column date"""
        col_xpath = f"//table[@class='datatable']//td[{col_idx}]"
        return [cellvalue.text for cellvalue in self._driver.find_elements(By.XPATH, col_xpath)]

    @PageService()
    def get_table_data(self):
        """
        Reads whole table for all the columns from mail
        :return: list fo rows(list of list)
        """
        rowcount = self._get_rows_count()
        table_data = []
        for row_idx in range(1, int(rowcount) + 1):
            table_data.append(self._get_row_data(row_idx))
        return table_data


class AlertMail:
    """This class can be used to details from mails which are triggered by web reports alerts"""
    def __init__(self, browser):
        self.browser = browser
        self._driver = self.browser.driver
        self._table = MailTable(self.browser)

    @WebAction()
    def _get_alert_name(self):
        """Get alert name from mail"""
        return str(self._driver.find_element(By.TAG_NAME, 'b').text)

    @WebAction()
    def _get_report_name(self):
        """Get report name from mail"""
        name = str(self._driver.find_element(By.XPATH, '//b/a').text)
        return name.strip('.')

    @WebAction()
    def _get_report_link(self):
        """Get report link from mail"""
        link_obj = self._driver.find_element(By.XPATH, '//b/a')
        return link_obj.get_attribute('href')

    @WebAction()
    def _get_bold_data(self):
        """Get all bold texts as list"""
        return [column.text for column in self._driver.find_elements(By.XPATH, '//b')]

    @PageService()
    def get_alert_name(self):
        """Returns alert name"""
        return self._get_alert_name()

    @PageService()
    def get_report_link(self):
        """Get report link"""
        return self._get_report_link()

    def get_report_name(self):
        """Get report name from mail"""
        return self._get_report_name()

    def get_table_data(self):
        """Get table data from mail"""
        return self._table.get_table_data()

    @PageService()
    def get_column_date(self):
        """ get column data from th email"""
        return self._table.get_column_date()

    @PageService()
    def get_bold_data(self):
        """Returns list"""
        return self._get_bold_data()


class ScheduleMail:
    """
    This class can be used to get details from mails which are triggered by web reports
    schedules
    """
    def __init__(self, browser):
        self.browser = browser
        self._driver = self.browser.driver

    @WebAction()
    def _click_un_subscribe_email(self):
        """Click on unsubscribe email"""
        self._driver.find_element(By.XPATH, "//a[contains(text(), 'here.')]").click()

    @WebAction()
    def _get_unsubscribe_notification_(self):
        """Reads notification present in mail browser"""
        try:
            return str(self.browser.driver.find_element(By.XPATH, "//*[@id='unsubscribeEmail']").text)
        except NoSuchElementException:
            return ''

    @PageService()
    def un_subscribe_email(self):
        """click on unsubscribe email"""
        self._click_un_subscribe_email()

    @PageService()
    def is_valid_notification(self, mail_id):
        """
        verify if unsubscribe notification has valid email id and notification
        Args:
            mail_id                (String) --       Email ID

        Returns:True if it has valid notification else returns False
        """
        expected_notification = "This email (%s) has been removed " \
                                "from this automatic schedule." % mail_id
        return expected_notification == self._get_unsubscribe_notification_()

class TestCriteriaHealthTable:
    """ This class can be used to get details of table content
    present in test criteria table for health tiles alert. """
    def __init__(self, browser):
        self.browser = browser
        self._driver = self.browser.driver

    @WebAction()
    def _get_column_names(self):
        """Returns column names in table"""
        return [column.text for column in self._driver.find_elements(By.XPATH, "//div[@class='item-title']")]

    @WebAction()
    def _get_rows_count(self):
        """Returns rows count"""
        return len(self._driver.find_elements(By.XPATH, "//div[contains(@class,'healthAlertTable')]//tr")) - 1

    @WebAction()
    def _get_row_data(self, row_idx):
        """Reads the row data"""
        row_xp = f"//div[contains(@class,'healthAlertTable')]//tr[{row_idx}]/td"
        return [cellvalue.text for cellvalue in self._driver.find_elements(By.XPATH, row_xp)]

    @PageService()
    def get_table_data(self):
        """
        Reads whole table for all the columns
        :return: list fo rows(list of list)
        """
        rowcount = self._get_rows_count()
        table_data = []
        for row_idx in range(1, int(rowcount) + 1):
            table_data.append(self._get_row_data(row_idx))
        return table_data


