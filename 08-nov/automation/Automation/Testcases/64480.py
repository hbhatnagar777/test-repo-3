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
    Metallic_O365_OneDrive:
    Basic Validation for Metallic Onedrive PIT Restore
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_OneDrive_PIT_Restore"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.app_type = None
        self.users = None
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
        self.app_type = O365AppTypes.onedrive
        self.users = self.tcinputs['Users'].split(",")
        self.app_name = self.tcinputs['Name']
        self.log.info("Creating an object for office365 helper")
        is_react = False
        if self.inputJSONnode['commcell']['isReact'] == 'true':
            is_react = True
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react)
        self.navigator = self.admin_console.navigator

    def run(self):
        """Main function for test case execution"""
        try:
            client_level_restore_dict={}
            user_level_restore_dict={}

            for each in self.tcinputs['BackedUpEntities']:
                if each['ClientLevel']==True:
                    client_level_restore_dict['ClientLevel']=True
                    client_level_restore_dict['Job ID']=each['Job']
                    client_level_restore_dict['Entity'] = each['Entity']
                else:
                    user_level_restore_dict['ClientLevel'] = False
                    user_level_restore_dict['Job ID'] = each['Job']
                    user_level_restore_dict['Entity'] = each['Entity']

            # Client level PIT Restore
            backup_count,restore_job_details=self.office365_obj.perform_point_in_time_restore(client_level_restore_dict)
            if(backup_count != int(restore_job_details['No of files restored'])-3):    # Automation Folder is restored for each entity
               raise Exception(f'Count Mismatch in Client level PIT Restore')
            self.log.info("Client level PIT Restore is verified")

            # User level PIT Restore
            backup_count, restore_job_details = self.office365_obj.perform_point_in_time_restore(user_level_restore_dict)
            if (backup_count != int(restore_job_details['No of files restored'])-3):  # Automation Folder is restored
                raise Exception(f'Count Mismatch in User level PIT Restore')
            self.log.info("User level PIT Restore is verified")

            self.log.info("Test Case 64480 is executed successfully")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
