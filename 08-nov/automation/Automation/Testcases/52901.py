# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""App Launch and Delete"""
from Web.Common.page_object import TestStep
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import (CVTestCaseInitFailure, CVTestStepFailure)
from Web.AdminConsole.Reports.apps import (
    AppsPage
)
from Web.AdminConsole.adminconsole import AdminConsole
from Web.WebConsole.webconsole import WebConsole
from Reports.App.util import AppUtils
from Web.API.cc import Apps as AppsApi
_APP_CONFIG = AppUtils.get_config()


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Install, Export, Delete, Import operation on App"
        self.adminconsole = None
        self.browser = None
        self.utils = None
        self.apps_page = None
        self.navigator = None
        self.webconsole = None
        self.app = None
        self.apps_api = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.apps_api = AppsApi(self.inputJSONnode['commcell']["webconsoleHostname"])
            self.utils = AppUtils(self)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.adminconsole = AdminConsole(
                self.browser,
                self.commcell.webconsole_hostname
            )
            self.adminconsole.login(
                self.inputJSONnode['commcell']["commcellUsername"],
                self.inputJSONnode['commcell']["commcellPassword"]
            )
            self.navigator = self.adminconsole.navigator
            self.navigator.navigate_to_cvapps()
            self.apps_page = AppsPage(self.adminconsole)

        except Exception as ex:
            raise CVTestCaseInitFailure(ex) from ex

    @test_step
    def install_app_from_store(self):
        # TODO
        """Install app from store"""
        self.store_app.install_app(_APP_CONFIG.DEFAULT.name)
        self.store_app.open_package(
            _APP_CONFIG.DEFAULT.name, category="APPS"
        )
        rpt_name = self.viewer.get_report_name()
        self.webconsole.get_all_unread_notifications()  # To clear error messages
        primary_comp = _APP_CONFIG.DEFAULT.primary.name
        if rpt_name != primary_comp:
            raise CVTestStepFailure(
                f"Expecting report title [{primary_comp}] when "
                f"[{_APP_CONFIG.DEFAULT.name}] is opened, but "
                f"received [{rpt_name}]"
            )
        self.webconsole.goto_applications()
        self.webconsole.goto_apps()

    @test_step
    def export_installed_app(self):
        # TODO
        """Export installed app"""
        App(_APP_CONFIG.DEFAULT.name, self.apps_page).export()
        self.utils.poll_for_tmp_files(ends_with="cvapp.zip", count=1)

    @test_step
    def search_app(self):
        """Search app"""
        app_name = _APP_CONFIG.DEFAULT.name
        self.apps_page.lookup_app(app_name)

    @test_step
    def delete_app(self):
        """Delete app"""
        app_name = _APP_CONFIG.DEFAULT.name
        self.apps_page.delete(app_name)
        self.browser.driver.refresh()
        if app_name in self.apps_page.get_apps():
            raise CVTestStepFailure("App visible on Apps page after deleteApp visible on Apps page after delete")

    @test_step
    def launch_app(self):
        """Launch app"""
        app_name = _APP_CONFIG.DEFAULT.name
        self.apps_page.launch(app_name)
        if app_name != self.adminconsole.driver.title:
            raise CVTestStepFailure("Launched app did not match with the given App Name")
        self.browser.close_current_tab()
        self.browser.switch_to_latest_tab()

    @test_step
    def import_app_from_filepath(self):
        """Import app from file"""
        filepath = self.tcinputs["filepath"]
        self.apps_api.import_app_from_path(filepath)
        self.browser.driver.refresh()
        if _APP_CONFIG.DEFAULT.name not in self.apps_page.get_apps():
            raise CVTestStepFailure("App not visible on Apps page after import")

    def run(self):
        try:
            self.init_tc()
            # self.install_app_from_store()
            # self.export_installed_app()
            self.import_app_from_filepath()
            self.launch_app()
            self.delete_app()

        except Exception as ex:
            self.utils.handle_testcase_exception(ex)
        finally:
            AdminConsole.logout_silently(self.adminconsole)
            Browser.close_silently(self.browser)
