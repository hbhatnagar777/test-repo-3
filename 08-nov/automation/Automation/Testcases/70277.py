# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

This test case verifies the functional cases on alert rule listing page

TestCase is the only class defined in this file.

TestCase: Class for executing this test case
"""
from selenium.webdriver.common.by import By
import datetime
import traceback
import csv
import xml.etree.ElementTree as ET

from AutomationUtils import logger
from AutomationUtils.config import get_config

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.Components.Navigator import _Navigator
from Web.AdminConsole.Components.table import Rtable, Rfilter
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.AdminConsolePages.AlertRules import AlertRules
from Web.AdminConsole.Helper.alert_rules_helper import AlertMain



class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "Functional testing on alert rule listing page"
        self.browser = None
        self.admin_console = None
        self.config = None
        self.exp = None
        self.logger = logger.get_log()

    def setup(self):
        """Setup function of this test case"""
        
        self.cs_user = self.inputJSONnode['commcell']['commcellUsername']
        self.cs_password = self.inputJSONnode['commcell']['commcellPassword']
        self.config = get_config()
        self.alert_rule_file_paths = self.tcinputs['AlertRulePaths']
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.table = Rtable(self.admin_console)
        self.admin_console.login(self.cs_user, self.cs_password)
        self.alert_rules = AlertRules(self.admin_console)
        self.alert_helper = AlertMain(self.admin_console)
        self.navigator = _Navigator(self.admin_console)
        self.alert_path_name_mapping = {path: self.alert_helper.get_rule_name_from_path(path) for path in self.alert_rule_file_paths}

    def run(self):
        """Run function of this test case"""

        try:
            # 1) Verify if “alert rules” page is shown under developer tools page

            self.navigator.navigate_to_alert_rules()
            self.table.setup_table('all') # select all columns

            # 1) Verify export table functionality
            self.alert_helper.export_and_verify("XLSX")
            self.alert_helper.export_and_verify("CSV")
            self.alert_helper.export_and_verify("PDF")

            # 2) Tasks related to single rule
            for path in self.alert_rule_file_paths:
                # 2.a) Import alert rule
                self.alert_rules.import_alert_rule(path)
                # 2.b) Verify if alert rule is imported
                self.navigator.navigate_to_alert_rules()
                result = self.alert_helper.does_alert_rule_exist(self.alert_path_name_mapping[path])
                if not result:
                    raise Exception(f"Alert rule '{self.alert_path_name_mapping[path]}' not found in the table.")
                # 2.c) Export alert rule
                self.alert_rules.export_alert_rule(self.alert_path_name_mapping[path])
                # 2.d) Toggle disable
                self.alert_rules.toggle_alert_rule(self.alert_path_name_mapping[path])
                # 2.e) Toggle enable
                self.alert_rules.toggle_alert_rule(self.alert_path_name_mapping[path])
            
            # 3) Verify filtering functionality
            self.alert_helper.perform_filtering_on_columns()

            # 4) Delete alert rules
            for path in self.alert_rule_file_paths:
                self.alert_rules.delete_alert_rule(self.alert_path_name_mapping[path])


        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""

        self.browser.close()