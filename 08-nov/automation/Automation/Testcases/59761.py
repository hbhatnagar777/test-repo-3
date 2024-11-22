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
import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.office365_metallic import Office365Metallic
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Metallic:office365:SharePoint: Basic case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic: office365: SharePoint: Basic case"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.utils = TestCaseUtils(self)

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.tcinputs['Name'] += str(int(time.time()))
        self.tcinputs['OneDriveSubclientName'] += str(int(time.time()))
        self.log.info("Creating an object for office365 helper")
        self.tcinputs['office_app_type'] = Office365Metallic.AppType.share_point_online
        self.office365_obj = Office365Metallic(tcinputs=self.tcinputs, admin_console=self.admin_console)

    def run(self):
        """Main function for test case execution"""
        try:
            self.navigator.navigate_to_office365()
            self.office365_obj.create_metallic_office365_app()
            if not self.office365_obj.modern_authentication:
                self.status = constants.FAILED
            self.office365_obj.access_office365_app(self.tcinputs['Name'])
            self.office365_obj.add_sharepoint_sites()
            self.office365_obj.kill_automatically_launched_job()
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.tcinputs['Name'])
            self.office365_obj.run_backup()
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.tcinputs['Name'])
            self.office365_obj.run_restore()
            self.office365_obj.verify_backedup_mails()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.tcinputs['Name'])
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
