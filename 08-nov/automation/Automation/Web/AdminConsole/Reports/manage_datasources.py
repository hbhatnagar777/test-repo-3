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

from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService

from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.table import Rtable


class _DatasourceDialog(RModalDialog):
    """Handles datasource dialogs"""

    @PageService()
    def _fill_commcell_details(self, commcell_name, username, password):
        """Fills the commcell details"""

        self.fill_text_in_field('datasourceName', commcell_name)
        self.fill_text_in_field('username', username)
        self.fill_text_in_field('password', password)

    @PageService()
    def _fill_database_details(self, ds_type, ds_name, host, username, password, instance=None, db_name=None, port=None):
        """Fills the database details"""

        self.select_dropdown_values('connectionType', [ds_type])
        self.fill_text_in_field('datasourceName', ds_name)
        self.fill_text_in_field('host', host)

        if port:
            self.fill_text_in_field('port', port)
        if db_name:
            self.fill_text_in_field('databaseName', db_name)
        if instance:
            self.fill_text_in_field('instance', instance)

        self.fill_text_in_field('username', username)
        self.fill_text_in_field('password', password)
        

class AddDatasourceDialog(_DatasourceDialog):
    """Handles add datasource dialogs"""

    @PageService()
    def _fill_commcell_details(self, *args, **kwargs):
        """selects Commcell radio button and calls base function"""

        self._admin_console.select_radio(value='COMMCELL')
        super()._fill_commcell_details(*args, **kwargs)

    @PageService()
    def _fill_database_details(self, *args, **kwargs):
        """selects Database radio button and calls base function"""

        self._admin_console.select_radio(value='DATASOURCE')
        super()._fill_database_details(*args, **kwargs)


class EditDatasourceDialog(_DatasourceDialog):
    """Handles edit datasource dialogs"""

    pass


class DataSource(ABC):
    """This class is to manage activities on the Data Sources page."""

    def __init__(self, adminconsole):
        """
        Args:
            adminconsole (AdminConsole): The adminconsole object to use

        """

        self._adminconsole = adminconsole
        self._driver = adminconsole.browser.driver
        self._alert = Alert(adminconsole)
        self._table = Rtable(adminconsole)

    @abstractmethod
    def _ds_type(self):
        """Type of the data source."""

        raise NotImplementedError

    @abstractmethod
    def _display_name(self):
        """
        Display format of the data source.

        Examples:
            sqlserver is displayed as SQL server.

            mysql is displayed as MySQL

        """

        raise NotImplementedError  

    def _get_data_source_names(self, datasource):
        """Returns the list of data sources of the given type."""

        ds_headings = {'COMMCELL', 'ORACLE', 'SQLSERVER', 'MYSQL'}

        row_names = self._table.get_table_data()['Name']

        try:
            # index of datasource heading
            ds_heading_idx = row_names.index(datasource.upper())
        except ValueError:
            return []

        data_sources = row_names[ds_heading_idx+1:]

        # slice list if another heading is present
        for i, row_name in enumerate(data_sources):
            if row_name in ds_headings:
                data_sources = data_sources[:i]
                break

        return data_sources

    @PageService()
    def get_data_source_names(self):
        """Fetches the list of data sources

        Returns:
            list - list of data sources.

        """

        return self._get_data_source_names(self._ds_type())

    @PageService()
    def delete_data_source(self, ds_name):
        """Deletes the given data source.

        Args:
            ds_name:        Name of the data source

        """

        self._table.access_action_item(ds_name, 'Delete', search=False)
        dialog = RModalDialog(self._adminconsole, title='Delete datasource')
        dialog.click_yes_button()
        self._alert.check_error_message()
        self._alert.close_popup()


class CommcellDataSource(DataSource):
    """All operations on Commcell Data Source goes into this class."""

    def _display_name(self):
        return "CommCells"

    def _ds_type(self):
        return "commcell"

    @PageService(hide_args=True)
    def add_data_source(self, commcell_name, username, password):
        """Adds a remote commcell as a data source.

        Args:
            commcell_name: name of the commcell

            username: name of the user

            password: password

        """

        self._table.access_toolbar_menu('Add new data source')
        dialog = AddDatasourceDialog(self._adminconsole, title='Add new data source')
        dialog._fill_commcell_details(commcell_name, username, password)
        dialog.click_submit()

        try:
            self._alert.check_error_message(wait_time=0, raise_error=True)
        except CVWebAutomationException:
            dialog.click_cancel()
            raise

    @PageService(hide_args=True)
    def edit_data_source(self, commcell_name, commcell_hostname, username, password):
        """Edits the given data source.

        Args:
            commcell_name: name of the commcell which wants to be edited

            commcell_hostname: hostname of the commcell

            username: name of the user

            password: password

        """

        self._table.access_action_item(commcell_name, 'Edit', search=False)
        dialog = EditDatasourceDialog(self._adminconsole, title='Edit remote CommCell')
        dialog._fill_commcell_details(commcell_hostname, username, password)
        dialog.click_submit()

        try:
            self._alert.check_error_message(wait_time=0, raise_error=True)
        except CVWebAutomationException:
            dialog.click_cancel()
            raise


class _DatabaseDataSource(DataSource):
    """All operations on Commcell Data Source goes into this class. """

    @abstractmethod
    def _database_type(self):
        """ Type of database such as database or instance."""

        raise NotImplementedError

    @PageService()
    def add_data_source(self, ds_name, host, db_name, username, password, port=None):
        """Adds the given data source.

        Args:
            ds_name: Name of the data source.

            host: Host name

            db_name: Database name.

            username: Name of the user.

            password: password

        """

        self._table.access_toolbar_menu('Add new data source')
        dialog = AddDatasourceDialog(
            self._adminconsole, title='Add new data source')
        if self._database_type() == 'instance':
            dialog._fill_database_details(self._display_name(),
                                          ds_name, host, username, password, instance=db_name, port=port)
        else:
            dialog._fill_database_details(self._display_name(),
                                          ds_name, host, username, password, db_name=db_name, port=port)
        dialog.click_submit()

        try:
            self._alert.check_error_message(wait_time=0, raise_error=True)
        except CVWebAutomationException:
            dialog.click_cancel()
            raise

    @PageService()
    def edit_data_source(self, ds_name, new_ds_name, host, db_name, username, password, port=None):
        """Edits the given data source.

        Args:
            ds_name: Name of the data source.

            new_ds_name: New name of the datasource

            host: Host name

            db_name: Database name.

            username: Name of the user.

            password: password

        """

        self._table.access_action_item(ds_name, 'Edit', search=False)
        dialog = EditDatasourceDialog(
            self._adminconsole, title='Edit remote database')
        if self._database_type() == 'instance':
            dialog._fill_database_details(self._display_name(),
                                          new_ds_name, host, username, password, instance=db_name, port=port)
        else:
            dialog._fill_database_details(self._display_name(),
                                          new_ds_name, host, username, password, db_name=db_name, port=port)
        dialog.click_submit()

        try:
            self._alert.check_error_message(wait_time=0, raise_error=True)
        except CVWebAutomationException:
            dialog.click_cancel()
            raise


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
        return "MySql"

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
