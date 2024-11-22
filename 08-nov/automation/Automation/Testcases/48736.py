# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Custom reports:Commcell Datasource registration """

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVWebAutomationException
)
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_datasources import CommcellDataSource

from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.utils import CustomReportUtils


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom reports:Commcell Datasource registration"
        self.browser = None
        self.adminconsole = None
        self.utils = None
        self.commcell_ds = None

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

            self.commcell_ds = CommcellDataSource(self.adminconsole)

            if self._tcinputs["display_name"] in self.commcell_ds.get_data_source_names():
                self.commcell_ds.delete_data_source(self._tcinputs["display_name"])
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def register_commcell_with_nonexisting_commcell(self):
        """Tries to register commcell datasource with unknown commcell"""
        error_msg = (f"Commcell : bdc an unknown commcell is getting registered."
                     f"Username:{self._tcinputs['username']} and Password: {self._tcinputs['password']}")
        try:
            self.commcell_ds.add_data_source("bdc",
                                             self._tcinputs["username"],
                                             self._tcinputs["password"])
            raise CVTestStepFailure(error_msg)
        except CVWebAutomationException as msg:
            if "Failed to reach remote commcell" not in str(msg):
                raise CVTestStepFailure("'Failed to reach remote commcell' string is missing in error message")
            if self._tcinputs["display_name"] in self.commcell_ds.get_data_source_names():
                raise CVTestStepFailure(error_msg)

    @test_step
    def register_commcell_with_wrong_creds(self):
        """Tries to register commcell datasource with wrong credentials"""
        error_msg = (f"Commcell : {self._tcinputs['commcell']} is getting registered with wrong credentials."
                     f"Username:{self._tcinputs['username']} and Password: WrongPassword")
        try:
            self.commcell_ds.add_data_source(self._tcinputs["commcell"],
                                             self._tcinputs["username"],
                                             "WrongPassword")
            raise CVTestStepFailure(error_msg)
        except CVWebAutomationException as msg:
            if "Invalid user name and password" not in str(msg):
                raise CVTestStepFailure("'Invalid user name and password' string is missing in error message")
            if self._tcinputs["display_name"] in self.commcell_ds.get_data_source_names():
                raise CVTestStepFailure(error_msg)

    @test_step
    def register_commcell_data_source(self):
        """Registers commcell data source."""
        self.commcell_ds.add_data_source(self._tcinputs["commcell"],
                                         self._tcinputs["username"],
                                         self._tcinputs["password"])

        if self._tcinputs["display_name"] not in self.commcell_ds.get_data_source_names():
            raise CVTestStepFailure(
                f"{self._tcinputs['display_name']} commcell data source is not listed after registration.")

    @test_step
    def delete_data_sources(self):
        """Deletes the commcell data source."""
        self.commcell_ds.delete_data_source(self._tcinputs["display_name"])

        if self._tcinputs["display_name"] in self.commcell_ds.get_data_source_names():
            raise CVTestStepFailure(
                f"{self._tcinputs['display_name']} commcell data source is listed after deleting it.")

    def run(self):
        try:
            self.init_tc()
            self.register_commcell_with_nonexisting_commcell()
            self.register_commcell_with_wrong_creds()

            self.register_commcell_data_source()
            self.delete_data_sources()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.adminconsole)
            Browser.close_silently(self.browser)

