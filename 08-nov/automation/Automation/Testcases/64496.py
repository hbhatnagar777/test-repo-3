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
from Web.AdminConsole.Hub.constants import O365AppTypes
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    Class for executing Validation Test of Metallic_O365_Sharepoint_Delete_Data:
    Basic Validation for Deleting Backed up data after Backup in Metallic SharePoint Client
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_Sharepoint_Delete_Data"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.app_type = None
        self.site = None
        self.app_name = None
        self.utils = TestCaseUtils(self)

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tcinputs['ExistingComcellUserName'],
                                 self.tcinputs['ExistingComcellPassword'])
        self.app_type = O365AppTypes.sharepoint
        self.navigator = self.admin_console.navigator
        self.site = {self.tcinputs['Site']: self.tcinputs['SiteTitle']}
        self.app_name = self.tcinputs['Name']
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react=True)

    def run(self):
        """Main function for test case execution"""
        try:
            self.navigator.navigate_to_office365()
            self.office365_obj.create_office365_app(name=self.app_name,
                                                    global_admin=self.tcinputs['GlobalAdmin'],
                                                    password=self.tcinputs['Password'])
            self.app_name = self.office365_obj.get_app_name()
            self.navigator.navigate_to_plan()
            self.office365_obj.get_plans_list()
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            total_associated_sites = self.office365_obj.add_user(self.site)
            bkp_job_details = self.office365_obj.run_backup()
            self.office365_obj.verify_status_tab_stats(job_id=bkp_job_details['Job Id'],
                                                       status_tab_expected_stats={
                                                           "Total": total_associated_sites,
                                                           "Successful": total_associated_sites
                                                       })
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            for i in self.site:
                self.office365_obj.browse_entity([i, self.site[i]])
            self.office365_obj.delete_item(items_to_delete=[self.tcinputs['FileToDelete']])
            self.office365_obj.verify_items_present_in_browse(items={self.tcinputs['FileToDelete']: 0})

            self.log.info("Delete Data Metallic testcase is verified")
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.app_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)