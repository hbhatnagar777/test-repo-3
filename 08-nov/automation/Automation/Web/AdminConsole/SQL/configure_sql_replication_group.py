# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on configuration of
SQL Server Replication Group

"""

from selenium.common.exceptions import WebDriverException

from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.table import Table


class SQLServerReplication:
    """All the form operations related to SQL server goes here"""

    def __init__(self, admin_console):
        self.admin_console = admin_console
        self.driver = self.admin_console.driver
        self.log = self.admin_console.log

        self.__table = Table(self.admin_console)

    @PageService()
    def set_source(self, name, server, instance, databases):
        """Sets the content for the creation of new replication group

        Args:
            server(str):        Name of the server

            name(str):          Name of the replication group

            instance(str):      Name of the instance

            databases(list):    List of Databases

        """

        if isinstance(databases, list) is False:
            raise TypeError("Databases are expected as list")
        self.admin_console.fill_form_by_id("replicationName", name)
        self.admin_console.cv_single_select("Servers", server)
        self.admin_console.cv_single_select("Instances", instance)
        self.admin_console.__table.select_rows(databases)
        self.admin_console.click_button("Next")

    @PageService()
    def set_target(self, server=None, instance=None):
        """Sets the target

        Args:
            server(str):    Name of the target server

            instance(str):  Name of the instance

        """

        if server:
            self.admin_console.cv_single_select("Servers", server)
        if instance:
            self.admin_console.cv_single_select("Instances", instance)

        self.admin_console.click_button("Next")

    @PageService()
    def edit_content(self, databases=None, name=None):
        """Edits the content.
        Assigning None to all the arguments in this method simply clicks the next button

        Args:
            databases(list):    List of the databases to be in the replication group. Existing DBs will
                                be removed by default.

                default:        None. This will leave the DBs unaltered

            name(str):          If set renames the replication group

                default:        None. This will leave the DBs unaltered


        """
        if databases:
            self.__table.select_rows(databases)
        if name:
            self.admin_console.fill_form_by_id("replicationName", name)
        self.admin_console.click_button("Next")

    @PageService()
    def submit(self):
        """Submits the form for creating a new replication group"""
        self.admin_console.click_button("Submit")
        self.admin_console.wait_for_completion()

    @PageService()
    def save_edited_changes(self):
        """Saves the edited changes"""
        self.admin_console.click_button("Save")

    @PageService()
    def set_redirect_options(self, db_name, new_db_name=None, data_file_path=None, log_file_path=None):
        """Sets the redirect option

        Args:
            db_name(str)    : name of the DB for which the redirect options has to be set

            new_db_name(str): new name to be set

                default: None

            data_file_path(str): path for the data file

                default: None

            log_file_path(str): path for the log file

                default:None

        """
        self.admin_console.expand_options("Redirect option")
        self.admin_console.select_hyperlink(db_name)
        self.admin_console.fill_form_by_id("databaseName", new_db_name)
        self.admin_console.fill_form_by_id("dataFilePath", data_file_path)
        self.admin_console.fill_form_by_id("logFilePath", log_file_path)

    @PageService()
    def set_advanced_options(self, sync_delay=0, standby=False, undo_file_path=None):
        """Sets the advanced options

        Args:
            sync_delay(int):        sync delay to be set

                default: 0

            standby(bool):          sets to standby mode

                default: False

            undo_file_path(str):    sets the undo file path

                default: None

        """

        self.admin_console.expand_options("Advanced option")
        self.admin_console.fill_form_by_id("syncDelay", sync_delay)
        try:
            if standby:
                self.admin_console.select_radio("Stand by")
                self.admin_console.fill_form_by_id("undoFilePath", undo_file_path)
            else:
                self.admin_console.select_radio("No recovery")

        except WebDriverException:
            raise CVWebAutomationException("live Sync options are disabled")
