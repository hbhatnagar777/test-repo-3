# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.access_control_helper import AccessControlHelper
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Basic Acceptance test for Access Policies page."""
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance test for Access Policies page."
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.access_control_obj = None
        self._initial_owner_permissions = None
        self._new_owner_permissions = None
        self.utils = TestCaseUtils(self)
        self.driver = None

    def setup(self):
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.driver = self.admin_console.driver
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'],
                                 stay_logged_in=True)
        self.navigator = self.admin_console.navigator

    def run(self):
        try:
            self.navigator.navigate_to_access_control()
            self.access_control_obj = AccessControlHelper(self.admin_console)

            self.access_control_obj.get_available_owner_permissions()

            self._initial_owner_permissions = self.access_control_obj.initial_owner_permissions()

            self._new_owner_permissions = self.access_control_obj.randomly_generate_owner_permissions()

            self.access_control_obj.edit_owner_permission(self._new_owner_permissions)

            self.access_control_obj.verify_owner_permissions(self._new_owner_permissions)

            popped_elem = self._new_owner_permissions.pop()

            self.access_control_obj.edit_owner_permission([popped_elem], False)

            self.access_control_obj.verify_owner_permissions(self._new_owner_permissions)

        except Exception as err:
            self.utils.handle_testcase_exception(err)

    def tear_down(self):
        try:
            self.access_control_obj.revert_owner_permissions(self._initial_owner_permissions)
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
