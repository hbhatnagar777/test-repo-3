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
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.RegionHelper import RegionMain
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test for regions test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test Regions in AdminConsole"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.region_obj = None
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""
        try:
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()

            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.region_obj = RegionMain(self.admin_console)

            self.region_obj.region_name = self.tcinputs.get('region_name') or \
                self.region_obj.region_name
            if self.commcell.regions.has_region(self.region_obj.region_name):
                self.log.info(f"Cleaning region {self.region_obj.region_name}")
                self.commcell.regions.delete(self.region_obj.region_name)

            self.region_obj.region_type = self.tcinputs.get('region_type') or \
                self.region_obj.region_type
            self.region_obj.region_locations = self.tcinputs.get('region_locations') or \
                self.region_obj.region_locations
            self.region_obj.edit_region_locations = self.tcinputs.get('edit_region_locations') or \
                self.region_obj.edit_region_locations

            self.region_obj.add_new_region()
            self.region_obj.validate_region_locations()
            self.region_obj.modify_region_location()
            self.region_obj.validate_region_locations()
            self.region_obj.delete_created_region()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        self.commcell.regions.refresh()
        if self.region_obj and self.commcell.regions.has_region(self.region_obj.region_name):
            self.log.info(f"Cleaning region {self.region_obj.region_name}")
            self.commcell.regions.delete(self.region_obj.region_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
