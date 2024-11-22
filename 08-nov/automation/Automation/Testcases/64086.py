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
import datetime
import time

from AutomationUtils.cvtestcase import CVTestCase
from Metallic.hubutils import HubManagement
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Metallic_O365_OneDrive_Delete_Feature:
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_OneDrive_Delete_Feature"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.hub_utils = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.hub_dashboard = None
        self.service_catalogue = None
        self.app_type = None
        self.users = None
        self.app_name = None
        self.file_names = None
        self.folder_names = None
        self.search_file = None
        self.app_id = None
        self.dir_id = None
        self.app_secret = None
        self.tenant_user_name = None
        self.tenant_password = None
        self.utils = TestCaseUtils(self)

    '''def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.hub_utils = HubManagement(self, self.commcell.webconsole_hostname)
        self.tenant_name = datetime.datetime.now().strftime('o365-auto-%d-%b-%H-%M')
        current_timestamp = str(int(time.time()))
        self.tenant_user_name = self.hub_utils.create_tenant(
            company_name=self.tenant_name,
            email=f'cvautouser-{current_timestamp}@onedrive{current_timestamp}.com')'''

    def setup(self):
        #self.create_tenant()
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        #self.admin_console.login(self.tenant_user_name,
        #                         self.inputJSONnode['commcell']['commcellPassword'])
        self.tenant_user_name = self.tcinputs['tenant_user_name']
        self.tenant_password = self.tcinputs['tenant_password']
        self.admin_console.login(self.tenant_user_name,
                                 self.tenant_password)

        self.service = HubServices.office365
        self.app_type = O365AppTypes.onedrive
        #self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)

        self.navigator = self.admin_console.navigator

        #self.navigator.navigate_to_service_catalogue()
        #self.service_catalogue.start_office365_trial()
        self.navigator.navigate_to_office365()
        self.users = self.tcinputs['Users'].split(",")
        self.app_name = self.tcinputs['Name']
        self.file_names = self.tcinputs['file_names']
        self.folder_names = self.tcinputs['folder_names']
        self.search_file = self.tcinputs["search_file"]
        self.app_id = self.tcinputs['app_id']
        self.dir_id = self.tcinputs['dir_id']
        self.app_secret = self.tcinputs['app_secret']
        self.log.info("Creating an object for office365 helper")
        is_react = False
        if self.inputJSONnode['commcell']['isReact'] == 'true':
            is_react = True
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react)

    def run(self):
        """Main function for test case execution"""
        try:
            self.office365_obj.create_office365_app(name=self.app_name,
                                                    global_admin=self.tcinputs['GlobalAdmin'],
                                                    password=self.tcinputs['Password'],
                                                    is_express_config=False, app_id=self.app_id,
                                                    dir_id=self.dir_id, app_secret=self.app_secret, plan=self.tcinputs['plan'])
            self.app_name = self.office365_obj.get_app_name()
            office365plan = self.tcinputs['office365plan']
            self.office365_obj.add_user(self.users, plan=office365plan)
            bkp_job_details = self.office365_obj.run_backup()
            if int(bkp_job_details['No of objects backed up']) != 15:
                raise Exception(f'Backup is not successful')
            time.sleep(10)
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            self.office365_obj.browse_entity(entity_name=self.users[0])
            self.office365_obj.access_folder_in_browse("My Drive")
            before_delete_count, after_delete_count = self.office365_obj.delete_backup_data([self.file_names[0]])
            if int(after_delete_count) != int(before_delete_count) - 1:
                raise Exception(f'Item is not deleted . Delete feature is not verified')
            before_delete_count, after_delete_count = self.office365_obj.delete_backup_data([self.folder_names[0]])

            before_delete_count, after_delete_count = self.office365_obj.delete_backup_data([self.folder_names[1], self.file_names[1], self.file_names[2]])

            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            restore_job_details = self.office365_obj.run_restore()
            if int(restore_job_details['No of files restored']) != int(bkp_job_details['No of objects backed up']) - 1:
                raise Exception(f'Delete feature or Restore is having failures')

            self.log.info("Delete Feature is Successfully Verified")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.app_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

