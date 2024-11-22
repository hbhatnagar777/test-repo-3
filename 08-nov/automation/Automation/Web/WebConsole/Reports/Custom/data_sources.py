from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for performing data sources related operation.



                            DataSource
                                 |
                    _____________|______________
                    |                          |
            CommcellDataSource         DatabaseDataSource
                                               |
                     __________________________|_________________________
                     |                         |                        |
                MySQLDataSource         OracleDataSource        SQLServerDataSource

"""

from abc import (
    abstractmethod,
    ABC
)
from time import sleep
from selenium.webdriver.support.ui import Select

from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (
    WebAction,
    PageService
)


class DataSource(ABC):
    """This class is to manage activities on the Data Sources page."""

    def __init__(self, webconsole):
        """
        Args:
            webconsole (WebConsole): The webconsole object to use
        """
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver

    @abstractmethod
    def _ds_type(self):
        """Type of the data source."""
        raise NotImplementedError

    @abstractmethod
    def _display_name(self):
        """Display format of the data source.
        Examples:
            sqlserver is displayed as SQL server.

            mysql is displayed as MySQL

        """
        raise NotImplementedError

    @WebAction()
    def _click_add(self):
        """Clicks 'Add new Data Source' button"""
        button = self._driver.find_element(By.XPATH, "//a[.='Add New Data Source']")
        button.click()
        sleep(0.5)

    @WebAction()
    def _click_edit(self, ds_name):
        """Clicks edit."""
        edit = self._driver.find_element(By.XPATH, 
            "//li[contains(.,'%s')]//a[@title = 'Edit this Data Source.']" % ds_name)
        edit.click()

    @WebAction()
    def _click_delete(self, ds_name):
        """Clicks delete."""
        delete = self._driver.find_element(By.XPATH, 
            "//li[contains(.,'%s')]//a[@title = 'Are you sure you want"
            " to delete this Data Source?']" % ds_name)
        delete.click()

    @WebAction()
    def _confirm_delete(self):
        """Confirms delete after the page is faded."""
        yes = self._driver.find_element(By.XPATH, "// button[@id = 'button-ok']")
        yes.click()

    @WebAction()
    def _click_save(self):
        """Clicks save button."""
        button = self._driver.find_element(By.XPATH, "//input[@id='submitButton']")
        button.click()

    @WebAction()
    def _is_data_source_expanded(self, datasource):
        """Returns True if the given datasource tab is expanded"""
        obj = self._driver.find_element(By.XPATH, f"//*[@id='{datasource}']")
        style = obj.get_attribute("style")
        return False if "display: none" in style else True

    @WebAction()
    def _expand_data_source(self, datasource):
        """Clicks the given data_source"""
        data_source = self._driver.find_element(By.XPATH, f"//a[.='{datasource}']")
        data_source.click()

    @WebAction()
    def _get_data_source_names(self, datasource):
        """Returns the list of data sources of the given type."""
        data_sources = self._driver.find_elements(By.XPATH, 
            f"//div[@id='{datasource}']//li[@class='dsList']")
        return [data_source.text.strip() for data_source in data_sources]

    def _validate_save(self):
        """Validates the given action."""
        notifications = self._webconsole.get_all_unread_notifications(expected_count=1)
        if "Successfully registered" not in notifications[0]:
            raise CVWebAutomationException(
                f"Register Data Source failed with [{notifications}]"
            )

    def _validate_delete(self):
        """Validates the given action."""
        notifications = self._webconsole.get_all_unread_notifications(expected_count=1)
        if "Successfully deleted" not in notifications[0]:
            raise CVWebAutomationException(f"Delete Data Source failed with [{notifications}]")

    @PageService()
    def get_data_source_names(self):
        """Fetches the list of data sources

        Returns:
            list - list of data sources.

        """
        if self._is_data_source_expanded(self._ds_type()) is False:
            self._expand_data_source(self._display_name())
        return self._get_data_source_names(self._ds_type())

    @PageService()
    def delete_data_source(self, ds_name):
        """Deletes the given data source.

        Args:
            ds_name:        Name of the data source

        """
        self._webconsole.clear_all_notifications()
        if self._is_data_source_expanded(self._ds_type()) is False:
            self._expand_data_source(self._display_name())
        self._click_delete(ds_name)
        self._confirm_delete()
        self._webconsole.wait_till_load_complete()
        self._validate_delete()


class CommcellDataSource(DataSource):
    """All operations on Commcell Data Source goes into this class."""

    def _display_name(self):
        return "CommCells"

    def _ds_type(self):
        return "commcell"

    def _fill_commcell_details(self, commcell_name, username, password):
        self._set_commcell_hostname(commcell_name)
        self._set_commcell_username(username)
        self._set_commcell_password(password)

    @WebAction()
    def _set_commcell_hostname(self, commcell_name):
        """Sets Commcell host name."""
        host_name = self._driver.find_element(By.XPATH, "//input[@name='commcell']")
        host_name.clear()
        host_name.send_keys(commcell_name)

    @WebAction()
    def _set_commcell_username(self, username):
        """Sets commcell username."""
        username_field = self._driver.find_element(By.XPATH, "//input[@name='userName']")
        username_field.clear()
        username_field.send_keys(username)

    @WebAction(hide_args=True)
    def _set_commcell_password(self, password):
        """Sets commcell password."""
        password_field = self._driver.find_element(By.XPATH, "//input[@id='commcell-password']")
        password_field.clear()
        password_field.send_keys(password)

    @PageService(hide_args=True)
    def add_data_source(self, commcell_name, username, password):
        """Adds a remote commcell as a data source.

        Args:
            commcell_name: name of the commcell

            username: name of the user

            password: password

        """
        self._click_add()
        self._fill_commcell_details(commcell_name, username, password)
        self._click_save()
        self._webconsole.wait_till_load_complete()
        self._validate_save()

    @PageService(hide_args=True)
    def edit_data_source(self, commcell_name, commcell_hostname, username, password):
        """Edits the given data source.

        Args:
            commcell_name: name of the commcell which wants to be edited

            commcell_hostname: hostname of the commcell

            username: name of the user

            password: password

        """
        if self._is_data_source_expanded(self._ds_type()) is False:
            self._expand_data_source(self._display_name())
        self._click_edit(commcell_name)
        self._fill_commcell_details(commcell_hostname, username, password)
        self._click_save()
        self._webconsole.wait_till_load_complete()
        self._validate_save()


class _DatabaseDataSource(DataSource):
    """All operations on Commcell Data Source goes into this class. """

    def __fill_database_details(self, ds_name, host, name, username, password):
        """Fills the database details"""
        self.__set_data_source_type_dropdown(self._ds_type())
        self.__set_data_source_name(ds_name)
        self.__set_host_name(host)
        self.__set_name(self._database_type(), name)
        self.__set_database_username(username)
        self.__set_database_password(password)

    @abstractmethod
    def _database_type(self):
        """ Type of database such as database or instance."""
        raise NotImplementedError

    @WebAction()
    def __set_name(self, database_type, name):
        """Sets the database/instance name"""
        username_field = self._driver.find_element(By.XPATH, "//input[@name='%s']" % database_type)
        username_field.clear()
        username_field.send_keys(name)

    @WebAction()
    def __click_add_remote_database(self):
        """Clicks 'Add Remote Database' radio button."""
        button = self._driver.find_element(By.XPATH, "//label[.='Add Remote Database']")
        button.click()

    @WebAction()
    def __set_data_source_name(self, ds_name):
        """Sets the data source name."""
        data_source = self._driver.find_element(By.XPATH, "//input[@name='connectionName']")
        data_source.clear()
        data_source.send_keys(ds_name)

    @WebAction()
    def __set_host_name(self, hostname):
        """Sets the data source name."""
        host = self._driver.find_element(By.XPATH, "//input[@name='host']")
        host.clear()
        host.send_keys(hostname)

    @WebAction()
    def __set_database_username(self, username):
        """Sets the database username."""
        username_field = self._driver.find_element(By.XPATH, "//input[@name='username']")
        username_field.clear()
        username_field.send_keys(username)

    @WebAction()
    def __set_database_password(self, password):
        """Sets the database password."""
        password_field = self._driver.find_element(By.XPATH, "//input[@name='pwd']")
        password_field.clear()
        password_field.send_keys(password)

    @WebAction()
    def __set_data_source_type_dropdown(self, ds_type):
        """Selects the given database type from the list."""
        drop_down = self._driver.find_element(By.XPATH, 
            "//select[@id='dbType']")
        Select(drop_down).select_by_value(ds_type)

    @PageService()
    def add_data_source(self, ds_name, host, db_name, username, password):
        """Adds the given data source.

        Args:
            ds_name: Name of the data source.

            host: Host name

            db_name: Database name.

            username: Name of the user.

            password: password
        """
        self._webconsole.clear_all_notifications()
        self._click_add()
        self.__click_add_remote_database()
        self.__fill_database_details(ds_name, host, db_name, username, password)
        self._click_save()
        self._webconsole.wait_till_load_complete()
        self._validate_save()

    @PageService()
    def edit_data_source(self, ds_name, new_ds_name, host, db_name, username, password):
        """Edits the given data source.

        Args:
            ds_name: Name of the data source.

            new_ds_name: New name of the datasource

            host: Host name

            db_name: Database name.

            username: Name of the user.

            password: password
        """
        self._webconsole.clear_all_notifications()
        if self._is_data_source_expanded(self._ds_type()) is False:
            self._expand_data_source(self._display_name())
        self._click_edit(ds_name)
        self.__fill_database_details(new_ds_name, host, db_name, username, password)
        self._click_save()
        self._webconsole.wait_till_load_complete()
        self._validate_save()


class OracleDataSource(_DatabaseDataSource):
    """All operations on Oracle Data Source goes into this class."""

    def _ds_type(self):
        return "oracle"

    def _display_name(self):
        return "Oracle"

    def _database_type(self):
        return "database"


class MySQLDataSource(_DatabaseDataSource):
    """All operations on MySQL Data Source goes into this class."""

    def _ds_type(self):
        return "mysql"

    def _display_name(self):
        return "MySQL"

    def _database_type(self):
        return "database"


class SQLServerDataSource(_DatabaseDataSource):
    """All operations on SQL Server Data Source goes into this class."""

    def _ds_type(self):
        return "sqlserver"

    def _display_name(self):
        return "SQL Server"

    def _database_type(self):
        return "instance"
