# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from datetime import datetime

from AutomationUtils.cvtestcase import CVTestCase
from Reports.storeutils import StoreUtils
from Web.Common.cvbrowser import Browser
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom import viewer
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole
from Web.API import (
    customreports as custom_reports_api)


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Recent Activity Link Validation"
        self.browser = None
        self.webconsole = None
        self.store = None
        self.cre_api = None
        self.table = None
        self.inputs = StoreUtils.get_store_config()

    def init_tc(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.store = StoreApp(self.webconsole)
            self.cre_api = custom_reports_api.CustomReportsAPI(
                self.commcell.webconsole_hostname
            )
            self.cre_api.delete_custom_report_by_name(
                self.inputs.Reports.FREE.name, suppress=True
            )
            self.webconsole.goto_store()
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def activity_validation(self):
        """When Recent Activity is clicked, Recent updates table is displayed"""
        self.store.access_recent_activity_link()
        activity_table = self.store.is_recent_updates_table_displayed()
        if activity_table:
            self.log.info("Recent Updates Table is displayed")
        else:
            self.log.info("Recent Updates Table is NOT displayed")
            raise CVTestStepFailure("Recent Updates Table is NOT displayed")
        viewer_obj = viewer.CustomReportViewer(self.webconsole)
        self.table = viewer.DataTable("Recent Updates")
        viewer_obj.associate_component(self.table)
        row = self.table.get_rows_from_table_data()[0]
        actual_activity = [row[0], row[1], ','.join(row[4].split(',')[:2]), row[5]]
        expected_activity = [self.inputs.Reports.FREE.name, 'Report',
                             datetime.now().strftime("%b %#d, %Y"), 'Manual Install']
        if expected_activity == actual_activity:
            self.log.info("Recent Activity is updated in Recent Updates Table")
        else:
            self.log.info("Expected row %s", expected_activity)
            self.log.info("Actual row displayed %s", actual_activity)
            raise CVTestStepFailure("Recent Activity is not updated in Recent Updates Table")

    @test_step
    def install_report(self):
        """Installing report"""
        self.store.install_report(
            self.inputs.Reports.FREE.name
        )

    def run(self):
        try:
            self.init_tc()
            self.install_report()
            self.activity_validation()
        except Exception as err:
            StoreUtils(self).handle_testcase_exception(err)
        finally:
            custom_reports_api.logout_silently(self.cre_api)
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
