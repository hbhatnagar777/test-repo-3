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

    run()           --  run function of this test case
"""


from AutomationUtils.cvtestcase import CVTestCase
from Server.routercommcell import RouterCommcell
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.sevice_commcell_helper import ServiceCommcellMain

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test for companies test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.router_commcell = None
        self.name = "Basic Acceptance test for page Service CommCell."
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.service_commcell_obj = None
        self.tcinputs = {
            "ServiceCommcellName": None,
            "ServiceCommcellAdminUserName": None,
            "ServiceCommcellAdminUserPassword": None
        }
        self.deleted = False

    def run(self):
        """Main function for test case execution"""
        try:
            self.router_commcell = RouterCommcell(self.commcell)
            self.router_commcell.get_service_commcell(self.tcinputs["ServiceCommcellName"],
                                                      self.tcinputs["ServiceCommcellAdminUserName"],
                                                      self.tcinputs["ServiceCommcellAdminUserPassword"])
            if self.commcell.is_commcell_registered(self.router_commcell.service_commcell.commserv_name):
                self.log.info("Unregister service commcell if already registered")
                self.router_commcell.unregister_service_commcell()

            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.service_commcell_obj = ServiceCommcellMain(self.admin_console, self.csdb, self.commcell)

            self.service_commcell_obj.host_name = self.tcinputs['ServiceCommcellName']
            self.service_commcell_obj.user_name = self.tcinputs['ServiceCommcellAdminUserName']
            self.service_commcell_obj.password = self.tcinputs['ServiceCommcellAdminUserPassword']

            self.service_commcell_obj.create_service_commcell()
            self.service_commcell_obj.validate_service_commcell()
            self.service_commcell_obj.delete_service_commcell()
            self.deleted = True

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        if self.commcell.is_commcell_registered(self.router_commcell.service_commcell.commserv_name):
            self.log.info("Unregister service commcell if still registered")
            self.router_commcell.unregister_service_commcell()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
