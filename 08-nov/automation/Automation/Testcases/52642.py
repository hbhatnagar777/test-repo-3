# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Test case to check the basic acceptance of operation window in Admin console.

It verifies
1. Creation of operation rule based on different criteria's passed as arguments
2. Validates if the operation rule is created successfully.
3. Editing of operation rule created in above steps.
4. Deletion of operation rule created, edited & verified in above steps.

Optional TC inputs:

creation_params: Dict with the parameters and values to pass to creation page service

edit_params: Dict with the paramteres and values to pass to edit page service
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.OperationWindowHelper import OperationWindowHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser


class TestCase(CVTestCase):
    """ Basic Acceptance test for Backup rule configuration """

    def __init__(self):
        """
        Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.op_helper = None
        self.name = "Basic Acceptance Test Blackout window in AdminConsole"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.tcinputs = {}

    def setup(self):
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self._inputJSONnode['commcell']['commcellUsername'],
                                 password=self._inputJSONnode['commcell']['commcellPassword'])
        self.op_helper = OperationWindowHelper(
            self.admin_console, self.commcell, self.tcinputs
        )

    def run(self):
        try:
            self.op_helper.setup_bw_page()
            self.op_helper.validate_bw_table()
            self.op_helper.validate_bw_creation()
            self.op_helper.validate_bw_edit()
            self.op_helper.validate_bw_delete()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            self.op_helper.clean_up()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
