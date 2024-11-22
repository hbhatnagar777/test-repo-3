# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Custom report: Remote DB registration """

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_datasources import (
    MySQLDataSource,
    OracleDataSource,
    SQLServerDataSource
)

from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.utils import CustomReportUtils


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom report: Remote DB registration"
        self.browser = None
        self.adminconsole = None
        self.mysql = None
        self.oracle = None
        self.sqlserver = None
        self.utils = None
        self.ds_name = {
            "mysql": "Automation DS MySQL",
            "oracle": "Automation DS Oracle",
            "sqlserver": "Automation DS SQL Server"
        }

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.utils = CustomReportUtils(self, username=self.inputJSONnode["commcell"]["commcellUsername"],
                                           password=self.inputJSONnode["commcell"]["commcellPassword"])
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.adminconsole = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.utils.webconsole = self.adminconsole
            self.adminconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                                    self.inputJSONnode['commcell']['commcellPassword'])
            navigator = self.adminconsole.navigator
            navigator.navigate_to_manage_datasources()
            self.mysql = MySQLDataSource(self.adminconsole)
            self.oracle = OracleDataSource(self.adminconsole)
            self.sqlserver = SQLServerDataSource(self.adminconsole)
            self.cleanup()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def cleanup(self):
        """Cleans up existing data sources created by automation"""
        if self.ds_name["mysql"] in self.mysql.get_data_source_names():
            self.mysql.delete_data_source(self.ds_name["mysql"])
        if self.ds_name["oracle"] in self.oracle.get_data_source_names():
            self.oracle.delete_data_source(self.ds_name["oracle"])
        if self.ds_name["sqlserver"] in self.sqlserver.get_data_source_names():
            self.sqlserver.delete_data_source(self.ds_name["sqlserver"])

    @test_step
    def register_data_sources(self):
        """Registers data source."""
        self.mysql.add_data_source(self.ds_name["mysql"], self._tcinputs["mysqlhostname"],
                                   "commvault", self._tcinputs["mysql_DB_user_name"],
                                   self._tcinputs["mysql_DB_password"])
        self.oracle.add_data_source(self.ds_name["oracle"], self._tcinputs["oraclehostname"],
                                    "commvault", self._tcinputs["Or_DB_user_name"],
                                    self._tcinputs["Or_DB_password"])
        self.sqlserver.add_data_source(self.ds_name["sqlserver"], self._tcinputs["Sqlhostname"],
                                       "commvault", self._tcinputs["sql_DB_user_name"],
                                       self._tcinputs["sql_DB_password"])

    @test_step
    def check_reflected_changes(self):
        """Checks whether the added data sources in shown up in the list."""
        if self.ds_name["mysql"] not in self.mysql.get_data_source_names():
            raise CVTestStepFailure("MySQL data source is not listed")
        if self.ds_name["oracle"] not in self.oracle.get_data_source_names():
            raise CVTestStepFailure("Oracle data source is not listed")
        if self.ds_name["sqlserver"] not in self.sqlserver.get_data_source_names():
            raise CVTestStepFailure("SQLServer data source is not listed")

    @test_step
    def delete_data_sources(self):
        """Deletes the data source."""
        self.mysql.delete_data_source(self.ds_name["mysql"])
        self.oracle.delete_data_source(self.ds_name["oracle"])
        self.sqlserver.delete_data_source(self.ds_name["sqlserver"])

        if self.ds_name["mysql"] in self.mysql.get_data_source_names():
            raise CVTestStepFailure("MySQL data source '{}'is listed even after deleting".
                                    format(self.ds_name["mysql"]))
        if self.ds_name["oracle"] in self.oracle.get_data_source_names():
            raise CVTestStepFailure("Oracle data source '{}'is listed even after deleting".
                                    format(self.ds_name["oracle"]))
        if self.ds_name["sqlserver"] in self.sqlserver.get_data_source_names():
            raise CVTestStepFailure("SQLServer data source '{}'is listed even after deleting".
                                    format(self.ds_name["sqlserver"]))

    def run(self):
        try:
            self.init_tc()
            self.register_data_sources()
            self.check_reflected_changes()
            self.delete_data_sources()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.adminconsole)
            Browser.close_silently(self.browser)